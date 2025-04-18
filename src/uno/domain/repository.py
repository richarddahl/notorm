"""
Repository pattern implementation for the domain layer.

This module provides a standardized repository pattern implementation that aligns
with the unified domain model, supporting both synchronous and asynchronous operations,
the specification pattern, and event collection from aggregates.
"""

from abc import ABC, abstractmethod
from typing import (
    Generic, TypeVar, Optional, List, Dict, Any, Type, Set, Union, 
    Protocol, runtime_checkable, Callable, AsyncIterator, Iterable
)
from datetime import datetime, UTC
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, and_, or_, not_

from uno.domain.core import Entity, AggregateRoot
from uno.core.events import DomainEventProtocol
from uno.domain.specifications import Specification
from uno.core.errors.result import Result, Success, Failure


# Type variables
T = TypeVar("T", bound=Entity)  # Entity type
A = TypeVar("A", bound=AggregateRoot)  # Aggregate type
M = TypeVar("M")  # Model type for the ORM


@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    """Protocol for repository operations."""
    
    async def get(self, id: Any) -> Optional[T]:
        """Get an entity by ID."""
        ...
    
    async def find(self, specification: Specification[T]) -> List[T]:
        """Find entities matching the specification."""
        ...
    
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """Find a single entity matching the specification."""
        ...
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        ...
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        ...
    
    async def exists(self, id: Any) -> bool:
        """Check if an entity with the ID exists."""
        ...


