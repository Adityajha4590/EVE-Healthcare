"""Pydantic schemas for diagnostic centre endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CentreCreateRequest(BaseModel):
    """Request body for creating a diagnostic centre (dev/seed use)."""

    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class CentreResponse(BaseModel):
    """Public representation of a diagnostic centre."""

    id: str
    name: str
    address: str
    city: str
    state: str
    pincode: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
