"""User repository — data access layer for the User model."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access layer for User entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email_and_tenant(
        self, email: str, tenant_id: uuid.UUID
    ) -> Optional[User]:
        """
        Fetch a user by email within a specific tenant.

        Email uniqueness is scoped per-tenant: the same email can exist in
        different tenants (different organizations).
        """
        stmt = select(User).where(
            User.email == email.lower(),
            User.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def email_exists_in_tenant(self, email: str, tenant_id: uuid.UUID) -> bool:
        """Check if an email is already registered within a tenant."""
        return self.get_by_email_and_tenant(email, tenant_id) is not None

    def tenant_has_any_user(self, tenant_id: uuid.UUID) -> bool:
        """Check if a tenant already has at least one user registered."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(User).where(
            User.tenant_id == tenant_id
        )
        count: int = self.db.execute(stmt).scalar_one()
        return count > 0

    def create_user(
        self,
        tenant_id: uuid.UUID,
        email: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.ANALYST,
    ) -> User:
        """
        Create a new user within a tenant.

        Args:
            tenant_id: The tenant this user belongs to.
            email: Email address (lowercased before storage).
            full_name: Display name.
            hashed_password: bcrypt hash of the user's password.
            role: UserRole.ADMIN or UserRole.ANALYST.

        Returns:
            The newly created User instance.
        """
        return self.create({
            "tenant_id": tenant_id,
            "email": email.lower(),
            "full_name": full_name,
            "hashed_password": hashed_password,
            "role": role,
            "is_active": True,
        })
