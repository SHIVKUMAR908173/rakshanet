"""Playbook model — static MITRE ATT&CK-aligned response playbooks."""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Playbook(Base):
    __tablename__ = "playbooks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    threat_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # phishing | credential_compromise | brute_force | ot_anomaly | data_exfil | ddos
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # low | medium | high | critical
    mitre_technique: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # e.g. T1566, T1078, T1110, T1021, T1041, T1498
    mitre_technique_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Human-readable MITRE name
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_sequence_json: Mapped[list] = mapped_column(
        JSON, nullable=False
    )  # Ordered list of response actions
    requires_human_confirmation: Mapped[bool] = mapped_column(
        default=True
    )  # Human-in-the-loop gate for Medium+ severity
    estimated_time_minutes: Mapped[int] = mapped_column(default=15)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="playbook", lazy="selectin"
    )
