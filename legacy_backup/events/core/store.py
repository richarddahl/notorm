"""
Event store for the Uno event system.

This module defines the event store abstraction, which is responsible for
persisting events and providing methods for retrieving events by various criteria.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from uno.events.core.event import Event

# Type variable for event store
E = TypeVar("E", bound=Event)


class EventStore(Generic[E], ABC):
    """
    Abstract base class for event stores.
    
    Event stores persist events and provide methods for retrieving
    events by various criteria. This enables event sourcing, auditing,
    and replay capabilities.
    """
    
    @abstractmethod
    async def save_event(self, event: E) -> None:
        """
        Save an event to the store.
        
        Args:
            event: The event to save
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_events_by_correlation_id(
        self,
        correlation_id: str,
    ) -> List[E]:
        """
        Get all events with a specific correlation ID.
        
        This enables tracing event chains across service boundaries.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of events with the specified correlation ID
        """
        pass
    
    @abstractmethod
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
        pass


class InMemoryEventStore(EventStore[E]):
    """
    In-memory implementation of the event store.
    
    This implementation stores events in memory, which is useful for
    testing and simple applications. Not suitable for production use
    as events will be lost on service restart.
    """
    
    def __init__(self):
        """Initialize the in-memory event store."""
        self.events: List[E] = []
    
    async def save_event(self, event: E) -> None:
        """
        Save an event to the in-memory store.
        
        Args:
            event: The event to save
        """
        self.events.append(event)
    
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