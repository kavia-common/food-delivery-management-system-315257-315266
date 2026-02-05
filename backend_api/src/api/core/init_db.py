from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from src.api.core.db import get_engine
from src.api.models.db_models import Base


# PUBLIC_INTERFACE
def init_db() -> None:
    """Initialize database schema (create tables if missing).

    This is a lightweight bootstrap suitable for early development.
    For production, use migrations (Alembic) instead.
    """
    engine = get_engine()
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        # Re-raise with a clearer message while preserving stack.
        raise RuntimeError(f"Failed to initialize database schema: {exc}") from exc
