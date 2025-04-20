"""
In-memory repository implementation for domain entities.

This module provides an in-memory repository implementation that is useful
for testing and prototyping.
"""

from collections.abc import AsyncIterator
from copy import deepcopy
from datetime import datetime
from typing import Any, Generic, TypeVar

from uno.core.entity import ID
from uno.core.errors.result import Result
from uno.domain.entity.base import EntityBase
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.specification.base import Specification

T = TypeVar("T", bound=EntityBase)  # Entity type


class InMemoryRepository(EntityRepository[T], Generic[T]):
    """
    In-memory repository implementation for domain entities.

    This class provides an implementation of the EntityRepository interface
    that stores entities in memory. It is useful for testing and prototyping.
    """

    def __init__(self, entity_type: type[T], optional_fields: list[str] | None = None):
        """
        Initialize the repository.

        Args:
            entity_type: The type of entity this repository manages
            optional_fields: Optional list of fields that can be None
        """
        super().__init__(entity_type, optional_fields)
        self._entities: dict[ID, T] = {}

    async def get(self, id: ID) -> Result[T | None, str]:
        """
        Get an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Result containing the entity if found or None, or a Failure with error message
        """
        try:
            return Success[T | None, str](
                deepcopy(self._entities.get(id)), convert=True
            )
        except Exception as e:
            return Failure[T | None, str](
                f"Error retrieving entity with ID {id}: {str(e)}", convert=True
            )

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = 0,
    ) -> Result[list[T], str]:
        """
        List entities matching filter criteria.

        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination

        Returns:
            Result containing list of entities matching criteria or an error message
        """
        try:
            # Convert values to list
            entities = list(self._entities.values())

            # Apply filters if provided
            if filters:
                entities = [
                    e
                    for e in entities
                    if all(
                        getattr(e, key) == value
                        for key, value in filters.items()
                        if hasattr(e, key)
                    )
                ]

            # Apply ordering if provided
            if order_by:
                for field in reversed(order_by):
                    reverse = False
                    sort_field = field
                    if field.startswith("-"):
                        sort_field = field[1:]
                        reverse = True

                    entities.sort(
                        key=lambda e: (
                            getattr(e, sort_field) if hasattr(e, sort_field) else None
                        ),
                        reverse=reverse,
                    )

            # Apply pagination
            if offset:
                entities = entities[offset:]
            if limit:
                entities = entities[:limit]

            # Return deep copies to prevent modification
            return Success[list[T], str]([deepcopy(e) for e in entities], convert=True)
        except Exception as e:
            return Failure[list[T], str](
                f"Error listing entities: {str(e)}", convert=True
            )

    async def add(self, entity: T) -> Result[T, str]:
        """
        Add a new entity.

        Args:
            entity: The entity to add

        Returns:
            Result containing the added entity with any generated values or an error message
        """
        try:
            # Ensure entity has an ID
            if entity.id is None:
                return Failure[T, str]("Entity must have an ID", convert=True)

            # Check if entity already exists
            if entity.id in self._entities:
                return Failure[T, str](
                    f"Entity with ID {entity.id} already exists", convert=True
                )

            # Set created/updated timestamps if not set
            now = datetime.now()
            if hasattr(entity, "created_at") and entity.created_at is None:
                entity.created_at = now
            if hasattr(entity, "updated_at"):
                entity.updated_at = now

            # Store a deep copy to prevent modification of original
            self._entities[entity.id] = deepcopy(entity)

            # Return a copy of the stored entity
            return Success[T, str](deepcopy(self._entities[entity.id]), convert=True)
        except Exception as e:
            return Failure[T, str](f"Error adding entity: {str(e)}", convert=True)

    async def update(self, entity: T) -> Result[T, str]:
        """
        Update an existing entity.

        Args:
            entity: The entity to update

        Returns:
            Result containing the updated entity or an error message
        """
        try:
            # Ensure entity has an ID
            if entity.id is None:
                return Failure[T, str]("Entity must have an ID", convert=True)

            # Check if entity exists
            if entity.id not in self._entities:
                return Failure[T, str](
                    f"Entity with ID {entity.id} not found", convert=True
                )

            # Set updated timestamp if not set
            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.now()

            # Store a deep copy to prevent modification of original
            self._entities[entity.id] = deepcopy(entity)

            # Return a copy of the stored entity
            return Success[T, str](deepcopy(self._entities[entity.id]), convert=True)
        except Exception as e:
            return Failure[T, str](f"Error updating entity: {str(e)}", convert=True)

    async def delete(self, entity: T) -> Result[bool, str]:
        """
        Delete an entity.

        Args:
            entity: The entity to delete

        Returns:
            Result indicating success (True) or failure with an error message
        """
        try:
            # Ensure entity has an ID
            if entity.id is None:
                return Failure[bool, str]("Entity must have an ID", convert=True)

            # Check if entity exists
            if entity.id not in self._entities:
                return Failure[bool, str](
                    f"Entity with ID {entity.id} not found", convert=True
                )

            # Delete the entity
            del self._entities[entity.id]
            return Success[bool, str](True, convert=True)
        except Exception as e:
            return Failure[bool, str](f"Error deleting entity: {str(e)}", convert=True)

    async def exists(self, id: ID) -> Result[bool, str]:
        """
        Check if an entity with the given ID exists.

        Args:
            id: Entity ID

        Returns:
            Result containing True if entity exists, False otherwise
        """
        try:
            return Success[bool, str](id in self._entities, convert=True)
        except Exception as e:
            return Failure[bool, str](
                f"Error checking if entity exists: {str(e)}", convert=True
            )

    async def find(
        self, specification: Specification | None = None
    ) -> Result[list[T], str]:
        """
        Find entities matching a specification.

        Args:
            specification: Optional specification to match against

        Returns:
            Result containing list of entities matching the specification or an error message
        """
        try:
            if specification is None:
                # If no specification is provided, return all entities
                return Success[list[T], str](
                    [deepcopy(entity) for entity in self._entities.values()],
                    convert=True,
                )

            matching_entities = [
                deepcopy(entity)
                for entity in self._entities.values()
                if specification.is_satisfied_by(entity)
            ]
            return Success[list[T], str](matching_entities, convert=True)
        except Exception as e:
            return Failure[list[T], str](
                f"Error finding entities: {str(e)}", convert=True
            )

    async def find_one(
        self, specification: Specification | None = None
    ) -> Result[T | None, str]:
        """
        Find a single entity matching a specification.

        Args:
            specification: Optional specification to match against

        Returns:
            Result containing the first matching entity or None if none found
        """
        try:
            if specification is None:
                # If no specification is provided, return the first entity (if any)
                if not self._entities:
                    return Success[T | None, str](None, convert=True)
                return Success[T | None, str](
                    deepcopy(next(iter(self._entities.values()))), convert=True
                )

            for entity in self._entities.values():
                if specification.is_satisfied_by(entity):
                    return Success[T | None, str](deepcopy(entity), convert=True)

            return Success[T | None, str](None, convert=True)
        except Exception as e:
            return Failure[T | None, str](
                f"Error finding entity: {str(e)}", convert=True
            )

    async def count(
        self, specification: Specification | None = None
    ) -> Result[int, str]:
        """
        Count entities matching the specification.

        Args:
            specification: Optional specification to filter entities

        Returns:
            Result containing count of matching entities or an error message
        """
        try:
            if specification is None:
                return Success[int, str](len(self._entities), convert=True)

            count = len(
                [e for e in self._entities.values() if specification.is_satisfied_by(e)]
            )

            return Success[int, str](count, convert=True)
        except Exception as e:
            return Failure[int, str](f"Error counting entities: {str(e)}", convert=True)

    async def bulk_add(self, entities: list[T]) -> Result[list[T], str]:
        """
        Add multiple entities in bulk.

        Args:
            entities: List of entities to add

        Returns:
            Result containing list of added entities with generated values or an error message
        """
        try:
            added_entities = []
            for entity in entities:
                result = await self.add(entity)
                if result.is_failure():
                    return Failure[list[T], str](
                        f"Failed to add entity: {result.error()}", convert=True
                    )
                added_entities.append(result.value())
            return Success[list[T], str](added_entities, convert=True)
        except Exception as e:
            return Failure[list[T], str](
                f"Error adding entities in bulk: {str(e)}", convert=True
            )

    async def bulk_update(self, entities: list[T]) -> Result[list[T], str]:
        """
        Update multiple entities in bulk.

        Args:
            entities: List of entities to update

        Returns:
            Result containing list of updated entities or an error message
        """
        try:
            updated_entities = []
            for entity in entities:
                result = await self.update(entity)
                if result.is_failure():
                    return Failure[list[T], str](
                        f"Failed to update entity: {result.error()}", convert=True
                    )
                updated_entities.append(result.value())
            return Success[list[T], str](updated_entities, convert=True)
        except Exception as e:
            return Failure[list[T], str](
                f"Error updating entities in bulk: {str(e)}", convert=True
            )

    async def bulk_delete(self, entities: list[T]) -> Result[bool, str]:
        """
        Delete multiple entities in bulk.

        Args:
            entities: List of entities to delete

        Returns:
            Result indicating success (True) or failure with an error message
        """
        try:
            for entity in entities:
                result = await self.delete(entity)
                if result.is_failure():
                    return Failure[bool, str](
                        f"Failed to delete entity: {result.error()}", convert=True
                    )
            return Success[bool, str](True, convert=True)
        except Exception as e:
            return Failure[bool, str](
                f"Error deleting entities in bulk: {str(e)}", convert=True
            )

    async def bulk_delete_by_ids(self, ids: list[ID]) -> Result[list[ID], str]:
        """
        Delete multiple entities by their IDs.

        Args:
            ids: List of entity IDs to delete

        Returns:
            Result containing list of IDs that were successfully deleted or an error message
        """
        try:
            deleted_ids = []
            for id in ids:
                if id in self._entities:
                    del self._entities[id]
                    deleted_ids.append(id)
            return Success[list[ID], str](deleted_ids, convert=True)
        except Exception as e:
            return Failure[list[ID], str](
                f"Error deleting entities by IDs: {str(e)}", convert=True
            )

    async def stream(
        self,
        specification: Specification | None = None,
        order_by: list[str] | None = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """
        Stream entities matching a specification.

        Args:
            specification: Optional specification to match against
            order_by: Optional list of fields to order by
            batch_size: Size of batches to fetch (ignored in in-memory implementation)

        Returns:
            Async iterator of entities matching the specification
        """
        # This method doesn't return a Result type since it's an async iterator.
        # Error handling should be done by the caller when consuming the iterator.

        # Get entities matching specification
        entities = list(self._entities.values())
        if specification:
            entities = [e for e in entities if specification.is_satisfied_by(e)]

        # Apply ordering if provided
        if order_by:
            for field in reversed(order_by):
                reverse = False
                sort_field = field
                if field.startswith("-"):
                    sort_field = field[1:]
                    reverse = True

                entities.sort(
                    key=lambda e: (
                        getattr(e, sort_field) if hasattr(e, sort_field) else None
                    ),
                    reverse=reverse,
                )

        # Yield entities one by one
        for entity in entities:
            yield deepcopy(entity)

    async def clear(self) -> Result[bool, str]:
        """
        Clear all entities from the repository.

        This method is useful for testing to reset the repository state.

        Returns:
            Result indicating success (True) or failure with an error message
        """
        try:
            self._entities.clear()
            return Success[bool, str](True, convert=True)
        except Exception as e:
            return Failure[bool, str](
                f"Error clearing repository: {str(e)}", convert=True
            )
