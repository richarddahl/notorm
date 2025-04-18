"""
SQLAlchemy implementation of the repository pattern.

This module provides concrete repository implementations using SQLAlchemy as
the ORM layer for database access.
"""

import logging
from datetime import datetime, UTC
from typing import (
    Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, Union, cast,
    AsyncIterator, get_args, get_origin
)

from sqlalchemy import select, insert, update, delete, func, text, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import Select
from sqlalchemy.sql.expression import ColumnElement

from uno.core.base.repository import (
    BaseRepository,
    SpecificationRepository,
    BatchRepository,
    StreamingRepository,
    CompleteRepository,
    FilterType,
)
from uno.domain.base.model import BaseModel


# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
M = TypeVar("M", bound=BaseModel)  # Model type


class SQLAlchemyRepository(BaseRepository[T, ID], Generic[T, ID, M]):
    """
    SQLAlchemy implementation of the repository pattern.
    
    This repository uses SQLAlchemy for data access, supporting both ORM and Core approaches.
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
    
    async def get(self, id: ID) -> Optional[T]:
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
            raise
    
    async def list(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[T]:
        """List entities matching filter criteria."""
        try:
            # Build base query
            stmt = select(self.model_class)
            
            # Apply filters
            if filters:
                stmt = self._apply_filters(stmt, filters)
            
            # Apply ordering
            if order_by:
                stmt = self._apply_ordering(stmt, order_by)
            
            # Apply pagination
            if offset:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            
            # Execute query
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # Convert to entities
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self.logger.error(f"Error listing entities: {e}")
            raise
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        try:
            # Check if entity already exists
            entity_id = getattr(entity, "id", None)
            if entity_id and await self.exists(entity_id):
                raise ValueError(f"Entity with ID {entity_id} already exists")
            
            # Ensure created_at is set
            if hasattr(entity, "created_at") and not getattr(entity, "created_at", None):
                setattr(entity, "created_at", datetime.now(UTC))
            
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
            self.logger.error(f"Error adding entity: {e}")
            raise
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            # Get entity ID
            entity_id = getattr(entity, "id", None)
            if not entity_id:
                raise ValueError("Entity ID is required for update")
                
            # Ensure entity exists
            if not await self.exists(entity_id):
                raise ValueError(f"Entity with ID {entity_id} not found")
            
            # Set updated_at if supported
            if hasattr(entity, "updated_at"):
                setattr(entity, "updated_at", datetime.now(UTC))
            
            # Convert entity to model data
            data = self._to_model_data(entity)
            
            # Check for optimistic concurrency control
            if hasattr(entity, "version"):
                # Use version for optimistic concurrency control
                stmt = select(self.model_class).where(
                    self.model_class.id == entity_id,
                    self.model_class.version == entity.version - 1
                )
                result = await self.session.execute(stmt)
                model = result.scalars().first()
                
                if model is None:
                    raise ValueError(f"Concurrency conflict for entity {entity_id}")
                
                # Update model attributes
                for key, value in data.items():
                    setattr(model, key, value)
                
                await self.session.flush()
                return self._to_entity(model)
            else:
                # Regular entity without versioning
                stmt = select(self.model_class).where(self.model_class.id == entity_id)
                result = await self.session.execute(stmt)
                model = result.scalars().first()
                
                if model is None:
                    raise ValueError(f"Entity with ID {entity_id} not found")
                
                # Update model attributes
                for key, value in data.items():
                    setattr(model, key, value)
                
                await self.session.flush()
                return self._to_entity(model)
        except Exception as e:
            self.logger.error(f"Error updating entity: {e}")
            raise
    
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        try:
            # Get entity ID
            entity_id = getattr(entity, "id", None)
            if not entity_id:
                raise ValueError("Entity ID is required for delete")
                
            # Find the entity
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            
            if model is None:
                raise ValueError(f"Entity with ID {entity_id} not found")
            
            # Delete the entity
            await self.session.delete(model)
            await self.session.flush()
        except Exception as e:
            self.logger.error(f"Error deleting entity: {e}")
            raise
    
    async def exists(self, id: ID) -> bool:
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
            raise
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        try:
            result = await self.session.execute(text(query), params or {})
            return [dict(row._mapping) for row in result.all()]
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
    
    async def execute_statement(self, statement: Select) -> List[Any]:
        """Execute a SQLAlchemy statement."""
        try:
            result = await self.session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Error executing statement: {e}")
            raise
    
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
                if not k.startswith("_") and k != "_sa_instance_state"
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
    
    def _apply_filters(self, stmt: Select, filters: FilterType) -> Select:
        """
        Apply filters to a query.
        
        Args:
            stmt: The query statement
            filters: Filter criteria
            
        Returns:
            Updated query statement
        """
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
                elif op == "ilike":
                    stmt = stmt.where(getattr(self.model_class, field).ilike(f"%{val}%"))
                elif op == "is_null":
                    stmt = stmt.where(getattr(self.model_class, field).is_(None))
                elif op == "not_null":
                    stmt = stmt.where(getattr(self.model_class, field).is_not(None))
            else:
                # Simple equality filter
                stmt = stmt.where(getattr(self.model_class, field) == value)
        
        return stmt
    
    def _apply_ordering(self, stmt: Select, order_by: List[str]) -> Select:
        """
        Apply ordering to a query.
        
        Args:
            stmt: The query statement
            order_by: Ordering fields
            
        Returns:
            Updated query statement
        """
        for field in order_by:
            if field.startswith("-"):
                # Descending order
                stmt = stmt.order_by(getattr(self.model_class, field[1:]).desc())
            else:
                # Ascending order
                stmt = stmt.order_by(getattr(self.model_class, field).asc())
        
        return stmt


class SQLAlchemySpecificationRepository(
    SQLAlchemyRepository[T, ID, M],
    SpecificationRepository[T, ID],
    Generic[T, ID, M]
):
    """
    SQLAlchemy repository with specification pattern support.
    
    Extends the base SQLAlchemy repository with support for the specification pattern.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        session: AsyncSession,
        model_class: Type[M],
        logger: Optional[logging.Logger] = None,
        specification_translator: Optional[Any] = None,
    ):
        """
        Initialize the SQLAlchemy specification repository.
        
        Args:
            entity_type: The type of entity this repository manages
            session: SQLAlchemy async session
            model_class: SQLAlchemy model class
            logger: Optional logger for diagnostic output
            specification_translator: Optional translator for specifications
        """
        super().__init__(entity_type, session, model_class, logger)
        self.specification_translator = specification_translator
    
    async def find(self, specification: Any) -> List[T]:
        """Find entities matching a specification."""
        try:
            # Convert specification to SQLAlchemy criteria
            criteria = self._specification_to_criteria(specification)
            
            # Build and execute query
            stmt = select(self.model_class)
            if criteria is not None:
                stmt = stmt.where(criteria)
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # Convert to entities
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self.logger.error(f"Error finding entities: {e}")
            raise
    
    async def find_one(self, specification: Any) -> Optional[T]:
        """Find a single entity matching a specification."""
        try:
            # Convert specification to SQLAlchemy criteria
            criteria = self._specification_to_criteria(specification)
            
            # Build and execute query
            stmt = select(self.model_class)
            if criteria is not None:
                stmt = stmt.where(criteria)
            
            # Limit to one result
            stmt = stmt.limit(1)
            
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            
            if model is None:
                return None
            
            # Convert to entity
            return self._to_entity(model)
        except Exception as e:
            self.logger.error(f"Error finding entity: {e}")
            raise
    
    async def count(self, specification: Optional[Any] = None) -> int:
        """Count entities matching a specification."""
        try:
            # Build base query
            stmt = select(func.count()).select_from(self.model_class)
            
            # Apply specification if provided
            if specification is not None:
                criteria = self._specification_to_criteria(specification)
                if criteria is not None:
                    stmt = stmt.where(criteria)
            
            # Execute query
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            return count or 0
        except Exception as e:
            self.logger.error(f"Error counting entities: {e}")
            raise
    
    def _specification_to_criteria(self, specification: Any) -> Optional[ColumnElement]:
        """
        Convert a specification to SQLAlchemy criteria.
        
        This method delegates to a specification translator if provided,
        otherwise it uses the specification directly if it provides a
        to_sqlalchemy_criteria method.
        
        Args:
            specification: The specification to convert
            
        Returns:
            SQLAlchemy criteria or None
        """
        # If we have a specification translator, use it
        if self.specification_translator:
            if hasattr(self.specification_translator, "translate"):
                return self.specification_translator.translate(specification)
            else:
                self.logger.warning("Specification translator does not implement translate method")
        
        # If the specification has a to_sqlalchemy_criteria method, use it
        if hasattr(specification, "to_sqlalchemy_criteria"):
            return specification.to_sqlalchemy_criteria(self.model_class)
        
        # Log a warning if we can't translate
        self.logger.warning(
            f"Unable to translate specification of type {type(specification).__name__} to SQLAlchemy criteria. "
            "Please provide a specification translator or use specifications with to_sqlalchemy_criteria method."
        )
        
        # Return None, which will result in no filtering
        return None


