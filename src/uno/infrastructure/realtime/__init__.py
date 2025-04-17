"""Real-time updates module for the Uno framework.

This module provides support for real-time updates via WebSockets, Server-Sent Events (SSE),
and a notification system. It includes subscription management for configuring what updates
clients receive.
"""

from uno.realtime.entities import (
    Notification,
    Subscription,
    Connection,
    Message,
    Event,
    NotificationId,
    SubscriptionId,
    ConnectionId,
    UserId,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    SubscriptionType,
    SubscriptionStatus,
    ConnectionState,
    MessageType,
    EventPriority
)

from uno.realtime.domain_services import (
    NotificationService,
    SubscriptionService,
    ConnectionService,
    WebSocketService,
    SSEService,
    RealtimeService,
    NotificationServiceProtocol,
    SubscriptionServiceProtocol,
    ConnectionServiceProtocol,
    WebSocketServiceProtocol,
    SSEServiceProtocol
)

from uno.realtime.domain_repositories import (
    NotificationRepository,
    SubscriptionRepository,
    ConnectionRepository,
    MessageRepository,
    EventRepository,
    NotificationRepositoryProtocol,
    SubscriptionRepositoryProtocol,
    ConnectionRepositoryProtocol,
    MessageRepositoryProtocol,
    EventRepositoryProtocol
)

from uno.realtime.domain_provider import (
    configure_realtime_dependencies,
    get_notification_service,
    get_subscription_service,
    get_connection_service,
    get_websocket_service,
    get_sse_service,
    get_realtime_service
)

from uno.realtime.domain_endpoints import create_realtime_router

__all__ = [
    # Entities
    'Notification',
    'Subscription',
    'Connection',
    'Message',
    'Event',
    'NotificationId',
    'SubscriptionId',
    'ConnectionId',
    'UserId',
    'NotificationType',
    'NotificationPriority',
    'NotificationStatus',
    'SubscriptionType',
    'SubscriptionStatus',
    'ConnectionState',
    'MessageType',
    'EventPriority',
    
    # Services
    'NotificationService',
    'SubscriptionService',
    'ConnectionService',
    'WebSocketService',
    'SSEService',
    'RealtimeService',
    'NotificationServiceProtocol',
    'SubscriptionServiceProtocol',
    'ConnectionServiceProtocol',
    'WebSocketServiceProtocol',
    'SSEServiceProtocol',
    
    # Repositories
    'NotificationRepository',
    'SubscriptionRepository',
    'ConnectionRepository',
    'MessageRepository',
    'EventRepository',
    'NotificationRepositoryProtocol',
    'SubscriptionRepositoryProtocol',
    'ConnectionRepositoryProtocol',
    'MessageRepositoryProtocol',
    'EventRepositoryProtocol',
    
    # Providers
    'configure_realtime_dependencies',
    'get_notification_service',
    'get_subscription_service',
    'get_connection_service',
    'get_websocket_service',
    'get_sse_service',
    'get_realtime_service',
    
    # Endpoints
    'create_realtime_router'
]