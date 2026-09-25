"""Pydantic schemas for payment endpoints."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PaymentResponse(BaseModel):
    """Public representation of a payment."""

    id: str
    booking_id: str
    transaction_id: str
    amount: Decimal
    status: str
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
