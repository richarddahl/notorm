# Realtime API

The Realtime module provides comprehensive support for real-time updates via WebSockets, Server-Sent Events (SSE), and a notification system. This document describes the API for interacting with the Realtime module.

## Overview

The Realtime module is built on domain-driven design principles and offers the following key capabilities:

- **Notifications**: Send and manage notifications to users through various channels.
- **Subscriptions**: Allow users to subscribe to resources, topics, or queries for real-time updates.
- **WebSockets**: Real-time bidirectional communication between client and server.
- **Server-Sent Events (SSE)**: Server-to-client streaming for real-time updates.

## Entities

### Notification

A notification represents a message sent to one or more users.

```python
from uno.realtime import Notification, NotificationId, UserId, NotificationType, NotificationPriority

# Create a notification
notification = Notification(
    id=NotificationId("notification-123"),
    title="New message",
    message="You have a new message from Jane",
    recipients=[UserId("user-456")],
    type=NotificationType.MESSAGE,
    priority=NotificationPriority.NORMAL,
    sender_id=UserId("user-789")
)

# Mark as delivered
notification.mark_as_delivered()

# Mark as read by a user
notification.mark_as_read(UserId("user-456"))

# Check if read by a user
is_read = notification.is_read_by(UserId("user-456"))

# Check if expired
is_expired = notification.is_expired()
```

### Subscription

A subscription allows users to receive updates for specific resources, topics, or queries.

```python
from uno.realtime import Subscription, SubscriptionId, UserId, SubscriptionType

# Create a subscription
subscription = Subscription(
    id=SubscriptionId("subscription-123"),
    user_id=UserId("user-456"),
    type=SubscriptionType.RESOURCE,
    resource_id="post-789",
    resource_type="post"
)

# Update status
subscription.update_status(SubscriptionStatus.PAUSED)

# Add label
subscription.add_label("important")

# Check if active
is_active = subscription.is_active()

# Check if matches event
matches = subscription.matches_event({
    "resource_id": "post-789",
    "action": "update"
})
```

### Connection

A connection represents a client connected via WebSocket or SSE.

```python
from uno.realtime import Connection, ConnectionId, UserId, ConnectionState

# Create a connection
connection = Connection(
    id=ConnectionId("connection-123"),
    state=ConnectionState.INITIALIZING
)

# Associate with user
connection.associate_user(UserId("user-456"))

# Update state
connection.update_state(ConnectionState.CONNECTED)

# Add subscription
connection.add_subscription(SubscriptionId("subscription-789"))

# Check if active
is_active = connection.is_active()

# Check if authenticated
is_authenticated = connection.is_authenticated()
```

## Endpoints

The Realtime module exposes RESTful endpoints under the `/api/realtime` prefix, a WebSocket endpoint at `/api/realtime/ws`, and an SSE endpoint at `/api/realtime/events`.

### Notification Endpoints

#### Create Notification

```
POST /api/realtime/notifications
```

Create a new notification for one or more users.

**Request Body**:

```json
{
  "title": "New message",
  "message": "You have a new message from Jane",
  "recipients": ["user-456", "user-789"],
  "type": "message",
  "priority": "normal",
  "sender_id": "user-123",
  "resource_type": "message",
  "resource_id": "message-789",
  "actions": [
    {
      "label": "View",
      "action": "view",
      "data": { "id": "message-789" }
    },
    {
      "label": "Reply",
      "action": "reply",
      "data": { "id": "message-789" }
    }
  ],
  "metadata": {
    "thread_id": "thread-123"
  },
  "expires_at": "2025-05-16T10:30:00Z"
}
```

**Response** (201 Created):

```json
{
  "id": "notification-123",
  "title": "New message",
  "message": "You have a new message from Jane",
  "type": "message",
  "priority": "normal",
  "status": "delivered",
  "recipients": ["user-456", "user-789"],
  "sender_id": "user-123",
  "created_at": "2025-04-16T10:30:00Z",
  "delivered_at": "2025-04-16T10:30:01Z",
  "read_by": [],
  "actions": [
    {
      "label": "View",
      "action": "view",
      "data": { "id": "message-789" }
    },
    {
      "label": "Reply",
      "action": "reply",
      "data": { "id": "message-789" }
    }
  ],
  "resource_type": "message",
  "resource_id": "message-789",
  "metadata": {
    "thread_id": "thread-123"
  }
}
```

