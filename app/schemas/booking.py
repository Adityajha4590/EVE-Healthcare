"""Pydantic schemas for booking endpoints."""

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class BookingCreateRequest(BaseModel):
    """Request body for creating a booking.

    The client provides only what they choose; the backend derives
    user_id, amount, and status.
    """

    centre_id: str
    test_id: str
    appointment_date: date
    appointment_time: time

    @field_validator("appointment_date")
    @classmethod
    def date_must_not_be_past(cls, v: date) -> date:
        from datetime import date as _date

        if v < _date.today():
            raise ValueError("Appointment date cannot be in the past")
        return v


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class BookingResponse(BaseModel):
    """Public representation of a booking."""

    id: str
    user_id: str
    centre_id: str
    test_id: str
    appointment_date: date
    appointment_time: time
    status: str
    amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
