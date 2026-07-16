"""PhishingScore model — output of the phishing classification module."""

from datetime import datetime
from sqlalchemy import Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PhishingScore(Base):
    __tablename__ = "phishing_scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events_raw.id"), unique=True, nullable=False
    )
    text_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    url_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    combined_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    verdict: Mapped[str] = mapped_column(
        String(20), nullable=False, default="benign"
    )  # benign | suspicious | phishing
    model_disagreement: Mapped[bool] = mapped_column(
        default=False
    )  # True when text and URL models disagree — evasion signal
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    event: Mapped["EventRaw"] = relationship(back_populates="phishing_score")
