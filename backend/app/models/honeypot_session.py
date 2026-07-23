"""HoneypotSession ORM model — a decoy environment session for high-risk actors."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.threat_event import ThreatEvent
    from app.models.monitored_account import MonitoredAccount


class HoneypotSession(TimestampMixin, Base):
    """
    Tracks a high-risk actor's session within the honeypot environment.

    When the Adaptive Response Engine assigns REDIRECT_HONEYPOT, the monitored
    account is silently routed to a simulated decoy system. Every action the
    attacker takes inside the honeypot is logged in session_log for forensic
    analysis.

    session_log structure (JSONB array of action records):
        [
          {
            "timestamp": "2026-07-23T21:00:00Z",
            "action": "file_access",
            "resource": "/etc/passwd",
            "ip": "192.168.1.100"
          },
          ...
        ]

    Design note:
        session_log uses JSONB because honeypot actions are highly variable
        and forensically collected — we don't want schema migrations to limit
        what we can capture. This is a justified use of JSONB (unlike replacing
        normalized feature tables).
    """

    __tablename__ = "honeypot_sessions"

    __table_args__ = (
        Index(
            "ix_honeypot_sessions_threat_event_id",
            "threat_event_id",
        ),
        Index(
            "ix_honeypot_sessions_tenant_active",
            "tenant_id", "is_active",
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

    # Source threat event that triggered the honeypot redirect
    threat_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threat_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The monitored account that was redirected
    monitored_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Network context
    attacker_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of the attacker at the time of redirection.",
    )

    # Honeypot session token (used to identify requests within the decoy env)
    session_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Opaque session token passed to the honeypot to correlate requests.",
    )

    # URL of the honeypot the attacker was redirected to
    decoy_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        doc="URL of the honeypot environment the attacker was sent to.",
    )

    # Session activity log (JSONB — see docstring for structure)
    session_log: Mapped[Optional[list]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=True,
        default=list,
        doc="JSON array of attacker actions captured inside the honeypot.",
    )

    # Active / ended state
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="True while the attacker is still in the honeypot session.",
    )

    # Timestamps
    redirected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC timestamp when the attacker was redirected to the honeypot.",
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the honeypot session ended (null if still active).",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    threat_event: Mapped["ThreatEvent"] = relationship(
        "ThreatEvent", back_populates="honeypot_sessions",
    )
    monitored_account: Mapped["MonitoredAccount"] = relationship(
        "MonitoredAccount", back_populates="honeypot_sessions",
    )

    def __repr__(self) -> str:
        return (
            f"<HoneypotSession id={self.id} "
            f"account={self.monitored_account_id} active={self.is_active}>"
        )
