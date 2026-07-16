"""
Playbook Engine — maps (threat_type × severity) pairs to MITRE ATT&CK-aligned
response sequences from the database.

Section 9.5: Playbooks are rule-based and reviewed by a security advisor before
deployment — deliberately not left to a black-box model, since response actions
can disrupt real operations if wrong.
"""

import logging
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.playbook import Playbook

logger = logging.getLogger("rakshanet.playbook_engine")


async def recommend_playbook(
    threat_type: str,
    severity: str,
    db: AsyncSession,
) -> Optional[dict]:
    """
    Find the best-matching playbook for a given threat type and severity.

    Falls back to a lower-severity playbook for the same threat type
    if an exact match is not found.
    """
    # Try exact match first
    result = await db.execute(
        select(Playbook).where(
            and_(
                Playbook.threat_type == threat_type,
                Playbook.severity == severity,
            )
        )
    )
    playbook = result.scalar_one_or_none()

    # Fallback: find any playbook for this threat type
    if not playbook:
        result = await db.execute(
            select(Playbook).where(Playbook.threat_type == threat_type).limit(1)
        )
        playbook = result.scalar_one_or_none()

    if not playbook:
        logger.warning(
            f"No playbook found for threat_type={threat_type}, severity={severity}"
        )
        return None

    return {
        "playbook_id": playbook.id,
        "name": playbook.name,
        "threat_type": playbook.threat_type,
        "severity": playbook.severity,
        "mitre_technique": playbook.mitre_technique,
        "mitre_technique_name": playbook.mitre_technique_name,
        "description": playbook.description,
        "action_sequence": playbook.action_sequence_json,
        "requires_human_confirmation": playbook.requires_human_confirmation,
        "estimated_time_minutes": playbook.estimated_time_minutes,
    }


def generate_incident_ticket(
    alert_data: dict,
    playbook_data: dict,
    explanation: dict,
) -> dict:
    """
    Generate a ready-to-act incident ticket from an alert and its matched playbook.

    This is the core output that closes the detection-to-response gap (Section 3.3):
    a concrete, actionable ticket rather than just another alert.
    """
    return {
        "title": f"[{alert_data['severity'].upper()}] {playbook_data['mitre_technique']} — {playbook_data['name']}",
        "severity": alert_data["severity"],
        "threat_type": alert_data["threat_type"],
        "mitre_technique": playbook_data["mitre_technique"],
        "mitre_technique_name": playbook_data["mitre_technique_name"],
        "risk_score": alert_data["risk_score"],
        "affected_identity": alert_data.get("user_identity", "Unknown"),
        "explanation": explanation.get("summary", ""),
        "top_features": explanation.get("features", []),
        "recommended_actions": playbook_data["action_sequence"],
        "requires_confirmation": playbook_data["requires_human_confirmation"],
        "estimated_response_time": f"{playbook_data['estimated_time_minutes']} minutes",
        "playbook_id": playbook_data["playbook_id"],
    }
