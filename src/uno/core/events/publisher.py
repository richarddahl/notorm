"""
Event publisher for the UNO framework.

This module provides a high-level publisher interface for working with events,
supporting both individual and batch publishing with various options.
"""

import asyncio
from typing import List, Optional, Any

import structlog

from uno.core.protocols.event import EventProtocol, EventBusProtocol, EventStoreProtocol
from uno.core.events.event import Event


class EventPublisher:
    """
    Publisher for domain events with support for persistence and batching.
    
    The EventPublisher provides a convenient way to publish events to an event bus
    and optionally persist them to an event store. It also supports collecting events
    for batch publishing.
    
    Features:
    - Immediate or batched publishing
    - Optional event persistence
    - Synchronous and asynchronous operations
    - Collection and deferred publishing
    """
    
    def __init__(
        self,
        event_bus: EventBusProtocol,
        event_store: Optional[EventStoreProtocol] = None,
    ):
        """
        Initialize the event publisher.
        
        Args:
            event_bus: The event bus to publish events to
            event_store: Optional event store for persisting events
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.logger = structlog.get_logger("uno.core.events")
        self._collected_events: List[EventProtocol] = []
    
    def collect(self, event: EventProtocol) -> None:
        """
        Collect an event for later batch publishing.
        
        This method adds the event to an internal collection without
        immediately publishing it. Call publish_collected() to publish
        all collected events.
        
        Args:
            event: The event to collect
        """
        self._collected_events.append(event)
    
    def collect_many(self, events: List[EventProtocol]) -> None:
        """
        Collect multiple events for later batch publishing.
        
        Args:
            events: The events to collect
        """
        self._collected_events.extend(events)
    
    def clear_collected(self) -> None:
        """Clear all collected events without publishing them."""
        self._collected_events.clear()
    
    async def publish_collected(self) -> None:
        """
        Publish all collected events.
        
        This method publishes all collected events and then clears
        the collection.
        """
        events = self._collected_events.copy()
        self._collected_events.clear()
        
        if not events:
            return
        
        # Store events if we have an event store
        if self.event_store:
            for event in events:
                # We ignore versions for collected events
                await self.event_store.append_events([event])
        
        # Publish events to the bus
        await self.event_bus.publish_many(events)
    
    async def publish(self, event: EventProtocol) -> None:
        """
        Publish a single event immediately.
        
        This method persists the event (if a store is configured) and
        publishes it to the event bus.
        
        Args:
            event: The event to publish
        """
        # Store the event if we have an event store
        if self.event_store:
            await self.event_store.append_events([event])
        
        # Publish to the bus
        await self.event_bus.publish(event)
    
    def publish_sync(self, event: EventProtocol) -> None:
        """
        Publish a single event synchronously.
        
        This is a convenience method for publishing from synchronous code.
        It runs the async publish method in an event loop.
        
        Args:
            event: The event to publish
        """
        try:
            # Try to get a running event loop
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # Create a task in the running loop
                asyncio.create_task(self.publish(event))
            else:
                # Run in the existing loop
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            # No running event loop, create a new one
            asyncio.run(self.publish(event))
    
    async def publish_many(self, events: List[EventProtocol]) -> None:
        """
        Publish multiple events.
        
        Args:
            events: The events to publish
        """
        # Store events if we have an event store
        if self.event_store and events:
            # We store them one by one to avoid version conflicts
            # A real implementation might use transactions here
            for event in events:
                await self.event_store.append_events([event])
        
        # Publish to the bus
        await self.event_bus.publish_many(events)