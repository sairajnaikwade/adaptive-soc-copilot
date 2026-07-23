"""RuleDefinition ORM model — configurable risk classification rules."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import RiskTier, RuleConditionField, RuleConditionOperator

if TYPE_CHECKING:
    from app.models.rule_evaluation import RuleEvaluation


class RuleDefinition(TimestampMixin, Base):
    """
    A configurable rule used by the Rule Engine to classify detected threats.

    Rules define a condition over a numeric score field and assign a risk tier
    when the condition is met. Rules are evaluated in priority order; the first
    matching rule's risk_tier is applied.

    Example rules:
        Rule 1: trust_score < 30    → HIGH    (priority 1)
        Rule 2: confidence_score > 80 → HIGH  (priority 2)
        Rule 3: trust_score < 60    → MEDIUM  (priority 3)
        Rule 4: confidence_score > 50 → MEDIUM(priority 4)
        Rule 5: *                   → LOW     (default catch-all)

    Multi-tenancy:
        Each tenant can define custom rules. System-wide default rules have
        a special system tenant or are seeded via migration and shared.
        (In Sprint 5, tenant admins will manage their own rules via the API.)

    Relationships:
        evaluations → RuleEvaluation records where this rule was tested.
    """

    __tablename__ = "rule_definitions"

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

    # Human-readable rule metadata
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Short descriptive name (e.g., 'Critical Trust Drop').",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Full description of what this rule detects and why.",
    )

    # Rule condition: field OPERATOR value → risk_tier
    condition_field: Mapped[RuleConditionField] = mapped_column(
        Enum(RuleConditionField, name="ruleconditionfield", create_type=False),
        nullable=False,
        doc="The score field this rule evaluates.",
    )
    condition_operator: Mapped[RuleConditionOperator] = mapped_column(
        Enum(RuleConditionOperator, name="ruleconditionoperator", create_type=False),
        nullable=False,
        doc="Comparison operator (lt, gt, lte, gte, eq).",
    )
    condition_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Threshold value for the condition (e.g., 30.0 for trust_score < 30).",
    )

    # Output risk tier when this rule matches
    risk_tier: Mapped[RiskTier] = mapped_column(
        Enum(RiskTier, name="risktier", create_type=False),
        nullable=False,
        doc="Risk tier assigned when this rule's condition is satisfied.",
    )

    # Evaluation order (lower number = evaluated first)
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        doc="Evaluation order. Lower priority number = evaluated earlier.",
    )

    # Toggle without deletion
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        doc="False = this rule is skipped during evaluation.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    evaluations: Mapped[List["RuleEvaluation"]] = relationship(
        "RuleEvaluation", back_populates="rule_definition",
    )

    def __repr__(self) -> str:
        return (
            f"<RuleDefinition name='{self.name}' "
            f"condition='{self.condition_field} {self.condition_operator} {self.condition_value}' "
            f"→ {self.risk_tier} priority={self.priority}>"
        )
