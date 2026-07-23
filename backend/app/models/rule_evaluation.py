"""RuleEvaluation ORM model — record of a rule being evaluated against a threat event."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RiskTier, RuleEvaluationResult

if TYPE_CHECKING:
    from app.models.threat_event import ThreatEvent
    from app.models.rule_definition import RuleDefinition


class RuleEvaluation(Base):
    """
    An audit record of one rule being evaluated against one threat event.

    All active rules are evaluated for every threat event, and all outcomes
    (matched or not_matched) are stored here for full audit trail. This allows:
        - Debugging why a specific risk_tier was assigned
        - Reporting on which rules fire most frequently
        - Tuning rule priorities based on match statistics

    Note: `risk_tier_assigned` is only set when `result == MATCHED`.
          The Rule Engine picks the highest-priority matching rule's tier
          and stores it as the ThreatEvent.risk_tier.
    """

    __tablename__ = "rule_evaluations"

    __table_args__ = (
        Index(
            "ix_rule_evaluations_threat_event_id",
            "threat_event_id",
        ),
        Index(
            "ix_rule_evaluations_tenant_rule",
            "tenant_id", "rule_definition_id",
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

    # Parent threat event
    threat_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threat_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Which rule was evaluated
    rule_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rule_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Evaluation outcome
    result: Mapped[RuleEvaluationResult] = mapped_column(
        Enum(RuleEvaluationResult, name="ruleevaluationresult", create_type=False),
        nullable=False,
        doc="Whether this rule's condition was satisfied.",
    )

    # Risk tier assigned (only meaningful when result == MATCHED)
    risk_tier_assigned: Mapped[RiskTier | None] = mapped_column(
        Enum(RiskTier, name="risktier", create_type=False),
        nullable=True,
        doc="Risk tier this rule would assign. Null when rule did not match.",
    )

    # Evaluation timestamp
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC timestamp when this rule was evaluated.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    threat_event: Mapped["ThreatEvent"] = relationship(
        "ThreatEvent", back_populates="rule_evaluations",
    )
    rule_definition: Mapped["RuleDefinition"] = relationship(
        "RuleDefinition", back_populates="evaluations",
    )

    def __repr__(self) -> str:
        return (
            f"<RuleEvaluation threat={self.threat_event_id} "
            f"rule={self.rule_definition_id} result={self.result}>"
        )
