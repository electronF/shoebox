"""
SQLAlchemy connection configuration and session factory.

Supports SQLite (default) as well as PostgreSQL/MySQL via the
DATABASE_URL environment variable — the rest of the code remains unchanged.
"""

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def _configure_sqlite(dbapi_connection, _connection_record) -> None:
    """
    Enables recommended SQLite pragmas on every new connection.

    WAL improves performance for concurrent reads.
    foreign_keys enforces referential integrity (disabled by default).
    """
    dbapi_connection.execute("PRAGMA journal_mode=WAL")
    dbapi_connection.execute("PRAGMA foreign_keys=ON")
    dbapi_connection.execute("PRAGMA synchronous=NORMAL")


def build_engine(database_url: str) -> Engine:
    """
    Builds the SQLAlchemy engine based on the connection URL.

    For SQLite, enables WAL mode and foreign keys.
    For PostgreSQL/MySQL, no specific configuration is required.

    Args:
        database_url: SQLAlchemy connection URL
                      (e.g.: "sqlite:///./data/shoebox.db").

    Returns:
        Configured SQLAlchemy Engine.
    """
    is_sqlite = database_url.startswith("sqlite")

    # SQLite specific: allow multi-threading access
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=settings.debug,           # logs SQL if DEBUG=true
        pool_pre_ping=True,            # checks connection health before use
    )

    if is_sqlite:
        event.listen(engine, "connect", _configure_sqlite)
        logger.info("SQLite configured with WAL + foreign_keys")
    else:
        # Logs the host/DB part only, hiding credentials
        logger.info("Database connection: %s", database_url.split("@")[-1])

    return engine


# Global instance — built once at startup
engine: Engine = build_engine(settings.database_url)

# Session factory — reused for every request
SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,   # prevents lazy-loading issues after commit
)


def get_session() -> Generator[Session, None, None]:
    """
    SQLAlchemy session generator — used as a FastAPI dependency.

    Ensures the session is closed even if an exception occurs.

    Yields:
        Active SQLAlchemy Session for the duration of the HTTP request.

    Example::

        @router.get("/transactions")
        def list_transactions(db: Session = Depends(get_session)):
            ...
    """
    session = SessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables() -> None:
    """Creates all tables defined in the ORM models. Idempotent."""
    # Local import to prevent circular imports
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created / verified.")