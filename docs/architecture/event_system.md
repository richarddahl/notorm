# Unified Event System

The Uno framework provides a comprehensive event system for implementing event-driven architecture patterns. This document explains the design, components, and usage of the unified event system.

## Overview

The event system is designed to facilitate loose coupling between components through events. It supports:

- Domain events as immutable records of significant occurrences
- Synchronous and asynchronous event handling
- Priority-based event execution
- Topic-based event routing
- Event persistence through event stores
- Comprehensive error handling

## Core Components

### DomainEvent

`DomainEvent` is the base class for all events in the system. It's a Pydantic model with frozen=True, meaning instances are immutable once created.

```python
class UserCreatedEvent(DomainEvent):
    user_id: str
    email: str
    username: str
```

Key features:

- Automatically assigned `event_id` and `timestamp`
- `event_type` derived from the class name (snake_case)
- Optional fields for `aggregate_id`, `aggregate_type`, `correlation_id`, `causation_id`, and `topic`
- Serialization/deserialization methods: `to_dict()`, `from_dict()`, `to_json()`, `from_json()`
- `with_metadata()` method to create a new instance with updated metadata

### EventBus

`EventBus` is responsible for routing events to their handlers:

```python
# Get the global event bus
event_bus = get_event_bus()

# Subscribe a handler to events
event_bus.subscribe(UserCreatedEvent, handler, priority=EventPriority.NORMAL)

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
class UserEventHandler(EventHandler[UserCreatedEvent]):
    def __init__(self):
        super().__init__(UserCreatedEvent)
        
    async def handle(self, event: UserCreatedEvent) -> None:
        # Handle the event...
```

### EventStore

`EventStore` is an abstract base class for event persistence implementations:

```python
class MyEventStore(EventStore[DomainEvent]):
    async def save_event(self, event: DomainEvent) -> None:
        # Save the event...
        
    async def get_events_by_aggregate_id(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[DomainEvent]:
        # Retrieve events...
        
    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[DomainEvent]:
        # Retrieve events...
```

The framework includes an `InMemoryEventStore` implementation for testing and small applications.

### EventPublisher

`EventPublisher` provides a convenient interface for publishing events:

```python
publisher = get_event_publisher()

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
class UserEventHandler(EventHandler[UserCreatedEvent]):
    def __init__(self):
        super().__init__(UserCreatedEvent)
        
    async def handle(self, event: UserCreatedEvent) -> None:
        # Handle the event...
```

### Function-based Handlers

```python
@event_handler(UserCreatedEvent)
async def handle_user_created(event: UserCreatedEvent) -> None:
    # Handle the event...
```

### Event Subscribers

```python
class AnalyticsSubscriber(EventSubscriber):
    def __init__(self, event_bus: EventBus):
        self.events = []
        super().__init__(event_bus)
    
    @event_handler(UserCreatedEvent)
    async def track_user_created(self, event: UserCreatedEvent) -> None:
        # Handle user created event...
    
    @event_handler(OrderPlacedEvent, priority=EventPriority.HIGH)
    async def track_order_placed(self, event: OrderPlacedEvent) -> None:
        # Handle order placed event with high priority...
```

### Priority-based Handling

```python
@event_handler(UserCreatedEvent, priority=EventPriority.HIGH)
async def high_priority_handler(event):
    # Executes before normal priority handlers...

@event_handler(UserCreatedEvent)  # Default is NORMAL priority
async def normal_priority_handler(event):
    # Executes after HIGH priority handlers...

@event_handler(UserCreatedEvent, priority=EventPriority.LOW)
async def low_priority_handler(event):
    # Executes after normal priority handlers...
```

### Topic-based Routing

```python
@event_handler(OrderEvent, topic_pattern="orders.*.created")
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

```python
# Get the default store (if configured)
store = get_event_store()

# Create a custom store
from uno.infrastructure.event_store import PostgresEventStore
custom_store = PostgresEventStore(DomainEvent)

# Save an event
await store.save_event(event)

# Get events by aggregate
events = await store.get_events_by_aggregate_id("aggregate-123")

# Get events by type
events = await store.get_events_by_type("user_created_event", since=yesterday)
```

## Automatic Handler Discovery

```python
# Scan a module for event handlers
import my_handlers_module
scan_for_handlers(my_handlers_module)

# Scan an instance for event handlers
analytics = AnalyticsService()
scan_instance_for_handlers(analytics)
```

## Error Handling

The event system includes comprehensive error handling:

- Each handler is executed in a separate try/except block
- Errors are enriched with event and handler context
- Exceptions in one handler don't prevent others from executing
- Errors are logged with detailed information

```python
try:
    await event_bus.publish(event)
except UnoError as e:
    print(f"Error: {e.message}")
    print(f"Context: {e.context}")
    print(f"Error code: {e.error_code}")
```

## Advanced Usage

### Event Sourcing

For event sourcing patterns, combine the event store with event-sourced repositories:

```python
from uno.core.unified_events import DomainEvent
from uno.infrastructure.event_store import PostgresEventStore, EventSourcedRepository
from uno.domain.models import AggregateRoot

