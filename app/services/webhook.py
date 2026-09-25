"""Webhook processing service."""

import hashlib
import hmac

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.booking import BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.schemas.webhook import WebhookPaymentPayload

logger = get_logger(__name__)


def verify_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
    """Verify the HMAC SHA256 signature of the payload."""
    if not signature:
        return False
        
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_payment_webhook(
    db: Session,
    payload: WebhookPaymentPayload,
) -> dict:
    """Process a payment webhook securely and idempotently."""

    # 1. Deduplication / Idempotency check via WebhookEvent
    # Using a separate table is excellent for idempotency because it works for all 
    # webhook types and clearly isolates the intent.
    try:
        event = WebhookEvent(
            event_id=f"payment_{payload.transaction_id}_{payload.status}",
            provider="simulated_gateway",
            payload=payload.model_dump_json(),
        )
        db.add(event)
        db.flush() # Will raise IntegrityError if event already exists
    except IntegrityError:
        db.rollback()
        logger.info("webhook_already_processed", transaction_id=payload.transaction_id)
        return {"status": "ok", "message": "Already processed"}

    # 2. Acquire row-level lock on the Payment to prevent race conditions
    payment = (
        db.query(Payment)
        .filter(Payment.transaction_id == payload.transaction_id)
        .with_for_update()
        .first()
    )
    
    if not payment:
        db.rollback()
        logger.error("webhook_unknown_transaction", transaction_id=payload.transaction_id)
        raise HTTPException(status_code=404, detail="Unknown transaction")

    # 3. Double-check terminal state on the payment itself
    if payment.status != PaymentStatus.PENDING.value:
        db.rollback()
        logger.info("webhook_payment_not_pending", transaction_id=payload.transaction_id, current_status=payment.status)
        return {"status": "ok", "message": "Payment already in terminal state"}
        
    # Verify amount matches to prevent tampering
    if payment.amount != payload.amount:
        db.rollback()
        logger.error("webhook_amount_mismatch", expected=str(payment.amount), received=str(payload.amount))
        # Keep it pending or fail it. Failing it is safer.
        payment.status = PaymentStatus.FAILED.value
        payment.failure_reason = "Amount mismatch in webhook"
        db.commit()
        return {"status": "ok", "message": "Failed due to amount mismatch"}

    # 4. Process the state transition
    if payload.status == "success":
        payment.status = PaymentStatus.SUCCESS.value
        payment.booking.status = BookingStatus.CONFIRMED.value
        logger.info("payment_succeeded", payment_id=payment.id, booking_id=payment.booking.id)
    else:
        payment.status = PaymentStatus.FAILED.value
        payment.failure_reason = payload.reason or "Payment failed"
        # Booking remains PENDING so the user can try again
        logger.info("payment_failed", payment_id=payment.id, reason=payment.failure_reason)

    db.commit()
    return {"status": "ok"}
