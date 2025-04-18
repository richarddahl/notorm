"""
Standalone test for event implementation.
"""

import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, Optional


class BasicEvent:
    """Simple event implementation without external dependencies."""
    
    def __init__(
        self,
        event_id: Optional[str] = None,
        event_type: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        **data
    ):
        """Initialize a basic event with the provided data."""
        self.event_id = event_id or str(uuid4())
        self.event_type = event_type or self.__class__.__name__.lower()
        self.occurred_at = occurred_at or datetime.now()
        self.correlation_id = correlation_id
        self.aggregate_id = aggregate_id
        self.data = data
        
        # Add data attributes to the instance
        for key, value in data.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
        }
        
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
            
        if self.aggregate_id:
            result["aggregate_id"] = self.aggregate_id
            
        result.update(self.data)
        return result
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BasicEvent':
        """Create event from dictionary."""
        event_data = data.copy()
        
        # Extract standard fields
        event_id = event_data.pop("event_id", None)
        event_type = event_data.pop("event_type", None)
        
        occurred_at_str = event_data.pop("occurred_at", None)
        occurred_at = datetime.fromisoformat(occurred_at_str) if occurred_at_str else None
        
        correlation_id = event_data.pop("correlation_id", None)
        aggregate_id = event_data.pop("aggregate_id", None)
        
        # Create event with remaining data
        return cls(
            event_id=event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            correlation_id=correlation_id,
            aggregate_id=aggregate_id,
            **event_data
        )


class UserCreated(BasicEvent):
    """Example event for user creation."""
    pass


def test_basic_event():
    """Test the basic event implementation."""
    # Create a test event
    event = UserCreated(
        username="testuser",
        email="test@example.com",
        aggregate_id="user-123"
    )
    
    # Check properties
    assert event.event_type == "usercreated"
    assert event.username == "testuser"
    assert event.email == "test@example.com"
    assert event.aggregate_id == "user-123"
    assert event.event_id is not None
    assert isinstance(event.occurred_at, datetime)
    
    # Test serialization
    event_dict = event.to_dict()
    assert event_dict["username"] == "testuser"
    assert event_dict["email"] == "test@example.com"
    assert event_dict["aggregate_id"] == "user-123"
    
    # Test to_json and from_dict
    json_str = event.to_json()
    parsed_dict = json.loads(json_str)
    assert parsed_dict["username"] == "testuser"
    
    # Create from dictionary
    new_event = BasicEvent.from_dict(event_dict)
    assert new_event.username == event.username
    assert new_event.email == event.email
    assert new_event.aggregate_id == event.aggregate_id
    
    print("Event test passed!")


def test_with_metadata():
    """Test event with metadata."""
    # Create a test event
    event = UserCreated(
        username="testuser",
        email="test@example.com"
    )
    
    # Add metadata via a new instance
    event_with_metadata = UserCreated(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        correlation_id="corr-123",
        aggregate_id="user-456",
        username=event.username,
        email=event.email
    )
    
    # Check metadata
    assert event_with_metadata.correlation_id == "corr-123"
    assert event_with_metadata.aggregate_id == "user-456"
    
    # Original data should be preserved
    assert event_with_metadata.username == event.username
    assert event_with_metadata.email == event.email
    
    print("Metadata test passed!")


if __name__ == "__main__":
    test_basic_event()
    test_with_metadata()
    print("All tests passed successfully!")