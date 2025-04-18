"""
Example of using the event system.

This example demonstrates how to use the event system to implement event-driven
architecture patterns, including:
- Defining and raising domain events
- Creating event handlers
- Event subscription and handling
- Async event processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from uno.core.events import (
    UnoEvent,
    EventPriority,
    event_handler,
    initialize_events,
    get_event_bus,
    publish_event,
    publish_event_sync,
    collect_event,
    publish_collected_events_async,
    EventHandlerScanner,
)


# =============================================================================
# Domain Events
# =============================================================================


class OrderCreatedEvent(UnoEvent):
    """Event raised when a new order is created."""

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


class OrderShippedEvent(UnoEvent):
    """Event raised when an order is shipped."""

    def __init__(
        self, order_id: str, tracking_number: str, shipping_date: datetime, **kwargs
    ):
        """
        Initialize an order shipped event.

        Args:
            order_id: The order ID
            tracking_number: The shipping tracking number
            shipping_date: The shipping date
            **kwargs: Additional event arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.tracking_number = tracking_number
        self.shipping_date = shipping_date


class OrderCancelledEvent(UnoEvent):
    """Event raised when an order is cancelled."""

    def __init__(self, order_id: str, reason: Optional[str] = None, **kwargs):
        """
        Initialize an order cancelled event.

        Args:
            order_id: The order ID
            reason: Optional reason for cancellation
            **kwargs: Additional event arguments
        """
        super().__init__(**kwargs)
        self.order_id = order_id
        self.reason = reason


# =============================================================================
# Event Handlers
# =============================================================================


class NotificationService:
    """Service responsible for sending notifications."""

    def __init__(self):
        """Initialize the notification service."""
        self.notifications = []
        self.logger = logging.getLogger("notification_service")

    async def handle(self, event: OrderCreatedEvent) -> None:
        """
        Handle an order created event by sending a notification.

        Args:
            event: The order created event
        """
        self.logger.info(f"Sending order confirmation email for order {event.order_id}")
        self.notifications.append(
            {
                "type": "email",
                "recipient": f"customer_{event.customer_id}@example.com",
                "subject": "Order Confirmation",
                "body": f"Your order #{event.order_id} has been received.",
            }
        )


class InventoryService:
    """Service responsible for managing inventory."""

    def __init__(self):
        """Initialize the inventory service."""
        self.inventory_updates = []
        self.logger = logging.getLogger("inventory_service")

    def handle(self, event: OrderCreatedEvent) -> None:
        """
        Handle an order created event by updating inventory.

        Args:
            event: The order created event
        """
        self.logger.info(f"Updating inventory for order {event.order_id}")
        for item in event.items:
            self.inventory_updates.append(
                {"product_id": item["product_id"], "quantity": -item["quantity"]}
            )


