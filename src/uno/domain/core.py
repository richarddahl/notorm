"""
Core domain components for the Uno framework.

This module provides the foundational classes for implementing a domain-driven design
approach in the Uno framework, including entities, value objects, aggregates, and events.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, TypeVar, Generic, Set, ClassVar

from pydantic import BaseModel, Field, ConfigDict, model_validator


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


class DomainEvent(BaseModel):
    """
    Base class for domain events.
    
    Domain events represent something significant that occurred within the domain.
    They are used to communicate between different parts of the application
    and to enable event-driven architectures.
    """
    
    model_config = ConfigDict(frozen=True)
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(default="domain_event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create an event from a dictionary."""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to a dictionary."""
        return self.model_dump()


class ValueObject(BaseModel):
    """
    Base class for value objects.
    
    Value objects are immutable objects that contain attributes but lack a conceptual identity.
    They are used to represent concepts within your domain that are defined by their attributes
    rather than by an identity.
    
    Examples include Money, Address, and DateRange.
    """
    
    model_config = ConfigDict(frozen=True)
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()
    
    def __hash__(self):
        return hash(tuple(sorted(self.model_dump().items())))


class Entity(BaseModel):
    """
    Base class for domain entities.
    
    Entities are objects that have a distinct identity that runs through time and
    different states. They are defined by their identity, not by their attributes.
    
    Examples include User, Order, and Product.
    """
    
    # Allow arbitrary types to support rich domain models
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    @model_validator(mode='before')
    def set_updated_at(self, values):
        """Update the updated_at field whenever the entity is modified."""
        # Only set updated_at for existing entities that are being modified
        if values.get('id') and values.get('created_at'):
            values['updated_at'] = datetime.utcnow()
        return values


T = TypeVar('T', bound=Entity)


class AggregateRoot(Entity, Generic[T]):
    """
    Base class for aggregate roots.
    
    Aggregate roots are the entry point to an aggregate - a cluster of domain objects
    that can be treated as a single unit. They encapsulate related domain objects and
    define boundaries for transactions and consistency.
    
    Examples include Order (which contains OrderLines), User (which contains Addresses).
    """
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # Use normal instance attributes instead of Pydantic fields
        # to avoid the underscore naming restriction
        self._events: List[DomainEvent] = []
        self._child_entities: Set[Entity] = set()
    
    def add_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to this aggregate.
        
        Domain events are collected within the aggregate and can be processed
        after the aggregate is saved.
        
        Args:
            event: The domain event to add
        """
        self._events.append(event)
    
    def clear_events(self) -> List[DomainEvent]:
        """
        Clear all domain events from this aggregate.
        
        Returns:
            The list of events that were cleared
        """
        events = self._events.copy()
        self._events.clear()
        return events
    
    def register_child_entity(self, entity: Entity) -> None:
        """
        Register a child entity with this aggregate root.
        
        Args:
            entity: The child entity to register
        """
        self._child_entities.add(entity)
    
    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities of this aggregate root.
        
        Returns:
            The set of child entities
        """
        return self._child_entities