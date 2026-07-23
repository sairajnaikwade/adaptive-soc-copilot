"""Report ORM model — metadata for generated PDF security reports."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ReportStatus, ReportType

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class Report(TimestampMixin, Base):
    """
    Metadata record for a generated SOC security report.

    The actual report content is a PDF file stored at file_path on the server's
    filesystem (or object storage in production). This table tracks generation
    status, delivery metadata, and the time period the report covers.

    Report types:
        DAILY     → Auto-generated nightly by the scheduled task
        WEEKLY    → Auto-generated weekly
        MONTHLY   → Auto-generated monthly
        ON_DEMAND → Triggered manually via POST /api/v1/reports/generate

    Delivery:
        recipients is an array of email addresses that received this report.
        sent_at is set when the email with the PDF attachment is delivered.
    """

    __tablename__ = "reports"

    __table_args__ = (
        Index(
            "ix_reports_tenant_type_created",
            "tenant_id", "report_type", "created_at",
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

    # Report metadata
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="reporttype", create_type=False),
        nullable=False,
        doc="Schedule type that triggered this report.",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable report title (e.g., 'SOC Daily Report — 2026-07-23').",
    )

    # PDF storage
    file_path: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        doc="Absolute path to the generated PDF file on the API server.",
    )

    # Coverage period
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC start of the reporting period.",
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC end of the reporting period.",
    )

    # Generation and delivery
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="reportstatus", create_type=False),
        nullable=False,
        default=ReportStatus.GENERATING,
        index=True,
        doc="Current generation/delivery status.",
    )
    generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="UUID of the analyst who requested this report. Null for scheduled reports.",
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the report email was delivered. Null if not yet sent.",
    )

    # Email delivery list stored as PostgreSQL text array
    recipients: Mapped[Optional[list]] = mapped_column(
        ARRAY(String(320)).with_variant(JSON, "sqlite"),
        nullable=True,
        doc="Array of email addresses this report was sent to.",
    )

    # Error details if generation failed
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error details if report generation or delivery failed.",
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="reports")

    generated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reports",
        foreign_keys=[generated_by],
    )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id} type={self.report_type} "
            f"status={self.status} period=[{self.period_start}, {self.period_end}]>"
        )
