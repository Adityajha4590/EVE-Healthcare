"""Authentication routes — signup, login, and current-user retrieval."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> User:
    """Create a new user account.

    Returns the created user's public information (never the password hash).
    """
    return create_user(db, email=body.email, password=body.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain an access token",
)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """Authenticate with email and password, returning a signed JWT."""
    user = authenticate_user(db, email=body.email, password=body.password)
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's public profile."""
    return current_user
