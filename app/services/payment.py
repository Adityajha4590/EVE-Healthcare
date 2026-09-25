"""Payment service and simulated gateway."""

import asyncio
import hashlib
import hmac
import json
import uuid

import httpx
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.logging import get_logger
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.config import settings

logger = get_logger(__name__)


def generate_webhook_signature(payload: str, secret: str) -> str:
    """Generate HMAC SHA256 signature for the webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def simulated_gateway_task(
    transaction_id: str, amount: str, target_url: str
):
    """Simulate a payment gateway processing a payment asynchronously."""
    await asyncio.sleep(1.0)  # Simulate network/processing delay

    # 80% success rate simulation
    import random
    is_success = random.random() < 0.8
    
    payload_dict = {
        "transaction_id": transaction_id,
        "status": "success" if is_success else "failed",
        "amount": amount,
    }
    if not is_success:
        payload_dict["reason"] = "Insufficient funds or generic decline"

    payload_str = json.dumps(payload_dict)
    
    # We use a dummy secret if none provided in settings, but settings should have it.
    # We will use WEBHOOK_SECRET as the webhook secret for this assignment.
    signature = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(target_url, content=payload_str, headers=headers)
            logger.info("simulated_gateway_callback_sent", transaction_id=transaction_id)
        except Exception as e:
            logger.error("simulated_gateway_callback_failed", error=str(e), transaction_id=transaction_id)


def initiate_payment(
    db: Session,
    *,
    user: User,
    booking_id: str,
    base_url: str,
    background_tasks,
) -> Payment:
    """Initiate a payment for a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundException(detail="Booking not found")
    if booking.user_id != user.id:
        raise ForbiddenException(detail="Access denied")
    
    if booking.status != BookingStatus.PENDING.value:
        raise ConflictException(detail=f"Cannot pay for a booking in {booking.status} status")

    # Check if there's already a pending or successful payment
    existing_payment = (
        db.query(Payment)
        .filter(Payment.booking_id == booking.id)
        .filter(Payment.status.in_([PaymentStatus.PENDING.value, PaymentStatus.SUCCESS.value]))
        .first()
    )
    if existing_payment:
        raise ConflictException(detail="A payment is already pending or successful for this booking")

    # Generate a unique transaction ID
    transaction_id = f"txn_{uuid.uuid4().hex}"
    
    payment = Payment(
        booking_id=booking.id,
        transaction_id=transaction_id,
        amount=booking.amount,
        status=PaymentStatus.PENDING.value,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Schedule simulated gateway callback
    webhook_url = f"{base_url}/webhooks/payments"
    background_tasks.add_task(
        simulated_gateway_task,
        transaction_id=transaction_id,
        amount=str(payment.amount),
        target_url=webhook_url,
    )
    
    logger.info("payment_initiated", payment_id=payment.id, transaction_id=transaction_id)
    return payment


def get_payment(db: Session, *, user: User, payment_id: str) -> Payment:
    """Return a single payment, enforcing ownership via booking."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundException(detail="Payment not found")
    
    # Check ownership via the booking relationship
    if payment.booking.user_id != user.id:
        raise ForbiddenException(detail="Access denied")
        
    return payment
