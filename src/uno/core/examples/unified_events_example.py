"""
Example of using the unified event system.

This example demonstrates how to use the unified event system to implement
event-driven architecture patterns, including:
- Defining domain events
- Creating event handlers (class-based and function-based)
- Event subscription and handling
- Topic-based event routing
- Priority-based event handling
- Event persistence
- Batch event processing
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from uuid import uuid4

from uno.core.unified_events import (
    UnoDomainEvent,
    EventBus,
    EventHandler,
    EventPublisher,
    InMemoryEventStore,
    EventPriority,
    EventSubscriber,
    EventHandlerScanner,
    event_handler,
    initialize_events,
    get_event_bus,
    get_event_publisher,
    get_event_store,
    publish_event,
    publish_event_sync,
    collect_event,
    publish_collected_events_async,
)


# =============================================================================
# Domain Events
# =============================================================================


class UserEvent(UnoDomainEvent):
    """Base class for user-related events."""

    user_id: str


class UserCreatedEvent(UserEvent):
    """Event raised when a new user is created."""

    email: str
    username: str


class UserUpdatedEvent(UserEvent):
    """Event raised when a user is updated."""

    fields_updated: List[str]


class UserDeletedEvent(UserEvent):
    """Event raised when a user is deleted."""

    reason: Optional[str] = None


class OrderEvent(UnoDomainEvent):
    """Base class for order-related events."""

    order_id: str
    user_id: str


class OrderCreatedEvent(OrderEvent):
    """Event raised when a new order is created."""

    items: List[Dict[str, Any]]
    total_amount: float


class OrderShippedEvent(OrderEvent):
    """Event raised when an order is shipped."""

    tracking_number: str
    shipping_date: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderCancelledEvent(OrderEvent):
    """Event raised when an order is cancelled."""

    reason: Optional[str] = None


# =============================================================================
# Event Handlers
# =============================================================================


class NotificationService:
    """Service responsible for sending notifications."""

    def __init__(self):
        """Initialize the notification service."""
        self.notifications: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("notification_service")

    async def send_notification(self, recipient: str, subject: str, body: str) -> None:
        """
        Send a notification.

        Args:
            recipient: Notification recipient
            subject: Notification subject
            body: Notification body
        """
        self.logger.info(f"Sending notification to {recipient}: {subject}")
        self.notifications.append(
            {
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "sent_at": datetime.now(UTC),
            }
        )


class UserNotificationHandler(EventHandler[UserCreatedEvent]):
    """Handler for user-related notifications."""

    def __init__(self, notification_service: NotificationService):
        """
        Initialize the handler.

        Args:
            notification_service: Service for sending notifications
        """
        super().__init__(UserCreatedEvent)
        self.notification_service = notification_service

    async def handle(self, event: UserCreatedEvent) -> None:
        """
        Handle user created event by sending a welcome notification.

        Args:
            event: The user created event
        """
        await self.notification_service.send_notification(
            recipient=event.email,
            subject="Welcome to Our Platform",
            body=f"Hello {event.username}, welcome to our platform!",
        )


class AnalyticsSubscriber(EventSubscriber):
    """Event subscriber for analytics tracking."""

    def __init__(self, event_bus: EventBus):
        """
        Initialize the analytics subscriber.

        Args:
            event_bus: The event bus to subscribe to
        """
        self.events: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("analytics")
        super().__init__(event_bus)

    @event_handler(UserCreatedEvent)
    async def track_user_created(self, event: UserCreatedEvent) -> None:
        """
        Track user created event.

        Args:
            event: The user created event
        """
        self.logger.info(f"Tracking user created: {event.user_id}")
        self.events.append(
            {
                "type": "user_created",
                "user_id": event.user_id,
                "email": event.email,
                "timestamp": event.timestamp,
            }
        )

    @event_handler(UserUpdatedEvent)
    async def track_user_updated(self, event: UserUpdatedEvent) -> None:
        """
        Track user updated event.

        Args:
            event: The user updated event
        """
        self.logger.info(f"Tracking user updated: {event.user_id}")
        self.events.append(
            {
                "type": "user_updated",
                "user_id": event.user_id,
                "fields_updated": event.fields_updated,
                "timestamp": event.timestamp,
            }
        )

    @event_handler(OrderCreatedEvent, priority=EventPriority.HIGH)
    async def track_order_created(self, event: OrderCreatedEvent) -> None:
        """
        Track order created event with high priority.

        Args:
            event: The order created event
        """
        self.logger.info(f"Tracking order created: {event.order_id}")
        self.events.append(
            {
                "type": "order_created",
                "order_id": event.order_id,
                "user_id": event.user_id,
                "amount": event.total_amount,
                "timestamp": event.timestamp,
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


@event_handler(OrderCancelledEvent, topic_pattern="orders.*.cancelled")
def process_order_cancellation(event: OrderCancelledEvent) -> None:
    """
    Process order cancellation with topic-based filtering.

    Args:
        event: The order cancelled event
    """
    logging.info(f"Processing cancellation for order {event.order_id}")
    # In a real implementation, this would process refunds etc.
    print(
        f"Order {event.order_id} has been cancelled. Reason: {event.reason or 'Not specified'}"
    )


# =============================================================================
# User Service (Event Producer)
# =============================================================================


class UserService:
    """Service responsible for user management."""

    def __init__(self):
        """Initialize the user service."""
        self.users: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("user_service")

    async def create_user(self, email: str, username: str) -> str:
        """
        Create a new user and raise a UserCreatedEvent.

        Args:
            email: User's email address
            username: User's username

        Returns:
            The new user ID
        """
        # Generate user ID
        user_id = f"user_{str(uuid4())[:8]}"

        # Create user
        self.users[user_id] = {
            "id": user_id,
            "email": email,
            "username": username,
            "created_at": datetime.now(UTC),
        }

        self.logger.info(f"Created user {user_id}: {username}")

        # Raise event
        event = UserCreatedEvent(user_id=user_id, email=email, username=username)
        publish_event(event)

        return user_id

    async def update_user(self, user_id: str, **kwargs) -> None:
        """
        Update a user and raise a UserUpdatedEvent.

        Args:
            user_id: The user ID
            **kwargs: Fields to update
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")

        # Update user
        updated_fields = []
        for field, value in kwargs.items():
            if field in self.users[user_id]:
                self.users[user_id][field] = value
                updated_fields.append(field)

        self.users[user_id]["updated_at"] = datetime.now(UTC)

        self.logger.info(f"Updated user {user_id}: {updated_fields}")

        # Raise event
        event = UserUpdatedEvent(user_id=user_id, fields_updated=updated_fields)
        publish_event(event)

    async def delete_user(self, user_id: str, reason: Optional[str] = None) -> None:
        """
        Delete a user and raise a UserDeletedEvent.

        Args:
            user_id: The user ID
            reason: Optional reason for deletion
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")

        # Delete user
        del self.users[user_id]

        self.logger.info(f"Deleted user {user_id}")

        # Collect event for batch processing
        event = UserDeletedEvent(user_id=user_id, reason=reason)
        collect_event(event)


# =============================================================================
# Order Service (Event Producer)
# =============================================================================


class OrderService:
    """Service responsible for order management."""

    def __init__(self):
        """Initialize the order service."""
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("order_service")

    async def create_order(
        self, user_id: str, items: List[Dict[str, Any]], topic: Optional[str] = None
    ) -> str:
        """
        Create a new order and raise an OrderCreatedEvent.

        Args:
            user_id: The user ID
            items: The order items
            topic: Optional topic for event routing

        Returns:
            The new order ID
        """
        # Generate order ID
        order_id = f"order_{str(uuid4())[:8]}"

        # Calculate total amount
        total_amount = sum(
            item.get("price", 0) * item.get("quantity", 0) for item in items
        )

        # Create order
        self.orders[order_id] = {
            "id": order_id,
            "user_id": user_id,
            "items": items,
            "total_amount": total_amount,
            "status": "created",
            "created_at": datetime.now(UTC),
        }

        self.logger.info(f"Created order {order_id} for user {user_id}")

        # Raise event
        event = OrderCreatedEvent(
            order_id=order_id,
            user_id=user_id,
            items=items,
            total_amount=total_amount,
            topic=topic,
        )
        publish_event_sync(event)

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
        self.orders[order_id]["shipped_at"] = datetime.now(UTC)

        self.logger.info(
            f"Shipped order {order_id} with tracking number {tracking_number}"
        )

        # Raise event
        event = OrderShippedEvent(
            order_id=order_id,
            user_id=self.orders[order_id]["user_id"],
            tracking_number=tracking_number,
        )
        publish_event(event)

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
        self.orders[order_id]["cancelled_at"] = datetime.now(UTC)

        self.logger.info(f"Cancelled order {order_id}")

        # Raise event
        event = OrderCancelledEvent(
            order_id=order_id,
            user_id=self.orders[order_id]["user_id"],
            reason=reason,
            topic=f"orders.{self.orders[order_id]['user_id']}.cancelled",
        )
        collect_event(event)


# =============================================================================
# Audit Service (Uses Event Store)
# =============================================================================


class AuditService:
    """Service for auditing and event replay."""

    def __init__(self, event_store: Optional[InMemoryEventStore] = None):
        """
        Initialize the audit service.

        Args:
            event_store: Optional event store (uses global one if not provided)
        """
        self.event_store = event_store or get_event_store()
        self.logger = logging.getLogger("audit_service")

    async def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get history of events for a user.

        Args:
            user_id: The user ID

        Returns:
            List of events
        """
        self.logger.info(f"Retrieving history for user {user_id}")

        # Get user-related events from store
        user_events = []

        # Get UserEvent instances
        events = await self.event_store.get_events_by_aggregate_id(user_id)
        user_events.extend(events)

        # Get OrderEvent instances that have user_id
        order_events = []
        for event_type in [
            "order_created_event",
            "order_shipped_event",
            "order_cancelled_event",
        ]:
            events = await self.event_store.get_events_by_type(event_type)
            # Filter events for this user
            for event in events:
                if hasattr(event, "user_id") and event.user_id == user_id:
                    order_events.append(event)

        user_events.extend(order_events)

        # Sort by timestamp
        user_events.sort(key=lambda e: e.timestamp)

        # Convert to dicts for better readability
        return [e.to_dict() for e in user_events]


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

    # Initialize the event system with in-memory store
    initialize_events(in_memory_event_store=True)

    # Create services
    notification_service = NotificationService()
    user_notification_handler = UserNotificationHandler(notification_service)
    analytics = AnalyticsSubscriber(get_event_bus())
    user_service = UserService()
    order_service = OrderService()
    audit_service = AuditService()

    # Subscribe handlers
    event_bus = get_event_bus()
    event_bus.subscribe(UserCreatedEvent, user_notification_handler)

    # Scan this module for function-based handlers
    scanner = EventHandlerScanner(event_bus)
    scanner.scan_module(__import__(__name__))

    print("\n=== Creating Users ===")
    # Create users
    alice_id = await user_service.create_user("alice@example.com", "alice")
    bob_id = await user_service.create_user("bob@example.com", "bob")

    # Wait for async events to be processed
    await asyncio.sleep(0.1)

    print("\n=== Creating Orders ===")
    # Create orders
    alice_order = await order_service.create_order(
        user_id=alice_id,
        items=[
            {"product_id": "prod-1", "name": "Widget", "price": 19.99, "quantity": 2},
            {"product_id": "prod-2", "name": "Gadget", "price": 29.99, "quantity": 1},
        ],
        topic="orders.new",
    )

    bob_order = await order_service.create_order(
        user_id=bob_id,
        items=[
            {
                "product_id": "prod-3",
                "name": "SuperWidget",
                "price": 49.99,
                "quantity": 1,
            }
        ],
        topic="orders.new",
    )

    # Ship Alice's order
    print("\n=== Shipping Order ===")
    await order_service.ship_order(alice_order, "TRACK123456")

    # Cancel Bob's order
    print("\n=== Cancelling Order ===")
    await order_service.cancel_order(bob_order, "Out of stock")

    # Update Alice
    print("\n=== Updating User ===")
    await user_service.update_user(alice_id, username="alice_updated")

    # Delete Bob
    print("\n=== Deleting User ===")
    await user_service.delete_user(bob_id, reason="User requested account deletion")

    # Process collected events (like order cancellations and user deletions)
    await publish_collected_events_async()

    # Wait for async events to be processed
    await asyncio.sleep(0.1)

    # Show audit trail for Alice
    print("\n=== User History (Alice) ===")
    history = await audit_service.get_user_history(alice_id)
    for event in history:
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("timestamp", "")

        if event_type == "user_created_event":
            print(f"- {timestamp}: User created: {event.get('username')}")
        elif event_type == "user_updated_event":
            print(f"- {timestamp}: User updated fields: {event.get('fields_updated')}")
        elif event_type == "order_created_event":
            print(
                f"- {timestamp}: Order created: {event.get('order_id')} (${event.get('total_amount', 0):.2f})"
            )
        elif event_type == "order_shipped_event":
            print(
                f"- {timestamp}: Order shipped: {event.get('order_id')} (Tracking: {event.get('tracking_number')})"
            )

    # Print results
    print("\n=== Notifications Sent ===")
    for notification in notification_service.notifications:
        print(f"- To: {notification['recipient']}")
        print(f"  Subject: {notification['subject']}")
        print(f"  Body: {notification['body']}")
        print(f"  Sent at: {notification['sent_at']}")

    print("\n=== Analytics Events ===")
    for event in analytics.events:
        print(f"- Type: {event['type']}")
        if "user_id" in event:
            print(f"  User: {event['user_id']}")
        if "order_id" in event:
            print(f"  Order: {event['order_id']}")
        if "amount" in event:
            print(f"  Amount: ${event['amount']:.2f}")
        print(f"  Timestamp: {event['timestamp']}")


if __name__ == "__main__":
    asyncio.run(main())
