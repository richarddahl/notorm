"""
Unit of work implementations for the domain layer.

This module provides implementations of the unit of work pattern for the domain layer,
managing transactions and tracking changes to entities.
"""

from typing import Dict, Set, Type, TypeVar, Optional, cast
from abc import ABC

from uno.domain.protocols import EntityProtocol
from uno.domain.repository_protocols import (
    RepositoryProtocol, UnitOfWorkProtocol
)

# Type variables
T = TypeVar('T', bound=EntityProtocol)  # Entity type


class UnitOfWork(UnitOfWorkProtocol):
    """
    Base unit of work implementation.
    
    This class provides a base implementation of the unit of work interface,
    managing transactions and tracking changes to entities.
    """
    
    def __init__(self):
        """Initialize the unit of work."""
        self._new_entities: Set[EntityProtocol] = set()
        self._dirty_entities: Set[EntityProtocol] = set()
        self._removed_entities: Set[EntityProtocol] = set()
        self._repositories: Dict[Type[EntityProtocol], RepositoryProtocol] = {}
    
    def __enter__(self) -> 'UnitOfWork':
        """
        Enter the unit of work context.
        
        Returns:
            The unit of work
        """
        self._begin_transaction()
        return self
    
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
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
    
    def _begin_transaction(self) -> None:
        """Begin a new transaction."""
        pass
    
    def get_repository(self, entity_type: Type[T]) -> RepositoryProtocol[T]:
        """
        Get a repository for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            A repository for the entity type
        """
        if entity_type not in self._repositories:
            self._repositories[entity_type] = self._create_repository(entity_type)
        return self._repositories[entity_type]
    
    def _create_repository(self, entity_type: Type[T]) -> RepositoryProtocol[T]:
        """
        Create a repository for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            A repository for the entity type
        """
        raise NotImplementedError
    
    def register_new(self, entity: EntityProtocol) -> None:
        """
        Register a new entity.
        
        Args:
            entity: The entity to register
        """
        self._new_entities.add(entity)
    
    def register_dirty(self, entity: EntityProtocol) -> None:
        """
        Register a modified entity.
        
        Args:
            entity: The entity to register
        """
        self._dirty_entities.add(entity)
    
    def register_removed(self, entity: EntityProtocol) -> None:
        """
        Register a removed entity.
        
        Args:
            entity: The entity to register
        """
        self._removed_entities.add(entity)
    
    def commit(self) -> None:
        """Commit the unit of work."""
        self._commit_new_entities()
        self._commit_dirty_entities()
        self._commit_removed_entities()
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
    
    def _commit_new_entities(self) -> None:
        """Commit new entities."""
        pass
    
    def _commit_dirty_entities(self) -> None:
        """Commit dirty entities."""
        pass
    
    def _commit_removed_entities(self) -> None:
        """Commit removed entities."""
        pass
    
    def rollback(self) -> None:
        """Rollback the unit of work."""
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
    
    def flush(self) -> None:
        """Flush changes to the database without committing."""
        pass


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory unit of work implementation for testing.
    
    This class provides an in-memory implementation of the unit of work
    interface, primarily for testing purposes.
    """
    
    def __init__(self):
        """Initialize the in-memory unit of work."""
        super().__init__()
        from uno.domain.repositories.base import InMemoryRepository
        self._repositories_by_entity_type: Dict[Type[EntityProtocol], InMemoryRepository] = {}
    
    def _create_repository(self, entity_type: Type[T]) -> RepositoryProtocol[T]:
        """
        Create a repository for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            A repository for the entity type
        """
        from uno.domain.repositories.base import InMemoryRepository
        if entity_type not in self._repositories_by_entity_type:
            self._repositories_by_entity_type[entity_type] = InMemoryRepository()
        return self._repositories_by_entity_type[entity_type]
    
    def _commit_new_entities(self) -> None:
        """Commit new entities."""
        for entity in self._new_entities:
            entity_type = type(entity)
            repository = cast(InMemoryRepository, self._create_repository(entity_type))
            repository._add(entity)
    
    def _commit_dirty_entities(self) -> None:
        """Commit dirty entities."""
        for entity in self._dirty_entities:
            entity_type = type(entity)
            repository = cast(InMemoryRepository, self._create_repository(entity_type))
            repository._update(entity)
    
    def _commit_removed_entities(self) -> None:
        """Commit removed entities."""
        for entity in self._removed_entities:
            entity_type = type(entity)
            repository = cast(InMemoryRepository, self._create_repository(entity_type))
            repository._remove(entity)
    
    def clear(self) -> None:
        """Clear all repositories."""
        for repository in self._repositories_by_entity_type.values():
            repository.clear()