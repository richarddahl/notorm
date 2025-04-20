# Event Subscription Management

The UNO framework includes a comprehensive event subscription management system that allows for:

- Persistent management of event subscriptions
- Dynamic registration and unregistration of event handlers
- Monitoring and metrics for event processing
- A web-based UI for managing subscriptions

## Overview

The subscription management system consists of:

1. **Subscription Manager** - Core component for managing subscriptions
2. **Subscription Repository** - Persistence layer for subscription configurations
3. **REST API** - HTTP endpoints for managing subscriptions
4. **Web UI** - User interface for subscription management

## Architecture

![Event Subscription Management Architecture](../assets/images/event_subscription_architecture.png)

The event subscription management system integrates with the core event system to provide:

- **Event Type Registry** - A catalog of all registered event types in the system
- **Subscription Registry** - A repository of subscription configurations
- **Handler Registry** - A runtime registry of active event handlers
- **Metrics Collection** - Performance and execution metrics for events and handlers

## Subscription Manager

The `SubscriptionManager` is the central component for managing event subscriptions. It provides:

```python
from uno.core.events import (
    AsyncEventBus,
    SubscriptionManager,
    SubscriptionRepository,
    SubscriptionConfig
)

# Create an event bus
event_bus = AsyncEventBus()

# Create a subscription repository
repository = SubscriptionRepository(config_path="subscriptions.json")

# Create the subscription manager
subscription_manager = SubscriptionManager(
    event_bus=event_bus,
    repository=repository,
    auto_load=True  # Automatically load and register subscriptions on startup
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

# Update a subscription
updated = await subscription_manager.update_subscription(
    subscription_id=subscription.subscription_id,
    config=SubscriptionConfig(
        is_active=False  # Deactivate the subscription
    )
)

# Delete a subscription
await subscription_manager.delete_subscription(subscription.subscription_id)

# Get metrics
metrics = await subscription_manager.get_metrics()
```

## REST API

The framework provides FastAPI endpoints for managing subscriptions:

```python
from fastapi import FastAPI
from uno.core.events import create_subscription_router

app = FastAPI()

# Create the subscription router
subscription_router = create_subscription_router(subscription_manager)

# Include the router in your app
app.include_router(subscription_router, prefix="/api/events")
```

The API provides the following endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events/subscriptions` | List all subscriptions |
| POST | `/api/events/subscriptions` | Create a new subscription |
| GET | `/api/events/subscriptions/{subscription_id}` | Get a specific subscription |
| PATCH | `/api/events/subscriptions/{subscription_id}` | Update a subscription |
| DELETE | `/api/events/subscriptions/{subscription_id}` | Delete a subscription |
| GET | `/api/events/types` | List all registered event types |
| POST | `/api/events/types` | Register a new event type |
| GET | `/api/events/types/{name}` | Get a specific event type |
| GET | `/api/events/metrics` | Get overall metrics |

## Web UI Component

The framework includes a web component for managing subscriptions through a user interface:

```html
<wa-event-subscription-manager baseUrl="/api/events"></wa-event-subscription-manager>
```

To use the UI component:

1. Include the component in your HTML:

```html
<script type="module" src="/static/components/events/wa-event-subscription-manager.js"></script>

<wa-event-subscription-manager baseUrl="/api/events"></wa-event-subscription-manager>
```

2. Serve the static files:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="path/to/static"), name="static")
```

The UI component provides:

- List of all subscriptions with status and metrics
- Form for creating new subscriptions
- Ability to enable/disable/delete subscriptions
- Metrics visualization with charts
- List of available event types

## Subscription Configuration

A subscription is defined by a `SubscriptionConfig` that includes:

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | str | The type of event to subscribe to |
| `handler_name` | str | The name of the handler function |
| `handler_module` | str | The Python module containing the handler |
| `handler_function` | str (optional) | The function name if different from `handler_name` |
| `description` | str | Description of what the handler does |
| `is_active` | bool | Whether the subscription is active |
| `is_async` | bool | Whether the handler is asynchronous |
| `max_retries` | int | Maximum number of retry attempts |
| `retry_delay_ms` | int | Delay between retries in milliseconds |
| `timeout_ms` | int | Timeout for handler execution |
| `filter_expression` | str (optional) | Expression to filter events |
| `batch_size` | int | Batch size for batch handlers |
| `batch_interval_ms` | int | Batch interval for time-based batching |
| `requires_permissions` | list[str] | Required permissions for the handler |
| `alert_on_failure` | bool | Whether to alert on handler failure |
| `alert_threshold` | float | Failure rate threshold for alerting |

## Event Type Registration

Event types can be registered to provide metadata and schema information:

```python
from uno.core.events import EventTypeInfo

# Register an event type
event_type = await subscription_manager.repository.register_event_type(
    EventTypeInfo(
        name="UserCreated",
        description="Triggered when a new user is created",
        schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["user_id", "username", "email"]
        },
        example={
            "user_id": "user-123",
            "username": "johndoe",
            "email": "john@example.com"
        },
        domain="users"
    )
)
```

## Complete Example

A complete example of setting up the subscription management system can be found in the [subscription_management_example.py](../../src/uno/core/examples/subscription_management_example.py) file.

To run the example:

```bash
python -m uno.core.examples.subscription_management_example
```

Then navigate to http://localhost:8000 to access the UI.

You can also use the API endpoints to interact with the subscription system:

```bash
# Create a demo user event
curl -X POST http://localhost:8000/api/demo/user

# Create a demo order event
curl -X POST http://localhost:8000/api/demo/order

# List all subscriptions
curl http://localhost:8000/api/events/subscriptions

# Get metrics
curl http://localhost:8000/api/events/metrics
```

## Metrics and Monitoring

The subscription management system collects detailed metrics for each subscription:

- **Invocation count** - Number of times the handler has been invoked
- **Success count** - Number of successful invocations
- **Failure count** - Number of failed invocations
- **Average processing time** - Average time to process an event
- **P95/P99 processing time** - 95th/99th percentile processing time
- **Min/Max processing time** - Minimum/maximum processing time

These metrics are available through:

1. The `/api/events/metrics` endpoint
2. The web UI dashboard
3. Programmatically via the `subscription_manager.get_metrics()` method

## Best Practices

1. **Descriptive Handler Names**: Use clear, descriptive names for handlers
2. **Proper Event Types**: Follow the naming convention of past-tense verbs for event types
3. **Modular Handlers**: Keep handlers small and focused on a single responsibility
4. **Error Handling**: Ensure handlers handle errors appropriately
5. **Performance Monitoring**: Regularly check handler performance metrics
6. **Idempotent Handlers**: Design handlers to be idempotent (safe to execute multiple times)
7. **Documentation**: Document the purpose and behavior of each subscription

## Security Considerations

1. **Access Control**: Secure the subscription management API with appropriate authentication and authorization
2. **Permission Checking**: Use the `requires_permissions` field to enforce permissions for handlers
3. **Input Validation**: Validate all input to the API endpoints
4. **Auditing**: Enable audit logging for subscription management actions