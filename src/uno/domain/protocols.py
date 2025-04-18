"""
Domain model protocols for the uno framework.

This module re-exports the core protocols from uno.core.protocols to maintain backward compatibility.
"""

from uno.core.protocols import (
    EntityProtocol,
    AggregateRootProtocol,
    ValueObjectProtocol
)

from uno.core.protocols.event import EventProtocol as DomainEventProtocol

# Export everything from core protocols
from uno.core.protocols import *

# Legacy type variables for backward compatibility
from typing import TypeVar, Protocol, runtime_checkable, Any, Dict, List, Optional, Set

# Type variables
IdT = TypeVar("IdT")  # Type for entity identifiers
EventT = TypeVar("EventT", bound="DomainEventProtocol")  # Type for domain events
ValueT = TypeVar("ValueT")  # Type for value object values
EntityT = TypeVar("EntityT", bound="EntityProtocol")  # Type for entities


# The following protocols are kept for backward compatibility
# but should be migrated to the new protocols in uno.core.protocols

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