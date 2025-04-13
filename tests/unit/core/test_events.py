"""
Tests for the event system.

This module tests the functionality of the event system, including:
- Event creation and handling
- Event bus subscription and publication
- Event handler registration and execution
- Event prioritization
- Asynchronous event handling
"""

import pytest
import asyncio
from typing import List
from unittest.mock import MagicMock, AsyncMock

from uno.core.events import (
    Event, EventPriority, EventHandlerWrapper, DefaultEventBus, EventPublisher,
    event_handler, EventHandlerScanner,
    initialize_events, reset_events, get_event_bus, get_event_publisher,
    publish_event, publish_event_sync, publish_event_async,
    collect_event, publish_collected_events, publish_collected_events_async,
    clear_collected_events, subscribe_handler, unsubscribe_handler
)


# =============================================================================
# Test Events and Handlers
# =============================================================================

class UserCreatedEvent(Event):
    """Event raised when a user is created."""
    
    def __init__(self, user_id: str, username: str, email: str, **kwargs):
        """
        Initialize a user created event.
        
        Args:
            user_id: The user ID
            username: The username
            email: The email address
            **kwargs: Additional event args
        """
        super().__init__(**kwargs)
        self.user_id = user_id
        self.username = username
        self.email = email


class UserUpdatedEvent(Event):
    """Event raised when a user is updated."""
    
    def __init__(self, user_id: str, username: str, email: str, **kwargs):
        """
        Initialize a user updated event.
        
        Args:
            user_id: The user ID
            username: The username
            email: The email address
            **kwargs: Additional event args
        """
        super().__init__(**kwargs)
        self.user_id = user_id
        self.username = username
        self.email = email


class BaseUserEvent(Event):
    """Base class for user events."""
    
    def __init__(self, user_id: str, **kwargs):
        """
        Initialize a base user event.
        
        Args:
            user_id: The user ID
            **kwargs: Additional event args
        """
        super().__init__(**kwargs)
        self.user_id = user_id


class UserDeletedEvent(BaseUserEvent):
    """Event raised when a user is deleted."""
    
    def __init__(self, user_id: str, reason: str = None, **kwargs):
        """
        Initialize a user deleted event.
        
        Args:
            user_id: The user ID
            reason: Reason for deletion
            **kwargs: Additional event args
        """
        super().__init__(user_id=user_id, **kwargs)
        self.reason = reason


class UserEventHandler:
    """Handler for user events."""
    
    def __init__(self):
        """Initialize the handler."""
        self.events: List[Event] = []
    
    async def handle(self, event: UserCreatedEvent) -> None:
        """
        Handle a user created event.
        
        Args:
            event: The event to handle
        """
        self.events.append(event)


class UserEventHandlerSync:
    """Synchronous handler for user events."""
    
    def __init__(self):
        """Initialize the handler."""
        self.events: List[Event] = []
    
    def handle(self, event: UserUpdatedEvent) -> None:
        """
        Handle a user updated event.
        
        Args:
            event: The event to handle
        """
        self.events.append(event)


class AllUserEventsHandler:
    """Handler for all user events."""
    
    def __init__(self):
        """Initialize the handler."""
        self.events: List[Event] = []
    
    async def handle(self, event: BaseUserEvent) -> None:
        """
        Handle any user event.
        
        Args:
            event: The event to handle
        """
        self.events.append(event)


# Function-based handlers
handled_events = []

@event_handler(UserCreatedEvent)
async def handle_user_created(event: UserCreatedEvent) -> None:
    """
    Handle a user created event.
    
    Args:
        event: The event to handle
    """
    handled_events.append(event)


@event_handler(UserUpdatedEvent)
def handle_user_updated(event: UserUpdatedEvent) -> None:
    """
    Handle a user updated event.
    
    Args:
        event: The event to handle
    """
    handled_events.append(event)


@event_handler(priority=EventPriority.HIGH)
async def handle_user_deleted(event: UserDeletedEvent) -> None:
    """
    Handle a user deleted event.
    
    Args:
        event: The event to handle
    """
    handled_events.append(event)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def setup_teardown():
    """Set up and tear down the event system for each test."""
    # Reset events before each test
    reset_events()
    
    # Clear handled events
    handled_events.clear()
    
    yield
    
    # Reset events after each test
    reset_events()


@pytest.fixture
def event_bus():
    """Create an event bus."""
    return DefaultEventBus()


@pytest.fixture
def event_publisher(event_bus):
    """Create an event publisher."""
    return EventPublisher(event_bus)


# =============================================================================
# Tests
# =============================================================================

