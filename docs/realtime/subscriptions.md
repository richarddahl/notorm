# Subscription Management

The subscription management system in the Uno framework provides a comprehensive solution for managing real-time update subscriptions, enabling users to receive notifications, WebSocket messages, and Server-Sent Events (SSE) based on their interests.

## Overview

The subscription management system consists of several key components:

- **SubscriptionManager**: Central manager for creating and managing subscriptions
- **Subscription**: Core data structure representing a subscription
- **SubscriptionStore**: Storage for subscriptions with query capabilities
- **Event Handlers**: Components that process events and deliver updates to subscribers

## Key Features

- **Multiple Subscription Types**: Resource, resource type, topic, and query-based subscriptions
- **Flexible Filtering**: Filter events based on subscription parameters
- **Integration with Notifications**: Send notifications for events matching subscriptions
- **WebSocket/SSE Integration**: Send WebSocket messages and SSE events to subscribers
- **Authorization**: Authorize subscription creation based on user permissions
- **Expiration**: Set subscription expiration dates
- **Labeling**: Add metadata and labels to categorize subscriptions

## Basic Usage

### Setting Up the Subscription Manager

```python
from uno.realtime.subscriptions import SubscriptionManager
from uno.realtime.subscriptions import NotificationEventHandler, WebSocketEventHandler, SSEEventHandler
from uno.realtime.notifications import NotificationHub
from uno.realtime.websocket import WebSocketManager
from uno.realtime.sse import SSEManager

# Create the managers
notification_hub = NotificationHub()
websocket_manager = WebSocketManager()
sse_manager = SSEManager()
subscription_manager = SubscriptionManager()

# Add event handlers for different delivery methods
subscription_manager.add_event_handler(```

NotificationEventHandler(notification_hub).handle_event
```
)
subscription_manager.add_event_handler(```

WebSocketEventHandler(websocket_manager).handle_event
```
)
subscription_manager.add_event_handler(```

SSEEventHandler(sse_manager).handle_event
```
)
```

### Creating Subscriptions

```python
# Subscribe to a specific resource
resource_sub_id = await subscription_manager.subscribe_to_resource(```

user_id="user123",
resource_id="post789",
resource_type="post"
```
)

# Subscribe to all resources of a type
type_sub_id = await subscription_manager.subscribe_to_resource_type(```

user_id="user123",
resource_type="comment"
```
)

# Subscribe to a topic
topic_sub_id = await subscription_manager.subscribe_to_topic(```

user_id="user123",
topic="announcements"
```
)

# Subscribe to a query
from datetime import datetime, timedelta
query_sub_id = await subscription_manager.subscribe_to_query(```

user_id="user123",
query={```

"department": "engineering",
"priority": "high"
```
},
expires_at=datetime.now() + timedelta(days=30)
```
)
```

### Processing Events

```python
# Process an event
event_data = {```

"resource_id": "post789",
"resource_type": "post",
"action": "update",
"title": "Post Updated",
"message": "A post you're following has been updated",
"data": {```

"title": "New Post Title",
"content": "Updated content..."
```
}
```
}

# Find matching subscriptions and trigger handlers
matching_subscriptions = await subscription_manager.process_event(event_data)

# You can also check number of notifications sent
print(f"Event sent to {len(matching_subscriptions)} subscribers")
```

### Managing Subscriptions

```python
# Get all subscriptions for a user
user_subscriptions = await subscription_manager.get_user_subscriptions(```

user_id="user123",
active_only=True
```
)

# Update subscription status
await subscription_manager.update_subscription_status(```

subscription_id=resource_sub_id,
status=SubscriptionStatus.PAUSED
```
)

# Update subscription expiration
from datetime import datetime, timedelta
await subscription_manager.update_subscription_expiration(```

subscription_id=topic_sub_id,
expires_at=datetime.now() + timedelta(days=90)
```
)

# Delete a subscription
await subscription_manager.delete_subscription(query_sub_id)
```

## Advanced Features

### Custom Authorization Handlers

You can implement custom authorization logic for subscription creation:

```python
async def authorize_resource_subscription(subscription: Subscription) -> bool:```

"""Authorize resource subscriptions."""
# Check if user has permission to subscribe to this resource
from your_app.permissions import has_resource_permission
``````

```
```

if not subscription.resource_id:```

return False
```
    
return await has_resource_permission(```

user_id=subscription.user_id,
resource_id=subscription.resource_id,
permission="subscribe"
```
)
```

# Register the authorization handler
subscription_manager.register_authorization_handler(```

SubscriptionType.RESOURCE,
authorize_resource_subscription
```
)
```

### Subscription Hooks

You can add hooks that run before and after subscription creation:

```python
# Pre-subscription hook for validation
async def validate_subscription(subscription: Subscription) -> bool:```

