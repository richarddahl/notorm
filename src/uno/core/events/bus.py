"""
AsyncEventBus implementation for the UNO framework.

This module provides the core event bus implementation that conforms to the
EventBusProtocol. It supports publishing and subscribing to events with
async handling and concurrency control.
"""

import asyncio
import logging
from typing import Dict, List, Set, Type, Callable, Awaitable, Optional, Any

import structlog

from uno.core.protocols.event import EventBusProtocol, EventProtocol, EventHandler
from uno.core.events.event import Event


class AsyncEventBus(EventBusProtocol):
    """
    Asynchronous event bus implementation that conforms to EventBusProtocol.
    
    The AsyncEventBus provides a central hub for publishing events and
    notifying subscribers. It supports multiple subscribers for each event type
    and handles all event processing asynchronously.
    
    Features:
    - Async event processing
    - Concurrency control
    - Error handling for subscribers
    - Support for various event types
    """
    
    def __init__(self, max_concurrency: int = 10):
        """
        Initialize the AsyncEventBus.
        
        Args:
            max_concurrency: Maximum number of handlers to execute concurrently
        """
        structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
        self.logger = structlog.get_logger("uno.core.events")
        self.max_concurrency = max_concurrency
        self._subscriptions: Dict[str, Set[EventHandler]] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    async def publish(self, event: EventProtocol) -> None:
        """
        Publish an event to all subscribers.
        
        This method notifies all handlers subscribed to this event type.
        If a handler raises an exception, it will be logged but not propagated
        to ensure other handlers can still process the event.
        
        Args:
            event: The event to publish
        """
        event_type = event.event_type
        self.logger.debug(
            "Publishing event",
            event_type=event_type,
            event_id=event.event_id,
        )
        
        handlers = self._subscriptions.get(event_type, set())
        if not handlers:
            self.logger.debug(
                "No handlers registered for event",
                event_type=event_type,
            )
            return
        
        # Create tasks for all handlers
        tasks = []
        for handler in handlers:
            tasks.append(self._execute_handler(handler, event))
        
        # Wait for all handlers to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of events to subscribe to
            handler: The handler function to call when an event is received
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = set()
        
        self._subscriptions[event_type].add(handler)
        
        self.logger.info(
            "Handler subscribed to event type",
            event_type=event_type,
            handler=getattr(handler, "__name__", str(handler))
        )
    
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of events to unsubscribe from
            handler: The handler function to remove
        """
        if event_type in self._subscriptions:
            self._subscriptions[event_type].discard(handler)
            
            self.logger.info(
                "Handler unsubscribed from event type",
                event_type=event_type,
                handler=getattr(handler, "__name__", str(handler))
            )
    
    async def _execute_handler(self, handler: EventHandler, event: EventProtocol) -> None:
        """
        Execute a single event handler with concurrency control and error handling.
        
        Args:
            handler: The handler to execute
            event: The event to pass to the handler
        """
        async with self._semaphore:
            try:
                await handler(event)
            except Exception as e:
                self.logger.error(
                    "Error in event handler",
                    handler=getattr(handler, "__name__", str(handler)),
                    event_type=event.event_type,
                    event_id=event.event_id,
                    error=str(e),
                    exc_info=True,
                )
    
    async def publish_many(self, events: List[EventProtocol]) -> None:
        """
        Publish multiple events sequentially.
        
        Args:
            events: The events to publish
        """
        for event in events:
            await self.publish(event)
    
    async def publish_many_async(self, events: List[EventProtocol]) -> None:
        """
        Publish multiple events concurrently.
        
        Args:
            events: The events to publish
        """
        tasks = [self.publish(event) for event in events]
        await asyncio.gather(*tasks)