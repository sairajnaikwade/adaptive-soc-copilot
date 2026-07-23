"""
Authentication endpoints.

Routes:
    POST /api/v1/auth/register  → Create new tenant + admin user
    POST /api/v1/auth/login     → Login and get JWT tokens
    POST /api/v1/auth/refresh   → Refresh access token
    GET  /api/v1/auth/me        → Get current authenticated user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_active_user
from app.core.exceptions import (
    DuplicateResourceError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TenantRegisterRequest,
    TokenResponse,
    UserMeResponse,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register new organization",
    description=(
        "Creates a new tenant (organization) and its first admin user. "
        "The admin can then create analyst accounts via the users endpoint."
    ),
    response_model=SuccessResponse[UserMeResponse],
)
def register(
    request: TenantRegisterRequest,
    db: Session = Depends(get_db),
) -> SuccessResponse[UserMeResponse]:
    """
    Register a new tenant + admin user.

    This is the entry point for new organizations joining the platform.
    After registration, the admin user is automatically authenticated —
    the response includes a JWT token pair in the data field.
    """
    service = AuthService(db)
    try:
        tenant, user, tokens = service.register_tenant_with_admin(request)
    except DuplicateResourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )

    return SuccessResponse(
        message=f"Organization '{tenant.name}' registered successfully. Welcome!",
        data=UserMeResponse.model_validate(user),
    )


@router.post(
    "/login",
    summary="Login",
    description=(
        "Authenticate with email and password. Returns a JWT access token "
        "(short-lived, 15 min) and a refresh token (long-lived, 7 days)."
    ),
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate using email + password (OAuth2 password flow).

    The `username` field of the OAuth2 form is used as the email address.
    The `tenant_id` is resolved from the user's own record.

    Note: In Sprint 1, login requires knowing the tenant_id. Future sprints
    will add email-domain → tenant resolution for a smoother login flow.
    The tenant_id can be passed as a query parameter or via a custom header.
    For now, we look up the user by email globally (first match).
    """
    from app.repositories.user_repository import UserRepository
    from sqlalchemy import select
    from app.models.user import User as UserModel

    # Find user by email globally (across all tenants — get first active match)
    stmt = select(UserModel).where(
        UserModel.email == form_data.username.lower(),
        UserModel.is_active == True,  # noqa: E712
    )
    user = db.execute(stmt).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = AuthService(db)
    try:
        _, tokens = service.login(
            email=form_data.username,
            password=form_data.password,
            tenant_id=user.tenant_id,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return tokens


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
    response_model=TokenResponse,
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Refresh a JWT access token using a valid refresh token."""
    service = AuthService(db)
    try:
        return service.refresh_access_token(request.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    summary="Get current user",
    description="Returns the profile of the currently authenticated user.",
    response_model=UserMeResponse,
)
def get_me(
    current_user: User = Depends(require_active_user),
) -> UserMeResponse:
    """Return the authenticated user's profile. Requires a valid access token."""
    return UserMeResponse.model_validate(current_user)
