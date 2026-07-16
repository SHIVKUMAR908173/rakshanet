"""AnalystFeedback model — analyst verdicts feeding back into model retraining."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id"), nullable=False
    )
    verdict: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # confirmed_threat | false_positive | needs_investigation
    analyst_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    confidence: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low | medium | high
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    alert: Mapped["Alert"] = relationship(back_populates="feedback")
    analyst: Mapped["User"] = relationship(back_populates="feedback")
