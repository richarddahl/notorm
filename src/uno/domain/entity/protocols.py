"""
Protocol definitions for domain entities.

This module defines protocol classes for domain entities, providing
type-safe abstractions for the domain model framework.
"""

from datetime import datetime
from typing import Any, Generic, List, Protocol, TypeVar, runtime_checkable
from uuid import UUID

ID = TypeVar("ID")  # Type variable for entity IDs


@runtime_checkable
class EntityProtocol(Protocol[ID]):
    """
    Protocol for entities in the domain model.

    An entity is an object that has a distinct identity that persists over time,
    even when its attributes change.
    """

    id: ID
    created_at: datetime
    updated_at: datetime

    def __eq__(self, other: Any) -> bool:
        """Compare entities by identity."""
        ...

    def __hash__(self) -> int:
        """Hash entities by identity."""
        ...


@runtime_checkable
class AggregateRootProtocol(EntityProtocol[ID], Protocol[ID]):
    """
    Protocol for aggregate roots in the domain model.

    An aggregate root is an entity that encapsulates a cluster of objects
    and ensures their consistency as a group. It is the entry point to
    the aggregate.
    """

    version: int  # For optimistic concurrency control

    def get_uncommitted_events(self) -> list[Any]:
        """Get all uncommitted domain events."""
        ...

    def clear_events(self) -> None:
        """Clear all uncommitted domain events."""
        ...

    def apply_event(self, event: Any) -> None:
        """Apply a domain event to this aggregate."""
        ...


@runtime_checkable
class ValueObjectProtocol(Protocol):
    """
    Protocol for value objects in the domain model.

    A value object is an immutable object that is defined by its attributes
    rather than by its identity. Value objects are typically used to represent
    concepts or measurements in the domain.
    """

    def __eq__(self, other: Any) -> bool:
        """Compare value objects by value."""
        ...

    def __hash__(self) -> int:
        """Hash value objects by value."""
        ...
