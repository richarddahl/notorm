"""Notification hub implementation.

This module provides the central notification hub for managing notifications.
"""

import asyncio
import logging
from typing import (
    Dict, List, Any, Optional, Set, Callable, Coroutine, 
    Union, TypeVar, Generic, Protocol, Awaitable
)
from datetime import datetime, timedelta

from uno.realtime.notifications.notification import (
    Notification,
    NotificationPriority, 
    NotificationStatus,
    NotificationType,
    create_system_notification,
    create_user_notification,
    create_resource_notification
)
from uno.realtime.notifications.store import (
    NotificationStore,
    InMemoryNotificationStoreWithCleanup
)
from uno.realtime.notifications.errors import (
    NotificationError,
    NotificationErrorCode,
    DeliveryError,
    ValidationError,
    RateLimitError
)


# Type for notification handler
NotificationHandler = Callable[[Notification], Awaitable[bool]]

# Type for notification filter
NotificationFilter = Callable[[Notification], Awaitable[bool]]


class DeliveryChannel(Protocol):
    """Protocol for notification delivery channels."""
    
    @property
    def channel_id(self) -> str:
        """Get the unique identifier for this channel."""
        ...
    
    async def deliver(self, notification: Notification) -> bool:
        """Deliver a notification through this channel.
        
        Args:
            notification: The notification to deliver.
            
        Returns:
            True if delivery was successful, False otherwise.
        """
        ...


class InAppDeliveryChannel:
    """Default in-app notification delivery channel."""
    
    @property
    def channel_id(self) -> str:
        """Get the unique identifier for this channel."""
        return "in_app"
    
    async def deliver(self, notification: Notification) -> bool:
        """Store the notification for in-app delivery.
        
        For in-app notifications, this is a no-op since they are
        already stored in the notification store.
        
        Args:
            notification: The notification to deliver.
            
        Returns:
            Always returns True for in-app notifications.
        """
        # Already stored in the notification store
        return True


