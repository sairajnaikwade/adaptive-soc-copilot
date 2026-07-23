"""Pydantic schemas — exports all schema classes."""

from app.schemas.common import SuccessResponse, PaginatedResponse, ErrorResponse
from app.schemas.auth import (
    TenantRegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserMeResponse,
)
from app.schemas.tenant import TenantResponse, TenantUpdateRequest
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest

__all__ = [
    "SuccessResponse", "PaginatedResponse", "ErrorResponse",
    "TenantRegisterRequest", "LoginRequest", "TokenResponse",
    "RefreshTokenRequest", "UserMeResponse",
    "TenantResponse", "TenantUpdateRequest",
    "UserCreateRequest", "UserResponse", "UserUpdateRequest",
]
