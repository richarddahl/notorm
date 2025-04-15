# WebSocket Implementation

The uno framework provides a robust WebSocket implementation for bidirectional real-time communication between server and clients. This document covers how to use and configure the WebSocket system.

## Architecture

The WebSocket implementation in uno is built with a layered architecture:

1. **WebSocketManager**: Central manager that handles connections, message routing, and broadcasting
2. **WebSocketConnection**: Represents a single client connection with its lifecycle
3. **WebSocketProtocol**: Defines the business logic for message handling
4. **Message**: Structured message format with type-based handling

```
┌─────────────────────┐     ┌─────────────────────┐
│  Web Framework      │     │  Authentication     │
│  Integration        ├─────┤  System             │
└─────────┬───────────┘     └─────────────────────┘```
```

  │                             ▲
  ▼                             │
```
```
┌─────────────────────┐                 │
│  WebSocketManager   │─────────────────┘
└─────────┬───────────┘```
```

  │
  ▼
```
```
┌─────────────────────┐
│  WebSocketConnection│◄──┐
└─────────┬───────────┘   │```
```

  │               │
  ▼               │
```
```
┌─────────────────────┐   │
│  WebSocketProtocol  │   │
└─────────┬───────────┘   │```
```

  │               │
  ▼               │
```
```
┌─────────────────────┐   │
│  Message Handlers   │───┘
└─────────────────────┘
```

## WebSocket Manager

The `WebSocketManager` is the main entry point for working with WebSockets. It provides methods for:

- Managing connections
- Broadcasting messages
- User and subscription targeting

### Creating a WebSocket Manager

```python
from uno.realtime.websocket import WebSocketManager

# Create a basic WebSocket manager
ws_manager = WebSocketManager(```

require_authentication=True,
auto_ping=True,
ping_interval=30.0,
```
)

# Add an authentication handler
async def authenticate_user(auth_data, connection):```

# Process auth_data and return user_id if valid, None otherwise
token = auth_data.get("token")
user = await verify_token(token)
if user:```

return user.id
```
return None
```

ws_manager = WebSocketManager(```

require_authentication=True,
auth_handler=authenticate_user
```
)
```

### Handling WebSocket Connections

To handle a new WebSocket connection, use the `handle_connection` method:

```python
# Using with a FastAPI WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):```

await websocket.accept()
``````

```
```

# Create a WebSocketSender adapter for the FastAPI WebSocket
class FastAPIWebSocketSender:```

async def send_text(self, data: str) -> None:
    await websocket.send_text(data)
``````

```
```

async def send_bytes(self, data: bytes) -> None:
    await websocket.send_bytes(data)
``````

```
```

async def close(self, code: int = 1000, reason: str = "") -> None:
    await websocket.close(code=code, reason=reason)
```
``````

```
```

# Handle the connection
await ws_manager.handle_connection(```

socket=FastAPIWebSocketSender(),
client_info={"user_agent": websocket.headers.get("user-agent")}
```
)
```
```

### Broadcasting Messages

The WebSocket manager provides several methods for sending messages:

```python
# Create a message
from uno.realtime.websocket import Message, MessageType
message = Message(```

type=MessageType.DATA,
payload={"resource": "user", "data": {"id": 1, "name": "John"}}
```
)

# Broadcast to all connected clients
await ws_manager.broadcast(message)

# Broadcast to specific users
await ws_manager.broadcast_to_users(message, user_ids=["user1", "user2"])

# Broadcast to connections with a specific subscription
await ws_manager.broadcast_to_subscription(message, subscription="user:1:updates")

# Send to a specific client
await ws_manager.send_to_client("client123", message)
```

### Connection Lifecycle Hooks

You can add handlers for connection lifecycle events:

```python
# Handle new connections
async def on_connect(connection):```

print(f"New connection: {connection.client_id}")
# Possibly add the connection to a room or channel
```
    
ws_manager.add_on_connect_handler(on_connect)

# Handle disconnections
async def on_disconnect(connection, code, reason):```

print(f"Connection closed: {connection.client_id}, code: {code}, reason: {reason}")
```
    
ws_manager.add_on_disconnect_handler(on_disconnect)

# Handle errors
async def on_error(connection, error):```

print(f"Connection error: {connection.client_id}, error: {error}")
```
    
ws_manager.add_on_error_handler(on_error)
```

## WebSocket Connection

The `WebSocketConnection` class represents a single WebSocket connection. It manages:

