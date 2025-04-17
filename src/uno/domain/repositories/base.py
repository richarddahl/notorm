"""
Base repository implementations for the domain layer.

This module provides base implementations of repositories for the domain layer,
including in-memory repositories for testing and specification-based querying.
"""

from typing import (
    Generic, TypeVar, List, Optional, Any, Dict, Callable, Set, Iterable,
    Iterator, Tuple, Union, Type, cast, overload, Collection
)
from abc import ABC, abstractmethod
from contextlib import contextmanager
import copy

from uno.domain.protocols import (
    EntityProtocol, SpecificationProtocol, AggregateRootProtocol
)
from uno.domain.models import Entity, AggregateRoot, CommandResult
from uno.domain.repository_protocols import (
    ReadRepositoryProtocol, WriteRepositoryProtocol, RepositoryProtocol,
    BatchRepositoryProtocol, UnitOfWorkProtocol
)
from uno.domain.repository_results import (
    RepositoryResult, GetResult, FindResult, FindOneResult, CountResult,
    ExistsResult, AddResult, UpdateResult, RemoveResult
)

# Type variables
T = TypeVar('T', bound=EntityProtocol)  # Entity type
A = TypeVar('A', bound=AggregateRootProtocol)  # Aggregate root type


class Repository(Generic[T], RepositoryProtocol[T], ABC):
    """
    Base repository implementation.
    
    This class provides a base implementation for repositories, implementing
    the repository protocol with abstract methods for the actual data access.
    """
    
    def __init__(self, unit_of_work_factory: Optional[Callable[[], UnitOfWorkProtocol]] = None):
        """
        Initialize the repository.
        
        Args:
            unit_of_work_factory: Factory function for creating a unit of work
        """
        self.unit_of_work_factory = unit_of_work_factory
    
    def get(self, id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        result = self.get_result(id)
        return result.entity if result.is_success else None
    
    def get_result(self, id: Any) -> GetResult[T]:
        """
        Get an entity by ID with result object.
        
        Args:
            id: The entity ID
            
        Returns:
            A result object containing the entity if found
        """
        try:
            entity = self._get(id)
            return GetResult.success(entity)
        except Exception as e:
            return GetResult.failure(e)
    
    @abstractmethod
    def _get(self, id: Any) -> Optional[T]:
        """
        Internal method to get an entity by ID.
        
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
        result = self.find_result(specification)
        return result.entities if result.is_success else []
    
    def find_result(self, specification: SpecificationProtocol[T]) -> FindResult[T]:
        """
        Find entities matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object containing the matching entities
        """
        try:
            entities = self._find(specification)
            return FindResult.success(entities)
        except Exception as e:
            return FindResult.failure(e)
    
    @abstractmethod
    def _find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """
        Internal method to find entities matching a specification.
        
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
        result = self.find_one_result(specification)
        return result.entity if result.is_success else None
    
    def find_one_result(self, specification: SpecificationProtocol[T]) -> FindOneResult[T]:
        """
        Find a single entity matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object containing the matching entity
        """
        try:
            entity = self._find_one(specification)
            return FindOneResult.success(entity)
        except Exception as e:
            return FindOneResult.failure(e)
    
    def _find_one(self, specification: SpecificationProtocol[T]) -> Optional[T]:
        """
        Internal method to find a single entity matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        entities = self._find(specification)
        return entities[0] if entities else None
    
    def exists(self, specification: SpecificationProtocol[T]) -> bool:
        """
        Check if an entity exists matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            True if a matching entity exists, False otherwise
        """
        result = self.exists_result(specification)
        return result.exists if result.is_success else False
    
    def exists_result(self, specification: SpecificationProtocol[T]) -> ExistsResult[T]:
        """
        Check if an entity exists matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object indicating whether a matching entity exists
        """
        try:
            exists = self._exists(specification)
            return ExistsResult.success(exists)
        except Exception as e:
            return ExistsResult.failure(e)
    
    def _exists(self, specification: SpecificationProtocol[T]) -> bool:
        """
        Internal method to check if an entity exists matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            True if a matching entity exists, False otherwise
        """
        return self._count(specification) > 0
    
    def count(self, specification: SpecificationProtocol[T]) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The number of matching entities
        """
        result = self.count_result(specification)
        return result.count if result.is_success else 0
    
    def count_result(self, specification: SpecificationProtocol[T]) -> CountResult[T]:
        """
        Count entities matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object containing the count
        """
        try:
            count = self._count(specification)
            return CountResult.success(count)
        except Exception as e:
            return CountResult.failure(e)
    
    def _count(self, specification: SpecificationProtocol[T]) -> int:
        """
        Internal method to count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The number of matching entities
        """
        return len(self._find(specification))
    
    def add(self, entity: T) -> None:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
        """
        result = self.add_result(entity)
        if result.is_failure and result.error:
            raise result.error
    
    def add_result(self, entity: T) -> AddResult[T]:
        """
        Add a new entity with result object.
        
        Args:
            entity: The entity to add
            
        Returns:
            A result object indicating success or failure
        """
        try:
            self._add(entity)
            return AddResult.success(entity)
        except Exception as e:
            return AddResult.failure(e)
    
    @abstractmethod
    def _add(self, entity: T) -> None:
        """
        Internal method to add a new entity.
        
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
        result = self.update_result(entity)
        if result.is_failure and result.error:
            raise result.error
    
    def update_result(self, entity: T) -> UpdateResult[T]:
        """
        Update an existing entity with result object.
        
        Args:
            entity: The entity to update
            
        Returns:
            A result object indicating success or failure
        """
        try:
            self._update(entity)
            return UpdateResult.success(entity)
        except Exception as e:
            return UpdateResult.failure(e)
    
    @abstractmethod
    def _update(self, entity: T) -> None:
        """
        Internal method to update an existing entity.
        
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
        result = self.remove_result(entity)
        if result.is_failure and result.error:
            raise result.error
    
    def remove_result(self, entity: T) -> RemoveResult[T]:
        """
        Remove an entity with result object.
        
        Args:
            entity: The entity to remove
            
        Returns:
            A result object indicating success or failure
        """
        try:
            self._remove(entity)
            return RemoveResult.success(entity)
        except Exception as e:
            return RemoveResult.failure(e)
    
    @abstractmethod
    def _remove(self, entity: T) -> None:
        """
        Internal method to remove an entity.
        
        Args:
            entity: The entity to remove
        """
        ...


class InMemoryRepository(Repository[T]):
    """
    In-memory repository implementation for testing.
    
    This class provides an in-memory implementation of the repository
    interface, primarily for testing purposes.
    """
    
    def __init__(self, unit_of_work_factory: Optional[Callable[[], UnitOfWorkProtocol]] = None):
        """
        Initialize the in-memory repository.
        
        Args:
            unit_of_work_factory: Factory function for creating a unit of work
        """
        super().__init__(unit_of_work_factory)
        self._entities: Dict[Any, T] = {}
    
    def _get(self, id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        return self._entities.get(id)
    
    def _find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        return [
            entity for entity in self._entities.values()
            if specification.is_satisfied_by(entity)
        ]
    
    def _add(self, entity: T) -> None:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
        """
        if entity.id in self._entities:
            raise ValueError(f"Entity with ID {entity.id} already exists")
        self._entities[entity.id] = entity
    
    def _update(self, entity: T) -> None:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
        """
        if entity.id not in self._entities:
            raise ValueError(f"Entity with ID {entity.id} does not exist")
        self._entities[entity.id] = entity
    
    def _remove(self, entity: T) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        if entity.id not in self._entities:
            raise ValueError(f"Entity with ID {entity.id} does not exist")
        del self._entities[entity.id]
    
    def clear(self) -> None:
        """Clear all entities from the repository."""
        self._entities.clear()