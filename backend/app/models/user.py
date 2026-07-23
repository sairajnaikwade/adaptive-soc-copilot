"""User ORM model — SOC analysts and tenant administrators."""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.analyst_feedback import AnalystFeedback
    from app.models.report import Report
    from app.models.retraining_run import RetrainingRun


class User(TimestampMixin, Base):
    """
    A SOC platform user — either a tenant admin or an analyst.

    Users are scoped to a single tenant. The first user created for a tenant
    is assigned the ADMIN role; subsequent users are ANALYST by default.

    Security notes:
        - Passwords are NEVER stored as plain text. Only bcrypt hashes.
        - The hashed_password field is excluded from all Pydantic response schemas.
        - is_active=False soft-deletes the user without removing audit history.

    Relationships:
        tenant          → The organization this user belongs to.
        feedbacks       → Analyst feedback records submitted by this user.
        reports         → Reports this user generated on-demand.
        retraining_runs → Model retraining runs triggered by this user.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique user identifier.",
    )

    # Multi-tenancy scoping
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the tenant this user belongs to.",
    )

    # Identity
    email: Mapped[str] = mapped_column(
        String(320),   # RFC 5321 max email length
        nullable=False,
        index=True,
        doc="User's email address. Unique within the tenant (enforced at DB level).",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User's display name shown in the dashboard.",
    )

    # Security — NEVER expose in API responses
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="bcrypt hash of the user's password. Never returned in API responses.",
    )

    # Authorization
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", create_type=False),
        nullable=False,
        default=UserRole.ANALYST,
        doc="User's role within the tenant. Controls endpoint access.",
    )

    # Account state
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="False when the account is deactivated. Preserves audit history.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")

    feedbacks: Mapped[List["AnalystFeedback"]] = relationship(
        "AnalystFeedback",
        back_populates="analyst",
        foreign_keys="AnalystFeedback.analyst_id",
        lazy="select",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="generated_by_user",
        foreign_keys="Report.generated_by",
        lazy="select",
    )
    retraining_runs: Mapped[List["RetrainingRun"]] = relationship(
        "RetrainingRun",
        back_populates="triggered_by_user",
        foreign_keys="RetrainingRun.triggered_by_user_id",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role={self.role}>"