#### Get User Notifications

```
GET /api/realtime/notifications?user_id=user-456&status=pending&page=1&page_size=20
```

Get notifications for a specific user.

**Query Parameters**:

- `user_id`: User ID
- `status`: Optional notification status filter
- `page`: Page number (default: 1)
- `page_size`: Page size (default: 20)

**Response** (200 OK):

```json
[
  {
    "id": "notification-123",
    "title": "New message",
    "message": "You have a new message from Jane",
    "type": "message",
    "priority": "normal",
    "status": "delivered",
    "recipients": ["user-456", "user-789"],
    "sender_id": "user-123",
    "created_at": "2025-04-16T10:30:00Z",
    "delivered_at": "2025-04-16T10:30:01Z",
    "read_by": [],
    "actions": [
      {
        "label": "View",
        "action": "view",
        "data": { "id": "message-789" }
      },
      {
        "label": "Reply",
        "action": "reply",
        "data": { "id": "message-789" }
      }
    ],
    "resource_type": "message",
    "resource_id": "message-789",
    "metadata": {
      "thread_id": "thread-123"
    }
  }
  // More notifications...
]
```

#### Get Notification

```
GET /api/realtime/notifications/{notification_id}
```

Get a specific notification by ID.

**Path Parameters**:

- `notification_id`: Notification ID

**Response** (200 OK):

```json
{
  "id": "notification-123",
  "title": "New message",
  "message": "You have a new message from Jane",
  "type": "message",
  "priority": "normal",
  "status": "delivered",
  "recipients": ["user-456", "user-789"],
  "sender_id": "user-123",
  "created_at": "2025-04-16T10:30:00Z",
  "delivered_at": "2025-04-16T10:30:01Z",
  "read_by": [],
  "actions": [
    {
      "label": "View",
      "action": "view",
      "data": { "id": "message-789" }
    },
    {
      "label": "Reply",
      "action": "reply",
      "data": { "id": "message-789" }
    }
  ],
  "resource_type": "message",
  "resource_id": "message-789",
  "metadata": {
    "thread_id": "thread-123"
  }
}
```

#### Mark Notification as Read

```
POST /api/realtime/notifications/{notification_id}/mark-read?user_id=user-456
```

Mark a notification as read by a specific user.

**Path Parameters**:

- `notification_id`: Notification ID

**Query Parameters**:

- `user_id`: User ID

**Response** (200 OK):

```json
{
  "id": "notification-123",
  "title": "New message",
  "message": "You have a new message from Jane",
  "type": "message",
  "priority": "normal",
  "status": "delivered",
  "recipients": ["user-456", "user-789"],
  "sender_id": "user-123",
  "created_at": "2025-04-16T10:30:00Z",
  "delivered_at": "2025-04-16T10:30:01Z",
  "read_by": ["user-456"],
  "actions": [
    {
      "label": "View",
      "action": "view",
      "data": { "id": "message-789" }
    },
    {
      "label": "Reply",
      "action": "reply",
      "data": { "id": "message-789" }
    }
  ],
  "resource_type": "message",
  "resource_id": "message-789",
  "metadata": {
    "thread_id": "thread-123"
  }
}
```

#### Get Unread Count

```
GET /api/realtime/notifications/unread-count/{user_id}
```

Get the count of unread notifications for a user.

**Path Parameters**:

- `user_id`: User ID

**Response** (200 OK):

```json
5
```

### Subscription Endpoints

#### Create Resource Subscription

```
POST /api/realtime/subscriptions/resource
```

Create a new subscription to a specific resource.

**Request Body**:

```json
{
  "user_id": "user-456",
  "resource_id": "post-789",
  "resource_type": "post",
  "labels": ["important", "post-updates"],
  "metadata": {
    "notification_channel": "email"
  },
  "expires_at": "2025-05-16T10:30:00Z"
}
```

**Response** (201 Created):

```json
{
  "id": "subscription-123",
  "user_id": "user-456",
  "type": "resource",
  "status": "active",
  "created_at": "2025-04-16T10:30:00Z",
  "updated_at": "2025-04-16T10:30:00Z",
  "expires_at": "2025-05-16T10:30:00Z",
  "resource_id": "post-789",
  "resource_type": "post",
  "topic": null,
  "query": null,
  "labels": ["important", "post-updates"],
  "metadata": {
    "notification_channel": "email"
  }
}
```

