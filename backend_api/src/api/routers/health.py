from __future__ import annotations

from fastapi import APIRouter

from src.api.core.db import check_db_connection

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness health check",
    description="Simple liveness probe. Does not require database connectivity.",
    operation_id="getHealth",
)
def health() -> dict:
    """Liveness probe endpoint.

    Returns:
        dict: A small payload indicating the service is up.
    """
    return {"status": "ok"}


@router.get(
    "/health/db",
    summary="Database health check",
    description="Checks whether the configured PostgreSQL database is reachable (SELECT 1).",
    operation_id="getDbHealth",
)
def health_db() -> dict:
    """Database connectivity health check.

    Returns:
        dict: status=ok if DB reachable, otherwise status=error.
    """
    ok = check_db_connection()
    return {"status": "ok" if ok else "error"}
