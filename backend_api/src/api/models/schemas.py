from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RestaurantBase(BaseModel):
    """Shared restaurant fields."""
    name: str = Field(..., description="Restaurant display name.", examples=["Sushi Place"])
    description: Optional[str] = Field(default=None, description="Optional restaurant description.")
    is_active: bool = Field(default=True, description="Whether the restaurant is accepting orders.")


class RestaurantCreate(RestaurantBase):
    """Payload to create a restaurant."""


class RestaurantRead(RestaurantBase):
    """Restaurant read model."""
    id: int = Field(..., description="Restaurant ID.")
    created_at: datetime = Field(..., description="Creation timestamp.")

    class Config:
        from_attributes = True


class MenuItemBase(BaseModel):
    """Shared menu item fields."""
    restaurant_id: int = Field(..., description="Owning restaurant ID.")
    name: str = Field(..., description="Item name.", examples=["Salmon Nigiri"])
    description: Optional[str] = Field(default=None, description="Optional item description.")
    price_cents: int = Field(..., ge=0, description="Item price in cents.", examples=[1299])
    is_available: bool = Field(default=True, description="Availability flag.")


class MenuItemCreate(MenuItemBase):
    """Payload to create a menu item."""


class MenuItemRead(MenuItemBase):
    """Menu item read model."""
    id: int = Field(..., description="Menu item ID.")
    created_at: datetime = Field(..., description="Creation timestamp.")

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    """Order item line payload."""
    menu_item_id: int = Field(..., description="Menu item ID.")
    quantity: int = Field(..., ge=1, description="Quantity ordered.", examples=[2])


class OrderCreate(BaseModel):
    """Payload to create an order."""
    restaurant_id: int = Field(..., description="Restaurant ID being ordered from.")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="At least one order line item.")


class OrderItemRead(BaseModel):
    """Order item read model."""
    id: int = Field(..., description="Order item ID.")
    menu_item_id: int = Field(..., description="Menu item ID.")
    quantity: int = Field(..., ge=1, description="Quantity ordered.")
    price_cents_each: int = Field(..., ge=0, description="Price per item (snapshotted at order time).")

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    """Order read model."""
    id: int = Field(..., description="Order ID.")
    restaurant_id: int = Field(..., description="Restaurant ID.")
    status: str = Field(..., description="Order status.", examples=["created", "paid", "preparing", "out_for_delivery", "delivered", "cancelled"])
    total_cents: int = Field(..., ge=0, description="Order total in cents.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    items: List[OrderItemRead] = Field(default_factory=list, description="Order line items.")

    class Config:
        from_attributes = True


class DeliveryUpdate(BaseModel):
    """Payload to update delivery status for an order."""
    status: str = Field(
        ...,
        description="New delivery status.",
        examples=["preparing", "out_for_delivery", "delivered"],
    )


class PaymentCreate(BaseModel):
    """Payload to record a payment for an order (placeholder for real payment integration)."""
    order_id: int = Field(..., description="Order being paid.")
    amount_cents: int = Field(..., ge=0, description="Amount paid in cents.")
    provider: str = Field(default="mock", description="Payment provider identifier.")