#### Create Topic Subscription

```
POST /api/realtime/subscriptions/topic
```

Create a new subscription to a topic.

**Request Body**:

```json
{
  "user_id": "user-456",
  "topic": "new-posts",
  "labels": ["news", "updates"],
  "metadata": {
    "notification_channel": "in-app"
  },
  "expires_at": "2025-05-16T10:30:00Z",
  "payload_filter": {
    "category": "tech"
  }
}
```

**Response** (201 Created):

```json
{
  "id": "subscription-123",
  "user_id": "user-456",
  "type": "topic",
  "status": "active",
  "created_at": "2025-04-16T10:30:00Z",
  "updated_at": "2025-04-16T10:30:00Z",
  "expires_at": "2025-05-16T10:30:00Z",
  "resource_id": null,
  "resource_type": null,
  "topic": "new-posts",
  "query": null,
  "labels": ["news", "updates"],
  "metadata": {
    "notification_channel": "in-app"
  }
}
```

#### Get User Subscriptions

```
GET /api/realtime/subscriptions?user_id=user-456&status=active&page=1&page_size=20
```

Get subscriptions for a specific user.

**Query Parameters**:

- `user_id`: User ID
- `status`: Optional subscription status filter
- `page`: Page number (default: 1)
- `page_size`: Page size (default: 20)

**Response** (200 OK):

```json
[
  {
    "id": "subscription-123",
    "user_id": "user-456",
    "type": "resource",
    "status": "active",
    "created_at": "2025-04-16T10:30:00Z",
    "updated_at": "2025-04-16T10:30:00Z",
    "expires_at": "2025-05-16T10:30:00Z",
    "resource_id": "post-789",
    "resource_type": "post",
    "topic": null,
    "query": null,
    "labels": ["important", "post-updates"],
    "metadata": {
      "notification_channel": "email"
    }
  },
  {
    "id": "subscription-124",
    "user_id": "user-456",
    "type": "topic",
    "status": "active",
    "created_at": "2025-04-16T10:30:00Z",
    "updated_at": "2025-04-16T10:30:00Z",
    "expires_at": "2025-05-16T10:30:00Z",
    "resource_id": null,
    "resource_type": null,
    "topic": "new-posts",
    "query": null,
    "labels": ["news", "updates"],
    "metadata": {
      "notification_channel": "in-app"
    }
  }
  // More subscriptions...
]
```

#### Get Subscription

```
GET /api/realtime/subscriptions/{subscription_id}
```

Get a specific subscription by ID.

**Path Parameters**:

- `subscription_id`: Subscription ID

**Response** (200 OK):

```json
{
  "id": "subscription-123",
  "user_id": "user-456",
  "type": "resource",
  "status": "active",
  "created_at": "2025-04-16T10:30:00Z",
  "updated_at": "2025-04-16T10:30:00Z",
  "expires_at": "2025-05-16T10:30:00Z",
  "resource_id": "post-789",
  "resource_type": "post",
  "topic": null,
  "query": null,
  "labels": ["important", "post-updates"],
  "metadata": {
    "notification_channel": "email"
  }
}
```

#### Update Subscription Status

```
PATCH /api/realtime/subscriptions/{subscription_id}/status
```

Update the status of a subscription.

**Path Parameters**:

- `subscription_id`: Subscription ID

**Request Body**:

```json
{
  "status": "paused"
}
```

**Response** (200 OK):

```json
{
  "id": "subscription-123",
  "user_id": "user-456",
  "type": "resource",
  "status": "paused",
  "created_at": "2025-04-16T10:30:00Z",
  "updated_at": "2025-04-16T10:31:00Z",
  "expires_at": "2025-05-16T10:30:00Z",
  "resource_id": "post-789",
  "resource_type": "post",
  "topic": null,
  "query": null,
  "labels": ["important", "post-updates"],
  "metadata": {
    "notification_channel": "email"
  }
}
```

#### Delete Subscription

```
DELETE /api/realtime/subscriptions/{subscription_id}
```

Delete a subscription.

**Path Parameters**:

- `subscription_id`: Subscription ID

