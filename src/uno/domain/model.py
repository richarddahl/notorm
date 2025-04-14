"""
Core domain model classes for the Uno framework.

This module contains the foundational domain model classes for implementing
a domain-driven design approach in the Uno framework.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, cast
from uuid import UUID, uuid4
from datetime import datetime, timezone
import json
import copy
from pydantic import BaseModel, ConfigDict, model_validator, Field

from uno.core.errors.base import AggregateInvariantViolationError, DomainValidationError


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
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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


class Entity(BaseModel, Generic[KeyT]):
    """
    Base class for all domain entities.
    
    Entities are distinguished by their identity, not their attributes.
    Two entities are considered equal if they have the same identity,
    regardless of their attributes.
    
    Type Parameters:
        KeyT: The type of the entity's identifier
    """
    
    model_config = ConfigDict(extra="allow")
    
    id: KeyT = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Use private attribute for events
    events: List[DomainEvent] = Field(default_factory=list, exclude=True)
    
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
        self.events.append(event)
    
    def clear_events(self) -> List[DomainEvent]:
        """
        Clear and return all registered domain events.
        
        Returns:
            List of registered domain events
        """
        registered_events = self.events.copy()
        self.events.clear()
        return registered_events
    
    def update(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to a dictionary.
        
        Returns:
            Dictionary representation of entity
        """
        # Use pydantic's model_dump but exclude events
        return self.model_dump(exclude_none=False, exclude={'events'})
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """
        Create an entity from a dictionary.
        
        Args:
            data: Dictionary containing entity data
            
        Returns:
            Entity instance
        """
        # Use pydantic's model validation
        return cls(**data)


class AggregateRoot(Entity[KeyT]):
    """
    Base class for aggregate roots.
    
    Aggregate roots are entities that serve as the entry point to an aggregate.
    They ensure the consistency of the aggregate and are the only objects that
    repositories directly work with.
    
    Type Parameters:
        KeyT: The type of the aggregate root's identifier
    """
    
    # Child entities - not part of equality/hash
    child_entities: Set[Entity] = Field(default_factory=set, exclude=True)
    
    # Version for optimistic concurrency control
    version: int = Field(default=1)
    
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
        self.child_entities.add(entity)
    
    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities of this aggregate.
        
        Returns:
            The set of child entities
        """
        return self.child_entities.copy()


class ValueObject(BaseModel):
    """
    Base class for value objects.
    
    Value objects are immutable objects defined by their attributes.
    Two value objects are considered equal if all their attributes are equal.
    
    Value objects should be instantiated with all required attributes and
    should not be changed after creation.
    """
    
    model_config = ConfigDict(frozen=True)
    
    @model_validator(mode='after')
    def validate_value_object(self) -> 'ValueObject':
        """
        Validate the value object after initialization.
        
        This method is automatically called after initialization
        to validate the value object's state.
        
        Raises:
            DomainValidationError: If validation fails
        """
        try:
            self.validate()
            return self
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
        return self.model_dump() == other.model_dump()
    
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
        # Use tuple of values for hash
        return hash(tuple(self.model_dump().values()))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert value object to a dictionary.
        
        Returns:
            Dictionary representation of value object
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValueObject':
        """
        Create a value object from a dictionary.
        
        Args:
            data: Dictionary containing value object data
            
        Returns:
            Value object instance
        """
        return cls(**data)


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
        return cls(value=value)


# Common value objects

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