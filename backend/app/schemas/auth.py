"""
Pydantic v2 schemas for authentication endpoints.

Covers:
    - Tenant registration + first admin user creation
    - User login (OAuth2 password flow)
    - Token response (access + refresh)
    - Token refresh
    - Current user response (me)
"""

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ===========================================================================
# Registration
# ===========================================================================

class TenantRegisterRequest(BaseModel):
    """Request body for POST /api/v1/auth/register — creates a tenant + admin user."""

    # Organization details
    tenant_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        examples=["Acme Corporation"],
        description="Full organization name. Used as display name in the dashboard.",
    )

    # Admin user details
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        examples=["Alice Sharma"],
        description="Full name of the initial admin user.",
    )
    email: EmailStr = Field(
        ...,
        examples=["alice@acme.com"],
        description="Email address for the admin account. Used for login.",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        examples=["SecurePass123!"],
        description="Password must be at least 8 characters.",
    )

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Enforce basic password strength requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


# ===========================================================================
# Login
# ===========================================================================

class LoginRequest(BaseModel):
    """Request body for POST /api/v1/auth/login."""

    email: EmailStr = Field(..., examples=["alice@acme.com"])
    password: str = Field(..., examples=["SecurePass123!"])


# ===========================================================================
# Token responses
# ===========================================================================

class TokenResponse(BaseModel):
    """Response returned on successful login or token refresh."""

    access_token: str = Field(..., description="Short-lived JWT access token (15 min default).")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token (7 days default).")
    token_type: str = Field(default="bearer", description="Always 'bearer'.")


class RefreshTokenRequest(BaseModel):
    """Request body for POST /api/v1/auth/refresh."""

    refresh_token: str = Field(..., description="A valid, non-expired refresh token.")


# ===========================================================================
# Current user response
# ===========================================================================

class UserMeResponse(BaseModel):
    """Response for GET /api/v1/auth/me — current authenticated user info."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
