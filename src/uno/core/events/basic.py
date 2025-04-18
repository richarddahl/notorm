"""
Basic event implementation without dependencies.
"""

import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, Optional


class BasicEvent:
    """Simple event implementation without pydantic dependency."""
    
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