class SQLAlchemyBatchRepository(
    SQLAlchemyRepository[T, ID, M],
    BatchRepository[T, ID],
    Generic[T, ID, M]
):
    """
    SQLAlchemy repository with batch operation support.
    
    Extends the base SQLAlchemy repository with support for batch operations.
    """
    
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """Add multiple entities."""
        try:
            # Convert entities to models and add to session
            models = []
            for entity in entities:
                # Ensure created_at is set
                if hasattr(entity, "created_at") and not getattr(entity, "created_at", None):
                    setattr(entity, "created_at", datetime.now(UTC))
                
                # Convert entity to model data
                data = self._to_model_data(entity)
                
                # Create model instance
                model = self.model_class(**data)
                models.append(model)
                
                # Add to session
                self.session.add(model)
            
            # Flush to database
            await self.session.flush()
            
            # Convert back to entities
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self.logger.error(f"Error adding entities: {e}")
            raise
    
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """Update multiple entities."""
        try:
            # Get entity IDs
            entity_list = list(entities)
            entity_ids = [getattr(entity, "id", None) for entity in entity_list]
            
            # Check for None IDs
            if None in entity_ids:
                raise ValueError("All entities must have an ID for batch update")
            
            # Load existing models
            stmt = select(self.model_class).where(self.model_class.id.in_(entity_ids))
            result = await self.session.execute(stmt)
            existing_models = {model.id: model for model in result.scalars().all()}
            
            # Check for missing entities
            missing_ids = set(entity_ids) - set(existing_models.keys())
            if missing_ids:
                raise ValueError(f"Entities with IDs {missing_ids} not found")
            
            # Update models
            updated_models = []
            for entity in entity_list:
                entity_id = getattr(entity, "id")
                model = existing_models[entity_id]
                
                # Set updated_at if supported
                if hasattr(entity, "updated_at"):
                    setattr(entity, "updated_at", datetime.now(UTC))
                
                # Check for optimistic concurrency
                if hasattr(entity, "version") and hasattr(model, "version"):
                    if model.version != entity.version - 1:
                        raise ValueError(f"Concurrency conflict for entity {entity_id}")
                
                # Update model with entity data
                data = self._to_model_data(entity)
                for key, value in data.items():
                    setattr(model, key, value)
                
                updated_models.append(model)
            
            # Flush changes
            await self.session.flush()
            
            # Convert back to entities
            return [self._to_entity(model) for model in updated_models]
        except Exception as e:
            self.logger.error(f"Error updating entities: {e}")
            raise
    
    async def delete_many(self, entities: Iterable[T]) -> None:
        """Delete multiple entities."""
        try:
            # Get entity IDs
            entity_ids = [getattr(entity, "id", None) for entity in entities]
            
            # Check for None IDs
            if None in entity_ids:
                raise ValueError("All entities must have an ID for batch delete")
            
            # Delete by IDs
            await self.delete_by_ids(entity_ids)
        except Exception as e:
            self.logger.error(f"Error deleting entities: {e}")
            raise
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """Delete entities by their IDs."""
        try:
            # Convert to list to avoid multiple iterations
            id_list = list(ids)
            if not id_list:
                return 0
            
            # Delete entities
            stmt = delete(self.model_class).where(self.model_class.id.in_(id_list))
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            # Return number of deleted rows
            return result.rowcount
        except Exception as e:
            self.logger.error(f"Error deleting entities by IDs: {e}")
            raise


