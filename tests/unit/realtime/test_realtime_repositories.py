"""
Tests for the Realtime repositories.

This module contains tests for repository implementations in the realtime module.
"""

import pytest
import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional, Set

from uno.core.result import Result
from uno.realtime.entities import (
    # Value Objects
    ConnectionId, NotificationId, SubscriptionId, UserId,
    
    # Enums
    NotificationPriority, NotificationType, NotificationStatus,
    SubscriptionType, SubscriptionStatus, ConnectionState,
    MessageType, EventPriority,
    
    # Entities
    Notification, Subscription, Connection, Message, Event
)
from uno.realtime.domain_repositories import (
    NotificationRepositoryProtocol,
    SubscriptionRepositoryProtocol,
    ConnectionRepositoryProtocol,
    MessageRepositoryProtocol,
    EventRepositoryProtocol
)


# In-memory repository implementations for testing
class InMemoryNotificationRepository:
    """In-memory implementation of notification repository for testing."""
    
    def __init__(self):
        """Initialize the repository."""
        self.notifications: Dict[str, Notification] = {}
    
    async def create(self, notification: Notification) -> Result[Notification]:
        """Create a new notification."""
        self.notifications[notification.id.value] = notification
        return Result.success(notification)
    
    async def get_by_id(self, notification_id: NotificationId) -> Result[Notification]:
        """Get a notification by ID."""
        notification = self.notifications.get(notification_id.value)
        if notification:
            return Result.success(notification)
        return Result.failure(f"Notification with ID {notification_id.value} not found")
    
    async def update(self, notification: Notification) -> Result[Notification]:
        """Update a notification."""
        if notification.id.value not in self.notifications:
            return Result.failure(f"Notification with ID {notification.id.value} not found")
        self.notifications[notification.id.value] = notification
        return Result.success(notification)
    
    async def delete(self, notification_id: NotificationId) -> Result[bool]:
        """Delete a notification."""
        if notification_id.value not in self.notifications:
            return Result.success(False)
        del self.notifications[notification_id.value]
        return Result.success(True)
    
    async def get_by_user(
        self, 
        user_id: UserId, 
        status: Optional[NotificationStatus] = None, 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[Notification]]:
        """Get notifications for a specific user."""
        result = []
        for notification in self.notifications.values():
            if not notification.has_recipient(user_id):
                continue
            if status is not None and notification.status != status:
                continue
            result.append(notification)
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        return Result.success(result[start:end])
    
    async def mark_as_delivered(self, notification_id: NotificationId) -> Result[Notification]:
        """Mark a notification as delivered."""
        notification = self.notifications.get(notification_id.value)
        if not notification:
            return Result.failure(f"Notification with ID {notification_id.value} not found")
        notification.mark_as_delivered()
        return Result.success(notification)
    
    async def mark_as_read(
        self, 
        notification_id: NotificationId, 
        user_id: UserId
    ) -> Result[Notification]:
        """Mark a notification as read by a user."""
        notification = self.notifications.get(notification_id.value)
        if not notification:
            return Result.failure(f"Notification with ID {notification_id.value} not found")
        if not notification.has_recipient(user_id):
            return Result.failure(f"User {user_id.value} is not a recipient of this notification")
        notification.mark_as_read(user_id)
        return Result.success(notification)
    
    async def get_unread_count(self, user_id: UserId) -> Result[int]:
        """Get the count of unread notifications for a user."""
        count = 0
        for notification in self.notifications.values():
            if notification.has_recipient(user_id) and not notification.is_read_by(user_id):
                count += 1
        return Result.success(count)
    
    async def search(
        self, 
        query: Dict[str, Any], 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[Notification]]:
        """Search for notifications based on query parameters."""
        result = []
        for notification in self.notifications.values():
            match = True
            for key, value in query.items():
                if key == "recipients":
                    # Special handling for recipients
                    recipient_ids = [r.value for r in notification.recipients]
                    if value not in recipient_ids:
                        match = False
                        break
                elif hasattr(notification, key):
                    attr_value = getattr(notification, key)
                    # Handle Enum values
                    if hasattr(attr_value, "value"):
                        if attr_value.value != value:
                            match = False
                            break
                    # Handle normal values
                    elif attr_value != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                result.append(notification)
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        return Result.success(result[start:end])


