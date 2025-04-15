# Notification System

The notification system in uno provides a comprehensive solution for creating, managing, and delivering real-time notifications to users through multiple channels.

## Overview

The notification system consists of several key components:

- **NotificationHub**: Central manager for creating and delivering notifications
- **Notification**: Core data structure representing a notification
- **NotificationStore**: Storage for notifications with query capabilities
- **DeliveryChannel**: Interface for different notification delivery methods

## Key Features

- **Multiple Delivery Channels**: Support for in-app, WebSocket, and SSE delivery
- **Priority Levels**: Five priority levels from LOW to EMERGENCY
- **Rate Limiting**: Intelligent rate limiting to prevent notification flooding
- **Notification Actions**: Support for interactive notification actions
- **Read Status Tracking**: Track read/unread status per user
- **Persistence**: Store notifications for later retrieval
- **Expiration**: Set notification expiration times
- **Delivery Guarantees**: Ensure notifications reach at least one delivery channel

## Basic Usage

### Setting Up the Notification Hub

```python
from uno.realtime.notifications import NotificationHub
from uno.realtime.websocket import WebSocketManager
from uno.realtime.sse import SSEManager
from uno.realtime.notifications import WebSocketNotificationChannel, SSENotificationChannel

# Create the notification hub
notification_hub = NotificationHub()

# Integrate with WebSocket and SSE (optional)
websocket_manager = WebSocketManager()
sse_manager = SSEManager()

# Register additional delivery channels
notification_hub.register_delivery_channel(WebSocketNotificationChannel(websocket_manager))
notification_hub.register_delivery_channel(SSENotificationChannel(sse_manager))
```

### Sending Notifications

```python
# Simple system notification
await notification_hub.notify_system(```

title="System Maintenance",
message="The system will be down for maintenance in 30 minutes.",
recipients=["user123", "user456"],
priority=NotificationPriority.HIGH
```
)

# User-to-user notification
await notification_hub.notify_user(```

title="New Message",
message="You have a new message from John.",
recipients=["user123"],
sender_id="user456",
type_=NotificationType.MESSAGE
```
)

# Resource notification with actions
await notification_hub.notify_resource(```

title="Comment on Your Post",
message="John commented on your post 'Hello World'",
recipients=["user123"],
resource_type="post",
resource_id="post789",
type_=NotificationType.COMMENT,
sender_id="user456",
actions=[```

{
    "label": "View",
    "action": "view_post",
    "data": {"post_id": "post789"}
},
{
    "label": "Reply",
    "action": "reply_comment",
    "data": {"post_id": "post789", "comment_id": "comment123"}
}
```
],
channels={"in_app", "websocket", "sse"}
```
)
```

### Retrieving User Notifications

```python
# Get recent unread notifications
notifications = await notification_hub.get_user_notifications(```

user_id="user123",
limit=10,
include_read=False
```
)

# Get notification count
count = await notification_hub.get_unread_count(user_id="user123")

# Mark notification as read
await notification_hub.mark_as_read(```

notification_id="notif123",
user_id="user123"
```
)

# Mark all notifications as read
await notification_hub.mark_all_as_read(user_id="user123")
```

## Advanced Features

### Custom Delivery Channels

You can create custom delivery channels by implementing the `DeliveryChannel` protocol:

```python
from uno.realtime.notifications import DeliveryChannel

class EmailNotificationChannel(DeliveryChannel):```

"""Email delivery channel for notifications."""
``````

```
```

@property
def channel_id(self) -> str:```

return "email"
```
``````

```
```

async def deliver(self, notification: Notification) -> bool:```

# Implement email delivery logic here
for recipient in notification.recipients:
    email = await get_user_email(recipient)
    if email:
        await send_email(
            to=email,
            subject=notification.title,
            body=notification.message
        )
return True
```
```

# Register the custom channel
notification_hub.register_delivery_channel(EmailNotificationChannel())
```

### Notification Hooks

You can add hooks that run before and after notification delivery:

```python
# Pre-notification hook for filtering
async def sensitive_content_filter(notification: Notification) -> bool:```

# Check if notification contains sensitive content
if contains_sensitive_content(notification.message):```

return False
```
return True
```

# Post-notification hook for logging
async def log_notification(notification: Notification) -> None:```

# Log the notification delivery
logger.info(f"Notification {notification.id} delivered to {len(notification.recipients)} recipients")
```

# Add the hooks
notification_hub.add_pre_notification_hook(sensitive_content_filter)
notification_hub.add_post_notification_hook(log_notification)
```

### Custom Rate Limiting

You can customize the rate limiting behavior:

```python
from uno.realtime.notifications import RateLimiter, NotificationPriority

# Create a custom rate limiter
rate_limiter = RateLimiter(```

max_per_minute={```

NotificationPriority.LOW: 3,
NotificationPriority.NORMAL: 5,
NotificationPriority.HIGH: 10,
NotificationPriority.URGENT: 15,
NotificationPriority.EMERGENCY: 30,
```
},
max_per_hour={```

NotificationPriority.LOW: 10,
NotificationPriority.NORMAL: 20,
NotificationPriority.HIGH: 40,
NotificationPriority.URGENT: 60,
NotificationPriority.EMERGENCY: 120,
```
}
```
)

# Create a notification hub with the custom rate limiter
notification_hub = NotificationHub(rate_limiter=rate_limiter)
```

### Custom Notification Store

You can implement a custom notification store for database persistence:

