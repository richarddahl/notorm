"""
Domain entities for the Realtime module.

This module defines the core domain entities for the Realtime module,
including notifications, subscriptions, and connection-related entities.
"""

import uuid
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set, Union
from datetime import datetime, UTC

from uno.domain.core import Entity, AggregateRoot, ValueObject


# Value Objects
@dataclass(frozen=True)
class ConnectionId(ValueObject):
    """Identifier for a connection."""
    value: str


@dataclass(frozen=True)
class NotificationId(ValueObject):
    """Identifier for a notification."""
    value: str


@dataclass(frozen=True)
class SubscriptionId(ValueObject):
    """Identifier for a subscription."""
    value: str


@dataclass(frozen=True)
class UserId(ValueObject):
    """Identifier for a user."""
    value: str


# Enums
class NotificationPriority(str, Enum):
    """Priority levels for notifications."""
    LOW = "low"           # Background, non-time-sensitive notifications
    NORMAL = "normal"     # Default for most notifications
    HIGH = "high"         # Important notifications that should be seen promptly
    URGENT = "urgent"     # Critical notifications requiring immediate attention
    EMERGENCY = "emergency"  # System-critical alerts (used rarely)


class NotificationType(str, Enum):
    """Types of notifications."""
    # System notifications
    SYSTEM = "system"          # System-generated notifications
    MAINTENANCE = "maintenance"  # System maintenance notifications
    
    # User interaction notifications
    MESSAGE = "message"        # Direct messages
    MENTION = "mention"        # User mentions
    COMMENT = "comment"        # Comments on resources
    
    # Content notifications
    UPDATE = "update"          # Content updates
    NEW_CONTENT = "new_content"  # New content available
    
    # Task notifications
    TASK = "task"              # Task assignments or updates
    REMINDER = "reminder"      # Task reminders
    DEADLINE = "deadline"      # Deadline notifications
    
    # Alert notifications
    WARNING = "warning"        # Warnings about potential issues
    ERROR = "error"            # Error notifications
    SECURITY = "security"      # Security-related notifications


class NotificationStatus(str, Enum):
    """Status of a notification."""
    PENDING = "pending"        # Created but not yet delivered
    DELIVERED = "delivered"    # Successfully delivered to at least one channel
    READ = "read"              # Marked as read by the recipient
    FAILED = "failed"          # Delivery failed
    EXPIRED = "expired"        # No longer relevant or expired
    CANCELED = "canceled"      # Canceled before delivery


class SubscriptionType(str, Enum):
    """Types of subscriptions."""
    # Content-based subscriptions
    RESOURCE = "resource"         # Subscribe to updates for a specific resource
    RESOURCE_TYPE = "resource_type"  # Subscribe to updates for a resource type
    
    # Topic-based subscriptions
    TOPIC = "topic"               # Subscribe to a named topic
    
    # Query-based subscriptions
    QUERY = "query"               # Subscribe to results matching a query


class SubscriptionStatus(str, Enum):
    """Status of a subscription."""
    ACTIVE = "active"           # Subscription is active
    PAUSED = "paused"           # Temporarily paused
    EXPIRED = "expired"         # Subscription has expired
    INACTIVE = "inactive"       # Manually deactivated


class ConnectionState(str, Enum):
    """State of a WebSocket or SSE connection."""
    INITIALIZING = "initializing"   # Connection is being initialized
    CONNECTING = "connecting"       # Connection is being established
    CONNECTED = "connected"         # Connection is established
    AUTHENTICATING = "authenticating"  # Client is being authenticated
    AUTHENTICATED = "authenticated"  # Client is authenticated
    DISCONNECTING = "disconnecting"  # Connection is being closed gracefully
    DISCONNECTED = "disconnected"   # Connection is closed
    ERROR = "error"                 # Connection is in error state


class MessageType(str, Enum):
    """Types of WebSocket messages."""
    TEXT = "text"                # Text message
    BINARY = "binary"            # Binary message
    PING = "ping"                # Ping message
    PONG = "pong"                # Pong message
    CLOSE = "close"              # Close message
    ERROR = "error"              # Error message
    SYSTEM = "system"            # System message
    NOTIFICATION = "notification"  # Notification message
    EVENT = "event"              # Event message