- Connection lifecycle (connect, authenticate, disconnect)
- Message sending and receiving
- Subscription management
- Ping/pong for connection health

### Connection States

A connection can be in one of these states:

- `INITIALIZING`: Connection is being set up
- `CONNECTING`: Connection is being established
- `CONNECTED`: Connection is established
- `AUTHENTICATING`: Client is being authenticated
- `AUTHENTICATED`: Client is authenticated
- `DISCONNECTING`: Connection is being closed gracefully
- `DISCONNECTED`: Connection is closed
- `ERROR`: Connection is in error state

### Adding Message Handlers

You can add handlers for specific message types:

```python
async def handle_action(message, connection):```

action = message.payload.get("action")
if action == "echo":```

# Echo the message back
response = message.create_response(
    MessageType.ACTION_RESULT,
    payload={"result": message.payload.get("data")}
)
await connection.send_message(response)
```
```

# Add the handler for ACTION messages
connection.add_message_handler(MessageType.ACTION, handle_action)
```

## Message Types and Format

The WebSocket implementation uses a structured message format with specific types:

```json
{
  "type": "DATA",
  "payload": {```

"resource": "user",
"data": {"id": 1, "name": "John"}
```
  },
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1619712345.123
}
```

### Standard Message Types

- **Connection lifecycle**: `CONNECT`, `CONNECT_ACK`, `DISCONNECT`
- **Authentication**: `AUTHENTICATE`, `AUTHENTICATE_SUCCESS`, `AUTHENTICATE_FAILURE`
- **Subscriptions**: `SUBSCRIBE`, `SUBSCRIBE_SUCCESS`, `SUBSCRIBE_FAILURE`, `UNSUBSCRIBE`, `UNSUBSCRIBE_ACK`
- **Data events**: `EVENT`, `DATA`, `NOTIFICATION`
- **Actions**: `ACTION`, `ACTION_RESULT`
- **System messages**: `PING`, `PONG`, `ERROR`

### Message Helpers

The framework provides helpers for creating common messages:

```python
from uno.realtime.websocket.message import (```

create_event_message,
create_data_message,
create_notification_message,
create_ping_message,
create_pong_message
```
)

# Create an event message
event_msg = create_event_message(```

event_type="user.updated",
data={"id": 1, "name": "John"}
```
)

# Create a data message
data_msg = create_data_message(```

resource="user",
data={"id": 1, "name": "John"}
```
)

# Create a notification message
notification_msg = create_notification_message(```

title="New message",
message="You have a new message from John",
level="info",
actions=[```

{"label": "View", "action": "view_message", "id": "msg123"}
```
]
```
)
```

## Custom Protocols

You can implement custom WebSocket protocols by subclassing `WebSocketProtocol`:

```python
from uno.realtime.websocket import WebSocketProtocol, WebSocketConnection, Message

class CustomProtocol(WebSocketProtocol):```

async def handle_connection_established(self, connection: WebSocketConnection) -> None:```

# Register message handlers
connection.add_message_handler(MessageType.ACTION, self._handle_action)
``````

```
```

# Custom welcome message
welcome_msg = Message(
    type=MessageType.EVENT,
    payload={"event": "welcome", "message": "Welcome to the server!"}
)
await connection.send_message(welcome_msg)
```
``````

```
```

async def handle_message(self, message: Message, connection: WebSocketConnection) -> None:```

# Custom message handling
pass
```
``````

```
```

async def handle_connection_closed(self, connection: WebSocketConnection, code: int, reason: str) -> None:```

# Custom disconnect handling
pass
```
``````

```
```

async def handle_error(self, connection: WebSocketConnection, error: WebSocketError) -> None:```

# Custom error handling
pass
```
``````

```
```

async def _handle_action(self, message: Message, connection: WebSocketConnection) -> None:```

# Handle action messages
pass
```
```

# Use the custom protocol with the manager
ws_manager = WebSocketManager(protocol=CustomProtocol())
```

## Security Considerations

### Authentication

The WebSocket implementation supports authentication through the `auth_handler` callback. This allows you to integrate with your existing authentication system.

```python
async def authenticate_user(auth_data, connection):```

# Verify JWT token
token = auth_data.get("token")
try:```

payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
user_id = payload.get("sub")
return user_id
```
except jwt.InvalidTokenError:```

return None
```
```

ws_manager = WebSocketManager(```

require_authentication=True,
auth_handler=authenticate_user
```
)
```

