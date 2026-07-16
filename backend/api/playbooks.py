"""Playbooks API — endpoints for retrieving MITRE ATT&CK-aligned response playbooks."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.playbook import Playbook
from schemas.playbook import PlaybookResponse, PlaybookListResponse, PlaybookActionStep

router = APIRouter(prefix="/playbooks", tags=["Playbooks"])


def _format_playbook(pb: Playbook) -> PlaybookResponse:
    """Convert a Playbook ORM object to its response schema."""
    action_steps = [
        PlaybookActionStep(**step) for step in (pb.action_sequence_json or [])
    ]
    return PlaybookResponse(
        id=pb.id,
        name=pb.name,
        threat_type=pb.threat_type,
        severity=pb.severity,
        mitre_technique=pb.mitre_technique,
        mitre_technique_name=pb.mitre_technique_name,
        description=pb.description,
        action_sequence=action_steps,
        requires_human_confirmation=pb.requires_human_confirmation,
        estimated_time_minutes=pb.estimated_time_minutes,
        created_at=pb.created_at,
    )


@router.get("", response_model=PlaybookListResponse)
async def list_playbooks(
    threat_type: Optional[str] = Query(None, description="Filter by threat type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all configured playbooks, optionally filtered by threat type and severity.

    This serves the Playbook Library view in the analyst dashboard (Section 12.3).
    """
    query = select(Playbook)

    if threat_type:
        query = query.where(Playbook.threat_type == threat_type)
    if severity:
        query = query.where(Playbook.severity == severity)

    result = await db.execute(query)
    playbooks = result.scalars().all()

    return PlaybookListResponse(
        total=len(playbooks),
        playbooks=[_format_playbook(pb) for pb in playbooks],
    )


@router.get("/{threat_type}", response_model=PlaybookListResponse)
async def get_playbooks_by_threat(
    threat_type: str,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the recommended playbook(s) for a given threat type.

    If severity is also specified, returns only the playbook matching
    both the threat type and severity level.
    """
    query = select(Playbook).where(Playbook.threat_type == threat_type)

    if severity:
        query = query.where(Playbook.severity == severity)

    result = await db.execute(query)
    playbooks = result.scalars().all()

    if not playbooks:
        raise HTTPException(
            status_code=404,
            detail=f"No playbooks found for threat_type='{threat_type}'"
            + (f", severity='{severity}'" if severity else ""),
        )

    return PlaybookListResponse(
        total=len(playbooks),
        playbooks=[_format_playbook(pb) for pb in playbooks],
    )
