"""
SQLAlchemy engine and session factory configuration.

Creates a synchronous connection pool backed by psycopg2 and exposes:
    - engine       : The raw SQLAlchemy engine (used by Alembic)
    - SessionLocal : A session factory for creating per-request DB sessions
    - get_db()     : FastAPI dependency that yields and auto-closes sessions
                     (re-exported here for convenience; canonical definition
                      is in app.core.dependencies)
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# SQLAlchemy Engine
# Pool settings are tuned for a moderate-traffic SOC API.
# Adjust pool_size and max_overflow for production load.
# ---------------------------------------------------------------------------
# Engine kwargs depend on database dialect
engine_kwargs = {
    "echo": settings.is_development,
}

# Connection pool settings for PostgreSQL
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)


# ---------------------------------------------------------------------------
# Session Factory
# autocommit=False : All writes must be explicit commit() calls
# autoflush=False  : Flush only on commit or explicit flush() — avoids
#                    unexpected SQL during business logic
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


# ---------------------------------------------------------------------------
# Engine event listeners (development diagnostics)
# ---------------------------------------------------------------------------
if settings.is_development:
    @event.listens_for(engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        logger.debug("New database connection established.")

    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("Connection checked out from pool.")