class InMemorySubscriptionRepository:
    """In-memory implementation of subscription repository for testing."""
    
    def __init__(self):
        """Initialize the repository."""
        self.subscriptions: Dict[str, Subscription] = {}
    
    async def create(self, subscription: Subscription) -> Result[Subscription]:
        """Create a new subscription."""
        self.subscriptions[subscription.id.value] = subscription
        return Result.success(subscription)
    
    async def get_by_id(self, subscription_id: SubscriptionId) -> Result[Subscription]:
        """Get a subscription by ID."""
        subscription = self.subscriptions.get(subscription_id.value)
        if subscription:
            return Result.success(subscription)
        return Result.failure(f"Subscription with ID {subscription_id.value} not found")
    
    async def update(self, subscription: Subscription) -> Result[Subscription]:
        """Update a subscription."""
        if subscription.id.value not in self.subscriptions:
            return Result.failure(f"Subscription with ID {subscription.id.value} not found")
        self.subscriptions[subscription.id.value] = subscription
        return Result.success(subscription)
    
    async def delete(self, subscription_id: SubscriptionId) -> Result[bool]:
        """Delete a subscription."""
        if subscription_id.value not in self.subscriptions:
            return Result.success(False)
        del self.subscriptions[subscription_id.value]
        return Result.success(True)
    
    async def get_by_user(
        self, 
        user_id: UserId, 
        status: Optional[SubscriptionStatus] = None, 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[Subscription]]:
        """Get subscriptions for a specific user."""
        result = []
        for subscription in self.subscriptions.values():
            if subscription.user_id != user_id:
                continue
            if status is not None and subscription.status != status:
                continue
            result.append(subscription)
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        return Result.success(result[start:end])
    
    async def get_active_by_resource(
        self, 
        resource_id: str, 
        resource_type: Optional[str] = None
    ) -> Result[List[Subscription]]:
        """Get active subscriptions for a specific resource."""
        result = []
        for subscription in self.subscriptions.values():
            if not subscription.is_active():
                continue
            if subscription.type != SubscriptionType.RESOURCE:
                continue
            if subscription.resource_id != resource_id:
                continue
            if resource_type is not None and subscription.resource_type != resource_type:
                continue
            result.append(subscription)
        return Result.success(result)
    
    async def get_active_by_topic(self, topic: str) -> Result[List[Subscription]]:
        """Get active subscriptions for a specific topic."""
        result = []
        for subscription in self.subscriptions.values():
            if not subscription.is_active():
                continue
            if subscription.type != SubscriptionType.TOPIC:
                continue
            if subscription.topic != topic:
                continue
            result.append(subscription)
        return Result.success(result)
    
    async def update_status(
        self, 
        subscription_id: SubscriptionId, 
        status: SubscriptionStatus
    ) -> Result[Subscription]:
        """Update the status of a subscription."""
        subscription = self.subscriptions.get(subscription_id.value)
        if not subscription:
            return Result.failure(f"Subscription with ID {subscription_id.value} not found")
        subscription.update_status(status)
        return Result.success(subscription)
    
    async def find_matching_subscriptions(
        self, 
        event_data: Dict[str, Any]
    ) -> Result[List[Subscription]]:
        """Find subscriptions that match the given event data."""
        result = []
        for subscription in self.subscriptions.values():
            if subscription.matches_event(event_data):
                result.append(subscription)
        return Result.success(result)
    
    async def cleanup_expired_subscriptions(self) -> Result[int]:
        """Clean up expired subscriptions."""
        expired_ids = []
        for subscription_id, subscription in self.subscriptions.items():
            if subscription.is_expired():
                expired_ids.append(subscription_id)
        
        for subscription_id in expired_ids:
            del self.subscriptions[subscription_id]
        
        return Result.success(len(expired_ids))


# Fixtures
@pytest.fixture
def notification_id() -> NotificationId:
    """Create a test notification ID."""
    return NotificationId(value=str(uuid.uuid4()))


@pytest.fixture
def user_id() -> UserId:
    """Create a test user ID."""
    return UserId(value=str(uuid.uuid4()))


@pytest.fixture
def user_ids() -> List[UserId]:
    """Create a list of test user IDs."""
    return [UserId(value=str(uuid.uuid4())) for _ in range(3)]


