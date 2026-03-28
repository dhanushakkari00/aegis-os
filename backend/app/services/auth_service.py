"""Authentication service with password hashing and JWT tokens.

Provides user registration, login validation, and JWT token creation/verification.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
PBKDF2_ITERATIONS = 310_000


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return f"{salt}${key.hex()}"


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt, stored_key = hashed.split("$", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
        return hmac.compare_digest(key.hex(), stored_key)
    except (ValueError, AttributeError):
        return False


def _create_jwt(payload: dict[str, Any], secret: str, expires_hours: int = 72) -> str:
    """Create a simple JWT token (HS256)."""
    issued_at = int(time.time())
    header = _b64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"), sort_keys=True).encode()
    )
    body = _b64url_encode(
        json.dumps(
            {
                **payload,
                "exp": issued_at + expires_hours * 3600,
                "iat": issued_at,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    signature_input = f"{header}.{body}"
    sig = _b64url_encode(hmac.new(secret.encode(), signature_input.encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def _decode_jwt(token: str, secret: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token. Returns None if invalid or expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b, body_b, sig = parts
        header = json.loads(_b64url_decode(header_b))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            return None
        expected_sig = _b64url_encode(
            hmac.new(secret.encode(), f"{header_b}.{body_b}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(_b64url_decode(body_b))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, binascii.Error):
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
