"""
Tests for the unified event system.

This module tests the functionality of the unified event system, ensuring
that all event handling, subscription, and publishing features work correctly.
"""

import asyncio
import logging
import pytest
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

from uno.core.unified_events import (
    UnoDomainEvent,
    EventBus,
    EventPublisher,
    EventStore,
    InMemoryEventStore,
    EventHandler,
    EventPriority,
    EventSubscriber,
    event_handler,
    initialize_events,
    reset_events,
    get_event_bus,
    get_event_publisher,
    publish_event,
    publish_event_sync,
    collect_event,
    publish_collected_events_async,
    clear_collected_events,
    scan_for_handlers,
    scan_instance_for_handlers,
)


# =============================================================================
# Test Events
# =============================================================================


class TestEvent(UnoDomainEvent):
    """Test event for testing the event system."""

    data: str
    value: int = 0


class UserCreatedEvent(UnoDomainEvent):
    """Event raised when a user is created."""

    user_id: str
    email: str
    username: str


class UserUpdatedEvent(UnoDomainEvent):
    """Event raised when a user is updated."""

    user_id: str
    fields_updated: List[str]


class OrderPlacedEvent(UnoDomainEvent):
    """Event raised when an order is placed."""

    order_id: str
    user_id: str
    items: List[Dict[str, Any]]
    total: float
    topic: str = "orders"


# =============================================================================
# Test Handlers
# =============================================================================


class TestEventHandler(EventHandler[TestEvent]):
    """Handler for TestEvent."""

    def __init__(self):
        super().__init__(TestEvent)
        self.handled_events: List[TestEvent] = []

    async def handle(self, event: TestEvent) -> None:
        """Handle the test event."""
        self.handled_events.append(event)


class UserEventHandler(EventHandler[UserCreatedEvent]):
    """Handler for UserCreatedEvent."""

    def __init__(self):
        super().__init__(UserCreatedEvent)
        self.users: Dict[str, Dict[str, Any]] = {}

    async def handle(self, event: UserCreatedEvent) -> None:
        """Handle the user created event."""
        self.users[event.user_id] = {
            "email": event.email,
            "username": event.username,
            "created_at": event.timestamp,
        }


class AnalyticsSubscriber(EventSubscriber):
    """Event subscriber that handles multiple event types."""

    def __init__(self, event_bus: EventBus):
        self.events: List[UnoDomainEvent] = []
        super().__init__(event_bus)

    @event_handler(UserCreatedEvent)
    async def track_user_created(self, event: UserCreatedEvent) -> None:
        """Track user created events."""
        self.events.append(event)

    @event_handler(UserUpdatedEvent)
    async def track_user_updated(self, event: UserUpdatedEvent) -> None:
        """Track user updated events."""
        self.events.append(event)

    @event_handler(OrderPlacedEvent, priority=EventPriority.HIGH)
    async def track_order_placed(self, event: OrderPlacedEvent) -> None:
        """Track order placed events with high priority."""
        self.events.append(event)


# Function-based handlers
@event_handler(TestEvent)
async def test_func_handler(event: TestEvent) -> None:
    """Function-based handler for TestEvent."""
    test_func_handler.events.append(event)  # type: ignore


test_func_handler.events = []  # type: ignore


@event_handler(OrderPlacedEvent, topic_pattern="orders.*")
def topic_handler(event: OrderPlacedEvent) -> None:
    """Handler for events with a specific topic pattern."""
    topic_handler.events.append(event)  # type: ignore


topic_handler.events = []  # type: ignore


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_event_system():
    """Reset the event system before and after each test."""
    reset_events()
    initialize_events()
    yield
    reset_events()


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return get_event_bus()


@pytest.fixture
def event_publisher():
    """Create an event publisher for testing."""
    return get_event_publisher()


@pytest.fixture
def test_event():
    """Create a test event."""
    return TestEvent(data="test data", value=42)


@pytest.fixture
def user_created_event():
    """Create a user created event."""
    return UserCreatedEvent(
        user_id="user-123", email="user@example.com", username="testuser"
    )


@pytest.fixture
def order_placed_event():
    """Create an order placed event."""
    return OrderPlacedEvent(
        order_id="order-456",
        user_id="user-123",
        items=[
            {"product_id": "prod-1", "quantity": 2, "price": 10.0},
            {"product_id": "prod-2", "quantity": 1, "price": 15.0},
        ],
        total=35.0,
        topic="orders.new",
    )


# =============================================================================
# Event System Tests
# =============================================================================


