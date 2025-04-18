"""
Repository protocols for the Uno framework.

This module defines the interface contracts for the repository pattern, providing
a clear boundary between domain logic and data access concerns.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Dict, Generic, Iterable, List, Optional, Protocol, Set, Type, TypeVar, Union, 
    runtime_checkable, AsyncIterator
)
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result
from uno.domain.specifications import Specification


# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
FilterType = Dict[str, Any]


@runtime_checkable
class RepositoryProtocol(Protocol[T, ID]):
    """
    Base protocol for repository operations.
    
    Defines the core interface that all repositories must implement.
    """
    
    async def get(self, id: ID) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        ...
    
    async def list(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[T]:
        """
        List entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria as field-value pairs
            order_by: Optional ordering fields (prefixed with - for descending)
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the criteria
        """
        ...
    
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity (possibly with generated ID)
        """
        ...
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        ...
    
    async def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
        """
        ...
    

@runtime_checkable
class SpecificationRepositoryProtocol(RepositoryProtocol[T, ID], Protocol[T, ID]):
    """
    Repository that supports the specification pattern.
    
    Extends the base repository with methods for querying using specifications.
    """
    
    async def find(self, specification: Specification[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification criteria
            
        Returns:
            List of entities matching the specification
        """
        ...
    
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification criteria
            
        Returns:
            The matching entity if found, None otherwise
        """
        ...
    
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: Optional specification criteria
            
        Returns:
            The count of matching entities
        """
        ...


@runtime_checkable
class BatchRepositoryProtocol(RepositoryProtocol[T, ID], Protocol[T, ID]):
    """
    Repository that supports batch operations.
    
    Extends the base repository with methods for performing operations on multiple entities.
    """
    
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """
        Add multiple entities.
        
        Args:
            entities: The entities to add
            
        Returns:
            The added entities
        """
        ...
    
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """
        Update multiple entities.
        
        Args:
            entities: The entities to update
            
        Returns:
            The updated entities
        """
        ...
    
    async def delete_many(self, entities: Iterable[T]) -> None:
        """
        Delete multiple entities.
        
        Args:
            entities: The entities to delete
        """
        ...
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """
        Delete entities by their IDs.
        
        Args:
            ids: The IDs of entities to delete
            
        Returns:
            The number of entities deleted
        """
        ...


@runtime_checkable
class StreamingRepositoryProtocol(RepositoryProtocol[T, ID], Protocol[T, ID]):
    """
    Repository that supports streaming large result sets.
    
    Extends the base repository with methods for handling large data volumes efficiently.
    """
    
    async def stream(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """
        Stream entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria
            order_by: Optional ordering fields
            batch_size: Number of entities to fetch in each batch
            
        Returns:
            An async iterator yielding entities
        """
        ...


@runtime_checkable
class EventCollectingRepositoryProtocol(RepositoryProtocol[T, ID], Protocol[T, ID]):
    """
    Repository that collects domain events.
    
    Extends the base repository with methods for collecting and retrieving domain events.
    """
    
    def collect_events(self) -> List[Any]:
        """
        Collect and clear pending domain events.
        
        Returns:
            List of pending domain events
        """
        ...


@runtime_checkable
class SQLRepositoryProtocol(Protocol):
    """Protocol for repositories that need direct SQL access."""
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            query: The SQL query to execute
            params: Query parameters
            
        Returns:
            List of results as dictionaries
        """
        ...
    
    async def execute_statement(self, statement: Select) -> List[Any]:
        """
        Execute a SQLAlchemy statement.
        
        Args:
            statement: The SQLAlchemy statement to execute
            
        Returns:
            List of results
        """
        ...


class UnitOfWorkProtocol(Protocol):
    """
    Protocol for the Unit of Work pattern.
    
    The Unit of Work coordinates the transaction boundaries and manages registered repositories.
    """
    
    repositories: List[Any]
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        ...
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...
    
    async def __aenter__(self) -> "UnitOfWorkProtocol":
        """Enter the unit of work context."""
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the unit of work context."""
        ...
    
    def register_repository(self, repository: Any) -> None:
        """
        Register a repository with this unit of work.
        
        Args:
            repository: The repository to register
        """
        ...