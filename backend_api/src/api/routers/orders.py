from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.api.core.db import get_db
from src.api.models import db_models
from src.api.models.schemas import DeliveryUpdate, OrderCreate, OrderItemRead, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])

_VALID_STATUSES = {"created", "paid", "preparing", "out_for_delivery", "delivered", "cancelled"}


def _order_to_read(order: db_models.Order) -> OrderRead:
    """Convert ORM order to API model."""
    items = [
        OrderItemRead.model_validate(oi)
        for oi in (order.items or [])
    ]
    return OrderRead(
        id=order.id,
        restaurant_id=order.restaurant_id,
        status=order.status,
        total_cents=order.total_cents,
        created_at=order.created_at,
        items=items,
    )


@router.post(
    "",
    response_model=OrderRead,
    summary="Create order",
    description="Create an order for a restaurant using menu items; totals are calculated from current menu prices.",
    operation_id="createOrder",
)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> OrderRead:
    """Create a new order with line items."""
    restaurant = db.get(db_models.Restaurant, payload.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    order = db_models.Order(restaurant_id=payload.restaurant_id, status="created", total_cents=0)
    db.add(order)
    db.flush()  # obtain order.id

    total = 0
    for line in payload.items:
        menu_item = db.get(db_models.MenuItem, line.menu_item_id)
        if not menu_item or menu_item.restaurant_id != payload.restaurant_id:
            raise HTTPException(status_code=400, detail=f"Invalid menu item {line.menu_item_id} for this restaurant")
        if not menu_item.is_available:
            raise HTTPException(status_code=400, detail=f"Menu item {line.menu_item_id} is not available")

        price_each = int(menu_item.price_cents)
        total += price_each * int(line.quantity)

        order_item = db_models.OrderItem(
            order_id=order.id,
            menu_item_id=line.menu_item_id,
            quantity=int(line.quantity),
            price_cents_each=price_each,
        )
        db.add(order_item)

    order.total_cents = total
    db.commit()

    # Reload with items
    stmt = (
        select(db_models.Order)
        .where(db_models.Order.id == order.id)
        .options(selectinload(db_models.Order.items))
    )
    order_full = db.execute(stmt).scalars().first()
    assert order_full is not None
    return _order_to_read(order_full)


@router.get(
    "",
    response_model=list[OrderRead],
    summary="List orders",
    description="List orders with optional status filter.",
    operation_id="listOrders",
)
def list_orders(
    status: str | None = Query(default=None, description="Filter by order status."),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of results."),
    offset: int = Query(default=0, ge=0, description="Offset for pagination."),
    db: Session = Depends(get_db),
) -> list[OrderRead]:
    """List orders."""
    stmt = (
        select(db_models.Order)
        .order_by(db_models.Order.id.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(db_models.Order.items))
    )
    if status is not None:
        stmt = stmt.where(db_models.Order.status == status)

    orders = db.execute(stmt).scalars().all()
    return [_order_to_read(o) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get order",
    description="Fetch an order by ID (includes items).",
    operation_id="getOrder",
)
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderRead:
    """Get an order by ID."""
    stmt = (
        select(db_models.Order)
        .where(db_models.Order.id == order_id)
        .options(selectinload(db_models.Order.items))
    )
    order = db.execute(stmt).scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_read(order)


@router.patch(
    "/{order_id}/delivery",
    response_model=OrderRead,
    summary="Update delivery status",
    description="Update delivery status for an order.",
    operation_id="updateDeliveryStatus",
)
def update_delivery_status(order_id: int, payload: DeliveryUpdate, db: Session = Depends(get_db)) -> OrderRead:
    """Update delivery status for an order."""
    if payload.status not in _VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(_VALID_STATUSES)}")

    stmt = (
        select(db_models.Order)
        .where(db_models.Order.id == order_id)
        .options(selectinload(db_models.Order.items))
    )
    order = db.execute(stmt).scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return _order_to_read(order)
