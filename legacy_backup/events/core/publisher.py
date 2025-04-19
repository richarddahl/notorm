"""
Event publisher for the Uno event system.

The event publisher provides a convenient interface for publishing events,
with support for event collection and batch publishing.
"""

import asyncio
import logging
from typing import List, Optional

import structlog

from uno.events.core.bus import EventBus
from uno.events.core.event import Event
from uno.events.core.store import EventStore


class EventPublisher:
    """
    Event publisher for collecting and publishing events.
    
    The event publisher provides a convenient interface for publishing events
    to an event bus, with optional persistence via an event store. It also
    supports collecting events for batch publishing.
    """
    
    def __init__(
        self, 
        event_bus: EventBus,
        event_store: Optional[EventStore] = None,
    ):
        """
        Initialize the event publisher.
        
        Args:
            event_bus: The event bus to publish events to
            event_store: Optional event store for persisting events
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.logger = structlog.get_logger("uno.events")
        self._collected_events: List[Event] = []
    
    def collect(self, event: Event) -> None:
        """
        Collect an event for later batch publishing.
        
        Args:
            event: The event to collect
        """
        self._collected_events.append(event)
    
    def collect_many(self, events: List[Event]) -> None:
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
        Publish all collected events sequentially.
        
        This method publishes all events that have been collected and then
        clears the collection of events.
        """
        events = self._collected_events.copy()
        self._collected_events.clear()
        
        if not events:
            return
        
        # Persist events if we have an event store
        if self.event_store:
            for event in events:
                await self.event_store.save_event(event)
        
        # Publish events to the event bus
        await self.event_bus.publish_many(events)
    
    async def publish_collected_async(self) -> None:
        """
        Publish all collected events concurrently.
        
        This method publishes all events that have been collected concurrently
        and then clears the collection of events.
        """
        events = self._collected_events.copy()
        self._collected_events.clear()
        
        if not events:
            return
        
        # Persist events if we have an event store
        if self.event_store:
            # Store events sequentially to maintain order
            for event in events:
                await self.event_store.save_event(event)
        
        # Publish events to the event bus concurrently
        await self.event_bus.publish_many_async(events)
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event immediately.
        
        Args:
            event: The event to publish
        """
        # Persist event if we have an event store
        if self.event_store:
            await self.event_store.save_event(event)
        
        # Publish event to the event bus
        await self.event_bus.publish(event)
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        # Persist event if we have an event store
        if self.event_store:
            await self.event_store.save_event(event)
        
        # Publish event to the event bus asynchronously
        await self.event_bus.publish_async(event)
    
    def publish_sync(self, event: Event) -> None:
        """
        Publish an event synchronously.
        
        This method blocks until all handlers have completed processing.
        
        Args:
            event: The event to publish
        """
        try:
            # Try to get a running event loop
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # Create a task in the running loop
                future = asyncio.run_coroutine_threadsafe(self.publish(event), loop)
                future.result()  # Wait for the result
            else:
                # Run in the existing loop
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            # No running event loop, create a new one
            asyncio.run(self.publish(event))
    
    async def publish_many(self, events: List[Event]) -> None:
        """
        Publish multiple events sequentially.
        
        Args:
            events: The events to publish
        """
        # Persist events if we have an event store
        if self.event_store:
            for event in events:
                await self.event_store.save_event(event)
        
        # Publish events to the event bus
        await self.event_bus.publish_many(events)
    
    async def publish_many_async(self, events: List[Event]) -> None:
        """
        Publish multiple events concurrently.
        
        Args:
            events: The events to publish
        """
        # Persist events if we have an event store
        if self.event_store:
            for event in events:
                await self.event_store.save_event(event)
        
        # Publish events to the event bus concurrently
        await self.event_bus.publish_many_async(events)