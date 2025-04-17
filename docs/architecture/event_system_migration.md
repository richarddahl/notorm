# Event System Migration Guide

This guide explains how to migrate from the previous event system implementations to the new unified event system in Uno.

## Overview

The Uno framework previously had two separate event system implementations:

1. `uno.core.events` - A core implementation focusing on event handling and dispatching
2. `uno.domain.events` - A domain-oriented implementation with event store capabilities

The new unified event system (`uno.core.unified_events`) combines the best features of both implementations into a single, consistent API that provides:

- Strongly-typed domain events
- Flexible event subscription and handling
- Priority-based event execution
- Topic-based event routing
- Synchronous and asynchronous event processing
- Event persistence through event stores
- Comprehensive error handling

## Migration Steps

### 1. Update Imports

Replace imports from the old event modules with imports from the unified event system:

```python
# Before - Core events
from uno.core.events import (
    Event, EventBus, EventHandlerWrapper, DefaultEventBus,
    event_handler, initialize_events, get_event_bus, publish_event
)

# Before - Domain events
from uno.domain.events import (
    DomainEvent, EventBus, EventHandler, EventStore, 
    EventPublisher, get_event_bus, get_event_store
)

# After - Unified events
from uno.core.unified_events import (
    DomainEvent, EventBus, EventHandler, EventStore, InMemoryEventStore,
    EventPublisher, EventPriority, EventSubscriber, event_handler,
    initialize_events, reset_events, get_event_bus, get_event_publisher,
    publish_event, publish_event_sync, collect_event, publish_collected_events_async
)
```

### 2. Update Event Definitions

All events should now inherit from the unified `DomainEvent` class:

```python
# Before - Core events
from uno.core.events import Event

class UserCreatedEvent(Event):
    def __init__(self, user_id, email, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.email = email

# Before - Domain events
from uno.domain.events import DomainEvent
from pydantic import BaseModel

class UserCreatedEvent(DomainEvent):
    user_id: str
    email: str

# After - Unified events
from uno.core.unified_events import DomainEvent

class UserCreatedEvent(DomainEvent):
    user_id: str
    email: str
    username: str
```

### 3. Update Event Handlers

#### Class-based Handlers

```python
# Before - Domain events
from uno.domain.events import EventHandler, DomainEvent

class UserEventHandler(EventHandler[UserCreatedEvent]):
    def __init__(self):
        super().__init__(UserCreatedEvent)
        
    async def handle(self, event: UserCreatedEvent) -> None:
        # Handle event...

# After - Unified events
from uno.core.unified_events import EventHandler

class UserEventHandler(EventHandler[UserCreatedEvent]):
    def __init__(self):
        super().__init__(UserCreatedEvent)
        
    async def handle(self, event: UserCreatedEvent) -> None:
        # Handle event...
```

#### Function-based Handlers

```python
# Before - Core events
from uno.core.events import event_handler

@event_handler(UserCreatedEvent)
async def handle_user_created(event):
    # Handle event...

# After - Unified events
from uno.core.unified_events import event_handler

@event_handler(UserCreatedEvent)
async def handle_user_created(event: UserCreatedEvent) -> None:
    # Handle event...
```

### 4. Update Event Subscribers

If you were using a pattern of grouping event handlers in a class:

```python
# Before - Domain events
from uno.domain.events import EventDispatcher, domain_event_handler

class UserEventSubscriber:
    def __init__(self, dispatcher: EventDispatcher):
        self.dispatcher = dispatcher
        
        # Register handlers
        dispatcher.subscribe("user_created", self.handle_user_created)
        
    async def handle_user_created(self, event):
        # Handle event...

# After - Unified events
from uno.core.unified_events import EventSubscriber, event_handler

class UserEventSubscriber(EventSubscriber):
    def __init__(self, event_bus):
        # Event handlers are automatically registered
        super().__init__(event_bus)
    
    @event_handler(UserCreatedEvent)
    async def handle_user_created(self, event: UserCreatedEvent) -> None:
        # Handle event...
```

### 5. Update Event Bus Usage

```python
# Before - Core events
from uno.core.events import get_event_bus, DefaultEventBus

event_bus = DefaultEventBus()
event_bus.subscribe(UserCreatedEvent, handle_user_created)
event_bus.publish(UserCreatedEvent("user-123", "user@example.com"))

# Before - Domain events
from uno.domain.events import get_event_bus, EventBus

event_bus = EventBus()
event_bus.subscribe(UserCreatedEvent, handler, "user.*")
await event_bus.publish(event)

# After - Unified events
from uno.core.unified_events import get_event_bus, EventBus, EventPriority

event_bus = get_event_bus()
event_bus.subscribe(
    UserCreatedEvent, 
    handler, 
    priority=EventPriority.NORMAL,
    topic_pattern="user.*"
)
await event_bus.publish(event)
```

