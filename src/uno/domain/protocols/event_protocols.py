"""
Event protocol interfaces.

This module defines protocol interfaces for DomainEvent.
"""

from typing import Protocol, Dict, Any, Optional
from datetime import datetime


class DomainEventProtocol(Protocol):
    """Protocol interface for DomainEvent."""

    event_id: str
    event_type: str
    timestamp: datetime
    aggregate_id: Optional[str]
    aggregate_type: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEventProtocol":
        """Create event from dictionary."""
        ...