### Rate Limiting

To protect against abuse, consider implementing rate limiting for connections and messages:

```python
# Add middleware for connection rate limiting
from uno.core.rate_limiter import RateLimiter

connection_limiter = RateLimiter(```

operations_per_second=5,  # 5 connections per second
window_size=60,  # Over a 60 second window
```
)

async def limit_connections(websocket):```

client_ip = websocket.client.host
if not await connection_limiter.check(client_ip):```

await websocket.close(code=1008, reason="Rate limit exceeded")
return False
```
return True
```
```

### Message Size Limits

The WebSocket manager has a configurable maximum message size:

```python
ws_manager = WebSocketManager(```

max_message_size=1024 * 50,  # 50 KB maximum message size
```
)
```

## Client-Side Implementation

Here's a simple example of a client-side implementation using JavaScript:

```javascript
class UnoWebSocket {
  constructor(url) {```

this.url = url;
this.socket = null;
this.handlers = {};
this.connected = false;
this.authenticated = false;
this.reconnectAttempts = 0;
this.maxReconnectAttempts = 5;
this.reconnectDelay = 1000; // Start with 1 second
```
  }

  connect() {```

this.socket = new WebSocket(this.url);
``````

```
```

this.socket.onopen = () => {
  console.log('WebSocket connected');
  this.connected = true;
  this.reconnectAttempts = 0;
  // Send connect message
  this.send({```

type: 'CONNECT',
payload: {}
```
  });
};
``````

```
```

this.socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Message received:', message);
  
  // Handle specific message types
  if (message.type === 'CONNECT_ACK') {```

if (message.payload.requires_auth) {
  this.authenticate();
}
```
  } else if (message.type === 'AUTHENTICATE_SUCCESS') {```

this.authenticated = true;
this.triggerHandler('authenticated', message.payload);
```
  } else if (message.type === 'PING') {```

// Respond with pong
this.send({
  type: 'PONG',
  correlation_id: message.id
});
```
  }
  
  // Trigger message type handlers
  this.triggerHandler(message.type, message);
  
  // Trigger any handlers for specific correlation_id
  if (message.correlation_id) {```

this.triggerHandler(`response:${message.correlation_id}`, message);
```
  }
};
``````

```
```

this.socket.onclose = (event) => {
  console.log('WebSocket closed:', event.code, event.reason);
  this.connected = false;
  this.authenticated = false;
  this.triggerHandler('close', { code: event.code, reason: event.reason });
  
  // Try to reconnect if appropriate
  if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {```

setTimeout(() => {
  this.reconnectAttempts++;
  this.connect();
}, this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1));
```
  }
};
``````

```
```

this.socket.onerror = (error) => {
  console.error('WebSocket error:', error);
  this.triggerHandler('error', error);
};
``````

```
```

return this;
```
  }
  
  authenticate(authData = {}) {```

// Send authentication message
return this.send({
  type: 'AUTHENTICATE',
  payload: {```

auth: {
  token: localStorage.getItem('token'),
  ...authData
}
```
  }
});
```
  }
  
  subscribe(subscriptions) {```

if (!Array.isArray(subscriptions)) {
  subscriptions = [subscriptions];
}
``````

```
```

return this.send({
  type: 'SUBSCRIBE',
  payload: {```

subscriptions
```
  }
});
```
  }
  
  unsubscribe(subscriptions) {```

if (!Array.isArray(subscriptions)) {
  subscriptions = [subscriptions];
}
``````

```
```

return this.send({
  type: 'UNSUBSCRIBE',
  payload: {```

subscriptions
```
  }
});
```
  }
  
  send(message) {```

if (!this.connected) {
  throw new Error('WebSocket not connected');
}
``````

```
```

// Generate id if not provided
if (!message.id) {
  message.id = this.generateId();
}
``````

```
```

// Add timestamp if not provided
if (!message.timestamp) {
  message.timestamp = Date.now() / 1000;
}
``````

```
```

const messageJson = JSON.stringify(message);
this.socket.send(messageJson);
``````

```
```

return message.id;
```
  }
  
  generateId() {```

return 'xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
  const r = Math.random() * 16 | 0;
  const v = c === 'x' ? r : (r & 0x3 | 0x8);
  return v.toString(16);
});
```
  }
  
  on(event, handler) {```

if (!this.handlers[event]) {
  this.handlers[event] = [];
}
this.handlers[event].push(handler);```
```

return this;
```
  }
  
  off(event, handler) {```

