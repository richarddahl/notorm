"""
Core domain model classes for the Uno framework.

This module contains the foundational domain model classes for implementing
a domain-driven design approach in the Uno framework.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, cast
from uuid import UUID, uuid4
from datetime import datetime
import json
import copy
from pydantic import BaseModel, ConfigDict, model_validator

from uno.domain.exceptions import AggregateInvariantViolationError, DomainValidationError


# Type variables
KeyT = TypeVar('KeyT')
ValueT = TypeVar('ValueT')

# Define valid types for primitive value objects
PrimitiveType = Union[str, int, float, bool, UUID, datetime, None]


class DomainEvent(BaseModel):
    """
    Base class for domain events.
    
    Domain events represent significant occurrences within the domain.
    They are immutable records of something that happened.
    """
    
    model_config = ConfigDict(frozen=True)
    
    # Standard event metadata
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = field(default="domain_event")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create event from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "DomainEvent":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass(kw_only=True)
class Entity(Generic[KeyT]):
    """
    Base class for all domain entities.
    
    Entities are distinguished by their identity, not their attributes.
    Two entities are considered equal if they have the same identity,
    regardless of their attributes.
    
    Type Parameters:
        KeyT: The type of the entity's identifier
    """
    
    id: KeyT = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Domain events are tracked but not part of entity state for equality/hash
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False, compare=False)
    
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
    
    def register_event(self, event: DomainEvent) -> None:
        """
        Register a domain event to be published when the entity is saved.
        
        Args:
            event: The domain event to register
        """
        self._events.append(event)
    
    def clear_events(self) -> List[DomainEvent]:
        """
        Clear and return all registered domain events.
        
        Returns:
            List of registered domain events
        """
        events = self._events.copy()
        self._events.clear()
        return events
    
    def update(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to a dictionary.
        
        Returns:
            Dictionary representation of entity
        """
        # Use dataclasses.asdict but filter out _events and other private fields
        result = asdict(self)
        return {k: v for k, v in result.items() if not k.startswith('_')}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """
        Create an entity from a dictionary.
        
        Args:
            data: Dictionary containing entity data
            
        Returns:
            Entity instance
        """
        # Filter out keys that are not in the entity's __init__ parameters
        init_params = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**init_params)


@dataclass(kw_only=True)
class AggregateRoot(Entity[KeyT], Generic[KeyT]):
    """
    Base class for aggregate roots.
    
    Aggregate roots are entities that serve as the entry point to an aggregate.
    They ensure the consistency of the aggregate and are the only objects that
    repositories directly work with.
    
    Type Parameters:
        KeyT: The type of the aggregate root's identifier
    """
    
    # Child entities - not part of equality/hash
    _child_entities: Set[Entity] = field(default_factory=set, init=False, repr=False, compare=False)
    
    # Version for optimistic concurrency control
    version: int = field(default=1)
    
    def check_invariants(self) -> None:
        """
        Check that all aggregate invariants are satisfied.
        
        This method should be overridden by derived classes to check
        that the aggregate is in a valid state.
        
        Raises:
            AggregateInvariantViolationError: If any invariant is violated
        """
        pass
    
    def apply_changes(self) -> None:
        """
        Apply any pending changes and ensure consistency.
        
        This method is called before saving the aggregate to ensure
        that all invariants are satisfied.
        
        Raises:
            AggregateInvariantViolationError: If any invariant is violated
        """
        self.check_invariants()
        self.update()
        self.version += 1
    
    def add_child_entity(self, entity: Entity) -> None:
        """
        Add a child entity to this aggregate.
        
        Args:
            entity: The child entity to add
        """
        self._child_entities.add(entity)
    
    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities of this aggregate.
        
        Returns:
            The set of child entities
        """
        return self._child_entities.copy()


@dataclass(frozen=True)
class ValueObject:
    """
    Base class for value objects.
    
    Value objects are immutable objects defined by their attributes.
    Two value objects are considered equal if all their attributes are equal.
    
    Value objects should be instantiated with all required attributes and
    should not be changed after creation.
    """
    
    def __post_init__(self) -> None:
        """
        Validate the value object after initialization.
        
        This method is automatically called after initialization
        to validate the value object's state.
        
        Raises:
            DomainValidationError: If validation fails
        """
        try:
            self.validate()
        except ValueError as e:
            raise DomainValidationError(str(e))
    
    def validate(self) -> None:
        """
        Validate the value object.
        
        This method should be overridden by derived classes to implement
        validation logic.
        
        Raises:
            ValueError: If validation fails
        """
        pass
    
    def equals(self, other: Any) -> bool:
        """
        Check if this value object equals another.
        
        Args:
            other: The object to compare with
            
        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __eq__(self, other: Any) -> bool:
        """
        Value objects are equal if they have the same type and all attributes are equal.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if equal, False otherwise
        """
        return self.equals(other)
    
    def __hash__(self) -> int:
        """
        Hash based on all attributes.
        
        Returns:
            Hash value
        """
        # Frozen dataclasses can be hashed by default
        return hash(tuple(self.__dict__.values()))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert value object to a dictionary.
        
        Returns:
            Dictionary representation of value object
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValueObject':
        """
        Create a value object from a dictionary.
        
        Args:
            data: Dictionary containing value object data
            
        Returns:
            Value object instance
        """
        # Filter out keys that are not in the value object's __init__ parameters
        init_params = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**init_params)


@dataclass(frozen=True)
class PrimitiveValueObject(ValueObject, Generic[ValueT]):
    """
    Value object that wraps a primitive value.
    
    Use this for domain values that need validation or semantic meaning
    beyond what a primitive type provides, e.g., EmailAddress, Money.
    
    Type Parameters:
        ValueT: The type of the primitive value
    """
    
    value: ValueT
    
    def __str__(self) -> str:
        """
        String representation of the primitive value.
        
        Returns:
            String representation
        """
        return str(self.value)
    
    @classmethod
    def create(cls, value: ValueT) -> 'PrimitiveValueObject[ValueT]':
        """
        Create a new primitive value object with validation.
        
        Args:
            value: The primitive value
            
        Returns:
            Primitive value object
            
        Raises:
            ValueError: If validation fails
        """
        return cls(value)


# Common value objects

@dataclass(frozen=True)
class Email(PrimitiveValueObject[str]):
    """Email address value object."""
    
    def validate(self) -> None:
        """Validate email address."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        if "@" not in self.value:
            raise ValueError("Email must contain @")
        if "." not in self.value.split("@")[1]:
            raise ValueError("Email must have a valid domain")


@dataclass(frozen=True)
class Money(ValueObject):
    """Money value object."""
    
    amount: float
    currency: str
    
    def validate(self) -> None:
        """Validate money."""
        if self.currency not in {"USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"}:
            raise ValueError(f"Unsupported currency: {self.currency}")
    
    def add(self, other: 'Money') -> 'Money':
        """
        Add money.
        
        Args:
            other: Money to add
            
        Returns:
            New money value
            
        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """
        Subtract money.
        
        Args:
            other: Money to subtract
            
        Returns:
            New money value
            
        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)


@dataclass(frozen=True)
class Address(ValueObject):
    """Address value object."""
    
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    
    def validate(self) -> None:
        """Validate address."""
        if not self.street:
            raise ValueError("Street cannot be empty")
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.postal_code:
            raise ValueError("Postal code cannot be empty")