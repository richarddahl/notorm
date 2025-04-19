"""
Mock event store for testing.

This module provides a mock implementation of the event store for testing.
"""

from datetime import datetime
from typing import Dict, Generic, List, Optional, Set, TypeVar

from uno.events.core.event import Event
from uno.events.core.store import EventStore

# Type variable for event store
E = TypeVar("E", bound=Event)


class MockEventStore(EventStore[E], Generic[E]):
    """
    Mock implementation of the event store for testing.
    
    This implementation stores events in memory and provides methods
    for inspecting what events have been saved.
    """
    
    def __init__(self):
        """Initialize the mock event store."""
        self.events: List[E] = []
        self.saved_event_ids: Set[str] = set()
    
    async def save_event(self, event: E) -> None:
        """
        Save an event to the store.
        
        Args:
            event: The event to save
        """
        self.events.append(event)
        self.saved_event_ids.add(event.id)
    
    async def get_events_by_aggregate_id(
        self, 
        aggregate_id: str,
        event_types: Optional[List[str]] = None,
        since: Optional[datetime] = None,
    ) -> List[E]:
        """
        Get all events for a specific aggregate ID.
        
        Args:
            aggregate_id: ID of the aggregate to get events for
            event_types: Optional list of event types to filter by
            since: Optional timestamp to only return events after
            
        Returns:
            List of events for the aggregate
        """
        filtered_events = [
            e for e in self.events 
            if getattr(e, "aggregate_id", None) == aggregate_id
        ]
        
        if event_types:
            filtered_events = [
                e for e in filtered_events
                if e.type in event_types
            ]
        
        if since:
            filtered_events = [
                e for e in filtered_events
                if e.timestamp >= since
            ]
        
        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)
        
        return filtered_events
    
    async def get_events_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[E]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            since: Optional timestamp to only return events after
            limit: Optional maximum number of events to return
            
        Returns:
            List of events of the specified type
        """
        filtered_events = [
            e for e in self.events
            if e.type == event_type
        ]
        
        if since:
            filtered_events = [
                e for e in filtered_events
                if e.timestamp >= since
            ]
        
        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)
        
        if limit:
            filtered_events = filtered_events[:limit]
        
        return filtered_events
    
    async def get_events_by_correlation_id(
        self,
        correlation_id: str,
    ) -> List[E]:
        """
        Get all events with a specific correlation ID.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of events with the specified correlation ID
        """
        filtered_events = [
            e for e in self.events
            if getattr(e, "correlation_id", None) == correlation_id
        ]
        
        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)
        
        return filtered_events
    
    async def get_all_events(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[E]:
        """
        Get all events in the event store.
        
        Args:
            since: Optional timestamp to only return events after
            limit: Optional maximum number of events to return
            
        Returns:
            List of all events
        """
        filtered_events = self.events.copy()
        
        if since:
            filtered_events = [
                e for e in filtered_events
                if e.timestamp >= since
            ]
        
        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.timestamp)
        
        if limit:
            filtered_events = filtered_events[:limit]
        
        return filtered_events
    
    def clear(self) -> None:
        """Clear all events from the store."""
        self.events.clear()
        self.saved_event_ids.clear()
    
    def has_saved_event(self, event_id: str) -> bool:
        """
        Check if an event has been saved to the store.
        
        Args:
            event_id: The event ID to check
            
        Returns:
            True if the event has been saved, False otherwise
        """
        return event_id in self.saved_event_ids