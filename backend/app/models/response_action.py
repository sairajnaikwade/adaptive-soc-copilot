"""ResponseAction ORM model — actions taken by the Adaptive Response Engine."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ResponseActionStatus, ResponseActionType

if TYPE_CHECKING:
    from app.models.threat_event import ThreatEvent


class ResponseAction(TimestampMixin, Base):
    """
    A record of one automated or manually triggered response action taken in
    reaction to a detected threat event.

    Multiple actions can be taken for a single threat event. For example, a HIGH
    risk event might trigger both BLOCK_ACCOUNT and REDIRECT_HONEYPOT actions.

    Action lifecycle:
        PENDING   → Created by the Response Engine
        EXECUTED  → Action was successfully applied to the monitored system
        FAILED    → Action attempted but failed (logged for retry / manual follow-up)
        REVERTED  → Analyst reversed the action (e.g., unblocked an account)

    executed_by:
        'system'    → Automated response (no human intervention)
        'analyst'   → Manually triggered or overridden by a SOC analyst

    Relationships:
        threat_event → The threat event that triggered this action.
    """

    __tablename__ = "response_actions"

    __table_args__ = (
        Index(
            "ix_response_actions_threat_event_id",
            "threat_event_id",
        ),
        Index(
            "ix_response_actions_tenant_status",
            "tenant_id", "status",
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

    # Parent threat event
    threat_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threat_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # What was done
    action_type: Mapped[ResponseActionType] = mapped_column(
        Enum(ResponseActionType, name="responseactiontype", create_type=False),
        nullable=False,
        doc="The type of response action executed.",
    )

    # Execution state
    status: Mapped[ResponseActionStatus] = mapped_column(
        Enum(ResponseActionStatus, name="responseactionstatus", create_type=False),
        nullable=False,
        default=ResponseActionStatus.PENDING,
        doc="Current execution status of this action.",
    )

    # Who triggered it ("system" or user UUID as string)
    executed_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="system",
        server_default="system",
        doc="'system' for automated actions, or a user UUID string for analyst overrides.",
    )

    # Free-text notes (reason for manual override, failure details, etc.)
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes explaining why this action was taken or reverted.",
    )

    # Execution timestamp
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the action was actually applied (null if still pending).",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    threat_event: Mapped["ThreatEvent"] = relationship(
        "ThreatEvent", back_populates="response_actions",
    )

    def __repr__(self) -> str:
        return (
            f"<ResponseAction id={self.id} type={self.action_type} "
            f"status={self.status} by='{self.executed_by}'>"
        )
