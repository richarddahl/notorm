"""
Public API for the Uno event system.

This module provides a simple public API for initializing and using
the event system without directly interacting with the underlying
implementation details.
"""

import asyncio
from typing import List, Optional, Type, TypeVar, Union

import structlog

from uno.events.core.bus import EventBus
from uno.events.core.event import Event
from uno.events.core.handler import EventHandler, EventHandlerCallable, EventPriority
from uno.events.core.publisher import EventPublisher
from uno.events.core.store import EventStore, InMemoryEventStore

# Type variables
E = TypeVar("E", bound=Event)

# Global instances
_event_bus: Optional[EventBus] = None
_event_store: Optional[EventStore] = None
_event_publisher: Optional[EventPublisher] = None


def initialize_events(
    in_memory_store: bool = True,
    max_concurrency: int = 10,
    event_store: Optional[EventStore] = None,
) -> None:
    """
    Initialize the global event system.
    
    This function sets up the global event bus, store, and publisher,
    making them available through the getter functions.
    
    Args:
        in_memory_store: Whether to create an in-memory event store
        max_concurrency: Maximum number of concurrent event handlers
        event_store: Optional custom event store implementation
        
    Raises:
        RuntimeError: If the event system is already initialized
    """
    global _event_bus, _event_store, _event_publisher
    
    if _event_bus is not None:
        raise RuntimeError("Event system is already initialized")
    
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )
    
    # Create components
    _event_bus = EventBus(max_concurrency=max_concurrency)
    
    if event_store is not None:
        _event_store = event_store
    elif in_memory_store:
        _event_store = InMemoryEventStore()
    
    _event_publisher = EventPublisher(_event_bus, _event_store)
    
    structlog.get_logger("uno.events").info("Event system initialized")


def reset_events() -> None:
    """
    Reset the global event system.
    
    This function clears all global event components, primarily used
    for testing scenarios.
    """
    global _event_bus, _event_store, _event_publisher
    _event_bus = None
    _event_store = None
    _event_publisher = None
    
    structlog.get_logger("uno.events").info("Event system reset")


def get_event_bus() -> EventBus:
    """
    Get the global event bus.
    
    Returns:
        The global event bus
        
    Raises:
        RuntimeError: If the event system is not initialized
    """
    if _event_bus is None:
        initialize_events()
    
    return _event_bus


def get_event_store() -> Optional[EventStore]:
    """
    Get the global event store.
    
    Returns:
        The global event store, or None if no store is configured
    """
    if _event_bus is None:
        initialize_events()
    
    return _event_store


def get_event_publisher() -> EventPublisher:
    """
    Get the global event publisher.
    
    Returns:
        The global event publisher
        
    Raises:
        RuntimeError: If the event system is not initialized
    """
    if _event_publisher is None:
        initialize_events()
    
    return _event_publisher


def publish_event(event: Event) -> None:
    """
    Publish an event.
    
    This function publishes an event asynchronously without waiting
    for handlers to complete.
    
    Args:
        event: The event to publish
    """
    asyncio.create_task(get_event_publisher().publish(event))


def publish_event_sync(event: Event) -> None:
    """
    Publish an event synchronously.
    
    This function publishes an event and blocks until all handlers
    have completed processing.
    
    Args:
        event: The event to publish
    """
    get_event_publisher().publish_sync(event)


async def publish_event_async(event: Event) -> None:
    """
    Publish an event asynchronously.
    
    This function publishes an event and waits for all handlers
    to complete processing.
    
    Args:
        event: The event to publish
    """
    await get_event_publisher().publish(event)


def collect_event(event: Event) -> None:
    """
    Collect an event for later batch publishing.
    
    Args:
        event: The event to collect
    """
    get_event_publisher().collect(event)


def collect_events(events: List[Event]) -> None:
    """
    Collect multiple events for later batch publishing.
    
    Args:
        events: The events to collect
    """
    get_event_publisher().collect_many(events)


def publish_collected_events() -> None:
    """
    Publish all collected events.
    
    This function publishes all collected events asynchronously without
    waiting for handlers to complete.
    """
    asyncio.create_task(get_event_publisher().publish_collected())


async def publish_collected_events_async() -> None:
    """
    Publish all collected events asynchronously.
    
    This function publishes all collected events and waits for all
    handlers to complete processing.
    
    Returns:
        A coroutine that completes when all handlers have finished
    """
    await get_event_publisher().publish_collected_async()


def subscribe(
    event_type: Type[E],
    handler: Union[EventHandler[E], EventHandlerCallable[E]],
    priority: EventPriority = EventPriority.NORMAL,
    topic: Optional[str] = None,
) -> None:
    """
    Subscribe a handler to events of a specific type.
    
    Args:
        event_type: The type of event to subscribe to
        handler: The handler function or class
        priority: The execution priority for this handler
        topic: Optional topic filter for topic-based routing
    """
    get_event_bus().subscribe(
        event_type=event_type,
        handler=handler,
        priority=priority,
        topic=topic,
    )


def unsubscribe(
    event_type: Type[E],
    handler: Union[EventHandler[E], EventHandlerCallable[E]],
    topic: Optional[str] = None,
) -> None:
    """
    Unsubscribe a handler from events of a specific type.
    
    Args:
        event_type: The type of event to unsubscribe from
        handler: The event handler to unsubscribe
        topic: Optional topic filter for topic-based routing
    """
    get_event_bus().unsubscribe(
        event_type=event_type,
        handler=handler,
        topic=topic,
    )