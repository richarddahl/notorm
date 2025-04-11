"""
Tests for the Event System.
"""

import pytest
import uuid
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime

from uno.core.events import (
    BaseDomainEvent, BaseEventHandler, SimpleEventBus,
    TypedEventBus, AsyncEventBus, event_handler, DomainEventProcessor
)


class TestEvent(BaseDomainEvent):
    """Test event for testing."""
    
    def __init__(self, entity_id: str, data_dict: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.entity_id = entity_id
        self._data_dict = data_dict
    
    @property
    def aggregate_id(self) -> str:
        return self.entity_id
        
    @property
    def data(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            **self._data_dict
        }
    
    def to_json(self) -> str:
        """Convert the event to JSON."""
        return json.dumps({
            "entity_id": self.entity_id,
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            **self._data_dict
        })
        
    @classmethod
    def from_json(cls, json_str: str) -> 'TestEvent':
        """Create an event from JSON."""
        data = json.loads(json_str)
        
        # Extract the base properties
        event_id = uuid.UUID(data.pop("event_id"))
        timestamp = datetime.fromisoformat(data.pop("timestamp"))
        entity_id = data.pop("entity_id")
        data.pop("event_type", None)  # Remove event_type if present
        
        # Create the event
        return cls(
            entity_id=entity_id,
            data_dict=data,  # Use remaining data as data_dict
            event_id=event_id,
            timestamp=timestamp
        )


class TestEventHandler(BaseEventHandler[TestEvent]):
    """Test event handler."""
    
    def __init__(self):
        self.handled_events = []
    
    async def handle(self, event: TestEvent) -> None:
        self.handled_events.append(event)


class TestEventProcessor(DomainEventProcessor):
    """Test event processor."""
    
    def __init__(self, event_bus):
        super().__init__(event_bus)
        self.handled_events = []
    
    @event_handler(TestEvent)
    async def handle_test_event(self, event: TestEvent):
        self.handled_events.append(event)


@pytest.mark.asyncio
async def test_simple_event_bus():
    """Test the SimpleEventBus."""
    # Create the event bus
    event_bus = SimpleEventBus()
    
    # Create a handler
    handler = TestEventHandler()
    
    # Subscribe the handler
    event_bus.subscribe("TestEvent", handler)
    
    # Create an event
    event = TestEvent(
        entity_id="test123",
        data_dict={"key": "value"}
    )
    
    # Publish the event
    await event_bus.publish(event)
    
    # Check that the handler was called
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0].entity_id == "test123"
    assert handler.handled_events[0].data["key"] == "value"


@pytest.mark.asyncio
async def test_typed_event_bus():
    """Test the TypedEventBus."""
    # Create the event bus
    event_bus = TypedEventBus()
    
    # Create a handler
    handler = TestEventHandler()
    
    # Subscribe the handler
    event_bus.subscribe_to_type(TestEvent, handler)
    
    # Create an event
    event = TestEvent(
        entity_id="test123",
        data_dict={"key": "value"}
    )
    
    # Publish the event
    await event_bus.publish(event)
    
    # Check that the handler was called
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0].entity_id == "test123"
    assert handler.handled_events[0].data["key"] == "value"


@pytest.mark.asyncio
async def test_event_handler_decorator():
    """Test the event_handler decorator."""
    # Create the event bus
    event_bus = TypedEventBus()
    
    # Create an event processor
    processor = TestEventProcessor(event_bus)
    
    # Create an event
    event = TestEvent(
        entity_id="test123",
        data_dict={"key": "value"}
    )
    
    # Publish the event
    await event_bus.publish(event)
    
    # Check that the handler was called
    assert len(processor.handled_events) == 1
    assert processor.handled_events[0].entity_id == "test123"
    assert processor.handled_events[0].data["key"] == "value"


@pytest.mark.asyncio
async def test_async_event_bus():
    """Test the AsyncEventBus."""
    # Create the event bus
    event_bus = AsyncEventBus()
    
    # Create a handler
    handler = TestEventHandler()
    
    # Subscribe the handler
    event_bus.subscribe_to_type(TestEvent, handler)
    
    # Start the event bus
    await event_bus.start()
    
    try:
        # Create an event
        event = TestEvent(
            entity_id="test123",
            data_dict={"key": "value"}
        )
        
        # Publish the event
        await event_bus.publish(event)
        
        # Give the worker some time to process the event
        await asyncio.sleep(0.1)
        
        # Check that the handler was called
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].entity_id == "test123"
        assert handler.handled_events[0].data["key"] == "value"
    finally:
        # Stop the event bus
        await event_bus.stop()


@pytest.mark.asyncio
async def test_event_to_json():
    """Test serializing events to JSON."""
    # Create an event
    event = TestEvent(
        entity_id="test123",
        data_dict={"key": "value"}
    )
    
    # Convert to JSON
    json_str = event.to_json()
    
    # Convert back from JSON
    event2 = TestEvent.from_json(json_str)
    
    # Check the values
    assert event2.entity_id == "test123"
    assert event2.data["key"] == "value"
    assert event2.event_type == "TestEvent"
    assert isinstance(event2.event_id, uuid.UUID)
    assert isinstance(event2.timestamp, datetime)