"""
In-memory implementation of the repository pattern.

This module provides repository implementations that store entities in memory,
which is useful for testing and prototyping.
"""

import logging
from copy import deepcopy
from datetime import datetime, timezone
from collections.abc import AsyncIterator, Iterable
from typing import Any, Generic, Optional, Sequence, Tuple, TypeVar, cast

from uno.core.errors.result import Result
from uno.domain.core import Entity, AggregateRoot
from uno.domain.specifications import Specification
from uno.domain.entity import (
    InMemoryRepository,
)

# Only modern in-memory repository implementations are retained. Legacy or deprecated classes have been removed.


# Type variables
T = TypeVar("T")  # Entity type
E = TypeVar("E", bound=Entity)  # Entity type with Entity constraint
A = TypeVar("A", bound=AggregateRoot)  # Aggregate type
ID = TypeVar("ID")  # ID type


class InMemoryRepository(Repository[T, ID], Generic[T, ID]):
    """
    In-memory implementation of the repository pattern.

    This repository stores entities in memory, making it useful for testing and prototyping.
    """

    def __init__(self, entity_type: Type[T], logger: logging.Logger | None = None):
        """
        Initialize the in-memory repository.

        Args:
            entity_type: The type of entity this repository manages
            logger: Optional logger for diagnostic output
        """
        super().__init__(entity_type, logger)
        self.entities: Dict[ID, T] = {}

    async def get(self, id: ID) -> Result[T, Exception]:
        """Get an entity by ID. Returns Result."""
        try:
            entity = self.entities.get(id)
            if entity is None:
                return Result.failure(ValueError(f"Entity with ID {id} not found"))
            return Result.success(entity)
        except Exception as e:
            return Failure(e)

    async def list(
        self,
        filters: Optional[FilterType] = None,
        order_by: list[str] | None = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> list[T]:
        """List entities matching filter criteria."""
        # Start with all entities
        filtered_entities = list(self.entities.values())

        # Apply filters
        if filters:
            filtered_entities = [
                entity
                for entity in filtered_entities
                if self._entity_matches_filters(entity, filters)
            ]

        # Apply sorting
        if order_by:
            filtered_entities = self._apply_ordering(filtered_entities, order_by)

        # Apply pagination
        if offset:
            filtered_entities = filtered_entities[offset:]

        if limit is not None:
            filtered_entities = filtered_entities[:limit]

        return filtered_entities

    async def add(self, entity: T) -> Result[T, Exception]:
        """Add a new entity. Returns Result."""
        try:
            entity_id = getattr(entity, "id", None)
            if not entity_id:
                return Result.failure(ValueError("Entity must have an ID"))
            if entity_id in self.entities:
                return Result.failure(
                    ValueError(f"Entity with ID {entity_id} already exists")
                )
            if hasattr(entity, "created_at") and not getattr(
                entity, "created_at", None
            ):
                setattr(entity, "created_at", datetime.now(timezone.utc))
            entity_copy = self._clone_entity(entity)
            self.entities[entity_id] = entity_copy
            return Result.success(entity_copy)
        except Exception as e:
            return Failure(e)

    async def update(self, entity: T) -> Result[T, Exception]:
        """Update an existing entity. Returns Result."""
        try:
            entity_id = getattr(entity, "id", None)
            if not entity_id:
                return Result.failure(ValueError("Entity must have an ID"))
            if entity_id not in self.entities:
                return Result.failure(
                    ValueError(f"Entity with ID {entity_id} not found")
                )
            # Check for optimistic concurrency
            if isinstance(entity, AggregateRoot):
                existing_entity = self.entities[entity_id]
                if (
                    isinstance(existing_entity, AggregateRoot)
                    and hasattr(entity, "version")
                    and hasattr(existing_entity, "version")
                    and getattr(entity, "version")
                    != getattr(existing_entity, "version")
                ):
                    return Result.failure(
                        ValueError("Version conflict for entity update")
                    )
            entity_copy = self._clone_entity(entity)
            self.entities[entity_id] = entity_copy
            return Result.success(entity_copy)
        except Exception as e:
            return Result.failure(e)

    async def delete(self, entity: T) -> Result[None, Exception]:
        """Delete an entity. Returns Result."""
        try:
            entity_id = getattr(entity, "id", None)
            if not entity_id:
                return Result.failure(ValueError("Entity must have an ID"))
            if entity_id in self.entities:
                del self.entities[entity_id]
                return Result.success(None)
            return Result.failure(ValueError(f"Entity with ID {entity_id} not found"))
        except Exception as e:
            return Result.failure(e)

    async def exists(self, id: ID) -> Result[bool, Exception]:
        """Check if an entity exists. Returns Result."""
        try:
            return Success(id in self.entities)
        except Exception as e:
            return Failure(e)

    def _entity_matches_filters(self, entity: T, filters: FilterType) -> bool:
        """
        Check if an entity matches the given filter criteria.

        Args:
            entity: The entity to check
            filters: Filter criteria

        Returns:
            True if the entity matches, False otherwise
        """
        for field, value in filters.items():
            if isinstance(value, dict) and "op" in value and "value" in value:
                # Handle advanced filters with operators
                op = value["op"]
                val = value["value"]
                attr_value = getattr(entity, field, None)

                if op == "eq" and attr_value != val:
                    return False
                elif op == "neq" and attr_value == val:
                    return False
                elif op == "gt" and (attr_value is None or attr_value <= val):
                    return False
                elif op == "gte" and (attr_value is None or attr_value < val):
                    return False
                elif op == "lt" and (attr_value is None or attr_value >= val):
                    return False
                elif op == "lte" and (attr_value is None or attr_value > val):
                    return False
                elif op == "in" and attr_value not in val:
                    return False
                elif op == "like" and (
                    attr_value is None
                    or not isinstance(attr_value, str)
                    or val.lower() not in attr_value.lower()
                ):
                    return False
                elif op == "is_null" and attr_value is not None:
                    return False
                elif op == "not_null" and attr_value is None:
                    return False
            else:
                # Simple equality filter
                if getattr(entity, field, None) != value:
                    return False

        return True

    def _apply_ordering(self, entities: list[T], order_by: list[str]) -> list[T]:
        """
        Apply ordering to a list of entities.

        Args:
            entities: The entities to order
            order_by: Ordering fields

        Returns:
            Ordered list of entities
        """
        # Create a copy of the list to avoid modifying the original
        result = list(entities)

        # Apply ordering in reverse order
        for field in reversed(order_by):
            reverse = False
            if field.startswith("-"):
                reverse = True
                field = field[1:]

            def sort_key(entity):
                value = getattr(entity, field, None)
                # Handle None values for proper sorting
                if value is None:
                    # Place None values at the beginning or end based on sort direction
                    return (0 if reverse else 1, None)
                return (1 if reverse else 0, value)

            result.sort(key=sort_key, reverse=reverse)

        return result

    def _clone_entity(self, entity: T) -> T:
        """
        Create a deep copy of an entity.

        Args:
            entity: The entity to clone

        Returns:
            A deep copy of the entity
        """
        # Use model_copy if available (Pydantic v2)
        if hasattr(entity, "model_copy"):
            return entity.model_copy(deep=True)

        # Use copy method if available
        if hasattr(entity, "copy") and callable(getattr(entity, "copy")):
            return entity.copy()

        # Use to_dict and create a new instance
        if hasattr(entity, "to_dict") and callable(getattr(entity, "to_dict")):
            data = entity.to_dict()
            return self.entity_type(**data)

        # Last resort: use deepcopy
        return deepcopy(entity)


class InMemorySpecificationRepository(
    InMemoryRepository[T, ID], SpecificationRepository[T, ID], Generic[T, ID]
):
    """
    In-memory repository with specification pattern support.

    Extends the base in-memory repository with support for the specification pattern.
    """

    async def find(self, specification: Specification[T]) -> list[T]:
        """Find entities matching a specification."""
        return [
            entity
            for entity in self.entities.values()
            if specification.is_satisfied_by(entity)
        ]

    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """Find a single entity matching a specification."""
        for entity in self.entities.values():
            if specification.is_satisfied_by(entity):
                return entity
        return None

    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """Count entities matching a specification."""
        if specification is None:
            return len(self.entities)

        return len(
            [
                entity
                for entity in self.entities.values()
                if specification.is_satisfied_by(entity)
            ]
        )


class InMemoryBatchRepository(
    InMemoryRepository[T, ID], BatchRepository[T, ID], Generic[T, ID]
):
    """
    In-memory repository with batch operation support.

    Extends the base in-memory repository with support for batch operations.
    """

    async def add_many(self, entities: Iterable[T]) -> list[T]:
        """Add multiple entities."""
        added_entities = []

        for entity in entities:
            # Add each entity
            added_entity = await self.add(entity)
            added_entities.append(added_entity)

        return added_entities

    async def update_many(self, entities: Iterable[T]) -> list[T]:
        """Update multiple entities."""
        updated_entities = []

        for entity in entities:
            # Update each entity
            updated_entity = await self.update(entity)
            updated_entities.append(updated_entity)

        return updated_entities

    async def delete_many(self, entities: Iterable[T]) -> None:
        """Delete multiple entities."""
        for entity in entities:
            # Delete each entity
            await self.delete(entity)

    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """Delete entities by their IDs."""
        id_list = list(ids)
        deleted_count = 0

        for entity_id in id_list:
            if entity_id in self.entities:
                del self.entities[entity_id]
                deleted_count += 1

        return deleted_count


class InMemoryStreamingRepository(
    InMemoryRepository[T, ID], StreamingRepository[T, ID], Generic[T, ID]
):
    """
    In-memory repository with streaming support.

    Extends the base in-memory repository with support for streaming.
    """

    async def stream(
        self,
        filters: Optional[FilterType] = None,
        order_by: list[str] | None = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """Stream entities matching filter criteria."""
        # Get filtered and ordered entities
        entities = await self.list(filters=filters, order_by=order_by)

        # Yield entities in batches
        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]
            for entity in batch:
                yield entity


class InMemoryEventCollectingRepository(
    InMemoryRepository[T, ID], EventCollectingRepository[T, ID], Generic[T, ID]
):
    """
    In-memory repository that collects domain events.

    Extends the base in-memory repository with event collection.
    """

    async def add(self, entity: T) -> T:
        """Add a new entity with event collection."""
        # Collect events before adding
        self._collect_events_from_entity(entity)

        # Use parent implementation for actual add
        return await super().add(entity)

    async def update(self, entity: T) -> T:
        """Update an entity with event collection."""
        # Collect events before updating
        self._collect_events_from_entity(entity)

        # Use parent implementation for actual update
        return await super().update(entity)


class InMemoryAggregateRepository(
    InMemoryRepository[A, ID], AggregateRepository[A, ID], Generic[A, ID]
):
    """
    In-memory repository for aggregate roots.

    Specializes the in-memory repository for working with aggregate roots.
    """

    async def add(self, aggregate: A) -> A:
        """Add a new aggregate with event collection."""
        # Apply changes to ensure invariants if supported
        if hasattr(aggregate, "apply_changes") and callable(aggregate.apply_changes):
            aggregate.apply_changes()

        # Collect events before adding
        self._collect_events_from_entity(aggregate)

        # Use parent implementation for actual add
        return await super().add(aggregate)

    async def update(self, aggregate: A) -> A:
        """Update an aggregate with event collection and version checking."""
        # Apply changes to ensure invariants if supported
        if hasattr(aggregate, "apply_changes") and callable(aggregate.apply_changes):
            aggregate.apply_changes()

        # Collect events before updating
        self._collect_events_from_entity(aggregate)

        # Use parent implementation for actual update
        return await super().update(aggregate)


class InMemoryCompleteRepository(
    InMemorySpecificationRepository[T, ID],
    InMemoryBatchRepository[T, ID],
    InMemoryStreamingRepository[T, ID],
    InMemoryEventCollectingRepository[T, ID],
    Generic[T, ID],
):
    """
    Complete in-memory repository with all capabilities.

    This class combines all in-memory repository features into a single implementation.
    Use this when you need a repository with all capabilities for testing.
    """

    pass
