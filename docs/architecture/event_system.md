# Unified Event System

The Uno framework provides a comprehensive event system for implementing event-driven architecture patterns. This document explains the design, components, and usage of the unified event system.

## Overview

The event system is designed to facilitate loose coupling between components through events. It supports:

- Domain events as immutable records of significant occurrences
- Synchronous and asynchronous event handling
- Priority-based event execution
- Topic-based event routing
- Event persistence through event stores
- Event sourcing for domain aggregates
- Integration with PostgreSQL and Redis
- Comprehensive error handling

## Core Components

### Event

`Event` is the base class for all events in the system. It's a Pydantic model with frozen=True, meaning instances are immutable once created.

```python
from uno.events import Event

class UserCreated(Event):
    username: str
    email: str
    roles: list[str] = []
```

Key features:

- Automatically assigned `id` and `timestamp`
- `type` derived from the class name (snake_case)
- Optional fields for `aggregate_id`, `aggregate_type`, `correlation_id`, `causation_id`, and `topic`
- Serialization/deserialization methods: `to_dict()`, `from_dict()`, `to_json()`, `from_json()`
- `with_metadata()` method to create a new instance with updated metadata

### EventBus

`EventBus` is responsible for routing events to their handlers:

```python
from uno.events import EventBus, EventPriority

# Create an event bus
event_bus = EventBus()

# Subscribe a handler to events
event_bus.subscribe(UserCreated, handler, priority=EventPriority.NORMAL)

# Publish an event
await event_bus.publish(event)
```

Key features:

- Registering and unregistering event handlers
- Priority-based event handler execution
- Topic-based event routing
- Support for both class-based and function-based handlers
- Synchronous and asynchronous publishing

### EventHandler

`EventHandler` is a base class for creating class-based event handlers:

```python
from uno.events import EventHandler

class UserEventHandler(EventHandler[UserCreated]):
    async def handle(self, event: UserCreated) -> None:
        # Handle the event...
```

### EventStore

`EventStore` is an abstract base class for event persistence implementations:

```python
from uno.events.core.store import EventStore

class MyEventStore(EventStore[Event]):
    async def save_event(self, event: Event) -> None:
        # Save the event...
        
    async def get_events_by_aggregate_id(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[Event]:
        # Retrieve events...
        
    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[Event]:
        # Retrieve events...
```

The framework includes `InMemoryEventStore` and `PostgresEventStore` implementations.

### EventPublisher

`EventPublisher` provides a convenient interface for publishing events:

```python
from uno.events.core.publisher import EventPublisher

publisher = EventPublisher(event_bus, event_store)

# Publish a single event
await publisher.publish(event)

# Collect events for batch publishing
publisher.collect(event1)
publisher.collect(event2)

# Publish collected events
await publisher.publish_collected()
```

## Event Handling Patterns

### Class-based Handlers

```python
from uno.events import EventHandler

class UserEventHandler(EventHandler[UserCreated]):
    async def handle(self, event: UserCreated) -> None:
        # Handle the event...
```

### Function-based Handlers

```python
from uno.events import event_handler

@event_handler(UserCreated)
async def handle_user_created(event: UserCreated) -> None:
    # Handle the event...
```

### Event Subscribers

```python
from uno.events import EventSubscriber, event_handler, EventPriority

class AnalyticsSubscriber(EventSubscriber):
    @event_handler(UserCreated)
    async def on_user_created(self, event: UserCreated) -> None:
        # Handle user created event...
    
    @event_handler(OrderPlaced, priority=EventPriority.HIGH)
    async def on_order_placed(self, event: OrderPlaced) -> None:
        # Handle order placed event with high priority...
```

### Priority-based Handling

```python
from uno.events import event_handler, EventPriority

@event_handler(UserCreated, priority=EventPriority.HIGH)
async def high_priority_handler(event):
    # Executes before normal priority handlers...

@event_handler(UserCreated)  # Default is NORMAL priority
async def normal_priority_handler(event):
    # Executes after HIGH priority handlers...

@event_handler(UserCreated, priority=EventPriority.LOW)
async def low_priority_handler(event):
    # Executes after normal priority handlers...
```

### Topic-based Routing

```python
from uno.events import event_handler

@event_handler(OrderEvent, topic="orders.*.created")
async def handle_new_orders(event):
    # Only handles OrderEvents with topics matching the pattern...

# Publishing with a topic
order_event = OrderEvent(
    order_id="order-123",
    items=[...],
    topic="orders.premium.created"  # Will match the pattern above
)
publish_event(order_event)
```

## Publishing Events

### Global API

The event system provides a simplified global API for common operations:

