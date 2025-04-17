"""Notification storage system.

This module provides storage for notifications with query and retrieval capabilities.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple, AsyncIterator
from datetime import datetime, timedelta

from uno.realtime.notifications.notification import (
    Notification, 
    NotificationStatus,
    NotificationPriority
)
from uno.realtime.notifications.errors import (
    StorageError, 
    NotificationErrorCode
)


class NotificationStore(ABC):
    """Abstract base class for notification stores.
    
    This class defines the interface for notification storage implementations.
    Concrete implementations can store notifications in memory, database, etc.
    """
    
    @abstractmethod
    async def save(self, notification: Notification) -> str:
        """Save a notification to the store.
        
        Args:
            notification: The notification to save.
            
        Returns:
            The ID of the saved notification.
            
        Raises:
            StorageError: If the notification cannot be saved.
        """
        pass
    
    @abstractmethod
    async def get(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID.
        
        Args:
            notification_id: The ID of the notification.
            
        Returns:
            The notification if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def update(self, notification: Notification) -> bool:
        """Update an existing notification.
        
        Args:
            notification: The updated notification.
            
        Returns:
            True if the notification was updated, False if not found.
            
        Raises:
            StorageError: If the notification cannot be updated.
        """
        pass
    
    @abstractmethod
    async def delete(self, notification_id: str) -> bool:
        """Delete a notification.
        
        Args:
            notification_id: The ID of the notification to delete.
            
        Returns:
            True if the notification was deleted, False if not found.
        """
        pass
    
    @abstractmethod
    async def get_for_user(
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
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read by a user.
        
        Args:
            notification_id: The ID of the notification.
            user_id: The ID of the user.
            
        Returns:
            True if the notification was marked as read, False otherwise.
        """
        pass
    
    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The number of notifications marked as read.
        """
        pass
    
    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """Get the count of unread notifications for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The count of unread notifications.
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired notifications.
        
        Returns:
            The number of notifications cleaned up.
        """
        pass


class InMemoryNotificationStore(NotificationStore):
    """In-memory implementation of NotificationStore.
    
    This implementation stores notifications in memory and is suitable for
    development, testing, or small applications with no persistence requirements.
    """
    
    def __init__(self):
        """Initialize the in-memory notification store."""
        self._notifications: Dict[str, Notification] = {}
        self._user_notifications: Dict[str, Set[str]] = {}
        self._logger = logging.getLogger(__name__)
    
    async def save(self, notification: Notification) -> str:
        """Save a notification to the store.
        
        Args:
            notification: The notification to save.
            
        Returns:
            The ID of the saved notification.
        """
        # Store the notification
        self._notifications[notification.id] = notification
        
        # Update user-to-notifications mapping
        for user_id in notification.recipients:
            if user_id not in self._user_notifications:
                self._user_notifications[user_id] = set()
            self._user_notifications[user_id].add(notification.id)
        
        return notification.id
    
    async def get(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID.
        
        Args:
            notification_id: The ID of the notification.
            
        Returns:
            The notification if found, None otherwise.
        """
        return self._notifications.get(notification_id)
    
    async def update(self, notification: Notification) -> bool:
        """Update an existing notification.
        
        Args:
            notification: The updated notification.
            
        Returns:
            True if the notification was updated, False if not found.
        """
        if notification.id not in self._notifications:
            return False
        
        # Update the notification
        self._notifications[notification.id] = notification
        
        # Update user-to-notifications mapping
        # (in case recipients changed)
        old_recipients = set()
        for user_id, notifications in self._user_notifications.items():
            if notification.id in notifications:
                old_recipients.add(user_id)
        
        new_recipients = set(notification.recipients)
        
        # Remove notification from users who are no longer recipients
        for user_id in old_recipients - new_recipients:
            if user_id in self._user_notifications:
                self._user_notifications[user_id].discard(notification.id)
        
        # Add notification to new recipients
        for user_id in new_recipients - old_recipients:
            if user_id not in self._user_notifications:
                self._user_notifications[user_id] = set()
            self._user_notifications[user_id].add(notification.id)
        
        return True
    
    async def delete(self, notification_id: str) -> bool:
        """Delete a notification.
        
        Args:
            notification_id: The ID of the notification to delete.
            
        Returns:
            True if the notification was deleted, False if not found.
        """
        if notification_id not in self._notifications:
            return False
        
        # Remove from user-to-notifications mapping
        for user_id, notifications in self._user_notifications.items():
            notifications.discard(notification_id)
        
        # Remove the notification
        del self._notifications[notification_id]
        
        return True
    
    async def get_for_user(
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
        if user_id not in self._user_notifications:
            return []
        
        # Get all notification IDs for the user
        notification_ids = self._user_notifications[user_id]
        
        # Filter notifications based on the include_read parameter
        filtered_notifications = [
            self._notifications[nid] for nid in notification_ids
            if nid in self._notifications and (
                include_read or not self._notifications[nid].is_read_by(user_id)
            )
        ]
        
        # Sort by created_at (newest first)
        sorted_notifications = sorted(
            filtered_notifications,
            key=lambda n: n.created_at,
            reverse=True
        )
        
        # Apply pagination
        paginated = sorted_notifications[offset:offset + limit]
        
        return paginated
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read by a user.
        
        Args:
            notification_id: The ID of the notification.
            user_id: The ID of the user.
            
        Returns:
            True if the notification was marked as read, False otherwise.
        """
        notification = self._notifications.get(notification_id)
        
        if notification is None:
            return False
        
        if not notification.has_recipient(user_id):
            return False
        
        notification.mark_as_read(user_id)
        return True
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The number of notifications marked as read.
        """
        if user_id not in self._user_notifications:
            return 0
        
        count = 0
        for notification_id in self._user_notifications[user_id]:
            notification = self._notifications.get(notification_id)
            if notification and not notification.is_read_by(user_id):
                notification.mark_as_read(user_id)
                count += 1
        
        return count
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get the count of unread notifications for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The count of unread notifications.
        """
        if user_id not in self._user_notifications:
            return 0
        
        count = 0
        for notification_id in self._user_notifications[user_id]:
            notification = self._notifications.get(notification_id)
            if notification and not notification.is_read_by(user_id):
                count += 1
        
        return count
    
    async def cleanup_expired(self) -> int:
        """Clean up expired notifications.
        
        Returns:
            The number of notifications cleaned up.
        """
        now = datetime.now()
        expired_ids = [
            nid for nid, n in self._notifications.items()
            if n.is_expired() or n.status == NotificationStatus.EXPIRED
        ]
        
        count = 0
        for notification_id in expired_ids:
            if await self.delete(notification_id):
                count += 1
        
        return count


class PeriodicCleanupMixin:
    """Mixin for adding periodic cleanup to notification stores."""
    
    def __init__(
        self, 
        cleanup_interval: int = 3600,  # Default: 1 hour
        max_age_days: int = 30,        # Default: 30 days
        *args, 
        **kwargs
    ):
        """Initialize the periodic cleanup mixin.
        
        Args:
            cleanup_interval: Cleanup interval in seconds.
            max_age_days: Maximum age of notifications in days.
        """
        super().__init__(*args, **kwargs)
        self.cleanup_interval = cleanup_interval
        self.max_age_days = max_age_days
        self._cleanup_task = None
        self._logger = logging.getLogger(__name__)
    
    async def start_cleanup_task(self) -> None:
        """Start the periodic cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())  # type: ignore
    
    async def stop_cleanup_task(self) -> None:
        """Stop the periodic cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _periodic_cleanup(self) -> None:
        """Run the periodic cleanup task."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                try:
                    # Use the concrete implementation's method
                    if hasattr(self, 'cleanup_expired'):
                        count = await self.cleanup_expired()  # type: ignore
                        if count > 0:
                            self._logger.info(f"Cleaned up {count} expired notifications")
                except Exception as e:
                    self._logger.error(f"Error during notification cleanup: {e}")
        except asyncio.CancelledError:
            # Task was canceled, exit gracefully
            pass
        except Exception as e:
            self._logger.error(f"Unexpected error in notification cleanup task: {e}")
    
    async def cleanup_old_notifications(self) -> int:
        """Clean up notifications older than max_age_days.
        
        Returns:
            The number of notifications cleaned up.
        """
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # This method must be implemented by the actual store
        return await self._cleanup_old_notifications(cutoff_date)
    
    @abstractmethod
    async def _cleanup_old_notifications(self, cutoff_date: datetime) -> int:
        """Actual implementation to clean up old notifications.
        
        Args:
            cutoff_date: The cutoff date for notification age.
            
        Returns:
            The number of notifications cleaned up.
        """
        pass


class InMemoryNotificationStoreWithCleanup(PeriodicCleanupMixin, InMemoryNotificationStore):
    """In-memory notification store with periodic cleanup."""
    
    async def _cleanup_old_notifications(self, cutoff_date: datetime) -> int:
        """Clean up notifications older than the cutoff date.
        
        Args:
            cutoff_date: The cutoff date for notification age.
            
        Returns:
            The number of notifications cleaned up.
        """
        old_notification_ids = [
            nid for nid, n in self._notifications.items()
            if n.created_at < cutoff_date
        ]
        
        count = 0
        for notification_id in old_notification_ids:
            if await self.delete(notification_id):
                count += 1
        
        return count