class AnalyticsService:
    """Service responsible for tracking analytics."""

    def __init__(self):
        """Initialize the analytics service."""
        self.events = []
        self.logger = logging.getLogger("analytics_service")

    @event_handler(OrderCreatedEvent)
    async def track_order_created(self, event: OrderCreatedEvent) -> None:
        """
        Track an order created event.

        Args:
            event: The order created event
        """
        self.logger.info(f"Tracking order created event for order {event.order_id}")
        self.events.append(
            {
                "event_type": "order_created",
                "order_id": event.order_id,
                "customer_id": event.customer_id,
                "total_amount": event.total_amount,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @event_handler(OrderShippedEvent)
    async def track_order_shipped(self, event: OrderShippedEvent) -> None:
        """
        Track an order shipped event.

        Args:
            event: The order shipped event
        """
        self.logger.info(f"Tracking order shipped event for order {event.order_id}")
        self.events.append(
            {
                "event_type": "order_shipped",
                "order_id": event.order_id,
                "tracking_number": event.tracking_number,
                "shipping_date": event.shipping_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @event_handler(OrderCancelledEvent, priority=EventPriority.HIGH)
    async def track_order_cancelled(self, event: OrderCancelledEvent) -> None:
        """
        Track an order cancelled event with high priority.

        Args:
            event: The order cancelled event
        """
        self.logger.info(f"Tracking order cancelled event for order {event.order_id}")
        self.events.append(
            {
                "event_type": "order_cancelled",
                "order_id": event.order_id,
                "reason": event.reason,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


# Function-based handlers
@event_handler(OrderShippedEvent)
async def send_shipping_notification(event: OrderShippedEvent) -> None:
    """
    Send a shipping notification when an order is shipped.

    Args:
        event: The order shipped event
    """
    logging.info(f"Sending shipping notification for order {event.order_id}")
    # In a real implementation, this would send an email or push notification
    print(
        f"Order {event.order_id} has been shipped! Tracking number: {event.tracking_number}"
    )


@event_handler(OrderCancelledEvent)
def refund_payment(event: OrderCancelledEvent) -> None:
    """
    Process refund when an order is cancelled.

    Args:
        event: The order cancelled event
    """
    logging.info(f"Processing refund for cancelled order {event.order_id}")
    # In a real implementation, this would call a payment gateway
    print(f"Refund processed for order {event.order_id}")


# =============================================================================
# Order Service (using events)
# =============================================================================


class OrderService:
    """Service responsible for managing orders."""

    def __init__(self):
        """Initialize the order service."""
        self.orders = {}
        self.logger = logging.getLogger("order_service")

    async def create_order(self, customer_id: str, items: List[Dict[str, Any]]) -> str:
        """
        Create a new order and raise an OrderCreatedEvent.

        Args:
            customer_id: The customer ID
            items: The order items

        Returns:
            The new order ID
        """
        # Generate order ID
        order_id = f"order_{len(self.orders) + 1}"

        # Calculate total amount
        total_amount = sum(item["price"] * item["quantity"] for item in items)

        # Create order
        self.orders[order_id] = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": items,
            "total_amount": total_amount,
            "status": "created",
            "created_at": datetime.utcnow(),
        }

        self.logger.info(f"Created order {order_id} for customer {customer_id}")

        # Raise event
        event = OrderCreatedEvent(
            order_id=order_id,
            customer_id=customer_id,
            items=items,
            total_amount=total_amount,
        )
        publish_event(event)

        return order_id

    async def ship_order(self, order_id: str, tracking_number: str) -> None:
        """
        Ship an order and raise an OrderShippedEvent.

        Args:
            order_id: The order ID
            tracking_number: The shipping tracking number
        """
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")

        # Update order status
        self.orders[order_id]["status"] = "shipped"
        self.orders[order_id]["tracking_number"] = tracking_number
        self.orders[order_id]["shipped_at"] = datetime.utcnow()

        self.logger.info(
            f"Shipped order {order_id} with tracking number {tracking_number}"
        )

        # Raise event
        event = OrderShippedEvent(
            order_id=order_id,
            tracking_number=tracking_number,
            shipping_date=self.orders[order_id]["shipped_at"],
        )
        publish_event_sync(event)

    async def cancel_order(self, order_id: str, reason: Optional[str] = None) -> None:
        """
        Cancel an order and raise an OrderCancelledEvent.

        Args:
            order_id: The order ID
            reason: Optional reason for cancellation
        """
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")

        # Update order status
        self.orders[order_id]["status"] = "cancelled"
        if reason:
            self.orders[order_id]["cancel_reason"] = reason
        self.orders[order_id]["cancelled_at"] = datetime.utcnow()

        self.logger.info(f"Cancelled order {order_id}")

        # Raise event
        event = OrderCancelledEvent(order_id=order_id, reason=reason)
        # Collect for batch processing
        collect_event(event)


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

    # Create services
    notification_service = NotificationService()
    inventory_service = InventoryService()
    analytics_service = AnalyticsService()
    order_service = OrderService()

    # Subscribe handlers
    event_bus = get_event_bus()
    event_bus.subscribe(OrderCreatedEvent, notification_service)
    event_bus.subscribe(OrderCreatedEvent, inventory_service)

    # Scan analytics service for decorated handlers
    scanner = EventHandlerScanner(event_bus)
    scanner.scan_instance(analytics_service)

    # Scan this module for function-based handlers
    scanner.scan_module(__import__(__name__))

    # Create an order
    order_id = await order_service.create_order(
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
    )

    # Wait for async events to be processed
    await asyncio.sleep(0.1)

    # Ship the order
    await order_service.ship_order(order_id, "TRACK123456")

    # Cancel another order
    await order_service.cancel_order("order_1", "Customer requested cancellation")

    # Process collected events (like order cancellations)
    await publish_collected_events_async()

    # Wait for async events to be processed
    await asyncio.sleep(0.1)

    # Print results
    print("\nNotifications:")
    for notification in notification_service.notifications:
        print(
            f"  - {notification['type']} to {notification['recipient']}: {notification['subject']}"
        )

    print("\nInventory Updates:")
    for update in inventory_service.inventory_updates:
        print(f"  - Product {update['product_id']}: {update['quantity']}")

    print("\nAnalytics Events:")
    for event in analytics_service.events:
        print(f"  - {event['event_type']} for order {event['order_id']}")

    print("\nFinal Order Status:")
    for order_id, order in order_service.orders.items():
        print(f"  - Order {order_id}: {order['status']}")


if __name__ == "__main__":
    asyncio.run(main())