```python
from uno.events import (
    initialize_events,
    publish_event,
    publish_event_sync,
    subscribe,
)

# Initialize the event system
initialize_events()

# Subscribe to events
subscribe(UserCreated, on_user_created)

# Publish an event
publish_event(UserCreated(username="alice", email="alice@example.com"))
```

### Asynchronous Publishing

```python
# Non-blocking (fire and forget)
publish_event(event)

# Awaitable
await publish_event_async(event)
```

### Synchronous Publishing

```python
# Blocking until all handlers complete
publish_event_sync(event)
```

### Batch Publishing

```python
# Collect events
collect_event(event1)
collect_event(event2)
collect_event(event3)

# Publish collected events
await publish_collected_events_async()

# Or clear without publishing
clear_collected_events()
```

## Event Store Integration

### PostgreSQL Store

```python
from uno.events.adapters.postgres import PostgresEventStore

# Create PostgreSQL event store
store = PostgresEventStore(
    event_type=Event,
    schema="public",
    table_name="events",
)

# Save an event
await store.save_event(event)

# Get events by aggregate
events = await store.get_events_by_aggregate_id("aggregate-123")

# Get events by type
events = await store.get_events_by_type("user_created", since=yesterday)
```

### In-Memory Store

```python
from uno.events.core.store import InMemoryEventStore

# Create in-memory event store (useful for testing)
store = InMemoryEventStore()
```

### Redis Integration

```python
from uno.events.adapters.redis import RedisEventPublisher, RedisEventSubscriber

# Create Redis publisher
redis_publisher = RedisEventPublisher(redis_url="redis://localhost:6379/0")

# Publish event to Redis
await redis_publisher.publish(event)

# Create Redis subscriber
redis_subscriber = RedisEventSubscriber(
    event_bus=event_bus,
    event_type=Event,
    redis_url="redis://localhost:6379/0",
)

# Subscribe to event types
await redis_subscriber.subscribe_by_type("user_created")

# Start listening for events
await redis_subscriber.start()
```

## Event Sourcing

The event system includes built-in support for event sourcing:

```python
from uno.events.sourcing import AggregateRoot, apply_event

class User(AggregateRoot):
    def __init__(self, id: Optional[str] = None):
        super().__init__(id)
        self.username = None
        self.email = None
        self.is_active = False
    
    def create(self, username: str, email: str) -> None:
        event = UserCreated(username=username, email=email)
        self.apply(event)
    
    @apply_event
    def apply_user_created(self, event: UserCreated) -> None:
        self.username = event.username
        self.email = event.email
        self.is_active = True
```

And event-sourced repositories:

```python
from uno.events.sourcing import EventSourcedRepository

# Create repository
repository = EventSourcedRepository(User, event_store)

# Create and save aggregate
user = User()
user.create(username="alice", email="alice@example.com")
await repository.save(user)

# Reconstitute aggregate from event history
user = await repository.find_by_id("user-123")
```

## Error Handling

The event system includes comprehensive error handling:

- Each handler is executed in a separate try/except block
- Errors are logged with structured logging (using structlog)
- Exceptions in one handler don't prevent others from executing

```python
import structlog

# Get a logger
logger = structlog.get_logger("uno.events")

# Log events with structured context
logger.info(
    "Event processed",
    event_id=event.id,
    event_type=event.type,
    handler="UserEventHandler",
)
```

## Testing with Events

The event system includes tools for testing:

```python
from uno.events.testing import MockEventStore, TestEventBus

# Create test event bus
event_bus = TestEventBus()

# Create mock event store
event_store = MockEventStore()

# Check published events
assert event_bus.has_published_event_type("user_created")
assert len(event_bus.get_published_events(UserCreated)) == 1

# Check stored events
assert event_store.has_saved_event(event.id)
```

## Best Practices

1. **Keep Events Immutable**: Never modify event properties after creation
2. **Use Descriptive Names**: Name events in the past tense, e.g., `UserCreated`
3. **Include Relevant Context**: Include all relevant data in events
4. **Handle Failures Gracefully**: Event handlers should be resilient to failures
5. **Control Handler Ordering**: Use priorities to control execution order
6. **Use Correlation IDs**: For distributed tracing across services
7. **Document Event Contracts**: Document the purpose and structure of events
8. **Monitor Event Processing**: Use structured logging for monitoring
9. **Test Event Handling**: Write tests for event handlers
10. **Consider Event Versioning**: For evolving event schemas over time

## Examples

For more detailed examples, see the examples in the `uno.events.examples` package:

- Basic usage: `uno.events.examples.basic_usage`
- Event sourcing: `uno.events.examples.event_sourcing`
- PostgreSQL integration: `uno.events.examples.postgres_integration`
- Redis integration: `uno.events.examples.redis_integration`