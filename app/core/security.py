"""Security utilities: password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

_ALGORITHM = settings.JWT_ALGORITHM


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for *subject* (user id).

    Token includes standard ``sub``, ``exp``, and ``iat`` claims.
    Expiration is controlled by ``JWT_ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises ``jwt.ExpiredSignatureError`` if the token has expired.
    Raises ``jwt.InvalidTokenError`` for any other validation failure.

    Returns the decoded payload dict on success.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[_ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
