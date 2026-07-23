"""Tenant service — business logic for tenant management."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.tenant import Tenant
from app.repositories.tenant_repository import TenantRepository

logger = get_logger(__name__)


class TenantService:
    """Service for tenant administration operations."""

    def __init__(self, db: Session) -> None:
        self._repo = TenantRepository(db)

    def get_tenant_by_id(self, tenant_id: uuid.UUID) -> Tenant:
        """
        Fetch a tenant by ID.

        Raises:
            ResourceNotFoundError: If the tenant does not exist.
        """
        tenant = self._repo.get_by_id(tenant_id)
        if tenant is None:
            raise ResourceNotFoundError("Tenant", tenant_id)
        return tenant

    def update_tenant(
        self, tenant_id: uuid.UUID, name: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Tenant:
        """
        Update tenant fields.

        Args:
            tenant_id: ID of the tenant to update.
            name: New display name (optional).
            is_active: New active state (optional).

        Returns:
            The updated Tenant instance.
        """
        tenant = self.get_tenant_by_id(tenant_id)
        updates = {}
        if name is not None:
            updates["name"] = name
        if is_active is not None:
            updates["is_active"] = is_active

        if updates:
            tenant = self._repo.update(tenant, updates)
            logger.info("Tenant updated | tenant_id=%s fields=%s", tenant_id, list(updates.keys()))

        return tenant
