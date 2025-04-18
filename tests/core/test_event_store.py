"""
Tests for the EventStore implementations.

This module tests the event store functionality, focusing on the InMemoryEventStore
implementation but with tests designed to be reusable for other implementations.
"""

import pytest
from datetime import datetime, UTC, timedelta
from typing import List, Optional

from uno.core.events import Event
from uno.core.events.store import InMemoryEventStore
from uno.core.errors.base import ConcurrencyError


class UserCreated(Event):
    """Test event for user creation."""
    user_id: str
    username: str


class UserUpdated(Event):
    """Test event for user updates."""
    user_id: str
    field_name: str
    new_value: str


class OrderPlaced(Event):
    """Test event for order placement."""
    order_id: str
    customer_id: str
    amount: float


@pytest.fixture
def event_store():
    """Fixture for an InMemoryEventStore instance."""
    return InMemoryEventStore()


@pytest.fixture
def user_events():
    """Fixture for a series of user-related events."""
    now = datetime.now(UTC)
    
    # Create events for the same aggregate (user) in time order
    return [
        UserCreated(
            user_id="123",
            username="testuser",
            aggregate_id="user-123",
            aggregate_type="user",
            occurred_at=now - timedelta(minutes=10)
        ),
        UserUpdated(
            user_id="123",
            field_name="email",
            new_value="test@example.com",
            aggregate_id="user-123",
            aggregate_type="user",
            occurred_at=now - timedelta(minutes=5)
        ),
        UserUpdated(
            user_id="123",
            field_name="name",
            new_value="Test User",
            aggregate_id="user-123",
            aggregate_type="user",
            occurred_at=now
        )
    ]


@pytest.fixture
def order_event():
    """Fixture for an order event."""
    return OrderPlaced(
        order_id="order-456",
        customer_id="123",
        amount=99.99,
        aggregate_id="order-456",
        aggregate_type="order",
        occurred_at=datetime.now(UTC)
    )


@pytest.mark.asyncio
async def test_append_and_get_events(event_store, user_events):
    """Test appending events and retrieving them by aggregate ID."""
    # Append the events
    version = await event_store.append_events(user_events)
    
    # Verify the returned version is correct
    assert version == len(user_events)
    
    # Retrieve the events
    retrieved_events = await event_store.get_events_by_aggregate(user_events[0].aggregate_id)
    
    # Verify the correct events were retrieved
    assert len(retrieved_events) == len(user_events)
    
    # Check that event order is preserved
    for i, event in enumerate(retrieved_events):
        assert event.event_id == user_events[i].event_id


@pytest.mark.asyncio
async def test_append_events_with_expected_version(event_store, user_events):
    """Test optimistic concurrency with expected_version."""
    # Append first event
    version = await event_store.append_events([user_events[0]])
    assert version == 1
    
    # Append more events with correct expected version
    version = await event_store.append_events([user_events[1]], expected_version=1)
    assert version == 2
    
    # Attempt to append with incorrect expected version
    with pytest.raises(ConcurrencyError):
        await event_store.append_events([user_events[2]], expected_version=1)
    
    # Append with correct version should work
    version = await event_store.append_events([user_events[2]], expected_version=2)
    assert version == 3


@pytest.mark.asyncio
async def test_get_events_by_type(event_store, user_events, order_event):
    """Test retrieving events by type."""
    # Append all events
    await event_store.append_events(user_events)
    await event_store.append_events([order_event])
    
    # Get events by type
    user_created_events = await event_store.get_events_by_type(UserCreated.get_event_type())
    assert len(user_created_events) == 1
    assert user_created_events[0].event_id == user_events[0].event_id
    
    # Get updated events
    user_updated_events = await event_store.get_events_by_type(UserUpdated.get_event_type())
    assert len(user_updated_events) == 2
    
    # Get order events
    order_events = await event_store.get_events_by_type(OrderPlaced.get_event_type())
    assert len(order_events) == 1
    assert order_events[0].event_id == order_event.event_id


@pytest.mark.asyncio
async def test_get_events_by_type_with_date_filter(event_store, user_events):
    """Test retrieving events by type with a date filter."""
    # Append all events
    await event_store.append_events(user_events)
    
    # Get events after a specific time
    cutoff_time = user_events[1].occurred_at
    
    filtered_events = await event_store.get_events_by_type(
        UserUpdated.get_event_type(),
        start_date=cutoff_time
    )
    
    # Should only get events occurring at or after the cutoff
    assert len(filtered_events) == 2
    assert filtered_events[0].event_id == user_events[1].event_id
    assert filtered_events[1].event_id == user_events[2].event_id


@pytest.mark.asyncio
async def test_get_events_with_from_version(event_store, user_events):
    """Test retrieving events with a starting version."""
    # Append the events
    await event_store.append_events(user_events)
    
    # Get events starting from version 2
    events = await event_store.get_events_by_aggregate(
        user_events[0].aggregate_id,
        from_version=2
    )
    
    # Should only get the last two events
    assert len(events) == 2
    assert events[0].event_id == user_events[1].event_id
    assert events[1].event_id == user_events[2].event_id