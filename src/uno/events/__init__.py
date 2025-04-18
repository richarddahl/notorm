"""
Unified event system for Uno framework.

This package provides a modern, simple event system for implementing event-driven
architectures in Python applications. It supports both synchronous and asynchronous
event handling, persistent event storage, and integration with PostgreSQL and Redis.

Key features:
- Simple event definition with Pydantic models
- Sync and async event publishing
- Topic-based routing for flexible subscription
- Event persistence with PostgreSQL 
- Pub/sub capabilities with Redis
- Event sourcing capabilities for domain aggregates
- Structured logging for enhanced observability
- Integrated error handling
"""

from uno.events.core.event import Event
from uno.events.core.bus import EventBus
from uno.events.core.store import EventStore
from uno.events.core.handler import EventHandler, event_handler
from uno.events.core.publisher import EventPublisher
from uno.events.core.subscriber import EventSubscriber

# Public API
from uno.events.api import (
    initialize_events,
    get_event_bus,
    get_event_store,
    get_event_publisher,
    publish_event,
    publish_event_sync,
    publish_event_async,
    collect_event,
    collect_events,
    publish_collected_events,
    publish_collected_events_async,
    subscribe,
    unsubscribe,
)

__all__ = [
    # Core classes
    "Event",
    "EventBus",
    "EventStore",
    "EventHandler",
    "EventPublisher",
    "EventSubscriber",
    "event_handler",
    
    # Public API
    "initialize_events",
    "get_event_bus",
    "get_event_store",
    "get_event_publisher",
    "publish_event",
    "publish_event_sync", 
    "publish_event_async",
    "collect_event",
    "collect_events",
    "publish_collected_events",
    "publish_collected_events_async",
    "subscribe",
    "unsubscribe",
]