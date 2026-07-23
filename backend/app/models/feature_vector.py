"""FeatureVector ORM model — computed behavioral feature windows for ML input."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.monitored_account import MonitoredAccount
    from app.models.feature_value import FeatureValue
    from app.models.threat_event import ThreatEvent


class FeatureVector(TimestampMixin, Base):
    """
    A time-windowed behavioral feature vector computed for a monitored account.

    Each FeatureVector represents a sliding-window aggregation of raw auth
    and activity events for one account over a fixed time range
    [window_start, window_end].

    The actual numeric feature values are stored as normalized rows in the
    FeatureValue table (see below), enabling:
        - Per-feature queries without JSON parsing
        - Clean SHAP contribution mapping (feature_name → shap_value)
        - Addition of new features without schema changes

    Relationships:
        monitored_account → The account this vector was computed for.
        feature_values    → Individual (feature_name, value) rows.
        threat_events     → Threat events scored using this vector.
    """

    __tablename__ = "feature_vectors"

    __table_args__ = (
        # Index for retrieving the latest vector per account (Trust Score queries)
        Index(
            "ix_feature_vectors_tenant_account_window",
            "tenant_id", "monitored_account_id", "window_end",
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

    # Account FK
    monitored_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Time window boundaries this vector aggregates
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC start of the aggregation window.",
    )
    window_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC end of the aggregation window.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    monitored_account: Mapped["MonitoredAccount"] = relationship(
        "MonitoredAccount", back_populates="feature_vectors",
    )
    feature_values: Mapped[List["FeatureValue"]] = relationship(
        "FeatureValue",
        back_populates="feature_vector",
        cascade="all, delete-orphan",
        lazy="select",
    )
    threat_events: Mapped[List["ThreatEvent"]] = relationship(
        "ThreatEvent",
        back_populates="feature_vector",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<FeatureVector id={self.id} account={self.monitored_account_id} "
            f"window=[{self.window_start}, {self.window_end}]>"
        )
