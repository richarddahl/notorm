"""
Domain provider for the Realtime module.

This module configures dependency injection for the Realtime module.
"""

import logging
from typing import Optional

import inject
from uno.database.provider import get_db_session

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


def configure_realtime_dependencies(binder: inject.Binder) -> None:
    """
    Configure dependencies for the Realtime module.
    
    Args:
        binder: Dependency injection binder
    """
    # Create logger
    logger = logging.getLogger("uno.realtime")
    
    # Bind repositories
    binder.bind(
        NotificationRepositoryProtocol,
        lambda: NotificationRepository(get_db_session())
    )
    binder.bind(
        SubscriptionRepositoryProtocol,
        lambda: SubscriptionRepository(get_db_session())
    )
    binder.bind(
        ConnectionRepositoryProtocol,
        lambda: ConnectionRepository(get_db_session())
    )
    binder.bind(
        MessageRepositoryProtocol,
        lambda: MessageRepository(get_db_session())
    )
    binder.bind(
        EventRepositoryProtocol,
        lambda: EventRepository(get_db_session())
    )
    
    # Bind services
    binder.bind(
        NotificationServiceProtocol,
        lambda: NotificationService(
            inject.instance(NotificationRepositoryProtocol),
            logger.getChild("notifications")
        )
    )
    binder.bind(
        SubscriptionServiceProtocol,
        lambda: SubscriptionService(
            inject.instance(SubscriptionRepositoryProtocol),
            logger.getChild("subscriptions")
        )
    )
    binder.bind(
        ConnectionServiceProtocol,
        lambda: ConnectionService(
            inject.instance(ConnectionRepositoryProtocol),
            logger.getChild("connections")
        )
    )
    binder.bind(
        WebSocketServiceProtocol,
        lambda: WebSocketService(
            inject.instance(ConnectionServiceProtocol),
            inject.instance(MessageRepositoryProtocol),
            logger.getChild("websocket")
        )
    )
    binder.bind(
        SSEServiceProtocol,
        lambda: SSEService(
            inject.instance(ConnectionServiceProtocol),
            inject.instance(EventRepositoryProtocol),
            logger.getChild("sse")
        )
    )
    
    # Bind coordinating service
    binder.bind(
        RealtimeService,
        lambda: RealtimeService(
            inject.instance(NotificationServiceProtocol),
            inject.instance(SubscriptionServiceProtocol),
            inject.instance(ConnectionServiceProtocol),
            inject.instance(WebSocketServiceProtocol),
            inject.instance(SSEServiceProtocol),
            logger
        )
    )


def get_notification_service() -> NotificationServiceProtocol:
    """
    Get the notification service.
    
    Returns:
        NotificationService instance
    """
    return inject.instance(NotificationServiceProtocol)


def get_subscription_service() -> SubscriptionServiceProtocol:
    """
    Get the subscription service.
    
    Returns:
        SubscriptionService instance
    """
    return inject.instance(SubscriptionServiceProtocol)


def get_connection_service() -> ConnectionServiceProtocol:
    """
    Get the connection service.
    
    Returns:
        ConnectionService instance
    """
    return inject.instance(ConnectionServiceProtocol)


def get_websocket_service() -> WebSocketServiceProtocol:
    """
    Get the WebSocket service.
    
    Returns:
        WebSocketService instance
    """
    return inject.instance(WebSocketServiceProtocol)


def get_sse_service() -> SSEServiceProtocol:
    """
    Get the SSE service.
    
    Returns:
        SSEService instance
    """
    return inject.instance(SSEServiceProtocol)


def get_realtime_service() -> RealtimeService:
    """
    Get the realtime service.
    
    Returns:
        RealtimeService instance
    """
    return inject.instance(RealtimeService)