class RateLimiter:
    """Rate limiter for notifications.
    
    Tracks and limits the number of notifications per user, per type,
    within a specified time window.
    """
    
    def __init__(
        self,
        max_per_minute: Optional[Dict[NotificationPriority, int]] = None,
        max_per_hour: Optional[Dict[NotificationPriority, int]] = None,
        max_per_day: Optional[Dict[NotificationPriority, int]] = None,
    ):
        """Initialize the rate limiter.
        
        Args:
            max_per_minute: Maximum notifications per minute by priority.
            max_per_hour: Maximum notifications per hour by priority.
            max_per_day: Maximum notifications per day by priority.
        """
        # Default limits by priority
        self.max_per_minute = max_per_minute or {
            NotificationPriority.LOW: 5,
            NotificationPriority.NORMAL: 10,
            NotificationPriority.HIGH: 20,
            NotificationPriority.URGENT: 30,
            NotificationPriority.EMERGENCY: 60,  # Essentially no limit
        }
        
        self.max_per_hour = max_per_hour or {
            NotificationPriority.LOW: 20,
            NotificationPriority.NORMAL: 40,
            NotificationPriority.HIGH: 60,
            NotificationPriority.URGENT: 120,
            NotificationPriority.EMERGENCY: 360,  # Essentially no limit
        }
        
        self.max_per_day = max_per_day or {
            NotificationPriority.LOW: 50,
            NotificationPriority.NORMAL: 100,
            NotificationPriority.HIGH: 200,
            NotificationPriority.URGENT: 500,
            NotificationPriority.EMERGENCY: 1000,  # Essentially no limit
        }
        
        # Tracking history: user_id -> notification_history
        self._history: Dict[str, List[datetime]] = {}
        
        # Tracking by type: user_id -> type -> notification_history
        self._type_history: Dict[str, Dict[NotificationType, List[datetime]]] = {}
        
        # Clean up expired tracking data periodically
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=10)
    
    def _get_user_history(self, user_id: str) -> List[datetime]:
        """Get notification history for a user.
        
        Args:
            user_id: The user ID.
            
        Returns:
            List of notification timestamps.
        """
        if user_id not in self._history:
            self._history[user_id] = []
        return self._history[user_id]
    
    def _get_user_type_history(
        self, user_id: str, notification_type: NotificationType
    ) -> List[datetime]:
        """Get notification history for a user and type.
        
        Args:
            user_id: The user ID.
            notification_type: The notification type.
            
        Returns:
            List of notification timestamps.
        """
        if user_id not in self._type_history:
            self._type_history[user_id] = {}
        
        if notification_type not in self._type_history[user_id]:
            self._type_history[user_id][notification_type] = []
        
        return self._type_history[user_id][notification_type]
    
    def _cleanup_old_entries(self) -> None:
        """Clean up old history entries."""
        now = datetime.now()
        
        # Only run cleanup at intervals
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        
        # Cut-off time is the oldest time that matters for any limit
        cutoff = now - timedelta(days=1)
        
        # Clean up user history
        for user_id in list(self._history.keys()):
            self._history[user_id] = [
                ts for ts in self._history[user_id] if ts > cutoff
            ]
        
        # Clean up type history
        for user_id in list(self._type_history.keys()):
            for notification_type in list(self._type_history[user_id].keys()):
                self._type_history[user_id][notification_type] = [
                    ts for ts in self._type_history[user_id][notification_type] 
                    if ts > cutoff
                ]
    
    def check_rate_limit(self, notification: Notification) -> bool:
        """Check if a notification would exceed rate limits.
        
        Args:
            notification: The notification to check.
            
        Returns:
            True if the notification would exceed rate limits, False otherwise.
        """
        self._cleanup_old_entries()
        
        now = datetime.now()
        priority = notification.priority
        
        # Check each recipient separately
        for user_id in notification.recipients:
            user_history = self._get_user_history(user_id)
            type_history = self._get_user_type_history(user_id, notification.type)
            
            # Count notifications in each time window
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            count_minute = sum(1 for ts in user_history if ts > minute_ago)
            count_hour = sum(1 for ts in user_history if ts > hour_ago)
            count_day = sum(1 for ts in user_history if ts > day_ago)
            
            # Check against limits
            if count_minute >= self.max_per_minute[priority]:
                return True
            
            if count_hour >= self.max_per_hour[priority]:
                return True
            
            if count_day >= self.max_per_day[priority]:
                return True
            
            # For Emergency priority, don't apply type-specific limits
            if priority != NotificationPriority.EMERGENCY:
                # Check for excessive notifications of the same type
                type_count_minute = sum(1 for ts in type_history if ts > minute_ago)
                type_count_hour = sum(1 for ts in type_history if ts > hour_ago)
                
                # Type-specific limits (more restrictive)
                if type_count_minute >= max(2, self.max_per_minute[priority] // 2):
                    return True
                
                if type_count_hour >= max(5, self.max_per_hour[priority] // 2):
                    return True
        
        return False
    
    def record_notification(self, notification: Notification) -> None:
        """Record a notification delivery for rate limiting.
        
        Args:
            notification: The delivered notification.
        """
        now = datetime.now()
        
        # Record for each recipient
        for user_id in notification.recipients:
            user_history = self._get_user_history(user_id)
            user_history.append(now)
            
            type_history = self._get_user_type_history(user_id, notification.type)
            type_history.append(now)


class NotificationHub:
    """Central hub for managing notifications.
    
    The NotificationHub is responsible for:
    - Creating and storing notifications
    - Managing delivery to different channels
    - Handling notification lifecycle
    - Filtering and prioritizing notifications
    """
    
    def __init__(
        self,
        store: Optional[NotificationStore] = None,
        rate_limiter: Optional[RateLimiter] = None,
        delivery_timeout: float = 5.0,
        enable_rate_limiting: bool = True
    ):
        """Initialize the notification hub.
        
        Args:
            store: The notification store to use.
            rate_limiter: The rate limiter to use.
            delivery_timeout: Timeout for delivery operations in seconds.
            enable_rate_limiting: Whether to enable rate limiting.
        """
        # Initialize logger first so it's available to all methods
        self._logger = logging.getLogger(__name__)
        
        self._store = store or InMemoryNotificationStoreWithCleanup()
        self._rate_limiter = rate_limiter or RateLimiter()
        self._delivery_timeout = delivery_timeout
        self._enable_rate_limiting = enable_rate_limiting
        
        # Delivery channels by ID
        self._delivery_channels: Dict[str, DeliveryChannel] = {}
        
        # Add default in-app channel
        self.register_delivery_channel(InAppDeliveryChannel())
        
        # Notification hooks
        self._pre_notification_hooks: List[NotificationFilter] = []
        self._post_notification_hooks: List[NotificationHandler] = []
    
    @property
    def store(self) -> NotificationStore:
        """Get the notification store."""
        return self._store
    
    def register_delivery_channel(self, channel: DeliveryChannel) -> None:
        """Register a delivery channel.
        
        Args:
            channel: The delivery channel to register.
        """
        self._delivery_channels[channel.channel_id] = channel
        self._logger.info(f"Registered delivery channel: {channel.channel_id}")
    
    def unregister_delivery_channel(self, channel_id: str) -> bool:
        """Unregister a delivery channel.
        
        Args:
            channel_id: The ID of the channel to unregister.
            
        Returns:
            True if the channel was unregistered, False if not found.
        """
        if channel_id in self._delivery_channels:
            del self._delivery_channels[channel_id]
            self._logger.info(f"Unregistered delivery channel: {channel_id}")
            return True
        return False
    
    def add_pre_notification_hook(self, hook: NotificationFilter) -> None:
        """Add a hook to run before delivering a notification.
        
        Pre-notification hooks can filter notifications before delivery.
        If any hook returns False, the notification will not be delivered.
        
        Args:
            hook: The hook function to add.
        """
        self._pre_notification_hooks.append(hook)
    
    def add_post_notification_hook(self, hook: NotificationHandler) -> None:
        """Add a hook to run after delivering a notification.
        
        Post-notification hooks are called after successful delivery.
        
        Args:
            hook: The hook function to add.
        """
        self._post_notification_hooks.append(hook)
    
    async def notify(self, notification: Notification) -> str:
        """Create and deliver a notification.
        
        Args:
            notification: The notification to deliver.
            
        Returns:
            The ID of the created notification.
            
        Raises:
            ValidationError: If the notification is invalid.
            RateLimitError: If rate limits would be exceeded.
            DeliveryError: If delivery fails.
        """
        # Validate notification
        if not notification.title or not notification.message:
            raise ValidationError(
                NotificationErrorCode.INVALID_NOTIFICATION,
                "Notification must have a title and message"
            )
        
        if not notification.recipients:
            raise ValidationError(
                NotificationErrorCode.INVALID_RECIPIENT,
                "Notification must have at least one recipient"
            )
        
        # Check rate limits
        if self._enable_rate_limiting and self._rate_limiter.check_rate_limit(notification):
            raise RateLimitError(
                NotificationErrorCode.RATE_LIMITED,
                "Rate limit exceeded for notification"
            )
        
        # Run pre-notification hooks
        for hook in self._pre_notification_hooks:
            try:
                allow = await hook(notification)
                if not allow:
                    raise NotificationError(
                        NotificationErrorCode.NOTIFICATION_REJECTED,
                        "Notification rejected by pre-notification hook"
                    )
            except Exception as e:
                self._logger.error(f"Error in pre-notification hook: {e}")
                # Continue with other hooks
        
        # Store the notification
        notification_id = await self._store.save(notification)
        
        try:
            # Deliver the notification to each channel
            delivery_channels = set()
            for channel_id in notification.channels:
                if channel_id in self._delivery_channels:
                    delivery_channels.add(channel_id)
            
            if not delivery_channels:
                # Default to in-app if no channels or no valid channels
                if "in_app" in self._delivery_channels:
                    delivery_channels.add("in_app")
            
            if not delivery_channels:
                raise DeliveryError(
                    NotificationErrorCode.INVALID_CHANNEL,
                    "No valid delivery channels available"
                )
            
            # Deliver to each channel
            delivery_tasks = []
            for channel_id in delivery_channels:
                channel = self._delivery_channels[channel_id]
                delivery_tasks.append(self._deliver_to_channel(notification, channel))
            
            # Wait for all deliveries with timeout
            if delivery_tasks:
                results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
                
                # Check for delivery failures
                all_failed = True
                for result in results:
                    if isinstance(result, Exception):
                        self._logger.error(f"Delivery error: {result}")
                    elif result is True:
                        all_failed = False
                
                if all_failed and results:
                    raise DeliveryError(
                        NotificationErrorCode.DELIVERY_FAILED,
                        "Failed to deliver notification to any channel"
                    )
            
            # Mark as delivered
            notification.mark_as_delivered()
            await self._store.update(notification)
            
            # Record for rate limiting
            if self._enable_rate_limiting:
                self._rate_limiter.record_notification(notification)
            
            # Run post-notification hooks
            for hook in self._post_notification_hooks:
                try:
                    await hook(notification)
                except Exception as e:
                    self._logger.error(f"Error in post-notification hook: {e}")
                    # Continue with other hooks
            
            return notification_id
        
        except Exception as e:
            # Update the notification status to FAILED
            notification.status = NotificationStatus.FAILED
            await self._store.update(notification)
            
            # Re-raise the exception
            if isinstance(e, NotificationError):
                raise
            
            raise DeliveryError(
                NotificationErrorCode.DELIVERY_FAILED,
                f"Failed to deliver notification: {str(e)}"
            )
    
    async def _deliver_to_channel(
        self, notification: Notification, channel: DeliveryChannel
    ) -> bool:
        """Deliver a notification to a specific channel with timeout.
        
        Args:
            notification: The notification to deliver.
            channel: The delivery channel.
            
        Returns:
            True if delivery was successful, False otherwise.
            
        Raises:
            DeliveryError: If delivery times out.
        """
        try:
            return await asyncio.wait_for(
                channel.deliver(notification),
                timeout=self._delivery_timeout
            )
        except asyncio.TimeoutError:
            self._logger.error(
                f"Delivery timeout for channel {channel.channel_id}"
            )
            raise DeliveryError(
                NotificationErrorCode.DELIVERY_TIMEOUT,
                f"Delivery timeout for channel {channel.channel_id}"
            )
    
    async def notify_system(
        self,
        title: str,
        message: str,
        recipients: List[str],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        actions: Optional[List[Dict[str, Any]]] = None,
        channels: Optional[Set[str]] = None
    ) -> str:
        """Send a system notification.
        
        Args:
            title: The notification title.
            message: The notification message.
            recipients: List of recipient user IDs.
            priority: The notification priority.
            actions: Optional list of actions.
            channels: Optional set of delivery channels.
            
        Returns:
            The ID of the created notification.
        """
        notification = create_system_notification(
            title=title,
            message=message,
            recipients=recipients,
            priority=priority,
            actions=actions or []
        )
        
        if channels:
            notification.channels = channels
        
        return await self.notify(notification)
    
    async def notify_user(
        self,
        title: str,
        message: str,
        recipients: List[str],
        sender_id: str,
        type_: NotificationType = NotificationType.MESSAGE,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        actions: Optional[List[Dict[str, Any]]] = None,
        channels: Optional[Set[str]] = None
    ) -> str:
        """Send a user-to-user notification.
        
        Args:
            title: The notification title.
            message: The notification message.
            recipients: List of recipient user IDs.
            sender_id: The ID of the sending user.
            type_: The notification type.
            priority: The notification priority.
            actions: Optional list of actions.
            channels: Optional set of delivery channels.
            
        Returns:
            The ID of the created notification.
        """
        notification = create_user_notification(
            title=title,
            message=message,
            recipients=recipients,
            sender_id=sender_id,
            type_=type_,
            priority=priority,
            actions=actions or []
        )
        
        if channels:
            notification.channels = channels
        
        return await self.notify(notification)
    
    async def notify_resource(
        self,
        title: str,
        message: str,
        recipients: List[str],
        resource_type: str,
        resource_id: str,
        type_: NotificationType = NotificationType.UPDATE,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        sender_id: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        channels: Optional[Set[str]] = None
    ) -> str:
        """Send a resource notification.
        
        Args:
            title: The notification title.
            message: The notification message.
            recipients: List of recipient user IDs.
            resource_type: The type of resource.
            resource_id: The ID of the resource.
            type_: The notification type.
            priority: The notification priority.
            sender_id: Optional ID of the sending user.
            actions: Optional list of actions.
            channels: Optional set of delivery channels.
            
        Returns:
            The ID of the created notification.
        """
        notification = create_resource_notification(
            title=title,
            message=message,
            recipients=recipients,
            resource_type=resource_type,
            resource_id=resource_id,
            type_=type_,
            priority=priority,
            sender_id=sender_id,
            actions=actions or []
        )
        
        if channels:
            notification.channels = channels
        
        return await self.notify(notification)
    
    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID.
        
        Args:
            notification_id: The ID of the notification.
            
        Returns:
            The notification if found, None otherwise.
        """
        return await self._store.get(notification_id)
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        include_read: bool = False
    ) -> List[Notification]:
        """Get notifications for a specific user.
        
        Args:
            user_id: The ID of the user.
            limit: Maximum number of notifications to return.
            offset: Offset for pagination.
            include_read: Whether to include read notifications.
            
        Returns:
            List of notifications for the user.
        """
        return await self._store.get_for_user(
            user_id, limit, offset, include_read
        )
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read by a user.
        
        Args:
            notification_id: The ID of the notification.
            user_id: The ID of the user.
            
        Returns:
            True if the notification was marked as read, False otherwise.
        """
        return await self._store.mark_as_read(notification_id, user_id)
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The number of notifications marked as read.
        """
        return await self._store.mark_all_as_read(user_id)
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get the count of unread notifications for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The count of unread notifications.
        """
        return await self._store.get_unread_count(user_id)
    
    async def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification.
        
        Args:
            notification_id: The ID of the notification to delete.
            
        Returns:
            True if the notification was deleted, False if not found.
        """
        return await self._store.delete(notification_id)


# Integration with WebSocket and SSE

class WebSocketNotificationChannel(DeliveryChannel):
    """WebSocket delivery channel for notifications."""
    
    def __init__(self, websocket_manager):
        """Initialize with a WebSocket manager.
        
        Args:
            websocket_manager: The WebSocket manager instance.
        """
        from uno.realtime.websocket import WebSocketManager
        self._websocket_manager = websocket_manager
    
    @property
    def channel_id(self) -> str:
        """Get the unique identifier for this channel."""
        return "websocket"
    
    async def deliver(self, notification: Notification) -> bool:
        """Deliver a notification through WebSocket.
        
        Args:
            notification: The notification to deliver.
            
        Returns:
            True if at least one recipient received the notification.
        """
        from uno.realtime.websocket.message import create_notification_message
        
        # Create a WebSocket notification message
        ws_message = create_notification_message(
            title=notification.title,
            message=notification.message,
            level=self._get_level(notification.priority),
            actions=notification.actions
        )
        
        # Broadcast to recipients
        count = await self._websocket_manager.broadcast_to_users(
            ws_message,
            user_ids=notification.recipients
        )
        
        return count > 0
    
    def _get_level(self, priority: NotificationPriority) -> str:
        """Map notification priority to WebSocket message level.
        
        Args:
            priority: The notification priority.
            
        Returns:
            The corresponding message level string.
        """
        level_map = {
            NotificationPriority.LOW: "info",
            NotificationPriority.NORMAL: "info",
            NotificationPriority.HIGH: "warning",
            NotificationPriority.URGENT: "error",
            NotificationPriority.EMERGENCY: "error"
        }
        return level_map.get(priority, "info")


class SSENotificationChannel(DeliveryChannel):
    """Server-Sent Events delivery channel for notifications."""
    
    def __init__(self, sse_manager):
        """Initialize with an SSE manager.
        
        Args:
            sse_manager: The SSE manager instance.
        """
        from uno.realtime.sse import SSEManager
        self._sse_manager = sse_manager
    
    @property
    def channel_id(self) -> str:
        """Get the unique identifier for this channel."""
        return "sse"
    
    async def deliver(self, notification: Notification) -> bool:
        """Deliver a notification through SSE.
        
        Args:
            notification: The notification to deliver.
            
        Returns:
            True if at least one recipient received the notification.
        """
        from uno.realtime.sse.event import create_notification_event, EventPriority
        
        # Map notification priority to SSE event priority
        priority_map = {
            NotificationPriority.LOW: EventPriority.LOW,
            NotificationPriority.NORMAL: EventPriority.NORMAL,
            NotificationPriority.HIGH: EventPriority.HIGH,
            NotificationPriority.URGENT: EventPriority.HIGHEST,
            NotificationPriority.EMERGENCY: EventPriority.CRITICAL
        }
        
        # Create an SSE notification event
        count = await self._sse_manager.broadcast_notification(
            title=notification.title,
            message=notification.message,
            level=self._get_level(notification.priority),
            actions=notification.actions,
            user_ids=notification.recipients,
            priority=priority_map.get(notification.priority, EventPriority.NORMAL)
        )
        
        return count > 0
    
    def _get_level(self, priority: NotificationPriority) -> str:
        """Map notification priority to SSE event level.
        
        Args:
            priority: The notification priority.
            
        Returns:
            The corresponding event level string.
        """
        level_map = {
            NotificationPriority.LOW: "info",
            NotificationPriority.NORMAL: "info",
            NotificationPriority.HIGH: "warning",
            NotificationPriority.URGENT: "error",
            NotificationPriority.EMERGENCY: "error"
        }
        return level_map.get(priority, "info")