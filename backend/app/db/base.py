"""
SQLAlchemy declarative base and reusable model mixins.

All ORM models must inherit from Base (registered with the shared metadata
that Alembic uses for migration generation).

Available mixins:
    TimestampMixin — adds created_at / updated_at (timezone-aware)

Usage:
    from app.db.base import Base, TimestampMixin

    class MyModel(TimestampMixin, Base):
        __tablename__ = "my_table"
        ...
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy ORM models.

    All models registered with this base are tracked in Base.metadata,
    which Alembic reads to generate migration scripts automatically.
    """

    pass


class TimestampMixin:
    """
    Mixin that adds timezone-aware created_at and updated_at columns.

    - created_at: Set by the database server on INSERT (immutable after creation).
    - updated_at: Set by the database server on INSERT and updated by
                  SQLAlchemy's ORM on every UPDATE through the Python layer.

    Note: Direct SQL UPDATEs (e.g., db.query(Model).filter(...).update({...}))
    bypass the ORM and will NOT automatically refresh updated_at. Use
    db.add(instance) + db.commit() for ORM-level updates.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was first created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was last modified.",
    )