# Create event store
event_store = PostgresEventStore(DomainEvent)

# Create event-sourced repository
repository = EventSourcedRepository(UserAggregate, event_store)

# Get aggregate by ID
user = await repository.get("user-123")

# Save aggregate (preserves and persists events)
user.add_event(UserUpdatedEvent(...))
await repository.save(user)
```

### Event Correlation and Causation

For distributed tracing, use correlation and causation IDs:

```python
# Initial event
initial_event = UserCreatedEvent(
    user_id="user-123",
    email="user@example.com",
    username="testuser",
    correlation_id="corr-123"  # Start a new correlation
)

# Event caused by the initial event
follow_up_event = EmailSentEvent(
    email="user@example.com",
    template="welcome",
    correlation_id=initial_event.correlation_id,  # Same correlation
    causation_id=initial_event.event_id  # Caused by the initial event
)
```

## Performance Considerations

1. **Asynchronous Publishing**: Use for non-critical events to avoid blocking
2. **Priority Control**: Use priorities to ensure critical handlers run first
3. **Topic Filtering**: Use topics to reduce the number of events processed by handlers
4. **Batch Processing**: Collect related events and publish them together
5. **Event Store Selection**: Choose appropriate event store implementation for your scale

## Integration with Other Framework Components

### CQRS Integration

```python
from uno.core.unified_events import collect_event
from uno.domain.cqrs import CommandHandler

class CreateUserCommandHandler(CommandHandler[CreateUserCommand, str]):
    async def _handle(self, command: CreateUserCommand, uow: UnitOfWork) -> str:
        # Business logic...
        
        # Create user
        user_id = str(uuid4())
        
        # Collect event (will be published after command completes)
        collect_event(UserCreatedEvent(
            user_id=user_id,
            email=command.email,
            username=command.username
        ))
        
        return user_id
```

### Domain Model Integration

```python
from uno.domain.models import AggregateRoot
from uno.core.unified_events import DomainEvent

class User(AggregateRoot):
    def __init__(self, id: str, email: str, username: str):
        super().__init__(id=id)
        self.email = email
        self.username = username
        
        # Register event
        self.register_event(UserCreatedEvent(
            user_id=id,
            email=email,
            username=username,
            aggregate_id=id,
            aggregate_type="User"
        ))
    
    def update_email(self, new_email: str) -> None:
        """Update the user's email."""
        self.email = new_email
        self.update()  # Update timestamp
        
        # Register event
        self.register_event(UserUpdatedEvent(
            user_id=self.id,
            fields_updated=["email"],
            aggregate_id=self.id,
            aggregate_type="User"
        ))
```

### API Integration

```python
from fastapi import Depends
from uno.core.unified_events import publish_event, DomainEvent
from uno.api.endpoint import UnoEndpoint

class UserEndpoints(UnoEndpoint):
    @app.post("/users")
    async def create_user(self, data: CreateUserRequest):
        # Business logic...
        
        # Publish event
        event = UserCreatedEvent(
            user_id=user_id,
            email=data.email,
            username=data.username
        )
        publish_event(event)
        
        return {"id": user_id}
```

## Configuring the Event System

The event system is initialized automatically when first used, but you can explicitly configure it:

```python
from uno.core.unified_events import initialize_events, reset_events
from logging import getLogger

# Reset the event system (useful for testing)
reset_events()

# Initialize with custom settings
initialize_events(
    logger=getLogger("events"),
    max_concurrency=20,
    in_memory_event_store=True
)
```

## Testing with Events

```python
import pytest
from uno.core.unified_events import reset_events, initialize_events, get_event_bus

@pytest.fixture(autouse=True)
def reset_event_system():
    """Reset the event system before and after each test."""
    reset_events()
    initialize_events()
    yield
    reset_events()

def test_event_handler():
    """Test that events are properly handled."""
    # Arrange
    handler = MockEventHandler()
    get_event_bus().subscribe(TestEvent, handler)
    
    # Act
    publish_event_sync(TestEvent(data="test"))
    
    # Assert
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0].data == "test"
```

## Best Practices

1. **Keep Events Immutable**: Never modify event properties after creation
2. **Use Descriptive Names**: Name events in the past tense, e.g., `UserCreatedEvent`
3. **Include Relevant Context**: Include all relevant data in events
4. **Handle Failures Gracefully**: Event handlers should be resilient to failures
5. **Control Handler Ordering**: Use priorities to control execution order
6. **Use Correlation IDs**: For distributed tracing across services
7. **Document Event Contracts**: Document the purpose and structure of events
8. **Monitor Event Processing**: Use logging and metrics for monitoring
9. **Test Event Handling**: Write tests for event handlers
10. **Consider Event Versioning**: For evolving event schemas over time

## Summary

The unified event system provides a flexible, type-safe, and performant way to implement event-driven architecture in your Uno applications. By separating event producers from consumers, it enables loose coupling between components while maintaining a clear flow of information.

For migration from previous event systems, see the [Event System Migration Guide](event_system_migration.md).