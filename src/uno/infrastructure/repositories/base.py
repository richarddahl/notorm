"""
Extended repository implementations for the Uno framework.

This module provides additional repository capabilities beyond the core base
repository classes, particularly for event collection and aggregate handling.
"""

import logging
from typing import Any, TypeVar, Generic
from uno.core.base.repository import BaseRepository
from uno.core.events import DomainEventProtocol
from uno.domain.core import AggregateRoot
T = TypeVar("T")  # Entity type
A = TypeVar("A", bound=AggregateRoot)  # Aggregate type
ID = TypeVar("ID")  # ID type


class EventCollectingRepository(BaseRepository[T, ID], Generic[T, ID]):
    """
    Repository implementation that collects domain events.
    
    Useful for aggregate repositories that need to track domain events.
    """

    def __init__(
        self,
        entity_type: type[T],
        logger: logging.Logger | None = None
    ):
        """Initialize with empty events collection."""
        super().__init__(entity_type, logger)
        self._pending_events: list[DomainEventProtocol] = []

    def collect_events(self) -> list[DomainEventProtocol]:
        """
        Collect and clear pending domain events.
        
        Returns:
            List of pending domain events
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    def _collect_events_from_entity(self, entity: Any) -> None:
        """
        Collect events from an entity that supports event collection.
        
        Args:
            entity: The entity to collect events from
        """
        if hasattr(entity, "clear_events") and callable(entity.clear_events):
            events = entity.clear_events()
            self._pending_events.extend(events)

        # Collect from child entities if this is an aggregate
        if hasattr(entity, "get_child_entities") and callable(entity.get_child_entities):
            for child in entity.get_child_entities():
                self._collect_events_from_entity(child)


class AggregateRepository(EventCollectingRepository[A, ID], Generic[A, ID]):
    """
    Repository specifically for aggregate roots.
    
    Provides specialized handling for aggregates, including version checks and event collection.
    """
    
    async def save(self, aggregate: A) -> A:
        """
        Save an aggregate (create or update) with event collection.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
        """
        # Apply changes to ensure invariants and increment version if needed
        if hasattr(aggregate, "apply_changes") and callable(aggregate.apply_changes):
            aggregate.apply_changes()
        
        # Collect events before saving
        self._collect_events_from_entity(aggregate)
        
        # Save using standard save method
        return await super().save(aggregate)
    
    async def update(self, aggregate: A) -> A:
        """
        Update an aggregate with version checking.
        
        Args:
            aggregate: The aggregate to update
            
        Returns:
            The updated aggregate
        """
        # Collect events before updating
        self._collect_events_from_entity(aggregate)
        
        # Delegate to implementation
        return await super().update(aggregate)