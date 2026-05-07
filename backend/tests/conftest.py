"""
Pytest fixtures for the Shoebox test suite.

Uses a temporary file-based SQLite database (not in-memory) to avoid
engine binding issues with module-level singletons. Each test gets a
fresh schema via drop_all/create_all — fast enough on a local file DB.
"""

import os
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.infrastructure.db import orm_models  # noqa: F401
from backend.infrastructure.db.database import Base, get_session
import backend.infrastructure.db.database as db_module
from backend.main import create_app


@pytest.fixture(scope="session", autouse=True)
def patch_db_engine():
    """
    Replaces the production SQLite engine with a temp-file engine
    for the entire test session. Restores original after all tests.

    Using a file-based temp DB (not :memory:) avoids the issue where
    multiple SQLAlchemy sessions on the same in-memory DB cannot see
    each other's tables because they use separate connections.
    """
    # Create a temp file for the test DB
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    test_engine = create_engine(
        f"sqlite:///{tmp_path}",
        connect_args={"check_same_thread": False},
    )

    # Replace module-level singletons before any test runs
    original_engine          = db_module.engine
    original_session_factory = db_module.SessionFactory

    db_module.engine         = test_engine
    db_module.SessionFactory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    # Create schema once
    Base.metadata.create_all(bind=test_engine)

    yield

    # Restore and clean up
    db_module.engine         = original_engine
    db_module.SessionFactory = original_session_factory
    test_engine.dispose()
    os.unlink(tmp_path)


@pytest.fixture
def db_session() -> Iterator[Session]:
    """
    Provides a clean DB session for each test.
    Drops and recreates all tables to guarantee zero state leakage.
    """
    Base.metadata.drop_all(bind=db_module.engine)
    Base.metadata.create_all(bind=db_module.engine)

    session = db_module.SessionFactory()
    yield session
    session.close()


@pytest.fixture(scope="session")
def test_app():
    """FastAPI app created once for the session."""
    return create_app()


@pytest.fixture
def api_client(test_app, db_session: Session) -> Iterator[TestClient]:
    """
    TestClient with the DB session overridden per test.
    Uses the same patched engine as db_session.
    """
    test_app.dependency_overrides[get_session] = lambda: db_session

    with TestClient(test_app, raise_server_exceptions=True) as client:
        yield client

    test_app.dependency_overrides.clear()