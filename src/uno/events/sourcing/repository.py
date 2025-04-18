"""
Event-sourced repository for aggregate roots.

This module provides an implementation of the repository pattern for
event-sourced aggregate roots, enabling aggregates to be persisted
and reconstituted from their event history.
"""

from typing import Dict, Generic, List, Optional, Type, TypeVar

import structlog

from uno.events.core.event import Event
from uno.events.core.store import EventStore
from uno.events.sourcing.aggregate import AggregateRoot

# Type variables
E = TypeVar("E", bound=Event)
T = TypeVar("T", bound=AggregateRoot)


class EventSourcedRepository(Generic[T, E]):
    """
    Repository for event-sourced aggregate roots.
    
    This repository stores aggregates by persisting their events to an
    event store, and reconstitutes aggregates by replaying their event history.
    """
    
    def __init__(
        self,
        aggregate_type: Type[T],
        event_store: EventStore[E],
    ):
        """
        Initialize the event-sourced repository.
        
        Args:
            aggregate_type: Type of aggregate this repository manages
            event_store: Event store for persisting and retrieving events
        """
        self.aggregate_type = aggregate_type
        self.event_store = event_store
        self.logger = structlog.get_logger("uno.events.repository")
        
        # In-memory cache of aggregates
        self._cache: Dict[str, T] = {}
    
    async def save(self, aggregate: T) -> T:
        """
        Save an aggregate root to the repository.
        
        This method persists all pending events for the aggregate to the
        event store and updates the in-memory cache.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
        """
        # Get pending events
        events = aggregate.clear_pending_events()
        
        if not events:
            self.logger.debug(
                "No events to save for aggregate",
                aggregate_id=aggregate.id,
                aggregate_type=self.aggregate_type.__name__,
            )
            return aggregate
        
        # Save each event to the event store
        for event in events:
            # Make sure the event has the aggregate metadata
            if not event.aggregate_id or not event.aggregate_type:
                event = event.with_metadata(
                    aggregate_id=aggregate.id,
                    aggregate_type=self.aggregate_type.__name__,
                )
            
            await self.event_store.save_event(event)
        
        # Update cache
        self._cache[aggregate.id] = aggregate
        
        self.logger.debug(
            "Saved aggregate to repository",
            aggregate_id=aggregate.id,
            aggregate_type=self.aggregate_type.__name__,
            events_count=len(events),
        )
        
        return aggregate
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find an aggregate by its ID.
        
        This method attempts to retrieve an aggregate from the cache,
        and if not found, reconstitutes it from its event history.
        
        Args:
            id: The aggregate ID
            
        Returns:
            The aggregate if found, None otherwise
        """
        # Check cache first
        if id in self._cache:
            return self._cache[id]
        
        # Get events for this aggregate
        events = await self.event_store.get_events_by_aggregate_id(id)
        
        if not events:
            self.logger.debug(
                "No events found for aggregate ID",
                aggregate_id=id,
                aggregate_type=self.aggregate_type.__name__,
            )
            return None
        
        # Create new aggregate instance
        aggregate = self.aggregate_type(id=id)
        
        # Apply each event to build up the state
        for event in events:
            aggregate.apply(event, is_new=False)
        
        # Add to cache
        self._cache[id] = aggregate
        
        self.logger.debug(
            "Reconstituted aggregate from event history",
            aggregate_id=id,
            aggregate_type=self.aggregate_type.__name__,
            events_count=len(events),
        )
        
        return aggregate
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache of aggregates."""
        self._cache.clear()
        
        self.logger.debug(
            "Cleared aggregate cache",
            aggregate_type=self.aggregate_type.__name__,
        )