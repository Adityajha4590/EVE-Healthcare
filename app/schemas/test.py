"""Pydantic schemas for diagnostic test endpoints."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class TestCreateRequest(BaseModel):
    """Request body for creating a diagnostic test (dev/seed use)."""

    centre_id: str
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)
    duration_minutes: int | None = Field(default=None, gt=0)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class TestResponse(BaseModel):
    """Public representation of a diagnostic test."""

    id: str
    centre_id: str
    name: str
    description: str | None
    price: Decimal
    duration_minutes: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
