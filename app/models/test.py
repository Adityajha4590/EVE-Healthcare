"""DiagnosticTest SQLAlchemy model."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiagnosticTest(Base):
    """A diagnostic test offered at a specific centre."""

    __tablename__ = "diagnostic_tests"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    centre_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnostic_centres.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    duration_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
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
    centre: Mapped["DiagnosticCentre"] = relationship(
        "DiagnosticCentre", back_populates="tests", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<DiagnosticTest id={self.id} name={self.name} price={self.price}>"
