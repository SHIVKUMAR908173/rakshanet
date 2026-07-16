"""Incident schemas — request/response models for incident management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class IncidentCreateRequest(BaseModel):
    """Open a formal incident from an actioned alert."""

    alert_id: int = Field(..., description="ID of the alert to create an incident from")
    playbook_id: int = Field(..., description="ID of the playbook to apply")
    assigned_to: Optional[str] = Field(None, description="Name/email of the assigned responder")
    notes: Optional[str] = Field(None, description="Initial notes about the incident")


class IncidentUpdateRequest(BaseModel):
    """Update incident status as the response proceeds."""

    status: Optional[str] = Field(
        None,
        description="open | in_progress | contained | resolved | closed",
    )
    assigned_to: Optional[str] = Field(None, description="Reassign to a different responder")
    notes: Optional[str] = Field(None, description="Updated notes")
    actions_taken: Optional[list[dict]] = Field(
        None,
        description="List of playbook steps that have been executed",
    )


class IncidentResponse(BaseModel):
    """Single incident with full details."""

    id: int
    alert_id: int
    playbook_id: int
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    actions_taken: list[dict]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    """List of incidents."""

    total: int
    incidents: list[IncidentResponse]


class DashboardSummary(BaseModel):
    """Aggregate counts and trends for the dashboard landing view."""

    total_alerts: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    total_incidents: int = 0
    open_incidents: int = 0
    resolved_incidents: int = 0
    alerts_today: int = 0
    avg_risk_score: float = 0.0
    threat_type_breakdown: dict = Field(default_factory=dict)
    severity_breakdown: dict = Field(default_factory=dict)
    alerts_trend: list[dict] = Field(
        default_factory=list,
        description="Daily alert counts for the trend chart",
    )
    recent_alerts: list[dict] = Field(
        default_factory=list,
        description="Last 10 alerts for the quick-view panel",
    )
