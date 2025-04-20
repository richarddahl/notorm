"""
Example demonstrating the AggregateRoot pattern with Domain Events.

This example shows the implementation of an Order as an AggregateRoot with encapsulated
business logic, domain events, and proper invariant enforcement. It demonstrates:

1. Implementing an AggregateRoot
2. Raising and handling domain events
3. Enforcing business rules (invariants)
4. Using Value Objects for type safety
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Type, TypeVar, cast
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ConfigDict,
    PositiveInt,
    PositiveFloat,
)

from uno.core.events import Event
from uno.domain.entity import EntityBase, Identity
from uno.domain.entity.value_object import ValueObject

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== Value Objects =====


class ProductId(Identity[str]):
    """Product identifier value object."""

    pass


class OrderId(Identity[str]):
    """Order identifier value object."""

    pass


class CustomerId(Identity[str]):
    """Customer identifier value object."""

    pass


class Money(ValueObject):
    """Money value object for handling currency amounts."""

    amount: Decimal
    currency: str = "USD"

    @classmethod
    def from_float(cls, amount: float, currency: str = "USD") -> "Money":
        """Create Money from a float amount."""
        return cls(amount=Decimal(str(amount)), currency=currency)

    def add(self, other: "Money") -> "Money":
        """Add two money values of the same currency."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")

        return Money(amount=self.amount + other.amount, currency=self.currency)

    def multiply(self, quantity: int) -> "Money":
        """Multiply money value by a quantity."""
        return Money(amount=self.amount * quantity, currency=self.currency)

    def __str__(self) -> str:
        """Format as currency string."""
        return f"{self.currency} {self.amount:.2f}"


class OrderStatus(Enum):
    """Enum for order status values."""

    NEW = auto()
    CONFIRMED = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


# ===== Domain Events =====


class OrderCreatedEvent(Event):
    """Event raised when an order is created."""

    order_id: str
    customer_id: str


class OrderItemAddedEvent(Event):
    """Event raised when an item is added to an order."""

    order_id: str
    product_id: str
    quantity: int
    unit_price: Decimal


class OrderConfirmedEvent(Event):
    """Event raised when an order is confirmed."""

    order_id: str
    total_amount: Decimal
    item_count: int


class OrderCancelledEvent(Event):
    """Event raised when an order is cancelled."""

    order_id: str
    reason: str


# ===== Entities =====


class OrderItem(BaseModel):
    """Value object representing an item in an order."""

    model_config = ConfigDict(frozen=True)

    product_id: str
    quantity: PositiveInt
    unit_price: Money

    @property
    def total_price(self) -> Money:
        """Calculate the total price for this item."""
        return self.unit_price.multiply(self.quantity)


