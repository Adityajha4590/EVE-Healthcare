"""Pydantic schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# bcrypt silently ignores bytes beyond this limit; the modern bcrypt library
# raises ValueError instead.  We reject at the validation layer so the error
# is a clean 422, never an unhandled 500.
BCRYPT_MAX_PASSWORD_BYTES = 72


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    """POST /auth/signup request body."""

    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password must not exceed {BCRYPT_MAX_PASSWORD_BYTES} bytes "
                "when UTF-8 encoded"
            )
        return v


class LoginRequest(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr
    password: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """Safe public representation of a user — never exposes password_hash."""

    id: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response returned after successful login."""

    access_token: str
    token_type: str = "bearer"
