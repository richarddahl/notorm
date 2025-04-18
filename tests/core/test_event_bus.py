"""
Tests for the AsyncEventBus implementation.

This module contains comprehensive tests for the event bus, covering
subscription, publication, and error handling scenarios.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, UTC
from typing import List, Optional

from uno.core.events import AsyncEventBus, Event, EventPublisher
from uno.core.events.store import InMemoryEventStore


class UserCreated(Event):
    """Test event for user creation."""
    user_id: str
    username: str


class OrderPlaced(Event):
    """Test event for order placement."""
    order_id: str
    customer_id: str
    amount: float


@pytest.fixture
def event_bus():
    """Fixture for an AsyncEventBus instance."""
    return AsyncEventBus()


@pytest.fixture
def user_created_event():
    """Fixture for a sample user created event."""
    return UserCreated(
        user_id="123",
        username="testuser",
        aggregate_id="user-123"
    )


@pytest.fixture
def order_placed_event():
    """Fixture for a sample order placed event."""
    return OrderPlaced(
        order_id="order-456",
        customer_id="123",
        amount=99.99,
        aggregate_id="order-456"
    )


@pytest.mark.asyncio
async def test_subscribe_and_publish(event_bus, user_created_event):
    """Test basic subscription and publication."""
    # Create a mock handler
    mock_handler = AsyncMock()
    
    # Subscribe to the event
    await event_bus.subscribe(user_created_event.event_type, mock_handler)
    
    # Publish the event
    await event_bus.publish(user_created_event)
    
    # Check that the handler was called with the event
    mock_handler.assert_called_once_with(user_created_event)


@pytest.mark.asyncio
async def test_multiple_handlers(event_bus, user_created_event):
    """Test multiple handlers for the same event type."""
    # Create mock handlers
    handler1 = AsyncMock()
    handler2 = AsyncMock()
    handler3 = AsyncMock()
    
    # Subscribe all handlers
    await event_bus.subscribe(user_created_event.event_type, handler1)
    await event_bus.subscribe(user_created_event.event_type, handler2)
    await event_bus.subscribe(user_created_event.event_type, handler3)
    
    # Publish the event
    await event_bus.publish(user_created_event)
    
    # Check that all handlers were called
    handler1.assert_called_once_with(user_created_event)
    handler2.assert_called_once_with(user_created_event)
    handler3.assert_called_once_with(user_created_event)


@pytest.mark.asyncio
async def test_unsubscribe(event_bus, user_created_event):
    """Test unsubscribing a handler."""
    # Create mock handlers
    handler1 = AsyncMock()
    handler2 = AsyncMock()
    
    # Subscribe both handlers
    await event_bus.subscribe(user_created_event.event_type, handler1)
    await event_bus.subscribe(user_created_event.event_type, handler2)
    
    # Unsubscribe one handler
    await event_bus.unsubscribe(user_created_event.event_type, handler1)
    
    # Publish the event
    await event_bus.publish(user_created_event)
    
    # Check that only the still-subscribed handler was called
    handler1.assert_not_called()
    handler2.assert_called_once_with(user_created_event)


@pytest.mark.asyncio
async def test_handler_exception_doesnt_affect_others(event_bus, user_created_event):
    """Test that an exception in one handler doesn't prevent others from running."""
    # Create handlers - one that raises an exception
    async def failing_handler(event):
        raise ValueError("Handler failure")
    
    normal_handler = AsyncMock()
    
    # Subscribe both handlers
    await event_bus.subscribe(user_created_event.event_type, failing_handler)
    await event_bus.subscribe(user_created_event.event_type, normal_handler)
    
    # Publish the event - this should not raise the exception
    await event_bus.publish(user_created_event)
    
    # Verify the normal handler was still called
    normal_handler.assert_called_once_with(user_created_event)


@pytest.mark.asyncio
async def test_publish_many(event_bus, user_created_event, order_placed_event):
    """Test publishing multiple events."""
    # Create mock handlers for each event type
    user_handler = AsyncMock()
    order_handler = AsyncMock()
    
    # Subscribe handlers
    await event_bus.subscribe(user_created_event.event_type, user_handler)
    await event_bus.subscribe(order_placed_event.event_type, order_handler)
    
    # Publish multiple events
    await event_bus.publish_many([user_created_event, order_placed_event])
    
    # Check handlers were called correctly
    user_handler.assert_called_once_with(user_created_event)
    order_handler.assert_called_once_with(order_placed_event)


@pytest.mark.asyncio
async def test_event_publisher_with_bus(event_bus, user_created_event):
    """Test the EventPublisher with an event bus."""
    # Create a publisher with just a bus
    publisher = EventPublisher(event_bus)
    
    # Create a mock handler
    mock_handler = AsyncMock()
    
    # Subscribe to the event
    await event_bus.subscribe(user_created_event.event_type, mock_handler)
    
    # Publish via the publisher
    await publisher.publish(user_created_event)
    
    # Check the handler was called
    mock_handler.assert_called_once_with(user_created_event)


@pytest.mark.asyncio
async def test_event_publisher_with_store(event_bus, user_created_event):
    """Test the EventPublisher with an event store."""
    # Create an in-memory store
    store = InMemoryEventStore()
    
    # Create a publisher with bus and store
    publisher = EventPublisher(event_bus, store)
    
    # Publish an event
    await publisher.publish(user_created_event)
    
    # Check the event was stored
    stored_events = await store.get_events_by_aggregate(user_created_event.aggregate_id)
    assert len(stored_events) == 1
    assert stored_events[0].event_id == user_created_event.event_id


@pytest.mark.asyncio
async def test_event_publisher_collect_and_publish(event_bus, user_created_event, order_placed_event):
    """Test collecting events and publishing them in a batch."""
    # Create handlers
    user_handler = AsyncMock()
    order_handler = AsyncMock()
    
    # Subscribe handlers
    await event_bus.subscribe(user_created_event.event_type, user_handler)
    await event_bus.subscribe(order_placed_event.event_type, order_handler)
    
    # Create a publisher
    publisher = EventPublisher(event_bus)
    
    # Collect events without publishing
    publisher.collect(user_created_event)
    publisher.collect(order_placed_event)
    
    # Verify no events published yet
    user_handler.assert_not_called()
    order_handler.assert_not_called()
    
    # Publish collected events
    await publisher.publish_collected()
    
    # Verify handlers were called
    user_handler.assert_called_once_with(user_created_event)
    order_handler.assert_called_once_with(order_placed_event)
    
    # Check collection was cleared
    publisher.collect(user_created_event)
    await publisher.publish_collected()
    assert user_handler.call_count == 2  # Called once more
    
    # Test clear_collected
    publisher.collect(user_created_event)
    publisher.clear_collected()
    await publisher.publish_collected()
    assert user_handler.call_count == 2  # Not called again