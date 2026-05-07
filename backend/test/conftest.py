"""
Pytest fixtures shared across all test modules.

Uses an in-memory SQLite database so tests are:
- Fast (no disk I/O)
- Isolated (each test uses a SAVEPOINT rolled back after completion)
- Independent of the production database file

Isolation strategy:
    test_engine  (session scope) — creates schema once
    test_app     (session scope) — creates FastAPI app once
    db_session   (function scope) — SAVEPOINT per test, always rolled back
    api_client   (function scope) — TestClient with overridden DB session
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from backend.infrastructure.db import orm_models  # noqa: F401 — registers ORM classes
from backend.infrastructure.db.database import Base, get_session
from backend.main import create_app

_IN_MEMORY_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    """
    Creates a shared in-memory SQLite engine for the test session.

    Tables are created once before all tests and dropped afterwards.
    The orm_models import at the top of this file ensures all ORM
    classes are registered with Base.metadata before create_all() runs.
    """
    engine = create_engine(
        _IN_MEMORY_DB_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def test_app():
    """
    Creates the FastAPI application once for the entire test session.

    Reusing a single app instance avoids the overhead of re-importing
    and re-registering all routers on every test.
    """
    return create_app()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    """
    Provides a fully isolated database session for a single test.

    Uses the SAVEPOINT pattern (join_transaction_mode="create_savepoint")
    so that even if the code under test calls session.commit(), all changes
    are contained within the outer transaction and rolled back after the test.

    This ensures zero state leakage between tests without dropping
    and recreating the schema on every function.
    """
    connection        = test_engine.connect()
    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def api_client(test_app, db_session: Session) -> Iterator[TestClient]:
    """
    Returns a FastAPI TestClient with the database session overridden
    to use the per-test in-memory session.

    dependency_overrides is cleared after each test to prevent one test's
    overrides from affecting subsequent tests.

    Args:
        test_app:   Shared FastAPI app instance (session-scoped).
        db_session: Transactional test session (function-scoped).

    Yields:
        Configured TestClient ready for HTTP-level testing.
    """
    test_app.dependency_overrides[get_session] = lambda: db_session

    with TestClient(test_app, raise_server_exceptions=True) as client:
        yield client

    test_app.dependency_overrides.clear()