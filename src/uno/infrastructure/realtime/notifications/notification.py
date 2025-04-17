"""Notification data structures.

This module defines the data structures used for notifications.
"""

import uuid
import json
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Set, Union, ClassVar
from datetime import datetime


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    
    LOW = 0       # Background, non-time-sensitive notifications
    NORMAL = 1    # Default for most notifications
    HIGH = 2      # Important notifications that should be seen promptly
    URGENT = 3    # Critical notifications requiring immediate attention
    EMERGENCY = 4 # System-critical alerts (used rarely)


class NotificationType(Enum):
    """Types of notifications."""
    
    # System notifications
    SYSTEM = auto()      # System-generated notifications
    MAINTENANCE = auto() # System maintenance notifications
    
    # User interaction notifications
    MESSAGE = auto()     # Direct messages
    MENTION = auto()     # User mentions
    COMMENT = auto()     # Comments on resources
    
    # Content notifications
    UPDATE = auto()      # Content updates
    NEW_CONTENT = auto() # New content available
    
    # Task notifications
    TASK = auto()        # Task assignments or updates
    REMINDER = auto()    # Task reminders
    DEADLINE = auto()    # Deadline notifications
    
    # Alert notifications
    WARNING = auto()     # Warnings about potential issues
    ERROR = auto()       # Error notifications
    SECURITY = auto()    # Security-related notifications


class NotificationStatus(Enum):
    """Status of a notification."""
    
    PENDING = auto()     # Created but not yet delivered
    DELIVERED = auto()   # Successfully delivered to at least one channel
    READ = auto()        # Marked as read by the recipient
    FAILED = auto()      # Delivery failed
    EXPIRED = auto()     # No longer relevant or expired
    CANCELED = auto()    # Canceled before delivery


