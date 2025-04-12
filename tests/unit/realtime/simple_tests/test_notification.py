"""Simple tests for the notification classes."""

import unittest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set

from uno.realtime.notifications.notification import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    create_system_notification,
    create_user_notification,
    create_resource_notification
)
from uno.realtime.notifications.store import InMemoryNotificationStore
from uno.realtime.notifications.hub import (
    NotificationHub,
    DeliveryChannel,
    InAppDeliveryChannel
)


class TestNotification(unittest.TestCase):
    """Tests for the Notification class."""
    
    def test_notification_creation(self):
        """Test creating a Notification."""
        notification = Notification(
            title="Test Title",
            message="Test Message",
            recipients=["user1", "user2"],
            type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL
        )
        
        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.message, "Test Message")
        self.assertEqual(notification.recipients, ["user1", "user2"])
        self.assertEqual(notification.type, NotificationType.SYSTEM)
        self.assertEqual(notification.priority, NotificationPriority.NORMAL)
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertIsNotNone(notification.id)
    
    def test_notification_serialization(self):
        """Test serializing and deserializing notifications."""
        notification = Notification(
            title="Test Title",
            message="Test Message",
            recipients=["user1", "user2"],
            type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            channels={"in_app", "email"}
        )
        
        # Convert to dict
        data = notification.to_dict()
        
        # Check dict values
        self.assertEqual(data["title"], "Test Title")
        self.assertEqual(data["message"], "Test Message")
        self.assertEqual(data["recipients"], ["user1", "user2"])
        self.assertEqual(data["type"], "SYSTEM")
        self.assertEqual(data["priority"], "NORMAL")
        self.assertEqual(data["status"], "PENDING")
        self.assertIn("in_app", data["channels"])
        self.assertIn("email", data["channels"])
        
        # Convert back to notification
        new_notification = Notification.from_dict(data)
        
        # Check values after round-trip
        self.assertEqual(new_notification.title, notification.title)
        self.assertEqual(new_notification.message, notification.message)
        self.assertEqual(new_notification.recipients, notification.recipients)
        self.assertEqual(new_notification.type, notification.type)
        self.assertEqual(new_notification.priority, notification.priority)
        self.assertEqual(new_notification.status, notification.status)
        self.assertEqual(new_notification.channels, notification.channels)
    
    def test_notification_read_status(self):
        """Test notification read status tracking."""
        notification = Notification(
            title="Test Title",
            message="Test Message",
            recipients=["user1", "user2"],
        )
        
        # Initially unread
        self.assertFalse(notification.is_read_by("user1"))
        self.assertFalse(notification.is_read_by("user2"))
        self.assertNotEqual(notification.status, NotificationStatus.READ)
        
        # Mark as read by user1
        notification.mark_as_read("user1")
        self.assertTrue(notification.is_read_by("user1"))
        self.assertFalse(notification.is_read_by("user2"))
        self.assertNotEqual(notification.status, NotificationStatus.READ)
        
        # Mark as read by user2
        notification.mark_as_read("user2")
        self.assertTrue(notification.is_read_by("user1"))
        self.assertTrue(notification.is_read_by("user2"))
        self.assertEqual(notification.status, NotificationStatus.READ)  # All recipients read
    
    def test_factory_functions(self):
        """Test notification factory functions."""
        # System notification
        sys_notif = create_system_notification(
            title="System Alert",
            message="System maintenance scheduled",
            recipients=["user1", "user2"],
            priority=NotificationPriority.HIGH
        )
        
        self.assertEqual(sys_notif.type, NotificationType.SYSTEM)
        self.assertEqual(sys_notif.priority, NotificationPriority.HIGH)
        self.assertEqual(sys_notif.sender_id, "system")
        
        # User notification
        user_notif = create_user_notification(
            title="New Message",
            message="Hello there!",
            recipients=["user2"],
            sender_id="user1",
            type_=NotificationType.MESSAGE
        )
        
        self.assertEqual(user_notif.type, NotificationType.MESSAGE)
        self.assertEqual(user_notif.sender_id, "user1")
        
        # Resource notification
        res_notif = create_resource_notification(
            title="New Comment",
            message="Someone commented on your post",
            recipients=["user1"],
            resource_type="post",
            resource_id="post123",
            type_=NotificationType.COMMENT,
            sender_id="user2"
        )
        
        self.assertEqual(res_notif.type, NotificationType.COMMENT)
        self.assertEqual(res_notif.resource_type, "post")
        self.assertEqual(res_notif.resource_id, "post123")
        self.assertEqual(res_notif.sender_id, "user2")


