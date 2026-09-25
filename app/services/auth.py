"""Authentication service — business logic for signup and login."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models.user import User

logger = get_logger(__name__)


def create_user(db: Session, email: str, password: str) -> User:
    """Register a new user.

    Raises ``ConflictException`` if the email is already registered.
    """
    normalized_email = email.strip().lower()

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("signup_duplicate_email", email=normalized_email)
        raise ConflictException(detail="A user with this email already exists")

    db.refresh(user)
    logger.info("user_created", user_id=user.id, email=normalized_email)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Validate credentials and return the user.

    Uses a single generic error message regardless of whether the email
    or the password was incorrect to prevent user-enumeration attacks.

    Raises ``UnauthorizedException`` on failure.
    """
    normalized_email = email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedException(detail="Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException(detail="Account is inactive")

    return user
