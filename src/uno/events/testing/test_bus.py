"""
Test event bus for testing event handlers.

This module provides a test-friendly implementation of the event bus for
testing event handlers.
"""

from typing import Dict, List, Set, Type

from uno.events.core.bus import EventBus
from uno.events.core.event import Event


class TestEventBus(EventBus):
    """
    Test implementation of the event bus for testing.
    
    This implementation provides additional methods for introspecting
    the events that have been published to the bus.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the test event bus."""
        super().__init__(*args, **kwargs)
        self.published_events: List[Event] = []
        self.published_event_types: Set[str] = set()
        self.published_event_ids: Set[str] = set()
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all matching handlers in sequence.
        
        Args:
            event: The event to publish
        """
        # Record the event
        self.published_events.append(event)
        self.published_event_types.add(event.type)
        self.published_event_ids.add(event.id)
        
        # Let the parent class handle the actual publishing
        await super().publish(event)
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event to all matching handlers concurrently.
        
        Args:
            event: The event to publish
        """
        # Record the event
        self.published_events.append(event)
        self.published_event_types.add(event.type)
        self.published_event_ids.add(event.id)
        
        # Let the parent class handle the actual publishing
        await super().publish_async(event)
    
    def clear_published_events(self) -> None:
        """Clear the record of published events."""
        self.published_events.clear()
        self.published_event_types.clear()
        self.published_event_ids.clear()
    
    def get_published_events(self, event_type: Type[Event] = None) -> List[Event]:
        """
        Get all events that have been published to this bus.
        
        Args:
            event_type: Optional type of events to filter by
            
        Returns:
            List of published events, optionally filtered by type
        """
        if event_type is None:
            return self.published_events.copy()
        
        return [
            e for e in self.published_events
            if isinstance(e, event_type)
        ]
    
    def has_published_event(self, event_id: str) -> bool:
        """
        Check if an event with the given ID has been published.
        
        Args:
            event_id: The event ID to check
            
        Returns:
            True if an event with the ID has been published, False otherwise
        """
        return event_id in self.published_event_ids
    
    def has_published_event_type(self, event_type: str) -> bool:
        """
        Check if an event of the given type has been published.
        
        Args:
            event_type: The event type to check
            
        Returns:
            True if an event of the type has been published, False otherwise
        """
        return event_type in self.published_event_types