"""ActivityEvent ORM model — user-activity events (file ops, API calls, config changes)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActivityEventType

if TYPE_CHECKING:
    from app.models.monitored_account import MonitoredAccount


class ActivityEvent(Base):
    """
    A single user-activity event ingested from a monitored system.

    Activity events capture what a monitored account DOES inside an application:
    downloading files, exporting data, changing privileges, calling APIs, etc.
    Combined with auth events, they form the full behavioral picture used
    by the Feature Extraction pipeline.

    JSONB metadata field:
        Stores event-type-specific context without requiring schema changes.
        Examples:
          FILE_DOWNLOAD  → {"file_path": "/reports/Q4.xlsx", "sensitivity": "high"}
          PRIVILEGE_CHANGE → {"from_role": "user", "to_role": "admin"}
          API_CALL       → {"endpoint": "/api/admin/users", "method": "DELETE"}

    Indexed for efficient querying:
        (tenant_id, monitored_account_id, timestamp) → timeline lookups
        (tenant_id, action_type, timestamp)           → threat pattern detection
    """

    __tablename__ = "activity_events"

    __table_args__ = (
        Index(
            "ix_activity_events_tenant_account_time",
            "tenant_id", "monitored_account_id", "timestamp",
        ),
        Index(
            "ix_activity_events_tenant_action_time",
            "tenant_id", "action_type", "timestamp",
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
    action_type: Mapped[ActivityEventType] = mapped_column(
        Enum(ActivityEventType, name="activityeventtype", create_type=False),
        nullable=False,
        doc="Classification of the user-activity event.",
    )

    # Resource being acted upon
    resource: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        doc="The resource identifier (file path, API endpoint, config key).",
    )

    # Resource size for volume-based anomaly detection (e.g., large data export)
    resource_size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Size of the resource in bytes (null if not applicable).",
    )

    # Flexible metadata for event-specific context (see docstring for examples)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB().with_variant(JSON, "sqlite"),
        nullable=True,
        doc="Event-type-specific metadata as JSONB. Schema validated at service layer.",
    )

    # Authoritative event timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC timestamp when the activity occurred in the monitored system.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    monitored_account: Mapped["MonitoredAccount"] = relationship(
        "MonitoredAccount", back_populates="activity_events",
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityEvent id={self.id} action={self.action_type} "
            f"resource='{self.resource}' ts={self.timestamp}>"
        )
