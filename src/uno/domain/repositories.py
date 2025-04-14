"""
Repository pattern implementation for the Uno framework.

This module provides the repository pattern for accessing and persisting
domain entities and aggregates, abstracting the details of the persistence mechanism.
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, Type, TypeVar, Any, Set, cast
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from uno.domain.model import Entity, AggregateRoot
from uno.domain.events import DomainEvent
from uno.core.errors.base import EntityNotFoundError, ConcurrencyError


T = TypeVar('T', bound=Entity)
A = TypeVar('A', bound=AggregateRoot)


class Repository(Generic[T], ABC):
    """
    Abstract base class for repositories.
    
    Repositories provide a collection-like interface for accessing and persisting
    domain entities, abstracting the details of the persistence mechanism.
    """
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> T:
        """
        Get an entity by ID, raising an exception if not found.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity
            
        Raises:
            EntityNotFoundError: If the entity is not found
        """
        entity = await self.get(id)
        if entity is None:
            raise EntityNotFoundError(self._get_entity_type_name(), id)
        return entity
    
    @abstractmethod
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        List entities with filtering and pagination.
        
        Args:
            filters: Optional filter criteria
            order_by: Optional ordering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the criteria
        """
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity (possibly with generated ID)
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        pass
    
    @abstractmethod
    async def remove(self, entity: T) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        pass
    
    @abstractmethod
    async def remove_by_id(self, id: str) -> bool:
        """
        Remove an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            True if the entity was removed, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: The entity ID
            
        Returns:
            True if the entity exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching the given criteria.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            The number of matching entities
        """
        pass
    
    def _get_entity_type_name(self) -> str:
        """Get the name of the entity type managed by this repository."""
        return self.__class__.__name__.replace('Repository', '')


