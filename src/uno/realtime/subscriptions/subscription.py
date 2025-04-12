"""Subscription data structures.

This module defines the data structures used for subscriptions.
"""

import uuid
import json
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Set, ClassVar
from datetime import datetime


class SubscriptionType(Enum):
    """Types of subscriptions."""
    
    # Content-based subscriptions
    RESOURCE = auto()    # Subscribe to updates for a specific resource
    RESOURCE_TYPE = auto()  # Subscribe to updates for a resource type
    
    # Topic-based subscriptions
    TOPIC = auto()       # Subscribe to a named topic
    
    # Query-based subscriptions
    QUERY = auto()       # Subscribe to results matching a query


class SubscriptionStatus(Enum):
    """Status of a subscription."""
    
    ACTIVE = auto()      # Subscription is active
    PAUSED = auto()      # Temporarily paused
    EXPIRED = auto()     # Subscription has expired
    INACTIVE = auto()    # Manually deactivated


@dataclass
class Subscription:
    """Represents a subscription to real-time updates.
    
    Attributes:
        id: Unique identifier for the subscription.
        user_id: ID of the subscribing user.
        type: The type of subscription.
        status: Current status of the subscription.
        created_at: When the subscription was created.
        updated_at: When the subscription was last updated.
        expires_at: When the subscription expires (optional).
        
        # Type-specific attributes
        resource_id: ID of the resource (for RESOURCE subscriptions).
        resource_type: Type of resource (for RESOURCE_TYPE subscriptions).
        topic: Topic name (for TOPIC subscriptions).
        query: Query parameters (for QUERY subscriptions).
        
        # Additional attributes
        metadata: Additional metadata for the subscription.
        payload_filter: Optional filter for event payloads.
        labels: Set of labels for categorizing subscriptions.
    """
    
    user_id: str
    type: SubscriptionType
    
    # Basic properties
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Type-specific properties (set appropriate ones based on type)
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    topic: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    
    # Additional properties
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload_filter: Optional[Dict[str, Any]] = None
    labels: Set[str] = field(default_factory=set)
    
    # Serialization keys
    ID_KEY: ClassVar[str] = "id"
    USER_ID_KEY: ClassVar[str] = "user_id"
    TYPE_KEY: ClassVar[str] = "type"
    
    def __post_init__(self):
        """Validate the subscription after initialization."""
        self._validate_type_specific_fields()
    
    def _validate_type_specific_fields(self):
        """Validate that the appropriate fields are set for the subscription type."""
        if self.type == SubscriptionType.RESOURCE and not self.resource_id:
            raise ValueError("resource_id must be set for RESOURCE subscriptions")
        
        if self.type == SubscriptionType.RESOURCE_TYPE and not self.resource_type:
            raise ValueError("resource_type must be set for RESOURCE_TYPE subscriptions")
            
        if self.type == SubscriptionType.TOPIC and not self.topic:
            raise ValueError("topic must be set for TOPIC subscriptions")
            
        if self.type == SubscriptionType.QUERY and not self.query:
            raise ValueError("query must be set for QUERY subscriptions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the subscription to a dictionary.
        
        Returns:
            Dictionary representation of the subscription.
        """
        data = asdict(self)
        
        # Convert enum values to strings
        data["type"] = self.type.name
        data["status"] = self.status.name
        
        # Convert datetime objects to ISO format strings
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        
        # Convert sets to lists for JSON compatibility
        data["labels"] = list(self.labels)
        
        return data
    
    def to_json(self) -> str:
        """Convert the subscription to a JSON string.
        
        Returns:
            JSON string representation of the subscription.
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subscription":
        """Create a Subscription from a dictionary.
        
        Args:
            data: Dictionary with subscription data.
            
        Returns:
            A new Subscription instance.
            
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Check required fields
        required_fields = ["user_id", "type"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Convert string enum values to enum instances
        if "type" in data and isinstance(data["type"], str):
            try:
                data["type"] = SubscriptionType[data["type"]]
            except KeyError:
                raise ValueError(f"Invalid subscription type: {data['type']}")
                
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = SubscriptionStatus[data["status"]]
            except KeyError:
                raise ValueError(f"Invalid subscription status: {data['status']}")
        
        # Convert ISO format strings to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if "expires_at" in data and isinstance(data["expires_at"], str) and data["expires_at"]:
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        
        # Convert lists to sets for internal representation
        if "labels" in data and isinstance(data["labels"], list):
            data["labels"] = set(data["labels"])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Subscription":
        """Create a Subscription from a JSON string.
        
        Args:
            json_str: JSON string with subscription data.
            
        Returns:
            A new Subscription instance.
            
        Raises:
            ValueError: If the JSON is invalid or required fields are missing.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        return cls.from_dict(data)
    
    def update_status(self, status: SubscriptionStatus) -> None:
        """Update the subscription status.
        
        Args:
            status: The new status.
        """
        self.status = status
        self.updated_at = datetime.now()
    
    def update_expiration(self, expires_at: Optional[datetime]) -> None:
        """Update the subscription expiration.
        
        Args:
            expires_at: The new expiration date, or None for no expiration.
        """
        self.expires_at = expires_at
        self.updated_at = datetime.now()
    
    def add_label(self, label: str) -> None:
        """Add a label to the subscription.
        
        Args:
            label: The label to add.
        """
        self.labels.add(label)
        self.updated_at = datetime.now()
    
    def remove_label(self, label: str) -> None:
        """Remove a label from the subscription.
        
        Args:
            label: The label to remove.
        """
        self.labels.discard(label)
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """Check if the subscription is active.
        
        Returns:
            True if the subscription is active, False otherwise.
        """
        if self.status != SubscriptionStatus.ACTIVE:
            return False
            
        if self.expires_at and datetime.now() > self.expires_at:
            return False
            
        return True
    
    def is_expired(self) -> bool:
        """Check if the subscription has expired.
        
        Returns:
            True if the subscription has expired, False otherwise.
        """
        if self.status == SubscriptionStatus.EXPIRED:
            return True
            
        if self.expires_at and datetime.now() > self.expires_at:
            return True
            
        return False
    
    def matches_event(self, event_data: Dict[str, Any]) -> bool:
        """Check if an event matches this subscription.
        
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


# Factory functions for common subscription types

def create_resource_subscription(
    user_id: str,
    resource_id: str,
    resource_type: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    labels: Optional[Set[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Subscription:
    """Create a subscription to a specific resource.
    
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
    return Subscription(
        user_id=user_id,
        type=SubscriptionType.RESOURCE,
        resource_id=resource_id,
        resource_type=resource_type,
        expires_at=expires_at,
        labels=labels or set(),
        metadata=metadata or {}
    )


def create_resource_type_subscription(
    user_id: str,
    resource_type: str,
    expires_at: Optional[datetime] = None,
    labels: Optional[Set[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Subscription:
    """Create a subscription to a resource type.
    
    Args:
        user_id: The ID of the subscribing user.
        resource_type: The type of resources to subscribe to.
        expires_at: Optional expiration date.
        labels: Optional set of labels.
        metadata: Optional metadata.
        
    Returns:
        A resource type subscription.
    """
    return Subscription(
        user_id=user_id,
        type=SubscriptionType.RESOURCE_TYPE,
        resource_type=resource_type,
        expires_at=expires_at,
        labels=labels or set(),
        metadata=metadata or {}
    )


def create_topic_subscription(
    user_id: str,
    topic: str,
    expires_at: Optional[datetime] = None,
    labels: Optional[Set[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    payload_filter: Optional[Dict[str, Any]] = None
) -> Subscription:
    """Create a subscription to a topic.
    
    Args:
        user_id: The ID of the subscribing user.
        topic: The topic to subscribe to.
        expires_at: Optional expiration date.
        labels: Optional set of labels.
        metadata: Optional metadata.
        payload_filter: Optional filter for event payloads.
        
    Returns:
        A topic subscription.
    """
    return Subscription(
        user_id=user_id,
        type=SubscriptionType.TOPIC,
        topic=topic,
        expires_at=expires_at,
        labels=labels or set(),
        metadata=metadata or {},
        payload_filter=payload_filter
    )


def create_query_subscription(
    user_id: str,
    query: Dict[str, Any],
    expires_at: Optional[datetime] = None,
    labels: Optional[Set[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Subscription:
    """Create a subscription to query results.
    
    Args:
        user_id: The ID of the subscribing user.
        query: The query parameters.
        expires_at: Optional expiration date.
        labels: Optional set of labels.
        metadata: Optional metadata.
        
    Returns:
        A query subscription.
    """
    return Subscription(
        user_id=user_id,
        type=SubscriptionType.QUERY,
        query=query,
        expires_at=expires_at,
        labels=labels or set(),
        metadata=metadata or {}
    )