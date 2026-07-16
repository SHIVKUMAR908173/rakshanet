"""EventRaw model — unprocessed ingested events prior to scoring."""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class EventRaw(Base):
    __tablename__ = "events_raw"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # email | network | auth | ot_scada
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="unknown"
    )  # phishing_candidate | login | network_flow | scada_access
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True
    )
    user_identity: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # email address or username of the person involved
    processed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="events", lazy="selectin")
    phishing_score: Mapped["PhishingScore"] = relationship(
        back_populates="event", uselist=False, lazy="selectin"
    )
    anomaly_score: Mapped["AnomalyScore"] = relationship(
        back_populates="event", uselist=False, lazy="selectin"
    )
