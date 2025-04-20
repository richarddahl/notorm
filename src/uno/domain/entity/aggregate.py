"""
Aggregate Root implementation for domain entities.

This module provides the AggregateRoot base class, which is responsible for maintaining
consistency across an aggregate and managing domain events. Aggregates are clusters
of domain objects that should be treated as a single unit for data changes.
"""

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Set, TypeVar, Generic, ClassVar, cast
from uuid import uuid4

from pydantic import Field, model_validator

from uno.core.events import Event
from uno.domain.entity.base import EntityBase

# Type variables
ID = TypeVar('ID')  # ID type
E = TypeVar('E', bound=EntityBase)  # Entity type


class AggregateRoot(EntityBase[ID]):
    """
    Base class for aggregate roots.
    
    An aggregate root serves as the entry point to an aggregate, which is a cluster
    of associated objects treated as a unit for data changes. It enforces invariants
    and maintains consistency across the aggregate.
    
    Features:
    - Optimistic concurrency with versioning
    - Domain event collection and management
    - Invariant checking and enforcement
    - Child entity management
    """
    
    # Version for optimistic concurrency control
    version: int = Field(default=1)
    
    # Child entities and events - excluded from serialization
    _child_entities: Set[EntityBase] = Field(default_factory=set, exclude=True)
    _events: List[Event] = Field(default_factory=list, exclude=True)
    
    @model_validator(mode='after')
    def validate_aggregate(self) -> 'AggregateRoot':
        """Validate the aggregate root after initialization."""
        # Check that the aggregate is in a valid state
        self.check_invariants()
        return self
    
    def check_invariants(self) -> None:
        """
        Check that the aggregate invariants are maintained.
        
        Override this method to implement specific invariant checks.
        
        Raises:
            ValueError: If invariants are violated
        """
        pass
    
    def add_event(self, event: Event) -> None:
        """
        Add a domain event to this aggregate.
        
        Args:
            event: The domain event to add
        """
        self._events.append(event)
    
    def clear_events(self) -> List[Event]:
        """
        Clear and return all pending domain events.
        
        Returns:
            The list of pending domain events
        """
        events = list(self._events)
        self._events.clear()
        return events
    
    @property
    def events(self) -> List[Event]:
        """
        Get all domain events without clearing them.
        
        Returns:
            The list of pending domain events
        """
        return list(self._events)

    def get_uncommitted_events(self) -> List[Event]:
        """
        Protocol-compliant alias for retrieving all uncommitted domain events (does not clear them).
        Returns:
            The list of pending domain events
        """
        return self.events
    
    def add_child_entity(self, entity: E) -> None:
        """
        Register a child entity with this aggregate.
        
        Args:
            entity: The child entity to register
        """
        self._child_entities.add(entity)
    
    def remove_child_entity(self, entity: E) -> None:
        """
        Remove a child entity from this aggregate.
        
        Args:
            entity: The child entity to remove
        """
        if entity in self._child_entities:
            self._child_entities.remove(entity)
    
    def get_child_entities(self) -> Set[EntityBase]:
        """
        Get all child entities in this aggregate.
        
        Returns:
            The set of child entities
        """
        return self._child_entities.copy()
    
    def apply_changes(self) -> None:
        """
        Apply any pending changes to the aggregate.
        
        This method ensures invariants are maintained and version is incremented.
        It should be called before persisting the aggregate.
        """
        # Check that the aggregate is in a valid state
        self.check_invariants()
        
        # Increment version
        self.version += 1
        
        # Update timestamp
        self.mark_modified()
    
    def mark_modified(self) -> None:
        """
        Mark the aggregate root and all child entities as modified.
        
        This ensures the entire aggregate's timestamps are consistent.
        """
        # Update own timestamp
        super().mark_modified()
        
        # Update child entities
        for entity in self._child_entities:
            if hasattr(entity, "mark_modified") and callable(getattr(entity, "mark_modified")):
                entity.mark_modified()