"""MonitoredAccount ORM model — the entity being tracked for anomalous behavior."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import MonitoredAccountStatus

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.auth_event import AuthEvent
    from app.models.activity_event import ActivityEvent
    from app.models.feature_vector import FeatureVector
    from app.models.threat_event import ThreatEvent
    from app.models.honeypot_session import HoneypotSession


class MonitoredAccount(TimestampMixin, Base):
    """
    Represents an account (employee, service account, etc.) being monitored
    by the SOC CoPilot platform.

    This is NOT a platform user — it is an external account from the
    tenant's own system. The platform ingests events for this account and
    tracks their behavioral baseline via the Trust Score.

    Design notes:
        - external_user_id is the account's ID in the monitored system (opaque string).
        - current_trust_score is updated in real-time by the Trust Score Engine.
        - status is updated by the Adaptive Response Engine.
        - Unique constraint on (tenant_id, external_user_id) prevents duplicate registration.

    Relationships:
        auth_events     → Authentication events for this account.
        activity_events → User-activity events for this account.
        feature_vectors → Computed behavioral feature windows.
        threat_events   → Detected threats associated with this account.
        honeypot_sessions → Honeypot sessions if the account was redirected.
    """

    __tablename__ = "monitored_accounts"

    # Composite unique constraint: same external_user_id cannot appear twice per tenant
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "external_user_id",
            name="uq_monitored_accounts_tenant_external_user",
        ),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Multi-tenancy scoping
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Account identification in the monitored system
    external_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Account ID in the tenant's own system (e.g., AD GUID, LDAP DN, email).",
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable username displayed in the SOC dashboard.",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(320),
        nullable=True,
        doc="Account's email (optional — used for email notifications).",
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Organizational department (used for peer-group baselining in future sprints).",
    )

    # Trust Score — maintained by the Trust Score Engine (Sprint 4)
    current_trust_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
        server_default="100.0",
        doc="Rolling trust score (0–100). Higher = more trustworthy.",
    )

    # Operational status — updated by the Adaptive Response Engine (Sprint 5)
    status: Mapped[MonitoredAccountStatus] = mapped_column(
        Enum(MonitoredAccountStatus, name="monitoredaccountstatus", create_type=False),
        nullable=False,
        default=MonitoredAccountStatus.ACTIVE,
        index=True,
        doc="Current operational status set by the Response Engine.",
    )

    # Last activity timestamp
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of the most recent event for this account.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="monitored_accounts")

    auth_events: Mapped[List["AuthEvent"]] = relationship(
        "AuthEvent", back_populates="monitored_account", cascade="all, delete-orphan",
    )
    activity_events: Mapped[List["ActivityEvent"]] = relationship(
        "ActivityEvent", back_populates="monitored_account", cascade="all, delete-orphan",
    )
    feature_vectors: Mapped[List["FeatureVector"]] = relationship(
        "FeatureVector", back_populates="monitored_account", cascade="all, delete-orphan",
    )
    threat_events: Mapped[List["ThreatEvent"]] = relationship(
        "ThreatEvent", back_populates="monitored_account", cascade="all, delete-orphan",
    )
    honeypot_sessions: Mapped[List["HoneypotSession"]] = relationship(
        "HoneypotSession", back_populates="monitored_account", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<MonitoredAccount id={self.id} username='{self.username}' "
            f"trust={self.current_trust_score:.1f} status={self.status}>"
        )
