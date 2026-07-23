"""
Alembic environment configuration.

This module configures Alembic to:
    1. Read the database URL from the application settings (not alembic.ini).
    2. Use the shared SQLAlchemy metadata (Base.metadata) populated by
       importing all ORM models — required for autogenerate support.
    3. Support both online (live DB) and offline (SQL script) migration modes.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Make the 'app' package importable when running alembic from backend/
# ---------------------------------------------------------------------------
# The backend/ directory must be in sys.path so that `from app.xxx import yyy`
# works inside this file and inside migration scripts.
backend_dir = Path(__file__).resolve().parent.parent  # adaptive-soc-copilot/backend/
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ---------------------------------------------------------------------------
# Import application settings and ALL ORM models (populates Base.metadata)
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402
from app.db.base import Base           # noqa: E402
import app.models  # noqa: E402, F401 — side-effect: registers all 17 models with Base.metadata

# ---------------------------------------------------------------------------
# Alembic Config object (gives access to alembic.ini values)
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url from application settings (ignores the %(DATABASE_URL)s
# placeholder in alembic.ini and uses the actual value from .env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate (Base.metadata contains all 17 tables)
target_metadata = Base.metadata


# =============================================================================
# Offline mode — generates a SQL script without a live DB connection
# =============================================================================

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates a SQL migration script that can be reviewed and applied manually.
    Useful for DBAs who review scripts before execution.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # Detect column type changes
        compare_server_default=True,  # Detect server_default changes
    )
    with context.begin_transaction():
        context.run_migrations()


# =============================================================================
# Online mode — runs migrations against a live database connection
# =============================================================================

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates a connection pool and runs each migration inside an explicit
    transaction. Uses NullPool for Alembic to avoid connection pool issues
    when running as a one-off command.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling for migration scripts
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# Entry point
# =============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
