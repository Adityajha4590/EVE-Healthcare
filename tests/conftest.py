import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.dependencies import get_db
from app.main import create_app

# Use SQLite for unit/integration tests — no PostgreSQL dependency needed for test runs.
# When models use PostgreSQL-specific features (e.g. UUID columns), switch to a test PG instance.
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine. Tables are created once per test session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    # Clean up the test database file
    if os.path.exists("./test.db"):
        os.unlink("./test.db")


@pytest.fixture()
def db_session(test_engine):
    """Provide a transactional database session that rolls back after each test.

    This ensures complete test isolation with zero cleanup overhead.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session: Session):
    """Provide a FastAPI TestClient with the database dependency overridden."""
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client
