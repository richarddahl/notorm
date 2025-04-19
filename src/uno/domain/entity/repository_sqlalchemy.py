"""
SQLAlchemy repository implementation for domain entities.

This module provides a SQLAlchemy-based implementation of the EntityRepository
interface for persisting and retrieving domain entities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, AsyncIterator, cast, Callable

from sqlalchemy import select, delete, update, insert, func, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select, Delete, Update

from uno.core.errors.result import Result, Success, Failure
from uno.domain.entity.base import EntityBase
from uno.domain.entity.specification.base import Specification, AttributeSpecification
from uno.domain.entity.specification.composite import (
    AndSpecification, OrSpecification, NotSpecification,
    AllSpecification, AnySpecification
)
from uno.domain.entity.repository import EntityRepository

# Type variables
T = TypeVar("T", bound=EntityBase)  # Entity type
ID = TypeVar("ID")  # ID type
M = TypeVar("M")  # Database model type


class EntityMapper(Generic[T, M]):
    """
    Maps between domain entities and database models.
    
    This class is responsible for converting between domain entities and
    the database model objects used by SQLAlchemy.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        model_type: Type[M],
        to_entity: Callable[[M], T],
        to_model: Callable[[T], M]
    ):
        """
        Initialize the mapper.
        
        Args:
            entity_type: The domain entity type
            model_type: The SQLAlchemy model type
            to_entity: Function to convert model to entity
            to_model: Function to convert entity to model
        """
        self.entity_type = entity_type
        self.model_type = model_type
        self.to_entity = to_entity
        self.to_model = to_model


