"""
Domain-driven design (DDD) building blocks for the Uno framework.

This module implements the core DDD building blocks: entities, aggregates,
value objects, and domain services.
"""

from abc import ABC, abstractmethod
import copy
from dataclasses import dataclass, field, fields, is_dataclass
from typing import (
    TypeVar,
    Generic,
    List,
    Dict,
    Any,
    Optional,
    Type,
    ClassVar,
    Set,
    Union,
    Protocol,
    runtime_checkable,
    TYPE_CHECKING,
)

# Import DomainEvent from protocols only when type checking
if TYPE_CHECKING:
    from uno.core.protocols import DomainEvent
else:
    # Define the protocols we need directly for runtime
    @runtime_checkable
    class DomainEvent(Protocol):
        """Protocol for domain events."""

        event_id: str
        event_type: str
        timestamp: float
        aggregate_id: Optional[str]

        def to_dict(self) -> Dict[str, Any]: ...


# Define the protocols we need directly rather than importing them
@runtime_checkable
class Entity(Protocol):
    """Protocol for entities."""

    id: Any

    def __eq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...


@runtime_checkable
class AggregateRoot(Entity, Protocol):
    """Protocol for aggregate roots."""

    events: List["DomainEvent"]

    def register_event(self, event: "DomainEvent") -> None: ...
    def clear_events(self) -> List["DomainEvent"]: ...


@runtime_checkable
class ValueObject(Protocol):
    """Protocol for value objects."""

    def equals(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...


T = TypeVar("T")
KeyT = TypeVar("KeyT")
EntityT = TypeVar("EntityT", bound=Entity)


@dataclass
class BaseEntity(Generic[KeyT]):
    """Base class for entities."""

    id: KeyT

    def __eq__(self, other: Any) -> bool:
        """
        Check if this entity equals another entity.

        Two entities are equal if they have the same type and ID.

        Args:
            other: The other entity

        Returns:
            True if the entities are equal, False otherwise
        """
        if not isinstance(other, BaseEntity):
            return False
        return self.__class__ == other.__class__ and self.id == other.id

    def __hash__(self) -> int:
        """
        Hash the entity.

        Returns:
            The hash of the entity's type and ID
        """
        return hash((self.__class__, self.id))


@dataclass
class AggregateEntity(Generic[KeyT]):
    """Base class for aggregate entities."""

    id: KeyT
    events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __eq__(self, other: Any) -> bool:
        """
        Check if this aggregate equals another aggregate.

        Two aggregates are equal if they have the same type and ID.

        Args:
            other: The other aggregate

        Returns:
            True if the aggregates are equal, False otherwise
        """
        if not isinstance(other, AggregateEntity):
            return False
        return self.__class__ == other.__class__ and self.id == other.id

    def __hash__(self) -> int:
        """
        Hash the aggregate.

        Returns:
            The hash of the aggregate's type and ID
        """
        return hash((self.__class__, self.id))

    def register_event(self, event: "DomainEvent") -> None:
        """
        Register a domain event to be published after the aggregate is saved.

        Args:
            event: The event to register
        """
        self.events.append(event)

    def clear_events(self) -> List["DomainEvent"]:
        """
        Clear and return all registered events.

        Returns:
            The list of registered events
        """
        events = copy.copy(self.events)
        self.events.clear()
        return events


@dataclass
class BaseValueObject:
    """Base class for value objects."""

    def equals(self, other: Any) -> bool:
        """
        Check if this value object equals another value object.

        Two value objects are equal if they have the same type and the same values.

        Args:
            other: The other value object

        Returns:
            True if the value objects are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False

        # For dataclasses, compare all fields
        if is_dataclass(self) and is_dataclass(other):
            for f in fields(self):
                if getattr(self, f.name) != getattr(other, f.name):
                    return False
            return True

        # For non-dataclasses, compare __dict__
        return self.__dict__ == other.__dict__

    def __eq__(self, other: Any) -> bool:
        """
        Check if this value object equals another object.

        Args:
            other: The other object

        Returns:
            True if the objects are equal, False otherwise
        """
        return self.equals(other)


class DomainService:
    """Base class for domain services."""

    def __init__(self) -> None:
        """Initialize the domain service."""
        pass


class Repository(Generic[EntityT, KeyT], ABC):
    """Base class for repositories."""

    @abstractmethod
    async def get(self, id: KeyT) -> Optional[EntityT]:
        """
        Get an entity by its ID.

        Args:
            id: The entity ID

        Returns:
            The entity, or None if not found
        """
        pass

    @abstractmethod
    async def save(self, entity: EntityT) -> None:
        """
        Save an entity.

        Args:
            entity: The entity to save
        """
        pass

    @abstractmethod
    async def delete(self, id: KeyT) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id: The entity ID

        Returns:
            True if the entity was deleted, False otherwise
        """
        pass


class IdentityGenerator(Generic[KeyT], ABC):
    """Base class for identity generators."""

    @abstractmethod
    def next_id(self) -> KeyT:
        """
        Generate a new unique identifier.

        Returns:
            A new unique identifier
        """
        pass

    @abstractmethod
    def parse(self, id_str: str) -> KeyT:
        """
        Parse a string into an identifier.

        Args:
            id_str: The string to parse

        Returns:
            The parsed identifier
        """
        pass


class DomainValidator(ABC):
    """Base class for domain validators."""

    def __init__(self, next_validator: Optional["DomainValidator"] = None):
        """
        Initialize the validator.

        Args:
            next_validator: The next validator in the chain
        """
        self.next_validator = next_validator

    def validate(self, entity: Any) -> List[str]:
        """
        Validate an entity.

        This implementation uses the Chain of Responsibility pattern to chain
        validators together.

        Args:
            entity: The entity to validate

        Returns:
            A list of validation errors, or an empty list if validation passed
        """
        errors = self._validate(entity)

        if self.next_validator:
            errors.extend(self.next_validator.validate(entity))

        return errors

    @abstractmethod
    def _validate(self, entity: Any) -> List[str]:
        """
        Perform validation on an entity.

        Args:
            entity: The entity to validate

        Returns:
            A list of validation errors, or an empty list if validation passed
        """
        pass
