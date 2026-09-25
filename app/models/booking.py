"""Booking SQLAlchemy model."""

import enum
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    """Booking lifecycle states."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Booking(Base):
    """A user's booking for a diagnostic test at a specific centre."""

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "centre_id",
            "test_id",
            "appointment_date",
            "appointment_time",
            name="uq_booking_slot",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    centre_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnostic_centres.id"),
        nullable=False,
    )
    test_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnostic_tests.id"),
        nullable=False,
    )
    appointment_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    appointment_time: Mapped[time] = mapped_column(
        Time, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=BookingStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")
    centre: Mapped["DiagnosticCentre"] = relationship(
        "DiagnosticCentre", lazy="select"
    )
    test: Mapped["DiagnosticTest"] = relationship(
        "DiagnosticTest", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Booking id={self.id} status={self.status}>"
