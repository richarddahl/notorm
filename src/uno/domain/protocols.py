"""
Domain model protocols for the uno framework.

This module defines protocols (interfaces) for all domain model components,
providing a clear, consistent foundation for domain-driven design.
"""

from typing import (
    Protocol,
    TypeVar,
    Generic,
    List,
    Set,
    Dict,
    Any,
    Optional,
    runtime_checkable,
    Self,
    ClassVar,
)
from datetime import datetime
from uuid import UUID

# Type variables
IdT = TypeVar("IdT")  # Type for entity identifiers
EventT = TypeVar("EventT", bound="DomainEventProtocol")  # Type for domain events
ValueT = TypeVar("ValueT")  # Type for value object values
EntityT = TypeVar("EntityT", bound="EntityProtocol")  # Type for entities


# Import the canonical domain event protocol implementation
from uno.core.events import DomainEventProtocol


@runtime_checkable
class ValueObjectProtocol(Protocol):
    """Protocol for value objects."""

    def equals(self, other: Any) -> bool:
        """Check if this value object equals another."""
        ...

    def validate(self) -> None:
        """Validate the value object."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert value object to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValueObjectProtocol":
        """Create value object from dictionary."""
        ...


@runtime_checkable
class PrimitiveValueObjectProtocol(ValueObjectProtocol, Protocol[ValueT]):
    """Protocol for primitive value objects."""

    value: ValueT

    @classmethod
    def create(cls, value: ValueT) -> "PrimitiveValueObjectProtocol[ValueT]":
        """Create a primitive value object."""
        ...


@runtime_checkable
class EntityProtocol(Protocol[IdT]):
    """Protocol for domain entities."""

    id: IdT
    created_at: datetime
    updated_at: Optional[datetime]

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


@runtime_checkable
class AggregateRootProtocol(EntityProtocol[IdT], Protocol):
    """Protocol for aggregate roots."""

    version: int

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


@runtime_checkable
class SpecificationProtocol(Protocol[EntityT]):
    """Protocol for specifications."""

    def is_satisfied_by(self, entity: EntityT) -> bool:
        """Check if the entity satisfies this specification."""
        ...

    def and_(
        self, other: "SpecificationProtocol[EntityT]"
    ) -> "SpecificationProtocol[EntityT]":
        """Combine with another specification using AND."""
        ...

    def or_(
        self, other: "SpecificationProtocol[EntityT]"
    ) -> "SpecificationProtocol[EntityT]":
        """Combine with another specification using OR."""
        ...

    def not_(self) -> "SpecificationProtocol[EntityT]":
        """Negate this specification."""
        ...


@runtime_checkable
class EntityFactoryProtocol(Protocol[EntityT]):
    """Protocol for entity factories."""

    @classmethod
    def create(cls, **kwargs: Any) -> EntityT:
        """Create a new entity."""
        ...

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> EntityT:
        """Create an entity from a dictionary."""
        ...


@runtime_checkable
class CommandResultProtocol(Protocol):
    """Protocol for command results."""

    is_success: bool
    events: List[DomainEventProtocol]

    @property
    def is_failure(self) -> bool:
        """Check if the command result is a failure."""
        ...

    @classmethod
    def success(
        cls, events: Optional[List[DomainEventProtocol]] = None
    ) -> "CommandResultProtocol":
        """Create a successful command result."""
        ...

    @classmethod
    def failure(cls, error: Exception) -> "CommandResultProtocol":
        """Create a failed command result."""
        ...


@runtime_checkable
class DomainServiceProtocol(Protocol):
    """Protocol for domain services."""

    def execute(self, **kwargs: Any) -> CommandResultProtocol:
        """Execute domain logic."""
        ...
