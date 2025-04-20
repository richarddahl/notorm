"""
Entity Protocol Definitions

This module defines the entity protocols used for domain modeling.
Entities are objects with a distinct identity that persists over time.
"""

from typing import Protocol, Generic, TypeVar, Any, runtime_checkable
from datetime import datetime


# Type variable for entity ID
ID = TypeVar("ID", covariant=True)  # ID type (typically str, UUID, or int)


@runtime_checkable
class EntityProtocol(Protocol, Generic[ID]):
    """
    Protocol defining the interface for domain entities.

    Entities are objects with a distinct identity that persists over time.
    They are defined by their identity rather than their attributes.

    Type parameters:
        ID: The type of the entity's identifier
    """

    @property
    def id(self) -> ID:
        """
        Get the unique identifier for this entity.

        Returns:
            The entity's ID
        """
        ...

    @property
    def created_at(self) -> datetime:
        """
        Get the timestamp when this entity was created.

        Returns:
            The creation timestamp
        """
        ...

    @property
    def updated_at(self) -> datetime:
        """
        Get the timestamp when this entity was last updated.

        Returns:
            The last update timestamp
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """
        Compare this entity with another by their IDs.

        Entities are considered equal if they have the same ID,
        regardless of their attribute values.

        Args:
            other: The object to compare with

        Returns:
            True if the entities have the same ID, False otherwise
        """
        ...

    def __hash__(self) -> int:
        """
        Get a hash value for this entity based on its ID.

        Returns:
            A hash value derived from the entity's ID
        """
        ...


@runtime_checkable
class AggregateRootProtocol(EntityProtocol[ID], Protocol[ID]):
    """
    Protocol defining the interface for aggregate roots.

    Aggregate roots are entities that serve as the entry point to an aggregate,
    which is a cluster of associated objects treated as a unit for data changes.
    They ensure the consistency of changes to the objects within the aggregate.

    Type parameters:
        ID: The type of the aggregate root's identifier
    """

    @property
    def version(self) -> int:
        """
        Get the current version of this aggregate.

        The version is incremented each time the aggregate is modified,
        and is used for optimistic concurrency control.

        Returns:
            The current version number
        """
        ...

    def add_event(self, event: Any) -> None:
        """
        Add a domain event to this aggregate.

        Domain events represent something that happened in the domain
        that is significant to the business.

        Args:
            event: The domain event to add
        """
        ...

    def clear_events(self) -> list[Any]:
        """
        Clear and return all pending events.

        This is typically called after events have been published.

        Returns:
            A list of all pending events
        """
        ...


@runtime_checkable
class ValueObjectProtocol(Protocol):
    """
    Protocol defining the interface for value objects.

    Value objects are objects that are defined by their attributes rather
    than their identity. They are immutable and have no identity.
    """

    def __eq__(self, other: Any) -> bool:
        """
        Compare this value object with another by their attributes.

        Value objects are considered equal if all their attributes are equal.

        Args:
            other: The object to compare with

        Returns:
            True if all attributes are equal, False otherwise
        """
        ...

    def __hash__(self) -> int:
        """
        Get a hash value for this value object based on its attributes.

        Returns:
            A hash value derived from the value object's attributes
        """
        ...