if (this.handlers[event]) {
  if (handler) {
    this.handlers[event] = this.handlers[event].filter(h => h !== handler);
  } else {
    delete this.handlers[event];
  }
}```
```

return this;
```
  }
  
  triggerHandler(event, data) {```

if (this.handlers[event]) {
  this.handlers[event].forEach(handler => {```

try {
  handler(data);
} catch (e) {
  console.error(`Error in handler for ${event}:`, e);
}
```
  });
}
```
  }
  
  close(code = 1000, reason = '') {```

if (this.socket) {
  // Send disconnect message before closing
  try {```

this.send({
  type: 'DISCONNECT',
  payload: { code, reason }
});
```
  } catch (e) {```

// Ignore errors when sending disconnect
```
  }
  
  // Close the socket
  this.socket.close(code, reason);
}
```
  }
}

// Usage example
const ws = new UnoWebSocket('wss://example.com/ws');

ws.on('authenticated', (data) => {
  console.log('Authenticated as:', data.user_id);
  // Subscribe to events
  ws.subscribe(['user:1:updates', 'notifications']);
});

ws.on('DATA', (message) => {
  console.log('Data received:', message.payload.data);
});

ws.on('NOTIFICATION', (message) => {
  showNotification(message.payload.title, message.payload.message);
});

// Connect to the server
ws.connect();
```

## Integration with Frameworks

### FastAPI Integration

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uno.realtime.websocket import WebSocketManager, WebSocketSender

app = FastAPI()
security = HTTPBearer()
ws_manager = WebSocketManager(require_authentication=True)

# WebSocket adapter for FastAPI
class FastAPIWebSocketSender(WebSocketSender):```

def __init__(self, websocket: WebSocket):```

self.websocket = websocket
```
``````

```
```

async def send_text(self, data: str) -> None:```

await self.websocket.send_text(data)
```
``````

```
```

async def send_bytes(self, data: bytes) -> None:```

await self.websocket.send_bytes(data)
```
``````

```
```

async def close(self, code: int = 1000, reason: str = "") -> None:```

await self.websocket.close(code=code, reason=reason)
```
```

# Authentication handler for WebSockets
async def authenticate_websocket(auth_data, connection):```

token = auth_data.get("token")
if not token:```

return None
```
``````

```
```

# Verify token
try:
    user = await verify_token(token)```

return user.id
```
except:```

return None
```
```

# Configure WebSocket manager
ws_manager.auth_handler = authenticate_websocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):```

await websocket.accept()
``````

```
```

# Create sender adapter
sender = FastAPIWebSocketSender(websocket)
``````

```
```

# Handle WebSocket connection
await ws_manager.handle_connection(```

socket=sender,
client_info={
    "user_agent": websocket.headers.get("user-agent"),
    "ip": websocket.client.host
}
```
)
```

# API endpoint to send a notification to a user
@app.post("/users/{user_id}/notify")
async def notify_user(```

user_id: str,
notification: dict,
credentials: HTTPAuthorizationCredentials = Depends(security)
```
):```

# Create notification message
message = create_notification_message(```

title=notification["title"],
message=notification["message"],
level=notification.get("level", "info")
```
)
``````

```
```

# Send to user's connections
await ws_manager.broadcast_to_users(message, [user_id])
``````

```
```

return {"status": "sent"}
```
```

### Starlette Integration

```python
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket
from uno.realtime.websocket import WebSocketManager, WebSocketSender

ws_manager = WebSocketManager(require_authentication=False)

# WebSocket adapter for Starlette
class StarletteWebSocketSender(WebSocketSender):```

def __init__(self, websocket: WebSocket):```

self.websocket = websocket
```
``````

```
```

async def send_text(self, data: str) -> None:```

await self.websocket.send_text(data)
```
``````

```
```

async def send_bytes(self, data: bytes) -> None:```

await self.websocket.send_bytes(data)
```
``````

```
```

async def close(self, code: int = 1000, reason: str = "") -> None:```

await self.websocket.close(code=code, reason=reason)
```
```

async def websocket_endpoint(websocket: WebSocket):```

await websocket.accept()
``````

```
```

# Create sender adapter
sender = StarletteWebSocketSender(websocket)
``````

```
```

# Handle WebSocket connection
await ws_manager.handle_connection(socket=sender)
```

app = Starlette(```

routes=[```

WebSocketRoute("/ws", websocket_endpoint)
```
]
```
)
```