@pytest.fixture
def notification(notification_id: NotificationId, user_ids: List[UserId]) -> Notification:
    """Create a test notification."""
    return Notification(
        id=notification_id,
        title="Test Notification",
        message="This is a test notification",
        recipients=user_ids,
        type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL,
        metadata={"source": "test"}
    )


@pytest.fixture
def subscription_id() -> SubscriptionId:
    """Create a test subscription ID."""
    return SubscriptionId(value=str(uuid.uuid4()))


@pytest.fixture
def subscription(subscription_id: SubscriptionId, user_id: UserId) -> Subscription:
    """Create a test subscription."""
    return Subscription(
        id=subscription_id,
        user_id=user_id,
        type=SubscriptionType.RESOURCE,
        resource_id="resource-123",
        resource_type="document",
        labels={"important", "document"}
    )


@pytest.fixture
def notification_repo() -> InMemoryNotificationRepository:
    """Create a test notification repository."""
    return InMemoryNotificationRepository()


@pytest.fixture
def subscription_repo() -> InMemorySubscriptionRepository:
    """Create a test subscription repository."""
    return InMemorySubscriptionRepository()


class TestNotificationRepository:
    """Tests for NotificationRepository."""
    
    @pytest.mark.asyncio
    async def test_create(self, notification_repo: InMemoryNotificationRepository, notification: Notification):
        """Test creating a notification."""
        # Act
        result = await notification_repo.create(notification)
        
        # Assert
        assert result.is_success()
        assert result.value == notification
        
        # Verify stored in repository
        get_result = await notification_repo.get_by_id(notification.id)
        assert get_result.is_success()
        assert get_result.value == notification
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, notification_repo: InMemoryNotificationRepository):
        """Test getting a non-existent notification."""
        # Arrange
        notification_id = NotificationId(value=str(uuid.uuid4()))
        
        # Act
        result = await notification_repo.get_by_id(notification_id)
        
        # Assert
        assert not result.is_success()
        assert f"Notification with ID {notification_id.value} not found" in result.error
    
    @pytest.mark.asyncio
    async def test_update(self, notification_repo: InMemoryNotificationRepository, notification: Notification):
        """Test updating a notification."""
        # Arrange
        await notification_repo.create(notification)
        
        # Modify the notification
        notification.title = "Updated Title"
        
        # Act
        result = await notification_repo.update(notification)
        
        # Assert
        assert result.is_success()
        assert result.value.title == "Updated Title"
        
        # Verify stored in repository
        get_result = await notification_repo.get_by_id(notification.id)
        assert get_result.is_success()
        assert get_result.value.title == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_delete(self, notification_repo: InMemoryNotificationRepository, notification: Notification):
        """Test deleting a notification."""
        # Arrange
        await notification_repo.create(notification)
        
        # Act
        result = await notification_repo.delete(notification.id)
        
        # Assert
        assert result.is_success()
        assert result.value is True
        
        # Verify removed from repository
        get_result = await notification_repo.get_by_id(notification.id)
        assert not get_result.is_success()
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, notification_repo: InMemoryNotificationRepository):
        """Test deleting a non-existent notification."""
        # Arrange
        notification_id = NotificationId(value=str(uuid.uuid4()))
        
        # Act
        result = await notification_repo.delete(notification_id)
        
        # Assert
        assert result.is_success()
        assert result.value is False  # Not found, so nothing deleted
    
    @pytest.mark.asyncio
    async def test_get_by_user(self, notification_repo: InMemoryNotificationRepository, notification: Notification, user_ids: List[UserId]):
        """Test getting notifications for a user."""
        # Arrange
        await notification_repo.create(notification)
        
        # Create another notification for the same user
        notification2 = Notification(
            id=NotificationId(value=str(uuid.uuid4())),
            title="Another Notification",
            message="This is another test notification",
            recipients=[user_ids[0]],  # Only for the first user
            type=NotificationType.MESSAGE
        )
        await notification_repo.create(notification2)
        
        # Act - get notifications for the first user
        result = await notification_repo.get_by_user(user_ids[0])
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 2
        assert notification in result.value
        assert notification2 in result.value
        
        # Act - get notifications for the second user
        result = await notification_repo.get_by_user(user_ids[1])
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert notification in result.value
        assert notification2 not in result.value
    
    @pytest.mark.asyncio
    async def test_get_by_user_with_status(self, notification_repo: InMemoryNotificationRepository, notification: Notification, user_ids: List[UserId]):
        """Test getting notifications for a user with status filter."""
        # Arrange
        await notification_repo.create(notification)
        
        # Create a delivered notification
        notification2 = Notification(
            id=NotificationId(value=str(uuid.uuid4())),
            title="Delivered Notification",
            message="This notification has been delivered",
            recipients=user_ids,
            status=NotificationStatus.DELIVERED
        )
        await notification_repo.create(notification2)
        
        # Act - get pending notifications
        result = await notification_repo.get_by_user(user_ids[0], status=NotificationStatus.PENDING)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert notification in result.value
        
        # Act - get delivered notifications
        result = await notification_repo.get_by_user(user_ids[0], status=NotificationStatus.DELIVERED)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert notification2 in result.value
    
    @pytest.mark.asyncio
    async def test_mark_as_delivered(self, notification_repo: InMemoryNotificationRepository, notification: Notification):
        """Test marking a notification as delivered."""
        # Arrange
        await notification_repo.create(notification)
        
        # Act
        result = await notification_repo.mark_as_delivered(notification.id)
        
        # Assert
        assert result.is_success()
        assert result.value.status == NotificationStatus.DELIVERED
        assert result.value.delivered_at is not None
        
        # Verify stored in repository
        get_result = await notification_repo.get_by_id(notification.id)
        assert get_result.is_success()
        assert get_result.value.status == NotificationStatus.DELIVERED
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, notification_repo: InMemoryNotificationRepository, notification: Notification, user_ids: List[UserId]):
        """Test marking a notification as read by a user."""
        # Arrange
        await notification_repo.create(notification)
        
        # Act
        result = await notification_repo.mark_as_read(notification.id, user_ids[0])
        
        # Assert
        assert result.is_success()
        assert user_ids[0] in result.value.read_by
        
        # Verify stored in repository
        get_result = await notification_repo.get_by_id(notification.id)
        assert get_result.is_success()
        assert user_ids[0] in get_result.value.read_by
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, notification_repo: InMemoryNotificationRepository, notification: Notification, user_ids: List[UserId]):
        """Test getting the unread notification count for a user."""
        # Arrange
        await notification_repo.create(notification)
        
        # Create another notification
        notification2 = Notification(
            id=NotificationId(value=str(uuid.uuid4())),
            title="Another Notification",
            message="This is another test notification",
            recipients=user_ids
        )
        await notification_repo.create(notification2)
        
        # Mark the first notification as read by the first user
        await notification_repo.mark_as_read(notification.id, user_ids[0])
        
        # Act - get unread count for the first user
        result = await notification_repo.get_unread_count(user_ids[0])
        
        # Assert
        assert result.is_success()
        assert result.value == 1  # Only notification2 is unread
        
        # Act - get unread count for the second user
        result = await notification_repo.get_unread_count(user_ids[1])
        
        # Assert
        assert result.is_success()
        assert result.value == 2  # Both notifications are unread
    
    @pytest.mark.asyncio
    async def test_search(self, notification_repo: InMemoryNotificationRepository, notification: Notification, user_ids: List[UserId]):
        """Test searching for notifications."""
        # Arrange
        await notification_repo.create(notification)
        
        # Create additional notifications
        notification2 = Notification(
            id=NotificationId(value=str(uuid.uuid4())),
            title="High Priority",
            message="This is a high priority notification",
            recipients=user_ids,
            priority=NotificationPriority.HIGH
        )
        await notification_repo.create(notification2)
        
        notification3 = Notification(
            id=NotificationId(value=str(uuid.uuid4())),
            title="Security Alert",
            message="This is a security notification",
            recipients=user_ids,
            type=NotificationType.SECURITY
        )
        await notification_repo.create(notification3)
        
        # Act - search by priority
        result = await notification_repo.search({"priority": NotificationPriority.HIGH.value})
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert result.value[0].id == notification2.id
        
        # Act - search by type
        result = await notification_repo.search({"type": NotificationType.SECURITY.value})
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert result.value[0].id == notification3.id
        
        # Act - search by recipient
        result = await notification_repo.search({"recipients": user_ids[0].value})
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 3  # All notifications have this recipient


