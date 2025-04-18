"""
Example of using the CQRS pattern implementation.

This example demonstrates how to use the CQRS (Command Query Responsibility Segregation)
pattern implementation to build a simple order management system, including:
- Defining commands and queries
- Implementing command and query handlers
- Setting up command and query buses
- Using the mediator pattern
- Handling domain events
"""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set

from uno.core.cqrs import (
    BaseCommand,
    BaseQuery,
    BaseCommandHandler,
    BaseQueryHandler,
    CommandBus,
    QueryBus,
    HandlerRegistry,
    Mediator,
    command_handler,
    query_handler,
    initialize_mediator,
    get_mediator,
    execute_command,
    execute_query,
)
from uno.core.events import (
    UnoEvent,
    EventPublisher,
    EventPriority,
    event_handler,
    initialize_events,
    get_event_publisher,
)


# =============================================================================
# Domain Models
# =============================================================================


class OrderStatus(Enum):
    """Possible order statuses."""

    CREATED = "created"
    APPROVED = "approved"
    REJECTED = "rejected"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# =============================================================================
# Events
# =============================================================================


class OrderCreatedEvent(UnoEvent):
    """Event raised when an order is created."""

    def __init__(
        self,
        order_id: str,
        customer_id: str,
        items: List[Dict[str, Any]],
        total_amount: float,
        **kwargs,
    ):
        """
        Initialize an order created event.

        Args:
            order_id: The order ID
            customer_id: The customer ID
            items: The order items
            total_amount: The total order amount
            **kwargs: Additional event arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items
        self.total_amount = total_amount


class OrderStatusChangedEvent(UnoEvent):
    """Event raised when an order's status changes."""

    def __init__(
        self,
        order_id: str,
        old_status: OrderStatus,
        new_status: OrderStatus,
        reason: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize an order status changed event.

        Args:
            order_id: The order ID
            old_status: The old status
            new_status: The new status
            reason: Optional reason for the status change
            **kwargs: Additional event arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.old_status = old_status
        self.new_status = new_status
        self.reason = reason


# =============================================================================
# Commands
# =============================================================================


class CreateOrderCommand(BaseCommand[str]):
    """Command to create a new order."""

    def __init__(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        **kwargs,
    ):
        """
        Initialize a create order command.

        Args:
            customer_id: The customer ID
            items: The order items
            shipping_address: The shipping address
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.customer_id = customer_id
        self.items = items
        self.shipping_address = shipping_address


class ApproveOrderCommand(BaseCommand[bool]):
    """Command to approve an order."""

    def __init__(self, order_id: str, **kwargs):
        """
        Initialize an approve order command.

        Args:
            order_id: The order ID
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id


class RejectOrderCommand(BaseCommand[bool]):
    """Command to reject an order."""

    def __init__(self, order_id: str, reason: str, **kwargs):
        """
        Initialize a reject order command.

        Args:
            order_id: The order ID
            reason: The reason for rejection
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.reason = reason


class ShipOrderCommand(BaseCommand[bool]):
    """Command to mark an order as shipped."""

    def __init__(self, order_id: str, tracking_number: str, carrier: str, **kwargs):
        """
        Initialize a ship order command.

        Args:
            order_id: The order ID
            tracking_number: The shipping tracking number
            carrier: The shipping carrier
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.tracking_number = tracking_number
        self.carrier = carrier


class CancelOrderCommand(BaseCommand[bool]):
    """Command to cancel an order."""

    def __init__(self, order_id: str, reason: Optional[str] = None, **kwargs):
        """
        Initialize a cancel order command.

        Args:
            order_id: The order ID
            reason: Optional reason for cancellation
            **kwargs: Additional command arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.reason = reason


# =============================================================================
# Queries
# =============================================================================


class GetOrderQuery(BaseQuery[Dict[str, Any]]):
    """Query to get an order by ID."""

    def __init__(self, order_id: str, **kwargs):
        """
        Initialize a get order query.

        Args:
            order_id: The order ID
            **kwargs: Additional query arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id


class GetOrdersByCustomerQuery(BaseQuery[List[Dict[str, Any]]]):
    """Query to get orders by customer ID."""

    def __init__(
        self,
        customer_id: str,
        status: Optional[OrderStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize a get orders by customer query.

        Args:
            customer_id: The customer ID
            status: Optional status filter
            limit: Optional limit on number of orders to return
            offset: Optional offset for pagination
            **kwargs: Additional query arguments
        """
        super().__init__(**kwargs)
        self.customer_id = customer_id
        self.status = status
        self.limit = limit
        self.offset = offset


class GetOrdersByStatusQuery(BaseQuery[List[Dict[str, Any]]]):
    """Query to get orders by status."""

    def __init__(
        self,
        status: OrderStatus,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize a get orders by status query.

        Args:
            status: The status to filter by
            limit: Optional limit on number of orders to return
            offset: Optional offset for pagination
            **kwargs: Additional query arguments
        """
        super().__init__(**kwargs)
        self.status = status
        self.limit = limit
        self.offset = offset


# =============================================================================
# Command Handlers
# =============================================================================


class OrderCommandHandler(BaseCommandHandler[CreateOrderCommand, str]):
    """Handler for order creation commands."""

    def __init__(self, event_publisher: EventPublisher):
        """
        Initialize the handler.

        Args:
            event_publisher: The event publisher
        """
        super().__init__(event_publisher)
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1

    async def handle(self, command: CreateOrderCommand) -> str:
        """
        Handle a create order command.

        Args:
            command: The command to handle

        Returns:
            The new order ID
        """
        # Generate order ID
        order_id = f"order_{self.next_id}"
        self.next_id += 1

        # Calculate total amount
        total_amount = sum(
            item.get("price", 0) * item.get("quantity", 0) for item in command.items
        )

        # Create order
        self.orders[order_id] = {
            "id": order_id,
            "customer_id": command.customer_id,
            "items": command.items,
            "shipping_address": command.shipping_address,
            "total_amount": total_amount,
            "status": OrderStatus.CREATED.value,
            "created_at": command.timestamp.isoformat(),
            "status_history": [
                {
                    "status": OrderStatus.CREATED.value,
                    "timestamp": command.timestamp.isoformat(),
                }
            ],
        }

        # Add event
        self.add_event(
            OrderCreatedEvent(
                order_id=order_id,
                customer_id=command.customer_id,
                items=command.items,
                total_amount=total_amount,
            )
        )

        # Publish events
        await self.publish_events()

        return order_id


class OrderStatusCommandHandler:
    """Handler for order status commands."""

    def __init__(
        self, orders: Dict[str, Dict[str, Any]], event_publisher: EventPublisher
    ):
        """
        Initialize the handler.

        Args:
            orders: The orders repository
            event_publisher: The event publisher
        """
        self.orders = orders
        self.event_publisher = event_publisher
        self.pending_events: List[Event] = []

    def add_event(self, event: Event) -> None:
        """
        Add an event to be published.

        Args:
            event: The event to add
        """
        self.pending_events.append(event)

    async def publish_events(self) -> None:
        """Publish all pending events."""
        for event in self.pending_events:
            self.event_publisher.publish(event)

        self.pending_events.clear()

    @command_handler(ApproveOrderCommand)
    async def approve_order(self, command: ApproveOrderCommand) -> bool:
        """
        Approve an order.

        Args:
            command: The command to handle

        Returns:
            True if the order was approved, False otherwise
        """
        if command.order_id not in self.orders:
            return False

        order = self.orders[command.order_id]

        # Check if the order can be approved
        if order["status"] != OrderStatus.CREATED.value:
            return False

        # Update order status
        old_status = OrderStatus(order["status"])
        new_status = OrderStatus.APPROVED

        order["status"] = new_status.value
        order["approved_at"] = command.timestamp.isoformat()
        order["status_history"].append(
            {"status": new_status.value, "timestamp": command.timestamp.isoformat()}
        )

        # Add event
        self.add_event(
            OrderStatusChangedEvent(
                order_id=command.order_id, old_status=old_status, new_status=new_status
            )
        )

        # Publish events
        await self.publish_events()

        return True

    @command_handler(RejectOrderCommand)
    async def reject_order(self, command: RejectOrderCommand) -> bool:
        """
        Reject an order.

        Args:
            command: The command to handle

        Returns:
            True if the order was rejected, False otherwise
        """
        if command.order_id not in self.orders:
            return False

        order = self.orders[command.order_id]

        # Check if the order can be rejected
        if order["status"] != OrderStatus.CREATED.value:
            return False

        # Update order status
        old_status = OrderStatus(order["status"])
        new_status = OrderStatus.REJECTED

        order["status"] = new_status.value
        order["rejected_at"] = command.timestamp.isoformat()
        order["rejection_reason"] = command.reason
        order["status_history"].append(
            {
                "status": new_status.value,
                "timestamp": command.timestamp.isoformat(),
                "reason": command.reason,
            }
        )

        # Add event
        self.add_event(
            OrderStatusChangedEvent(
                order_id=command.order_id,
                old_status=old_status,
                new_status=new_status,
                reason=command.reason,
            )
        )

        # Publish events
        await self.publish_events()

        return True

    @command_handler(ShipOrderCommand)
    async def ship_order(self, command: ShipOrderCommand) -> bool:
        """
        Mark an order as shipped.

        Args:
            command: The command to handle

        Returns:
            True if the order was marked as shipped, False otherwise
        """
        if command.order_id not in self.orders:
            return False

        order = self.orders[command.order_id]

        # Check if the order can be shipped
        if order["status"] != OrderStatus.APPROVED.value:
            return False

        # Update order status
        old_status = OrderStatus(order["status"])
        new_status = OrderStatus.SHIPPED

        order["status"] = new_status.value
        order["shipped_at"] = command.timestamp.isoformat()
        order["tracking_number"] = command.tracking_number
        order["carrier"] = command.carrier
        order["status_history"].append(
            {
                "status": new_status.value,
                "timestamp": command.timestamp.isoformat(),
                "tracking_number": command.tracking_number,
                "carrier": command.carrier,
            }
        )

        # Add event
        self.add_event(
            OrderStatusChangedEvent(
                order_id=command.order_id, old_status=old_status, new_status=new_status
            )
        )

        # Publish events
        await self.publish_events()

        return True

    @command_handler(CancelOrderCommand)
    async def cancel_order(self, command: CancelOrderCommand) -> bool:
        """
        Cancel an order.

        Args:
            command: The command to handle

        Returns:
            True if the order was cancelled, False otherwise
        """
        if command.order_id not in self.orders:
            return False

        order = self.orders[command.order_id]

        # Check if the order can be cancelled
        allowed_statuses = [OrderStatus.CREATED.value, OrderStatus.APPROVED.value]

        if order["status"] not in allowed_statuses:
            return False

        # Update order status
        old_status = OrderStatus(order["status"])
        new_status = OrderStatus.CANCELLED

        order["status"] = new_status.value
        order["cancelled_at"] = command.timestamp.isoformat()

        if command.reason:
            order["cancellation_reason"] = command.reason

        order["status_history"].append(
            {
                "status": new_status.value,
                "timestamp": command.timestamp.isoformat(),
                "reason": command.reason,
            }
        )

        # Add event
        self.add_event(
            OrderStatusChangedEvent(
                order_id=command.order_id,
                old_status=old_status,
                new_status=new_status,
                reason=command.reason,
            )
        )

        # Publish events
        await self.publish_events()

        return True


# =============================================================================
# Query Handlers
# =============================================================================


class OrderQueryHandler:
    """Handler for order queries."""

    def __init__(self, orders: Dict[str, Dict[str, Any]]):
        """
        Initialize the handler.

        Args:
            orders: The orders repository
        """
        self.orders = orders

    @query_handler(GetOrderQuery)
    async def get_order(self, query: GetOrderQuery) -> Dict[str, Any]:
        """
        Get an order by ID.

        Args:
            query: The query to handle

        Returns:
            The order data, or an empty dict if not found
        """
        return self.orders.get(query.order_id, {})

    @query_handler(GetOrdersByCustomerQuery)
    async def get_orders_by_customer(
        self, query: GetOrdersByCustomerQuery
    ) -> List[Dict[str, Any]]:
        """
        Get orders by customer ID.

        Args:
            query: The query to handle

        Returns:
            List of matching orders
        """
        # Filter orders by customer ID
        customer_orders = [
            order
            for order in self.orders.values()
            if order["customer_id"] == query.customer_id
        ]

        # Apply status filter if provided
        if query.status is not None:
            customer_orders = [
                order
                for order in customer_orders
                if order["status"] == query.status.value
            ]

        # Sort by creation date (newest first)
        customer_orders.sort(key=lambda o: o["created_at"], reverse=True)

        # Apply pagination
        if query.offset is not None:
            customer_orders = customer_orders[query.offset :]

        if query.limit is not None:
            customer_orders = customer_orders[: query.limit]

        return customer_orders

    @query_handler(GetOrdersByStatusQuery)
    async def get_orders_by_status(
        self, query: GetOrdersByStatusQuery
    ) -> List[Dict[str, Any]]:
        """
        Get orders by status.

        Args:
            query: The query to handle

        Returns:
            List of matching orders
        """
        # Filter orders by status
        status_orders = [
            order
            for order in self.orders.values()
            if order["status"] == query.status.value
        ]

        # Sort by creation date (newest first)
        status_orders.sort(key=lambda o: o["created_at"], reverse=True)

        # Apply pagination
        if query.offset is not None:
            status_orders = status_orders[query.offset :]

        if query.limit is not None:
            status_orders = status_orders[: query.limit]

        return status_orders


# =============================================================================
# Event Handlers
# =============================================================================


class NotificationService:
    """Service for sending notifications."""

    def __init__(self):
        """Initialize the service."""
        self.notifications: List[Dict[str, Any]] = []

    @event_handler(OrderCreatedEvent)
    async def notify_order_created(self, event: OrderCreatedEvent) -> None:
        """
        Send a notification when an order is created.

        Args:
            event: The event to handle
        """
        self.notifications.append(
            {
                "type": "order_created",
                "order_id": event.order_id,
                "customer_id": event.customer_id,
                "timestamp": event.timestamp.isoformat(),
                "message": f"Order {event.order_id} has been created. Total amount: ${event.total_amount:.2f}",
            }
        )

        print(
            f"Notification: Order {event.order_id} created for customer {event.customer_id}"
        )

    @event_handler(OrderStatusChangedEvent)
    async def notify_status_change(self, event: OrderStatusChangedEvent) -> None:
        """
        Send a notification when an order's status changes.

        Args:
            event: The event to handle
        """
        message = f"Order {event.order_id} status changed from {event.old_status.value} to {event.new_status.value}"

        if event.reason:
            message += f". Reason: {event.reason}"

        self.notifications.append(
            {
                "type": "status_changed",
                "order_id": event.order_id,
                "old_status": event.old_status.value,
                "new_status": event.new_status.value,
                "timestamp": event.timestamp.isoformat(),
                "message": message,
            }
        )

        print(f"Notification: {message}")


class InventoryService:
    """Service for managing inventory."""

    def __init__(self):
        """Initialize the service."""
        self.inventory_updates: List[Dict[str, Any]] = []

    @event_handler(OrderCreatedEvent)
    async def reserve_inventory(self, event: OrderCreatedEvent) -> None:
        """
        Reserve inventory for a new order.

        Args:
            event: The event to handle
        """
        for item in event.items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)

            if not product_id or quantity <= 0:
                continue

            self.inventory_updates.append(
                {
                    "type": "reserve",
                    "product_id": product_id,
                    "quantity": quantity,
                    "order_id": event.order_id,
                    "timestamp": event.timestamp.isoformat(),
                }
            )

            print(
                f"Inventory: Reserved {quantity} units of product {product_id} for order {event.order_id}"
            )

    @event_handler(OrderStatusChangedEvent, priority=EventPriority.HIGH)
    async def update_inventory_on_status_change(
        self, event: OrderStatusChangedEvent
    ) -> None:
        """
        Update inventory when an order's status changes.

        Args:
            event: The event to handle
        """
        # Release inventory if order is cancelled or rejected
        if event.new_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            # In a real system, we would look up the items in the order
            # For this example, we'll just log the action
            print(
                f"Inventory: Released reserved inventory for order {event.order_id} due to {event.new_status.value}"
            )

            self.inventory_updates.append(
                {
                    "type": "release",
                    "order_id": event.order_id,
                    "status": event.new_status.value,
                    "timestamp": event.timestamp.isoformat(),
                }
            )

        # Commit inventory reduction if order is shipped
        elif event.new_status == OrderStatus.SHIPPED:
            print(
                f"Inventory: Committed inventory reduction for order {event.order_id}"
            )

            self.inventory_updates.append(
                {
                    "type": "commit",
                    "order_id": event.order_id,
                    "status": event.new_status.value,
                    "timestamp": event.timestamp.isoformat(),
                }
            )


# =============================================================================
# Example Usage
# =============================================================================


async def main():
    """Run the example."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize the event system
    initialize_events()
    event_publisher = get_event_publisher()

    # Create command and query buses
    command_bus = CommandBus()
    query_bus = QueryBus()

    # Create order repository (shared between handlers)
    orders = {}

    # Create and register command handlers
    order_handler = OrderCommandHandler(event_publisher)
    command_bus.register(CreateOrderCommand, order_handler)

    status_handler = OrderStatusCommandHandler(orders, event_publisher)

    # Create and register query handlers
    query_handler = OrderQueryHandler(orders)

    # Create registry and scan handlers
    registry = HandlerRegistry(command_bus, query_bus)
    registry.scan_instance(status_handler)
    registry.scan_instance(query_handler)

    # Initialize the mediator
    initialize_mediator(command_bus, query_bus)
    mediator = get_mediator()

    # Create notification and inventory services
    notification_service = NotificationService()
    inventory_service = InventoryService()

    # Register event handlers
    from uno.core.events import EventHandlerScanner

    scanner = EventHandlerScanner(get_event_bus())
    scanner.scan_instance(notification_service)
    scanner.scan_instance(inventory_service)

    # Create an order
    print("\n=== Creating an order ===")
    create_command = CreateOrderCommand(
        customer_id="customer123",
        items=[
            {
                "product_id": "product1",
                "name": "Product 1",
                "price": 19.99,
                "quantity": 2,
            },
            {
                "product_id": "product2",
                "name": "Product 2",
                "price": 29.99,
                "quantity": 1,
            },
        ],
        shipping_address={
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "US",
        },
    )

    order_id = await execute_command(create_command)
    print(f"Created order: {order_id}")

    # Wait for async event handlers
    await asyncio.sleep(0.1)

    # Get the order
    print("\n=== Getting the order ===")
    get_query = GetOrderQuery(order_id=order_id)
    order = await execute_query(get_query)

    print(
        f"Order details: ID={order['id']}, Status={order['status']}, Amount=${order['total_amount']:.2f}"
    )
    print(f"Items: {len(order['items'])}")
    for item in order["items"]:
        print(f"  - {item['name']}: ${item['price']} x {item['quantity']}")

    # Approve the order
    print("\n=== Approving the order ===")
    approve_command = ApproveOrderCommand(order_id=order_id)
    result = await execute_command(approve_command)
    print(f"Order approved: {result}")

    # Wait for async event handlers
    await asyncio.sleep(0.1)

    # Get the updated order
    order = await execute_query(get_query)
    print(f"Order status: {order['status']}")

    # Ship the order
    print("\n=== Shipping the order ===")
    ship_command = ShipOrderCommand(
        order_id=order_id, tracking_number="TRACK123456", carrier="Express Shipping"
    )
    result = await execute_command(ship_command)
    print(f"Order shipped: {result}")

    # Wait for async event handlers
    await asyncio.sleep(0.1)

    # Get the updated order
    order = await execute_query(get_query)
    print(f"Order status: {order['status']}")
    print(f"Tracking: {order['tracking_number']} via {order['carrier']}")

    # Create another order and reject it
    print("\n=== Creating and rejecting another order ===")
    create_command = CreateOrderCommand(
        customer_id="customer456",
        items=[
            {
                "product_id": "product3",
                "name": "Product 3",
                "price": 99.99,
                "quantity": 1,
            }
        ],
        shipping_address={
            "street": "456 Oak St",
            "city": "Othertown",
            "state": "NY",
            "zip": "67890",
            "country": "US",
        },
    )

    order_id2 = await execute_command(create_command)
    print(f"Created order: {order_id2}")

    # Wait for async event handlers
    await asyncio.sleep(0.1)

    # Reject the order
    reject_command = RejectOrderCommand(order_id=order_id2, reason="Payment declined")
    result = await execute_command(reject_command)
    print(f"Order rejected: {result}")

    # Wait for async event handlers
    await asyncio.sleep(0.1)

    # Get orders by customer
    print("\n=== Getting orders by customer ===")
    customer_query = GetOrdersByCustomerQuery(customer_id="customer123")
    customer_orders = await execute_query(customer_query)

    print(f"Found {len(customer_orders)} orders for customer123:")
    for order in customer_orders:
        print(
            f"  - Order {order['id']}: Status={order['status']}, Amount=${order['total_amount']:.2f}"
        )

    # Get orders by status
    print("\n=== Getting orders by status ===")
    status_query = GetOrdersByStatusQuery(status=OrderStatus.SHIPPED)
    shipped_orders = await execute_query(status_query)

    print(f"Found {len(shipped_orders)} shipped orders:")
    for order in shipped_orders:
        print(f"  - Order {order['id']} for customer {order['customer_id']}")

    # Display notifications
    print("\n=== Notifications sent ===")
    for notification in notification_service.notifications:
        print(f"  - {notification['type']}: {notification['message']}")

    # Display inventory updates
    print("\n=== Inventory updates ===")
    for update in inventory_service.inventory_updates:
        print(f"  - {update['type']} operation for order {update['order_id']}")


if __name__ == "__main__":
    asyncio.run(main())
