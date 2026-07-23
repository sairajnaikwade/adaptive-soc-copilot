"""Pydantic schemas for User management endpoints."""

import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreateRequest(BaseModel):
    """Request for admin to create a new analyst within the same tenant."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="analyst", pattern="^(admin|analyst)$")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserResponse(BaseModel):
    """Response schema for user data (never includes hashed_password)."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Request for updating user profile."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
