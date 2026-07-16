"""Alert schemas — request/response models for the alert API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    """Single alert with full details."""

    id: int
    user_identity: Optional[str] = None
    asset_id: Optional[int] = None
    risk_score: float
    severity: str
    threat_type: str
    mitre_technique: Optional[str] = None
    status: str
    explanation_json: dict
    explanation_text: str
    source_event_ids: list[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    total: int
    page: int
    page_size: int
    alerts: list[AlertResponse]


class AlertFeedbackRequest(BaseModel):
    """Record an analyst verdict for an alert."""

    verdict: str = Field(
        ...,
        description="confirmed_threat | false_positive | needs_investigation",
    )
    analyst_id: int = Field(..., description="ID of the analyst providing feedback")
    confidence: str = Field("medium", description="low | medium | high")
    notes: Optional[str] = Field(None, description="Additional analyst notes")


class AlertFeedbackResponse(BaseModel):
    """Response after recording feedback."""

    feedback_id: int
    alert_id: int
    verdict: str
    message: str = "Feedback recorded successfully"


class AlertStatusUpdate(BaseModel):
    """Update alert status."""

    status: str = Field(
        ...,
        description="open | investigating | confirmed | dismissed | escalated",
    )
