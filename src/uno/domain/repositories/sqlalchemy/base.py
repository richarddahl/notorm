"""
SQLAlchemy repository base implementations for the domain layer.

This module provides repository implementations that use SQLAlchemy as the ORM,
with full support for the specification pattern and async operations.
"""

from typing import (
    TypeVar, Generic, Dict, Any, List, Optional, Type, cast,
    Union, Callable, Set, Tuple
)
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging

from sqlalchemy import select, func, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from uno.domain.protocols import EntityProtocol, SpecificationProtocol
from uno.domain.models import Entity, AggregateRoot
from uno.domain.repository_protocols import (
    AsyncRepositoryProtocol,
    AsyncUnitOfWorkProtocol
)
from uno.domain.repository_results import (
    RepositoryResult, GetResult, FindResult, FindOneResult,
    CountResult, ExistsResult, AddResult, UpdateResult, RemoveResult
)
from uno.domain.specification_translators import (
    SpecificationTranslator, PostgreSQLSpecificationTranslator
)
from uno.model import UnoModel

# Type variables
T = TypeVar('T', bound=EntityProtocol)  # Entity type
M = TypeVar('M', bound=UnoModel)  # Model type


class SQLAlchemyUnitOfWork(AsyncUnitOfWorkProtocol):
    """
    Unit of work implementation for SQLAlchemy.
    
    This class manages transactions and tracks changes to entities.
    """
    
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        repositories: Optional[Dict[Type[EntityProtocol], 'SQLAlchemyRepository']] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQLAlchemy unit of work.
        
        Args:
            session_factory: Factory function for creating SQLAlchemy sessions
            repositories: Optional dictionary of repositories by entity type
            logger: Optional logger for diagnostic output
        """
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self._new_entities: Set[EntityProtocol] = set()
        self._dirty_entities: Set[EntityProtocol] = set()
        self._removed_entities: Set[EntityProtocol] = set()
        self._repositories: Dict[Type[EntityProtocol], 'SQLAlchemyRepository'] = repositories or {}
        self.logger = logger or logging.getLogger(__name__)
    
    async def __aenter__(self) -> 'SQLAlchemyUnitOfWork':
        """
        Enter the async unit of work context.
        
        Returns:
            The async unit of work
        """
        self._session = await self._session_factory().__aenter__()
        return self
    
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
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            # Always close the session
            if self._session is not None:
                await self._session.__aexit__(exc_type, exc_val, exc_tb)
                self._session = None
    
    async def commit(self) -> None:
        """Commit the unit of work."""
        if self._session is None:
            raise ValueError("Session is not initialized")
        
        try:
            # Process all entities
            await self._process_new_entities()
            await self._process_dirty_entities()
            await self._process_removed_entities()
            
            # Commit the transaction
            await self._session.commit()
            
            # Clear entity tracking
            self._new_entities.clear()
            self._dirty_entities.clear()
            self._removed_entities.clear()
        except Exception as e:
            self.logger.error(f"Error committing unit of work: {e}")
            await self.rollback()
            raise
    
    async def rollback(self) -> None:
        """Rollback the unit of work."""
        if self._session is not None:
            await self._session.rollback()
        
        # Clear entity tracking
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
    
    async def flush(self) -> None:
        """Flush changes to the database without committing."""
        if self._session is None:
            raise ValueError("Session is not initialized")
        
        # Process entities and flush changes
        await self._process_new_entities()
        await self._process_dirty_entities()
        await self._process_removed_entities()
        await self._session.flush()
    
    async def _process_new_entities(self) -> None:
        """Process new entities."""
        for entity in self._new_entities:
            await self._add_entity(entity)
    
    async def _process_dirty_entities(self) -> None:
        """Process dirty (modified) entities."""
        for entity in self._dirty_entities:
            await self._update_entity(entity)
    
    async def _process_removed_entities(self) -> None:
        """Process removed entities."""
        for entity in self._removed_entities:
            await self._remove_entity(entity)
    
    async def _add_entity(self, entity: EntityProtocol) -> None:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
        """
        entity_type = type(entity)
        repo = await self.get_repository(entity_type)
        await repo._add(entity)
    
    async def _update_entity(self, entity: EntityProtocol) -> None:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
        """
        entity_type = type(entity)
        repo = await self.get_repository(entity_type)
        await repo._update(entity)
    
    async def _remove_entity(self, entity: EntityProtocol) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        entity_type = type(entity)
        repo = await self.get_repository(entity_type)
        await repo._remove(entity)
    
    async def get_repository(self, entity_type: Type[T]) -> AsyncRepositoryProtocol[T]:
        """
        Get a repository for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            A repository for the entity type
        """
        if entity_type not in self._repositories:
            raise ValueError(f"No repository registered for entity type {entity_type.__name__}")
        
        return self._repositories[entity_type]
    
    async def register_new(self, entity: EntityProtocol) -> None:
        """
        Register a new entity.
        
        Args:
            entity: The entity to register
        """
        self._new_entities.add(entity)
    
    async def register_dirty(self, entity: EntityProtocol) -> None:
        """
        Register a modified entity.
        
        Args:
            entity: The entity to register
        """
        self._dirty_entities.add(entity)
    
    async def register_removed(self, entity: EntityProtocol) -> None:
        """
        Register a removed entity.
        
        Args:
            entity: The entity to register
        """
        self._removed_entities.add(entity)


class SQLAlchemyRepository(Generic[T, M], AsyncRepositoryProtocol[T]):
    """
    Repository implementation for SQLAlchemy.
    
    This class provides a base implementation of the repository protocol
    using SQLAlchemy for data access and specification translation.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        model_class: Type[M],
        session_factory: Callable[[], AsyncSession],
        unit_of_work_factory: Optional[Callable[[], AsyncUnitOfWorkProtocol]] = None,
        translator: Optional[SpecificationTranslator[T]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQLAlchemy repository.
        
        Args:
            entity_type: The domain entity type
            model_class: The SQLAlchemy model class
            session_factory: Factory function for creating SQLAlchemy sessions
            unit_of_work_factory: Optional factory function for creating units of work
            translator: Optional specification translator
            logger: Optional logger for diagnostic output
        """
        self.entity_type = entity_type
        self.model_class = model_class
        self.session_factory = session_factory
        self.unit_of_work_factory = unit_of_work_factory
        self.translator = translator or PostgreSQLSpecificationTranslator(model_class)
        self.logger = logger or logging.getLogger(__name__)
    
    async def get(self, id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        result = await self.get_result(id)
        return result.entity if result.is_success else None
    
    async def get_result(self, id: Any) -> GetResult[T]:
        """
        Get an entity by ID with result object.
        
        Args:
            id: The entity ID
            
        Returns:
            A result object containing the entity if found
        """
        try:
            entity = await self._get(id)
            return GetResult.success(entity)
        except Exception as e:
            self.logger.error(f"Error getting entity with ID {id}: {e}")
            return GetResult.failure(e)
    
    async def _get(self, id: Any) -> Optional[T]:
        """
        Internal method to get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            model = result.scalars().first()
        
        if model is None:
            return None
        
        return self._to_entity(model)
    
    async def find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        result = await self.find_result(specification)
        return result.entities if result.is_success else []
    
    async def find_result(self, specification: SpecificationProtocol[T]) -> FindResult[T]:
        """
        Find entities matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object containing the matching entities
        """
        try:
            entities = await self._find(specification)
            return FindResult.success(entities)
        except Exception as e:
            self.logger.error(f"Error finding entities with specification: {e}")
            return FindResult.failure(e)
    
    async def _find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """
        Internal method to find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        # Translate specification to SQLAlchemy query
        query = self.translator.translate(specification)
        
        # Execute query
        async with self.session_factory() as session:
            result = await session.execute(query)
            models = result.scalars().all()
        
        # Convert models to entities
        return [self._to_entity(model) for model in models]
    
    async def find_one(self, specification: SpecificationProtocol[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        result = await self.find_one_result(specification)
        return result.entity if result.is_success else None
    
    async def find_one_result(self, specification: SpecificationProtocol[T]) -> FindOneResult[T]:
        """
        Find a single entity matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object containing the matching entity
        """
        try:
            entity = await self._find_one(specification)
            return FindOneResult.success(entity)
        except Exception as e:
            self.logger.error(f"Error finding one entity with specification: {e}")
            return FindOneResult.failure(e)
    
    async def _find_one(self, specification: SpecificationProtocol[T]) -> Optional[T]:
        """
        Internal method to find a single entity matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        # Translate specification to SQLAlchemy query
        query = self.translator.translate(specification)
        
        # Add limit to return only one result
        query = query.limit(1)
        
        # Execute query
        async with self.session_factory() as session:
            result = await session.execute(query)
            model = result.scalars().first()
        
        # Convert model to entity
        return self._to_entity(model) if model is not None else None
    
    async def exists(self, specification: SpecificationProtocol[T]) -> bool:
        """
        Check if an entity exists matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            True if a matching entity exists, False otherwise
        """
        result = await self.exists_result(specification)
        return result.exists if result.is_success else False
    
    async def exists_result(self, specification: SpecificationProtocol[T]) -> ExistsResult[T]:
        """
        Check if an entity exists matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object indicating whether a matching entity exists
        """
        try:
            exists = await self._exists(specification)
            return ExistsResult.success(exists)
        except Exception as e:
            self.logger.error(f"Error checking existence with specification: {e}")
            return ExistsResult.failure(e)
    
    async def _exists(self, specification: SpecificationProtocol[T]) -> bool:
        """
        Internal method to check if an entity exists matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            True if a matching entity exists, False otherwise
        """
        count = await self._count(specification)
        return count > 0
    
    async def count(self, specification: SpecificationProtocol[T]) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The number of matching entities
        """
        result = await self.count_result(specification)
        return result.count if result.is_success else 0
    
    async def count_result(self, specification: SpecificationProtocol[T]) -> CountResult[T]:
        """
        Count entities matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A result object containing the count
        """
        try:
            count = await self._count(specification)
            return CountResult.success(count)
        except Exception as e:
            self.logger.error(f"Error counting with specification: {e}")
            return CountResult.failure(e)
    
    async def _count(self, specification: SpecificationProtocol[T]) -> int:
        """
        Internal method to count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The number of matching entities
        """
        # Translate specification to SQLAlchemy query
        query = self.translator.translate(specification)
        
        # Modify query to count
        count_query = select(func.count()).select_from(query.subquery())
        
        # Execute query
        async with self.session_factory() as session:
            result = await session.execute(count_query)
            count = result.scalar_one()
        
        return count
    
    async def add(self, entity: T) -> None:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
        """
        result = await self.add_result(entity)
        if result.is_failure and result.error:
            raise result.error
    
    async def add_result(self, entity: T) -> AddResult[T]:
        """
        Add a new entity with result object.
        
        Args:
            entity: The entity to add
            
        Returns:
            A result object indicating success or failure
        """
        try:
            await self._add(entity)
            return AddResult.success(entity)
        except Exception as e:
            self.logger.error(f"Error adding entity: {e}")
            return AddResult.failure(e)
    
    async def _add(self, entity: T) -> None:
        """
        Internal method to add a new entity.
        
        Args:
            entity: The entity to add
        """
        # Convert entity to model
        model = self._to_model(entity)
        
        # Add model to session
        async with self.session_factory() as session:
            session.add(model)
            await session.commit()
    
    async def update(self, entity: T) -> None:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
        """
        result = await self.update_result(entity)
        if result.is_failure and result.error:
            raise result.error
    
    async def update_result(self, entity: T) -> UpdateResult[T]:
        """
        Update an existing entity with result object.
        
        Args:
            entity: The entity to update
            
        Returns:
            A result object indicating success or failure
        """
        try:
            await self._update(entity)
            return UpdateResult.success(entity)
        except Exception as e:
            self.logger.error(f"Error updating entity: {e}")
            return UpdateResult.failure(e)
    
    async def _update(self, entity: T) -> None:
        """
        Internal method to update an existing entity.
        
        Args:
            entity: The entity to update
        """
        # Check if entity exists
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == entity.id)
            )
            model = result.scalars().first()
            
            if model is None:
                raise ValueError(f"Entity with id {entity.id} not found")
            
            # Update model with entity data
            self._update_model(model, entity)
            
            # Commit changes
            await session.commit()
    
    async def remove(self, entity: T) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        result = await self.remove_result(entity)
        if result.is_failure and result.error:
            raise result.error
    
    async def remove_result(self, entity: T) -> RemoveResult[T]:
        """
        Remove an entity with result object.
        
        Args:
            entity: The entity to remove
            
        Returns:
            A result object indicating success or failure
        """
        try:
            await self._remove(entity)
            return RemoveResult.success(entity)
        except Exception as e:
            self.logger.error(f"Error removing entity: {e}")
            return RemoveResult.failure(e)
    
    async def _remove(self, entity: T) -> None:
        """
        Internal method to remove an entity.
        
        Args:
            entity: The entity to remove
        """
        # Remove model from session
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == entity.id)
            )
            model = result.scalars().first()
            
            if model is None:
                raise ValueError(f"Entity with id {entity.id} not found")
            
            await session.delete(model)
            await session.commit()
    
    def _to_entity(self, model: M) -> T:
        """
        Convert a model to a domain entity.
        
        Args:
            model: The model to convert
            
        Returns:
            The corresponding domain entity
        """
        # Extract data from model
        data = self._model_to_dict(model)
        
        # Create entity from data
        return self.entity_type(**data)
    
    def _to_model(self, entity: T) -> M:
        """
        Convert a domain entity to a model.
        
        Args:
            entity: The entity to convert
            
        Returns:
            The corresponding model
        """
        # Extract data from entity
        data = self._entity_to_dict(entity)
        
        # Create model from data
        return self.model_class(**data)
    
    def _update_model(self, model: M, entity: T) -> None:
        """
        Update a model with entity data.
        
        Args:
            model: The model to update
            entity: The entity with updated data
        """
        # Extract data from entity
        data = self._entity_to_dict(entity)
        
        # Update model attributes
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        # Set updated_at timestamp if available
        if hasattr(model, 'updated_at'):
            model.updated_at = datetime.now(timezone.utc)
    
    def _model_to_dict(self, model: M) -> Dict[str, Any]:
        """
        Convert a model to a dictionary.
        
        Args:
            model: The model to convert
            
        Returns:
            Dictionary representation of the model
        """
        # Convert SQLAlchemy model to dictionary
        # Exclude SQLAlchemy internal attributes
        return {
            k: v for k, v in model.__dict__.items()
            if not k.startswith('_')
        }
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert an entity to a dictionary.
        
        Args:
            entity: The entity to convert
            
        Returns:
            Dictionary representation of the entity
        """
        # Convert Pydantic model to dictionary
        if hasattr(entity, 'model_dump'):
            # Pydantic v2
            return entity.model_dump()
        elif hasattr(entity, 'dict'):
            # Pydantic v1
            return entity.dict()
        else:
            # Fallback to __dict__
            return {
                k: v for k, v in entity.__dict__.items()
                if not k.startswith('_')
            }