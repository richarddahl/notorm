# Event-Driven Architecture in the Uno Framework

Event-Driven Architecture (EDA) is a software architecture pattern that promotes the production, detection, consumption of, and reaction to events. The Uno framework implements a robust event system with topic-based routing, event persistence, and both synchronous and asynchronous event handling.

## Core Concepts

### Events

Events in the Uno framework are represented by the `DomainEvent` class and represent significant occurrences within the domain model. Events are immutable records of something that happened, containing:

- **Metadata**: Event ID, timestamp, type, version
- **Context Information**: Aggregate ID, aggregate type
- **Correlation Data**: Correlation ID, causation ID for tracing event chains
- **Routing Information**: Topic for message routing
- **Payload**: Event-specific data

```python
from uno.domain.events import DomainEvent

class UserCreatedEvent(DomainEvent):
    user_id: str
    username: str
    email: str
    
    # The event_type field is automatically set to the class name
```

### Event Bus

The Event Bus is the central component of the event system, responsible for:

- **Publication**: Distributing events to interested subscribers
- **Subscription**: Allowing handlers to register for specific events
- **Routing**: Directing events to the appropriate handlers

```python
from uno.domain.events import get_event_bus, EventPriority

# Get the default event bus
event_bus = get_event_bus()

# Subscribe to events
event_bus.subscribe(
    handler=my_handler,
    event_type=UserCreatedEvent,
    topic_pattern="users.*",
    priority=EventPriority.HIGH
)

# Publish an event
await event_bus.publish(event)
```

### Event Handlers

Event handlers process events by executing business logic in response to them. There are two ways to define handlers:

1. **Handler Functions**:

```python
from uno.domain.events import subscribe

@subscribe(event_type=UserCreatedEvent)
async def handle_user_created(event: UserCreatedEvent) -> None:
    # Handle the event
    print(f"User created: {event.username}")
    
# Synchronous handlers are also supported
@subscribe(event_type=UserDeletedEvent)
def handle_user_deleted(event: UserDeletedEvent) -> None:
    # Handle the event synchronously
    print(f"User deleted: {event.user_id}")
```

2. **Handler Classes**:

```python
from uno.domain.events import EventHandler

class UserCreatedHandler(EventHandler[UserCreatedEvent]):
    def __init__(self):
        super().__init__(UserCreatedEvent)
    
    async def handle(self, event: UserCreatedEvent) -> None:
        # Handle the event
        print(f"User created: {event.username}")
```

### Event Store

The Event Store provides persistence for domain events, enabling:

- **Event Sourcing**: Reconstructing aggregates from their event history
- **Audit Trail**: Complete history of all changes to the system
- **Replay**: Replaying events for debugging or recovery

```python
from uno.domain.event_store import create_database_event_store
from uno.domain.events import get_event_store

# Use the default in-memory event store
event_store = get_event_store()

# Or create a database event store
db_event_store = create_database_event_store(
    session_factory=my_session_factory,
    event_registry=my_event_registry
)

# Append an event
await event_store.append(event)

# Get events
events = await event_store.get_events(
    aggregate_id="user-123",
    since_version=5
)
```

## Topic-Based Routing

The Uno framework supports topic-based routing for events, which allows handlers to subscribe to events based on topic patterns. Topics are hierarchical strings that can be used to categorize events:

```python
# Publish an event with a topic
event = UserCreatedEvent(
    user_id="user-123",
    username="john",
    email="john@example.com",
    topic="users.created"
)

# Subscribe to a specific topic
event_bus.subscribe(
    handler=my_handler,
    topic_pattern="users.created"
)

# Subscribe to all user events
event_bus.subscribe(
    handler=my_audit_handler,
    topic_pattern="users.*"
)

# Subscribe to all creation events
event_bus.subscribe(
    handler=my_creation_handler,
    topic_pattern="*.created"
)
```

## Event Correlation and Causation