"""Validate a subscription before creation."""
# Check if subscription is valid
if subscription.type == SubscriptionType.TOPIC:```

valid_topics = ["announcements", "updates", "system"]
if subscription.topic not in valid_topics:
    return False
```
return True
```

# Post-subscription hook for logging
async def log_subscription(subscription: Subscription) -> None:```

"""Log subscription creation."""
logger.info(f"Subscription {subscription.id} created by {subscription.user_id}")
```

# Add the hooks
subscription_manager.add_pre_subscription_hook(validate_subscription)
subscription_manager.add_post_subscription_hook(log_subscription)
```

### Custom Event Handlers

You can implement custom event handlers for special processing:

```python
async def analytics_event_handler(```

event_data: Dict[str, Any],
matching_subscriptions: List[Subscription]
```
) -> None:```

"""Track event delivery for analytics."""
# Log event delivery for analytics
from your_app.analytics import track_event_delivery
``````

```
```

await track_event_delivery(```

event_type=event_data.get("resource_type", "unknown"),
event_id=event_data.get("resource_id", "unknown"),
subscriber_count=len(matching_subscriptions),
subscriber_ids=[sub.user_id for sub in matching_subscriptions]
```
)
```

# Add the event handler
subscription_manager.add_event_handler(analytics_event_handler)
```

### Custom Subscription Store

You can implement a custom subscription store for database persistence:

```python
from uno.realtime.subscriptions import SubscriptionStore, Subscription

class PostgresSubscriptionStore(SubscriptionStore):```

"""PostgreSQL-based subscription store."""
``````

```
```

def __init__(self, db_connection):```

self.db = db_connection
```
``````

```
```

async def save(self, subscription: Subscription) -> str:```

# Implement database save logic
query = """
INSERT INTO subscriptions 
    (id, user_id, type, status, resource_id, resource_type, topic, query, ...)
VALUES 
    ($1, $2, $3, $4, $5, $6, $7, $8, ...)
"""
await self.db.execute(
    query, 
    subscription.id, 
    subscription.user_id, 
    subscription.type.name,
    subscription.status.name,
    subscription.resource_id,
    subscription.resource_type,
    subscription.topic,
    json.dumps(subscription.query or {})
)
return subscription.id
```
``````

```
```

# Implement other required methods
# ...
```

# Create a subscription manager with the custom store
db_connection = await create_database_connection()
store = PostgresSubscriptionStore(db_connection)
subscription_manager = SubscriptionManager(store=store)
```

## Integration with Domain Events

The subscription management system can be integrated with domain events:

```python
from uno.events import EventBus, Event
from uno.realtime.subscriptions import SubscriptionManager

class PostUpdatedEvent(Event):```

"""Event raised when a post is updated."""
``````

```
```

def __init__(self, post_id: str, user_id: str, title: str, content: str):```

super().__init__()
self.post_id = post_id
self.user_id = user_id
self.title = title
self.content = content
```
```

async def post_updated_handler(event: PostUpdatedEvent, subscription_manager: SubscriptionManager):```

"""Handle post updated event."""
# Create event data for subscription system
event_data = {```

"resource_id": event.post_id,
"resource_type": "post",
"action": "update",
"title": "Post Updated",
"message": f"The post '{event.title}' has been updated",
"user_id": event.user_id,
"data": {
    "title": event.title,
    "content": event.content
}
```
}
``````

```
```

# Process the event with the subscription system
await subscription_manager.process_event(event_data)
```

# Register the event handler
event_bus = EventBus()
event_bus.register(PostUpdatedEvent, post_updated_handler, subscription_manager=subscription_manager)
```

## Frontend Integration

### Subscribing to Resources

```javascript
// Function to subscribe to a resource
async function subscribeToResource(resourceId, resourceType) {```

const response = await fetch('/api/subscriptions/resource', {```

method: 'POST',
headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getAuthToken()}`
},
body: JSON.stringify({
    resource_id: resourceId,
    resource_type: resourceType
})
```
});
``````

```
```

if (!response.ok) {```

throw new Error('Failed to subscribe');
```
}
``````

```
```

const result = await response.json();
return result.subscription_id;
```
}

// Usage example
const subscribeButton = document.getElementById('subscribe-button');
subscribeButton.addEventListener('click', async () => {```

try {```

const postId = document.querySelector('[data-post-id]').dataset.postId;
await subscribeToResource(postId, 'post');
``````

```
```

// Update UI to show subscribed state
subscribeButton.textContent = 'Unsubscribe';
subscribeButton.classList.add('subscribed');
``````

```
```

showNotification('Subscription successful', 'You will receive updates for this post');
```
} catch (error) {```

showError('Subscription failed', error.message);
```
}
```
});
```

### Managing User Subscriptions

```javascript
// Function to fetch user subscriptions
async function getUserSubscriptions() {```

const response = await fetch('/api/subscriptions', {```

headers: {
    'Authorization': `Bearer ${getAuthToken()}`
}
```
});
``````

```
```

if (!response.ok) {```

throw new Error('Failed to fetch subscriptions');
```
}
``````

```
```

return await response.json();
```
}

