"""FeatureValue ORM model — individual (feature_name, value) rows for a FeatureVector."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.feature_vector import FeatureVector


class FeatureValue(Base):
    """
    A single normalized feature value within a FeatureVector.

    Normalizing features into rows (instead of JSONB) enables:
        1. Direct SQL aggregation and filtering by feature name.
        2. Clean SHAP contribution joins: feature_name matches between
           FeatureValue and SHAPContribution for visual explanation.
        3. Future feature importance reporting at the DB level.

    Feature examples (populated by Feature Extraction in Sprint 3):
        "login_failure_count_24h"    → 15.0
        "unique_ip_count_24h"        → 5.0
        "data_export_bytes_24h"      → 52428800.0 (50 MB)
        "off_hours_access_ratio"     → 0.82
        "privilege_change_count_7d"  → 3.0

    Uniqueness:
        (feature_vector_id, feature_name) is unique — prevents duplicate
        feature entries for the same vector.

    Design note:
        No tenant_id here — the parent FeatureVector already carries tenant_id.
        Queries always join through FeatureVector which is tenant-scoped.
    """

    __tablename__ = "feature_values"

    __table_args__ = (
        UniqueConstraint(
            "feature_vector_id", "feature_name",
            name="uq_feature_values_vector_name",
        ),
        Index(
            "ix_feature_values_vector_id",
            "feature_vector_id",
        ),
        Index(
            "ix_feature_values_name",
            "feature_name",
        ),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK to the parent vector
    feature_vector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_vectors.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Feature name — matches the column name used during model training
    feature_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc=(
            "Snake_case feature name (e.g., 'login_failure_count_24h'). "
            "Must match the feature names used when the ML model was trained."
        ),
    )

    # Numeric feature value (all features are normalized to floats)
    feature_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Numeric value of the feature. Ratios are in [0, 1]; counts are non-negative.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    feature_vector: Mapped["FeatureVector"] = relationship(
        "FeatureVector", back_populates="feature_values",
    )

    def __repr__(self) -> str:
        return (
            f"<FeatureValue vector={self.feature_vector_id} "
            f"name='{self.feature_name}' value={self.feature_value}>"
        )
