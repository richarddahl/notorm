"""
Tests for the Realtime domain entities.

This module contains tests for the domain entities in the realtime module.
"""

import json
import uuid
import pytest
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional, Set

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


class TestValueObjects:
    """Tests for value objects."""
    
    def test_connection_id(self):
        """Test ConnectionId creation."""
        # Arrange
        value = str(uuid.uuid4())
        
        # Act
        connection_id = ConnectionId(value=value)
        
        # Assert
        assert connection_id.value == value
        assert str(connection_id) == value
    
    def test_notification_id(self):
        """Test NotificationId creation."""
        # Arrange
        value = str(uuid.uuid4())
        
        # Act
        notification_id = NotificationId(value=value)
        
        # Assert
        assert notification_id.value == value
        assert str(notification_id) == value
    
    def test_subscription_id(self):
        """Test SubscriptionId creation."""
        # Arrange
        value = str(uuid.uuid4())
        
        # Act
        subscription_id = SubscriptionId(value=value)
        
        # Assert
        assert subscription_id.value == value
        assert str(subscription_id) == value
    
    def test_user_id(self):
        """Test UserId creation."""
        # Arrange
        value = str(uuid.uuid4())
        
        # Act
        user_id = UserId(value=value)
        
        # Assert
        assert user_id.value == value
        assert str(user_id) == value
    
    def test_equality(self):
        """Test value object equality."""
        # Arrange
        value1 = str(uuid.uuid4())
        value2 = str(uuid.uuid4())
        
        # Act
        id1a = UserId(value=value1)
        id1b = UserId(value=value1)
        id2 = UserId(value=value2)
        
        # Assert
        assert id1a == id1b
        assert id1a != id2
        assert hash(id1a) == hash(id1b)
        assert hash(id1a) != hash(id2)


class TestNotification:
    """Tests for Notification entity."""
    
    @pytest.fixture
    def notification_id(self) -> NotificationId:
        """Create a test notification ID."""
        return NotificationId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def user_ids(self) -> List[UserId]:
        """Create a list of test user IDs."""
        return [UserId(value=str(uuid.uuid4())) for _ in range(3)]
    
    @pytest.fixture
    def notification(self, notification_id: NotificationId, user_ids: List[UserId]) -> Notification:
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
    
    def test_notification_creation(self, notification: Notification, notification_id: NotificationId, user_ids: List[UserId]):
        """Test creating a notification."""
        # Assert
        assert notification.id == notification_id
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.recipients == user_ids
        assert notification.type == NotificationType.SYSTEM
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.status == NotificationStatus.PENDING
        assert notification.metadata == {"source": "test"}
        assert "in_app" in notification.channels
        assert notification.created_at is not None
        assert notification.delivered_at is None
        assert notification.expires_at is None
        assert len(notification.read_by) == 0
    
    def test_mark_as_delivered(self, notification: Notification):
        """Test marking a notification as delivered."""
        # Act
        notification.mark_as_delivered()
        
        # Assert
        assert notification.status == NotificationStatus.DELIVERED
        assert notification.delivered_at is not None
    
    def test_mark_as_read(self, notification: Notification, user_ids: List[UserId]):
        """Test marking a notification as read."""
        # Act
        notification.mark_as_read(user_ids[0])
        
        # Assert
        assert user_ids[0] in notification.read_by
        assert notification.status == NotificationStatus.PENDING  # Not all users have read it
        
        # Act - mark as read by all users
        for user_id in user_ids[1:]:
            notification.mark_as_read(user_id)
        
        # Assert
        assert notification.status == NotificationStatus.READ
        assert all(user_id in notification.read_by for user_id in user_ids)
    
    def test_is_read_by(self, notification: Notification, user_ids: List[UserId]):
        """Test checking if a notification is read by a user."""
        # Arrange
        notification.mark_as_read(user_ids[0])
        
        # Act & Assert
        assert notification.is_read_by(user_ids[0]) is True
        assert notification.is_read_by(user_ids[1]) is False
    
    def test_is_expired(self, notification: Notification):
        """Test checking if a notification is expired."""
        # Arrange & Assert - not expired
        assert notification.is_expired() is False
        
        # Arrange - set expiration in the past
        notification.expires_at = datetime.now(UTC) - timedelta(hours=1)
        
        # Act & Assert - expired
        assert notification.is_expired() is True
        
        # Arrange - set status to expired
        notification.expires_at = None
        notification.status = NotificationStatus.EXPIRED
        
        # Act & Assert - expired by status
        assert notification.is_expired() is True
    
    def test_has_recipient(self, notification: Notification, user_ids: List[UserId]):
        """Test checking if a user is a recipient of a notification."""
        # Act & Assert
        assert notification.has_recipient(user_ids[0]) is True
        
        # Create a new user that is not a recipient
        non_recipient = UserId(value=str(uuid.uuid4()))
        assert notification.has_recipient(non_recipient) is False
    
    def test_add_action(self, notification: Notification):
        """Test adding an action to a notification."""
        # Act
        notification.add_action("View", "view_resource", {"resource_id": "123"})
        
        # Assert
        assert len(notification.actions) == 1
        action = notification.actions[0]
        assert action["label"] == "View"
        assert action["action"] == "view_resource"
        assert action["data"] == {"resource_id": "123"}
        
        # Act - add action without data
        notification.add_action("Dismiss", "dismiss_notification")
        
        # Assert
        assert len(notification.actions) == 2
        action = notification.actions[1]
        assert action["label"] == "Dismiss"
        assert action["action"] == "dismiss_notification"
        assert "data" not in action
    
    def test_create_system_notification(self, user_ids: List[UserId]):
        """Test the factory method for creating system notifications."""
        # Act
        notification = Notification.create_system_notification(
            title="System Notice",
            message="System maintenance scheduled",
            recipients=user_ids,
            priority=NotificationPriority.HIGH
        )
        
        # Assert
        assert notification.title == "System Notice"
        assert notification.message == "System maintenance scheduled"
        assert notification.recipients == user_ids
        assert notification.type == NotificationType.SYSTEM
        assert notification.priority == NotificationPriority.HIGH
        assert notification.status == NotificationStatus.PENDING
        assert notification.sender_id is None


