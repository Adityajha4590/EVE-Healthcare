"""Diagnostic centre service — business logic for centres and tests."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest


# ---------------------------------------------------------------------------
# Centres
# ---------------------------------------------------------------------------


def list_centres(
    db: Session, *, page: int = 1, page_size: int = 20, active_only: bool = True
) -> list[DiagnosticCentre]:
    """Return a paginated list of diagnostic centres."""
    query = db.query(DiagnosticCentre)
    if active_only:
        query = query.filter(DiagnosticCentre.is_active.is_(True))
    query = query.order_by(DiagnosticCentre.name)
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()


def get_centre(db: Session, centre_id: str) -> DiagnosticCentre:
    """Return a single centre by ID.

    Raises ``NotFoundException`` if not found.
    """
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.id == centre_id
    ).first()
    if centre is None:
        raise NotFoundException(detail="Diagnostic centre not found")
    return centre


def create_centre(db: Session, **kwargs) -> DiagnosticCentre:
    """Create a new diagnostic centre (development / seed use)."""
    centre = DiagnosticCentre(**kwargs)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def list_tests_for_centre(
    db: Session, centre_id: str, *, active_only: bool = True
) -> list[DiagnosticTest]:
    """Return all tests for a given centre.

    Raises ``NotFoundException`` if the centre does not exist.
    """
    centre = get_centre(db, centre_id)
    query = db.query(DiagnosticTest).filter(
        DiagnosticTest.centre_id == centre.id
    )
    if active_only:
        query = query.filter(DiagnosticTest.is_active.is_(True))
    return query.order_by(DiagnosticTest.name).all()


def get_test(db: Session, test_id: str) -> DiagnosticTest:
    """Return a single test by ID.

    Raises ``NotFoundException`` if not found.
    """
    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.id == test_id
    ).first()
    if test is None:
        raise NotFoundException(detail="Diagnostic test not found")
    return test


def create_test(db: Session, **kwargs) -> DiagnosticTest:
    """Create a new diagnostic test (development / seed use)."""
    test = DiagnosticTest(**kwargs)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test