class Order(EntityBase[str]):
    """
    Order aggregate root entity.

    This class demonstrates the Aggregate Root pattern with proper encapsulation,
    business rule enforcement, and event raising.
    """

    # Basic properties
    customer_id: str
    status: OrderStatus = Field(default=OrderStatus.NEW)

    # Collection of items - note these are value objects
    items: list[OrderItem] = Field(default_factory=list)

    # Additional properties
    shipping_address: Optional[Dict[str, str]] = None
    notes: str | None = None

    # Domain events collection - not serialized
    _events: list[Event] = Field(default_factory=list, exclude=True)

    @model_validator(mode="after")
    def validate_order(self) -> "Order":
        """
        Validate the order after initialization.

        This method enforces invariants that must always be true for this entity.
        """
        # Order must have a valid customer ID
        if not self.customer_id:
            raise ValueError("Order must have a customer ID")

        return self

    @classmethod
    def create(cls, customer_id: str) -> "Order":
        """Create a new order for a customer."""
        order = cls(
            id=str(uuid4()),
            customer_id=customer_id,
        )

        # Raise domain event
        order._events.append(
            OrderCreatedEvent(order_id=order.id, customer_id=customer_id)
        )

        return order

    def add_item(self, product_id: str, quantity: int, unit_price: float) -> None:
        """
        Add an item to the order.

        Args:
            product_id: The product ID
            quantity: The quantity to add
            unit_price: The unit price as a float

        Raises:
            ValueError: If the order is not in NEW status or quantity/price is invalid
        """
        # Business rule: can only add items to orders in NEW status
        if self.status != OrderStatus.NEW:
            raise ValueError(
                f"Cannot add items to an order with status {self.status.name}"
            )

        # Create price as value object
        price = Money.from_float(unit_price)

        # Create item
        item = OrderItem(product_id=product_id, quantity=quantity, unit_price=price)

        # Add to items
        self.items.append(item)

        # Mark as modified
        self.mark_modified()

        # Raise domain event
        self._events.append(
            OrderItemAddedEvent(
                order_id=self.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=price.amount,
            )
        )

    def confirm(self) -> None:
        """
        Confirm the order.

        This changes the order status to CONFIRMED and raises an event.

        Raises:
            ValueError: If the order is empty or not in NEW status
        """
        # Business rules
        if self.status != OrderStatus.NEW:
            raise ValueError(f"Cannot confirm an order with status {self.status.name}")

        if not self.items:
            raise ValueError("Cannot confirm an empty order")

        # Update status
        self.status = OrderStatus.CONFIRMED

        # Mark as modified
        self.mark_modified()

        # Raise domain event
        self._events.append(
            OrderConfirmedEvent(
                order_id=self.id,
                total_amount=self.total_amount.amount,
                item_count=len(self.items),
            )
        )

    def cancel(self, reason: str) -> None:
        """
        Cancel the order.

        This changes the order status to CANCELLED and raises an event.

        Args:
            reason: The reason for cancellation

        Raises:
            ValueError: If the order is already DELIVERED or CANCELLED
        """
        # Business rules
        if self.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise ValueError(f"Cannot cancel an order with status {self.status.name}")

        # Update status
        self.status = OrderStatus.CANCELLED

        # Mark as modified
        self.mark_modified()

        # Raise domain event
        self._events.append(OrderCancelledEvent(order_id=self.id, reason=reason))

    @property
    def total_amount(self) -> Money:
        """Calculate the total amount for the order."""
        if not self.items:
            return Money(amount=Decimal("0.00"))

        # Sum up all item totals
        return Money(
            amount=sum(item.total_price.amount for item in self.items),
            currency=self.items[0].unit_price.currency,
        )

    @property
    def events(self) -> list[Event]:
        """Get the collected events."""
        return self._events.copy()

    def clear_events(self) -> list[Event]:
        """Get and clear the collected events."""
        events = self._events.copy()
        self._events.clear()
        return events


# ===== Example Usage =====


async def run_example():
    """Run the example demonstrating the Aggregate Root pattern."""
    try:
        logger.info("=== Aggregate Root Example ===")

        # Create a new order
        logger.info("Creating a new order...")
        order = Order.create(customer_id="customer-123")
        logger.info(f"Order created with ID: {order.id}")

        # Get the events
        events = order.clear_events()
        logger.info(f"Events raised: {[e.__class__.__name__ for e in events]}")

        # Add some items
        logger.info("Adding items to the order...")
        order.add_item("product-456", 2, 29.99)
        order.add_item("product-789", 1, 49.99)

        # Get the events
        events = order.clear_events()
        logger.info(f"Events raised: {[e.__class__.__name__ for e in events]}")

        # Show order total
        logger.info(f"Order total: {order.total_amount}")

        # Confirm the order
        logger.info("Confirming the order...")
        order.confirm()

        # Get the events
        events = order.clear_events()
        logger.info(f"Events raised: {[e.__class__.__name__ for e in events]}")

        # Try adding items after confirmation (should fail)
        logger.info("Trying to add items to a confirmed order (should fail)...")
        try:
            order.add_item("product-101", 1, 19.99)
        except ValueError as e:
            logger.info(f"Caught expected error: {e}")

        # Cancel the order
        logger.info("Cancelling the order...")
        order.cancel("Customer request")

        # Get the events
        events = order.clear_events()
        logger.info(f"Events raised: {[e.__class__.__name__ for e in events]}")

        # Show final order state
        logger.info(f"Final order status: {order.status.name}")

    except Exception as e:
        logger.exception(f"Error in example: {e}")


# Run the example
if __name__ == "__main__":
    asyncio.run(run_example())
