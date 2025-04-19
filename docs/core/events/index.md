# Event System

The Event System is a core component of the Uno framework, providing a robust foundation for event-driven architecture.

## Overview

Uno's event system enables loosely coupled communication between components through domain events. Events represent meaningful occurrences in the domain that other components might want to react to. The event system follows a publish-subscribe pattern, allowing multiple subscribers to react to the same event.

## Key Components

### Event

`Event` is the foundation of the event system, representing domain events:

```python
from uno.core.events import Event
from uuid import UUID
from datetime import datetime

class UserCreated(Event):
    """Event triggered when a new user is created."""
    
    user_id: UUID
    username: str
    email: str
```

Events are immutable value objects with built-in metadata:
- Event ID: Unique identifier for the event
- Event Type: Automatically derived from the class name
- Timestamp: When the event was created
- Aggregate ID: Optional identifier of the domain entity that triggered the event
- Correlation ID: For tracking related events
- Causation ID: For tracking event chains

### EventBus

The `EventBus` handles event publishing and subscription:

```python
from uno.core.events import AsyncEventBus, Event

# Create an event bus
event_bus = AsyncEventBus(max_concurrency=10)

# Subscribe to events
async def handle_user_created(event: UserCreated):
    print(f"User created: {event.username}")

await event_bus.subscribe("user_created", handle_user_created)

# Publish an event
event = UserCreated(
    user_id=user.id, 
    username=user.username, 
    email=user.email
)
await event_bus.publish(event)
```

The `AsyncEventBus` features:
- Fully asynchronous event handling
- Concurrency control
- Error isolation between handlers
- Type-based routing

### EventStore

The `EventStore` provides persistent storage for events:

```python
from uno.core.events import EventStore, PostgresEventStore

# Create a persistent event store
event_store = PostgresEventStore(connection_factory)

# Store events
await event_store.append_events([event], aggregate_id=user.id)

# Retrieve events by aggregate
events = await event_store.get_events_by_aggregate(user.id)

# Retrieve events by type
user_created_events = await event_store.get_events_by_type("user_created")
```

The `EventStore` enables:
- Event persistence
- Optimistic concurrency control
- Support for event sourcing patterns
- Temporal querying (events by time range)

### EventPublisher

The `EventPublisher` provides a high-level interface for publishing events:

```python
from uno.core.events import EventPublisher

# Create a publisher with bus and store
publisher = EventPublisher(event_bus, event_store)

# Collect events for batch publishing
publisher.collect(event1)
publisher.collect(event2)

# Publish collected events
await publisher.publish_collected()

# Or publish immediately
await publisher.publish(event3)
```

## Integration with Unit of Work

Events integrate seamlessly with the Unit of Work pattern:

```python
from uno.core.uow import UnitOfWork
from uno.domain.entity import AggregateRoot

class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def place_order(self, user_id: UUID, items: List[UUID]) -> Order:
        async with self.uow:
            # Create order
            order = Order.create(user_id, items)
            
            # Add to repository (entity events are automatically collected)
            order_repo = self.uow.get_repository(OrderRepository)
            await order_repo.add(order)
            
            # Add an explicit event if needed
            from myapp.domain.events import OrderPlaced
            self.uow.add_event(OrderPlaced(
                order_id=order.id,
                user_id=user_id,
                item_count=len(items)
            ))
            
            # Events are automatically published after successful commit
            return order
```

## Subscription Management

Event subscriptions can be managed through the subscription system:

```python
from uno.core.events import SubscriptionManager, EventHandlerFunc

# Register handlers with the subscription manager
subscription_manager = SubscriptionManager(event_bus)

@subscription_manager.subscribe("user_created")
async def send_welcome_email(event: UserCreated):
    # Send welcome email logic
    pass

@subscription_manager.subscribe("user_created")
async def update_analytics(event: UserCreated):
    # Update analytics logic
    pass

# Later, start all subscriptions
await subscription_manager.start_all()

# Or stop all subscriptions
await subscription_manager.stop_all()
```

## Implementing Event Handlers

Event handlers should be focused and follow these best practices:

```python
async def handle_user_created(event: UserCreated):
    # 1. Keep handlers small and focused
    # 2. Make handlers idempotent when possible
    # 3. Handle errors properly
    try:
        # Main handler logic
        await send_welcome_email(event.email, event.username)
    except Exception as e:
        # Log the error but don't break the event flow
        logger.error(f"Failed to send welcome email: {e}")
```

## Event Design Patterns

### Event Sourcing

Events can be used as the primary source of truth:

```python
class Order(AggregateRoot[UUID]):
    @classmethod
    def create(cls, user_id: UUID, items: List[UUID]) -> "Order":
        order = cls(id=uuid4(), user_id=user_id, items=items, status="created")
        order.record_event(OrderCreated(
            order_id=order.id,
            user_id=user_id,
            items=items
        ))
        return order
    
    def cancel(self, reason: str) -> None:
        if self.status == "completed":
            raise ValueError("Cannot cancel completed order")
            
        self.status = "cancelled"
        self.cancel_reason = reason
        
        self.record_event(OrderCancelled(
            order_id=self.id,
            reason=reason
        ))
    
    @classmethod
    def from_events(cls, events: List[Event]) -> "Order":
        """Reconstruct order state from events."""
        # Implementation details...
```

### CQRS with Events

Events can drive query model updates:

```python
@subscription_manager.subscribe("order_created")
async def update_order_summary(event: OrderCreated):
    # Update a read model in response to the event
    await order_summary_repo.add(OrderSummary(
        order_id=event.order_id,
        user_id=event.user_id,
        item_count=len(event.items),
        created_at=event.timestamp
    ))
```

## Best Practices

1. **Event Naming**: Use past tense verbs (e.g., `UserCreated`, `OrderPlaced`)
2. **Event Content**: Include all necessary data for handlers in the event
3. **Handler Isolation**: Keep handlers independent and focused
4. **Idempotency**: Design handlers to be idempotent when possible
5. **Error Handling**: Catch and log errors in handlers to prevent cascade failures
6. **Versioning**: Consider versioning for long-lived events
7. **Performance**: Be mindful of event size and handler performance

## Implementation Details

### AsyncEventBus

The `AsyncEventBus` implementation:

1. Maintains a dictionary of event type → set of handlers
2. Uses a semaphore to control concurrency
3. Catches and logs exceptions from handlers
4. Supports both sequential and concurrent event publishing

### EventStore

The `EventStore` interface defines methods for:

1. Appending events (with optional optimistic concurrency)
2. Retrieving events by aggregate ID
3. Retrieving events by type
4. Filtering events by time range

## Related Components

- [Unit of Work](../uow/index.md): Transaction management with event coordination
- [Domain Events](../../domain/domain_events.md): Using events in the domain layer
- [Event-Driven Architecture](../../architecture/event_driven_architecture.md): Architectural patterns