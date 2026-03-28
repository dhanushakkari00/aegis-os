"""Authentication service with password hashing and JWT tokens.

Provides user registration, login validation, and JWT token creation/verification.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import base64
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)


def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = uuid.uuid4().hex
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${key.hex()}"


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt, stored_key = hashed.split("$", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return hmac.compare_digest(key.hex(), stored_key)
    except (ValueError, AttributeError):
        return False


def _create_jwt(payload: dict[str, Any], secret: str, expires_hours: int = 72) -> str:
    """Create a simple JWT token (HS256)."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload["exp"] = int(time.time()) + expires_hours * 3600
    payload["iat"] = int(time.time())
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature_input = f"{header}.{body}"
    sig = hmac.new(secret.encode(), signature_input.encode(), hashlib.sha256).hexdigest()
    return f"{header}.{body}.{sig}"


def _decode_jwt(token: str, secret: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token. Returns None if invalid or expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b, body_b, sig = parts
        expected_sig = hmac.new(secret.encode(), f"{header_b}.{body_b}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        # Pad base64
        body_padded = body_b + "=" * (4 - len(body_b) % 4)
        payload = json.loads(base64.urlsafe_b64decode(body_padded))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


class AuthService:
    """Handles user registration, login, and token management."""

    def __init__(self, settings: Settings) -> None:
        self.secret = settings.secret_key

    def register(self, db: Session, *, email: str, username: str, password: str) -> User:
        """Register a new user. Raises ValueError if email/username exists."""
        existing = db.query(User).filter((User.email == email) | (User.username == username)).first()
        if existing:
            if existing.email == email:
                raise ValueError("Email already registered.")
            raise ValueError("Username already taken.")

        user = User(
            email=email,
            username=username,
            hashed_password=_hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("User registered: %s", email)
        return user

    def login(self, db: Session, *, email: str, password: str) -> tuple[User, str]:
        """Validate credentials and return (user, jwt_token). Raises ValueError on failure."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not _verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        token = _create_jwt({"sub": user.id, "email": user.email, "username": user.username}, self.secret)
        logger.info("User logged in: %s", email)
        return user, token

    def get_current_user(self, db: Session, token: str) -> User | None:
        """Decode the token and return the user, or None if invalid."""
        payload = _decode_jwt(token, self.secret)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id).first()
