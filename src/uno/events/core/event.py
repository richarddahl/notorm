"""
Core event model for the Uno event system.

This module defines the base Event class used throughout the event system.
All events should inherit from this class to ensure consistency and compatibility.
"""

import json
import re
from datetime import datetime, UTC
from typing import Any, ClassVar, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    """
    Base class for all events in the system.
    
    Events are immutable value objects that represent something that happened
    in the system. They are named in the past tense (e.g., UserCreated) and
    contain all the data relevant to the event.
    """
    
    model_config = ConfigDict(frozen=True)
    
    # Core event metadata
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str = Field(default_factory=lambda: _class_to_event_type(Event.__name__))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Optional metadata for tracing and correlation
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    # Optional domain-specific metadata
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    aggregate_version: Optional[int] = None
    
    # Optional routing information
    topic: Optional[str] = None
    
    @classmethod
    def get_event_type(cls) -> str:
        """Get the standardized event type for this event class."""
        return _class_to_event_type(cls.__name__)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an event from a dictionary."""
        return cls.model_validate(data)
    
    def to_json(self) -> str:
        """Convert the event to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create an event from a JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def with_metadata(
        self,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        topic: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_version: Optional[int] = None,
    ) -> "Event":
        """
        Create a copy of this event with additional metadata.
        
        This method is useful for adding correlation IDs, causation IDs, 
        and other metadata to events without modifying the original event.
        
        Args:
            correlation_id: ID for tracing related events across services
            causation_id: ID of the event that caused this event
            topic: Topic for topic-based routing
            aggregate_id: ID of the aggregate that produced this event
            aggregate_type: Type of the aggregate that produced this event
            aggregate_version: Version of the aggregate after this event
            
        Returns:
            A new event instance with the additional metadata
        """
        data = self.to_dict()
        
        if correlation_id is not None:
            data["correlation_id"] = correlation_id
            
        if causation_id is not None:
            data["causation_id"] = causation_id
            
        if topic is not None:
            data["topic"] = topic
            
        if aggregate_id is not None:
            data["aggregate_id"] = aggregate_id
            
        if aggregate_type is not None:
            data["aggregate_type"] = aggregate_type
            
        if aggregate_version is not None:
            data["aggregate_version"] = aggregate_version
            
        return self.__class__(**data)


def _class_to_event_type(class_name: str) -> str:
    """
    Convert a class name to an event type identifier.
    
    Args:
        class_name: The class name to convert (e.g., UserCreated)
        
    Returns:
        The event type in snake_case (e.g., user_created)
    """
    # Convert CamelCase to snake_case
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()