class AggregateRepository(Repository[A], Generic[A]):
    """
    Repository for aggregate roots.
    
    This repository provides methods for working with aggregate roots,
    including managing their lifecycle and collecting domain events.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the aggregate repository.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._pending_events: List[DomainEvent] = []
    
    async def save(self, aggregate: A) -> A:
        """
        Save an aggregate (create or update).
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
            
        Raises:
            ConcurrencyError: If the aggregate has been modified since it was loaded
        """
        # Check if aggregate exists
        exists = await self.exists(aggregate.id)
        
        # Apply changes and collect events
        aggregate.apply_changes()
        self._collect_aggregate_events(aggregate)
        
        # Save the aggregate
        if exists:
            return await self.update(aggregate)
        else:
            return await self.add(aggregate)
    
    def collect_events(self) -> List[DomainEvent]:
        """
        Collect all pending domain events.
        
        Returns:
            List of pending domain events
        """
        events = self._pending_events.copy()
        self._pending_events.clear()
        return events
    
    def _collect_aggregate_events(self, aggregate: A) -> None:
        """
        Collect events from an aggregate.
        
        Args:
            aggregate: The aggregate to collect events from
        """
        self._pending_events.extend(aggregate.clear_events())


class SqlAlchemyRepository(Repository[T], Generic[T]):
    """
    SQLAlchemy implementation of the repository pattern.
    
    This repository uses SQLAlchemy to persist entities.
    """
    
    def __init__(
        self, 
        session: AsyncSession, 
        entity_type: Type[T],
        table_name: str,
        model_class: Any = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQLAlchemy repository.
        
        Args:
            session: The SQLAlchemy session
            entity_type: The type of entity this repository manages
            table_name: The name of the database table
            model_class: Optional SQLAlchemy model class for ORM mapping
            logger: Optional logger instance
        """
        self.session = session
        self.entity_type = entity_type
        self.table_name = table_name
        self.model_class = model_class
        self.logger = logger or logging.getLogger(__name__)
    
    async def get(self, id: str) -> Optional[T]:
        """Get an entity by ID."""
        try:
            if self.model_class:
                # Use SQLAlchemy ORM
                stmt = select(self.model_class).where(self.model_class.id == id)
                result = await self.session.execute(stmt)
                model = result.scalars().first()
                if model is None:
                    return None
                return self._convert_to_entity(model)
            else:
                # Use SQLAlchemy Core
                stmt = select("*").select_from(self.table_name).where(f"{self.table_name}.id = :id")
                result = await self.session.execute(stmt, {"id": id})
                row = result.first()
                if row is None:
                    return None
                return self._convert_to_entity(dict(row))
        except Exception as e:
            self.logger.error(f"Error getting entity by ID {id}: {str(e)}")
            return None
    
    async def get_by_id(self, id: str) -> T:
        """Get an entity by ID, raising an exception if not found."""
        entity = await self.get(id)
        if entity is None:
            raise EntityNotFoundError(self._get_entity_type_name(), id)
        return entity
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """List entities with filtering and pagination."""
        try:
            if self.model_class:
                # Use SQLAlchemy ORM
                stmt = select(self.model_class)
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        stmt = stmt.where(getattr(self.model_class, field) == value)
                
                # Apply ordering
                if order_by:
                    for field in order_by:
                        if field.startswith('-'):
                            stmt = stmt.order_by(getattr(self.model_class, field[1:]).desc())
                        else:
                            stmt = stmt.order_by(getattr(self.model_class, field))
                
                # Apply pagination
                if limit is not None:
                    stmt = stmt.limit(limit)
                if offset is not None:
                    stmt = stmt.offset(offset)
                
                # Execute query
                result = await self.session.execute(stmt)
                models = result.scalars().all()
                
                # Convert to entities
                return [self._convert_to_entity(model) for model in models]
            else:
                # Use SQLAlchemy Core
                stmt = select("*").select_from(self.table_name)
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        stmt = stmt.where(f"{self.table_name}.{field} = :{field}")
                
                # Apply ordering
                if order_by:
                    for field in order_by:
                        if field.startswith('-'):
                            stmt = stmt.order_by(f"{self.table_name}.{field[1:]} DESC")
                        else:
                            stmt = stmt.order_by(f"{self.table_name}.{field}")
                
                # Apply pagination
                if limit is not None:
                    stmt = stmt.limit(limit)
                if offset is not None:
                    stmt = stmt.offset(offset)
                
                # Execute query
                result = await self.session.execute(stmt, filters or {})
                rows = result.fetchall()
                
                # Convert to entities
                return [self._convert_to_entity(dict(row)) for row in rows]
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return []
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        try:
            # Check if entity already exists
            if await self.exists(entity.id):
                raise ValueError(f"Entity with ID {entity.id} already exists")
            
            # Convert entity to model/data
            data = self._convert_to_model_data(entity)
            
            if self.model_class:
                # Use SQLAlchemy ORM
                model = self.model_class(**data)
                self.session.add(model)
                await self.session.flush()
                return self._convert_to_entity(model)
            else:
                # Use SQLAlchemy Core
                stmt = insert(self.table_name).values(**data).returning("*")
                result = await self.session.execute(stmt)
                row = result.first()
                return self._convert_to_entity(dict(row))
        except Exception as e:
            self.logger.error(f"Error adding entity: {str(e)}")
            raise
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            # Ensure entity exists
            if not await self.exists(entity.id):
                raise EntityNotFoundError(self._get_entity_type_name(), id)
            
            # Convert entity to model/data
            data = self._convert_to_model_data(entity)
            
            # Handle optimistic concurrency control if applicable
            if isinstance(entity, AggregateRoot):
                if self.model_class:
                    # Use SQLAlchemy ORM with version check
                    stmt = select(self.model_class).where(
                        self.model_class.id == entity.id,
                        self.model_class.version == entity.version - 1  # Version should be one less
                    )
                    result = await self.session.execute(stmt)
                    model = result.scalars().first()
                    if model is None:
                        raise ConcurrencyError(self._get_entity_type_name(), entity.id)
                    
                    # Update model
                    for key, value in data.items():
                        setattr(model, key, value)
                    
                    await self.session.flush()
                    return self._convert_to_entity(model)
                else:
                    # Use SQLAlchemy Core with version check
                    stmt = update(self.table_name).where(
                        f"{self.table_name}.id = :id AND {self.table_name}.version = :version"
                    ).values(**data).returning("*")
                    
                    result = await self.session.execute(
                        stmt, 
                        {"id": entity.id, "version": entity.version - 1}
                    )
                    row = result.first()
                    if row is None:
                        raise ConcurrencyError(self._get_entity_type_name(), entity.id)
                    
                    return self._convert_to_entity(dict(row))
            else:
                # Regular entity without versioning
                if self.model_class:
                    # Use SQLAlchemy ORM
                    stmt = select(self.model_class).where(self.model_class.id == entity.id)
                    result = await self.session.execute(stmt)
                    model = result.scalars().first()
                    if model is None:
                        raise EntityNotFoundError(self._get_entity_type_name(), entity.id)
                    
                    # Update model
                    for key, value in data.items():
                        setattr(model, key, value)
                    
                    await self.session.flush()
                    return self._convert_to_entity(model)
                else:
                    # Use SQLAlchemy Core
                    stmt = update(self.table_name).where(
                        f"{self.table_name}.id = :id"
                    ).values(**data).returning("*")
                    
                    result = await self.session.execute(stmt, {"id": entity.id})
                    row = result.first()
                    if row is None:
                        raise EntityNotFoundError(self._get_entity_type_name(), entity.id)
                    
                    return self._convert_to_entity(dict(row))
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            raise
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        await self.remove_by_id(entity.id)
    
    async def remove_by_id(self, id: str) -> bool:
        """Remove an entity by ID."""
        try:
            if self.model_class:
                # Use SQLAlchemy ORM
                stmt = delete(self.model_class).where(self.model_class.id == id)
                result = await self.session.execute(stmt)
                return result.rowcount > 0
            else:
                # Use SQLAlchemy Core
                stmt = delete(self.table_name).where(f"{self.table_name}.id = :id")
                result = await self.session.execute(stmt, {"id": id})
                return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error removing entity by ID {id}: {str(e)}")
            return False
    
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        try:
            if self.model_class:
                # Use SQLAlchemy ORM
                stmt = select(self.model_class.id).where(self.model_class.id == id)
                result = await self.session.execute(stmt)
                return result.scalar() is not None
            else:
                # Use SQLAlchemy Core
                stmt = select("id").select_from(self.table_name).where(f"{self.table_name}.id = :id")
                result = await self.session.execute(stmt, {"id": id})
                return result.scalar() is not None
        except Exception as e:
            self.logger.error(f"Error checking if entity exists: {str(e)}")
            return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching the given criteria."""
        try:
            if self.model_class:
                # Use SQLAlchemy ORM
                stmt = select(self.model_class)
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        stmt = stmt.where(getattr(self.model_class, field) == value)
                
                # Execute query
                result = await self.session.execute(stmt)
                return len(result.scalars().all())
            else:
                # Use SQLAlchemy Core
                stmt = select("COUNT(*)").select_from(self.table_name)
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        stmt = stmt.where(f"{self.table_name}.{field} = :{field}")
                
                # Execute query
                result = await self.session.execute(stmt, filters or {})
                return result.scalar()
        except Exception as e:
            self.logger.error(f"Error counting entities: {str(e)}")
            return 0
    
    def _convert_to_entity(self, data: Any) -> T:
        """
        Convert data/model to entity.
        
        Args:
            data: Data to convert
            
        Returns:
            Entity instance
        """
        if isinstance(data, dict):
            return self.entity_type(**data)
        else:
            # If it's a model, convert it to a dict
            return self.entity_type(**{k: getattr(data, k) for k in data.__table__.columns.keys()})
    
    def _convert_to_model_data(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to model data.
        
        Args:
            entity: Entity to convert
            
        Returns:
            Model data as a dictionary
        """
        # Use to_dict method if available
        if hasattr(entity, 'to_dict') and callable(getattr(entity, 'to_dict')):
            return entity.to_dict()
        else:
            # Otherwise, convert all public attributes
            return {k: v for k, v in entity.__dict__.items() if not k.startswith('_')}


