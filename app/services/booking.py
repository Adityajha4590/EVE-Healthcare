"""Booking service — business logic for creating and retrieving bookings."""

from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.logging import get_logger
from app.models.booking import Booking, BookingStatus
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.user import User

logger = get_logger(__name__)


def create_booking(
    db: Session,
    *,
    user: User,
    centre_id: str,
    test_id: str,
    appointment_date: date,
    appointment_time,
) -> Booking:
    """Create a booking after validating all business rules.

    The backend controls user_id, amount, and status.
    """
    # --- Validate centre ---
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.id == centre_id
    ).first()
    if centre is None:
        raise NotFoundException(detail="Diagnostic centre not found")
    if not centre.is_active:
        raise AppException(
            detail="Cannot book at an inactive centre", status_code=400
        )

    # --- Validate test ---
    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.id == test_id
    ).first()
    if test is None:
        raise NotFoundException(detail="Diagnostic test not found")
    if not test.is_active:
        raise AppException(
            detail="Cannot book an inactive test", status_code=400
        )
    if test.centre_id != centre_id:
        raise AppException(
            detail="This test does not belong to the selected centre",
            status_code=400,
        )

    # --- Snapshot price at booking time ---
    amount = test.price

    booking = Booking(
        user_id=user.id,
        centre_id=centre_id,
        test_id=test_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status=BookingStatus.PENDING.value,
        amount=amount,
    )
    db.add(booking)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            "booking_duplicate_slot",
            user_id=user.id,
            centre_id=centre_id,
            test_id=test_id,
        )
        raise ConflictException(
            detail="A booking already exists for this slot"
        )

    db.refresh(booking)
    logger.info("booking_created", booking_id=booking.id, user_id=user.id)
    return booking


def list_bookings(
    db: Session,
    *,
    user: User,
    page: int = 1,
    page_size: int = 20,
) -> list[Booking]:
    """Return the authenticated user's bookings (paginated)."""
    offset = (page - 1) * page_size
    return (
        db.query(Booking)
        .filter(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


def get_booking(db: Session, *, user: User, booking_id: str) -> Booking:
    """Return a single booking, enforcing ownership.

    Raises ``NotFoundException`` if the booking doesn't exist.
    Raises ``ForbiddenException`` if the booking belongs to another user.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking is None:
        raise NotFoundException(detail="Booking not found")
    if booking.user_id != user.id:
        raise ForbiddenException(detail="Access denied")
    return booking
