# Event Subscription Manager UI

This directory contains web components for managing event subscriptions in the UNO framework.

## Components

### wa-event-subscription-manager

A web component for viewing, creating, updating, and deleting event subscriptions, as well as monitoring event processing metrics.

#### Features

- View all event subscriptions with status and metrics
- Create new event subscriptions
- Enable/disable existing subscriptions
- Delete subscriptions
- View metrics for event processing
- View event types

#### Usage

```html
<script type="module" src="/static/components/events/wa-event-subscription-manager.js"></script>

<wa-event-subscription-manager baseUrl="/api/events"></wa-event-subscription-manager>
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| baseUrl | String | The base URL for the event subscription API |
| loading | Boolean | Whether the component is loading data |
| error | String | Error message, if any |
| subscriptions | Array | List of active event subscriptions |
| availableEvents | Array | List of available event types |
| metrics | Object | Subscription metrics data |

#### Events

| Event | Description |
|-------|-------------|
| load-start | Fired when data loading starts |
| load-complete | Fired when data loading completes |
| load-error | Fired when data loading fails |
| notification | Fired when a notification is sent |

## Integration with FastAPI

To use the event subscription manager UI with FastAPI, set up the event subscription router:

```python
from fastapi import FastAPI
from uno.core.events import (
    SubscriptionManager,
    create_subscription_router
)

app = FastAPI()

# Set up the subscription manager
# (see subscription_management_example.py for full example)
subscription_manager = SubscriptionManager(event_bus, repository)
await subscription_manager.initialize()

# Include the subscription router
subscription_router = create_subscription_router(subscription_manager)
app.include_router(subscription_router, prefix="/api/events")

# Serve static files (for the web components)
app.mount("/static", StaticFiles(directory="/path/to/static"), name="static")
```

Then create a simple HTML template to host the component:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Event Subscription Manager</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <wa-event-subscription-manager baseUrl="/api/events"></wa-event-subscription-manager>
    
    <script type="module" src="/static/components/events/wa-event-subscription-manager.js"></script>
</body>
</html>
```

## API Endpoints

The component expects the following API endpoints to be available:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events/subscriptions` | List all subscriptions |
| POST | `/api/events/subscriptions` | Create a new subscription |
| GET | `/api/events/subscriptions/{subscription_id}` | Get a specific subscription |
| PATCH | `/api/events/subscriptions/{subscription_id}` | Update a subscription |
| DELETE | `/api/events/subscriptions/{subscription_id}` | Delete a subscription |
| GET | `/api/events/types` | List all registered event types |
| GET | `/api/events/metrics` | Get overall metrics |

See the `create_subscription_router` function in `/src/uno/core/events/api.py` for the implementation of these endpoints.

## Customization

The component uses the WebAwesome/lit framework and can be customized using CSS custom properties. For example:

```css
wa-event-subscription-manager {
    --subscription-bg: #f0f4f8;
    --subscription-padding: 24px;
    /* etc. */
}
```

## Example

For a complete example of setting up and using the event subscription manager, see the `/src/uno/core/examples/subscription_management_example.py` file.