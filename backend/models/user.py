"""User model — IT/security staff who use the analyst dashboard."""

from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="analyst"
    )  # analyst | admin | engineer
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user", lazy="selectin")
    feedback: Mapped[list["AnalystFeedback"]] = relationship(
        back_populates="analyst", lazy="selectin"
    )
