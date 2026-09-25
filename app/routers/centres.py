"""Diagnostic catalogue routes — centres and tests."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.centre import CentreCreateRequest, CentreResponse
from app.schemas.test import TestCreateRequest, TestResponse
from app.services.centre import (
    create_centre,
    create_test,
    get_centre,
    get_test,
    list_centres,
    list_tests_for_centre,
)

router = APIRouter(tags=["catalogue"])


# ---------------------------------------------------------------------------
# Centres
# ---------------------------------------------------------------------------


@router.get(
    "/centres",
    response_model=list[CentreResponse],
    summary="List active diagnostic centres",
)
def list_centres_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list:
    return list_centres(db, page=page, page_size=page_size)


@router.get(
    "/centres/{centre_id}",
    response_model=CentreResponse,
    summary="Get a diagnostic centre by ID",
)
def get_centre_endpoint(centre_id: str, db: Session = Depends(get_db)):
    return get_centre(db, centre_id)


@router.get(
    "/centres/{centre_id}/tests",
    response_model=list[TestResponse],
    summary="List active tests at a centre",
)
def list_centre_tests_endpoint(
    centre_id: str, db: Session = Depends(get_db)
) -> list:
    return list_tests_for_centre(db, centre_id)


# ---------------------------------------------------------------------------
# Tests (direct access)
# ---------------------------------------------------------------------------


@router.get(
    "/tests/{test_id}",
    response_model=TestResponse,
    summary="Get a diagnostic test by ID",
)
def get_test_endpoint(test_id: str, db: Session = Depends(get_db)):
    return get_test(db, test_id)


# ---------------------------------------------------------------------------
# Seed / dev helpers (create resources)
# ---------------------------------------------------------------------------


@router.post(
    "/centres",
    response_model=CentreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic centre",
)
def create_centre_endpoint(
    body: CentreCreateRequest, db: Session = Depends(get_db)
):
    return create_centre(db, **body.model_dump())


@router.post(
    "/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic test",
)
def create_test_endpoint(
    body: TestCreateRequest, db: Session = Depends(get_db)
):
    return create_test(db, **body.model_dump())
