"""Payment routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.payment import PaymentResponse
from app.services.payment import get_payment, initiate_payment

router = APIRouter(tags=["payments"])


@router.post(
    "/bookings/{booking_id}/pay",
    response_model=PaymentResponse,
    status_code=202,
    summary="Initiate a simulated payment for a booking",
)
def pay_for_booking_endpoint(
    booking_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiates a payment for a specific booking.
    Returns 202 Accepted because the payment happens asynchronously.
    """
    # Use request.base_url to pass to the simulated gateway so it knows where to webhook back to
    base_url = str(request.base_url).rstrip("/")
    return initiate_payment(
        db,
        user=current_user,
        booking_id=booking_id,
        base_url=base_url,
        background_tasks=background_tasks,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment status",
)
def get_payment_endpoint(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check the status of a payment."""
    return get_payment(db, user=current_user, payment_id=payment_id)