def test_event_creation():
    """Test creating events."""
    # Create a simple event
    event = Event()
    assert event.event_id is not None
    assert event.event_type == "Event"
    assert event.timestamp is not None
    assert event.metadata == {}
    
    # Create a user created event
    user_event = UserCreatedEvent(
        user_id="123",
        username="testuser",
        email="test@example.com"
    )
    assert user_event.event_id is not None
    assert user_event.event_type == "UserCreatedEvent"
    assert user_event.timestamp is not None
    assert user_event.user_id == "123"
    assert user_event.username == "testuser"
    assert user_event.email == "test@example.com"


def test_event_serialization():
    """Test serializing and deserializing events."""
    # Create an event
    event = UserCreatedEvent(
        user_id="123",
        username="testuser",
        email="test@example.com",
        metadata={"source": "test"}
    )
    
    # Serialize to dict
    event_dict = event.to_dict()
    
    # Check dict contents
    assert event_dict["event_id"] == event.event_id
    assert event_dict["event_type"] == "UserCreatedEvent"
    assert "timestamp" in event_dict
    assert event_dict["metadata"] == {"source": "test"}
    assert event_dict["data"]["user_id"] == "123"
    assert event_dict["data"]["username"] == "testuser"
    assert event_dict["data"]["email"] == "test@example.com"
    
    # Deserialize from dict
    new_event = UserCreatedEvent.from_dict(event_dict)
    
    # Check deserialized event
    assert new_event.event_id == event.event_id
    assert new_event.event_type == event.event_type
    assert new_event.user_id == "123"
    assert new_event.username == "testuser"
    assert new_event.email == "test@example.com"
    assert new_event.metadata == {"source": "test"}


def test_event_equality():
    """Test event equality."""
    # Create events with same ID
    event1 = Event(event_id="123")
    event2 = Event(event_id="123")
    
    # Create event with different ID
    event3 = Event(event_id="456")
    
    # Check equality
    assert event1 == event2
    assert event1 != event3
    assert event2 != event3
    
    # Check hash
    assert hash(event1) == hash(event2)
    assert hash(event1) != hash(event3)


@pytest.mark.asyncio
async def test_event_handler_wrapper():
    """Test event handler wrapper execution."""
    # Create events and handlers
    event = UserCreatedEvent(user_id="123", username="testuser", email="test@example.com")
    mock_handler = AsyncMock()
    mock_handler_sync = MagicMock()
    
    # Create wrappers
    wrapper_async = EventHandlerWrapper(mock_handler, EventPriority.NORMAL, True)
    wrapper_sync = EventHandlerWrapper(mock_handler_sync, EventPriority.HIGH, False)
    
    # Execute handlers
    await wrapper_async.execute(event)
    await wrapper_sync.execute(event)
    
    # Check that handlers were called
    mock_handler.assert_called_once_with(event)
    mock_handler_sync.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_publish():
    """Test subscribing to and publishing events on the event bus."""
    bus = DefaultEventBus()
    
    # Create handlers
    handler_async = AsyncMock()
    handler_sync = MagicMock()
    
    # Subscribe handlers
    bus.subscribe(UserCreatedEvent, handler_async)
    bus.subscribe_with_priority(UserUpdatedEvent, handler_sync, EventPriority.HIGH)
    
    # Create events
    created_event = UserCreatedEvent(user_id="123", username="testuser", email="test@example.com")
    updated_event = UserUpdatedEvent(user_id="123", username="updateduser", email="updated@example.com")
    
    # Publish events
    await bus.publish(created_event)
    await bus.publish(updated_event)
    
    # Check that handlers were called
    handler_async.assert_called_once_with(created_event)
    handler_sync.assert_called_once_with(updated_event)


@pytest.mark.asyncio
async def test_event_bus_inheritance():
    """Test that event handlers receive events from subclasses."""
    bus = DefaultEventBus()
    
    # Create handler for base class
    handler = AsyncMock()
    
    # Subscribe handler
    bus.subscribe(BaseUserEvent, handler)
    
    # Create events
    base_event = BaseUserEvent(user_id="123")
    deleted_event = UserDeletedEvent(user_id="123", reason="test")
    
    # Publish events
    await bus.publish(base_event)
    await bus.publish(deleted_event)
    
    # Check that handler was called for both events
    assert handler.call_count == 2
    handler.assert_any_call(base_event)
    handler.assert_any_call(deleted_event)


