from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.api.core.db import get_db
from src.api.models import db_models
from src.api.models.schemas import OrderItemRead, OrderRead, PaymentCreate

router = APIRouter(prefix="/payments", tags=["payments"])


def _order_to_read(order: db_models.Order) -> OrderRead:
    """Convert ORM order to API model."""
    items = [OrderItemRead.model_validate(oi) for oi in (order.items or [])]
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
    response_model=dict,
    summary="Create payment (mock)",
    description="Records a payment for an order and sets order status to 'paid' if amount covers total.",
    operation_id="createPayment",
)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> dict:
    """Record a payment and update the order status (mock)."""
    stmt = (
        select(db_models.Order)
        .where(db_models.Order.id == payload.order_id)
        .options(selectinload(db_models.Order.items))
    )
    order = db.execute(stmt).scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = db_models.Payment(order_id=payload.order_id, provider=payload.provider, amount_cents=payload.amount_cents)
    db.add(payment)

    if payload.amount_cents >= order.total_cents:
        order.status = "paid"

    db.commit()
    return {"status": "ok", "order_id": order.id, "order_status": order.status}
