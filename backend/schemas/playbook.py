"""Playbook schemas — response models for playbook retrieval."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PlaybookActionStep(BaseModel):
    """A single step within a playbook's action sequence."""

    step_number: int
    action: str
    description: str
    is_automated: bool = False
    requires_confirmation: bool = True
    estimated_minutes: int = 5


class PlaybookResponse(BaseModel):
    """Single playbook with full details."""

    id: int
    name: str
    threat_type: str
    severity: str
    mitre_technique: str
    mitre_technique_name: str
    description: str
    action_sequence: list[PlaybookActionStep]
    requires_human_confirmation: bool
    estimated_time_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlaybookListResponse(BaseModel):
    """List of playbooks, optionally filtered."""

    total: int
    playbooks: list[PlaybookResponse]