```python
from uno.realtime.notifications import NotificationStore, Notification

class PostgresNotificationStore(NotificationStore):```

"""PostgreSQL-based notification store."""
``````

```
```

def __init__(self, db_connection):```

self.db = db_connection
```
``````

```
```

async def save(self, notification: Notification) -> str:```

# Implement database save logic
query = """
INSERT INTO notifications 
    (id, title, message, type, priority, recipients, ...)
VALUES 
    ($1, $2, $3, $4, $5, $6, ...)
"""
await self.db.execute(query, notification.id, notification.title, ...)
return notification.id
```
``````

```
```

# Implement other required methods
# ...
```

# Create a notification hub with the custom store
db_connection = await create_database_connection()
store = PostgresNotificationStore(db_connection)
notification_hub = NotificationHub(store=store)
```

## Integration with Domain Events

The notification system can be integrated with domain events:

```python
from uno.events import EventBus, Event
from uno.realtime.notifications import NotificationHub, NotificationPriority, NotificationType

class CommentAddedEvent(Event):```

"""Event raised when a comment is added to a post."""
``````

```
```

def __init__(self, post_id: str, comment_id: str, author_id: str, post_author_id: str):```

super().__init__()
self.post_id = post_id
self.comment_id = comment_id
self.author_id = author_id
self.post_author_id = post_author_id
```
```

async def comment_added_handler(event: CommentAddedEvent, notification_hub: NotificationHub):```

"""Handle comment added event by creating a notification."""
# Get user data
author = await get_user(event.author_id)
post = await get_post(event.post_id)
``````

```
```

# Create notification for post author
await notification_hub.notify_resource(```

title=f"New Comment from {author.name}",
message=f"{author.name} commented on your post '{post.title}'",
recipients=[event.post_author_id],
resource_type="post",
resource_id=event.post_id,
type_=NotificationType.COMMENT,
sender_id=event.author_id,
actions=[
    {
        "label": "View",
        "action": "view_comment",
        "data": {"post_id": event.post_id, "comment_id": event.comment_id}
    },
    {
        "label": "Reply",
        "action": "reply_comment",
        "data": {"post_id": event.post_id, "comment_id": event.comment_id}
    }
]
```
)
```

# Register the event handler
event_bus = EventBus()
event_bus.register(CommentAddedEvent, comment_added_handler, notification_hub=notification_hub)
```

## Frontend Integration

### WebSocket Client

```javascript
// Connect to WebSocket and handle notifications
const socket = new WebSocket('wss://example.com/ws');

socket.addEventListener('message', (event) => {```

const data = JSON.parse(event.data);
``````

```
```

// Handle notification messages
if (data.type === 'NOTIFICATION') {```

const notification = data.payload;
showNotification(```

notification.title,
notification.message,
notification.level,
notification.actions
```
);
```
}
```
});

// Helper function to display notifications
function showNotification(title, message, level, actions) {```

// Create notification UI element
const notificationElement = document.createElement('div');
notificationElement.className = `notification notification-${level}`;
``````

```
```

// Set content
notificationElement.innerHTML = ````

<h3>${title}</h3>
<p>${message}</p>
<div class="notification-actions">
    ${actions.map(action => 
        `<button data-action="${action.action}" 
                 data-action-data='${JSON.stringify(action.data)}'>
            ${action.label}
        </button>`
    ).join('')}
</div>
```
`;
``````

```
```

// Add event listeners for actions
const actionButtons = notificationElement.querySelectorAll('[data-action]');
actionButtons.forEach(button => {```

button.addEventListener('click', (e) => {
    const actionType = button.getAttribute('data-action');
    const actionData = JSON.parse(button.getAttribute('data-action-data') || '{}');
    handleNotificationAction(actionType, actionData);
});
```
});
``````

```
```

// Add to notifications area
document.getElementById('notifications-container').appendChild(notificationElement);
```
}

// Handle notification actions
function handleNotificationAction(actionType, actionData) {```

switch (actionType) {```

case 'view_post':
    window.location.href = `/posts/${actionData.post_id}`;
    break;
case 'reply_comment':
    window.location.href = `/posts/${actionData.post_id}#comment-${actionData.comment_id}`;
    break;
// Handle other action types
```
}
```
}
```

### Server-Sent Events Client

```javascript
// Connect to SSE endpoint
const eventSource = new EventSource('/sse');

// Listen for notification events
eventSource.addEventListener('notification', (event) => {```

const notification = JSON.parse(event.data);
showNotification(```

notification.title,
notification.message,
notification.level,
notification.actions
```
);
```
});

// Use the same showNotification and handleNotificationAction functions
// as in the WebSocket example
```

## Security Considerations

- **Authentication**: Always authenticate users before delivering sensitive notifications
- **User Verification**: Verify that notification recipients are authorized to receive the notification
- **Content Security**: Sanitize notification content to prevent XSS attacks
- **Rate Limiting**: Use rate limiting to prevent abuse and notification spam
- **Sensitive Information**: Avoid including sensitive information in notification content
- **Client-Side Validation**: Always validate notification actions on the server side before processing

## Performance Tips

- Use the in-memory store for transient notifications and a database store for persistent notifications
- Enable periodic cleanup of old notifications to manage storage growth
- Batch related notifications together when possible to reduce notification fatigue
- Use appropriate priority levels to ensure critical notifications are delivered
- Consider the impact of WebSocket broadcasts on server performance for large recipient lists