"""
Authentication service — tenant registration, login, and token management.

Implements the business logic layer between the API endpoints and the
data access (repository) layer. This service never directly touches the
database; it delegates all DB operations to TenantRepository and UserRepository.
"""

import re
import uuid
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DuplicateResourceError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.enums import UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TenantRegisterRequest, TokenResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _generate_slug(name: str) -> str:
    """
    Generate a URL-safe slug from an organization name.

    Examples:
        "Acme Corporation" → "acme-corporation"
        "SecureOps Ltd."   → "secureops-ltd"
    """
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)   # Remove special chars
    slug = re.sub(r"[\s_]+", "-", slug)     # Replace spaces/underscores with hyphens
    slug = re.sub(r"-+", "-", slug)          # Collapse multiple hyphens
    return slug.strip("-")


class AuthService:
    """
    Service class for all authentication and authorization operations.

    Follows the Dependency Injection pattern — a Session is injected at
    construction time rather than imported as a global.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._tenant_repo = TenantRepository(db)
        self._user_repo = UserRepository(db)

    # -----------------------------------------------------------------------
    # Tenant + Admin Registration
    # -----------------------------------------------------------------------

    def register_tenant_with_admin(
        self, request: TenantRegisterRequest
    ) -> Tuple[Tenant, User, TokenResponse]:
        """
        Create a new tenant and its first admin user in a single transaction.

        Process:
            1. Generate a unique slug from the tenant name.
            2. Check for duplicate slug — raise 409 if taken.
            3. Create the Tenant record.
            4. Hash the password.
            5. Create the User record with role=ADMIN.
            6. Issue JWT tokens for immediate login after registration.

        Args:
            request: Validated TenantRegisterRequest payload.

        Returns:
            Tuple of (Tenant, User, TokenResponse).

        Raises:
            DuplicateResourceError: If the derived tenant slug is already taken.
        """
        slug = _generate_slug(request.tenant_name)

        # Ensure slug uniqueness — append a 4-char UUID fragment if already taken
        if self._tenant_repo.slug_exists(slug):
            slug = f"{slug}-{str(uuid.uuid4())[:4]}"

        logger.info("Registering new tenant | name='%s' slug='%s'", request.tenant_name, slug)

        # Create tenant
        tenant = self._tenant_repo.create_tenant(
            name=request.tenant_name,
            slug=slug,
        )

        # Hash password
        hashed_password = get_password_hash(request.password)

        # Create first admin user
        admin_user = self._user_repo.create_user(
            tenant_id=tenant.id,
            email=request.email,
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
        )

        logger.info(
            "Tenant registered | tenant_id=%s admin_user_id=%s email='%s'",
            tenant.id,
            admin_user.id,
            admin_user.email,
        )

        # Issue tokens for immediate dashboard access
        tokens = self._issue_tokens(admin_user)
        return tenant, admin_user, tokens

    # -----------------------------------------------------------------------
    # Login
    # -----------------------------------------------------------------------

    def login(self, email: str, password: str, tenant_id: uuid.UUID) -> Tuple[User, TokenResponse]:
        """
        Authenticate a user and return JWT tokens.

        Note: tenant_id must be resolved before calling this method. In practice,
        the login endpoint accepts email + password and resolves tenant from
        the email domain or a tenant header (future enhancement). For Sprint 1,
        tenant is resolved from the JWT or request body.

        Raises:
            InvalidCredentialsError: If email not found or password doesn't match.
        """
        user = self._user_repo.get_by_email_and_tenant(email, tenant_id)

        if user is None or not verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt | email='%s' tenant=%s", email, tenant_id)
            raise InvalidCredentialsError(
                "Invalid email or password. Please check your credentials and try again."
            )

        if not user.is_active:
            raise InvalidCredentialsError(
                "This account has been deactivated. Please contact your administrator."
            )

        logger.info("Successful login | user_id=%s tenant_id=%s", user.id, user.tenant_id)
        tokens = self._issue_tokens(user)
        return user, tokens

    # -----------------------------------------------------------------------
    # Token refresh
    # -----------------------------------------------------------------------

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Validate a refresh token and issue a new access token.

        Args:
            refresh_token: A valid, non-expired refresh token.

        Returns:
            New TokenResponse with a fresh access token and the same refresh token.

        Raises:
            InvalidTokenError: If the refresh token is invalid, expired, or wrong type.
        """
        try:
            payload = decode_token(refresh_token)
        except InvalidTokenError:
            raise

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Provided token is not a refresh token.")

        user_id_str: str = payload.get("sub", "")
        tenant_id_str: str = payload.get("tenant_id", "")

        try:
            user_id = uuid.UUID(user_id_str)
            tenant_id = uuid.UUID(tenant_id_str)
        except ValueError as exc:
            raise InvalidTokenError("Token contains invalid UUID claims.") from exc

        user = self._user_repo.get_by_id(user_id, tenant_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("User associated with this token no longer exists.")

        new_access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role.value,
            email=user.email,
        )
        logger.debug("Access token refreshed | user_id=%s", user_id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Return the same refresh token
            token_type="bearer",
        )

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _issue_tokens(self, user: User) -> TokenResponse:
        """Create and return a fresh access + refresh token pair for a user."""
        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role.value,
            email=user.email,
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
