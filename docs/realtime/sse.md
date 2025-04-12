# Server-Sent Events (SSE)

Server-Sent Events (SSE) is a technology that allows a server to push updates to a client over HTTP connection. It is designed for scenarios where the server needs to send data to the client without the client explicitly requesting it.

## Overview

The Uno framework provides comprehensive support for Server-Sent Events through the `uno.realtime.sse` module. This module includes:

- `SSEConnection`: Manages individual SSE connections
- `SSEManager`: Centralizes SSE connection management and event broadcasting
- `Event`: Defines the structure of SSE events
- Error types and utilities for robust error handling

## Key Features

- **Connection Management**: Track and manage SSE connections with automatic cleanup
- **User Authentication**: Optional authentication with customizable handlers
- **Subscription Support**: Filter events based on subscription topics
- **Priority-based Events**: Ensure important events are delivered with appropriate priority
- **Framework Integration**: Ready-to-use adapters for FastAPI and other frameworks
- **Automatic Keep-alive**: Prevent connection timeouts with configurable keep-alive signals

## Basic Usage

### Setting Up the SSE Manager

```python
from uno.realtime.sse import SSEManager

# Create the SSE manager
sse_manager = SSEManager(
    require_authentication=True,
    keep_alive=True,
    keep_alive_interval=30.0  # seconds
)

# Set up authentication
async def authenticate(auth_data):
    token = auth_data.get("token")
    if token:
        # Validate token and return user_id if valid
        user_id = await validate_token(token)
        if user_id:
            return user_id
    return None

sse_manager.auth_handler = authenticate
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request, Depends
from uno.realtime.sse.manager import sse_endpoint

app = FastAPI()

# Create a global SSE manager
sse_manager = SSEManager(require_authentication=True)

# Define your authentication handler
async def authenticate(auth_data):
    # ... authentication logic ...
    return user_id if valid else None

sse_manager.auth_handler = authenticate

# Create an SSE endpoint
@app.get("/sse")
async def sse(request: Request, subscription: str = None):
    # Extract auth data from request
    auth_data = {"token": request.headers.get("Authorization")}
    
    # Extract client info
    client_info = {"ip": request.client.host}
    
    # Use the helper function to create the SSE endpoint
    return await sse_endpoint(
        sse_manager, 
        request, 
        subscription=subscription,
        auth_data=auth_data,
        client_info=client_info
    )
```

### Broadcasting Events

```python
# Broadcast to all connections
await sse_manager.broadcast_data(
    resource="notifications",
    data={"message": "Server maintenance scheduled"}
)

# Broadcast to specific users
await sse_manager.broadcast_data(
    resource="messages", 
    data={"from": "system", "text": "Private message"},
    user_ids=["user123", "user456"]
)

# Broadcast to specific subscriptions
await sse_manager.broadcast_data(
    resource="chat", 
    data={"room": "general", "message": "New message"},
    subscription_ids=["chat:general"]
)

# Send notifications with different priority levels
await sse_manager.broadcast_notification(
    title="System Update",
    message="The system will be updated in 5 minutes",
    level="warning",
    priority=EventPriority.HIGH
)
```

## Client-Side Integration

### JavaScript Example

```javascript
// Connect to SSE endpoint
function connectSSE(subscription = null) {
    // Build URL with optional subscription
    const url = subscription ? 
        `/sse?subscription=${subscription}` : 
        '/sse';
    
    // Create EventSource
    const eventSource = new EventSource(url);
    
    // Handle connection open
    eventSource.onopen = (event) => {
        console.log('SSE connection established');
    };
    
    // Handle connection error
    eventSource.onerror = (event) => {
        console.error('SSE connection error', event);
        // Automatically try to reconnect
        setTimeout(() => {
            eventSource.close();
            connectSSE(subscription);
        }, 5000);
    };
    
    // Handle default messages
    eventSource.onmessage = (event) => {
        console.log('Received message:', event.data);
        // Parse JSON data if applicable
        try {
            const data = JSON.parse(event.data);
            handleData(data);
        } catch (e) {
            console.log('Received non-JSON message:', event.data);
        }
    };
    
    // Handle typed events
    eventSource.addEventListener('data', (event) => {
        const data = JSON.parse(event.data);
        handleResourceData(data.resource, data.data);
    });
    
    eventSource.addEventListener('notification', (event) => {
        const notification = JSON.parse(event.data);
        showNotification(
            notification.title, 
            notification.message, 
            notification.level
        );
    });
    
    return eventSource;
}

// Usage
const eventSource = connectSSE('updates:dashboard');
```

## Advanced Features

### Custom Event Types

You can create custom event types by extending the `Event` class:

```python
from uno.realtime.sse.event import Event, EventPriority

# Create a custom event type
def create_chat_message_event(room: str, user: str, message: str) -> Event:
    return Event(
        data={
            "room": room,
            "user": user,
            "message": message,
            "timestamp": time.time()
        },
        event="chat_message",  # Custom event type
        priority=EventPriority.NORMAL
    )

# Then broadcast it
await sse_manager.broadcast_event(
    create_chat_message_event("general", "user123", "Hello everyone!"),
    filter_func=lambda conn: conn.has_subscription(f"chat:{room}")
)
```

### Connection Filtering

You can create custom filters for broadcasts:

```python
# Broadcast only to authenticated users who have been connected for >1 minute
one_minute_ago = time.time() - 60

await sse_manager.broadcast_event(
    event,
    filter_func=lambda conn: (
        conn.is_authenticated and 
        conn.client_info.get('connected_at', 0) < one_minute_ago
    )
)
```

### Subscription Patterns

Implement advanced subscription patterns:

```python
# Set up hierarchical subscriptions
user_id = "user123"

# Subscribe to all user events
await sse_manager.add_subscription(client_id, f"user:{user_id}")

# Subscribe to specific event types
await sse_manager.add_subscription(client_id, f"user:{user_id}:messages")
await sse_manager.add_subscription(client_id, f"user:{user_id}:notifications")

# Later, broadcast to specific subscription patterns
await sse_manager.broadcast_data(
    resource="messages",
    data={"id": "msg123", "content": "New message"},
    subscription_ids=[f"user:{user_id}", f"user:{user_id}:messages"]
)
```

## Security Considerations

- **Authentication**: Always authenticate users before allowing sensitive data subscriptions
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Data Validation**: Validate all data before broadcasting to prevent injection attacks
- **Connection Timeouts**: Set appropriate timeouts to prevent resource exhaustion
- **Error Handling**: Handle errors gracefully to prevent information leakage

## Performance Tips

- Use `weakref` dictionaries to prevent memory leaks from disconnected clients
- Implement connection cleanup routines
- Use priority-based event delivery for critical messages
- Consider batching events during high-load situations
- Implement backpressure handling for clients that process events slowly