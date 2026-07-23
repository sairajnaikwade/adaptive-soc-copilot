"""
FastAPI dependency injection functions.

These are the building blocks of the Clean Architecture injection layer.
Every API endpoint receives its dependencies through FastAPI's Depends()
mechanism — never via global state.

Dependency chain:
    get_db              → yields a SQLAlchemy Session
    get_current_user    → validates JWT, returns User model
    require_active_user → ensures the user's account is active
    require_admin       → ensures the user holds the 'admin' role
    get_request_tenant  → returns the Tenant object for the current user
"""

import uuid
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TenantNotFoundError,
)
from app.core.security import decode_token
from app.db.session import SessionLocal

# ---------------------------------------------------------------------------
# OAuth2 scheme — FastAPI reads the Bearer token from the Authorization header
# tokenUrl must match the login endpoint path
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ===========================================================================
# Database session dependency
# ===========================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy database session for the duration of one request.

    The session is always closed in the finally block, even if an exception
    is raised inside the request handler. This prevents connection leaks.

    Usage:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===========================================================================
# Authentication dependencies
# ===========================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> "User":  # type: ignore[name-defined]  # noqa: F821
    """
    Validate the Bearer JWT token and return the corresponding User record.

    This is the primary authentication dependency. Import and use in any
    route that requires a logged-in user.

    Args:
        token: Bearer token extracted from the Authorization header.
        db: SQLAlchemy database session.

    Returns:
        The authenticated User ORM model instance.

    Raises:
        HTTPException 401: If the token is missing, expired, invalid, or the
                           user does not exist in the database.
    """
    # Import here to avoid circular imports (models → db → dependencies → models)
    from app.models.user import User
    from app.models.tenant import Tenant

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except InvalidTokenError:
        raise credentials_exception

    # Validate token type — only access tokens are accepted here
    token_type: str = payload.get("type", "")
    if token_type != "access":
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    tenant_id_str: str | None = payload.get("tenant_id")

    if not user_id_str or not tenant_id_str:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
        tenant_id = uuid.UUID(tenant_id_str)
    except ValueError:
        raise credentials_exception

    # Fetch user from database — always verify against DB, never trust token alone
    user: User | None = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == tenant_id)
        .first()
    )
    if user is None:
        raise credentials_exception

    return user


def require_active_user(
    current_user: "User" = Depends(get_current_user),  # type: ignore[name-defined]  # noqa: F821
) -> "User":  # type: ignore[name-defined]  # noqa: F821
    """
    Extend get_current_user to also verify the account is active.

    Use this instead of get_current_user for all non-trivial endpoints.

    Raises:
        HTTPException 403: If the user's account has been deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact your administrator.",
        )
    return current_user


def require_admin(
    current_user: "User" = Depends(require_active_user),  # type: ignore[name-defined]  # noqa: F821
) -> "User":  # type: ignore[name-defined]  # noqa: F821
    """
    Restrict an endpoint to users with the 'admin' role.

    Use this for tenant management, user creation, model retraining triggers,
    and any other privileged operations.

    Raises:
        HTTPException 403: If the user is not an admin.
    """
    from app.models.enums import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required for this operation.",
        )
    return current_user


def get_request_tenant(
    current_user: "User" = Depends(require_active_user),  # type: ignore[name-defined]  # noqa: F821
    db: Session = Depends(get_db),
) -> "Tenant":  # type: ignore[name-defined]  # noqa: F821
    """
    Resolve and return the Tenant record for the currently authenticated user.

    Use this dependency in any endpoint that needs to scope queries or
    operations to the requesting user's organization.

    Raises:
        HTTPException 404: If the tenant from the token no longer exists
                           (e.g., tenant was deleted after token was issued).
    """
    from app.models.tenant import Tenant

    tenant: Tenant | None = (
        db.query(Tenant)
        .filter(Tenant.id == current_user.tenant_id, Tenant.is_active == True)  # noqa: E712
        .first()
    )
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{current_user.tenant_id}' not found or has been deactivated.",
        )
    return tenant
