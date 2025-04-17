"""
Core domain components for the Uno framework.

This module provides the foundational classes for implementing a domain-driven design
approach in the Uno framework, including entities, value objects, aggregates, and events.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import (
    Dict,
    Any,
    Optional,
    List,
    TypeVar,
    Generic,
    Set,
    ClassVar,
    Type,
    Union,
    cast,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, model_validator

# Define types that can be used for primitive value objects
PrimitiveType = Union[str, int, float, bool, UUID, datetime, None]

# Type variables
T_ID = TypeVar("T_ID")  # Entity ID type
T = TypeVar("T", bound="Entity")  # Entity type
T_Child = TypeVar("T_Child", bound="Entity")  # Child entity type
E = TypeVar("E", bound="UnoDomainEvent")  # Event type
V = TypeVar("V")  # Value type for primitive value objects


class DomainException(Exception):
    """
    Base exception for domain-related errors.

    Domain exceptions represent business rule violations or domain logic errors.
    They should be specific and meaningful to the domain.
    """

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        """
        Initialize a domain exception.

        Args:
            message: A descriptive error message
            code: An error code for categorizing the error
        """
        self.code = code
        super().__init__(message)


# Import the canonical domain event implementation
import warnings
from uno.core.unified_events import UnoDomainEvent as CanonicalUnoDomainEvent

# Alias the canonical implementation with a deprecation warning
class UnoDomainEvent(CanonicalUnoDomainEvent):
    """
    Base class for domain events. (DEPRECATED)
    
    This is a compatibility alias for UnoDomainEvent from unified_events.
    Domain events represent something significant that occurred within the domain.
    They are immutable records of what happened, used to communicate between
    different parts of the application.
    """
    
    def __new__(cls, *args, **kwargs):
        warnings.warn(
            "UnoDomainEvent in uno.domain.core is deprecated. "
            "Please use UnoDomainEvent from uno.core.unified_events instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return super().__new__(cls, *args, **kwargs)


class ValueObject(BaseModel):
    """
    Base class for value objects.

    Value objects:
    - Are immutable objects defined by their attributes
    - Have no identity
    - Are equatable by their attributes
    - Cannot be changed after creation

    Examples include Money, Address, and DateRange.
    """

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_value_object(self) -> "ValueObject":
        """
        Validate the value object after initialization.

        This method is automatically called after initialization
        to validate the value object's state.

        Returns:
            The validated value object

        Raises:
            ValueError: If validation fails
        """
        self.validate()
        return self

    def validate(self) -> None:
        """
        Validate the value object.

        Override this method to implement specific validation logic.

        Raises:
            ValueError: If validation fails
        """
        pass

    def __eq__(self, other: Any) -> bool:
        """
        Value objects are equal if they have the same type and attributes.

        Args:
            other: Object to compare with

        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """
        Hash based on all attributes.

        Returns:
            Hash value
        """
        # Use sorted items to ensure consistent hash
        return hash(tuple(sorted(self.model_dump().items())))


class PrimitiveValueObject(ValueObject, Generic[V]):
    """
    Value object that wraps a primitive value.

    Use this for domain values that need validation or semantic meaning
    beyond what a primitive type provides, e.g., EmailAddress, Money.

    Type Parameters:
        V: The type of the primitive value
    """

    value: V

    def __str__(self) -> str:
        """
        String representation of the primitive value.

        Returns:
            String representation
        """
        return str(self.value)

    @classmethod
    def create(cls, value: V) -> "PrimitiveValueObject[V]":
        """
        Create a new primitive value object.

        Args:
            value: The primitive value

        Returns:
            Primitive value object

        Raises:
            ValueError: If validation fails
        """
        return cls(value=value)


class Entity(BaseModel, Generic[T_ID]):
    """
    Base class for domain entities.

    Entities:
    - Have a distinct identity that persists through state changes
    - Are equatable by their identity, not their attributes
    - May change over time
    - Can register domain events

    Examples include User, Order, and Product.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: T_ID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None

    # Domain events - excluded from serialization
    _events: List[UnoDomainEvent] = Field(default_factory=list, exclude=True)

    def __eq__(self, other: Any) -> bool:
        """
        Entities are equal if they have the same type and ID.

        Args:
            other: Object to compare with

        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash based on the entity's ID.

        Returns:
            Hash value
        """
        return hash(self.id)

    @model_validator(mode="before")
    def set_updated_at(cls, values):
        """Update the updated_at field whenever the entity is modified."""
        # Only set updated_at for existing entities that are being modified
        if isinstance(values, dict) and values.get("id") and values.get("created_at"):
            values["updated_at"] = datetime.now(UTC)
        return values

    def add_event(self, event: UnoDomainEvent) -> None:
        """
        Add a domain event to this entity.

        Events represent significant changes that have occurred to the entity.
        They will be published when the entity is saved.

        Args:
            event: The domain event to add
        """
        self._events.append(event)

    def clear_events(self) -> List[UnoDomainEvent]:
        """
        Clear and return all domain events.

        Returns:
            The list of events that were cleared
        """
        events = list(self._events)
        self._events.clear()
        return events

    def get_events(self) -> List[UnoDomainEvent]:
        """
        Get all domain events without clearing them.

        Returns:
            The list of events
        """
        return list(self._events)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to a dictionary.

        Returns:
            Dictionary representation of entity
        """
        # Exclude private fields and events
        return self.model_dump(exclude={"_events"})

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """
        Create an entity from a dictionary.

        Args:
            data: Dictionary containing entity data

        Returns:
            Entity instance
        """
        return cls(**data)


class AggregateRoot(Entity[T_ID]):
    """
    Base class for aggregate roots.

    Aggregate Roots:
    - Are entities that are the root of an aggregate
    - Maintain consistency boundaries
    - Manage lifecycle of child entities
    - Enforce invariants across the aggregate
    - Coordinate domain events for the aggregate

    Examples include Order (containing OrderItems), User (containing Addresses).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Version for optimistic concurrency control
    version: int = Field(default=1)

    # Child entities - excluded from serialization
    _child_entities: Set[Entity] = Field(default_factory=set, exclude=True)

    def check_invariants(self) -> None:
        """
        Check that the aggregate invariants are maintained.

        Override this method to implement specific invariant checks.

        Raises:
            ValueError: If invariants are violated
        """
        pass

    def apply_changes(self) -> None:
        """
        Apply any pending changes and ensure consistency.

        This method should be called before saving the aggregate to ensure
        that it is in a valid state and to update metadata.

        Raises:
            ValueError: If invariants are violated
        """
        self.check_invariants()
        self.updated_at = datetime.now(UTC)
        self.version += 1

    def add_child_entity(self, entity: Entity) -> None:
        """
        Register a child entity with this aggregate root.

        Args:
            entity: The child entity to register
        """
        self._child_entities.add(entity)

    def remove_child_entity(self, entity: Entity) -> None:
        """
        Remove a child entity from this aggregate root.

        Args:
            entity: The child entity to remove
        """
        self._child_entities.discard(entity)

    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities of this aggregate root.

        Returns:
            The set of child entities
        """
        return self._child_entities.copy()