class SQLAlchemyRepository(EntityRepository[T, ID], Generic[T, ID, M]):
    """
    SQLAlchemy-based repository implementation for domain entities.
    
    This class provides an implementation of the EntityRepository interface
    that uses SQLAlchemy for database access.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        mapper: EntityMapper[T, M],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            session: SQLAlchemy async session
            mapper: Entity-model mapper
            logger: Optional logger for diagnostic output
        """
        super().__init__(mapper.entity_type, logger)
        self.session = session
        self.mapper = mapper
    
    async def get(self, id: ID) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        stmt = select(self.mapper.model_type).where(self.mapper.model_type.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_entity(model)
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[T]:
        """
        List entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination
            
        Returns:
            List of entities matching criteria
        """
        stmt = select(self.mapper.model_type)
        
        # Apply filters if provided
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.mapper.model_type, key):
                    conditions.append(getattr(self.mapper.model_type, key) == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
        
        # Apply ordering if provided
        if order_by:
            for field in order_by:
                direction = "asc"
                if field.startswith('-'):
                    field = field[1:]
                    direction = "desc"
                
                if hasattr(self.mapper.model_type, field):
                    order_attr = getattr(self.mapper.model_type, field)
                    if direction == "desc":
                        order_attr = order_attr.desc()
                    stmt = stmt.order_by(order_attr)
        
        # Apply pagination
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        
        # Execute query
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        # Convert to entities
        return [self.mapper.to_entity(model) for model in models]
    
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity with any generated values
        """
        # Set created/updated timestamps if not set
        now = datetime.now()
        if not entity.created_at:
            entity.created_at = now
        if not entity.updated_at:
            entity.updated_at = now
        
        # Convert to model
        model = self.mapper.to_model(entity)
        
        # Add to session
        self.session.add(model)
        await self.session.flush()
        
        # Convert back to entity with generated values
        return self.mapper.to_entity(model)
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        # Update timestamp
        entity.updated_at = datetime.now()
        
        # Convert to model
        model = self.mapper.to_model(entity)
        
        # Update in session
        self.session.add(model)
        await self.session.flush()
        
        # Convert back to entity
        return self.mapper.to_entity(model)
    
    async def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
        """
        # Convert to model
        model = self.mapper.to_model(entity)
        
        # Delete from session
        await self.session.delete(model)
        await self.session.flush()
    
    async def exists(self, id: ID) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        stmt = select(func.count()).select_from(self.mapper.model_type).where(self.mapper.model_type.id == id)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0
    
    async def find(self, specification: Specification[T]) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            List of entities matching the specification
        """
        # Convert specification to SQLAlchemy where clause
        stmt = select(self.mapper.model_type)
        where_clause = self._specification_to_where_clause(specification)
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        
        # Execute query
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        # Convert to entities
        entities = [self.mapper.to_entity(model) for model in models]
        
        # Apply any non-translatable specifications in-memory
        if self._needs_in_memory_filtering(specification):
            entities = [e for e in entities if specification.is_satisfied_by(e)]
        
        return entities
    
    async def find_one(self, specification: Specification[T]) -> Optional[T]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            The first entity matching the specification, or None if none found
        """
        # Convert specification to SQLAlchemy where clause
        stmt = select(self.mapper.model_type)
        where_clause = self._specification_to_where_clause(specification)
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        
        # Limit to one result
        stmt = stmt.limit(1)
        
        # Execute query
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        # Convert to entity
        entity = self.mapper.to_entity(model)
        
        # Check if it actually satisfies the specification
        if not specification.is_satisfied_by(entity):
            return None
        
        return entity
    
    async def count(self, specification: Optional[Specification[T]] = None) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: Optional specification to match against
            
        Returns:
            Number of entities matching the specification
        """
        stmt = select(func.count()).select_from(self.mapper.model_type)
        
        if specification:
            where_clause = self._specification_to_where_clause(specification)
            if where_clause is not None:
                stmt = stmt.where(where_clause)
        
        # Execute query
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        
        # If specification needs in-memory filtering, we need to do a full query
        if specification and self._needs_in_memory_filtering(specification):
            entities = await self.find(specification)
            return len(entities)
        
        return count
    
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """
        Add multiple entities.
        
        Args:
            entities: Iterable of entities to add
            
        Returns:
            List of added entities with any generated values
        """
        now = datetime.now()
        models = []
        
        for entity in entities:
            # Set created/updated timestamps if not set
            if not entity.created_at:
                entity.created_at = now
            if not entity.updated_at:
                entity.updated_at = now
            
            # Convert to model
            model = self.mapper.to_model(entity)
            models.append(model)
        
        # Add all to session
        self.session.add_all(models)
        await self.session.flush()
        
        # Convert back to entities with generated values
        return [self.mapper.to_entity(model) for model in models]
    
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """
        Update multiple entities.
        
        Args:
            entities: Iterable of entities to update
            
        Returns:
            List of updated entities
        """
        now = datetime.now()
        models = []
        
        for entity in entities:
            # Update timestamp
            entity.updated_at = now
            
            # Convert to model
            model = self.mapper.to_model(entity)
            models.append(model)
        
        # Update all in session
        self.session.add_all(models)
        await self.session.flush()
        
        # Convert back to entities
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete_many(self, entities: Iterable[T]) -> None:
        """
        Delete multiple entities.
        
        Args:
            entities: Iterable of entities to delete
        """
        for entity in entities:
            # Convert to model
            model = self.mapper.to_model(entity)
            
            # Delete from session
            await self.session.delete(model)
        
        await self.session.flush()
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """
        Delete entities by their IDs.
        
        Args:
            ids: Iterable of entity IDs to delete
            
        Returns:
            Number of entities deleted
        """
        # Convert to list for multiple use
        id_list = list(ids)
        
        # Check how many entities exist
        stmt = select(func.count()).select_from(self.mapper.model_type).where(self.mapper.model_type.id.in_(id_list))
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        
        # Delete entities
        stmt = delete(self.mapper.model_type).where(self.mapper.model_type.id.in_(id_list))
        await self.session.execute(stmt)
        
        return count
    
    async def stream(
        self,
        specification: Optional[Specification[T]] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """
        Stream entities matching a specification.
        
        Args:
            specification: Optional specification to match against
            order_by: Optional list of fields to order by
            batch_size: Size of batches to fetch
            
        Returns:
            Async iterator of entities matching the specification
        """
        # Start with 0 offset
        offset = 0
        
        while True:
            # Build query for current batch
            stmt = select(self.mapper.model_type)
            
            # Apply specification if provided
            if specification:
                where_clause = self._specification_to_where_clause(specification)
                if where_clause is not None:
                    stmt = stmt.where(where_clause)
            
            # Apply ordering if provided
            if order_by:
                for field in order_by:
                    direction = "asc"
                    if field.startswith('-'):
                        field = field[1:]
                        direction = "desc"
                    
                    if hasattr(self.mapper.model_type, field):
                        order_attr = getattr(self.mapper.model_type, field)
                        if direction == "desc":
                            order_attr = order_attr.desc()
                        stmt = stmt.order_by(order_attr)
            
            # Apply pagination for current batch
            stmt = stmt.offset(offset).limit(batch_size)
            
            # Execute query
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # If no models returned, we're done
            if not models:
                break
            
            # Convert to entities
            entities = [self.mapper.to_entity(model) for model in models]
            
            # Apply in-memory filtering if needed
            if specification and self._needs_in_memory_filtering(specification):
                entities = [e for e in entities if specification.is_satisfied_by(e)]
            
            # Yield entities one by one
            for entity in entities:
                yield entity
            
            # Update offset for next batch
            offset += batch_size
    
    def _specification_to_where_clause(self, specification: Specification[T]) -> Optional[Any]:
        """
        Convert a specification to a SQLAlchemy where clause.
        
        Args:
            specification: The specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        if isinstance(specification, AttributeSpecification):
            return self._attribute_specification_to_where_clause(specification)
        elif isinstance(specification, AndSpecification):
            return self._and_specification_to_where_clause(specification)
        elif isinstance(specification, OrSpecification):
            return self._or_specification_to_where_clause(specification)
        elif isinstance(specification, NotSpecification):
            return self._not_specification_to_where_clause(specification)
        elif isinstance(specification, AllSpecification):
            return self._all_specification_to_where_clause(specification)
        elif isinstance(specification, AnySpecification):
            return self._any_specification_to_where_clause(specification)
        
        # If we don't know how to translate this specification, return None
        # This will cause _needs_in_memory_filtering to return True
        return None
    
    def _attribute_specification_to_where_clause(self, specification: AttributeSpecification[T]) -> Optional[Any]:
        """
        Convert an attribute specification to a SQLAlchemy where clause.
        
        Args:
            specification: The attribute specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        if not hasattr(self.mapper.model_type, specification.attribute_name):
            return None
        
        attr = getattr(self.mapper.model_type, specification.attribute_name)
        
        # If we have a custom comparator, we need special handling
        if specification.comparator.__name__ != 'eq':
            if specification.comparator.__name__ == 'lt':
                return attr < specification.expected_value
            elif specification.comparator.__name__ == 'lte':
                return attr <= specification.expected_value
            elif specification.comparator.__name__ == 'gt':
                return attr > specification.expected_value
            elif specification.comparator.__name__ == 'gte':
                return attr >= specification.expected_value
            elif specification.comparator.__name__ == 'contains':
                return attr.contains(specification.expected_value)
            elif specification.comparator.__name__ == 'startswith':
                return attr.startswith(specification.expected_value)
            elif specification.comparator.__name__ == 'endswith':
                return attr.endswith(specification.expected_value)
            
            # If we don't know how to translate this comparator, return None
            return None
        
        # Default to equality
        return attr == specification.expected_value
    
    def _and_specification_to_where_clause(self, specification: AndSpecification[T]) -> Optional[Any]:
        """
        Convert an AND specification to a SQLAlchemy where clause.
        
        Args:
            specification: The AND specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        left = self._specification_to_where_clause(specification.left)
        right = self._specification_to_where_clause(specification.right)
        
        # If either side is not translatable, we can't translate the AND
        if left is None or right is None:
            return None
        
        return and_(left, right)
    
    def _or_specification_to_where_clause(self, specification: OrSpecification[T]) -> Optional[Any]:
        """
        Convert an OR specification to a SQLAlchemy where clause.
        
        Args:
            specification: The OR specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        left = self._specification_to_where_clause(specification.left)
        right = self._specification_to_where_clause(specification.right)
        
        # If either side is not translatable, we can't translate the OR
        if left is None or right is None:
            return None
        
        return or_(left, right)
    
    def _not_specification_to_where_clause(self, specification: NotSpecification[T]) -> Optional[Any]:
        """
        Convert a NOT specification to a SQLAlchemy where clause.
        
        Args:
            specification: The NOT specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        inner = self._specification_to_where_clause(specification.specification)
        
        # If inner is not translatable, we can't translate the NOT
        if inner is None:
            return None
        
        return not_(inner)
    
    def _all_specification_to_where_clause(self, specification: AllSpecification[T]) -> Optional[Any]:
        """
        Convert an ALL specification to a SQLAlchemy where clause.
        
        Args:
            specification: The ALL specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        clauses = []
        
        for spec in specification.specifications:
            clause = self._specification_to_where_clause(spec)
            if clause is None:
                # If any specification is not translatable, we can't translate the ALL
                return None
            clauses.append(clause)
        
        if not clauses:
            # Empty ALL is always true
            return True
        
        return and_(*clauses)
    
    def _any_specification_to_where_clause(self, specification: AnySpecification[T]) -> Optional[Any]:
        """
        Convert an ANY specification to a SQLAlchemy where clause.
        
        Args:
            specification: The ANY specification to convert
            
        Returns:
            SQLAlchemy expression or None if not translatable
        """
        clauses = []
        
        for spec in specification.specifications:
            clause = self._specification_to_where_clause(spec)
            if clause is None:
                # If any specification is not translatable, we can't translate the ANY
                return None
            clauses.append(clause)
        
        if not clauses:
            # Empty ANY is always false
            return False
        
        return or_(*clauses)
    
    def _needs_in_memory_filtering(self, specification: Specification[T]) -> bool:
        """
        Check if a specification needs in-memory filtering.
        
        Args:
            specification: The specification to check
            
        Returns:
            True if in-memory filtering is needed, False otherwise
        """
        # If we can't translate to a where clause, we need in-memory filtering
        return self._specification_to_where_clause(specification) is None