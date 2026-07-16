"""AnomalyScore model — output of the anomaly detection module."""

from datetime import datetime
from sqlalchemy import Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class AnomalyScore(Base):
    __tablename__ = "anomaly_scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events_raw.id"), unique=True, nullable=False
    )
    isolation_forest_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    autoencoder_error: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    combined_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    anomaly_type: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # impossible_travel | brute_force | off_hours_ot | data_exfil | protocol_anomaly
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    event: Mapped["EventRaw"] = relationship(back_populates="anomaly_score")