class Repository(Generic[T], ABC):
    """
    Abstract base repository for domain entities.
    
    This class provides a standardized interface for repository operations,
    abstracting the persistence details from the domain layer.
    """
    
    def __init__(self, entity_type: Type[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the repository.
        
        Args:
            entity_type: The type of entity this repository manages
            logger: Optional logger for diagnostic output
        """
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    async def get_by_id(self, id: Any) -> Result[T]:
        """
        Get an entity by ID with result object.
        
        Args:
            id: The entity ID
            
        Returns:
            A Result containing the entity if found, or a failure
        """
        try:
            entity = await self.get(id)
            if entity is None:
                return Failure(f"Entity with ID {id} not found")
            return Success(entity)
        except Exception as e:
            self.logger.error(f"Error getting entity with ID {id}: {e}")
            return Failure(str(e))
    
    @abstractmethod
    async def find(self, specification: Specification[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        pass
    
    async def find_result(self, specification: Specification[T]) -> Result[List[T]]:
        """
        Find entities matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A Result containing the matching entities or a failure
        """
        try:
            entities = await self.find(specification)
            return Success(entities)
        except Exception as e:
            self.logger.error(f"Error finding entities: {e}")
            return Failure(str(e))
    
    @abstractmethod
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        pass
    
    async def find_one_result(self, specification: Specification[T]) -> Result[Optional[T]]:
        """
        Find a single entity matching a specification with result object.
        
        Args:
            specification: The specification to match
            
        Returns:
            A Result containing the matching entity or a failure
        """
        try:
            entity = await self.find_one(specification)
            return Success(entity)
        except Exception as e:
            self.logger.error(f"Error finding entity: {e}")
            return Failure(str(e))
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
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
    
    async def add_result(self, entity: T) -> Result[T]:
        """
        Add a new entity with result object.
        
        Args:
            entity: The entity to add
            
        Returns:
            A Result containing the added entity or a failure
        """
        try:
            added_entity = await self.add(entity)
            return Success(added_entity)
        except Exception as e:
            self.logger.error(f"Error adding entity: {e}")
            return Failure(str(e))
    
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
    
    async def update_result(self, entity: T) -> Result[T]:
        """
        Update an existing entity with result object.
        
        Args:
            entity: The entity to update
            
        Returns:
            A Result containing the updated entity or a failure
        """
        try:
            updated_entity = await self.update(entity)
            return Success(updated_entity)
        except Exception as e:
            self.logger.error(f"Error updating entity: {e}")
            return Failure(str(e))
    
    @abstractmethod
    async def remove(self, entity: T) -> None:
        """
        Remove an entity.
        
        Args:
            entity: The entity to remove
        """
        pass
    
    async def remove_result(self, entity: T) -> Result[None]:
        """
        Remove an entity with result object.
        
        Args:
            entity: The entity to remove
            
        Returns:
            A Result indicating success or failure
        """
        try:
            await self.remove(entity)
            return Success(None)
        except Exception as e:
            self.logger.error(f"Error removing entity: {e}")
            return Failure(str(e))
    
    @abstractmethod
    async def remove_by_id(self, id: Any) -> bool:
        """
        Remove an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            True if the entity was removed, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: The entity ID
            
        Returns:
            True if the entity exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: Optional specification to match
            
        Returns:
            The number of matching entities
        """
        pass
    
    async def count_filtered(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            The number of matching entities
        """
        raise NotImplementedError("This method must be implemented by subclasses")


class AggregateRepository(Repository[A], Generic[A]):
    """
    Repository for aggregate roots.
    
    This repository extends the base repository with methods for working with
    aggregate roots, including event collection and lifecycle management.
    """
    
    def __init__(self, aggregate_type: Type[A], logger: Optional[logging.Logger] = None):
        """
        Initialize the aggregate repository.
        
        Args:
            aggregate_type: The type of aggregate this repository manages
            logger: Optional logger for diagnostic output
        """
        super().__init__(aggregate_type, logger)
        self._pending_events: List[DomainEventProtocol] = []
    
    async def save(self, aggregate: A) -> A:
        """
        Save an aggregate (create or update).
        
        This method applies changes to the aggregate, collects events,
        and persists the aggregate to the repository.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
        """
        # Apply changes to ensure invariants and increment version
        aggregate.apply_changes()
        
        # Collect events
        self._collect_events(aggregate)
        
        # Determine if this is a create or update
        exists = await self.exists(aggregate.id)
        
        # Save the aggregate
        if exists:
            return await self.update(aggregate)
        else:
            return await self.add(aggregate)
    
    async def save_result(self, aggregate: A) -> Result[A]:
        """
        Save an aggregate with result object.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            A Result containing the saved aggregate or a failure
        """
        try:
            saved_aggregate = await self.save(aggregate)
            return Success(saved_aggregate)
        except Exception as e:
            self.logger.error(f"Error saving aggregate: {e}")
            return Failure(str(e))
    
    def collect_events(self) -> List[DomainEventProtocol]:
        """
        Collect all pending domain events.
        
        Returns:
            List of pending domain events
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
    
    def _collect_events(self, aggregate: A) -> None:
        """
        Collect events from an aggregate.
        
        Args:
            aggregate: The aggregate to collect events from
        """
        # Get events from the aggregate
        events = aggregate.clear_events()
        
        # Add them to the pending events
        self._pending_events.extend(events)
        
        # Also collect events from child entities
        for child in aggregate.get_child_entities():
            if hasattr(child, "clear_events"):
                self._pending_events.extend(child.clear_events())


class SQLAlchemyRepository(Repository[T], Generic[T, M]):
    """
    SQLAlchemy implementation of the repository pattern.
    
    This repository uses SQLAlchemy for data access, with support for both
    ORM and Core approaches.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        session: AsyncSession,
        model_class: Type[M],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SQLAlchemy repository.
        
        Args:
            entity_type: The type of entity this repository manages
            session: SQLAlchemy async session
            model_class: SQLAlchemy model class
            logger: Optional logger for diagnostic output
        """
        super().__init__(entity_type, logger)
        self.session = session
        self.model_class = model_class
    
    async def get(self, id: Any) -> Optional[T]:
        """Get an entity by ID."""
        try:
            stmt = select(self.model_class).where(self.model_class.id == id)
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            
            if model is None:
                return None
                
            return self._to_entity(model)
        except Exception as e:
            self.logger.error(f"Error getting entity with ID {id}: {e}")
            return None
    
    async def find(self, specification: Specification[T]) -> List[T]:
        """Find entities matching a specification."""
        try:
            # Convert specification to SQLAlchemy criteria
            criteria = self._specification_to_criteria(specification)
            
            # Build query
            stmt = select(self.model_class)
            if criteria is not None:
                stmt = stmt.where(criteria)
                
            # Execute query
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # Convert to entities
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self.logger.error(f"Error finding entities: {e}")
            return []
    
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """Find a single entity matching a specification."""
        try:
            # Convert specification to SQLAlchemy criteria
            criteria = self._specification_to_criteria(specification)
            
            # Build query
            stmt = select(self.model_class)
            if criteria is not None:
                stmt = stmt.where(criteria)
                
            # Limit to one result
            stmt = stmt.limit(1)
                
            # Execute query
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            
            # Convert to entity
            if model is None:
                return None
                
            return self._to_entity(model)
        except Exception as e:
            self.logger.error(f"Error finding entity: {e}")
            return None
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """List entities with filtering and pagination."""
        try:
            # Build base query
            stmt = select(self.model_class)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if isinstance(value, dict) and "op" in value and "value" in value:
                        # Handle advanced filters with operators
                        op = value["op"]
                        val = value["value"]
                        
                        if op == "eq":
                            stmt = stmt.where(getattr(self.model_class, field) == val)
                        elif op == "neq":
                            stmt = stmt.where(getattr(self.model_class, field) != val)
                        elif op == "gt":
                            stmt = stmt.where(getattr(self.model_class, field) > val)
                        elif op == "gte":
                            stmt = stmt.where(getattr(self.model_class, field) >= val)
                        elif op == "lt":
                            stmt = stmt.where(getattr(self.model_class, field) < val)
                        elif op == "lte":
                            stmt = stmt.where(getattr(self.model_class, field) <= val)
                        elif op == "in":
                            stmt = stmt.where(getattr(self.model_class, field).in_(val))
                        elif op == "like":
                            stmt = stmt.where(getattr(self.model_class, field).like(f"%{val}%"))
                    else:
                        # Simple equality filter
                        stmt = stmt.where(getattr(self.model_class, field) == value)
            
            # Apply ordering
            if order_by:
                for field in order_by:
                    if field.startswith("-"):
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
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self.logger.error(f"Error listing entities: {e}")
            return []
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        try:
            # Check if entity already exists
            if entity.id and await self.exists(entity.id):
                raise ValueError(f"Entity with ID {entity.id} already exists")
            
            # Ensure created_at is set
            if not entity.created_at:
                entity.created_at = datetime.now(UTC)
            
            # Convert entity to model data
            data = self._to_model_data(entity)
            
            # Create model instance
            model = self.model_class(**data)
            
            # Add to session
            self.session.add(model)
            await self.session.flush()
            
            # Convert back to entity
            return self._to_entity(model)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error adding entity: {e}")
            raise
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            # Ensure entity exists
            if not await self.exists(entity.id):
                raise ValueError(f"Entity with ID {entity.id} not found")
            
            # Set updated_at
            entity.updated_at = datetime.now(UTC)
            
            # Convert entity to model data
            data = self._to_model_data(entity)
            
            # Check for optimistic concurrency control
            if isinstance(entity, AggregateRoot):
                # Use version for optimistic concurrency control
                stmt = select(self.model_class).where(
                    self.model_class.id == entity.id,
                    self.model_class.version == entity.version - 1
                )
                result = await self.session.execute(stmt)
                model = result.scalars().first()
                
                if model is None:
                    raise ValueError(f"Concurrency conflict for entity {entity.id}")
                
                # Update model attributes
                for key, value in data.items():
                    setattr(model, key, value)
                
                await self.session.flush()
                return self._to_entity(model)
            else:
                # Regular entity without versioning
                stmt = select(self.model_class).where(self.model_class.id == entity.id)
                result = await self.session.execute(stmt)
                model = result.scalars().first()
                
                if model is None:
                    raise ValueError(f"Entity with ID {entity.id} not found")
                
                # Update model attributes
                for key, value in data.items():
                    setattr(model, key, value)
                
                await self.session.flush()
                return self._to_entity(model)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating entity: {e}")
            raise
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        await self.remove_by_id(entity.id)
    
    async def remove_by_id(self, id: Any) -> bool:
        """Remove an entity by ID."""
        try:
            # Find the entity
            stmt = select(self.model_class).where(self.model_class.id == id)
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            
            if model is None:
                return False
            
            # Delete the entity
            await self.session.delete(model)
            await self.session.flush()
            
            return True
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error removing entity with ID {id}: {e}")
            return False
    
    async def exists(self, id: Any) -> bool:
        """Check if an entity exists."""
        try:
            stmt = select(func.count()).select_from(self.model_class).where(
                self.model_class.id == id
            )
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking if entity exists: {e}")
            return False
    
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """Count entities matching a specification."""
        try:
            # Build base query
            stmt = select(func.count()).select_from(self.model_class)
            
            # Apply specification
            if specification is not None:
                criteria = self._specification_to_criteria(specification)
                if criteria is not None:
                    stmt = stmt.where(criteria)
            
            # Execute query
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            return count
        except Exception as e:
            self.logger.error(f"Error counting entities: {e}")
            return 0
    
    async def count_filtered(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filter criteria."""
        try:
            # Build base query
            stmt = select(func.count()).select_from(self.model_class)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if isinstance(value, dict) and "op" in value and "value" in value:
                        # Handle advanced filters with operators
                        op = value["op"]
                        val = value["value"]
                        
                        if op == "eq":
                            stmt = stmt.where(getattr(self.model_class, field) == val)
                        elif op == "neq":
                            stmt = stmt.where(getattr(self.model_class, field) != val)
                        elif op == "gt":
                            stmt = stmt.where(getattr(self.model_class, field) > val)
                        elif op == "gte":
                            stmt = stmt.where(getattr(self.model_class, field) >= val)
                        elif op == "lt":
                            stmt = stmt.where(getattr(self.model_class, field) < val)
                        elif op == "lte":
                            stmt = stmt.where(getattr(self.model_class, field) <= val)
                        elif op == "in":
                            stmt = stmt.where(getattr(self.model_class, field).in_(val))
                        elif op == "like":
                            stmt = stmt.where(getattr(self.model_class, field).like(f"%{val}%"))
                    else:
                        # Simple equality filter
                        stmt = stmt.where(getattr(self.model_class, field) == value)
            
            # Execute query
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            return count
        except Exception as e:
            self.logger.error(f"Error counting entities: {e}")
            return 0
    
    def _to_entity(self, model: M) -> T:
        """
        Convert a model to an entity.
        
        Args:
            model: The model to convert
            
        Returns:
            The entity
        """
        # Extract data from model
        if hasattr(model, "__table__"):
            # SQLAlchemy model
            data = {
                c.name: getattr(model, c.name)
                for c in model.__table__.columns
                if not c.name.startswith("_")
            }
        elif hasattr(model, "__dict__"):
            # Object with __dict__
            data = {
                k: v
                for k, v in model.__dict__.items()
                if not k.startswith("_")
            }
        else:
            # Try to convert to dict as a last resort
            data = dict(model)
        
        # Create entity from data
        return self.entity_type(**data)
    
    def _to_model_data(self, entity: T) -> Dict[str, Any]:
        """
        Convert an entity to model data.
        
        Args:
            entity: The entity to convert
            
        Returns:
            The model data
        """
        # Use model_dump or to_dict if available
        if hasattr(entity, "model_dump"):
            # Pydantic v2
            return entity.model_dump(exclude={"events", "child_entities"})
        elif hasattr(entity, "to_dict"):
            # Custom to_dict method
            return entity.to_dict()
        else:
            # Extract from __dict__, excluding private fields
            return {
                k: v
                for k, v in entity.__dict__.items()
                if not k.startswith("_")
            }
    
    def _specification_to_criteria(self, specification: Specification[T]) -> Any:
        """
        Convert a specification to SQLAlchemy criteria.
        
        Args:
            specification: The specification to convert
            
        Returns:
            SQLAlchemy criteria
        """
        # This is a stub - concrete implementations would need to handle
        # different specification types and convert them to SQLAlchemy criteria
        # For now, we raise a NotImplementedError, which will be overridden
        # by concrete implementations
        raise NotImplementedError("Specification translation must be implemented by subclasses")


class SQLAlchemyAggregateRepository(AggregateRepository[A], SQLAlchemyRepository[A, M], Generic[A, M]):
    """
    SQLAlchemy implementation of the aggregate repository.
    
    This repository extends both the aggregate repository and SQLAlchemy repository,
    providing optimized aggregate persistence with SQLAlchemy.
    """
    
    def __init__(
        self,
        aggregate_type: Type[A],
        session: AsyncSession,
        model_class: Type[M],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SQLAlchemy aggregate repository.
        
        Args:
            aggregate_type: The type of aggregate this repository manages
            session: SQLAlchemy async session
            model_class: SQLAlchemy model class
            logger: Optional logger for diagnostic output
        """
        AggregateRepository.__init__(self, aggregate_type, logger)
        SQLAlchemyRepository.__init__(self, aggregate_type, session, model_class, logger)
    
    async def add(self, aggregate: A) -> A:
        """Add a new aggregate."""
        # Collect events first
        self._collect_events(aggregate)
        
        # Delegate to SQLAlchemy implementation
        return await SQLAlchemyRepository.add(self, aggregate)
    
    async def update(self, aggregate: A) -> A:
        """Update an existing aggregate."""
        # Collect events first
        self._collect_events(aggregate)
        
        # Delegate to SQLAlchemy implementation
        return await SQLAlchemyRepository.update(self, aggregate)


class InMemoryRepository(Repository[T], Generic[T]):
    """
    In-memory implementation of the repository pattern.
    
    This repository stores entities in memory, making it useful for testing.
    """
    
    def __init__(self, entity_type: Type[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the in-memory repository.
        
        Args:
            entity_type: The type of entity this repository manages
            logger: Optional logger for diagnostic output
        """
        super().__init__(entity_type, logger)
        self.entities: Dict[Any, T] = {}
    
    async def get(self, id: Any) -> Optional[T]:
        """Get an entity by ID."""
        return self.entities.get(id)
    
    async def find(self, specification: Specification[T]) -> List[T]:
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
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """List entities with filtering and pagination."""
        entities = list(self.entities.values())
        
        # Apply filters
        if filters:
            filtered_entities = []
            for entity in entities:
                matches = True
                for field, value in filters.items():
                    if isinstance(value, dict) and "op" in value and "value" in value:
                        # Handle advanced filters with operators
                        op = value["op"]
                        val = value["value"]
                        attr_value = getattr(entity, field, None)
                        
                        if op == "eq" and attr_value != val:
                            matches = False
                        elif op == "neq" and attr_value == val:
                            matches = False
                        elif op == "gt" and (attr_value is None or attr_value <= val):
                            matches = False
                        elif op == "gte" and (attr_value is None or attr_value < val):
                            matches = False
                        elif op == "lt" and (attr_value is None or attr_value >= val):
                            matches = False
                        elif op == "lte" and (attr_value is None or attr_value > val):
                            matches = False
                        elif op == "in" and attr_value not in val:
                            matches = False
                        elif op == "like" and (attr_value is None or val.lower() not in str(attr_value).lower()):
                            matches = False
                    elif getattr(entity, field, None) != value:
                        matches = False
                        break
                if matches:
                    filtered_entities.append(entity)
            entities = filtered_entities
        
        # Apply sorting
        if order_by:
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
                
                entities.sort(key=sort_key, reverse=reverse)
        
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
        
        # Set created_at if not set
        if not entity.created_at:
            entity.created_at = datetime.now(UTC)
        
        # Clone the entity to avoid reference issues
        if hasattr(entity, "model_copy"):
            # Pydantic v2
            cloned_entity = entity.model_copy(deep=True)
        elif hasattr(entity, "copy"):
            # Custom copy method
            cloned_entity = entity.copy()
        else:
            # Try to use the constructor with the entity's data
            data = self._to_dict(entity)
            cloned_entity = self.entity_type(**data)
        
        # Add to repository
        self.entities[entity.id] = cloned_entity
        
        return cloned_entity
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        if entity.id not in self.entities:
            raise ValueError(f"Entity with ID {entity.id} not found")
        
        # Set updated_at
        entity.updated_at = datetime.now(UTC)
        
        # Check for optimistic concurrency control
        if isinstance(entity, AggregateRoot) and isinstance(self.entities[entity.id], AggregateRoot):
            existing_version = self.entities[entity.id].version
            if existing_version != entity.version - 1:
                raise ValueError(f"Concurrency conflict for entity {entity.id}")
        
        # Clone the entity to avoid reference issues
        if hasattr(entity, "model_copy"):
            # Pydantic v2
            cloned_entity = entity.model_copy(deep=True)
        elif hasattr(entity, "copy"):
            # Custom copy method
            cloned_entity = entity.copy()
        else:
            # Try to use the constructor with the entity's data
            data = self._to_dict(entity)
            cloned_entity = self.entity_type(**data)
        
        # Update in repository
        self.entities[entity.id] = cloned_entity
        
        return cloned_entity
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        await self.remove_by_id(entity.id)
    
    async def remove_by_id(self, id: Any) -> bool:
        """Remove an entity by ID."""
        if id in self.entities:
            del self.entities[id]
            return True
        return False
    
    async def exists(self, id: Any) -> bool:
        """Check if an entity exists."""
        return id in self.entities
    
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """Count entities matching a specification."""
        if specification is None:
            return len(self.entities)
        
        count = 0
        for entity in self.entities.values():
            if specification.is_satisfied_by(entity):
                count += 1
        
        return count
    
    async def count_filtered(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filter criteria."""
        if not filters:
            return len(self.entities)
        
        count = 0
        for entity in self.entities.values():
            matches = True
            for field, value in filters.items():
                if isinstance(value, dict) and "op" in value and "value" in value:
                    # Handle advanced filters with operators
                    op = value["op"]
                    val = value["value"]
                    attr_value = getattr(entity, field, None)
                    
                    if op == "eq" and attr_value != val:
                        matches = False
                    elif op == "neq" and attr_value == val:
                        matches = False
                    elif op == "gt" and (attr_value is None or attr_value <= val):
                        matches = False
                    elif op == "gte" and (attr_value is None or attr_value < val):
                        matches = False
                    elif op == "lt" and (attr_value is None or attr_value >= val):
                        matches = False
                    elif op == "lte" and (attr_value is None or attr_value > val):
                        matches = False
                    elif op == "in" and attr_value not in val:
                        matches = False
                    elif op == "like" and (attr_value is None or val.lower() not in str(attr_value).lower()):
                        matches = False
                elif getattr(entity, field, None) != value:
                    matches = False
                    break
            if matches:
                count += 1
        
        return count
    
    def _to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert an entity to a dictionary.
        
        Args:
            entity: The entity to convert
            
        Returns:
            Dictionary representation of the entity
        """
        # Use model_dump or to_dict if available
        if hasattr(entity, "model_dump"):
            # Pydantic v2
            return entity.model_dump(exclude={"events", "child_entities"})
        elif hasattr(entity, "to_dict"):
            # Custom to_dict method
            return entity.to_dict()
        else:
            # Extract from __dict__, excluding private fields
            return {
                k: v
                for k, v in entity.__dict__.items()
                if not k.startswith("_")
            }


class InMemoryAggregateRepository(AggregateRepository[A], InMemoryRepository[A], Generic[A]):
    """
    In-memory implementation of the aggregate repository.
    
    This repository extends both the aggregate repository and in-memory repository,
    providing aggregate functionality in memory for testing.
    """
    
    def __init__(self, aggregate_type: Type[A], logger: Optional[logging.Logger] = None):
        """
        Initialize the in-memory aggregate repository.
        
        Args:
            aggregate_type: The type of aggregate this repository manages
            logger: Optional logger for diagnostic output
        """
        AggregateRepository.__init__(self, aggregate_type, logger)
        InMemoryRepository.__init__(self, aggregate_type, logger)
    
    async def add(self, aggregate: A) -> A:
        """Add a new aggregate."""
        # Collect events first
        self._collect_events(aggregate)
        
        # Delegate to in-memory implementation
        return await InMemoryRepository.add(self, aggregate)
    
    async def update(self, aggregate: A) -> A:
        """Update an existing aggregate."""
        # Collect events first
        self._collect_events(aggregate)
        
        # Delegate to in-memory implementation
        return await InMemoryRepository.update(self, aggregate)
"""