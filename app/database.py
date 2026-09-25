from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Lazily create and return the SQLAlchemy engine.

    Engine is created on first call, then cached. This avoids connection
    attempts at import time, which would break tests that override the DB.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory, creating it lazily if needed."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass
