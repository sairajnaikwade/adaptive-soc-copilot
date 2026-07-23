"""RetrainingRun ORM model — audit trail for model retraining runs."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import RetrainingStatus

if TYPE_CHECKING:
    from app.models.ml_model import MLModel
    from app.models.user import User


class RetrainingRun(TimestampMixin, Base):
    """
    A record of one model retraining run in the Continuous Improvement pipeline.

    Retraining can be triggered two ways:
        1. Automatic: Scheduled task when enough analyst-labeled samples accumulate
                      (triggered_by_user_id = None → triggered_by_system = True)
        2. Manual:    An admin triggers retraining via the API
                      (triggered_by_user_id = <admin's UUID>)

    On completion, a new MLModel record is created and linked as output_model_id.
    accuracy_before and accuracy_after allow analysts to evaluate whether
    retraining improved model performance.

    Relationships:
        ml_model            → The model that was retrained (source model).
        output_model        → The new MLModel produced by this run.
        triggered_by_user   → The admin who triggered the run (null = system).
    """

    __tablename__ = "retraining_runs"

    __table_args__ = (
        Index(
            "ix_retraining_runs_tenant_status",
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

    # Source model being retrained
    ml_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="RESTRICT"),
        nullable=False,
        doc="The model that was used as the starting point for retraining.",
    )

    # Output model produced by this run (set on completion)
    output_model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True,
        doc="The new MLModel produced by this retraining run (null until completion).",
    )

    # Trigger metadata
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="The admin who triggered this run. Null = system-triggered.",
    )
    triggered_by_system: Mapped[bool] = mapped_column(
        # Boolean stored as BOOLEAN in PostgreSQL
        nullable=False,
        default=False,
        server_default="false",
        doc="True = automatically triggered by the scheduled retraining task.",
    )

    # Run statistics
    samples_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of labeled feedback samples used in this retraining run.",
    )
    accuracy_before: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Model performance metric before retraining.",
    )
    accuracy_after: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Model performance metric after retraining.",
    )

    # Run lifecycle
    status: Mapped[RetrainingStatus] = mapped_column(
        Enum(RetrainingStatus, name="retrainingstatus", create_type=False),
        nullable=False,
        default=RetrainingStatus.PENDING,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the retraining job started.",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the retraining job finished (success or failure).",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error details if the retraining run failed.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    ml_model: Mapped["MLModel"] = relationship(
        "MLModel",
        back_populates="retraining_runs",
        foreign_keys=[ml_model_id],
    )
    triggered_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="retraining_runs",
        foreign_keys=[triggered_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<RetrainingRun id={self.id} status={self.status} "
            f"samples={self.samples_used}>"
        )
