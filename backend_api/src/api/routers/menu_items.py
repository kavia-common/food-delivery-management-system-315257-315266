from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.models import db_models
from src.api.models.schemas import MenuItemCreate, MenuItemRead

router = APIRouter(prefix="/menu-items", tags=["menu"])


@router.post(
    "",
    response_model=MenuItemRead,
    summary="Create menu item",
    description="Create a menu item for a restaurant (admin use).",
    operation_id="createMenuItem",
)
def create_menu_item(payload: MenuItemCreate, db: Session = Depends(get_db)) -> MenuItemRead:
    """Create a menu item."""
    restaurant = db.get(db_models.Restaurant, payload.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    item = db_models.MenuItem(
        restaurant_id=payload.restaurant_id,
        name=payload.name,
        description=payload.description,
        price_cents=payload.price_cents,
        is_available=payload.is_available,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return MenuItemRead.model_validate(item)


@router.get(
    "",
    response_model=list[MenuItemRead],
    summary="List menu items",
    description="List menu items, optionally filtered by restaurant and availability.",
    operation_id="listMenuItems",
)
def list_menu_items(
    restaurant_id: int | None = Query(default=None, description="Filter to a restaurant."),
    is_available: bool | None = Query(default=None, description="Filter by availability."),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of results."),
    offset: int = Query(default=0, ge=0, description="Offset for pagination."),
    db: Session = Depends(get_db),
) -> list[MenuItemRead]:
    """List menu items."""
    stmt = select(db_models.MenuItem).order_by(db_models.MenuItem.id).limit(limit).offset(offset)
    if restaurant_id is not None:
        stmt = stmt.where(db_models.MenuItem.restaurant_id == restaurant_id)
    if is_available is not None:
        stmt = stmt.where(db_models.MenuItem.is_available == is_available)

    rows = db.execute(stmt).scalars().all()
    return [MenuItemRead.model_validate(i) for i in rows]


@router.get(
    "/{menu_item_id}",
    response_model=MenuItemRead,
    summary="Get menu item",
    description="Fetch a menu item by ID.",
    operation_id="getMenuItem",
)
def get_menu_item(menu_item_id: int, db: Session = Depends(get_db)) -> MenuItemRead:
    """Get a menu item by ID."""
    item = db.get(db_models.MenuItem, menu_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return MenuItemRead.model_validate(item)
