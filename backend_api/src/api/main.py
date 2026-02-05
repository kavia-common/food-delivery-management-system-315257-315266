from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.core.init_db import init_db
from src.api.routers.health import router as health_router
from src.api.routers.menu_items import router as menu_items_router
from src.api.routers.orders import router as orders_router
from src.api.routers.payments import router as payments_router
from src.api.routers.restaurants import router as restaurants_router

settings = get_settings()

openapi_tags = [
    {"name": "health", "description": "Health and readiness endpoints."},
    {"name": "restaurants", "description": "Restaurant browsing and management endpoints."},
    {"name": "menu", "description": "Menu item endpoints."},
    {"name": "orders", "description": "Order creation and tracking endpoints."},
    {"name": "payments", "description": "Payment endpoints (mock placeholder)."},
]

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    openapi_tags=openapi_tags,
)


if settings.allowed_origins or settings.allowed_headers or settings.allowed_methods:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=settings.allowed_methods or ["*"],
        allow_headers=settings.allowed_headers or ["*"],
        max_age=settings.cors_max_age,
    )
else:
    # Backwards-compatible default
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def _startup() -> None:
    """Initialize application state on startup.

    - Creates DB tables if they do not exist (dev bootstrap).
    """
    # This will raise clearly if DATABASE_URL/PG* are not configured.
    init_db()


@app.get(
    "/",
    summary="Legacy health check",
    description="Compatibility endpoint maintained to keep existing OpenAPI stable.",
    tags=["health"],
    operation_id="legacyRootHealth",
)
def root() -> dict:
    """Legacy root endpoint kept for compatibility.

    Returns:
        dict: Health payload.
    """
    return {"message": "Healthy"}


# Routers
app.include_router(health_router)
app.include_router(restaurants_router)
app.include_router(menu_items_router)
app.include_router(orders_router)
app.include_router(payments_router)
