"""Alerts API — endpoints for retrieving, filtering, and providing feedback on alerts."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.alert import Alert
from models.feedback import AnalystFeedback
from schemas.alert import (
    AlertResponse,
    AlertListResponse,
    AlertFeedbackRequest,
    AlertFeedbackResponse,
    AlertStatusUpdate,
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    threat_type: Optional[str] = Query(None, description="Filter by threat type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the current prioritised alert queue.

    Alerts are sorted by risk score (descending) so the most
    critical items appear first. Supports filtering by severity,
    status, and threat type.
    """
    query = select(Alert)

    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if threat_type:
        query = query.where(Alert.threat_type == threat_type)

    # Count total matching alerts
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page of alerts, ordered by risk score desc
    query = query.order_by(desc(Alert.risk_score)).offset(
        (page - 1) * page_size
    ).limit(page_size)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        alerts=[AlertResponse.model_validate(a) for a in alerts],
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single alert with its full SHAP explanation.

    The explanation_json field contains the top contributing features
    and their SHAP values, while explanation_text is the plain-language
    summary for generalist IT staff.
    """
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/feedback", response_model=AlertFeedbackResponse, status_code=201)
async def submit_feedback(
    alert_id: int,
    request: AlertFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Record an analyst verdict (confirmed_threat / false_positive / needs_investigation).

    This feedback is logged and used to periodically retrain both
    detection engines (Section 9.2.3 of the technical report).
    """
    # Verify alert exists
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    feedback = AnalystFeedback(
        alert_id=alert_id,
        verdict=request.verdict,
        analyst_id=request.analyst_id,
        confidence=request.confidence,
        notes=request.notes,
    )
    db.add(feedback)
    await db.flush()

    # Update alert status based on verdict
    if request.verdict == "confirmed_threat":
        alert.status = "confirmed"
    elif request.verdict == "false_positive":
        alert.status = "dismissed"
    elif request.verdict == "needs_investigation":
        alert.status = "investigating"

    return AlertFeedbackResponse(
        feedback_id=feedback.id,
        alert_id=alert_id,
        verdict=request.verdict,
        message="Feedback recorded successfully",
    )


@router.patch("/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    request: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update the status of an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    alert.status = request.status
    return {"alert_id": alert_id, "status": request.status, "message": "Status updated"}
