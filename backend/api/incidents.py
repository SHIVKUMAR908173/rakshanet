"""Incidents API — endpoints for creating and managing incident response workflows."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.alert import Alert
from models.incident import Incident
from models.playbook import Playbook
from schemas.incident import (
    IncidentCreateRequest,
    IncidentUpdateRequest,
    IncidentResponse,
    IncidentListResponse,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    request: IncidentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Open a formal incident from an actioned alert.

    Links the alert to a specific playbook and begins the response workflow.
    The alert status is automatically updated to 'investigating'.
    """
    # Verify alert exists
    alert_result = await db.execute(select(Alert).where(Alert.id == request.alert_id))
    alert = alert_result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {request.alert_id} not found")

    # Check for existing incident on this alert
    existing = await db.execute(
        select(Incident).where(Incident.alert_id == request.alert_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Incident already exists for alert {request.alert_id}",
        )

    # Verify playbook exists
    pb_result = await db.execute(
        select(Playbook).where(Playbook.id == request.playbook_id)
    )
    playbook = pb_result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(
            status_code=404, detail=f"Playbook {request.playbook_id} not found"
        )

    incident = Incident(
        alert_id=request.alert_id,
        playbook_id=request.playbook_id,
        status="open",
        assigned_to=request.assigned_to,
        notes=request.notes,
        actions_taken=[],
    )
    db.add(incident)
    await db.flush()

    # Update alert status
    alert.status = "investigating"

    return IncidentResponse.model_validate(incident)


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all incidents, optionally filtered by status."""
    query = select(Incident)

    if status:
        query = query.where(Incident.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(Incident.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size)
    result = await db.execute(query)
    incidents = result.scalars().all()

    return IncidentListResponse(
        total=total,
        incidents=[IncidentResponse.model_validate(inc) for inc in incidents],
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single incident with full details."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return IncidentResponse.model_validate(incident)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    request: IncidentUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update incident status as the response proceeds.

    Supports updating status, reassignment, notes, and tracking
    which playbook steps have been executed.
    """
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    if request.status is not None:
        incident.status = request.status
        if request.status in ("resolved", "closed"):
            incident.resolved_at = datetime.now(timezone.utc)
    if request.assigned_to is not None:
        incident.assigned_to = request.assigned_to
    if request.notes is not None:
        incident.notes = request.notes
    if request.actions_taken is not None:
        incident.actions_taken = request.actions_taken

    return IncidentResponse.model_validate(incident)
