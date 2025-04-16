"""
Domain services for the Realtime module.

This module defines the core domain services for the Realtime module,
providing high-level operations for notifications, subscriptions, and connections.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, Set, Union, Callable, Protocol, runtime_checkable, AsyncIterator
from dataclasses import dataclass

from uno.core.result import Result
from uno.domain.service import DomainService

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
    NotificationStatus,
    NotificationType,
    NotificationPriority,
    SubscriptionStatus,
    SubscriptionType,
    ConnectionState,
    MessageType,
    EventPriority
)
from uno.realtime.domain_repositories import (
    NotificationRepositoryProtocol,
    SubscriptionRepositoryProtocol,
    ConnectionRepositoryProtocol,
    MessageRepositoryProtocol,
    EventRepositoryProtocol
)


@runtime_checkable
class NotificationServiceProtocol(Protocol):
    """Protocol for notification service."""
    
    async def create_notification(
        self,
        title: str,
        message: str,
        recipients: List[UserId],
        type_: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Result[Notification]:
        """
        Create a new notification.
        
        Args:
            title: The notification title
            message: The notification message
            recipients: List of recipient user IDs
            type_: The notification type
            priority: The notification priority
            **kwargs: Additional notification parameters
            
        Returns:
            Result containing the created notification or an error
        """
        ...
    
    async def get_notification(self, notification_id: NotificationId) -> Result[Notification]:
        """
        Get a notification by ID.
        
        Args:
            notification_id: ID of the notification to retrieve
            
        Returns:
            Result containing the notification or an error if not found
        """
        ...
    
    async def get_user_notifications(
        self,
        user_id: UserId,
        status: Optional[NotificationStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[List[Notification]]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: User ID
            status: Optional notification status filter
            page: Page number (1-based)
            page_size: Number of notifications per page
            
        Returns:
            Result containing a list of notifications or an error
        """
        ...
    
    async def mark_as_delivered(self, notification_id: NotificationId) -> Result[Notification]:
        """
        Mark a notification as delivered.
        
        Args:
            notification_id: ID of the notification to mark
            
        Returns:
            Result containing the updated notification or an error
        """
        ...
    
    async def mark_as_read(
        self,
        notification_id: NotificationId,
        user_id: UserId
    ) -> Result[Notification]:
        """
        Mark a notification as read by a user.
        
        Args:
            notification_id: ID of the notification to mark
            user_id: ID of the user who read the notification
            
        Returns:
            Result containing the updated notification or an error
        """
        ...
    
    async def get_unread_count(self, user_id: UserId) -> Result[int]:
        """
        Get the count of unread notifications for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing the count or an error
        """
        ...
    
    async def delete_notification(self, notification_id: NotificationId) -> Result[bool]:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def create_system_notification(
        self,
        title: str,
        message: str,
        recipients: List[UserId],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Result[Notification]:
        """
        Create a system notification.
        
        Args:
            title: The notification title
            message: The notification message
            recipients: List of recipient user IDs
            priority: The notification priority
            **kwargs: Additional notification parameters
            
        Returns:
            Result containing the created notification or an error
        """
        ...


@runtime_checkable
class SubscriptionServiceProtocol(Protocol):
    """Protocol for subscription service."""
    
    async def create_subscription(
        self,
        user_id: UserId,
        type_: SubscriptionType,
        **kwargs
    ) -> Result[Subscription]:
        """
        Create a new subscription.
        
        Args:
            user_id: User ID
            type_: Subscription type
            **kwargs: Additional subscription parameters
            
        Returns:
            Result containing the created subscription or an error
        """
        ...
    
    async def get_subscription(self, subscription_id: SubscriptionId) -> Result[Subscription]:
        """
        Get a subscription by ID.
        
        Args:
            subscription_id: ID of the subscription to retrieve
            
        Returns:
            Result containing the subscription or an error if not found
        """
        ...
    
    async def update_subscription(self, subscription: Subscription) -> Result[Subscription]:
        """
        Update a subscription.
        
        Args:
            subscription: Subscription to update
            
        Returns:
            Result containing the updated subscription or an error
        """
        ...
    
    async def delete_subscription(self, subscription_id: SubscriptionId) -> Result[bool]:
        """
        Delete a subscription.
        
        Args:
            subscription_id: ID of the subscription to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def get_user_subscriptions(
        self,
        user_id: UserId,
        status: Optional[SubscriptionStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[List[Subscription]]:
        """
        Get subscriptions for a specific user.
        
        Args:
            user_id: User ID
            status: Optional subscription status filter
            page: Page number (1-based)
            page_size: Number of subscriptions per page
            
        Returns:
            Result containing a list of subscriptions or an error
        """
        ...
    
    async def update_subscription_status(
        self,
        subscription_id: SubscriptionId,
        status: SubscriptionStatus
    ) -> Result[Subscription]:
        """
        Update the status of a subscription.
        
        Args:
            subscription_id: ID of the subscription to update
            status: New status
            
        Returns:
            Result containing the updated subscription or an error
        """
        ...
    
    async def find_matching_subscriptions(
        self,
        event_data: Dict[str, Any]
    ) -> Result[List[Subscription]]:
        """
        Find subscriptions that match the given event data.
        
        Args:
            event_data: Event data to match against subscriptions
            
        Returns:
            Result containing a list of matching subscriptions or an error
        """
        ...
    
    async def create_resource_subscription(
        self,
        user_id: UserId,
        resource_id: str,
        resource_type: Optional[str] = None,
        **kwargs
    ) -> Result[Subscription]:
        """
        Create a subscription to a specific resource.
        
        Args:
            user_id: User ID
            resource_id: Resource ID
            resource_type: Optional resource type
            **kwargs: Additional subscription parameters
            
        Returns:
            Result containing the created subscription or an error
        """
        ...
    
    async def create_topic_subscription(
        self,
        user_id: UserId,
        topic: str,
        **kwargs
    ) -> Result[Subscription]:
        """
        Create a subscription to a topic.
        
        Args:
            user_id: User ID
            topic: Topic name
            **kwargs: Additional subscription parameters
            
        Returns:
            Result containing the created subscription or an error
        """
        ...


@runtime_checkable
class ConnectionServiceProtocol(Protocol):
    """Protocol for connection service."""
    
    async def create_connection(
        self,
        client_info: Optional[Dict[str, Any]] = None
    ) -> Result[Connection]:
        """
        Create a new connection.
        
        Args:
            client_info: Optional client information
            
        Returns:
            Result containing the created connection or an error
        """
        ...
    
    async def get_connection(self, connection_id: ConnectionId) -> Result[Connection]:
        """
        Get a connection by ID.
        
        Args:
            connection_id: ID of the connection to retrieve
            
        Returns:
            Result containing the connection or an error if not found
        """
        ...
    
    async def update_connection_state(
        self,
        connection_id: ConnectionId,
        state: ConnectionState
    ) -> Result[Connection]:
        """
        Update the state of a connection.
        
        Args:
            connection_id: ID of the connection to update
            state: New state
            
        Returns:
            Result containing the updated connection or an error
        """
        ...
    
    async def associate_user(
        self,
        connection_id: ConnectionId,
        user_id: UserId
    ) -> Result[Connection]:
        """
        Associate a user with a connection.
        
        Args:
            connection_id: ID of the connection to update
            user_id: User ID to associate
            
        Returns:
            Result containing the updated connection or an error
        """
        ...
    
    async def close_connection(self, connection_id: ConnectionId) -> Result[bool]:
        """
        Close a connection.
        
        Args:
            connection_id: ID of the connection to close
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def get_user_connections(self, user_id: UserId) -> Result[List[Connection]]:
        """
        Get active connections for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing a list of connections or an error
        """
        ...
    
    async def add_subscription_to_connection(
        self,
        connection_id: ConnectionId,
        subscription_id: SubscriptionId
    ) -> Result[Connection]:
        """
        Add a subscription to a connection.
        
        Args:
            connection_id: ID of the connection to update
            subscription_id: ID of the subscription to add
            
        Returns:
            Result containing the updated connection or an error
        """
        ...
    
    async def remove_subscription_from_connection(
        self,
        connection_id: ConnectionId,
        subscription_id: SubscriptionId
    ) -> Result[Connection]:
        """
        Remove a subscription from a connection.
        
        Args:
            connection_id: ID of the connection to update
            subscription_id: ID of the subscription to remove
            
        Returns:
            Result containing the updated connection or an error
        """
        ...


@runtime_checkable
class WebSocketServiceProtocol(Protocol):
    """Protocol for WebSocket service."""
    
    async def send_message(
        self,
        connection_id: ConnectionId,
        message_type: MessageType,
        payload: Union[str, bytes, Dict[str, Any]]
    ) -> Result[bool]:
        """
        Send a message to a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            message_type: Message type
            payload: Message payload
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def broadcast_message(
        self,
        message_type: MessageType,
        payload: Union[str, Dict[str, Any]],
        recipients: Optional[List[ConnectionId]] = None,
        exclude: Optional[List[ConnectionId]] = None
    ) -> Result[int]:
        """
        Broadcast a message to multiple WebSocket connections.
        
        Args:
            message_type: Message type
            payload: Message payload
            recipients: Optional list of recipient connection IDs
            exclude: Optional list of connection IDs to exclude
            
        Returns:
            Result containing the number of connections the message was sent to or an error
        """
        ...
    
    async def send_notification(
        self,
        notification: Notification
    ) -> Result[int]:
        """
        Send a notification to connected users.
        
        Args:
            notification: Notification to send
            
        Returns:
            Result containing the number of connections the notification was sent to or an error
        """
        ...
    
    async def handle_message(
        self,
        connection_id: ConnectionId,
        message: str,
        binary: bool = False
    ) -> Result[Any]:
        """
        Handle an incoming message from a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            message: Message content
            binary: Whether the message is binary
            
        Returns:
            Result containing the handling result or an error
        """
        ...


@runtime_checkable
class SSEServiceProtocol(Protocol):
    """Protocol for Server-Sent Events (SSE) service."""
    
    async def create_event(
        self,
        event_type: str,
        data: str,
        priority: EventPriority = EventPriority.NORMAL
    ) -> Result[Event]:
        """
        Create a new SSE event.
        
        Args:
            event_type: Event type
            data: Event data
            priority: Event priority
            
        Returns:
            Result containing the created event or an error
        """
        ...
    
    async def send_event(
        self,
        connection_id: ConnectionId,
        event: Event
    ) -> Result[bool]:
        """
        Send an event to an SSE connection.
        
        Args:
            connection_id: Connection ID
            event: Event to send
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def broadcast_event(
        self,
        event: Event,
        recipients: Optional[List[ConnectionId]] = None,
        exclude: Optional[List[ConnectionId]] = None
    ) -> Result[int]:
        """
        Broadcast an event to multiple SSE connections.
        
        Args:
            event: Event to broadcast
            recipients: Optional list of recipient connection IDs
            exclude: Optional list of connection IDs to exclude
            
        Returns:
            Result containing the number of connections the event was sent to or an error
        """
        ...
    
    async def get_event_stream(
        self,
        connection_id: ConnectionId
    ) -> Result[AsyncIterator[Event]]:
        """
        Get an event stream for an SSE connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Result containing an async iterator of events or an error
        """
        ...


class NotificationService(DomainService, NotificationServiceProtocol):
    """Service for managing notifications."""
    
    def __init__(
        self,
        repository: NotificationRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the notification service.
        
        Args:
            repository: Notification repository
            logger: Optional logger
        """
        self.repository = repository
        self.logger = logger or logging.getLogger("uno.realtime.notifications")
    
    async def create_notification(
        self,
        title: str,
        message: str,
        recipients: List[UserId],
        type_: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Result[Notification]:
        """
        Create a new notification.
        
        Args:
            title: The notification title
            message: The notification message
            recipients: List of recipient user IDs
            type_: The notification type
            priority: The notification priority
            **kwargs: Additional notification parameters
            
        Returns:
            Result containing the created notification or an error
        """
        try:
            # Extract additional parameters
            group_id = kwargs.get("group_id")
            sender_id = kwargs.get("sender_id")
            resource_type = kwargs.get("resource_type")
            resource_id = kwargs.get("resource_id")
            actions = kwargs.get("actions", [])
            channels = kwargs.get("channels", {"in_app"})
            expires_at = kwargs.get("expires_at")
            metadata = kwargs.get("metadata", {})
            
            # Create notification
            notification = Notification(
                id=NotificationId(str(uuid.uuid4())),
                title=title,
                message=message,
                recipients=recipients,
                type=type_,
                priority=priority,
                group_id=group_id,
                sender_id=sender_id,
                resource_type=resource_type,
                resource_id=resource_id,
                actions=actions,
                channels=channels,
                expires_at=expires_at,
                metadata=metadata
            )
            
            # Save notification
            result = await self.repository.create(notification)
            if result.is_success():
                self.logger.debug(f"Created notification with ID {notification.id.value}")
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to create notification: {str(e)}")
            return Result.failure(f"Failed to create notification: {str(e)}")
    
    async def get_notification(self, notification_id: NotificationId) -> Result[Notification]:
        """
        Get a notification by ID.
        
        Args:
            notification_id: ID of the notification to retrieve
            
        Returns:
            Result containing the notification or an error if not found
        """
        return await self.repository.get_by_id(notification_id)
    
    async def get_user_notifications(
        self,
        user_id: UserId,
        status: Optional[NotificationStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[List[Notification]]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: User ID
            status: Optional notification status filter
            page: Page number (1-based)
            page_size: Number of notifications per page
            
        Returns:
            Result containing a list of notifications or an error
        """
        return await self.repository.get_by_user(user_id, status, page, page_size)
    
    async def mark_as_delivered(self, notification_id: NotificationId) -> Result[Notification]:
        """
        Mark a notification as delivered.
        
        Args:
            notification_id: ID of the notification to mark
            
        Returns:
            Result containing the updated notification or an error
        """
        return await self.repository.mark_as_delivered(notification_id)
    
    async def mark_as_read(
        self,
        notification_id: NotificationId,
        user_id: UserId
    ) -> Result[Notification]:
        """
        Mark a notification as read by a user.
        
        Args:
            notification_id: ID of the notification to mark
            user_id: ID of the user who read the notification
            
        Returns:
            Result containing the updated notification or an error
        """
        return await self.repository.mark_as_read(notification_id, user_id)
    
    async def get_unread_count(self, user_id: UserId) -> Result[int]:
        """
        Get the count of unread notifications for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing the count or an error
        """
        return await self.repository.get_unread_count(user_id)
    
    async def delete_notification(self, notification_id: NotificationId) -> Result[bool]:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        return await self.repository.delete(notification_id)
    
    async def create_system_notification(
        self,
        title: str,
        message: str,
        recipients: List[UserId],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Result[Notification]:
        """
        Create a system notification.
        
        Args:
            title: The notification title
            message: The notification message
            recipients: List of recipient user IDs
            priority: The notification priority
            **kwargs: Additional notification parameters
            
        Returns:
            Result containing the created notification or an error
        """
        return await self.create_notification(
            title=title,
            message=message,
            recipients=recipients,
            type_=NotificationType.SYSTEM,
            priority=priority,
            sender_id=None,
            **kwargs
        )


class SubscriptionService(DomainService, SubscriptionServiceProtocol):
    """Service for managing subscriptions."""
    
    def __init__(
        self,
        repository: SubscriptionRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the subscription service.
        
        Args:
            repository: Subscription repository
            logger: Optional logger
        """
        self.repository = repository
        self.logger = logger or logging.getLogger("uno.realtime.subscriptions")
    
    async def create_subscription(
        self,
        user_id: UserId,
        type_: SubscriptionType,
        **kwargs
    ) -> Result[Subscription]:
        """
        Create a new subscription.
        
        Args:
            user_id: User ID
            type_: Subscription type
            **kwargs: Additional subscription parameters
            
        Returns:
            Result containing the created subscription or an error
        """
        try:
            # Extract specific parameters based on type
            resource_id = kwargs.get("resource_id")
            resource_type = kwargs.get("resource_type")
            topic = kwargs.get("topic")
            query = kwargs.get("query")
            
            # Additional parameters
            expires_at = kwargs.get("expires_at")
            metadata = kwargs.get("metadata", {})
            payload_filter = kwargs.get("payload_filter")
            labels = kwargs.get("labels", set())
            
            # Create subscription
            subscription = Subscription(
                id=SubscriptionId(str(uuid.uuid4())),
                user_id=user_id,
                type=type_,
                resource_id=resource_id,
                resource_type=resource_type,
                topic=topic,
                query=query,
                expires_at=expires_at,
                metadata=metadata,
                payload_filter=payload_filter,
                labels=labels
            )
            
            # Save subscription
            result = await self.repository.create(subscription)
            if result.is_success():
                self.logger.debug(f"Created subscription with ID {subscription.id.value}")
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to create subscription: {str(e)}")
            return Result.failure(f"Failed to create subscription: {str(e)}")
    
    async def get_subscription(self, subscription_id: SubscriptionId) -> Result[Subscription]:
        """
        Get a subscription by ID.
        
        Args:
            subscription_id: ID of the subscription to retrieve
            
        Returns:
            Result containing the subscription or an error if not found
        """
        return await self.repository.get_by_id(subscription_id)
    
    async def update_subscription(self, subscription: Subscription) -> Result[Subscription]:
        """
        Update a subscription.
        
        Args:
            subscription: Subscription to update
            
        Returns:
            Result containing the updated subscription or an error
        """
        return await self.repository.update(subscription)
    
    async def delete_subscription(self, subscription_id: SubscriptionId) -> Result[bool]:
        """
        Delete a subscription.
        
        Args:
            subscription_id: ID of the subscription to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        return await self.repository.delete(subscription_id)
    
    async def get_user_subscriptions(
        self,
        user_id: UserId,
        status: Optional[SubscriptionStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[List[Subscription]]:
        """
        Get subscriptions for a specific user.
        
        Args:
            user_id: User ID
            status: Optional subscription status filter
            page: Page number (1-based)
            page_size: Number of subscriptions per page
            
        Returns:
            Result containing a list of subscriptions or an error
        """
        return await self.repository.get_by_user(user_id, status, page, page_size)
    
    async def update_subscription_status(
        self,
        subscription_id: SubscriptionId,
        status: SubscriptionStatus
    ) -> Result[Subscription]:
        """
        Update the status of a subscription.
        
        Args:
            subscription_id: ID of the subscription to update
            status: New status
            
        Returns:
            Result containing the updated subscription or an error
        """
        return await self.repository.update_status(subscription_id, status)
    
    async def find_matching_subscriptions(
        self,
        event_data: Dict[str, Any]
    ) -> Result[List[Subscription]]:
        """
        Find subscriptions that match the given event data.
        
        Args:
            event_data: Event data to match against subscriptions
            
        Returns:
            Result containing a list of matching subscriptions or an error
        """
        return await self.repository.find_matching_subscriptions(event_data)
    
    async def create_resource_subscription(
        self,
        user_id: UserId,
        resource_id: str,
        resource_type: Optional[str] = None,
        **kwargs
    ) -> Result[Subscription]:
        """
        Create a subscription to a specific resource.
        
        Args:
            user_id: User ID
            resource_id: Resource ID
            resource_type: Optional resource type
            **kwargs: Additional subscription parameters
            
        Returns:
            Result containing the created subscription or an error
        """
        return await self.create_subscription(
            user_id=user_id,
            type_=SubscriptionType.RESOURCE,
            resource_id=resource_id,
            resource_type=resource_type,
            **kwargs
        )
    
    async def create_topic_subscription(
        self,
        user_id: UserId,
        topic: str,
        **kwargs
    ) -> Result[Subscription]:
        """
        Create a subscription to a topic.
        
        Args:
            user_id: User ID
            topic: Topic name
            **kwargs: Additional subscription parameters
            
        Returns:
            Result containing the created subscription or an error
        """
        return await self.create_subscription(
            user_id=user_id,
            type_=SubscriptionType.TOPIC,
            topic=topic,
            **kwargs
        )


class ConnectionService(DomainService, ConnectionServiceProtocol):
    """Service for managing connections."""
    
    def __init__(
        self,
        repository: ConnectionRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the connection service.
        
        Args:
            repository: Connection repository
            logger: Optional logger
        """
        self.repository = repository
        self.logger = logger or logging.getLogger("uno.realtime.connections")
    
    async def create_connection(
        self,
        client_info: Optional[Dict[str, Any]] = None
    ) -> Result[Connection]:
        """
        Create a new connection.
        
        Args:
            client_info: Optional client information
            
        Returns:
            Result containing the created connection or an error
        """
        try:
            # Create connection
            connection = Connection(
                id=ConnectionId(str(uuid.uuid4())),
                state=ConnectionState.INITIALIZING,
                client_info=client_info or {}
            )
            
            # Save connection
            result = await self.repository.create(connection)
            if result.is_success():
                self.logger.debug(f"Created connection with ID {connection.id.value}")
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to create connection: {str(e)}")
            return Result.failure(f"Failed to create connection: {str(e)}")
    
    async def get_connection(self, connection_id: ConnectionId) -> Result[Connection]:
        """
        Get a connection by ID.
        
        Args:
            connection_id: ID of the connection to retrieve
            
        Returns:
            Result containing the connection or an error if not found
        """
        return await self.repository.get_by_id(connection_id)
    
    async def update_connection_state(
        self,
        connection_id: ConnectionId,
        state: ConnectionState
    ) -> Result[Connection]:
        """
        Update the state of a connection.
        
        Args:
            connection_id: ID of the connection to update
            state: New state
            
        Returns:
            Result containing the updated connection or an error
        """
        return await self.repository.update_state(connection_id, state)
    
    async def associate_user(
        self,
        connection_id: ConnectionId,
        user_id: UserId
    ) -> Result[Connection]:
        """
        Associate a user with a connection.
        
        Args:
            connection_id: ID of the connection to update
            user_id: User ID to associate
            
        Returns:
            Result containing the updated connection or an error
        """
        return await self.repository.associate_user(connection_id, user_id)
    
    async def close_connection(self, connection_id: ConnectionId) -> Result[bool]:
        """
        Close a connection.
        
        Args:
            connection_id: ID of the connection to close
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            # Update connection state
            result = await self.repository.update_state(connection_id, ConnectionState.DISCONNECTED)
            if result.is_failure():
                return result
            
            # Delete connection
            return await self.repository.delete(connection_id)
        except Exception as e:
            self.logger.error(f"Failed to close connection: {str(e)}")
            return Result.failure(f"Failed to close connection: {str(e)}")
    
    async def get_user_connections(self, user_id: UserId) -> Result[List[Connection]]:
        """
        Get active connections for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing a list of connections or an error
        """
        return await self.repository.get_by_user(user_id)
    
    async def add_subscription_to_connection(
        self,
        connection_id: ConnectionId,
        subscription_id: SubscriptionId
    ) -> Result[Connection]:
        """
        Add a subscription to a connection.
        
        Args:
            connection_id: ID of the connection to update
            subscription_id: ID of the subscription to add
            
        Returns:
            Result containing the updated connection or an error
        """
        return await self.repository.add_subscription(connection_id, subscription_id)
    
    async def remove_subscription_from_connection(
        self,
        connection_id: ConnectionId,
        subscription_id: SubscriptionId
    ) -> Result[Connection]:
        """
        Remove a subscription from a connection.
        
        Args:
            connection_id: ID of the connection to update
            subscription_id: ID of the subscription to remove
            
        Returns:
            Result containing the updated connection or an error
        """
        return await self.repository.remove_subscription(connection_id, subscription_id)


class WebSocketService(DomainService, WebSocketServiceProtocol):
    """Service for WebSocket operations."""
    
    def __init__(
        self,
        connection_service: ConnectionServiceProtocol,
        message_repository: MessageRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the WebSocket service.
        
        Args:
            connection_service: Connection service
            message_repository: Message repository
            logger: Optional logger
        """
        self.connection_service = connection_service
        self.message_repository = message_repository
        self.logger = logger or logging.getLogger("uno.realtime.websocket")
        
        # Active WebSocket connections
        self.active_connections: Dict[str, Any] = {}
    
    def register_socket(self, connection_id: ConnectionId, socket: Any) -> None:
        """
        Register a WebSocket object for a connection.
        
        Args:
            connection_id: Connection ID
            socket: WebSocket object
        """
        self.active_connections[connection_id.value] = socket
    
    def unregister_socket(self, connection_id: ConnectionId) -> None:
        """
        Unregister a WebSocket object.
        
        Args:
            connection_id: Connection ID
        """
        self.active_connections.pop(connection_id.value, None)
    
    async def send_message(
        self,
        connection_id: ConnectionId,
        message_type: MessageType,
        payload: Union[str, bytes, Dict[str, Any]]
    ) -> Result[bool]:
        """
        Send a message to a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            message_type: Message type
            payload: Message payload
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            # Get socket
            socket = self.active_connections.get(connection_id.value)
            if not socket:
                return Result.failure(f"WebSocket connection {connection_id.value} not found")
            
            # Create message
            message = Message(
                connection_id=connection_id,
                type=message_type,
                payload=payload
            )
            
            # Store message
            await self.message_repository.create(message)
            
            # Get connection to check if it has a user_id
            connection_result = await self.connection_service.get_connection(connection_id)
            if connection_result.is_success():
                connection = connection_result.value
                if connection.user_id:
                    message.user_id = connection.user_id
            
            # Send message
            if isinstance(payload, dict):
                # Convert dict to JSON string
                data = json.dumps({
                    "type": message_type.value,
                    "payload": payload,
                    "id": message.id
                })
                await socket.send_text(data)
            elif isinstance(payload, bytes):
                # Send binary data
                await socket.send_bytes(payload)
            else:
                # Send text data
                data = json.dumps({
                    "type": message_type.value,
                    "payload": payload,
                    "id": message.id
                })
                await socket.send_text(data)
            
            # Update connection activity
            await self.connection_service.get_connection(connection_id)
            
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return Result.failure(f"Failed to send message: {str(e)}")
    
    async def broadcast_message(
        self,
        message_type: MessageType,
        payload: Union[str, Dict[str, Any]],
        recipients: Optional[List[ConnectionId]] = None,
        exclude: Optional[List[ConnectionId]] = None
    ) -> Result[int]:
        """
        Broadcast a message to multiple WebSocket connections.
        
        Args:
            message_type: Message type
            payload: Message payload
            recipients: Optional list of recipient connection IDs
            exclude: Optional list of connection IDs to exclude
            
        Returns:
            Result containing the number of connections the message was sent to or an error
        """
        try:
            # Convert exclude list to set of strings
            exclude_set = {conn.value for conn in (exclude or [])}
            
            # Get connections to send to
            if recipients:
                connections = [conn for conn in recipients if conn.value not in exclude_set]
            else:
                # Use all active connections
                connections = [ConnectionId(conn_id) for conn_id in self.active_connections.keys() 
                              if conn_id not in exclude_set]
            
            # Send message to each connection
            sent_count = 0
            for connection_id in connections:
                result = await self.send_message(connection_id, message_type, payload)
                if result.is_success():
                    sent_count += 1
            
            return Result.success(sent_count)
        except Exception as e:
            self.logger.error(f"Failed to broadcast message: {str(e)}")
            return Result.failure(f"Failed to broadcast message: {str(e)}")
    
    async def send_notification(
        self,
        notification: Notification
    ) -> Result[int]:
        """
        Send a notification to connected users.
        
        Args:
            notification: Notification to send
            
        Returns:
            Result containing the number of connections the notification was sent to or an error
        """
        try:
            sent_count = 0
            
            # Get connections for each recipient
            for recipient in notification.recipients:
                connections_result = await self.connection_service.get_user_connections(recipient)
                if connections_result.is_failure():
                    continue
                
                connections = connections_result.value
                
                # Send to each connection
                for connection in connections:
                    # Convert notification to payload
                    payload = {
                        "id": notification.id.value,
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.type.value,
                        "priority": notification.priority.value,
                        "created_at": notification.created_at.isoformat(),
                        "actions": notification.actions
                    }
                    
                    # Add additional fields if present
                    if notification.sender_id:
                        payload["sender_id"] = notification.sender_id.value
                    if notification.resource_type:
                        payload["resource_type"] = notification.resource_type
                    if notification.resource_id:
                        payload["resource_id"] = notification.resource_id
                    
                    # Send message
                    result = await self.send_message(
                        connection.id, 
                        MessageType.NOTIFICATION, 
                        payload
                    )
                    
                    if result.is_success():
                        sent_count += 1
            
            return Result.success(sent_count)
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return Result.failure(f"Failed to send notification: {str(e)}")
    
    async def handle_message(
        self,
        connection_id: ConnectionId,
        message: str,
        binary: bool = False
    ) -> Result[Any]:
        """
        Handle an incoming message from a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            message: Message content
            binary: Whether the message is binary
            
        Returns:
            Result containing the handling result or an error
        """
        try:
            # Create message object
            if binary:
                # Store as binary message
                message_obj = Message(
                    connection_id=connection_id,
                    type=MessageType.BINARY,
                    payload=message if isinstance(message, bytes) else message.encode()
                )
            else:
                # Parse JSON message
                try:
                    data = json.loads(message)
                    message_type = MessageType(data.get("type", "text"))
                    payload = data.get("payload", message)
                    message_obj = Message(
                        connection_id=connection_id,
                        type=message_type,
                        payload=payload
                    )
                except json.JSONDecodeError:
                    # Not valid JSON, treat as text
                    message_obj = Message(
                        connection_id=connection_id,
                        type=MessageType.TEXT,
                        payload=message
                    )
            
            # Store message
            await self.message_repository.create(message_obj)
            
            # Update connection activity
            await self.connection_service.get_connection(connection_id)
            
            # Process message based on type
            # This would be expanded with actual message handling logic
            
            return Result.success({"message_id": message_obj.id})
        except Exception as e:
            self.logger.error(f"Failed to handle message: {str(e)}")
            return Result.failure(f"Failed to handle message: {str(e)}")


class SSEService(DomainService, SSEServiceProtocol):
    """Service for Server-Sent Events (SSE) operations."""
    
    def __init__(
        self,
        connection_service: ConnectionServiceProtocol,
        event_repository: EventRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SSE service.
        
        Args:
            connection_service: Connection service
            event_repository: Event repository
            logger: Optional logger
        """
        self.connection_service = connection_service
        self.event_repository = event_repository
        self.logger = logger or logging.getLogger("uno.realtime.sse")
        
        # Active SSE connections and their event queues
        self.event_queues: Dict[str, asyncio.Queue] = {}
    
    def register_connection(self, connection_id: ConnectionId) -> asyncio.Queue:
        """
        Register an SSE connection and create its event queue.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Event queue for the connection
        """
        queue = asyncio.Queue()
        self.event_queues[connection_id.value] = queue
        return queue
    
    def unregister_connection(self, connection_id: ConnectionId) -> None:
        """
        Unregister an SSE connection.
        
        Args:
            connection_id: Connection ID
        """
        queue = self.event_queues.pop(connection_id.value, None)
        if queue:
            # Add None to signal the connection is closed
            queue.put_nowait(None)
    
    async def create_event(
        self,
        event_type: str,
        data: str,
        priority: EventPriority = EventPriority.NORMAL
    ) -> Result[Event]:
        """
        Create a new SSE event.
        
        Args:
            event_type: Event type
            data: Event data
            priority: Event priority
            
        Returns:
            Result containing the created event or an error
        """
        try:
            event = Event(
                event=event_type,
                data=data,
                priority=priority
            )
            
            # Store event
            result = await self.event_repository.create(event)
            if result.is_success():
                self.logger.debug(f"Created event with ID {event.id}")
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to create event: {str(e)}")
            return Result.failure(f"Failed to create event: {str(e)}")
    
    async def send_event(
        self,
        connection_id: ConnectionId,
        event: Event
    ) -> Result[bool]:
        """
        Send an event to an SSE connection.
        
        Args:
            connection_id: Connection ID
            event: Event to send
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            # Get connection's event queue
            queue = self.event_queues.get(connection_id.value)
            if not queue:
                return Result.failure(f"SSE connection {connection_id.value} not found")
            
            # Add event to queue
            await queue.put(event)
            
            # Update connection activity
            await self.connection_service.get_connection(connection_id)
            
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Failed to send event: {str(e)}")
            return Result.failure(f"Failed to send event: {str(e)}")
    
    async def broadcast_event(
        self,
        event: Event,
        recipients: Optional[List[ConnectionId]] = None,
        exclude: Optional[List[ConnectionId]] = None
    ) -> Result[int]:
        """
        Broadcast an event to multiple SSE connections.
        
        Args:
            event: Event to broadcast
            recipients: Optional list of recipient connection IDs
            exclude: Optional list of connection IDs to exclude
            
        Returns:
            Result containing the number of connections the event was sent to or an error
        """
        try:
            # Convert exclude list to set of strings
            exclude_set = {conn.value for conn in (exclude or [])}
            
            # Get connections to send to
            if recipients:
                connections = [conn for conn in recipients if conn.value not in exclude_set]
            else:
                # Use all active connections
                connections = [ConnectionId(conn_id) for conn_id in self.event_queues.keys() 
                              if conn_id not in exclude_set]
            
            # Send event to each connection
            sent_count = 0
            for connection_id in connections:
                result = await self.send_event(connection_id, event)
                if result.is_success():
                    sent_count += 1
            
            return Result.success(sent_count)
        except Exception as e:
            self.logger.error(f"Failed to broadcast event: {str(e)}")
            return Result.failure(f"Failed to broadcast event: {str(e)}")
    
    async def get_event_stream(
        self,
        connection_id: ConnectionId
    ) -> Result[AsyncIterator[Event]]:
        """
        Get an event stream for an SSE connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Result containing an async iterator of events or an error
        """
        try:
            # Get or create connection's event queue
            queue = self.event_queues.get(connection_id.value)
            if not queue:
                queue = self.register_connection(connection_id)
            
            # Return an async iterator that yields events from the queue
            async def event_iterator():
                while True:
                    event = await queue.get()
                    if event is None:
                        # Connection closed
                        break
                    yield event
                    queue.task_done()
            
            return Result.success(event_iterator())
        except Exception as e:
            self.logger.error(f"Failed to get event stream: {str(e)}")
            return Result.failure(f"Failed to get event stream: {str(e)}")


class RealtimeService(DomainService):
    """Coordinating service for realtime operations."""
    
    def __init__(
        self,
        notification_service: NotificationServiceProtocol,
        subscription_service: SubscriptionServiceProtocol,
        connection_service: ConnectionServiceProtocol,
        websocket_service: WebSocketServiceProtocol,
        sse_service: SSEServiceProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the realtime service.
        
        Args:
            notification_service: Notification service
            subscription_service: Subscription service
            connection_service: Connection service
            websocket_service: WebSocket service
            sse_service: SSE service
            logger: Optional logger
        """
        self.notification_service = notification_service
        self.subscription_service = subscription_service
        self.connection_service = connection_service
        self.websocket_service = websocket_service
        self.sse_service = sse_service
        self.logger = logger or logging.getLogger("uno.realtime")