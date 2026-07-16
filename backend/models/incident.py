"""Incident model — tracked response workflow once an alert is actioned."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id"), unique=True, nullable=False
    )
    playbook_id: Mapped[int] = mapped_column(
        ForeignKey("playbooks.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="open"
    )  # open | in_progress | contained | resolved | closed
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions_taken: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # Track which playbook steps have been executed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    alert: Mapped["Alert"] = relationship(back_populates="incident")
    playbook: Mapped["Playbook"] = relationship(back_populates="incidents")