class TestSubscription:
    """Tests for Subscription entity."""
    
    @pytest.fixture
    def subscription_id(self) -> SubscriptionId:
        """Create a test subscription ID."""
        return SubscriptionId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def user_id(self) -> UserId:
        """Create a test user ID."""
        return UserId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def resource_subscription(self, subscription_id: SubscriptionId, user_id: UserId) -> Subscription:
        """Create a test resource subscription."""
        return Subscription(
            id=subscription_id,
            user_id=user_id,
            type=SubscriptionType.RESOURCE,
            resource_id="resource-123",
            resource_type="document",
            labels={"important", "document"}
        )
    
    @pytest.fixture
    def topic_subscription(self, user_id: UserId) -> Subscription:
        """Create a test topic subscription."""
        return Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.TOPIC,
            topic="system-updates"
        )
    
    @pytest.fixture
    def query_subscription(self, user_id: UserId) -> Subscription:
        """Create a test query subscription."""
        return Subscription(
            id=SubscriptionId(value=str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.QUERY,
            query={"category": "news", "tag": "technology"}
        )
    
    def test_subscription_creation(self, resource_subscription: Subscription, subscription_id: SubscriptionId, user_id: UserId):
        """Test creating a subscription."""
        # Assert
        assert resource_subscription.id == subscription_id
        assert resource_subscription.user_id == user_id
        assert resource_subscription.type == SubscriptionType.RESOURCE
        assert resource_subscription.status == SubscriptionStatus.ACTIVE
        assert resource_subscription.resource_id == "resource-123"
        assert resource_subscription.resource_type == "document"
        assert resource_subscription.created_at is not None
        assert resource_subscription.updated_at is not None
        assert resource_subscription.expires_at is None
        assert "important" in resource_subscription.labels
        assert "document" in resource_subscription.labels
    
    def test_validation_resource_type(self, user_id: UserId):
        """Test validation for resource type subscription."""
        # Missing resource_type for RESOURCE_TYPE subscription
        with pytest.raises(ValueError, match="resource_type must be set for RESOURCE_TYPE subscriptions"):
            Subscription(
                id=SubscriptionId(value=str(uuid.uuid4())),
                user_id=user_id,
                type=SubscriptionType.RESOURCE_TYPE
            )
    
    def test_validation_resource_id(self, user_id: UserId):
        """Test validation for resource subscription."""
        # Missing resource_id for RESOURCE subscription
        with pytest.raises(ValueError, match="resource_id must be set for RESOURCE subscriptions"):
            Subscription(
                id=SubscriptionId(value=str(uuid.uuid4())),
                user_id=user_id,
                type=SubscriptionType.RESOURCE
            )
    
    def test_validation_topic(self, user_id: UserId):
        """Test validation for topic subscription."""
        # Missing topic for TOPIC subscription
        with pytest.raises(ValueError, match="topic must be set for TOPIC subscriptions"):
            Subscription(
                id=SubscriptionId(value=str(uuid.uuid4())),
                user_id=user_id,
                type=SubscriptionType.TOPIC
            )
    
    def test_validation_query(self, user_id: UserId):
        """Test validation for query subscription."""
        # Missing query for QUERY subscription
        with pytest.raises(ValueError, match="query must be set for QUERY subscriptions"):
            Subscription(
                id=SubscriptionId(value=str(uuid.uuid4())),
                user_id=user_id,
                type=SubscriptionType.QUERY
            )
    
    def test_update_status(self, resource_subscription: Subscription):
        """Test updating subscription status."""
        # Arrange
        original_updated_at = resource_subscription.updated_at
        
        # Act
        resource_subscription.update_status(SubscriptionStatus.PAUSED)
        
        # Assert
        assert resource_subscription.status == SubscriptionStatus.PAUSED
        assert resource_subscription.updated_at > original_updated_at
    
    def test_update_expiration(self, resource_subscription: Subscription):
        """Test updating subscription expiration."""
        # Arrange
        original_updated_at = resource_subscription.updated_at
        expires_at = datetime.now(UTC) + timedelta(days=30)
        
        # Act
        resource_subscription.update_expiration(expires_at)
        
        # Assert
        assert resource_subscription.expires_at == expires_at
        assert resource_subscription.updated_at > original_updated_at
    
    def test_add_remove_label(self, resource_subscription: Subscription):
        """Test adding and removing labels."""
        # Arrange
        original_updated_at = resource_subscription.updated_at
        
        # Act - add label
        resource_subscription.add_label("urgent")
        
        # Assert
        assert "urgent" in resource_subscription.labels
        assert resource_subscription.updated_at > original_updated_at
        
        # Act - update timestamp for next check
        original_updated_at = resource_subscription.updated_at
        
        # Act - remove label
        resource_subscription.remove_label("document")
        
        # Assert
        assert "document" not in resource_subscription.labels
        assert resource_subscription.updated_at > original_updated_at
        
        # Act - remove non-existent label (should not raise)
        resource_subscription.remove_label("non-existent")
    
    def test_is_active(self, resource_subscription: Subscription):
        """Test checking if a subscription is active."""
        # Assert - initially active
        assert resource_subscription.is_active() is True
        
        # Arrange - set status to inactive
        resource_subscription.update_status(SubscriptionStatus.INACTIVE)
        
        # Assert - no longer active
        assert resource_subscription.is_active() is False
        
        # Arrange - set status back to active but expired
        resource_subscription.update_status(SubscriptionStatus.ACTIVE)
        resource_subscription.update_expiration(datetime.now(UTC) - timedelta(days=1))
        
        # Assert - not active due to expiration
        assert resource_subscription.is_active() is False
    
    def test_is_expired(self, resource_subscription: Subscription):
        """Test checking if a subscription is expired."""
        # Assert - initially not expired
        assert resource_subscription.is_expired() is False
        
        # Arrange - set status to expired
        resource_subscription.update_status(SubscriptionStatus.EXPIRED)
        
        # Assert - expired by status
        assert resource_subscription.is_expired() is True
        
        # Arrange - set status back but with expiration in the past
        resource_subscription.update_status(SubscriptionStatus.ACTIVE)
        resource_subscription.update_expiration(datetime.now(UTC) - timedelta(days=1))
        
        # Assert - expired by date
        assert resource_subscription.is_expired() is True
    
    def test_matches_event_resource(self, resource_subscription: Subscription):
        """Test if a resource subscription matches events."""
        # Arrange - matching event
        matching_event = {
            "resource_id": "resource-123",
            "action": "update"
        }
        
        # Act & Assert - should match
        assert resource_subscription.matches_event(matching_event) is True
        
        # Arrange - non-matching event
        non_matching_event = {
            "resource_id": "resource-456",
            "action": "update"
        }
        
        # Act & Assert - should not match
        assert resource_subscription.matches_event(non_matching_event) is False
        
        # Arrange - inactive subscription
        resource_subscription.update_status(SubscriptionStatus.INACTIVE)
        
        # Act & Assert - should not match when inactive
        assert resource_subscription.matches_event(matching_event) is False
    
    def test_matches_event_topic(self, topic_subscription: Subscription):
        """Test if a topic subscription matches events."""
        # Arrange - matching event
        matching_event = {
            "topic": "system-updates",
            "message": "System update scheduled"
        }
        
        # Act & Assert - should match
        assert topic_subscription.matches_event(matching_event) is True
        
        # Arrange - non-matching event
        non_matching_event = {
            "topic": "security-alerts",
            "message": "Security alert"
        }
        
        # Act & Assert - should not match
        assert topic_subscription.matches_event(non_matching_event) is False
    
    def test_matches_event_query(self, query_subscription: Subscription):
        """Test if a query subscription matches events."""
        # Arrange - matching event (all query params match)
        matching_event = {
            "category": "news",
            "tag": "technology",
            "title": "New Tech Announcement"
        }
        
        # Act & Assert - should match
        assert query_subscription.matches_event(matching_event) is True
        
        # Arrange - non-matching event (missing query param)
        non_matching_event1 = {
            "category": "news",
            "title": "Politics Update"
        }
        
        # Act & Assert - should not match
        assert query_subscription.matches_event(non_matching_event1) is False
        
        # Arrange - non-matching event (different value)
        non_matching_event2 = {
            "category": "news",
            "tag": "politics",
            "title": "Political News"
        }
        
        # Act & Assert - should not match
        assert query_subscription.matches_event(non_matching_event2) is False
    
    def test_create_resource_subscription_factory(self, user_id: UserId):
        """Test the factory method for creating resource subscriptions."""
        # Arrange
        resource_id = "doc-123"
        resource_type = "document"
        expires_at = datetime.now(UTC) + timedelta(days=30)
        labels = {"important", "document"}
        metadata = {"created_by": "test"}
        
        # Act
        subscription = Subscription.create_resource_subscription(
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            expires_at=expires_at,
            labels=labels,
            metadata=metadata
        )
        
        # Assert
        assert isinstance(subscription.id, SubscriptionId)
        assert subscription.user_id == user_id
        assert subscription.type == SubscriptionType.RESOURCE
        assert subscription.resource_id == resource_id
        assert subscription.resource_type == resource_type
        assert subscription.expires_at == expires_at
        assert subscription.labels == labels
        assert subscription.metadata == metadata


class TestConnection:
    """Tests for Connection entity."""
    
    @pytest.fixture
    def connection_id(self) -> ConnectionId:
        """Create a test connection ID."""
        return ConnectionId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def user_id(self) -> UserId:
        """Create a test user ID."""
        return UserId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def connection(self, connection_id: ConnectionId) -> Connection:
        """Create a test connection."""
        return Connection(
            id=connection_id,
            metadata={"client": "web-browser"},
            client_info={"user_agent": "Mozilla/5.0", "ip": "127.0.0.1"}
        )
    
    def test_connection_creation(self, connection: Connection, connection_id: ConnectionId):
        """Test creating a connection."""
        # Assert
        assert connection.id == connection_id
        assert connection.user_id is None
        assert connection.state == ConnectionState.INITIALIZING
        assert connection.created_at is not None
        assert connection.last_activity_at is not None
        assert connection.metadata == {"client": "web-browser"}
        assert connection.client_info == {"user_agent": "Mozilla/5.0", "ip": "127.0.0.1"}
        assert len(connection.subscriptions) == 0
    
    def test_update_state(self, connection: Connection):
        """Test updating connection state."""
        # Arrange
        original_last_activity = connection.last_activity_at
        
        # Act
        connection.update_state(ConnectionState.CONNECTED)
        
        # Assert
        assert connection.state == ConnectionState.CONNECTED
        assert connection.last_activity_at > original_last_activity
    
    def test_associate_user(self, connection: Connection, user_id: UserId):
        """Test associating a user with a connection."""
        # Arrange
        original_last_activity = connection.last_activity_at
        
        # Act
        connection.associate_user(user_id)
        
        # Assert
        assert connection.user_id == user_id
        assert connection.last_activity_at > original_last_activity
    
    def test_add_remove_subscription(self, connection: Connection):
        """Test adding and removing subscriptions."""
        # Arrange
        subscription_id = SubscriptionId(value=str(uuid.uuid4()))
        
        # Act - add subscription
        connection.add_subscription(subscription_id)
        
        # Assert
        assert subscription_id in connection.subscriptions
        
        # Act - remove subscription
        connection.remove_subscription(subscription_id)
        
        # Assert
        assert subscription_id not in connection.subscriptions
        
        # Act - remove non-existent subscription (should not raise)
        connection.remove_subscription(SubscriptionId(value=str(uuid.uuid4())))
    
    def test_update_activity(self, connection: Connection):
        """Test updating the last activity timestamp."""
        # Arrange
        original_last_activity = connection.last_activity_at
        
        # Act
        connection.update_activity()
        
        # Assert
        assert connection.last_activity_at > original_last_activity
    
    def test_is_active(self, connection: Connection):
        """Test checking if a connection is active."""
        # Assert - initially not active
        assert connection.is_active() is False
        
        # Arrange - set to connected state
        connection.update_state(ConnectionState.CONNECTED)
        
        # Assert - now active
        assert connection.is_active() is True
        
        # Arrange - set to authenticated state
        connection.update_state(ConnectionState.AUTHENTICATED)
        
        # Assert - still active
        assert connection.is_active() is True
        
        # Arrange - set to disconnected state
        connection.update_state(ConnectionState.DISCONNECTED)
        
        # Assert - no longer active
        assert connection.is_active() is False
    
    def test_is_authenticated(self, connection: Connection, user_id: UserId):
        """Test checking if a connection is authenticated."""
        # Assert - initially not authenticated
        assert connection.is_authenticated() is False
        
        # Arrange - set to authenticated state but without user
        connection.update_state(ConnectionState.AUTHENTICATED)
        
        # Assert - still not authenticated (no user)
        assert connection.is_authenticated() is False
        
        # Arrange - associate user but wrong state
        connection.associate_user(user_id)
        connection.update_state(ConnectionState.CONNECTED)
        
        # Assert - not authenticated (wrong state)
        assert connection.is_authenticated() is False
        
        # Arrange - correct state and user
        connection.update_state(ConnectionState.AUTHENTICATED)
        
        # Assert - now authenticated
        assert connection.is_authenticated() is True


class TestMessage:
    """Tests for Message entity."""
    
    @pytest.fixture
    def connection_id(self) -> ConnectionId:
        """Create a test connection ID."""
        return ConnectionId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def user_id(self) -> UserId:
        """Create a test user ID."""
        return UserId(value=str(uuid.uuid4()))
    
    @pytest.fixture
    def text_message(self, connection_id: ConnectionId, user_id: UserId) -> Message:
        """Create a test text message."""
        return Message(
            type=MessageType.TEXT,
            payload="Hello, world!",
            connection_id=connection_id,
            user_id=user_id,
            metadata={"source": "test"}
        )
    
    @pytest.fixture
    def json_message(self, connection_id: ConnectionId) -> Message:
        """Create a test JSON message."""
        return Message(
            type=MessageType.NOTIFICATION,
            payload={"title": "Test", "body": "This is a test"},
            connection_id=connection_id,
            metadata={"priority": "high"}
        )
    
    @pytest.fixture
    def binary_message(self, connection_id: ConnectionId) -> Message:
        """Create a test binary message."""
        return Message(
            type=MessageType.BINARY,
            payload=b"\x00\x01\x02\x03",
            connection_id=connection_id
        )
    
    def test_message_creation(self, text_message: Message, connection_id: ConnectionId, user_id: UserId):
        """Test creating a message."""
        # Assert
        assert text_message.id is not None
        assert text_message.type == MessageType.TEXT
        assert text_message.payload == "Hello, world!"
        assert text_message.connection_id == connection_id
        assert text_message.user_id == user_id
        assert text_message.timestamp is not None
        assert text_message.metadata == {"source": "test"}
    
    def test_to_dict_text(self, text_message: Message, connection_id: ConnectionId, user_id: UserId):
        """Test converting a text message to a dictionary."""
        # Act
        result = text_message.to_dict()
        
        # Assert
        assert result["id"] == text_message.id
        assert result["type"] == MessageType.TEXT.value
        assert result["payload"] == "Hello, world!"
        assert result["connection_id"] == connection_id.value
        assert result["user_id"] == user_id.value
        assert isinstance(result["timestamp"], str)  # ISO format string
        assert result["metadata"] == {"source": "test"}
    
    def test_to_dict_json(self, json_message: Message, connection_id: ConnectionId):
        """Test converting a JSON message to a dictionary."""
        # Act
        result = json_message.to_dict()
        
        # Assert
        assert result["id"] == json_message.id
        assert result["type"] == MessageType.NOTIFICATION.value
        assert result["payload"] == {"title": "Test", "body": "This is a test"}
        assert result["connection_id"] == connection_id.value
        assert "user_id" not in result  # No user_id was set
        assert isinstance(result["timestamp"], str)
        assert result["metadata"] == {"priority": "high"}
    
    def test_to_dict_binary(self, binary_message: Message):
        """Test converting a binary message to a dictionary."""
        # Act
        result = binary_message.to_dict()
        
        # Assert
        assert result["id"] == binary_message.id
        assert result["type"] == MessageType.BINARY.value
        assert result["payload_encoding"] == "base64"
        # Binary data is base64 encoded
        assert result["payload"] == "AAECAw=="
    
    def test_to_json_text(self, text_message: Message):
        """Test converting a text message to JSON."""
        # Act
        json_str = text_message.to_json()
        
        # Assert
        # Parse back to verify
        parsed = json.loads(json_str)
        assert parsed["id"] == text_message.id
        assert parsed["type"] == MessageType.TEXT.value
        assert parsed["payload"] == "Hello, world!"
    
    def test_to_json_dict(self, json_message: Message):
        """Test converting a JSON message to JSON."""
        # Act
        json_str = json_message.to_json()
        
        # Assert
        # Parse back to verify
        parsed = json.loads(json_str)
        assert parsed["id"] == json_message.id
        assert parsed["type"] == MessageType.NOTIFICATION.value
        assert parsed["payload"] == {"title": "Test", "body": "This is a test"}
    
    def test_to_json_binary_raises(self, binary_message: Message):
        """Test that converting a binary message to JSON raises an error."""
        # Act & Assert
        with pytest.raises(TypeError, match="Cannot convert binary message directly to JSON"):
            binary_message.to_json()


class TestEvent:
    """Tests for Event entity."""
    
    @pytest.fixture
    def event(self) -> Event:
        """Create a test event."""
        return Event(
            event="notification",
            data='{"title":"Test","message":"This is a test"}',
            priority=EventPriority.NORMAL,
            retry=3000,
            comment="Test notification event"
        )
    
    def test_event_creation(self, event: Event):
        """Test creating an event."""
        # Assert
        assert event.id is not None
        assert event.event == "notification"
        assert event.data == '{"title":"Test","message":"This is a test"}'
        assert event.priority == EventPriority.NORMAL
        assert event.retry == 3000
        assert event.comment == "Test notification event"
        assert event.timestamp is not None
        assert event.metadata == {}
    
    def test_to_sse_format(self, event: Event):
        """Test converting an event to SSE format."""
        # Act
        sse_string = event.to_sse_format()
        
        # Assert
        lines = sse_string.strip().split("\n")
        assert lines[0] == f": {event.comment}"
        assert lines[1] == f"event: {event.event}"
        assert lines[2] == f"id: {event.id}"
        assert lines[3] == f"retry: {event.retry}"
        assert lines[4] == f"data: {event.data}"
        assert lines[5] == ""  # Empty line at the end
    
    def test_to_sse_format_multiline_data(self):
        """Test converting an event with multiline data to SSE format."""
        # Arrange
        multiline_data = "line 1\nline 2\nline 3"
        event = Event(
            event="message",
            data=multiline_data
        )
        
        # Act
        sse_string = event.to_sse_format()
        
        # Assert
        lines = sse_string.strip().split("\n")
        assert lines[0] == f"event: {event.event}"
        assert lines[1] == f"id: {event.id}"
        assert lines[2] == "data: line 1"
        assert lines[3] == "data: line 2"
        assert lines[4] == "data: line 3"
    
    def test_from_dict(self):
        """Test creating an event from a dictionary."""
        # Arrange
        event_dict = {
            "id": "test-id",
            "event": "update",
            "data": '{"status":"complete"}',
            "priority": "high",
            "retry": 5000,
            "comment": "Status update",
            "metadata": {"source": "system"}
        }
        
        # Act
        event = Event.from_dict(event_dict)
        
        # Assert
        assert event.id == "test-id"
        assert event.event == "update"
        assert event.data == '{"status":"complete"}'
        assert event.priority == EventPriority.HIGH
        assert event.retry == 5000
        assert event.comment == "Status update"
        assert event.metadata == {"source": "system"}
    
    def test_from_dict_required_fields_missing(self):
        """Test that creating an event from a dictionary with missing required fields raises an error."""
        # Arrange - missing 'event'
        event_dict1 = {
            "data": '{"status":"complete"}'
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required fields: event"):
            Event.from_dict(event_dict1)
        
        # Arrange - missing 'data'
        event_dict2 = {
            "event": "update"
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required fields: data"):
            Event.from_dict(event_dict2)
        
        # Arrange - missing both
        event_dict3 = {}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required fields: event, data"):
            Event.from_dict(event_dict3)