**Response** (204 No Content)

### WebSocket Endpoint

The WebSocket endpoint allows for real-time bidirectional communication between client and server.

```
WebSocket: /api/realtime/ws
```

#### Connection Establishment

1. Client connects to the WebSocket endpoint
2. Server accepts the connection and creates a `Connection` entity
3. Server sends a connection message with the connection ID:

```json
{
  "type": "connection",
  "connection_id": "connection-123"
}
```

#### Message Protocol

**Client to Server**:

```json
{
  "type": "message",
  "payload": "Hello, server!"
}
```

**Server to Client**:

```json
{
  "type": "message",
  "payload": "Hello, client!",
  "id": "message-123"
}
```

#### Notification Message

When a notification is sent to a user, all their WebSocket connections receive a notification message:

```json
{
  "type": "notification",
  "payload": {
    "id": "notification-123",
    "title": "New message",
    "message": "You have a new message from Jane",
    "type": "message",
    "priority": "normal",
    "created_at": "2025-04-16T10:30:00Z",
    "sender_id": "user-123",
    "actions": [
      {
        "label": "View",
        "action": "view",
        "data": { "id": "message-789" }
      },
      {
        "label": "Reply",
        "action": "reply",
        "data": { "id": "message-789" }
      }
    ]
  }
}
```

### Server-Sent Events (SSE) Endpoint

The SSE endpoint allows for real-time server-to-client streaming.

```
GET /api/realtime/events
```

**Example SSE Stream**:

```
event: connection
id: event-123
data: {"connection_id":"connection-123"}

event: ping
id: event-124
data: {"timestamp":"2025-04-16T10:30:00Z"}

event: notification
id: event-125
data: {"id":"notification-123","title":"New message","message":"You have a new message from Jane"}
```

#### Create Event

```
POST /api/realtime/events
```

Create a new SSE event.

**Request Body**:

```json
{
  "event": "update",
  "data": "{\"resource_id\":\"post-789\",\"action\":\"update\"}",
  "priority": "normal",
  "retry": 3000,
  "comment": "Resource update event"
}
```

**Response** (201 Created):

```json
{
  "id": "event-123",
  "event": "update",
  "data": "{\"resource_id\":\"post-789\",\"action\":\"update\"}",
  "priority": "normal",
  "retry": 3000,
  "comment": "Resource update event"
}
```

#### Broadcast Event

```
POST /api/realtime/events/broadcast
```

Broadcast an SSE event to multiple connections.

**Request Body**:

```json
{
  "event": "update",
  "data": "{\"resource_id\":\"post-789\",\"action\":\"update\"}",
  "priority": "normal",
  "recipients": ["connection-123", "connection-456"],
  "exclude": ["connection-789"]
}
```

**Response** (200 OK):

```json
2
```

## Using the Realtime Module Programmatically

### Configuring Dependencies

```python
from uno.dependencies.container import configure_container
from uno.realtime import configure_realtime_dependencies

# Configure realtime dependencies
configure_container(configure_realtime_dependencies)
```

### Notifications

```python
import inject
from uno.realtime import (
    NotificationServiceProtocol,
    UserId,
    NotificationType,
    NotificationPriority
)

# Get notification service
notification_service = inject.instance(NotificationServiceProtocol)

# Create a notification
result = await notification_service.create_notification(
    title="New message",
    message="You have a new message from Jane",
    recipients=[UserId("user-456"), UserId("user-789")],
    type_=NotificationType.MESSAGE,
    priority=NotificationPriority.NORMAL,
    sender_id=UserId("user-123"),
    resource_type="message",
    resource_id="message-789",
    actions=[
        {
            "label": "View",
            "action": "view",
            "data": {"id": "message-789"}
        },
        {
            "label": "Reply",
            "action": "reply",
            "data": {"id": "message-789"}
        }
    ]
)

if result.is_success():
    notification = result.value
    print(f"Created notification with ID {notification.id.value}")
else:
    print(f"Error: {result.error}")
```

### Subscriptions

```python
import inject
from uno.realtime import (
    SubscriptionServiceProtocol,
    UserId
)

# Get subscription service
subscription_service = inject.instance(SubscriptionServiceProtocol)

# Create a resource subscription
result = await subscription_service.create_resource_subscription(
    user_id=UserId("user-456"),
    resource_id="post-789",
    resource_type="post",
    labels={"important", "post-updates"},
    metadata={"notification_channel": "email"}
)

if result.is_success():
    subscription = result.value
    print(f"Created subscription with ID {subscription.id.value}")
else:
    print(f"Error: {result.error}")
```