@pytest.mark.asyncio
async def test_event_publisher():
    """Test the event publisher."""
    bus = DefaultEventBus()
    publisher = EventPublisher(bus)
    
    # Create mock handler
    handler = AsyncMock()
    
    # Subscribe handler
    bus.subscribe(UserCreatedEvent, handler)
    
    # Create event
    event = UserCreatedEvent(user_id="123", username="testuser", email="test@example.com")
    
    # Test collect and publish
    publisher.collect(event)
    await publisher.publish_collected_async()
    
    # Check that handler was called
    handler.assert_called_once_with(event)
    
    # Test clear and collect
    handler.reset_mock()
    publisher.collect(event)
    publisher.clear_collected()
    await publisher.publish_collected_async()
    
    # Check that handler was not called
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_event_handler_decorator():
    """Test the event handler decorator."""
    initialize_events()
    bus = get_event_bus()
    
    # Clear handled events
    handled_events.clear()
    
    # Create events
    created_event = UserCreatedEvent(user_id="123", username="testuser", email="test@example.com")
    updated_event = UserUpdatedEvent(user_id="123", username="updateduser", email="updated@example.com")
    deleted_event = UserDeletedEvent(user_id="123", reason="test")
    
    # Subscribe handlers
    scanner = EventHandlerScanner(bus)
    scanner.scan_module(__import__(__name__))
    
    # Publish events
    await bus.publish(created_event)
    await bus.publish(updated_event)
    await bus.publish(deleted_event)
    
    # Check that handlers were called
    assert len(handled_events) == 3
    assert created_event in handled_events
    assert updated_event in handled_events
    assert deleted_event in handled_events


@pytest.mark.asyncio
async def test_event_handler_priority():
    """Test that event handlers are executed in priority order."""
    bus = DefaultEventBus()
    
    # Create events to track execution order
    execution_order = []
    
    # Create handlers with different priorities
    async def high_handler(event):
        execution_order.append("high")
    
    async def normal_handler(event):
        execution_order.append("normal")
    
    async def low_handler(event):
        execution_order.append("low")
    
    # Subscribe handlers with priorities
    bus.subscribe_with_priority(Event, high_handler, EventPriority.HIGH)
    bus.subscribe_with_priority(Event, normal_handler, EventPriority.NORMAL)
    bus.subscribe_with_priority(Event, low_handler, EventPriority.LOW)
    
    # Publish event
    await bus.publish(Event())
    
    # Check execution order
    assert execution_order == ["high", "normal", "low"]


@pytest.mark.asyncio
async def test_global_event_api():
    """Test the global event API functions."""
    # Initialize events
    initialize_events()
    
    # Create mock handler
    handler = AsyncMock()
    
    # Subscribe handler
    subscribe_handler(UserCreatedEvent, handler)
    
    # Create event
    event = UserCreatedEvent(user_id="123", username="testuser", email="test@example.com")
    
    # Test publish
    publish_event(event)
    
    # Wait for async task to complete
    await asyncio.sleep(0.1)
    
    # Check that handler was called
    handler.assert_called_once_with(event)
    
    # Reset mock
    handler.reset_mock()
    
    # Test collect and publish
    collect_event(event)
    await publish_collected_events_async()
    
    # Check that handler was called
    handler.assert_called_once_with(event)
    
    # Reset mock and unsubscribe
    handler.reset_mock()
    unsubscribe_handler(UserCreatedEvent, handler)
    
    # Publish again
    publish_event(event)
    
    # Wait for async task to complete
    await asyncio.sleep(0.1)
    
    # Check that handler was not called
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_event_handler_scanner():
    """Test the event handler scanner."""
    bus = DefaultEventBus()
    
    # Create mock module with handlers
    class MockModule:
        pass
    
    mock_module = MockModule()
    
    # Add handlers to mock module
    mock_module.handler1 = AsyncMock()
    mock_module.handler1.__event_handler__ = True
    mock_module.handler1.__event_type__ = UserCreatedEvent
    mock_module.handler1.__event_priority__ = EventPriority.NORMAL
    
    class MockHandler:
        async def handle(self, event: UserUpdatedEvent):
            pass
    
    mock_module.MockHandler = MockHandler
    
    # Create scanner
    scanner = EventHandlerScanner(bus)
    
    # Patch inspect.getmembers to return our mock handlers
    original_getmembers = inspect.getmembers
    
    try:
        inspect.getmembers = lambda obj, predicate=None: [
            ("handler1", mock_module.handler1),
            ("MockHandler", MockHandler)
        ]
        
        # Get type hints for handle method
        original_get_type_hints = get_type_hints
        
        def mock_get_type_hints(obj):
            if obj == MockHandler.handle:
                return {"event": UserUpdatedEvent}
            return {}
        
        import typing
        typing.get_type_hints = mock_get_type_hints
        
        # Scan module
        count = scanner.scan_module(mock_module)
        
        # Check that handlers were registered
        assert count == 2
        
        # Create events
        created_event = UserCreatedEvent(user_id="123", username="testuser", email="test@example.com")
        updated_event = UserUpdatedEvent(user_id="123", username="updateduser", email="updated@example.com")
        
        # Publish events
        await bus.publish(created_event)
        await bus.publish(updated_event)
        
        # Check that handler was called
        mock_module.handler1.assert_called_once_with(created_event)
        
    finally:
        # Restore original functions
        inspect.getmembers = original_getmembers
        typing.get_type_hints = original_get_type_hints