class TestSubscriptionRepository:
    """Tests for SubscriptionRepository."""
    
    @pytest.mark.asyncio
    async def test_create(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription):
        """Test creating a subscription."""
        # Act
        result = await subscription_repo.create(subscription)
        
        # Assert
        assert result.is_success()
        assert result.value == subscription
        
        # Verify stored in repository
        get_result = await subscription_repo.get_by_id(subscription.id)
        assert get_result.is_success()
        assert get_result.value == subscription
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, subscription_repo: InMemorySubscriptionRepository):
        """Test getting a non-existent subscription."""
        # Arrange
        subscription_id = SubscriptionId(value=str(uuid.uuid4()))
        
        # Act
        result = await subscription_repo.get_by_id(subscription_id)
        
        # Assert
        assert not result.is_success()
        assert f"Subscription with ID {subscription_id.value} not found" in result.error
    
    @pytest.mark.asyncio
    async def test_update(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription):
        """Test updating a subscription."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Add a label to the subscription
        subscription.add_label("urgent")
        
        # Act
        result = await subscription_repo.update(subscription)
        
        # Assert
        assert result.is_success()
        assert "urgent" in result.value.labels
        
        # Verify stored in repository
        get_result = await subscription_repo.get_by_id(subscription.id)
        assert get_result.is_success()
        assert "urgent" in get_result.value.labels
    
    @pytest.mark.asyncio
    async def test_delete(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription):
        """Test deleting a subscription."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Act
        result = await subscription_repo.delete(subscription.id)
        
        # Assert
        assert result.is_success()
        assert result.value is True
        
        # Verify removed from repository
        get_result = await subscription_repo.get_by_id(subscription.id)
        assert not get_result.is_success()
    
    @pytest.mark.asyncio
    async def test_get_by_user(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription, user_id: UserId):
        """Test getting subscriptions for a user."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Create another subscription for the same user
        subscription2 = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.TOPIC,
            topic="system-updates"
        )
        await subscription_repo.create(subscription2)
        
        # Create a subscription for a different user
        other_user_id = UserId(value=str(uuid.uuid4()))
        subscription3 = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=other_user_id,
            type=SubscriptionType.RESOURCE,
            resource_id="resource-456"
        )
        await subscription_repo.create(subscription3)
        
        # Act
        result = await subscription_repo.get_by_user(user_id)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 2
        assert subscription in result.value
        assert subscription2 in result.value
        assert subscription3 not in result.value
    
    @pytest.mark.asyncio
    async def test_get_by_user_with_status(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription, user_id: UserId):
        """Test getting subscriptions for a user with status filter."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Create an inactive subscription
        subscription2 = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.TOPIC,
            topic="system-updates",
            status=SubscriptionStatus.INACTIVE
        )
        await subscription_repo.create(subscription2)
        
        # Act - get active subscriptions
        result = await subscription_repo.get_by_user(user_id, status=SubscriptionStatus.ACTIVE)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert subscription in result.value
        
        # Act - get inactive subscriptions
        result = await subscription_repo.get_by_user(user_id, status=SubscriptionStatus.INACTIVE)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert subscription2 in result.value
    
    @pytest.mark.asyncio
    async def test_get_active_by_resource(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription):
        """Test getting active subscriptions for a resource."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Create an inactive subscription for the same resource
        inactive_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=UserId(value=str(uuid.uuid4())),
            type=SubscriptionType.RESOURCE,
            resource_id="resource-123",
            resource_type="document",
            status=SubscriptionStatus.INACTIVE
        )
        await subscription_repo.create(inactive_subscription)
        
        # Create an active subscription for a different resource
        other_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=UserId(value=str(uuid.uuid4())),
            type=SubscriptionType.RESOURCE,
            resource_id="resource-456",
            resource_type="document"
        )
        await subscription_repo.create(other_subscription)
        
        # Act - get subscriptions for resource-123
        result = await subscription_repo.get_active_by_resource("resource-123")
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert subscription in result.value
        
        # Act - get subscriptions for resource-123 with document type
        result = await subscription_repo.get_active_by_resource("resource-123", "document")
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert subscription in result.value
        
        # Act - get subscriptions for resource-123 with wrong type
        result = await subscription_repo.get_active_by_resource("resource-123", "image")
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 0
    
    @pytest.mark.asyncio
    async def test_get_active_by_topic(self, subscription_repo: InMemorySubscriptionRepository, user_id: UserId):
        """Test getting active subscriptions for a topic."""
        # Arrange
        topic_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.TOPIC,
            topic="system-updates"
        )
        await subscription_repo.create(topic_subscription)
        
        # Create an inactive subscription for the same topic
        inactive_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=UserId(value=str(uuid.uuid4())),
            type=SubscriptionType.TOPIC,
            topic="system-updates",
            status=SubscriptionStatus.INACTIVE
        )
        await subscription_repo.create(inactive_subscription)
        
        # Create an active subscription for a different topic
        other_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=UserId(value=str(uuid.uuid4())),
            type=SubscriptionType.TOPIC,
            topic="security-alerts"
        )
        await subscription_repo.create(other_subscription)
        
        # Act - get subscriptions for system-updates
        result = await subscription_repo.get_active_by_topic("system-updates")
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert topic_subscription in result.value
        
        # Act - get subscriptions for security-alerts
        result = await subscription_repo.get_active_by_topic("security-alerts")
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1
        assert other_subscription in result.value
    
    @pytest.mark.asyncio
    async def test_update_status(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription):
        """Test updating the status of a subscription."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Act
        result = await subscription_repo.update_status(subscription.id, SubscriptionStatus.PAUSED)
        
        # Assert
        assert result.is_success()
        assert result.value.status == SubscriptionStatus.PAUSED
        
        # Verify stored in repository
        get_result = await subscription_repo.get_by_id(subscription.id)
        assert get_result.is_success()
        assert get_result.value.status == SubscriptionStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_find_matching_subscriptions(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription, user_id: UserId):
        """Test finding subscriptions that match an event."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Create a topic subscription
        topic_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.TOPIC,
            topic="document-updates"
        )
        await subscription_repo.create(topic_subscription)
        
        # Create a query subscription
        query_subscription = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.QUERY,
            query={"resource_type": "document", "action": "update"}
        )
        await subscription_repo.create(query_subscription)
        
        # Create an event that matches the resource subscription
        resource_event = {
            "resource_id": "resource-123",
            "resource_type": "document",
            "action": "update"
        }
        
        # Act
        result = await subscription_repo.find_matching_subscriptions(resource_event)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1  # Only the resource subscription should match
        assert subscription in result.value
        
        # Create an event that matches the topic subscription
        topic_event = {
            "topic": "document-updates",
            "message": "Document update notification"
        }
        
        # Act
        result = await subscription_repo.find_matching_subscriptions(topic_event)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1  # Only the topic subscription should match
        assert topic_subscription in result.value
        
        # Create an event that matches the query subscription
        query_event = {
            "resource_type": "document",
            "action": "update",
            "status": "completed"
        }
        
        # Act
        result = await subscription_repo.find_matching_subscriptions(query_event)
        
        # Assert
        assert result.is_success()
        assert len(result.value) == 1  # Only the query subscription should match
        assert query_subscription in result.value
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_subscriptions(self, subscription_repo: InMemorySubscriptionRepository, subscription: Subscription, user_id: UserId):
        """Test cleaning up expired subscriptions."""
        # Arrange
        await subscription_repo.create(subscription)
        
        # Create an expired subscription (by status)
        expired_subscription1 = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.TOPIC,
            topic="expired-topic",
            status=SubscriptionStatus.EXPIRED
        )
        await subscription_repo.create(expired_subscription1)
        
        # Create an expired subscription (by date)
        expired_subscription2 = Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.RESOURCE,
            resource_id="expired-resource",
            expires_at=datetime.now(UTC) - timedelta(days=1)
        )
        await subscription_repo.create(expired_subscription2)
        
        # Act
        result = await subscription_repo.cleanup_expired_subscriptions()
        
        # Assert
        assert result.is_success()
        assert result.value == 2  # Two subscriptions were deleted
        
        # Verify the expired subscriptions are removed
        get_result1 = await subscription_repo.get_by_id(expired_subscription1.id)
        assert not get_result1.is_success()
        
        get_result2 = await subscription_repo.get_by_id(expired_subscription2.id)
        assert not get_result2.is_success()
        
        # Verify the active subscription is still there
        get_result3 = await subscription_repo.get_by_id(subscription.id)
        assert get_result3.is_success()