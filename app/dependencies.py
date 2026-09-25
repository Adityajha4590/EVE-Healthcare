from collections.abc import Generator

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_session_factory
from app.models.user import User

# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, ensuring it is closed after use."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the JWT from the Authorization header, load and return the user.

    Rejects requests with missing/invalid/expired tokens or inactive accounts.
    """
    if credentials is None:
        raise UnauthorizedException(detail="Not authenticated")

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(detail="Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException(detail="Invalid token")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedException(detail="User not found")

    if not user.is_active:
        raise UnauthorizedException(detail="Account is inactive")

    return user