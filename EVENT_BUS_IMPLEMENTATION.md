# Event Bus Implementation Documentation

This document provides an overview of the Event Bus implementation for the UNO framework as part of the architectural modernization plan.

## Implementation Summary

The Event Bus system has been implemented as a core component of the UNO framework, providing a decoupled communication mechanism between components. The implementation follows the protocols defined in `uno.core.protocols.event` and provides comprehensive support for event publishing, subscription, and storage.

## Key Components

### Event

The `Event` class is the foundation of the event system, providing:

- Immutable value objects for domain events
- Built-in metadata (ID, type, timestamp)
- Support for correlation and causation IDs
- Serialization to/from JSON and dictionaries
- Type safety with Pydantic validation

Example usage:

```python
from uno.core.events import Event

class UserCreated(Event):
    user_id: str
    username: str
    email: str

# Create and publish an event
event = UserCreated(
    user_id="123",
    username="johndoe",
    email="john@example.com",
    aggregate_id="user-123"  # Optional domain context
)
```

### AsyncEventBus

The `AsyncEventBus` implements the `EventBusProtocol`, providing:

- Async event publishing and subscription
- Concurrent event handling with concurrency limits
- Error isolation between handlers
- Structured logging

Example usage:

```python
from uno.core.events import AsyncEventBus

# Create an event bus
event_bus = AsyncEventBus(max_concurrency=10)

# Subscribe to events
async def handle_user_created(event):
    print(f"User created: {event.username}")

await event_bus.subscribe("user_created", handle_user_created)

# Publish an event
await event_bus.publish(event)
```

### EventStore

The `EventStore` interface and its implementations provide:

- Persistent storage for events
- Support for event sourcing patterns
- Retrieval by aggregate ID, event type, or time range
- Optimistic concurrency control

Example usage:

```python
from uno.core.events import InMemoryEventStore

# Create an event store
event_store = InMemoryEventStore()

# Store events with optimistic concurrency
await event_store.append_events([event], expected_version=0)

# Retrieve events for an aggregate
events = await event_store.get_events_by_aggregate("user-123")

# Retrieve events by type
user_created_events = await event_store.get_events_by_type("user_created")
```

### EventPublisher

The `EventPublisher` provides a high-level interface for publishing events:

- Immediate or batched event publishing
- Integration with both the event bus and event store
- Support for event collection and deferred publishing
- Synchronous publishing from synchronous code

Example usage:

```python
from uno.core.events import EventPublisher, AsyncEventBus, InMemoryEventStore

# Create the event publisher
event_bus = AsyncEventBus()
event_store = InMemoryEventStore()
publisher = EventPublisher(event_bus, event_store)

# Collect events for batch publishing
publisher.collect(event1)
publisher.collect(event2)

# Publish collected events
await publisher.publish_collected()

# Or publish immediately
await publisher.publish(event3)
```

## Backward Compatibility

To ensure a smooth transition to the new event system, a backward compatibility layer has been implemented in `uno.events.compat`. This provides adapter implementations that expose the old API but use the new implementations internally.

Key compatibility features:

- Deprecation warnings to encourage migration
- Support for legacy event handlers
- Automatic conversion between old and new event formats
- Seamless integration with existing code

## Testing

Comprehensive tests have been implemented for the event system:

- Unit tests for all event system components
- Integration tests for the event bus and event store
- Concurrency and error handling tests
- Performance benchmarks for event publishing

## Implementation Details

### AsyncEventBus

The AsyncEventBus implementation:

1. Maintains a dictionary of event type → set of handlers
2. Uses a semaphore to control concurrency
3. Catches and logs exceptions from handlers to prevent cascade failures
4. Supports both sequential and concurrent event publishing

### EventStore

The EventStore interface defines methods for:

1. Appending events (with optional optimistic concurrency)
2. Retrieving events by aggregate ID
3. Retrieving events by type
4. Filtering events by time range

The InMemoryEventStore implementation provides an in-memory version suitable for testing and development.

## Next Steps

1. Implement a PostgreSQL-based event store (`PostgresEventStore`)
2. Add support for event projections and read models
3. Implement event replay functionality for system recovery
4. Add monitoring and metrics for event processing
5. Develop integration with the Unit of Work pattern

## Conclusion

The Event Bus implementation completes a critical piece of the core infrastructure for the UNO framework. It provides a robust foundation for event-driven architecture and reactive patterns throughout the system.