"""ThreatEvent ORM model — a detected anomaly with full scoring and response state."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import RiskTier, ThreatEventStatus

if TYPE_CHECKING:
    from app.models.monitored_account import MonitoredAccount
    from app.models.feature_vector import FeatureVector
    from app.models.ml_model import MLModel
    from app.models.shap_contribution import SHAPContribution
    from app.models.rule_evaluation import RuleEvaluation
    from app.models.response_action import ResponseAction
    from app.models.honeypot_session import HoneypotSession
    from app.models.analyst_feedback import AnalystFeedback


class ThreatEvent(TimestampMixin, Base):
    """
    The central entity in the detection pipeline — a scored and classified
    anomalous behavioral event.

    A ThreatEvent is created when the ML pipeline identifies an anomaly in a
    FeatureVector. It carries all scoring data and links to the explanation
    (SHAP), rule evaluations, response actions, and analyst feedback.

    Score fields:
        anomaly_score    → Raw output from the ML model (-1 to 0 for IF; negative = more anomalous)
        trust_score      → Processed 0–100 score (100 = fully trusted)
        confidence_score → 0–100% confidence that this is a real threat

    Lifecycle:
        OPEN → ACKNOWLEDGED → RESOLVED (or FALSE_POSITIVE)

    Dashboard performance indexes:
        (tenant_id, risk_tier, detected_at) → dashboard filters
        (tenant_id, status, detected_at)    → open alerts feed
    """

    __tablename__ = "threat_events"

    __table_args__ = (
        Index(
            "ix_threat_events_tenant_tier_time",
            "tenant_id", "risk_tier", "detected_at",
        ),
        Index(
            "ix_threat_events_tenant_status_time",
            "tenant_id", "status", "detected_at",
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

    # Source links
    monitored_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_vector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_vectors.id", ondelete="RESTRICT"),
        nullable=False,
        doc="The feature vector that triggered this threat detection.",
    )
    ml_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="RESTRICT"),
        nullable=False,
        doc="The ML model that scored this feature vector.",
    )

    # ML Scores
    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Raw anomaly score from the ML model. More negative = more anomalous.",
    )
    trust_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Processed trust score (0–100). 100 = fully trusted, 0 = maximum threat.",
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Threat confidence percentage (0–100). How confident the system is this is a threat.",
    )

    # Rule Engine output
    risk_tier: Mapped[RiskTier] = mapped_column(
        Enum(RiskTier, name="risktier", create_type=False),
        nullable=False,
        index=True,
        doc="Risk classification: LOW / MEDIUM / HIGH.",
    )

    # Analyst-facing lifecycle status
    status: Mapped[ThreatEventStatus] = mapped_column(
        Enum(ThreatEventStatus, name="threateventstatus", create_type=False),
        nullable=False,
        default=ThreatEventStatus.OPEN,
        index=True,
        doc="Current review status of this threat event.",
    )

    # Model version string for auditability (duplicated from MLModel for fast reads)
    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Version of the ML model that scored this event (cached for quick display).",
    )

    # Detection timestamp (when the pipeline processed it — not the underlying event time)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC timestamp when the threat was detected by the ML pipeline.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    monitored_account: Mapped["MonitoredAccount"] = relationship(
        "MonitoredAccount", back_populates="threat_events",
    )
    feature_vector: Mapped["FeatureVector"] = relationship(
        "FeatureVector", back_populates="threat_events",
    )
    ml_model: Mapped["MLModel"] = relationship(
        "MLModel", back_populates="threat_events",
    )
    shap_contributions: Mapped[List["SHAPContribution"]] = relationship(
        "SHAPContribution",
        back_populates="threat_event",
        cascade="all, delete-orphan",
    )
    rule_evaluations: Mapped[List["RuleEvaluation"]] = relationship(
        "RuleEvaluation",
        back_populates="threat_event",
        cascade="all, delete-orphan",
    )
    response_actions: Mapped[List["ResponseAction"]] = relationship(
        "ResponseAction",
        back_populates="threat_event",
        cascade="all, delete-orphan",
    )
    honeypot_sessions: Mapped[List["HoneypotSession"]] = relationship(
        "HoneypotSession",
        back_populates="threat_event",
        cascade="all, delete-orphan",
    )
    feedbacks: Mapped[List["AnalystFeedback"]] = relationship(
        "AnalystFeedback",
        back_populates="threat_event",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ThreatEvent id={self.id} tier={self.risk_tier} "
            f"trust={self.trust_score:.1f} confidence={self.confidence_score:.1f}% "
            f"status={self.status}>"
        )