The Uno framework supports event correlation and causation for distributed tracing:

```python
# Create an event with correlation ID
event = UserCreatedEvent(
    user_id="user-123",
    username="john",
    email="john@example.com",
    correlation_id="transaction-456"
)

# Create a causally related event
related_event = UserProfileCreatedEvent(
    user_id="user-123",
    correlation_id=event.correlation_id,
    causation_id=event.event_id
)
```

## Event Persistence

Events can be persisted in a database using the `DatabaseEventStore`:

```python
from uno.domain.event_store import DatabaseEventStore, register_event

# Register event types
@register_event
class UserCreatedEvent(DomainEvent):
    user_id: str
    username: str
    email: str

# Create a database event store
event_store = DatabaseEventStore(
    session_factory=lambda: AsyncSession(engine),
    event_types={"UserCreatedEvent": UserCreatedEvent}
)

# Create the event store schema
await event_store.create_schema()

# Persist events
await event_store.append(event)

# Query events
events = await event_store.get_events(
    aggregate_id="user-123",
    since_timestamp=datetime(2023, 1, 1)
)
```

## Event Sourcing

The Uno framework supports event sourcing, which allows aggregates to be rebuilt from their event history:

```python
from uno.domain.event_store import EventSourcedRepository
from uno.domain.model import AggregateRoot

class User(AggregateRoot):
    def __init__(self, id: str):
        super().__init__(id=id)
        self.username = None
        self.email = None
    
    def create(self, username: str, email: str) -> None:
        self.register_event(UserCreatedEvent(
            user_id=self.id,
            username=username,
            email=email
        ))
    
    def apply_usercreated(self, event: UserCreatedEvent) -> None:
        self.username = event.username
        self.email = event.email

# Create a repository for the User aggregate
repository = EventSourcedRepository(
    aggregate_type=User,
    event_store=event_store
)

# Get a user by ID (rebuilds from events)
user = await repository.get_by_id("user-123")
```

## Best Practices

### Event Design

1. **Be Explicit**: Name events clearly to indicate what happened
2. **Include Context**: Include enough information to understand the event
3. **Immutability**: Events should be immutable and represent something that happened
4. **Semantic Versioning**: Version events when they evolve
5. **Keep it Simple**: Avoid complex events, prefer multiple simple events

### Event Handling

1. **Idempotency**: Event handlers should be idempotent (can be called multiple times)
2. **Fault Tolerance**: Handlers should handle failures gracefully
3. **Asynchronous Processing**: Use async handlers for long-running operations
4. **Prioritization**: Use priorities for critical handlers
5. **Decoupling**: Avoid direct dependencies between handlers

### Event Sourcing

1. **Snapshot Aggregates**: Cache reconstructed aggregates for performance
2. **Evolve Carefully**: Be careful when evolving event schemas
3. **Separation of Concerns**: Separate command and query responsibilities
4. **Event Migration**: Have a strategy for migrating events when schemas change
5. **Performance Considerations**: Event sourcing can be slow for large aggregates

## Integration with Bounded Contexts

Events are a key mechanism for integrating bounded contexts in a loosely coupled way:

```python
# Context A - Publishing an event
from uno.domain.events import get_event_publisher

publisher = get_event_publisher()
await publisher.publish(UserCreatedEvent(
    user_id="user-123",
    username="john",
    email="john@example.com",
    topic="users.created"
))

# Context B - Subscribing to the event
from uno.domain.events import subscribe

@subscribe(topic_pattern="users.created")
async def create_user_profile(event: UserCreatedEvent) -> None:
    # Create a profile in Context B
    profile = Profile(user_id=event.user_id)
    await profile_repository.add(profile)
```

## Conclusion

The event-driven architecture in the Uno framework provides a powerful and flexible way to implement loosely coupled, scalable systems. By using domain events, the event bus, and event sourcing, you can build systems that are responsive, resilient, and maintainable.