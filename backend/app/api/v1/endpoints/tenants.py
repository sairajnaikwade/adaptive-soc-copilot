"""
Tenant management endpoints.

Routes:
    GET   /api/v1/tenants/me             → Get current user's tenant info
    GET   /api/v1/tenants/{tenant_id}    → Get tenant by ID (admin only)
    PATCH /api/v1/tenants/{tenant_id}    → Update tenant (admin only)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_request_tenant, require_active_user, require_admin
from app.core.exceptions import ResourceNotFoundError
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.tenant import TenantResponse, TenantUpdateRequest
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get(
    "/me",
    summary="Get my organization",
    description="Returns the tenant (organization) of the currently authenticated user.",
    response_model=TenantResponse,
)
def get_my_tenant(
    tenant: Tenant = Depends(get_request_tenant),
) -> TenantResponse:
    """Return the current user's organization details."""
    return TenantResponse.model_validate(tenant)


@router.get(
    "/{tenant_id}",
    summary="Get tenant by ID",
    description="Fetch a specific tenant by ID. Restricted to admin users.",
    response_model=TenantResponse,
)
def get_tenant(
    tenant_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> TenantResponse:
    """Admin-only: fetch any tenant by its UUID."""
    service = TenantService(db)
    try:
        tenant = service.get_tenant_by_id(tenant_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return TenantResponse.model_validate(tenant)


@router.patch(
    "/{tenant_id}",
    summary="Update tenant",
    description="Update tenant display name or active status. Restricted to admin users.",
    response_model=SuccessResponse[TenantResponse],
)
def update_tenant(
    tenant_id: uuid.UUID,
    request: TenantUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[TenantResponse]:
    """Admin-only: update tenant name or active state."""
    service = TenantService(db)
    try:
        tenant = service.update_tenant(
            tenant_id=tenant_id,
            name=request.name,
            is_active=request.is_active,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

    return SuccessResponse(
        message="Tenant updated successfully.",
        data=TenantResponse.model_validate(tenant),
    )
