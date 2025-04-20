"""
Extended repository implementations for the Uno framework.

This module provides additional repository capabilities beyond the core base
repository classes, particularly for event collection and aggregate handling.
"""

import logging
from typing import Any, TypeVar, Generic
from uno.core.base.repository import BaseRepository
from uno.core.errors.result import Result
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

    def __init__(self, entity_type: type[T], logger: logging.Logger | None = None):
        """Initialize with empty events collection."""
        super().__init__(entity_type, logger)
        self._pending_events: list[DomainEventProtocol] = []

    def collect_events(self) -> Result[list[DomainEventProtocol], Exception]:
        """
        Collect and clear pending domain events.
        Returns Result monad.
        """
        try:
            events = list(self._pending_events)
            self._pending_events.clear()
            return Success(events)
        except Exception as e:
            return Failure(e)

    def _collect_events_from_entity(self, entity: Any) -> Result[None, Exception]:
        """
        Collect events from an entity that supports event collection. Returns Result.
        """
        try:
            if hasattr(entity, "clear_events") and callable(entity.clear_events):
                events = entity.clear_events()
                self._pending_events.extend(events)
            if hasattr(entity, "get_child_entities") and callable(
                entity.get_child_entities
            ):
                for child in entity.get_child_entities():
                    self._collect_events_from_entity(child)
            return Success(None)
        except Exception as e:
            return Failure(e)


class AggregateRepository(EventCollectingRepository[A, ID], Generic[A, ID]):
    """
    Repository specifically for aggregate roots.

    Provides specialized handling for aggregates, including version checks and event collection.
    """

    async def save(self, aggregate: A) -> Result[A, Exception]:
        """
        Save an aggregate (create or update) with event collection. Returns Result.
        """
        try:
            if hasattr(aggregate, "apply_changes") and callable(
                aggregate.apply_changes
            ):
                aggregate.apply_changes()
            collect_result = self._collect_events_from_entity(aggregate)
            if isinstance(collect_result, Failure):
                return collect_result
            save_result = await super().save(aggregate)
            return Success(save_result)
        except Exception as e:
            return Failure(e)

    async def update(self, aggregate: A) -> Result[A, Exception]:
        """
        Update an aggregate with version checking. Returns Result.
        """
        try:
            collect_result = self._collect_events_from_entity(aggregate)
            if isinstance(collect_result, Failure):
                return collect_result
            update_result = await super().update(aggregate)
            return Success(update_result)
        except Exception as e:
            return Failure(e)
