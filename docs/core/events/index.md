# Event System

The UNO framework includes a comprehensive event system that provides an implementation of the event-driven architecture pattern. The event system allows components to communicate through events, decoupling the sender from the receiver.

## Components

- [**Event**](./event.md) - Base class for defining domain events
- [**Event Bus**](./bus.md) - Central hub for publishing and subscribing to events
- [**Event Store**](./store.md) - Persistence layer for events, supporting event sourcing
- [**Event Publisher**](./publisher.md) - High-level API for publishing events
- [**Postgres Event Store**](./postgres.md) - PostgreSQL implementation of the event store
- [**Subscription Management**](./subscription_management.md) - Management of event subscriptions with UI

## Key Features

- **Event Sourcing** - Use events as the source of truth for application state
- **Domain Events** - Represent business events in your domain
- **Decoupled Architecture** - Decouple components by using events for communication
- **Event Persistence** - Store events for later retrieval and replay
- **Asynchronous Processing** - Process events asynchronously
- **Event Subscriptions** - Subscribe to events with configurable handlers
- **Metrics and Monitoring** - Track event processing performance and success rates
- **Management UI** - Web-based UI for managing event subscriptions

## Example Usage

```python
from uno.core.events import AsyncEventBus, Event, EventPublisher

# Define an event
class UserCreated(Event):
    user_id: str
    username: str
    email: str
    
    @property
    def aggregate_id(self) -> str:
        return self.user_id

# Create an event bus
event_bus = AsyncEventBus()

# Define a handler
async def send_welcome_email(event: UserCreated):
    print(f"Sending welcome email to {event.email}")

# Subscribe to the event
await event_bus.subscribe("UserCreated", send_welcome_email)

# Create and publish an event
event = UserCreated(
    user_id="user-123",
    username="johndoe",
    email="john@example.com"
)
await event_bus.publish(event)
```

## Advanced Example with Event Store

```python
from uno.core.events import AsyncEventBus, Event, PostgresEventStore, PostgresEventStoreConfig, EventPublisher

# Configure event store
config = PostgresEventStoreConfig(
    connection_string="postgresql+asyncpg://user:password@localhost/events",
    schema="events",
    table_name="events"
)
event_store = PostgresEventStore(config=config)

# Initialize event store
await event_store.initialize()

# Create event bus
event_bus = AsyncEventBus()

# Create event publisher
publisher = EventPublisher(
    event_bus=event_bus,
    event_store=event_store
)

# Publish event with persistence
event = UserCreated(
    user_id="user-123",
    username="johndoe",
    email="john@example.com"
)
await publisher.publish(event)

# Retrieve events
events = await event_store.get_events_by_aggregate("user-123")
```

## Subscription Management Example

```python
from uno.core.events import (
    AsyncEventBus, 
    SubscriptionManager, 
    SubscriptionRepository,
    SubscriptionConfig
)

# Create a subscription repository
repository = SubscriptionRepository(config_path="subscriptions.json")

# Create a subscription manager
subscription_manager = SubscriptionManager(
    event_bus=event_bus,
    repository=repository
)

# Initialize the manager
await subscription_manager.initialize()

# Create a subscription
subscription = await subscription_manager.create_subscription(
    SubscriptionConfig(
        event_type="UserCreated",
        handler_name="send_welcome_email",
        handler_module="your.module.path",
        description="Sends a welcome email to newly registered users"
    )
)
```

## FastAPI Integration

```python
from fastapi import FastAPI
from uno.core.events import create_subscription_router

app = FastAPI()

# Include the subscription router
subscription_router = create_subscription_router(subscription_manager)
app.include_router(subscription_router, prefix="/api/events")
```

## Web UI Component

```html
<wa-event-subscription-manager baseUrl="/api/events"></wa-event-subscription-manager>
```

## Learn More

- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Domain Events Pattern](https://martinfowler.com/eaaDev/DomainEvent.html)
- [Command Query Responsibility Segregation (CQRS)](https://martinfowler.com/bliki/CQRS.html)