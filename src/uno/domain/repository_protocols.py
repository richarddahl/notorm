"""
Repository protocol interfaces for the domain layer.

This module defines protocol interfaces for repositories, providing a clean
contract for data access implementations in the domain layer.
"""

from typing import (
    Protocol, TypeVar, Generic, List, Optional, Any, Dict, Callable,
    runtime_checkable, Set, Iterable, AsyncIterator, Iterator, Tuple, Union,
    Type, overload
)
from datetime import datetime
from contextlib import AbstractContextManager, AbstractAsyncContextManager

from uno.domain.protocols import EntityProtocol, AggregateRootProtocol, SpecificationProtocol
from uno.domain.models import Entity, CommandResult

# Type variables
T = TypeVar('T', bound=EntityProtocol)  # Entity type
ID = TypeVar('ID')  # ID type


@runtime_checkable
class ReadRepositoryProtocol(Protocol[T]):
    """Protocol for read-only repository operations."""
    
    def get(self, id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        ...
    
    def find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        ...
    
    def find_one(self, specification: SpecificationProtocol[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        ...
    
    def exists(self, specification: SpecificationProtocol[T]) -> bool:
        """
        Check if an entity exists matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            True if a matching entity exists, False otherwise
        """
        ...
    
    def count(self, specification: SpecificationProtocol[T]) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The number of matching entities
        """
        ...


@runtime_checkable
class WriteRepositoryProtocol(Protocol[T]):
    """Protocol for write repository operations."""
    
    def add(self, entity: T) -> None:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
        """
        ...
    
    def update(self, entity: T) -> None:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
        """
        ...
    
    def remove(self, entity: T) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        ...


@runtime_checkable
class RepositoryProtocol(ReadRepositoryProtocol[T], WriteRepositoryProtocol[T], Protocol[T]):
    """Protocol for repositories combining read and write operations."""
    pass


@runtime_checkable
class BatchRepositoryProtocol(Protocol[T]):
    """Protocol for repositories supporting batch operations."""
    
    def get_batch(self, ids: List[Any]) -> Dict[Any, T]:
        """
        Get multiple entities by IDs.
        
        Args:
            ids: The entity IDs
            
        Returns:
            Dictionary mapping IDs to entities
        """
        ...
    
    def add_batch(self, entities: List[T]) -> None:
        """
        Add multiple entities.
        
        Args:
            entities: The entities to add
        """
        ...
    
    def update_batch(self, entities: List[T]) -> None:
        """
        Update multiple entities.
        
        Args:
            entities: The entities to update
        """
        ...
    
    def remove_batch(self, entities: List[T]) -> None:
        """
        Remove multiple entities.
        
        Args:
            entities: The entities to remove
        """
        ...


@runtime_checkable
class UnitOfWorkProtocol(AbstractContextManager, Protocol):
    """Protocol for unit of work."""
    
    def __enter__(self) -> 'UnitOfWorkProtocol':
        """
        Enter the unit of work context.
        
        Returns:
            The unit of work
        """
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the unit of work context.
        
        If no exception occurred, commit the unit of work.
        If an exception occurred, rollback the unit of work.
        
        Args:
            exc_type: Exception type if an exception was raised, None otherwise
            exc_val: Exception value if an exception was raised, None otherwise
            exc_tb: Exception traceback if an exception was raised, None otherwise
        """
        ...
    
    def commit(self) -> None:
        """Commit the unit of work."""
        ...
    
    def rollback(self) -> None:
        """Rollback the unit of work."""
        ...
    
    def get_repository(self, entity_type: Type[T]) -> RepositoryProtocol[T]:
        """
        Get a repository for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            A repository for the entity type
        """
        ...
    
    def register_new(self, entity: EntityProtocol) -> None:
        """
        Register a new entity.
        
        Args:
            entity: The entity to register
        """
        ...
    
    def register_dirty(self, entity: EntityProtocol) -> None:
        """
        Register a modified entity.
        
        Args:
            entity: The entity to register
        """
        ...
    
    def register_removed(self, entity: EntityProtocol) -> None:
        """
        Register a removed entity.
        
        Args:
            entity: The entity to register
        """
        ...
    
    def flush(self) -> None:
        """Flush changes to the database without committing."""
        ...


# Async protocols

@runtime_checkable
class AsyncReadRepositoryProtocol(Protocol[T]):
    """Protocol for async read-only repository operations."""
    
    async def get(self, id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        ...
    
    async def find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        ...
    
    async def find_one(self, specification: SpecificationProtocol[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        ...
    
    async def exists(self, specification: SpecificationProtocol[T]) -> bool:
        """
        Check if an entity exists matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            True if a matching entity exists, False otherwise
        """
        ...
    
    async def count(self, specification: SpecificationProtocol[T]) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The number of matching entities
        """
        ...


@runtime_checkable
class AsyncWriteRepositoryProtocol(Protocol[T]):
    """Protocol for async write repository operations."""
    
    async def add(self, entity: T) -> None:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
        """
        ...
    
    async def update(self, entity: T) -> None:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
        """
        ...
    
    async def remove(self, entity: T) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        ...


@runtime_checkable
class AsyncRepositoryProtocol(AsyncReadRepositoryProtocol[T], AsyncWriteRepositoryProtocol[T], Protocol[T]):
    """Protocol for async repositories combining read and write operations."""
    pass


@runtime_checkable
class AsyncBatchRepositoryProtocol(Protocol[T]):
    """Protocol for async repositories supporting batch operations."""
    
    async def get_batch(self, ids: List[Any]) -> Dict[Any, T]:
        """
        Get multiple entities by IDs.
        
        Args:
            ids: The entity IDs
            
        Returns:
            Dictionary mapping IDs to entities
        """
        ...
    
    async def add_batch(self, entities: List[T]) -> None:
        """
        Add multiple entities.
        
        Args:
            entities: The entities to add
        """
        ...
    
    async def update_batch(self, entities: List[T]) -> None:
        """
        Update multiple entities.
        
        Args:
            entities: The entities to update
        """
        ...
    
    async def remove_batch(self, entities: List[T]) -> None:
        """
        Remove multiple entities.
        
        Args:
            entities: The entities to remove
        """
        ...


@runtime_checkable
class AsyncUnitOfWorkProtocol(AbstractAsyncContextManager, Protocol):
    """Protocol for async unit of work."""
    
    async def __aenter__(self) -> 'AsyncUnitOfWorkProtocol':
        """
        Enter the async unit of work context.
        
        Returns:
            The async unit of work
        """
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the async unit of work context.
        
        If no exception occurred, commit the unit of work.
        If an exception occurred, rollback the unit of work.
        
        Args:
            exc_type: Exception type if an exception was raised, None otherwise
            exc_val: Exception value if an exception was raised, None otherwise
            exc_tb: Exception traceback if an exception was raised, None otherwise
        """
        ...
    
    async def commit(self) -> None:
        """Commit the unit of work."""
        ...
    
    async def rollback(self) -> None:
        """Rollback the unit of work."""
        ...
    
    async def get_repository(self, entity_type: Type[T]) -> AsyncRepositoryProtocol[T]:
        """
        Get a repository for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            A repository for the entity type
        """
        ...
    
    async def register_new(self, entity: EntityProtocol) -> None:
        """
        Register a new entity.
        
        Args:
            entity: The entity to register
        """
        ...
    
    async def register_dirty(self, entity: EntityProtocol) -> None:
        """
        Register a modified entity.
        
        Args:
            entity: The entity to register
        """
        ...
    
    async def register_removed(self, entity: EntityProtocol) -> None:
        """
        Register a removed entity.
        
        Args:
            entity: The entity to register
        """
        ...
    
    async def flush(self) -> None:
        """Flush changes to the database without committing."""
        ...


# Repository result protocols

@runtime_checkable
class RepositoryResultProtocol(Protocol[T]):
    """Protocol for repository operation results."""
    
    @property
    def is_success(self) -> bool:
        """
        Check if the operation was successful.
        
        Returns:
            True if successful, False otherwise
        """
        ...
    
    @property
    def is_failure(self) -> bool:
        """
        Check if the operation failed.
        
        Returns:
            True if failed, False otherwise
        """
        ...
    
    @property
    def error(self) -> Optional[Exception]:
        """
        Get the error if the operation failed.
        
        Returns:
            The error if failed, None otherwise
        """
        ...


@runtime_checkable
class GetResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for get operation results."""
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        ...


@runtime_checkable
class FindResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for find operation results."""
    
    @property
    def entities(self) -> List[T]:
        """
        Get the entities if the operation was successful.
        
        Returns:
            The entities if successful, empty list otherwise
        """
        ...


@runtime_checkable
class CountResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for count operation results."""
    
    @property
    def count(self) -> int:
        """
        Get the count if the operation was successful.
        
        Returns:
            The count if successful, 0 otherwise
        """
        ...


@runtime_checkable
class ExistsResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for exists operation results."""
    
    @property
    def exists(self) -> bool:
        """
        Check if the entity exists if the operation was successful.
        
        Returns:
            True if exists and successful, False otherwise
        """
        ...


@runtime_checkable
class AddResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for add operation results."""
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the added entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        ...


@runtime_checkable
class UpdateResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for update operation results."""
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the updated entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        ...


@runtime_checkable
class RemoveResultProtocol(RepositoryResultProtocol[T], Protocol[T]):
    """Protocol for remove operation results."""
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the removed entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        ...
