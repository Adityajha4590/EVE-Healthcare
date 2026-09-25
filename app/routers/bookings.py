"""Booking routes — create and retrieve bookings (all require JWT auth)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.services.booking import create_booking, get_booking, list_bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a booking",
)
def create_booking_endpoint(
    body: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Book a diagnostic test.

    The backend derives user_id, amount, and status — they cannot be
    submitted by the client.
    """
    return create_booking(
        db,
        user=current_user,
        centre_id=body.centre_id,
        test_id=body.test_id,
        appointment_date=body.appointment_date,
        appointment_time=body.appointment_time,
    )


@router.get(
    "",
    response_model=list[BookingResponse],
    summary="List my bookings",
)
def list_bookings_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return list_bookings(db, user=current_user, page=page, page_size=page_size)


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get a booking by ID",
)
def get_booking_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_booking(db, user=current_user, booking_id=booking_id)