### WebSockets

```python
import inject
from uno.realtime import (
    WebSocketServiceProtocol,
    ConnectionId,
    MessageType
)

# Get WebSocket service
websocket_service = inject.instance(WebSocketServiceProtocol)

# Send a message to a connection
result = await websocket_service.send_message(
    connection_id=ConnectionId("connection-123"),
    message_type=MessageType.TEXT,
    payload="Hello, client!"
)

if result.is_success():
    print("Message sent successfully")
else:
    print(f"Error: {result.error}")

# Broadcast a message
result = await websocket_service.broadcast_message(
    message_type=MessageType.SYSTEM,
    payload={"type": "system", "message": "Server maintenance in 5 minutes"}
)

if result.is_success():
    print(f"Message broadcast to {result.value} connections")
else:
    print(f"Error: {result.error}")
```

### Server-Sent Events (SSE)

```python
import inject
from uno.realtime import (
    SSEServiceProtocol,
    ConnectionId,
    EventPriority
)

# Get SSE service
sse_service = inject.instance(SSEServiceProtocol)

# Create an event
event_result = await sse_service.create_event(
    event_type="update",
    data='{"resource_id":"post-789","action":"update"}',
    priority=EventPriority.NORMAL
)

if event_result.is_success():
    event = event_result.value
    
    # Send to a connection
    result = await sse_service.send_event(
        connection_id=ConnectionId("connection-123"),
        event=event
    )
    
    if result.is_success():
        print("Event sent successfully")
    else:
        print(f"Error: {result.error}")
else:
    print(f"Error creating event: {event_result.error}")
```

## Integration with Domain-Driven Design

The Realtime module is built using domain-driven design principles:

1. **Entities**: Core domain objects like `Notification`, `Subscription`, `Connection`, `Message`, and `Event`.
2. **Value Objects**: Immutable objects like `NotificationId`, `SubscriptionId`, `ConnectionId`, and `UserId`.
3. **Repositories**: Data access interfaces with implementations for each entity.
4. **Domain Services**: Business logic in services like `NotificationService`, `SubscriptionService`, `ConnectionService`, `WebSocketService`, and `SSEService`.
5. **Application Services**: Coordinating services like `RealtimeService` that orchestrate domain services.

## Best Practices

When using the Realtime module, follow these best practices:

1. **Use subscriptions for fine-grained control**: Instead of broadcasting all events to all users, use the subscription system to determine who should receive what updates.
2. **Be mindful of connection resources**: WebSocket and SSE connections consume server resources. Implement proper connection management and cleanup.
3. **Handle connection failures gracefully**: Clients should implement reconnection strategies for WebSocket and SSE connections.
4. **Structure event data consistently**: Use consistent data formats for events to make client-side handling simpler.
5. **Consider message delivery guarantees**: For critical updates, consider combining real-time delivery with persistent notifications.
6. **Monitor connection metrics**: Track the number of active connections, message throughput, and error rates.
7. **Implement rate limiting**: Protect against abuse by implementing rate limits for connections and message sending.
8. **Use HTTPS in production**: Always use HTTPS for WebSocket and SSE connections in production environments.

## Error Handling

All services in the Realtime module use the Result pattern for error handling. This means that instead of throwing exceptions, they return a `Result` object that can be either successful or contain an error message.

```python
from uno.core.result import Result

# Example of checking a result
result = await notification_service.create_notification(...)

if result.is_success():
    # Success case
    notification = result.value
    print(f"Created notification with ID {notification.id.value}")
else:
    # Error case
    error_message = result.error
    logger.error(f"Failed to create notification: {error_message}")
```

This pattern allows for more robust error handling and better separation of concerns.

## Further Reading

- [Realtime Communication Overview](../realtime/overview.md)
- [WebSocket Protocol Guide](../realtime/websocket.md)
- [Server-Sent Events Guide](../realtime/sse.md)
- [Notification System Deep Dive](../realtime/notifications.md)
- [Subscription System Guide](../realtime/subscriptions.md)