from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database import get_session_factory


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, ensuring it is closed after use."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
