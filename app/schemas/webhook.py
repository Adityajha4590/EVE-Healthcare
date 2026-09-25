"""Pydantic schemas for webhook endpoints."""

from decimal import Decimal

from pydantic import BaseModel, Field


class WebhookPaymentPayload(BaseModel):
    """Payload received from the simulated payment gateway."""

    transaction_id: str
    status: str = Field(..., description="success or failed")
    amount: Decimal
    reason: str | None = None
