"""Alert model — correlated, explainable alert ready for analyst review."""

from datetime import datetime
from sqlalchemy import Float, String, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_identity: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # email or username of the identity under threat
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )  # assigned analyst (nullable until assigned)
    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # low | medium | high | critical
    threat_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # phishing | credential_compromise | brute_force | ot_anomaly | data_exfil | ddos
    mitre_technique: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # e.g. T1566, T1078, T1110
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open | investigating | confirmed | dismissed | escalated
    explanation_json: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # SHAP-based explanation object
    explanation_text: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Plain-language summary for generalist IT staff
    source_event_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # IDs of raw events that contributed to this alert
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="alerts", lazy="selectin")
    asset: Mapped["Asset"] = relationship(back_populates="alerts", lazy="selectin")
    incident: Mapped["Incident"] = relationship(
        back_populates="alert", uselist=False, lazy="selectin"
    )
    feedback: Mapped[list["AnalystFeedback"]] = relationship(
        back_populates="alert", lazy="selectin"
    )
