"""AuthEvent ORM model — authentication events (login, logout, MFA, etc.)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AuthEventType

if TYPE_CHECKING:
    from app.models.monitored_account import MonitoredAccount


class AuthEvent(Base):
    """
    A single authentication event ingested from a monitored system.

    Auth events are the primary signal for detecting compromised accounts
    (e.g., brute-force attacks via burst login failures) and insider threats
    (e.g., login from unusual geolocation or device).

    Note: No TimestampMixin — the event's own `timestamp` field IS the
    authoritative time. `created_at` (insertion time) is omitted to keep
    the table lean for high-volume ingestion.

    Indexed for efficient querying:
        (tenant_id, monitored_account_id, timestamp) → timeline lookups
        (tenant_id, event_type, timestamp) → threat pattern detection

    Relationships:
        monitored_account → The account that generated this event.
    """

    __tablename__ = "auth_events"

    __table_args__ = (
        # Composite index for per-account timeline queries (most common access pattern)
        Index(
            "ix_auth_events_tenant_account_time",
            "tenant_id", "monitored_account_id", "timestamp",
        ),
        # Index for event-type filtering across a tenant (detection queries)
        Index(
            "ix_auth_events_tenant_type_time",
            "tenant_id", "event_type", "timestamp",
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
    )

    # Account FK
    monitored_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Event classification
    event_type: Mapped[AuthEventType] = mapped_column(
        Enum(AuthEventType, name="autheventtype", create_type=False),
        nullable=False,
        doc="Classification of the authentication event.",
    )

    # Network context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),   # Supports both IPv4 (15 chars) and IPv6 (39 chars) + mapped
        nullable=True,
        doc="Source IP address of the authentication attempt.",
    )
    geo_location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Resolved geolocation string (e.g., 'Mumbai, India'). Set by ingestion API.",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        doc="HTTP User-Agent header from the authentication request.",
    )

    # Device fingerprint — used for device change detection
    device_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Opaque device fingerprint string from the monitored system.",
    )

    # Authoritative event timestamp (from the source system, not insertion time)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC timestamp when the event occurred in the monitored system.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    monitored_account: Mapped["MonitoredAccount"] = relationship(
        "MonitoredAccount", back_populates="auth_events",
    )

    def __repr__(self) -> str:
        return (
            f"<AuthEvent id={self.id} type={self.event_type} "
            f"ip='{self.ip_address}' ts={self.timestamp}>"
        )
