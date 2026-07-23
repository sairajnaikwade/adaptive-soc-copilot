"""Tenant ORM model — root of the multi-tenant hierarchy."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.monitored_account import MonitoredAccount
    from app.models.report import Report


class Tenant(TimestampMixin, Base):
    """
    Represents an organization using the SOC CoPilot platform.

    Every other entity in the system belongs to exactly one tenant. All queries
    MUST filter by tenant_id to guarantee data isolation between organizations.

    Relationships:
        users              → The SOC analysts and admins for this organization.
        monitored_accounts → The accounts this organization is watching.
        reports            → Periodic security reports for this organization.
    """

    __tablename__ = "tenants"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique tenant identifier (UUID v4).",
    )

    # Organization name displayed in the dashboard
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Full organization name (e.g., 'Acme Corporation').",
    )

    # URL-safe unique identifier for the tenant (used in multi-tenant routing)
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="URL-safe unique identifier (e.g., 'acme-corp'). Auto-generated from name.",
    )

    # Soft-delete / suspension flag
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="False if the tenant has been suspended or offboarded.",
    )

    # ---------------------------------------------------------------------------
    # Relationships (back-populated from child models)
    # ---------------------------------------------------------------------------
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="select",
    )
    monitored_accounts: Mapped[List["MonitoredAccount"]] = relationship(
        "MonitoredAccount",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="select",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug='{self.slug}' active={self.is_active}>"
