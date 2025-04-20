"""
Domain events for the catalog context.

This module defines the events that can be raised by entities in the catalog
context. Events represent something significant that happened in the domain.
"""

from decimal import Decimal
from typing import Optional, Dict, Any

from uno.core.events import UnoEvent


class ProductCreatedEvent(UnoEvent):
    """Event raised when a new product is created."""

    name: str
    sku: str
    price: Decimal
    currency: str


class ProductUpdatedEvent(UnoEvent):
    """Event raised when a product is updated."""

    name: str
    status: str
    attributes: Optional[Dict[str, Any]] = None


class ProductPriceChangedEvent(UnoEvent):
    """Event raised when a product's price is changed."""

    old_price: Decimal
    new_price: Decimal
    currency: str


class ProductInventoryUpdatedEvent(UnoEvent):
    """Event raised when a product's inventory is updated."""

    old_quantity: int
    new_quantity: int
    is_low_stock: Optional[bool] = None


class CategoryCreatedEvent(UnoEvent):
    """Event raised when a new category is created."""

    name: str
    parent_id: str | None = None