// Function to render subscriptions list
async function renderSubscriptionsList() {```

const subscriptionsContainer = document.getElementById('subscriptions-list');
subscriptionsContainer.innerHTML = '<p>Loading subscriptions...</p>';
``````

```
```

try {```

const subscriptions = await getUserSubscriptions();
``````

```
```

if (subscriptions.length === 0) {
    subscriptionsContainer.innerHTML = '<p>No active subscriptions</p>';
    return;
}
``````

```
```

// Group subscriptions by type
const groupedSubscriptions = {
    'RESOURCE': [],
    'RESOURCE_TYPE': [],
    'TOPIC': [],
    'QUERY': []
};
``````

```
```

subscriptions.forEach(subscription => {
    groupedSubscriptions[subscription.type].push(subscription);
});
``````

```
```

// Render subscriptions by group
subscriptionsContainer.innerHTML = '';
``````

```
```

Object.entries(groupedSubscriptions).forEach(([type, items]) => {
    if (items.length === 0) return;
    
    const section = document.createElement('section');
    section.className = 'subscription-group';
    section.innerHTML = `
        <h3>${formatSubscriptionType(type)}</h3>
        <ul class="subscription-list"></ul>
    `;
    
    const list = section.querySelector('ul');
    
    items.forEach(subscription => {
        const item = document.createElement('li');
        item.className = 'subscription-item';
        item.dataset.id = subscription.id;
        
        // Render based on subscription type
        let label;
        switch (subscription.type) {
            case 'RESOURCE':
                label = `${subscription.resource_type}: ${subscription.resource_id}`;
                break;
            case 'RESOURCE_TYPE':
                label = subscription.resource_type;
                break;
            case 'TOPIC':
                label = subscription.topic;
                break;
            case 'QUERY':
                label = `Query: ${JSON.stringify(subscription.query)}`;
                break;
        }
        
        item.innerHTML = `
            <div class="subscription-info">
                <span class="subscription-label">${label}</span>
                <span class="subscription-status ${subscription.status.toLowerCase()}">${subscription.status}</span>
            </div>
            <div class="subscription-actions">
                <button class="action-pause ${subscription.status === 'PAUSED' ? 'hidden' : ''}">Pause</button>
                <button class="action-resume ${subscription.status !== 'PAUSED' ? 'hidden' : ''}">Resume</button>
                <button class="action-delete">Delete</button>
            </div>
        `;
        
        list.appendChild(item);
    });
    
    subscriptionsContainer.appendChild(section);
});
``````

```
```

// Add event listeners for actions
addSubscriptionActionListeners();
```
    
} catch (error) {```

subscriptionsContainer.innerHTML = `<p class="error">Error loading subscriptions: ${error.message}</p>`;
```
}
```
}

// Format subscription type for display
function formatSubscriptionType(type) {```

const formatMap = {```

'RESOURCE': 'Specific Resources',
'RESOURCE_TYPE': 'Resource Types',
'TOPIC': 'Topics',
'QUERY': 'Custom Queries'
```
};
return formatMap[type] || type;
```
}

// Add event listeners for subscription actions
function addSubscriptionActionListeners() {```

// Pause button
document.querySelectorAll('.action-pause').forEach(button => {```

button.addEventListener('click', async (e) => {
    const item = e.target.closest('.subscription-item');
    const id = item.dataset.id;
    
    try {
        await updateSubscriptionStatus(id, 'PAUSED');
        item.querySelector('.subscription-status').textContent = 'PAUSED';
        item.querySelector('.subscription-status').className = 'subscription-status paused';
        item.querySelector('.action-pause').classList.add('hidden');
        item.querySelector('.action-resume').classList.remove('hidden');
    } catch (error) {
        showError('Failed to pause subscription', error.message);
    }
});
```
});
``````

```
```

// Similar handlers for resume and delete buttons
// ...
```
}
```

## Security Considerations

- **Authentication**: Always authenticate users before allowing subscription creation
- **Authorization**: Implement authorization checks for resource subscriptions
- **Rate Limiting**: Limit the number of subscriptions per user
- **Validation**: Validate subscription parameters, especially for query subscriptions
- **Expiration**: Use expiration dates for temporary subscriptions
- **Permission Checks**: Verify resource access permissions before creating resource subscriptions

## Performance Tips

- Use the in-memory store for development and testing, but implement a database-backed store for production
- Enable periodic cleanup of expired and inactive subscriptions
- Index subscription queries in database implementations
- Use efficient event matching algorithms for query subscriptions
- Consider batching event processing for high-volume events
- Implement caching for frequently accessed subscriptions
- Use separate worker processes for event processing in high-scale systems