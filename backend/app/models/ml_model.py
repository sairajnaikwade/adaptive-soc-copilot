"""MLModel ORM model — registry of trained anomaly detection models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import MLModelType

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.threat_event import ThreatEvent
    from app.models.retraining_run import RetrainingRun


class MLModel(TimestampMixin, Base):
    """
    Registry entry for a trained ML anomaly detection model.

    Each row represents one trained model artifact stored on disk (or object
    storage in production). The file_path points to the serialized scikit-learn
    pipeline (.pkl / .joblib file).

    Model lifecycle:
        1. Training (Sprint 3): A new MLModel row is created with is_active=False.
        2. Validation: After performance checks, is_active is set to True.
        3. Retirement: When a new model is activated, the old one is deactivated.
        4. Retraining (Sprint 6): RetrainingRun creates a new MLModel row.

    Only ONE model per (tenant_id, model_type) should be active at any time.
    This is enforced at the service layer, not via a DB constraint, to allow
    atomic swap-over without downtime.

    Relationships:
        tenant           → The tenant this model was trained for.
        threat_events    → Threat events scored by this model.
        retraining_runs  → Retraining runs that produced or used this model.
    """

    __tablename__ = "ml_models"

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
        doc="Tenant this model was trained for. Null = system-wide base model (future).",
    )

    # Model type
    model_type: Mapped[MLModelType] = mapped_column(
        Enum(MLModelType, name="mlmodeltype", create_type=False),
        nullable=False,
        doc="Algorithm family: isolation_forest (primary) or one_class_svm (comparison).",
    )

    # Human-readable version string (e.g., "v1.0", "v2.3-retrained-2026-07-23")
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Version string. Incremented automatically on each retraining run.",
    )

    # Path to serialized model artifact
    file_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Absolute or relative path to the .pkl model file on the API server.",
    )

    # Training performance metrics
    training_samples: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of feature vectors used to train this model.",
    )
    training_accuracy: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Model accuracy metric from training evaluation (e.g., F1 if labels available).",
    )
    contamination_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Contamination parameter used for Isolation Forest training.",
    )

    # Hyperparameters stored as a JSON-compatible string for auditability
    hyperparameters: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON string of hyperparameters used during training.",
    )

    # Training timestamp
    trained_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when model training completed.",
    )

    # Active/inactive flag — only one active model per (tenant, model_type)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        doc="True = this model is currently serving predictions.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant")

    threat_events: Mapped[List["ThreatEvent"]] = relationship(
        "ThreatEvent", back_populates="ml_model",
    )
    retraining_runs: Mapped[List["RetrainingRun"]] = relationship(
        "RetrainingRun",
        back_populates="ml_model",
        foreign_keys="RetrainingRun.ml_model_id",
    )

    def __repr__(self) -> str:
        return (
            f"<MLModel id={self.id} type={self.model_type} "
            f"version='{self.version}' active={self.is_active}>"
        )
