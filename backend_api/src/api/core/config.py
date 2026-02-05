from __future__ import annotations

import os
from typing import List, Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings sourced from environment variables.

    Notes:
        - We intentionally do not read the `.env` file directly here. The runtime environment
          is responsible for loading env vars (python-dotenv is available if used by the runner).
    """

    app_name: str = Field(default="Food Delivery Backend API", description="Human-friendly API name.")
    app_version: str = Field(default="0.1.0", description="API version string.")
    app_description: str = Field(
        default="Backend API for a food delivery app: restaurants, menus, orders, delivery tracking.",
        description="Long-form application description.",
    )

    allowed_origins: List[str] = Field(
        default_factory=list,
        description="CORS allowed origins parsed from ALLOWED_ORIGINS (comma-separated).",
    )
    allowed_headers: List[str] = Field(
        default_factory=list,
        description="CORS allowed headers parsed from ALLOWED_HEADERS (comma-separated).",
    )
    allowed_methods: List[str] = Field(
        default_factory=list,
        description="CORS allowed methods parsed from ALLOWED_METHODS (comma-separated).",
    )
    cors_max_age: int = Field(default=3600, description="CORS preflight max age in seconds.")

    # DB: we support either DATABASE_URL (preferred) or discrete PG* variables.
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL SQLAlchemy URL. Prefer setting DATABASE_URL, e.g. postgresql+psycopg://user:pass@host:5432/db",
    )

    pg_host: Optional[str] = Field(default=None, description="PostgreSQL host (fallback if DATABASE_URL is not set).")
    pg_port: int = Field(default=5432, description="PostgreSQL port (fallback if DATABASE_URL is not set).")
    pg_user: Optional[str] = Field(default=None, description="PostgreSQL user (fallback if DATABASE_URL is not set).")
    pg_password: Optional[str] = Field(
        default=None, description="PostgreSQL password (fallback if DATABASE_URL is not set)."
    )
    pg_db: Optional[str] = Field(default=None, description="PostgreSQL database name (fallback if DATABASE_URL is not set).")


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from environment variables.

    Returns:
        Settings: Parsed settings.

    Environment variables:
        - ALLOWED_ORIGINS: comma-separated list
        - ALLOWED_HEADERS: comma-separated list
        - ALLOWED_METHODS: comma-separated list
        - CORS_MAX_AGE: integer seconds
        - DATABASE_URL: SQLAlchemy URL (preferred)
        - PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE: fallback pieces if DATABASE_URL missing
    """

    def _csv(name: str) -> List[str]:
        raw = os.getenv(name, "").strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]

    settings = Settings(
        allowed_origins=_csv("ALLOWED_ORIGINS"),
        allowed_headers=_csv("ALLOWED_HEADERS"),
        allowed_methods=_csv("ALLOWED_METHODS"),
        cors_max_age=int(os.getenv("CORS_MAX_AGE", "3600")),
        database_url=os.getenv("DATABASE_URL"),
        pg_host=os.getenv("PGHOST"),
        pg_port=int(os.getenv("PGPORT", "5432")),
        pg_user=os.getenv("PGUSER"),
        pg_password=os.getenv("PGPASSWORD"),
        pg_db=os.getenv("PGDATABASE"),
    )
    return settings
