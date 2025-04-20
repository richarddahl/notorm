"""
Example demonstrating the use of the Unit of Work pattern with Domain entities.

This example shows how to use the new AbstractUnitOfWork from the uno.core.uow
package with domain entities and repositories. It demonstrates how to:

1. Create repositories for domain entities
2. Register repositories with the Unit of Work
3. Use the Unit of Work to manage transactions
4. Collect and publish domain events
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Optional, Set, Type, TypeVar
from uuid import uuid4

from uno.core.events import Event, AsyncEventBus, EventPublisher
from uno.core.protocols import Repository
from uno.core.uow import (
    AbstractUnitOfWork,
    InMemoryUnitOfWork,
    transaction,
    unit_of_work,
)
from uno.domain.entity import EntityBase, Identity

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")


# ===== Domain Model =====


class OrderId(Identity[str]):
    """Order identifier value object."""

    pass


class Order(EntityBase[str]):
    """Example Order entity."""

    customer_id: str
    items: list[dict[str, any]] = field(default_factory=list)
    status: str = "new"
    total_amount: float = 0.0

    @classmethod
    def create(cls, customer_id: str) -> "Order":
        """Create a new order."""
        return cls(
            id=str(uuid4()), customer_id=customer_id, created_at=datetime.now(UTC)
        )

    def add_item(self, product_id: str, quantity: int, price: float) -> None:
        """Add an item to the order."""
        # Add the item
        self.items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "price": price,
                "total": quantity * price,
            }
        )

        # Update total
        self.total_amount = sum(item["total"] for item in self.items)

        # Mark as modified
        self.mark_modified()

        # Record an event
        self.record_change("items", [], self.items)


# ===== Domain Events =====


class OrderCreatedEvent(Event):
    """Event raised when an order is created."""

    order_id: str
    customer_id: str
    timestamp: datetime


class OrderItemAddedEvent(Event):
    """Event raised when an item is added to an order."""

    order_id: str
    product_id: str
    quantity: int
    price: float


# ===== Repositories =====


class InMemoryOrderRepository(Repository[Order, str]):
    """In-memory implementation of order repository."""

    def __init__(self):
        """Initialize with empty storage."""
        self.orders: dict[str, Order] = {}
        self.events: list[Event] = []

    async def get_by_id(self, id: str) -> Optional[Order]:
        """Get an order by ID."""
        return self.orders.get(id)

    async def list(self, filters=None, options=None) -> list[Order]:
        """List orders with optional filtering."""
        # Simple implementation without filtering for this example
        return list(self.orders.values())

    async def add(self, entity: Order) -> Order:
        """Add a new order."""
        self.orders[entity.id] = entity
        # Simulate domain event creation
        self.events.append(
            OrderCreatedEvent(
                order_id=entity.id,
                customer_id=entity.customer_id,
                timestamp=entity.created_at,
            )
        )
        return entity

    async def update(self, entity: Order) -> Order:
        """Update an existing order."""
        # Check for changes requiring events
        if hasattr(entity, "get_changes") and callable(entity.get_changes):
            changes = entity.get_changes()
            if "items" in changes:
                for item in entity.items:
                    # This is simplified - in a real system you'd check what actually changed
                    self.events.append(
                        OrderItemAddedEvent(
                            order_id=entity.id,
                            product_id=item["product_id"],
                            quantity=item["quantity"],
                            price=item["price"],
                        )
                    )

        self.orders[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete an order by ID."""
        if id in self.orders:
            del self.orders[id]
            return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if an order exists."""
        return id in self.orders

    async def count(self, filters=None) -> int:
        """Count orders with optional filtering."""
        return len(self.orders)

    def collect_events(self) -> list[Event]:
        """Collect domain events from the repository."""
        events = list(self.events)
        self.events.clear()
        return events


# ===== Application Services =====


class OrderService:
    """Service for order management."""

    def __init__(self, uow_factory):
        """Initialize with Unit of Work factory."""
        self.uow_factory = uow_factory

    @unit_of_work(lambda: order_uow_factory())
    async def create_order(self, customer_id: str, uow: AbstractUnitOfWork) -> Order:
        """
        Create a new order.

        This method uses the Unit of Work decorator for transaction management.
        """
        # Get repository from UoW
        repo = uow.get_repository(InMemoryOrderRepository)

        # Create order
        order = Order.create(customer_id=customer_id)

        # Add to repository
        await repo.add(order)

        # The Unit of Work decorator will automatically commit and publish events
        return order

    async def add_item_to_order(
        self, order_id: str, product_id: str, quantity: int, price: float
    ) -> Order:
        """
        Add an item to an order.

        This method uses the transaction context manager for transaction management.
        """
        async with transaction(lambda: order_uow_factory()) as uow:
            # Get repository from UoW
            repo = uow.get_repository(InMemoryOrderRepository)

            # Get order
            order = await repo.get_by_id(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")

            # Add item
            order.add_item(product_id, quantity, price)

            # Update order
            await repo.update(order)

            # The transaction context manager will automatically commit and publish events
            return order

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID."""
        async with transaction(lambda: order_uow_factory()) as uow:
            repo = uow.get_repository(InMemoryOrderRepository)
            return await repo.get_by_id(order_id)

    async def list_orders(self) -> list[Order]:
        """List all orders."""
        async with transaction(lambda: order_uow_factory()) as uow:
            repo = uow.get_repository(InMemoryOrderRepository)
            return await repo.list()


# ===== Event Handlers =====


async def handle_order_created(event: OrderCreatedEvent) -> None:
    """Handle order created events."""
    logger.info(f"Order created: {event.order_id} for customer {event.customer_id}")


async def handle_order_item_added(event: OrderItemAddedEvent) -> None:
    """Handle order item added events."""
    logger.info(
        f"Item added to order {event.order_id}: {event.product_id}, "
        f"quantity: {event.quantity}, price: {event.price}"
    )


# ===== Setup =====

# Create event bus
event_bus = AsyncEventBus()

# Register event handlers
event_bus.subscribe("OrderCreatedEvent", handle_order_created)
event_bus.subscribe("OrderItemAddedEvent", handle_order_item_added)

# Create repository
order_repository = InMemoryOrderRepository()


# Factory function for creating Unit of Work
def order_uow_factory() -> AbstractUnitOfWork:
    """Create a Unit of Work with order repository."""
    uow = InMemoryUnitOfWork(event_bus=event_bus)
    uow.register_repository(InMemoryOrderRepository, order_repository)
    return uow


# Create order service
order_service = OrderService(order_uow_factory)


# ===== Example Usage =====


async def run_example():
    """Run the example."""
    try:
        # Create an order
        logger.info("Creating an order...")
        order = await order_service.create_order("customer-123")
        logger.info(f"Order created with ID: {order.id}")

        # Add items to the order
        logger.info("Adding items to the order...")
        order = await order_service.add_item_to_order(order.id, "product-456", 2, 29.99)
        order = await order_service.add_item_to_order(order.id, "product-789", 1, 49.99)

        # Get the final order
        final_order = await order_service.get_order(order.id)
        logger.info(
            f"Final order {final_order.id} has {len(final_order.items)} items "
            f"and total amount {final_order.total_amount}"
        )

        # List all orders
        orders = await order_service.list_orders()
        logger.info(f"Total orders: {len(orders)}")

    except Exception as e:
        logger.exception(f"Error in example: {e}")


# Run the example
if __name__ == "__main__":
    asyncio.run(run_example())
