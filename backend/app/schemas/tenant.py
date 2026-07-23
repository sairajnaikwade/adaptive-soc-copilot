"""Pydantic schemas for Tenant endpoints."""

import uuid
from typing import Optional
from pydantic import BaseModel, Field


class TenantResponse(BaseModel):
    """Response schema for tenant data."""

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool

    model_config = {"from_attributes": True}


class TenantUpdateRequest(BaseModel):
    """Request body for PATCH /api/v1/tenants/{id}."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
