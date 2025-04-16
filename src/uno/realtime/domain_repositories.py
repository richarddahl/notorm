"""
Domain repositories for the Realtime module.

This module defines repository interfaces and implementations for the Realtime module.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator, Set, Union
from dataclasses import dataclass

from uno.core.result import Result
from uno.domain.repository import DomainRepository, AsyncDomainRepository

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
    SubscriptionStatus,
    ConnectionState
)


@runtime_checkable
class NotificationRepositoryProtocol(Protocol):
    """Protocol for notification repository."""
    
    async def create(self, notification: Notification) -> Result[Notification]:
        """
        Create a new notification.
        
        Args:
            notification: Notification to create
            
        Returns:
            Result containing the created notification or an error
        """
        ...
    
    async def get_by_id(self, notification_id: NotificationId) -> Result[Notification]:
        """
        Get a notification by ID.
        
        Args:
            notification_id: ID of the notification to retrieve
            
        Returns:
            Result containing the notification or an error if not found
        """
        ...
    
    async def update(self, notification: Notification) -> Result[Notification]:
        """
        Update a notification.
        
        Args:
            notification: Notification to update
            
        Returns:
            Result containing the updated notification or an error
        """
        ...
    
    async def delete(self, notification_id: NotificationId) -> Result[bool]:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def get_by_user(
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
    
    async def search(
        self, 
        query: Dict[str, Any], 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[Notification]]:
        """
        Search for notifications based on query parameters.
        
        Args:
            query: Search query parameters
            page: Page number (1-based)
            page_size: Number of notifications per page
            
        Returns:
            Result containing a list of notifications or an error
        """
        ...


@runtime_checkable
class SubscriptionRepositoryProtocol(Protocol):
    """Protocol for subscription repository."""
    
    async def create(self, subscription: Subscription) -> Result[Subscription]:
        """
        Create a new subscription.
        
        Args:
            subscription: Subscription to create
            
        Returns:
            Result containing the created subscription or an error
        """
        ...
    
    async def get_by_id(self, subscription_id: SubscriptionId) -> Result[Subscription]:
        """
        Get a subscription by ID.
        
        Args:
            subscription_id: ID of the subscription to retrieve
            
        Returns:
            Result containing the subscription or an error if not found
        """
        ...
    
    async def update(self, subscription: Subscription) -> Result[Subscription]:
        """
        Update a subscription.
        
        Args:
            subscription: Subscription to update
            
        Returns:
            Result containing the updated subscription or an error
        """
        ...
    
    async def delete(self, subscription_id: SubscriptionId) -> Result[bool]:
        """
        Delete a subscription.
        
        Args:
            subscription_id: ID of the subscription to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def get_by_user(
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
    
    async def get_active_by_resource(
        self, 
        resource_id: str, 
        resource_type: Optional[str] = None
    ) -> Result[List[Subscription]]:
        """
        Get active subscriptions for a specific resource.
        
        Args:
            resource_id: Resource ID
            resource_type: Optional resource type
            
        Returns:
            Result containing a list of subscriptions or an error
        """
        ...
    
    async def get_active_by_topic(self, topic: str) -> Result[List[Subscription]]:
        """
        Get active subscriptions for a specific topic.
        
        Args:
            topic: Topic name
            
        Returns:
            Result containing a list of subscriptions or an error
        """
        ...
    
    async def update_status(
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
    
    async def cleanup_expired_subscriptions(self) -> Result[int]:
        """
        Clean up expired subscriptions.
        
        Returns:
            Result containing the number of deleted subscriptions or an error
        """
        ...


@runtime_checkable
class ConnectionRepositoryProtocol(Protocol):
    """Protocol for connection repository."""
    
    async def create(self, connection: Connection) -> Result[Connection]:
        """
        Create a new connection.
        
        Args:
            connection: Connection to create
            
        Returns:
            Result containing the created connection or an error
        """
        ...
    
    async def get_by_id(self, connection_id: ConnectionId) -> Result[Connection]:
        """
        Get a connection by ID.
        
        Args:
            connection_id: ID of the connection to retrieve
            
        Returns:
            Result containing the connection or an error if not found
        """
        ...
    
    async def update(self, connection: Connection) -> Result[Connection]:
        """
        Update a connection.
        
        Args:
            connection: Connection to update
            
        Returns:
            Result containing the updated connection or an error
        """
        ...
    
    async def delete(self, connection_id: ConnectionId) -> Result[bool]:
        """
        Delete a connection.
        
        Args:
            connection_id: ID of the connection to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def get_by_user(self, user_id: UserId) -> Result[List[Connection]]:
        """
        Get active connections for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing a list of connections or an error
        """
        ...
    
    async def get_active_connections(self) -> Result[List[Connection]]:
        """
        Get all active connections.
        
        Returns:
            Result containing a list of active connections or an error
        """
        ...
    
    async def update_state(
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
    
    async def update_activity(self, connection_id: ConnectionId) -> Result[Connection]:
        """
        Update the last activity timestamp of a connection.
        
        Args:
            connection_id: ID of the connection to update
            
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
    
    async def add_subscription(
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
    
    async def remove_subscription(
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
    
    async def cleanup_inactive_connections(self, older_than: datetime) -> Result[int]:
        """
        Clean up inactive connections.
        
        Args:
            older_than: Timestamp to compare against last activity
            
        Returns:
            Result containing the number of deleted connections or an error
        """
        ...


@runtime_checkable
class MessageRepositoryProtocol(Protocol):
    """Protocol for message repository."""
    
    async def create(self, message: Message) -> Result[Message]:
        """
        Create a new message.
        
        Args:
            message: Message to create
            
        Returns:
            Result containing the created message or an error
        """
        ...
    
    async def get_by_id(self, message_id: str) -> Result[Message]:
        """
        Get a message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            Result containing the message or an error if not found
        """
        ...
    
    async def get_by_connection(
        self, 
        connection_id: ConnectionId, 
        limit: int = 100
    ) -> Result[List[Message]]:
        """
        Get messages for a specific connection.
        
        Args:
            connection_id: Connection ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            Result containing a list of messages or an error
        """
        ...
    
    async def get_by_user(
        self, 
        user_id: UserId, 
        limit: int = 100
    ) -> Result[List[Message]]:
        """
        Get messages for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            Result containing a list of messages or an error
        """
        ...
    
    async def delete_old_messages(self, older_than: datetime) -> Result[int]:
        """
        Delete old messages.
        
        Args:
            older_than: Timestamp to compare against message timestamp
            
        Returns:
            Result containing the number of deleted messages or an error
        """
        ...


@runtime_checkable
class EventRepositoryProtocol(Protocol):
    """Protocol for event repository."""
    
    async def create(self, event: Event) -> Result[Event]:
        """
        Create a new event.
        
        Args:
            event: Event to create
            
        Returns:
            Result containing the created event or an error
        """
        ...
    
    async def get_by_id(self, event_id: str) -> Result[Event]:
        """
        Get an event by ID.
        
        Args:
            event_id: ID of the event to retrieve
            
        Returns:
            Result containing the event or an error if not found
        """
        ...
    
    async def get_recent_events(
        self, 
        event_type: Optional[str] = None, 
        limit: int = 100
    ) -> Result[List[Event]]:
        """
        Get recent events.
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to retrieve
            
        Returns:
            Result containing a list of events or an error
        """
        ...
    
    async def delete_old_events(self, older_than: datetime) -> Result[int]:
        """
        Delete old events.
        
        Args:
            older_than: Timestamp to compare against event timestamp
            
        Returns:
            Result containing the number of deleted events or an error
        """
        ...


# Repository implementations
class NotificationRepository(AsyncDomainRepository, NotificationRepositoryProtocol):
    """Implementation of notification repository."""
    
    async def create(self, notification: Notification) -> Result[Notification]:
        """
        Create a new notification.
        
        Args:
            notification: Notification to create
            
        Returns:
            Result containing the created notification or an error
        """
        try:
            # Convert to dictionary for database insertion
            notification_dict = {
                "id": notification.id.value,
                "title": notification.title,
                "message": notification.message,
                "recipients": [r.value for r in notification.recipients],
                "type": notification.type.value,
                "priority": notification.priority.value,
                "status": notification.status.value,
                "group_id": notification.group_id,
                "sender_id": notification.sender_id.value if notification.sender_id else None,
                "resource_type": notification.resource_type,
                "resource_id": notification.resource_id,
                "actions": notification.actions,
                "channels": list(notification.channels),
                "created_at": notification.created_at,
                "delivered_at": notification.delivered_at,
                "expires_at": notification.expires_at,
                "read_by": [r.value for r in notification.read_by],
                "metadata": notification.metadata
            }
            
            # Store in database
            query = """
                INSERT INTO notifications (
                    id, title, message, recipients, type, priority, status,
                    group_id, sender_id, resource_type, resource_id, actions,
                    channels, created_at, delivered_at, expires_at, read_by, metadata
                ) VALUES (
                    :id, :title, :message, :recipients, :type, :priority, :status,
                    :group_id, :sender_id, :resource_type, :resource_id, :actions,
                    :channels, :created_at, :delivered_at, :expires_at, :read_by, :metadata
                )
                RETURNING *
            """
            
            await self.db.query_one(query, notification_dict)
            
            return Result.success(notification)
        except Exception as e:
            return Result.failure(f"Failed to create notification: {str(e)}")
    
    # Implement other methods as defined in the protocol...


class SubscriptionRepository(AsyncDomainRepository, SubscriptionRepositoryProtocol):
    """Implementation of subscription repository."""
    
    # Implement methods as defined in the protocol...
    

class ConnectionRepository(AsyncDomainRepository, ConnectionRepositoryProtocol):
    """Implementation of connection repository."""
    
    # Implement methods as defined in the protocol...
    

class MessageRepository(AsyncDomainRepository, MessageRepositoryProtocol):
    """Implementation of message repository."""
    
    # Implement methods as defined in the protocol...
    

class EventRepository(AsyncDomainRepository, EventRepositoryProtocol):
    """Implementation of event repository."""
    
    # Implement methods as defined in the protocol...