class EventPriority(str, Enum):
    """Priority levels for SSE events."""
    LOW = "low"             # Low priority events
    NORMAL = "normal"       # Normal priority events
    HIGH = "high"           # High priority events
    URGENT = "urgent"       # Urgent events that should be processed immediately


# Entities
@dataclass
class Notification(Entity):
    """A notification to be delivered to users."""
    
    id: NotificationId
    title: str
    message: str
    recipients: List[UserId]
    type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    
    # Grouping and relationships
    group_id: Optional[str] = None
    sender_id: Optional[UserId] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # User interaction
    actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Delivery information
    channels: Set[str] = field(default_factory=lambda: {"in_app"})
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    delivered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    read_by: Set[UserId] = field(default_factory=set)
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_as_delivered(self) -> None:
        """Mark the notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now(UTC)
    
    def mark_as_read(self, user_id: UserId) -> None:
        """
        Mark the notification as read by a specific user.
        
        Args:
            user_id: The ID of the user who read the notification.
        """
        self.read_by.add(user_id)
        if set(self.recipients).issubset(self.read_by):
            self.status = NotificationStatus.READ
    
    def is_read_by(self, user_id: UserId) -> bool:
        """
        Check if the notification has been read by a specific user.
        
        Args:
            user_id: The ID of the user to check.
            
        Returns:
            True if the user has read the notification, False otherwise.
        """
        return user_id in self.read_by
    
    def is_expired(self) -> bool:
        """
        Check if the notification has expired.
        
        Returns:
            True if the notification has expired, False otherwise.
        """
        if self.status == NotificationStatus.EXPIRED:
            return True
            
        if self.expires_at is not None:
            return datetime.now(UTC) > self.expires_at
            
        return False
    
    def has_recipient(self, user_id: UserId) -> bool:
        """
        Check if a user is a recipient of this notification.
        
        Args:
            user_id: The ID of the user to check.
            
        Returns:
            True if the user is a recipient, False otherwise.
        """
        return user_id in self.recipients
    
    def add_action(self, label: str, action: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an action to the notification.
        
        Args:
            label: The display label for the action.
            action: The action identifier.
            data: Optional data associated with the action.
        """
        self.actions.append({
            "label": label,
            "action": action,
            **({"data": data} if data else {})
        })
    
    @classmethod
    def create_system_notification(
        cls,
        title: str,
        message: str,
        recipients: List[UserId],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> "Notification":
        """
        Create a system notification.
        
        Args:
            title: The notification title.
            message: The notification message.
            recipients: List of recipient user IDs.
            priority: The notification priority.
            actions: Optional list of actions.
            
        Returns:
            A system notification.
        """
        return cls(
            id=NotificationId(str(uuid.uuid4())),
            title=title,
            message=message,
            recipients=recipients,
            type=NotificationType.SYSTEM,
            priority=priority,
            actions=actions or [],
            sender_id=None
        )


@dataclass
class Subscription(Entity):
    """A subscription to real-time updates."""
    
    id: SubscriptionId
    user_id: UserId
    type: SubscriptionType
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None
    
    # Type-specific properties
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    topic: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    
    # Additional properties
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload_filter: Optional[Dict[str, Any]] = None
    labels: Set[str] = field(default_factory=set)
    
    def __post_init__(self) -> None:
        """Validate the subscription after initialization."""
        self._validate_type_specific_fields()
    
    def _validate_type_specific_fields(self) -> None:
        """Validate that the appropriate fields are set for the subscription type."""
        if self.type == SubscriptionType.RESOURCE and not self.resource_id:
            raise ValueError("resource_id must be set for RESOURCE subscriptions")
        
        if self.type == SubscriptionType.RESOURCE_TYPE and not self.resource_type:
            raise ValueError("resource_type must be set for RESOURCE_TYPE subscriptions")
            
        if self.type == SubscriptionType.TOPIC and not self.topic:
            raise ValueError("topic must be set for TOPIC subscriptions")
            
        if self.type == SubscriptionType.QUERY and not self.query:
            raise ValueError("query must be set for QUERY subscriptions")
    
    def update_status(self, status: SubscriptionStatus) -> None:
        """
        Update the subscription status.
        
        Args:
            status: The new status.
        """
        self.status = status
        self.updated_at = datetime.now(UTC)
    
    def update_expiration(self, expires_at: Optional[datetime]) -> None:
        """
        Update the subscription expiration.
        
        Args:
            expires_at: The new expiration date, or None for no expiration.
        """
        self.expires_at = expires_at
        self.updated_at = datetime.now(UTC)
    
    def add_label(self, label: str) -> None:
        """
        Add a label to the subscription.
        
        Args:
            label: The label to add.
        """
        self.labels.add(label)
        self.updated_at = datetime.now(UTC)
    
    def remove_label(self, label: str) -> None:
        """
        Remove a label from the subscription.
        
        Args:
            label: The label to remove.
        """
        self.labels.discard(label)
        self.updated_at = datetime.now(UTC)
    
    def is_active(self) -> bool:
        """
        Check if the subscription is active.
        
        Returns:
            True if the subscription is active, False otherwise.
        """
        if self.status != SubscriptionStatus.ACTIVE:
            return False
            
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False
            
        return True
    
    def is_expired(self) -> bool:
        """
        Check if the subscription has expired.
        
        Returns:
            True if the subscription has expired, False otherwise.
        """
        if self.status == SubscriptionStatus.EXPIRED:
            return True
            
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return True
            
        return False
    
    def matches_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Check if an event matches this subscription.
        
        Args:
            event_data: The event data to check.
            
        Returns:
            True if the event matches this subscription, False otherwise.
        """
        if not self.is_active():
            return False
        
        # Check based on subscription type
        if self.type == SubscriptionType.RESOURCE:
            # Check if event is for this resource
            event_resource_id = event_data.get("resource_id")
            return bool(event_resource_id and event_resource_id == self.resource_id)
        
        elif self.type == SubscriptionType.RESOURCE_TYPE:
            # Check if event is for this resource type
            event_resource_type = event_data.get("resource_type")
            return bool(event_resource_type and event_resource_type == self.resource_type)
        
        elif self.type == SubscriptionType.TOPIC:
            # Check if event is for this topic
            event_topic = event_data.get("topic")
            return bool(event_topic and event_topic == self.topic)
        
        elif self.type == SubscriptionType.QUERY:
            # Check if event matches query parameters
            if not self.query:
                return False
                
            # Simple implementation: check that all query parameters match
            # In a real system, this would use a more sophisticated query matching
            for key, value in self.query.items():
                if key not in event_data or event_data[key] != value:
                    return False
            return True
        
        return False
    
    @classmethod
    def create_resource_subscription(
        cls,
        user_id: UserId,
        resource_id: str,
        resource_type: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        labels: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Subscription":
        """
        Create a subscription to a specific resource.
        
        Args:
            user_id: The ID of the subscribing user.
            resource_id: The ID of the resource.
            resource_type: Optional type of the resource.
            expires_at: Optional expiration date.
            labels: Optional set of labels.
            metadata: Optional metadata.
            
        Returns:
            A resource subscription.
        """
        return cls(
            id=SubscriptionId(str(uuid.uuid4())),
            user_id=user_id,
            type=SubscriptionType.RESOURCE,
            resource_id=resource_id,
            resource_type=resource_type,
            expires_at=expires_at,
            labels=labels or set(),
            metadata=metadata or {}
        )


@dataclass
class Connection(Entity):
    """A real-time connection (WebSocket or SSE)."""
    
    id: ConnectionId
    user_id: Optional[UserId] = None
    state: ConnectionState = ConnectionState.INITIALIZING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    subscriptions: Set[SubscriptionId] = field(default_factory=set)
    client_info: Dict[str, Any] = field(default_factory=dict)
    
    def update_state(self, state: ConnectionState) -> None:
        """
        Update the connection state.
        
        Args:
            state: The new state.
        """
        self.state = state
        self.last_activity_at = datetime.now(UTC)
    
    def associate_user(self, user_id: UserId) -> None:
        """
        Associate a user with this connection.
        
        Args:
            user_id: The user ID to associate.
        """
        self.user_id = user_id
        self.last_activity_at = datetime.now(UTC)
    
    def add_subscription(self, subscription_id: SubscriptionId) -> None:
        """
        Add a subscription to this connection.
        
        Args:
            subscription_id: The subscription ID to add.
        """
        self.subscriptions.add(subscription_id)
    
    def remove_subscription(self, subscription_id: SubscriptionId) -> None:
        """
        Remove a subscription from this connection.
        
        Args:
            subscription_id: The subscription ID to remove.
        """
        self.subscriptions.discard(subscription_id)
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity_at = datetime.now(UTC)
    
    def is_active(self) -> bool:
        """
        Check if the connection is active.
        
        Returns:
            True if the connection is active, False otherwise.
        """
        return self.state in {
            ConnectionState.CONNECTED,
            ConnectionState.AUTHENTICATED
        }
    
    def is_authenticated(self) -> bool:
        """
        Check if the connection is authenticated.
        
        Returns:
            True if the connection is authenticated, False otherwise.
        """
        return self.state == ConnectionState.AUTHENTICATED and self.user_id is not None


@dataclass
class Message(Entity):
    """A WebSocket message."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.TEXT
    payload: Union[str, bytes, Dict[str, Any]] = ""
    connection_id: Optional[ConnectionId] = None
    user_id: Optional[UserId] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message.
        """
        result = {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
        
        # Handle connection_id and user_id
        if self.connection_id:
            result["connection_id"] = self.connection_id.value
        
        if self.user_id:
            result["user_id"] = self.user_id.value
        
        # Handle payload based on type
        if isinstance(self.payload, bytes):
            # For binary data, encode as base64
            import base64
            result["payload"] = base64.b64encode(self.payload).decode("ascii")
            result["payload_encoding"] = "base64"
        elif isinstance(self.payload, dict):
            # For dict payload, include as-is
            result["payload"] = self.payload
        else:
            # For string payload, include as-is
            result["payload"] = self.payload
        
        return result
    
    def to_json(self) -> str:
        """
        Convert the message to a JSON string.
        
        Returns:
            JSON string representation of the message.
            
        Raises:
            TypeError: If the message contains binary data.
        """
        if isinstance(self.payload, bytes):
            raise TypeError("Cannot convert binary message directly to JSON. Use to_dict() first.")
        
        return json.dumps(self.to_dict())


@dataclass
class Event(Entity):
    """A Server-Sent Events (SSE) event."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: str
    data: str
    priority: EventPriority = EventPriority.NORMAL
    retry: Optional[int] = None
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_sse_format(self) -> str:
        """
        Convert the event to SSE format.
        
        Returns:
            The event in SSE format.
        """
        lines = []
        
        # Add comment if present
        if self.comment:
            lines.append(f": {self.comment}")
        
        # Add event field
        lines.append(f"event: {self.event}")
        
        # Add ID field
        lines.append(f"id: {self.id}")
        
        # Add retry field if present
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        # Add data field, handling multi-line data
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")
        
        # End with a blank line
        lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Create an Event from a dictionary.
        
        Args:
            data: Dictionary with event data.
            
        Returns:
            A new Event instance.
            
        Raises:
            ValueError: If required fields are missing.
        """
        # Check required fields
        required_fields = ["event", "data"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Extract optional fields
        event_id = data.get("id", str(uuid.uuid4()))
        priority = EventPriority(data.get("priority", EventPriority.NORMAL.value))
        retry = data.get("retry")
        comment = data.get("comment")
        timestamp = data.get("timestamp", datetime.now(UTC))
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        metadata = data.get("metadata", {})
        
        return cls(
            id=event_id,
            event=data["event"],
            data=data["data"],
            priority=priority,
            retry=retry,
            comment=comment,
            timestamp=timestamp,
            metadata=metadata
        )