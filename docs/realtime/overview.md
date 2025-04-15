# Real-time Updates Overview

The Uno framework provides built-in support for real-time updates via several complementary mechanisms. This allows your applications to deliver responsive, live-updating user experiences without complex custom code.

## Available Mechanisms

Uno offers multiple real-time update mechanisms that can be used independently or together:

1. **WebSockets**: Full-duplex communication channel for bidirectional real-time updates
2. **Server-Sent Events (SSE)**: Lightweight, unidirectional server-to-client data streaming
3. **Notification System**: Pub/sub system for managing and distributing notifications
4. **Subscription Management**: Configure and manage what updates clients receive

## Architecture Overview

The real-time update system is built as an independent module that integrates with the core Uno framework. It follows the same principles of loose coupling and protocol-based design as the rest of the framework.

``````
```

          ┌─────────────────────┐
          │   Domain Events     │
          └──────────┬──────────┘
                     │
                     ▼
```
```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  WebSocket  │     │  Notification Hub   │     │       SSE       │
│   Server    │◄────┤                     ├────►│     Server      │
└─────┬───────┘     │                     │     └────────┬────────┘```

  │             └─────────────────────┘              │
  │                        ▲                         │
  │                        │                         │
  │                        │                         │
  │             ┌──────────┴──────────┐              │
  │             │  Subscription Mgr   │              │
  │             └─────────────────────┘              │
  │                                                  │
  ▼                                                  ▼
```
┌─────────────────────────────────────────────────────────────────┐
│                       Connected Clients                         │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### WebSocket Server

The WebSocket server enables full-duplex communication between the server and clients. Features include:

- Connection management with authentication and authorization
- Message routing and distribution
- Bi-directional communication with protocol handling
- Connection health monitoring and reconnection support

### Server-Sent Events (SSE)

The SSE implementation provides a lightweight alternative to WebSockets for unidirectional updates:

- Efficient one-way data streaming
- Automatic reconnection handling
- Event typing for structured data
- Compatible with all modern browsers with minimal client-side code

### Notification System

The notification system handles the creation, management, and delivery of notifications:

- User-targeted and broadcast notifications
- Priority levels for critical updates
- Notification history and storage
- Read/unread status tracking

### Subscription Management

The subscription management system allows fine-grained control over what updates a client receives:

- Entity-level and type-level subscriptions
- Topic-based subscriptions for channel-like updates
- Query-based subscriptions for data changes matching certain criteria
- Subscription persistence for reconnecting clients

## Integration with Domain Events

The real-time update system integrates with Uno's event system, allowing domain events to be published as real-time updates. This provides:

- Consistency between your domain model and client state
- Automatic updates when business operations complete
- Filtered event propagation based on authorization rules

## Implementation Status

The real-time updates module has been implemented in phases:

- ✅ WebSocket implementation (complete)
- ✅ Server-Sent Events implementation (complete)
- ✅ Notification system (complete)
- ✅ Subscription management (complete)

## Getting Started

See the following guides for detailed implementation instructions:

- [WebSocket Configuration and Usage](websocket.md)
- [Server-Sent Events Implementation](sse.md)
- [Notification System](notifications.md)
- [Subscription Management](subscriptions.md)