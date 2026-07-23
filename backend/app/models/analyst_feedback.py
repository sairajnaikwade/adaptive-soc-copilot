"""AnalystFeedback ORM model — analyst verdicts on detected threat events."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AnalystVerdict

if TYPE_CHECKING:
    from app.models.threat_event import ThreatEvent
    from app.models.user import User


class AnalystFeedback(TimestampMixin, Base):
    """
    An analyst's classification verdict on a detected threat event.

    Analyst feedback closes the loop between human expertise and automated AI.
    Verdicts (TRUE_POSITIVE, FALSE_POSITIVE, NEEDS_REVIEW) feed directly into
    the Continuous Improvement pipeline (Sprint 6) which uses them as labeled
    training samples to retrain and improve the ML models.

    Uniqueness:
        One analyst can only submit one feedback per threat event. If they need
        to change their verdict, the existing record is updated (not duplicated).
        Enforced by the unique constraint on (threat_event_id, analyst_id).

    Relationships:
        threat_event → The threat event being reviewed.
        analyst      → The SOC analyst who submitted this verdict.
    """

    __tablename__ = "analyst_feedback"

    __table_args__ = (
        UniqueConstraint(
            "threat_event_id", "analyst_id",
            name="uq_analyst_feedback_event_analyst",
        ),
        Index(
            "ix_analyst_feedback_threat_event_id",
            "threat_event_id",
        ),
        Index(
            "ix_analyst_feedback_tenant_verdict",
            "tenant_id", "verdict",
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

    # The threat event being reviewed
    threat_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threat_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The analyst who submitted this verdict
    analyst_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The analyst's verdict
    verdict: Mapped[AnalystVerdict] = mapped_column(
        Enum(AnalystVerdict, name="analystverdict", create_type=False),
        nullable=False,
        doc="Analyst's classification: true_positive / false_positive / needs_review.",
    )

    # Optional free-text notes explaining the verdict
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Analyst's reasoning or additional context for this verdict.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    threat_event: Mapped["ThreatEvent"] = relationship(
        "ThreatEvent", back_populates="feedbacks",
    )
    analyst: Mapped["User"] = relationship(
        "User",
        back_populates="feedbacks",
        foreign_keys=[analyst_id],
    )

    def __repr__(self) -> str:
        return (
            f"<AnalystFeedback event={self.threat_event_id} "
            f"analyst={self.analyst_id} verdict={self.verdict}>"
        )