class TestUnifiedEventSystem:
    """Test suite for the unified event system."""

    @pytest.mark.asyncio
    async def test_domain_event_creation(self):
        """Test creating a domain event."""
        event = TestEvent(data="test")
        assert event.data == "test"
        assert event.value == 0
        assert event.event_id is not None
        assert event.event_type == "test_event"
        assert isinstance(event.timestamp, datetime)

        # Test converting to dict and back
        event_dict = event.to_dict()
        assert event_dict["data"] == "test"

        event2 = TestEvent.from_dict(event_dict)
        assert event2.data == "test"
        assert event2.event_id == event.event_id

        # Test converting to json and back
        event_json = event.to_json()
        event3 = TestEvent.from_json(event_json)
        assert event3.data == "test"
        assert event3.event_id == event.event_id

        # Test with_metadata
        event4 = event.with_metadata(
            correlation_id="corr-123",
            causation_id="cause-456",
            topic="test-topic",
            aggregate_id="agg-789",
            aggregate_type="TestAggregate",
        )
        assert event4.correlation_id == "corr-123"
        assert event4.causation_id == "cause-456"
        assert event4.topic == "test-topic"
        assert event4.aggregate_id == "agg-789"
        assert event4.aggregate_type == "TestAggregate"
        assert event4.data == "test"  # Original data is preserved

    @pytest.mark.asyncio
    async def test_event_handler(self, test_event):
        """Test event handlers processing events."""
        handler = TestEventHandler()

        # Direct execution
        await handler.handle(test_event)
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].data == "test data"

        # Check handler can_handle method
        assert handler.can_handle(test_event)
        assert not handler.can_handle(
            UserCreatedEvent(user_id="123", email="a@b.com", username="test")
        )

    @pytest.mark.asyncio
    async def test_event_bus_subscription_and_publishing(self, event_bus, test_event):
        """Test subscribing and publishing with the event bus."""
        handler = TestEventHandler()
        event_bus.subscribe(TestEvent, handler)

        # Publish event
        await event_bus.publish(test_event)
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].event_id == test_event.event_id

        # Unsubscribe
        event_bus.unsubscribe(TestEvent, handler)
        await event_bus.publish(test_event)
        assert len(handler.handled_events) == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_event_bus_topic_based_routing(self, event_bus, order_placed_event):
        """Test topic-based event routing."""
        # Clear existing events
        topic_handler.events = []

        # Subscribe to events with a specific topic pattern
        event_bus.subscribe(OrderPlacedEvent, topic_handler, topic_pattern="orders.*")

        # Publish event
        await event_bus.publish(order_placed_event)
        assert len(topic_handler.events) == 1

        # Test with non-matching topic
        topic_handler.events = []
        event2 = OrderPlacedEvent(
            order_id="order-789",
            user_id="user-456",
            items=[],
            total=0.0,
            topic="payments.new",  # Different topic
        )
        await event_bus.publish(event2)
        assert len(topic_handler.events) == 0  # Should not match

    @pytest.mark.asyncio
    async def test_function_based_handler(self, event_bus, test_event):
        """Test function-based event handlers."""
        # Clear existing events
        test_func_handler.events = []

        # Register handler
        event_bus.subscribe(TestEvent, test_func_handler)

        # Publish event
        await event_bus.publish(test_event)
        assert len(test_func_handler.events) == 1
        assert test_func_handler.events[0].data == "test data"

    @pytest.mark.asyncio
    async def test_event_subscriber(
        self, event_bus, user_created_event, order_placed_event
    ):
        """Test the EventSubscriber class."""
        subscriber = AnalyticsSubscriber(event_bus)

        # Publish events
        await event_bus.publish(user_created_event)
        await event_bus.publish(order_placed_event)

        # Check that events were tracked
        assert len(subscriber.events) == 2
        assert subscriber.events[0].event_id == user_created_event.event_id
        assert subscriber.events[1].event_id == order_placed_event.event_id

    @pytest.mark.asyncio
    async def test_event_priority(self, event_bus):
        """Test that event handlers are executed in priority order."""
        results = []

        @event_handler(TestEvent, priority=EventPriority.LOW)
        async def low_handler(event):
            results.append("low")

        @event_handler(TestEvent)
        async def normal_handler(event):
            results.append("normal")

        @event_handler(TestEvent, priority=EventPriority.HIGH)
        async def high_handler(event):
            results.append("high")

        # Register handlers
        event_bus.subscribe(TestEvent, low_handler)
        event_bus.subscribe(TestEvent, normal_handler)
        event_bus.subscribe(TestEvent, high_handler)

        # Publish event
        await event_bus.publish(TestEvent(data="test"))

        # Check execution order
        assert results == ["high", "normal", "low"]

    @pytest.mark.asyncio
    async def test_event_publisher(
        self, event_publisher, test_event, user_created_event
    ):
        """Test the EventPublisher."""
        handler = TestEventHandler()
        user_handler = UserEventHandler()

        # Subscribe handlers
        event_bus = get_event_bus()
        event_bus.subscribe(TestEvent, handler)
        event_bus.subscribe(UserCreatedEvent, user_handler)

        # Test publishing a single event
        await event_publisher.publish(test_event)
        assert len(handler.handled_events) == 1

        # Test collecting and publishing events
        event_publisher.collect(user_created_event)

        # New test event
        test_event2 = TestEvent(data="second test", value=100)
        event_publisher.collect(test_event2)

        # Publish collected
        await event_publisher.publish_collected()

        # Check that all events were handled
        assert len(handler.handled_events) == 2
        assert handler.handled_events[1].data == "second test"
        assert len(user_handler.users) == 1
        assert user_handler.users["user-123"]["username"] == "testuser"

        # Test clear collected
        event_publisher.collect(TestEvent(data="should not be published"))
        event_publisher.clear_collected()
        await event_publisher.publish_collected()
        assert len(handler.handled_events) == 2  # Still 2, not 3

    @pytest.mark.asyncio
    async def test_in_memory_event_store(self):
        """Test the InMemoryEventStore."""
        store = InMemoryEventStore()

        # Save events
        event1 = TestEvent(
            data="store test 1", aggregate_id="agg-1", aggregate_type="Test"
        )
        event2 = TestEvent(
            data="store test 2", aggregate_id="agg-1", aggregate_type="Test"
        )
        event3 = UserCreatedEvent(
            user_id="user-1",
            email="test@example.com",
            username="testuser",
            aggregate_id="agg-2",
            aggregate_type="User",
        )

        await store.save_event(event1)
        await store.save_event(event2)
        await store.save_event(event3)

        # Get events by aggregate ID
        events = await store.get_events_by_aggregate_id("agg-1")
        assert len(events) == 2
        assert events[0].data == "store test 1"
        assert events[1].data == "store test 2"

        # Get events by type
        events = await store.get_events_by_type("test_event")
        assert len(events) == 2
        events = await store.get_events_by_type("user_created_event")
        assert len(events) == 1
        assert events[0].user_id == "user-1"

    @pytest.mark.asyncio
    async def test_scan_for_handlers(self):
        """Test scanning for handlers in a module."""
        # Import local module for testing
        import sys

        current_module = sys.modules[__name__]

        # Clear existing events
        test_func_handler.events = []
        topic_handler.events = []

        # Scan module
        count = scan_for_handlers(current_module)
        assert count >= 2  # At least the function handlers we defined

        # Test publishing
        await get_event_bus().publish(TestEvent(data="scan test"))
        await get_event_bus().publish(
            OrderPlacedEvent(
                order_id="order-123",
                user_id="user-456",
                items=[],
                total=0.0,
                topic="orders.test",
            )
        )

        assert len(test_func_handler.events) == 1
        assert test_func_handler.events[0].data == "scan test"
        assert len(topic_handler.events) == 1
        assert topic_handler.events[0].order_id == "order-123"

    @pytest.mark.asyncio
    async def test_scan_instance_for_handlers(self):
        """Test scanning for handlers in an instance."""

        # Create an instance with event handlers
        class TestInstance:
            def __init__(self):
                self.events = []

            @event_handler(TestEvent)
            async def handle_test(self, event):
                self.events.append(event)

        instance = TestInstance()

        # Scan instance
        count = scan_instance_for_handlers(instance)
        assert count == 1

        # Test publishing
        await get_event_bus().publish(TestEvent(data="instance scan test"))
        assert len(instance.events) == 1
        assert instance.events[0].data == "instance scan test"

    @pytest.mark.asyncio
    async def test_public_api_functions(self, test_event):
        """Test the public API functions."""
        handler = TestEventHandler()
        get_event_bus().subscribe(TestEvent, handler)

        # Test publish_event
        publish_event(test_event)
        # Allow async task to complete
        await asyncio.sleep(0.1)
        assert len(handler.handled_events) == 1

        # Test publish_event_sync
        publish_event_sync(test_event)
        assert len(handler.handled_events) == 2

        # Test collect_event and publish_collected_events_async
        handler.handled_events.clear()
        collect_event(test_event)
        collect_event(TestEvent(data="another test"))
        await publish_collected_events_async()
        assert len(handler.handled_events) == 2
