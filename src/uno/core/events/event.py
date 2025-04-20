"""
Base Event class for the UNO framework.

This module defines the core Event class that all domain events should inherit from.
Events are immutable value objects that represent something that happened in the domain.
"""

import json
from datetime import datetime, UTC
from typing import Any, Dict, Optional, ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class Event(BaseModel):
    """
    Base class for all events in the UNO framework.

    Events are immutable value objects representing something that happened in the system.
    They are named in the past tense (e.g., UserCreated) and should contain all relevant data.

    Events provide built-in functionality for:
    - Unique identification
    - Timestamp tracking
    - Serialization
    - Metadata for tracing and correlation
    - Domain-specific context (aggregate info)
    """

    model_config = ConfigDict(frozen=True)

    # Core event metadata
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(
        default_factory=lambda: _class_to_event_type(Event.__name__)
    )
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Tracing and correlation
    correlation_id: str | None = None
    causation_id: str | None = None

    # Domain context
    aggregate_id: str | None = None
    aggregate_type: str | None = None
    aggregate_version: Optional[int] = None

    @classmethod
    def get_event_type(cls) -> str:
        """Get the standardized event type name based on the class name."""
        return _class_to_event_type(cls.__name__)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an event from a dictionary representation."""
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
        correlation_id: str | None = None,
        causation_id: str | None = None,
        aggregate_id: str | None = None,
        aggregate_type: str | None = None,
        aggregate_version: Optional[int] = None,
    ) -> "Event":
        """
        Create a new instance of this event with additional metadata.

        This is useful for adding correlation IDs, causation IDs, and
        aggregate information without modifying the original event.

        Args:
            correlation_id: ID for tracing related events
            causation_id: ID of the event that caused this one
            aggregate_id: ID of the aggregate this event belongs to
            aggregate_type: Type of the aggregate
            aggregate_version: Version of the aggregate after this event

        Returns:
            A new event instance with the additional metadata
        """
        data = self.to_dict()

        if correlation_id is not None:
            data["correlation_id"] = correlation_id
        if causation_id is not None:
            data["causation_id"] = causation_id
        if aggregate_id is not None:
            data["aggregate_id"] = aggregate_id
        if aggregate_type is not None:
            data["aggregate_type"] = aggregate_type
        if aggregate_version is not None:
            data["aggregate_version"] = aggregate_version

        return self.__class__(**data)


def _class_to_event_type(class_name: str) -> str:
    """
    Convert a PascalCase class name to a snake_case event type.

    Args:
        class_name: The class name to convert (e.g., UserCreated)

    Returns:
        The event type in snake_case (e.g., user_created)
    """
    import re

    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