### 6. Update Event Publishing

```python
# Before - Core events
from uno.core.events import publish_event, publish_event_sync

publish_event(event)  # Asynchronous
publish_event_sync(event)  # Synchronous

# Before - Domain events
from uno.domain.events import get_event_publisher

publisher = get_event_publisher()
await publisher.publish(event)

# After - Unified events
from uno.core.unified_events import (
    publish_event, publish_event_sync, publish_event_async,
    collect_event, publish_collected_events_async
)

# Direct publishing
publish_event(event)  # Non-blocking
publish_event_sync(event)  # Blocking
await publish_event_async(event)  # Awaitable

# Batch publishing
collect_event(event1)
collect_event(event2)
await publish_collected_events_async()
```

### 7. Update Event Store Integration

```python
# Before - Domain events
from uno.domain.events import get_event_store
from uno.domain.event_store import PostgresEventStore, EventSourcedRepository

event_store = PostgresEventStore(DomainEvent)
repository = EventSourcedRepository(AggregateRoot, event_store)

# After - Unified events
from uno.core.unified_events import get_event_store, EventStore
from uno.infrastructure.event_store import PostgresEventStore, EventSourcedRepository

# Use the built-in store
event_store = get_event_store()

# Or create a custom one
custom_store = PostgresEventStore(DomainEvent)
repository = EventSourcedRepository(AggregateRoot, custom_store)
```

## Special Features in the Unified Event System

### Priority-based Event Handling

```python
from uno.core.unified_events import event_handler, EventPriority

@event_handler(UserCreatedEvent, priority=EventPriority.HIGH)
async def high_priority_handler(event):
    # Executes before normal priority handlers
    ...

@event_handler(UserCreatedEvent)  # Default is NORMAL priority
async def normal_priority_handler(event):
    ...

@event_handler(UserCreatedEvent, priority=EventPriority.LOW)
async def low_priority_handler(event):
    # Executes after normal priority handlers
    ...
```

### Topic-based Event Routing

```python
from uno.core.unified_events import event_handler

@event_handler(OrderEvent, topic_pattern="orders.*.created")
async def handle_new_orders(event):
    # Only handles OrderEvents with topics matching the pattern
    ...

# Publishing with a topic
order_event = OrderEvent(
    order_id="order-123",
    user_id="user-456",
    items=[...],
    topic="orders.premium.created"  # Will match the pattern above
)
publish_event(order_event)
```

### Automatic Handler Discovery

```python
from uno.core.unified_events import scan_for_handlers, scan_instance_for_handlers

# Scan a module for event handlers
import my_handlers_module
scan_for_handlers(my_handlers_module)

# Scan an instance for event handlers
analytics = AnalyticsService()
scan_instance_for_handlers(analytics)
```

## Performance Best Practices

1. **Use Asynchronous Publishing for Non-Critical Events**:
   ```python
   publish_event(event)  # Non-blocking
   ```

2. **Use Synchronous Publishing When Order Matters**:
   ```python
   publish_event_sync(event)  # Blocking until all handlers complete
   ```

3. **Batch Process Events When Possible**:
   ```python
   collect_event(event1)
   collect_event(event2)
   collect_event(event3)
   await publish_collected_events_async()
   ```

4. **Consider Handler Priorities**:
   - `HIGH`: Use for critical handlers that must run first
   - `NORMAL`: Default for most handlers
   - `LOW`: Use for optional handlers that should run last

5. **Use Topic-based Routing for Large Systems**:
   - Create a topic hierarchy for your events (e.g., `orders.created`, `users.updated`)
   - Subscribe to specific patterns to avoid processing unneeded events

## Common Migration Issues

### Event Definition Changes

The unified event system uses Pydantic models with frozen=True. This means:

- Events are immutable once created
- All fields should be defined in class declaration
- Use `with_metadata()` to create a modified copy of an event

### Handler Execution Order Changes

The unified system respects handler priorities more consistently. If you were relying on a specific execution order in the previous systems, you may need to explicitly set priorities now.

### Async/Sync Differences

The unified system handles both async and non-async handlers, but always executes them in an async context. If you were mixing sync and async code, make sure you're using the correct publishing methods.

## Getting Help

If you encounter issues during migration, please:

1. Review the [event system documentation](/docs/architecture/event_system.md)
2. Check the [API reference](/docs/api/events.md)
3. Review the [example implementations](/src/uno/core/examples/events_example.py)