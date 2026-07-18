"""
Event Processor — orchestrates the end-to-end scoring pipeline.

Sequence (Section 8.2):
  1. Load raw event from database
  2. Run phishing or anomaly scorer (depending on event type)
  3. Check for correlated signals on the same identity
  4. Compute fused risk score via the correlation engine
  5. Generate SHAP-like explanation
  6. If above alert threshold, create alert and match playbook
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models.event import EventRaw
from models.phishing_score import PhishingScore
from models.anomaly_score import AnomalyScore
from models.alert import Alert
from services.phishing_scorer import score_email
from services.anomaly_scorer import score_event
from services.correlation import (
    compute_risk_score,
    should_create_alert,
    determine_threat_type,
    get_mitre_technique,
)
from services.explainability import generate_explanation
from services.websocket_manager import manager
from schemas.alert import AlertResponse
from config import settings

logger = logging.getLogger("rakshanet.event_processor")


async def process_event(event_id: int, scoring_type: str):
    """
    Process a single event through the full scoring pipeline.

    This runs as a background task, using its own database session.

    Args:
        event_id: ID of the raw event to process
        scoring_type: "phishing" or "anomaly"
    """
    async with async_session() as db:
        try:
            # ── 1. Load the event ──
            result = await db.execute(
                select(EventRaw).where(EventRaw.id == event_id)
            )
            event = result.scalar_one_or_none()
            if not event:
                logger.error(f"Event {event_id} not found")
                return

            payload = event.raw_payload or {}
            phishing_result = None
            anomaly_result = None

            # ── 2. Run the appropriate scorer ──
            if scoring_type == "phishing":
                phishing_result = score_email(
                    subject=payload.get("subject", ""),
                    body=payload.get("body", ""),
                    urls=payload.get("urls", []),
                    headers=payload.get("headers"),
                )

                # Save phishing score
                ps = PhishingScore(
                    event_id=event_id,
                    text_score=phishing_result["text_score"],
                    url_score=phishing_result["url_score"],
                    combined_score=phishing_result["combined_score"],
                    verdict=phishing_result["verdict"],
                    model_disagreement=phishing_result["model_disagreement"],
                )
                db.add(ps)

            elif scoring_type == "anomaly":
                log_type = payload.get("log_type", event.source)
                anomaly_result = score_event(log_type, payload)

                # Save anomaly score
                ans = AnomalyScore(
                    event_id=event_id,
                    isolation_forest_score=anomaly_result["isolation_forest_score"],
                    autoencoder_error=anomaly_result["autoencoder_error"],
                    combined_score=anomaly_result["combined_score"],
                    anomaly_type=anomaly_result["anomaly_type"],
                )
                db.add(ans)

            # ── 3. Check for correlated signals ──
            phishing_score = (
                phishing_result["combined_score"] if phishing_result else 0.0
            )
            anomaly_score = (
                anomaly_result["combined_score"] if anomaly_result else 0.0
            )

            has_correlation = False
            if event.user_identity:
                has_correlation = await _check_correlation(
                    db, event.user_identity, event_id, scoring_type
                )

            # ── 4. Compute fused risk score ──
            risk_result = compute_risk_score(
                phishing_score=phishing_score,
                anomaly_score=anomaly_score,
                has_correlated_signals=has_correlation,
            )

            # ── 5. Create alert if above threshold ──
            if should_create_alert(risk_result["risk_score"]):
                threat_type = determine_threat_type(
                    phishing_score=phishing_score,
                    anomaly_score=anomaly_score,
                    anomaly_type=(
                        anomaly_result["anomaly_type"] if anomaly_result else None
                    ),
                    has_correlation=has_correlation,
                )

                # Generate explanation
                explanation = generate_explanation(
                    phishing_contributions=(
                        phishing_result.get("feature_contributions")
                        if phishing_result
                        else None
                    ),
                    anomaly_contributions=(
                        anomaly_result.get("feature_contributions")
                        if anomaly_result
                        else None
                    ),
                    correlation_breakdown=risk_result["breakdown"],
                    threat_type=threat_type,
                    severity=risk_result["severity"],
                )

                alert = Alert(
                    user_identity=event.user_identity,
                    asset_id=event.asset_id,
                    risk_score=risk_result["risk_score"],
                    severity=risk_result["severity"],
                    threat_type=threat_type,
                    mitre_technique=get_mitre_technique(threat_type),
                    status="open",
                    explanation_json=explanation,
                    explanation_text=explanation["summary"],
                    source_event_ids=[event_id],
                )
                db.add(alert)

                logger.info(
                    f"Alert created: severity={risk_result['severity']}, "
                    f"threat={threat_type}, score={risk_result['risk_score']}"
                )
                
            # Mark event as processed
            event.processed = True
            await db.commit()
            
            # Broadcast alert if one was created
            if should_create_alert(risk_result["risk_score"]):
                try:
                    await db.refresh(alert)
                    alert_dict = AlertResponse.model_validate(alert).model_dump(mode='json')
                    await manager.broadcast_alert(alert_dict)
                except Exception as ws_e:
                    logger.warning(f"Failed to broadcast alert over WS: {ws_e}")

        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}", exc_info=True)
            await db.rollback()


async def _check_correlation(
    db: AsyncSession,
    user_identity: str,
    current_event_id: int,
    current_type: str,
) -> bool:
    """
    Check if there are correlated signals on the same identity within
    the correlation window (default 24 hours).

    A correlation exists when both phishing and anomaly signals have
    fired for the same user identity recently.
    """
    window_start = datetime.now(timezone.utc) - timedelta(
        hours=settings.correlation_window_hours
    )

    if current_type == "phishing":
        # Check for recent anomaly alerts on this identity
        result = await db.execute(
            select(Alert).where(
                and_(
                    Alert.user_identity == user_identity,
                    Alert.threat_type != "phishing",
                    Alert.created_at >= window_start,
                )
            ).limit(1)
        )
    else:
        # Check for recent phishing alerts on this identity
        result = await db.execute(
            select(Alert).where(
                and_(
                    Alert.user_identity == user_identity,
                    Alert.threat_type == "phishing",
                    Alert.created_at >= window_start,
                )
            ).limit(1)
        )

    return result.scalar_one_or_none() is not None
