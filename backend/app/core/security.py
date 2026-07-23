"""
Security utilities — JWT token management and bcrypt password hashing.

Provides:
    - Password hashing and verification (bcrypt via Passlib)
    - JWT access token creation and decoding
    - JWT refresh token creation
    - Token payload extraction

All token operations use the SECRET_KEY and ALGORITHM from application settings.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

# ---------------------------------------------------------------------------
# Bcrypt password hashing context
# deprecated="auto" automatically upgrades weaker hashes on next login
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===========================================================================
# Password utilities
# ===========================================================================

import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash of a password."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


# ===========================================================================
# JWT token utilities
# ===========================================================================

def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    email: str,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: The user's UUID (stored in the 'sub' claim).
        tenant_id: The tenant UUID for multi-tenant scoping.
        role: The user's role ('admin' or 'analyst').
        email: The user's email address.
        extra_claims: Optional additional claims to embed in the token.

    Returns:
        A signed JWT access token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "email": email,
        "type": "access",
        "jti": str(uuid.uuid4()),  # Unique token ID for potential revocation
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, tenant_id: str) -> str:
    """
    Create a long-lived JWT refresh token.

    Refresh tokens contain only the minimal claims needed to issue new
    access tokens. They should be stored securely by the client.

    Args:
        subject: The user's UUID.
        tenant_id: The tenant UUID.

    Returns:
        A signed JWT refresh token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The raw JWT token string from the Authorization header.

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        InvalidTokenError: If the token is expired, malformed, or has an
                           invalid signature.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise InvalidTokenError(f"Token validation failed: {exc}") from exc


def extract_token_subject(token: str) -> str:
    """
    Extract the 'sub' (user UUID) claim from a token without full auth checks.

    Used internally by the dependency layer. Callers must still validate the
    token via decode_token() before trusting any claim.

    Args:
        token: The raw JWT token string.

    Returns:
        The subject (user UUID) string.

    Raises:
        InvalidTokenError: If the token is invalid or the 'sub' claim is missing.
    """
    payload = decode_token(token)
    subject: Optional[str] = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Token is missing the 'sub' claim.")
    return subject
