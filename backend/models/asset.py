"""Asset model — endpoints and OT/SCADA systems being monitored."""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv4 or IPv6
    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="endpoint"
    )  # endpoint | server | ot_scada | network_device | cloud_instance
    criticality_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard"
    )  # standard | high | critical — maps to NCIIPC CII sector classification
    sector: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # banking | power | telecom | health | transport | government
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    events: Mapped[list["EventRaw"]] = relationship(back_populates="asset", lazy="selectin")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="asset", lazy="selectin")
