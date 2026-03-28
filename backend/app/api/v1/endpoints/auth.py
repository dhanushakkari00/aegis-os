"""Authentication API endpoints.

Provides signup, login, logout, and current user info endpoints.
No OTP verification — simple email/password authentication with JWT tokens.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.auth_service import AuthService

router = APIRouter()
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    """Request body for user registration."""

    email: str
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid email address.")
        return normalized


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid email address.")
        return normalized


class AuthResponse(BaseModel):
    """Response containing user info and JWT token."""

    id: str
    email: str
    username: str
    token: str


class UserResponse(BaseModel):
    """Response with current user info."""

    id: str
    email: str
    username: str


def get_auth_service() -> AuthService:
    """Return an AuthService instance."""
    return AuthService(get_settings())


def get_current_user_dep(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Dependency to extract and verify the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    return UserResponse(id=user.id, email=user.email, username=user.username)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(
    body: SignupRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Register a new user account."""
    try:
        user = auth_service.register(
            db, email=body.email, username=body.username, password=body.password
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    _, token = auth_service.login(db, email=body.email, password=body.password)
    return AuthResponse(id=user.id, email=user.email, username=user.username, token=token)


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Log in with email and password."""
    try:
        user, token = auth_service.login(db, email=body.email, password=body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return AuthResponse(id=user.id, email=user.email, username=user.username, token=token)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: UserResponse = Depends(get_current_user_dep),
) -> UserResponse:
    """Get the current authenticated user's profile."""
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout() -> dict[str, str]:
    """Log out (client-side token discard). Stateless — just acknowledges."""
    return {"detail": "Logged out successfully. Discard the token on the client."}
