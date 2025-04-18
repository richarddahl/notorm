"""
Domain entity base classes.

This module provides base classes for domain entities, aggregate roots,
and value objects.
"""

import uuid
from abc import ABC
from typing import Any, Dict, List, Optional, Set, TypeVar, Generic, ClassVar
from datetime import datetime, UTC

from pydantic import BaseModel, Field

from uno.core.errors.result import Result

# Reusable type variables
T = TypeVar("T")  # Generic type
ID = TypeVar("ID")  # ID type


class ValueObject(BaseModel):
    """
    Base class for value objects.
    
    Value objects are immutable objects that represent concepts in the domain,
    defined by their attributes rather than their identity.
    """
    
    class Config:
        """Pydantic configuration for value objects."""
        frozen = True  # Value objects are immutable
    
    def equals(self, other: Any) -> bool:
        """
        Check if this value object equals another.
        
        Two value objects are equal if they have the same type and attribute values.
        
        Args:
            other: The other value object to compare
            
        Returns:
            True if the objects are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        
        return self.model_dump() == other.model_dump()


class Entity(BaseModel):
    """
    Base class for domain entities.
    
    Entities are objects with a distinct identity that runs through time and
    different states, defined primarily by their identity rather than attributes.
    """
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration for entities."""
        validate_assignment = True
    
    def equals(self, other: Any) -> bool:
        """
        Check if this entity equals another.
        
        Two entities are equal if they have the same type and ID.
        
        Args:
            other: The other entity to compare
            
        Returns:
            True if the entities are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        
        return self.id == other.id
    
    def update(self) -> None:
        """
        Update the entity's updated_at timestamp.
        
        This should be called whenever an entity is modified.
        """
        self.updated_at = datetime.now(UTC)


class AggregateRoot(Entity):
    """
    Base class for aggregate roots.
    
    Aggregate roots are special entities that serve as the entry point to an aggregate,
    which is a cluster of associated objects treated as a unit for data changes.
    """
    
    version: int = Field(default=1)
    _events: List[Any] = []
    _child_entities: Set[Entity] = set()
    
    def add_event(self, event: Any) -> None:
        """
        Add a domain event to this aggregate.
        
        Args:
            event: The domain event to add
        """
        self._events.append(event)
    
    def clear_events(self) -> List[Any]:
        """
        Clear and return all pending domain events.
        
        Returns:
            The list of pending domain events
        """
        events = list(self._events)
        self._events.clear()
        return events
    
    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities in this aggregate.
        
        Returns:
            The set of child entities
        """
        return self._child_entities
    
    def register_child_entity(self, entity: Entity) -> None:
        """
        Register a child entity with this aggregate.
        
        Args:
            entity: The child entity to register
        """
        self._child_entities.add(entity)
    
    def apply_changes(self) -> None:
        """
        Apply any pending changes to the aggregate.
        
        This method ensures invariants are maintained and version is incremented.
        It should be called before persisting the aggregate.
        """
        # Increment version
        self.version += 1
        
        # Update timestamp
        self.update()
    
    def update(self) -> None:
        """
        Update the aggregate and all child entities.
        
        This ensures the entire aggregate's timestamps are consistent.
        """
        # Update own timestamp
        super().update()
        
        # Update child entities
        for entity in self._child_entities:
            if hasattr(entity, "update") and callable(getattr(entity, "update")):
                entity.update()