@dataclass
class Notification:
    """Represents a notification.
    
    Attributes:
        id: Unique identifier for the notification.
        title: Notification title (short summary).
        message: Notification message (full content).
        type: The type of notification.
        priority: Priority level for the notification.
        recipients: List of recipient IDs.
        group_id: ID that groups related notifications together.
        sender_id: ID of the sender (user or system).
        resource_type: Type of resource the notification refers to.
        resource_id: ID of the resource the notification refers to.
        actions: Optional list of actions the user can take.
        channels: Delivery channels to use.
        status: Current status of the notification.
        created_at: When the notification was created.
        delivered_at: When the notification was delivered.
        expires_at: When the notification expires.
        read_by: Set of recipient IDs who have read the notification.
        metadata: Additional metadata for the notification.
    """
    
    title: str
    message: str
    recipients: List[str]
    
    # Basic properties
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    
    # Grouping and relationships
    group_id: Optional[str] = None
    sender_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # User interaction
    actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Delivery information
    channels: Set[str] = field(default_factory=lambda: {"in_app"})
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    read_by: Set[str] = field(default_factory=set)
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Serialization keys
    ID_KEY: ClassVar[str] = "id"
    TITLE_KEY: ClassVar[str] = "title"
    MESSAGE_KEY: ClassVar[str] = "message"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the notification to a dictionary.
        
        Returns:
            Dictionary representation of the notification.
        """
        data = asdict(self)
        
        # Convert enum values to strings
        data["type"] = self.type.name
        data["priority"] = self.priority.name
        data["status"] = self.status.name
        
        # Convert datetime objects to ISO format strings
        data["created_at"] = self.created_at.isoformat()
        if self.delivered_at:
            data["delivered_at"] = self.delivered_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        
        # Convert sets to lists for JSON compatibility
        data["channels"] = list(self.channels)
        data["read_by"] = list(self.read_by)
        
        return data
    
    def to_json(self) -> str:
        """Convert the notification to a JSON string.
        
        Returns:
            JSON string representation of the notification.
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """Create a Notification from a dictionary.
        
        Args:
            data: Dictionary with notification data.
            
        Returns:
            A new Notification instance.
            
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Check required fields
        required_fields = ["title", "message", "recipients"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Convert string enum values to enum instances
        if "type" in data and isinstance(data["type"], str):
            try:
                data["type"] = NotificationType[data["type"]]
            except KeyError:
                raise ValueError(f"Invalid notification type: {data['type']}")
                
        if "priority" in data and isinstance(data["priority"], str):
            try:
                data["priority"] = NotificationPriority[data["priority"]]
            except KeyError:
                raise ValueError(f"Invalid notification priority: {data['priority']}")
                
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = NotificationStatus[data["status"]]
            except KeyError:
                raise ValueError(f"Invalid notification status: {data['status']}")
        
        # Convert ISO format strings to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "delivered_at" in data and isinstance(data["delivered_at"], str):
            data["delivered_at"] = datetime.fromisoformat(data["delivered_at"])
        if "expires_at" in data and isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        
        # Convert lists to sets for internal representation
        if "channels" in data and isinstance(data["channels"], list):
            data["channels"] = set(data["channels"])
        if "read_by" in data and isinstance(data["read_by"], list):
            data["read_by"] = set(data["read_by"])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Notification":
        """Create a Notification from a JSON string.
        
        Args:
            json_str: JSON string with notification data.
            
        Returns:
            A new Notification instance.
            
        Raises:
            ValueError: If the JSON is invalid or required fields are missing.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        return cls.from_dict(data)
    
    def mark_as_delivered(self) -> None:
        """Mark the notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_as_read(self, user_id: str) -> None:
        """Mark the notification as read by a specific user.
        
        Args:
            user_id: The ID of the user who read the notification.
        """
        self.read_by.add(user_id)
        if set(self.recipients).issubset(self.read_by):
            self.status = NotificationStatus.READ
    
    def is_read_by(self, user_id: str) -> bool:
        """Check if the notification has been read by a specific user.
        
        Args:
            user_id: The ID of the user to check.
            
        Returns:
            True if the user has read the notification, False otherwise.
        """
        return user_id in self.read_by
    
    def is_expired(self) -> bool:
        """Check if the notification has expired.
        
        Returns:
            True if the notification has expired, False otherwise.
        """
        if self.status == NotificationStatus.EXPIRED:
            return True
            
        if self.expires_at is not None:
            return datetime.now() > self.expires_at
            
        return False
    
    def has_recipient(self, user_id: str) -> bool:
        """Check if a user is a recipient of this notification.
        
        Args:
            user_id: The ID of the user to check.
            
        Returns:
            True if the user is a recipient, False otherwise.
        """
        return user_id in self.recipients
    
    def add_action(self, label: str, action: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add an action to the notification.
        
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


# Factory functions for common notification types

def create_system_notification(
    title: str,
    message: str,
    recipients: List[str],
    priority: NotificationPriority = NotificationPriority.NORMAL,
    actions: Optional[List[Dict[str, Any]]] = None
) -> Notification:
    """Create a system notification.
    
    Args:
        title: The notification title.
        message: The notification message.
        recipients: List of recipient user IDs.
        priority: The notification priority.
        actions: Optional list of actions.
        
    Returns:
        A system notification.
    """
    return Notification(
        title=title,
        message=message,
        recipients=recipients,
        type=NotificationType.SYSTEM,
        priority=priority,
        actions=actions or [],
        sender_id="system"
    )


def create_user_notification(
    title: str,
    message: str,
    recipients: List[str],
    sender_id: str,
    type_: NotificationType = NotificationType.MESSAGE,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    actions: Optional[List[Dict[str, Any]]] = None
) -> Notification:
    """Create a user-to-user notification.
    
    Args:
        title: The notification title.
        message: The notification message.
        recipients: List of recipient user IDs.
        sender_id: The ID of the sending user.
        type_: The notification type.
        priority: The notification priority.
        actions: Optional list of actions.
        
    Returns:
        A user-to-user notification.
    """
    return Notification(
        title=title,
        message=message,
        recipients=recipients,
        type=type_,
        priority=priority,
        actions=actions or [],
        sender_id=sender_id
    )


def create_resource_notification(
    title: str,
    message: str,
    recipients: List[str],
    resource_type: str,
    resource_id: str,
    type_: NotificationType = NotificationType.UPDATE,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    sender_id: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None
) -> Notification:
    """Create a resource notification.
    
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
        
    Returns:
        A resource notification.
    """
    return Notification(
        title=title,
        message=message,
        recipients=recipients,
        type=type_,
        priority=priority,
        resource_type=resource_type,
        resource_id=resource_id,
        sender_id=sender_id,
        actions=actions or []
    )