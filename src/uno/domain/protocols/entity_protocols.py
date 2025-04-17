"""
Entity protocol interfaces.

This module defines protocol interfaces for Entity and AggregateRoot.
"""

from typing import Protocol, TypeVar, List, Set, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from .event_protocols import DomainEventProtocol

ID = TypeVar("ID")


class EntityProtocol(Protocol):
    """Protocol interface for Entity."""

    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    events: List[DomainEventProtocol]

    def register_event(self, event: DomainEventProtocol) -> None:
        """Register a domain event."""
        ...

    def clear_events(self) -> List[DomainEventProtocol]:
        """Clear and return all registered domain events."""
        ...

    def update(self) -> None:
        """Update the entity."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityProtocol":
        """Create entity from dictionary."""
        ...


class AggregateRootProtocol(EntityProtocol, Protocol):
    """Protocol interface for AggregateRoot."""

    version: int
    child_entities: Set[EntityProtocol]

    def check_invariants(self) -> None:
        """Check that all aggregate invariants are satisfied."""
        ...

    def apply_changes(self) -> None:
        """Apply changes and ensure consistency."""
        ...

    def add_child_entity(self, entity: EntityProtocol) -> None:
        """Add a child entity."""
        ...

    def get_child_entities(self) -> Set[EntityProtocol]:
        """Get all child entities."""
        ...
