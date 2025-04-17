"""
Core domain model classes for the uno framework.

This module provides the foundational domain model classes for the uno framework,
implementing a domain-driven design approach with modern Python patterns.
"""

from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import (
    Dict, Any, List, Optional, Set, Generic, TypeVar, Type, cast, 
    ClassVar, final
)
import json
import copy

from pydantic import BaseModel, Field, model_validator, ConfigDict

from uno.core.errors.base import AggregateInvariantViolationError, DomainValidationError
from uno.domain.protocols import (
    DomainEventProtocol, EntityProtocol, AggregateRootProtocol,
    ValueObjectProtocol, PrimitiveValueObjectProtocol
)

# Type variables
IdT = TypeVar('IdT')  # Type for entity identifiers
ValueT = TypeVar('ValueT')  # Type for value object values


class DomainEvent(BaseModel):
    """
    Base class for domain events.
    
    Domain events represent significant occurrences within the domain.
    They are immutable records of something that happened.
    """
    
    model_config = ConfigDict(frozen=True)
    
    # Standard event metadata
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(default_factory=lambda: cls_name_to_event_type(DomainEvent.__name__))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary.
        
        Returns:
            Dictionary representation of event
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """
        Create event from dictionary.
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            Domain event instance
        """
        return cls(**data)
    
    def to_json(self) -> str:
        """
        Convert event to JSON string.
        
        Returns:
            JSON string representation of event
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "DomainEvent":
        """
        Create event from JSON string.
        
        Args:
            json_str: JSON string containing event data
            
        Returns:
            Domain event instance
        """
        return cls.from_dict(json.loads(json_str))


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
        
        Returns:
            Self if validation passes
            
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
        # Use sorted tuple of values for hash
        return hash(tuple(sorted(self.model_dump().items())))
    
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


class Entity(BaseModel, Generic[IdT]):
    """
    Base class for all domain entities.
    
    Entities are distinguished by their identity, not their attributes.
    Two entities are considered equal if they have the same identity,
    regardless of their attributes.
    
    Type Parameters:
        IdT: The type of the entity's identifier
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: IdT = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Store domain events
    events: List[DomainEventProtocol] = Field(default_factory=list, exclude=True)
    
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
    
    def register_event(self, event: DomainEventProtocol) -> None:
        """
        Register a domain event to be published when the entity is saved.
        
        Args:
            event: The domain event to register
        """
        self.events.append(event)
    
    def clear_events(self) -> List[DomainEventProtocol]:
        """
        Clear and return all registered domain events.
        
        Returns:
            List of registered domain events
        """
        registered_events = copy.copy(self.events)
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
    
    @model_validator(mode='before')
    @classmethod
    def set_updated_at(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the updated_at field when the entity is modified.
        
        Args:
            data: Entity data
            
        Returns:
            Updated entity data
        """
        # Only set updated_at for existing entities being modified (with id and created_at)
        if isinstance(data, dict) and 'id' in data and 'created_at' in data:
            data['updated_at'] = datetime.now(timezone.utc)
        return data


class AggregateRoot(Entity[IdT]):
    """
    Base class for aggregate roots.
    
    Aggregate roots are entities that serve as the entry point to an aggregate.
    They ensure the consistency of the aggregate and are the only objects that
    repositories directly work with.
    
    Type Parameters:
        IdT: The type of the aggregate root's identifier
    """
    
    # Child entities - not part of equality/hash
    child_entities: Set[EntityProtocol] = Field(default_factory=set, exclude=True)
    
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
    
    def add_child_entity(self, entity: EntityProtocol) -> None:
        """
        Add a child entity to this aggregate.
        
        Args:
            entity: The child entity to add
        """
        self.child_entities.add(entity)
    
    def get_child_entities(self) -> Set[EntityProtocol]:
        """
        Get all child entities of this aggregate.
        
        Returns:
            The set of child entities
        """
        return copy.copy(self.child_entities)
    
    def get_all_events(self) -> List[DomainEventProtocol]:
        """
        Get all events from this aggregate and its child entities.
        
        Returns:
            List of all domain events
        """
        all_events = self.clear_events()
        
        # Collect events from child entities
        for child in self.child_entities:
            if hasattr(child, 'clear_events') and callable(child.clear_events):
                all_events.extend(child.clear_events())
        
        return all_events


class CommandResult:
    """
    Represents the result of executing a command.
    
    Commands can succeed or fail, and can produce domain events.
    """
    
    def __init__(
        self, 
        is_success: bool, 
        events: Optional[List[DomainEventProtocol]] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a command result.
        
        Args:
            is_success: Whether the command succeeded
            events: Optional list of domain events
            error: Optional error if the command failed
        """
        self.is_success = is_success
        self.events = events or []
        self.error = error
    
    @property
    def is_failure(self) -> bool:
        """
        Check if the command result is a failure.
        
        Returns:
            True if the command failed, False otherwise
        """
        return not self.is_success
    
    @classmethod
    def success(cls, events: Optional[List[DomainEventProtocol]] = None) -> 'CommandResult':
        """
        Create a successful command result.
        
        Args:
            events: Optional list of domain events
            
        Returns:
            Successful command result
        """
        return cls(is_success=True, events=events or [])
    
    @classmethod
    def failure(cls, error: Exception) -> 'CommandResult':
        """
        Create a failed command result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            Failed command result
        """
        return cls(is_success=False, error=error)


# Helper functions

def cls_name_to_event_type(cls_name: str) -> str:
    """
    Convert a class name to an event type.
    
    Args:
        cls_name: The class name to convert
        
    Returns:
        The event type
    """
    # Convert CamelCase to snake_case
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Common value objects

class Email(PrimitiveValueObject[str]):
    """Email address value object."""
    
    def validate(self) -> None:
        """
        Validate email address.
        
        Raises:
            ValueError: If validation fails
        """
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
        """
        Validate money.
        
        Raises:
            ValueError: If validation fails
        """
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
        """
        Validate address.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.street:
            raise ValueError("Street cannot be empty")
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.postal_code:
            raise ValueError("Postal code cannot be empty")
