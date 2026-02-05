from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.config import get_settings


def _build_database_url() -> Optional[str]:
    """Build a SQLAlchemy PostgreSQL URL from discrete PG* env vars (fallback mode)."""
    settings = get_settings()
    if settings.database_url:
        return settings.database_url

    if not (settings.pg_host and settings.pg_user and settings.pg_password and settings.pg_db):
        return None

    # psycopg (v3) driver
    return (
        f"postgresql+psycopg://{settings.pg_user}:{settings.pg_password}"
        f"@{settings.pg_host}:{settings.pg_port}/{settings.pg_db}"
    )


_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Get a singleton SQLAlchemy engine.

    Returns:
        Engine: SQLAlchemy engine configured for PostgreSQL via psycopg.

    Raises:
        RuntimeError: If no database configuration is available.
    """
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        return _engine

    db_url = _build_database_url()
    if not db_url:
        raise RuntimeError(
            "Database is not configured. Set DATABASE_URL (preferred) or PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE."
        )

    _engine = create_engine(
        db_url,
        pool_pre_ping=True,  # helps avoid stale connections
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session and ensure it is closed.

    Yields:
        Session: SQLAlchemy ORM session.
    """
    global _SessionLocal
    if _SessionLocal is None:
        # Initialize engine/sessionmaker lazily
        get_engine()

    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for internal usage (non-FastAPI dependency injection)."""
    gen = get_db()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            gen.close()
        except Exception:
            session.close()


# PUBLIC_INTERFACE
def check_db_connection() -> bool:
    """Check whether the database is reachable.

    Returns:
        bool: True if a simple `SELECT 1` succeeds, else False.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
