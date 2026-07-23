"""Tenant repository — data access layer for the Tenant model."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Data access layer for Tenant entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(Tenant, db)

    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Fetch a tenant by its unique URL slug."""
        stmt = select(Tenant).where(Tenant.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_active(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """Fetch an active tenant by ID. Returns None if tenant is deactivated."""
        stmt = select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.is_active == True,  # noqa: E712
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def slug_exists(self, slug: str) -> bool:
        """Check if a slug is already taken by another tenant."""
        return self.get_by_slug(slug) is not None

    def create_tenant(self, name: str, slug: str) -> Tenant:
        """
        Create a new tenant with the given name and slug.

        Args:
            name: Organization display name.
            slug: URL-safe unique identifier.

        Returns:
            The newly created Tenant instance.
        """
        return self.create({"name": name, "slug": slug, "is_active": True})
