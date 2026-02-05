from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.models import db_models
from src.api.models.schemas import RestaurantCreate, RestaurantRead

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post(
    "",
    response_model=RestaurantRead,
    summary="Create restaurant",
    description="Create a restaurant (admin use).",
    operation_id="createRestaurant",
)
def create_restaurant(payload: RestaurantCreate, db: Session = Depends(get_db)) -> RestaurantRead:
    """Create a new restaurant.

    Args:
        payload: RestaurantCreate payload.
        db: SQLAlchemy session.

    Returns:
        RestaurantRead: The created restaurant.
    """
    restaurant = db_models.Restaurant(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return RestaurantRead.model_validate(restaurant)


@router.get(
    "",
    response_model=list[RestaurantRead],
    summary="List restaurants",
    description="List restaurants with optional active filter.",
    operation_id="listRestaurants",
)
def list_restaurants(
    is_active: bool | None = Query(default=None, description="If provided, filter by active status."),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of results."),
    offset: int = Query(default=0, ge=0, description="Offset for pagination."),
    db: Session = Depends(get_db),
) -> list[RestaurantRead]:
    """List restaurants.

    Returns:
        list[RestaurantRead]: Restaurants.
    """
    stmt = select(db_models.Restaurant).order_by(db_models.Restaurant.id).limit(limit).offset(offset)
    if is_active is not None:
        stmt = stmt.where(db_models.Restaurant.is_active == is_active)

    rows = db.execute(stmt).scalars().all()
    return [RestaurantRead.model_validate(r) for r in rows]


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantRead,
    summary="Get restaurant",
    description="Fetch a restaurant by ID.",
    operation_id="getRestaurant",
)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)) -> RestaurantRead:
    """Get a restaurant by ID."""
    restaurant = db.get(db_models.Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return RestaurantRead.model_validate(restaurant)
