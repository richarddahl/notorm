"""
Repository protocol interfaces.

This module defines protocol interfaces for repositories and unit of work.
"""

from typing import Protocol, TypeVar, Generic, List, Optional, Any
from abc import abstractmethod

from ..protocols.entity_protocols import EntityProtocol
from ..specifications import Specification
from ..repository_results import RepositoryResult, GetResult

T = TypeVar("T", bound=EntityProtocol)


class RepositoryProtocol(Generic[T], Protocol):
    """Protocol interface for repositories."""

    @abstractmethod
    async def add(self, entity: T) -> RepositoryResult[T]:
        """
        Add an entity to the repository.

        Args:
            entity: The entity to add

        Returns:
            A repository result
        """
        ...

    @abstractmethod
    async def update(self, entity: T) -> RepositoryResult[T]:
        """
        Update an entity in the repository.

        Args:
            entity: The entity to update

        Returns:
            A repository result
        """
        ...

    @abstractmethod
    async def delete(self, entity: T) -> RepositoryResult[T]:
        """
        Delete an entity from the repository.

        Args:
            entity: The entity to delete

        Returns:
            A repository result
        """
        ...

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> GetResult[T]:
        """
        Get an entity by its ID.

        Args:
            entity_id: The ID of the entity to get

        Returns:
            A get result
        """
        ...

    @abstractmethod
    async def get_all(self) -> GetResult[List[T]]:
        """
        Get all entities.

        Returns:
            A get result containing a list of entities
        """
        ...

    @abstractmethod
    async def get_by_specification(
        self, specification: Specification[T]
    ) -> GetResult[List[T]]:
        """
        Get entities that satisfy a specification.

        Args:
            specification: The specification to satisfy

        Returns:
            A get result containing a list of entities
        """
        ...


class UnitOfWorkProtocol(Protocol):
    """Protocol interface for unit of work."""

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWorkProtocol":
        """Enter the context manager."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...
