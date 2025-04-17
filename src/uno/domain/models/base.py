"""
Base domain entities and value objects.

This module provides the base classes for the domain model, including
Entity, AggregateRoot, ValueObject, DomainEvent, and related classes.
"""

from typing import (
    Any, Dict, Generic, List, Optional, Set, TypeVar, ClassVar, Type, Union
)
from datetime import datetime, timezone
from uuid import uuid4, UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict, EmailStr, field_serializer

T = TypeVar('T')
ID = TypeVar('ID')


class DomainEvent(BaseModel):
    """Base class for all domain events."""
    
    model_config = ConfigDict(frozen=True)
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(default="domain_event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create event from dictionary."""
        return cls(**data)


class ValueObject(BaseModel):
    """Base class for all value objects."""
    
    model_config = ConfigDict(frozen=True)
    
    def equals(self, other: Any) -> bool:
        """Check if this value object equals another."""
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()
    
    def validate(self) -> None:
        """Validate the value object."""
        # Validation is handled by Pydantic
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert value object to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValueObject":
        """Create value object from dictionary."""
        return cls(**data)


class PrimitiveValueObject(ValueObject, Generic[T]):
    """
    Base class for value objects that wrap a single primitive value.
    
    This is a convenient base class for value objects that are essentially
    wrappers around a single primitive value, like Email or Money.
    """
    
    value: T
    
    @classmethod
    def create(cls, value: T) -> "PrimitiveValueObject[T]":
        """Create a primitive value object."""
        return cls(value=value)


class Email(PrimitiveValueObject[str]):
    """Email value object."""
    
    value: EmailStr
    
    @field_validator('value')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower() if isinstance(v, str) else v


class Money(PrimitiveValueObject[float]):
    """Money value object."""
    
    value: float
    currency: str = "USD"
    
    @field_validator('value')
    @classmethod
    def validate_money(cls, v: float) -> float:
        """Validate money value is positive and round to 2 decimal places."""
        if v < 0:
            raise ValueError("Money value cannot be negative")
        return round(v, 2)
    
    def add(self, other: "Money") -> "Money":
        """Add money values."""
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(value=self.value + other.value, currency=self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        """Subtract money values."""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        result = self.value - other.value
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(value=result, currency=self.currency)
    
    def multiply(self, factor: float) -> "Money":
        """Multiply money by a factor."""
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        return Money(value=self.value * factor, currency=self.currency)


class Address(ValueObject):
    """Address value object."""
    
    street: str
    city: str
    state: str
    zip: str
    country: str = "US"
    
    @property
    def formatted(self) -> str:
        """Return formatted address string."""
        return f"{self.street}, {self.city}, {self.state} {self.zip}, {self.country}"


class Entity(BaseModel, Generic[ID]):
    """Base class for all domain entities."""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="ignore",
    )
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Private fields for storing events (won't be in JSON output)
    _events: List[DomainEvent] = Field(default_factory=list, exclude=True)
    
    def register_event(self, event: DomainEvent) -> None:
        """
        Register a domain event.
        
        Args:
            event: The domain event to register
        """
        self._events.append(event)
    
    def clear_events(self) -> List[DomainEvent]:
        """
        Clear and return all registered domain events.
        
        Returns:
            List of domain events
        """
        events = self._events.copy()
        self._events.clear()
        return events
    
    def update(self) -> None:
        """Update the entity."""
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return self.model_dump(exclude={"_events"})
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create entity from dictionary."""
        return cls(**data)


class AggregateRoot(Entity[ID]):
    """Base class for all aggregate roots."""
    
    version: int = Field(default=1)
    _child_entities: Set[Entity] = Field(default_factory=set, exclude=True)
    
    def check_invariants(self) -> None:
        """Check that all aggregate invariants are satisfied."""
        pass
    
    def apply_changes(self) -> None:
        """Apply changes and ensure consistency."""
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
        self.check_invariants()
    
    def add_child_entity(self, entity: Entity) -> None:
        """
        Add a child entity.
        
        Args:
            entity: The child entity to add
        """
        self._child_entities.add(entity)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities.
        
        Returns:
            Set of child entities
        """
        return self._child_entities.copy()


class CommandResult(BaseModel):
    """Result of a domain command operation."""
    
    is_success: bool
    events: List[DomainEvent] = Field(default_factory=list)
    error: Optional[Exception] = None
    message: Optional[str] = None
    
    @property
    def is_failure(self) -> bool:
        """
        Check if the command result is a failure.
        
        Returns:
            True if the command failed, False otherwise
        """
        return not self.is_success
    
    @classmethod
    def success(cls, events: Optional[List[DomainEvent]] = None, message: Optional[str] = None) -> "CommandResult":
        """
        Create a successful command result.
        
        Args:
            events: Optional list of domain events
            message: Optional success message
            
        Returns:
            A successful command result
        """
        return cls(
            is_success=True,
            events=events or [],
            message=message
        )
    
    @classmethod
    def failure(cls, error: Exception, message: Optional[str] = None) -> "CommandResult":
        """
        Create a failed command result.
        
        Args:
            error: The error that caused the failure
            message: Optional error message
            
        Returns:
            A failed command result
        """
        return cls(
            is_success=False,
            error=error,
            message=message or str(error)
        )