class SqlAlchemyAggregateRepository(AggregateRepository[A], SqlAlchemyRepository[A], Generic[A]):
    """
    SQLAlchemy implementation of the aggregate repository.
    
    This repository uses SQLAlchemy to persist aggregate roots.
    """
    
    def __init__(
        self, 
        session: AsyncSession, 
        aggregate_type: Type[A],
        table_name: str,
        model_class: Any = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQLAlchemy aggregate repository.
        
        Args:
            session: The SQLAlchemy session
            aggregate_type: The type of aggregate this repository manages
            table_name: The name of the database table
            model_class: Optional SQLAlchemy model class for ORM mapping
            logger: Optional logger instance
        """
        AggregateRepository.__init__(self, logger)
        SqlAlchemyRepository.__init__(
            self, session, aggregate_type, table_name, model_class, logger
        )
    
    async def add(self, aggregate: A) -> A:
        """Add a new aggregate."""
        # Collect events first
        self._collect_aggregate_events(aggregate)
        
        # Delegate to base implementation
        return await SqlAlchemyRepository.add(self, aggregate)
    
    async def update(self, aggregate: A) -> A:
        """Update an existing aggregate."""
        # Collect events first
        self._collect_aggregate_events(aggregate)
        
        # Delegate to base implementation
        return await SqlAlchemyRepository.update(self, aggregate)
    
    async def save(self, aggregate: A) -> A:
        """
        Save an aggregate (create or update).
        
        This method applies changes, checks invariants, and manages the
        aggregate's lifecycle.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
        """
        # Apply changes and check invariants
        aggregate.apply_changes()
        
        # Collect events
        self._collect_aggregate_events(aggregate)
        
        # Determine if this is a create or update
        exists = await self.exists(aggregate.id)
        
        # Save the aggregate
        if exists:
            return await SqlAlchemyRepository.update(self, aggregate)
        else:
            return await SqlAlchemyRepository.add(self, aggregate)


class InMemoryRepository(Repository[T], Generic[T]):
    """
    In-memory repository for testing.
    
    This repository stores entities in memory, which is useful for testing.
    """
    
    def __init__(self, entity_type: Type[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the in-memory repository.
        
        Args:
            entity_type: The type of entity this repository manages
            logger: Optional logger instance
        """
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(__name__)
        self.entities: Dict[str, T] = {}
    
    async def get(self, id: str) -> Optional[T]:
        """Get an entity by ID."""
        return self.entities.get(id)
    
    async def get_by_id(self, id: str) -> T:
        """Get an entity by ID, raising an exception if not found."""
        entity = await self.get(id)
        if entity is None:
            raise EntityNotFoundError(self._get_entity_type_name(), id)
        return entity
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """List entities with filtering and pagination."""
        entities = list(self.entities.values())
        
        # Apply filters
        if filters:
            filtered_entities = []
            for entity in entities:
                matches = True
                for field, value in filters.items():
                    if getattr(entity, field, None) != value:
                        matches = False
                        break
                if matches:
                    filtered_entities.append(entity)
            entities = filtered_entities
        
        # Apply ordering
        if order_by:
            for field in reversed(order_by):
                reverse = False
                if field.startswith('-'):
                    reverse = True
                    field = field[1:]
                
                entities.sort(key=lambda e: getattr(e, field, None), reverse=reverse)
        
        # Apply pagination
        if offset is not None:
            entities = entities[offset:]
        
        if limit is not None:
            entities = entities[:limit]
        
        return entities
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        if entity.id in self.entities:
            raise ValueError(f"Entity with ID {entity.id} already exists")
        
        # Add entity to the repository
        self.entities[entity.id] = entity
        
        return entity
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        if entity.id not in self.entities:
            raise EntityNotFoundError(self._get_entity_type_name(), entity.id)
        
        # Handle optimistic concurrency control
        if isinstance(entity, AggregateRoot) and isinstance(self.entities[entity.id], AggregateRoot):
            existing_version = self.entities[entity.id].version
            if existing_version != entity.version - 1:
                raise ConcurrencyError(self._get_entity_type_name(), entity.id)
        
        # Update entity in the repository
        self.entities[entity.id] = entity
        
        return entity
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        await self.remove_by_id(entity.id)
    
    async def remove_by_id(self, id: str) -> bool:
        """Remove an entity by ID."""
        if id in self.entities:
            del self.entities[id]
            return True
        return False
    
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        return id in self.entities
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching the given criteria."""
        if not filters:
            return len(self.entities)
        
        # Apply filters
        count = 0
        for entity in self.entities.values():
            matches = True
            for field, value in filters.items():
                if getattr(entity, field, None) != value:
                    matches = False
                    break
            if matches:
                count += 1
        
        return count


class InMemoryAggregateRepository(AggregateRepository[A], InMemoryRepository[A], Generic[A]):
    """
    In-memory repository for aggregates.
    
    This repository extends the in-memory repository with aggregate-specific
    functionality.
    """
    
    def __init__(self, aggregate_type: Type[A], logger: Optional[logging.Logger] = None):
        """
        Initialize the in-memory aggregate repository.
        
        Args:
            aggregate_type: The type of aggregate this repository manages
            logger: Optional logger instance
        """
        AggregateRepository.__init__(self, logger)
        InMemoryRepository.__init__(self, aggregate_type, logger)
    
    async def add(self, aggregate: A) -> A:
        """Add a new aggregate."""
        # Collect events first
        self._collect_aggregate_events(aggregate)
        
        # Delegate to base implementation
        return await InMemoryRepository.add(self, aggregate)
    
    async def update(self, aggregate: A) -> A:
        """Update an existing aggregate."""
        # Collect events first
        self._collect_aggregate_events(aggregate)
        
        # Delegate to base implementation
        return await InMemoryRepository.update(self, aggregate)