class TestInMemoryNotificationStore(unittest.IsolatedAsyncioTestCase):
    """Tests for the InMemoryNotificationStore class."""
    
    async def test_save_and_get(self):
        """Test saving and retrieving notifications."""
        store = InMemoryNotificationStore()
        
        # Create a notification
        notification = Notification(
            title="Test Title",
            message="Test Message",
            recipients=["user1", "user2"]
        )
        
        # Save it
        notification_id = await store.save(notification)
        
        # Retrieve it
        retrieved = await store.get(notification_id)
        
        # Check it matches
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, notification.id)
        self.assertEqual(retrieved.title, notification.title)
        self.assertEqual(retrieved.message, notification.message)
    
    async def test_get_for_user(self):
        """Test retrieving notifications for a user."""
        store = InMemoryNotificationStore()
        
        # Create and save notifications for different users
        notif1 = Notification(
            title="For User 1",
            message="Message for User 1",
            recipients=["user1"]
        )
        
        notif2 = Notification(
            title="For Both Users",
            message="Message for Both Users",
            recipients=["user1", "user2"]
        )
        
        notif3 = Notification(
            title="For User 2",
            message="Message for User 2",
            recipients=["user2"]
        )
        
        await store.save(notif1)
        await store.save(notif2)
        await store.save(notif3)
        
        # Get notifications for user1
        user1_notifications = await store.get_for_user("user1")
        
        # Check results
        self.assertEqual(len(user1_notifications), 2)
        titles = [n.title for n in user1_notifications]
        self.assertIn("For User 1", titles)
        self.assertIn("For Both Users", titles)
        self.assertNotIn("For User 2", titles)
    
    async def test_mark_as_read(self):
        """Test marking notifications as read."""
        store = InMemoryNotificationStore()
        
        # Create a notification
        notification = Notification(
            title="Test Title",
            message="Test Message",
            recipients=["user1", "user2"]
        )
        
        # Save it
        notification_id = await store.save(notification)
        
        # Mark as read
        result = await store.mark_as_read(notification_id, "user1")
        self.assertTrue(result)
        
        # Get updated notification
        updated = await store.get(notification_id)
        
        # Check read status
        self.assertTrue(updated.is_read_by("user1"))
        self.assertFalse(updated.is_read_by("user2"))
    
    async def test_unread_count(self):
        """Test getting unread notification count."""
        store = InMemoryNotificationStore()
        
        # Create and save notifications for a user
        for i in range(5):
            notif = Notification(
                title=f"Notification {i}",
                message=f"Message {i}",
                recipients=["user1"]
            )
            await store.save(notif)
        
        # Check unread count
        count = await store.get_unread_count("user1")
        self.assertEqual(count, 5)
        
        # Mark one as read
        notifications = await store.get_for_user("user1")
        await store.mark_as_read(notifications[0].id, "user1")
        
        # Check count again
        count = await store.get_unread_count("user1")
        self.assertEqual(count, 4)
        
        # Mark all as read
        await store.mark_all_as_read("user1")
        
        # Check count again
        count = await store.get_unread_count("user1")
        self.assertEqual(count, 0)


class MockDeliveryChannel(DeliveryChannel):
    """Mock delivery channel for testing."""
    
    def __init__(self, channel_id: str = "mock"):
        self._channel_id = channel_id
        self.delivered: List[Notification] = []
    
    @property
    def channel_id(self) -> str:
        return self._channel_id
    
    async def deliver(self, notification: Notification) -> bool:
        self.delivered.append(notification)
        return True


class TestNotificationHub(unittest.IsolatedAsyncioTestCase):
    """Tests for the NotificationHub class."""
    
    async def test_notify(self):
        """Test sending a notification through the hub."""
        hub = NotificationHub()
        
        # Add a mock delivery channel
        mock_channel = MockDeliveryChannel()
        hub.register_delivery_channel(mock_channel)
        
        # Create a notification with specific channel
        notification = Notification(
            title="Test Title",
            message="Test Message",
            recipients=["user1"],
            channels={"mock"}
        )
        
        # Send it
        notification_id = await hub.notify(notification)
        
        # Check that the notification was delivered
        self.assertEqual(len(mock_channel.delivered), 1)
        self.assertEqual(mock_channel.delivered[0].id, notification_id)
        
        # Check that it was stored
        stored = await hub.get_notification(notification_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.status, NotificationStatus.DELIVERED)
    
    async def test_helper_methods(self):
        """Test notification helper methods."""
        hub = NotificationHub()
        
        # Add a mock delivery channel
        mock_channel = MockDeliveryChannel()
        hub.register_delivery_channel(mock_channel)
        
        # Send system notification
        sys_id = await hub.notify_system(
            title="System Alert",
            message="Test system message",
            recipients=["user1"],
            channels={"mock"}
        )
        
        # Send user notification
        user_id = await hub.notify_user(
            title="User Message",
            message="Test user message",
            recipients=["user1"],
            sender_id="user2",
            channels={"mock"}
        )
        
        # Send resource notification
        res_id = await hub.notify_resource(
            title="Resource Update",
            message="Test resource message",
            recipients=["user1"],
            resource_type="post",
            resource_id="post123",
            channels={"mock"}
        )
        
        # Check that all notifications were delivered
        self.assertEqual(len(mock_channel.delivered), 3)
        
        # Get notifications for user
        notifications = await hub.get_user_notifications("user1")
        self.assertEqual(len(notifications), 3)
        
        # Check titles
        titles = [n.title for n in notifications]
        self.assertIn("System Alert", titles)
        self.assertIn("User Message", titles)
        self.assertIn("Resource Update", titles)


if __name__ == "__main__":
    unittest.main()