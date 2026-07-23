"""SHAPContribution ORM model — per-feature SHAP values for XAI explanations."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.threat_event import ThreatEvent


class SHAPContribution(Base):
    """
    A single SHAP (SHapley Additive exPlanations) feature contribution value
    for a specific ThreatEvent.

    One SHAPContribution row per (threat_event, feature_name) pair. The complete
    set of rows for a ThreatEvent forms the full SHAP explanation displayed in
    the SOC Dashboard's "Why was this flagged?" panel.

    SHAP value semantics:
        shap_value > 0  → This feature INCREASED the anomaly score (pushed toward threat)
        shap_value < 0  → This feature DECREASED the anomaly score (pushed toward normal)
        |shap_value|    → The magnitude of this feature's contribution

    Normalized design benefits:
        - Dashboard can sort features by |shap_value| using SQL ORDER BY
        - Easy top-N most important features query
        - No JSON parsing needed for display

    Uniqueness: (threat_event_id, feature_name) is unique per threat event.
    """

    __tablename__ = "shap_contributions"

    __table_args__ = (
        UniqueConstraint(
            "threat_event_id", "feature_name",
            name="uq_shap_contributions_event_feature",
        ),
        Index(
            "ix_shap_contributions_threat_event_id",
            "threat_event_id",
        ),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Multi-tenancy scoping (denormalized for faster tenant-scoped XAI queries)
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

    # Feature identification
    feature_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc=(
            "Snake_case feature name. Matches feature_values.feature_name "
            "for the same feature_vector."
        ),
    )

    # SHAP values
    shap_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="SHAP contribution value. Positive → increases anomaly; negative → decreases.",
    )
    feature_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Actual numeric value of the feature (for displaying '24 failures' vs just 0.91).",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    threat_event: Mapped["ThreatEvent"] = relationship(
        "ThreatEvent", back_populates="shap_contributions",
    )

    def __repr__(self) -> str:
        return (
            f"<SHAPContribution threat={self.threat_event_id} "
            f"feature='{self.feature_name}' shap={self.shap_value:+.4f}>"
        )
