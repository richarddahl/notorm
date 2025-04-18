"""
Backward compatibility layer for the event system.

This module provides compatibility with the old event system implementation,
allowing existing code to continue working while migrating to the new APIs.
"""

import warnings
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, Callable

from uno.core.events.event import Event as CoreEvent
from uno.core.events.bus import AsyncEventBus
from uno.core.events.store import EventStore
from uno.core.events.publisher import EventPublisher

from uno.events.core.event import Event as LegacyEvent
from uno.events.core.bus import EventBus as LegacyEventBus
from uno.events.core.store import EventStore as LegacyEventStore
from uno.events.core.publisher import EventPublisher as LegacyEventPublisher
from uno.events.core.handler import EventHandler as LegacyEventHandler, EventPriority


# Type variables
E = TypeVar('E', bound=LegacyEvent)


class CompatEventBus(LegacyEventBus):
    """
    Compatibility wrapper for the new AsyncEventBus implementation.
    
    This class implements the old EventBus interface while using the new
    AsyncEventBus under the hood, allowing gradual migration.
    """
    
    def __init__(self, max_concurrency: int = 10):
        """
        Initialize the compatibility event bus.
        
        Args:
            max_concurrency: Maximum number of handlers to execute concurrently
        """
        warnings.warn(
            "CompatEventBus is deprecated and will be removed in a future version. "
            "Use uno.core.events.AsyncEventBus instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Initialize the old EventBus to set up the logger
        super().__init__(max_concurrency)
        
        # Create the new bus
        self._new_bus = AsyncEventBus(max_concurrency)
        
        # Track subscriptions for compatibility
        self._legacy_subscriptions = {}
    
    def subscribe(
        self,
        event_type: Type[E],
        handler: Union[LegacyEventHandler[E], Callable[[E], Any]],
        priority: EventPriority = EventPriority.NORMAL,
        topic: Optional[str] = None,
    ) -> None:
        """
        Subscribe a handler to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The event handler (function or class)
            priority: The execution priority for this handler
            topic: Optional topic filter
        """
        if topic:
            warnings.warn(
                "Topic filtering is not supported in the new event system. "
                "The topic parameter will be ignored.",
                DeprecationWarning,
                stacklevel=2
            )
        
        # Create a wrapper that adapts between the old and new APIs
        async def wrapper(event):
            # The new bus expects a standard function as handler
            if isinstance(handler, LegacyEventHandler):
                result = handler.handle(event)
                if hasattr(result, "__await__"):
                    await result
            else:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result
        
        # Store the wrapper for later unsubscription
        if event_type not in self._legacy_subscriptions:
            self._legacy_subscriptions[event_type] = {}
        self._legacy_subscriptions[event_type][handler] = wrapper
        
        # Subscribe to the new bus
        asyncio.create_task(
            self._new_bus.subscribe(event_type.get_event_type(), wrapper)
        )
    
    def unsubscribe(
        self,
        event_type: Type[E],
        handler: Union[LegacyEventHandler[E], Callable[[E], Any]],
        topic: Optional[str] = None,
    ) -> None:
        """
        Unsubscribe a handler from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The event handler to unsubscribe
            topic: Optional topic filter
        """
        # Get the wrapper
        wrapper = self._legacy_subscriptions.get(event_type, {}).get(handler)
        if not wrapper:
            return
        
        # Unsubscribe from the new bus
        asyncio.create_task(
            self._new_bus.unsubscribe(event_type.get_event_type(), wrapper)
        )
        
        # Remove from our tracking
        self._legacy_subscriptions[event_type].pop(handler, None)
        if not self._legacy_subscriptions[event_type]:
            self._legacy_subscriptions.pop(event_type, None)
    
    async def publish(self, event: LegacyEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        await self._new_bus.publish(event)
    
    async def publish_async(self, event: LegacyEvent) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        await self._new_bus.publish(event)
    
    async def publish_many(self, events: List[LegacyEvent]) -> None:
        """
        Publish multiple events.
        
        Args:
            events: The events to publish
        """
        await self._new_bus.publish_many(events)
    
    async def publish_many_async(self, events: List[LegacyEvent]) -> None:
        """
        Publish multiple events asynchronously.
        
        Args:
            events: The events to publish
        """
        await self._new_bus.publish_many(events)


# Update the original module's EventBus to use our compatibility layer
import uno.events.core.bus
uno.events.core.bus.EventBus = CompatEventBus


class CompatEvent(LegacyEvent):
    """
    Compatibility wrapper for the new Event class.
    
    This class maintains the interface of the old Event class while
    providing warnings and compatibility with the new implementation.
    """
    
    def __init__(self, **kwargs):
        """Initialize with deprecation warning."""
        warnings.warn(
            "CompatEvent is deprecated and will be removed in a future version. "
            "Use uno.core.events.Event instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(**kwargs)


# Update the original module's Event to use our compatibility layer
import uno.events.core.event
uno.events.core.event.Event = CompatEvent