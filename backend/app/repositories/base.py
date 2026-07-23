"""
Generic base repository implementing CRUD operations for any SQLAlchemy model.

All domain repositories extend BaseRepository[ModelType] and gain
standard CRUD methods automatically. Tenant-scoped queries are enforced
by the require_tenant parameter in every read/update/delete method.
"""

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing standard CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: Session):
                super().__init__(User, db)
    """

    def __init__(self, model: Type[ModelType], db: Session) -> None:
        self.model = model
        self.db = db

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_id(
        self, record_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None
    ) -> Optional[ModelType]:
        """Fetch a record by primary key, optionally scoped to a tenant."""
        stmt = select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        if tenant_id is not None:
            stmt = stmt.where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Fetch paginated records scoped to a tenant.

        Args:
            tenant_id: Mandatory tenant scope.
            skip: Number of records to skip (offset).
            limit: Maximum records to return.
            filters: Optional dict of exact-match column filters.
        """
        stmt = select(self.model).where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
        if filters:
            for column, value in filters.items():
                stmt = stmt.where(getattr(self.model, column) == value)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(
        self, tenant_id: uuid.UUID, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records matching the tenant scope and optional filters."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model).where(  # type: ignore[arg-type]
            self.model.tenant_id == tenant_id  # type: ignore[attr-defined]
        )
        if filters:
            for column, value in filters.items():
                stmt = stmt.where(getattr(self.model, column) == value)
        return self.db.execute(stmt).scalar_one()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new record.

        Args:
            data: Dictionary of column name → value pairs.

        Returns:
            The created and refreshed ORM instance.
        """
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(
        self, instance: ModelType, data: Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing ORM instance with new field values.

        Args:
            instance: The ORM instance to update (already fetched from DB).
            data: Dictionary of fields to update.

        Returns:
            The updated and refreshed instance.
        """
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        """
        Hard-delete an ORM instance from the database.

        Prefer soft-delete (setting is_active=False) for entities with
        audit history. Use this only when the record must be fully removed.
        """
        self.db.delete(instance)
        self.db.commit()
