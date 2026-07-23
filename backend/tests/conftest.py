"""
Test fixtures — shared pytest configuration for all test modules.

Provides:
    client   → TestClient for the FastAPI app (no real DB needed for unit tests)
    db       → In-memory SQLite session for integration tests
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# Override DATABASE_URL with SQLite in-memory before importing the app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-production")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.db.base import Base
from app.db.session import SessionLocal
from app.main import app
from app.core.dependencies import get_db


# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables in the in-memory test DB once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Session:
    """Provide a transactional DB session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> TestClient:
    """
    Provide a FastAPI TestClient with the test DB session injected.

    The get_db dependency is overridden to use the test session so that
    test requests hit the in-memory SQLite DB, not the real PostgreSQL DB.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