class SQLAlchemyStreamingRepository(
    SQLAlchemyRepository[T, ID, M],
    StreamingRepository[T, ID],
    Generic[T, ID, M]
):
    """
    SQLAlchemy repository with streaming support.
    
    Extends the base SQLAlchemy repository with support for streaming large result sets.
    """
    
    async def stream(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """Stream entities matching filter criteria."""
        try:
            # Build base query
            stmt = select(self.model_class)
            
            # Apply filters
            if filters:
                stmt = self._apply_filters(stmt, filters)
            
            # Apply ordering
            if order_by:
                stmt = self._apply_ordering(stmt, order_by)
            
            # Get total count for progress tracking
            count_stmt = select(func.count()).select_from(self.model_class)
            if filters:
                count_stmt = self._apply_filters(count_stmt, filters)
            
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # Stream entities in batches
            offset = 0
            while True:
                # Apply pagination for current batch
                batch_stmt = stmt.limit(batch_size).offset(offset)
                result = await self.session.execute(batch_stmt)
                models = result.scalars().all()
                
                # Stop if no more results
                if not models:
                    break
                
                # Yield entities one by one
                for model in models:
                    yield self._to_entity(model)
                
                # Move to next batch
                offset += batch_size
                
                # Stop if we've processed all entities
                if offset >= total_count:
                    break
        except Exception as e:
            self.logger.error(f"Error streaming entities: {e}")
            raise


class SQLAlchemyCompleteRepository(
    SQLAlchemySpecificationRepository[T, ID, M],
    SQLAlchemyBatchRepository[T, ID, M],
    SQLAlchemyStreamingRepository[T, ID, M],
    Generic[T, ID, M]
):
    """
    Complete SQLAlchemy repository with all capabilities.
    
    This class combines all SQLAlchemy repository features into a single implementation.
    Use this when you need a repository with all capabilities.
    """
    pass