"""
SQLAlchemy repository implementation for domain entities.

This module provides a SQLAlchemy-based implementation of the EntityRepository
interface for persisting and retrieving domain entities.
"""

from collections.abc import AsyncIterator, Callable, Iterable
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, delete, func, not_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.entity import ID
from uno.core.errors.result import Failure, Result, Success
from uno.domain.entity.base import EntityBase
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.specification.base import AttributeSpecification, Specification
from uno.domain.entity.specification.composite import (
    AllSpecification,
    AndSpecification,
    AnySpecification,
    NotSpecification,
    OrSpecification,
)

# Type variables
T = TypeVar("T", bound=EntityBase)  # Entity type
M = TypeVar("M")  # Database model type


class EntityMapper(Generic[T, M]):
    """
    Maps between domain entities and database models.
    
    This class is responsible for converting between domain entities and
    the database model objects used by SQLAlchemy.
    """
    
    def __init__(
        self,
        entity_type: type[T],
        model_type: type[M],
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


class SQLAlchemyRepository(EntityRepository[T], Generic[T, M]):
    """
    SQLAlchemy-based repository implementation for domain entities.
    
    This class provides an implementation of the EntityRepository interface
    that uses SQLAlchemy for database access.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        mapper: EntityMapper[T, M],
        optional_fields: list[str] | None = None
    ):
        """
        Initialize the repository.
        
        Args:
            session: SQLAlchemy async session
            mapper: Entity-model mapper
            optional_fields: Optional list of fields that can be None
        """
        super().__init__(mapper.entity_type, optional_fields)
        self.session = session
        self.mapper = mapper
    
    async def get(self, id: ID) -> Result[T | None, str]:
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Result containing the entity if found or None, or a Failure with error message
        """
        try:
            stmt = select(self.mapper.model_type).where(self.mapper.model_type.id == id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model is None:
                return Success[T | None, str](None, convert=True)
            
            return Success[T | None, str](self.mapper.to_entity(model), convert=True)
        except SQLAlchemyError as e:
            return Failure[T | None, str](f"Database error retrieving entity with ID {id}: {str(e)}", convert=True)
        except Exception as e:
            return Failure[T | None, str](f"Error retrieving entity with ID {id}: {str(e)}", convert=True)
    
    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = 0,
    ) -> Result[list[T], str]:
        """
        List entities matching filter criteria.
        
        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination
            
        Returns:
            Result containing list of entities matching criteria or an error message
        """
        try:
            stmt = select(self.mapper.model_type)
            
            # Apply filters if provided
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.mapper.model_type, key):
                        field = getattr(self.mapper.model_type, key)
                        conditions.append(field == value)
                
                if conditions:
                    stmt = stmt.where(*conditions)
            
            # Apply ordering if provided
            if order_by:
                order_clauses = []
                for sort_item in order_by:
                    desc = False
                    field_name = sort_item
                    if sort_item.startswith("-"):
                        desc = True
                        field_name = sort_item[1:]
                    
                    if hasattr(self.mapper.model_type, field_name):
                        field_attr = getattr(self.mapper.model_type, field_name)
                        if desc:
                            field_attr = field_attr.desc()
                        order_clauses.append(field_attr)
                
                if order_clauses:
                    stmt = stmt.order_by(*order_clauses)
            
            # Apply pagination
            if limit is not None:
                stmt = stmt.limit(limit)
            
            if offset is not None:
                stmt = stmt.offset(offset)
            
            # Execute query
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # Convert models to entities
            entities = [self.mapper.to_entity(model) for model in models]
            return Success[list[T], str](entities, convert=True)
        except SQLAlchemyError as e:
            return Failure[list[T], str](f"Database error listing entities: {str(e)}", convert=True)
        except Exception as e:
            return Failure[list[T], str](f"Error listing entities: {str(e)}", convert=True)
    
    async def add(self, entity: T) -> Result[T, str]:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            Result containing the added entity with any generated values or an error message
        """
        try:
            if entity.id is not None:
                exists_result = await self.exists(entity.id)
                if exists_result.is_success() and exists_result.value() is True:
                    return Failure[T, str](f"Entity with ID {entity.id} already exists", convert=True)
                
            model = self.mapper.to_model(entity)
            
            self.session.add(model)
            await self.session.flush()
            
            # Get the fully populated model with any generated values
            await self.session.refresh(model)
            
            # Convert back to an entity and return
            return Success[T, str](self.mapper.to_entity(model), convert=True)
        except SQLAlchemyError as e:
            return Failure[T, str](f"Database error adding entity: {str(e)}", convert=True)
        except Exception as e:
            return Failure[T, str](f"Error adding entity: {str(e)}", convert=True)
    
    async def update(self, entity: T) -> Result[T, str]:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            Result containing the updated entity or an error message
        """
        try:
            exists_result = await self.exists(entity.id)
            if exists_result.is_failure():
                return Failure[T, str](f"Error checking entity existence: {exists_result.error()}", convert=True)
                
            if not exists_result.value():
                return Failure[T, str](f"Entity with ID {entity.id} does not exist", convert=True)
                
            model = self.mapper.to_model(entity)
            self.session.add(model)
            await self.session.flush()
            
            # Convert back to an entity and return
            return Success[T, str](self.mapper.to_entity(model), convert=True)
        except SQLAlchemyError as e:
            return Failure[T, str](f"Database error updating entity: {str(e)}", convert=True)
        except Exception as e:
            return Failure[T, str](f"Error updating entity: {str(e)}", convert=True)
    
    async def delete(self, entity: T) -> Result[bool, str]:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
            
        Returns:
            Result indicating success (True) or failure with an error message
        """
        try:
            model = self.mapper.to_model(entity)
            await self.session.delete(model)
            await self.session.flush()
            return Success[bool, str](True, convert=True)
        except SQLAlchemyError as e:
            return Failure[bool, str](f"Database error deleting entity: {str(e)}", convert=True)
        except Exception as e:
            return Failure[bool, str](f"Error deleting entity: {str(e)}", convert=True)
    
    async def exists(self, id: ID) -> Result[bool, str]:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: Entity ID
            
        Returns:
            Result containing True if exists, False otherwise, or an error message
        """
        try:
            stmt = select(func.count()).select_from(self.mapper.model_type).where(self.mapper.model_type.id == id)
            result = await self.session.execute(stmt)
            count = result.scalar_one()
            return Success[bool, str](count > 0, convert=True)
        except SQLAlchemyError as e:
            return Failure[bool, str](f"Database error checking entity existence: {str(e)}", convert=True)
        except Exception as e:
            return Failure[bool, str](f"Error checking entity existence: {str(e)}", convert=True)
    
    async def find(self, specification: Specification[T]) -> Result[list[T], str]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            Result containing a list of entities matching the specification or an error message
        """
        try:
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
            
            return Success[list[T], str](entities, convert=True)
        except SQLAlchemyError as e:
            return Failure[list[T], str](f"Database error finding entities: {str(e)}", convert=True)
        except Exception as e:
            return Failure[list[T], str](f"Error finding entities: {str(e)}", convert=True)
    
    async def find_one(self, specification: Specification[T]) -> Result[T | None, str]:
        """
        Find a single entity matching a specification.
        
        Args:
            specification: The specification to match against
            
        Returns:
            Result containing the first entity matching the specification, or None if none found, or an error message
        """
        try:
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
                return Success[T | None, str](None, convert=True)
            
            # Convert to entity
            entity = self.mapper.to_entity(model)
            
            # Check if it actually satisfies the specification
            if not specification.is_satisfied_by(entity):
                return Success[T | None, str](None, convert=True)
            
            return Success[T | None, str](entity, convert=True)
        except SQLAlchemyError as e:
            return Failure[T | None, str](f"Database error finding entity: {str(e)}", convert=True)
        except Exception as e:
            return Failure[T | None, str](f"Error finding entity: {str(e)}", convert=True)
    
    async def count(self, specification: Specification[T] | None = None) -> Result[int, str]:
        """
        Count entities matching a specification.
        
        Args:
            specification: Optional specification to match against
            
        Returns:
            Result containing the number of entities matching the specification or an error message
        """
        try:
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
                entities_result = await self.find(specification)
                if entities_result.is_failure():
                    return Failure[int, str](f"Error counting entities: {entities_result.error()}", convert=True)
                return Success[int, str](len(entities_result.value()), convert=True)
            
            return Success[int, str](count, convert=True)
        except SQLAlchemyError as e:
            return Failure[int, str](f"Database error counting entities: {str(e)}", convert=True)
        except Exception as e:
            return Failure[int, str](f"Error counting entities: {str(e)}", convert=True)
    
    async def add_many(self, entities: list[T]) -> Result[list[T], str]:
        """
        Add multiple entities.
        
        Args:
            entities: Iterable of entities to add
            
        Returns:
            Result containing a list of added entities with any generated values or an error message
        """
        try:
            added_entities = []
            for entity in entities:
                result = await self.add(entity)
                if result.is_failure():
                    return Failure[list[T], str](f"Error adding entity: {result.error()}", convert=True)
                added_entities.append(result.value())
            
            return Success[list[T], str](added_entities, convert=True)
        except SQLAlchemyError as e:
            return Failure[list[T], str](f"Database error adding entities: {str(e)}", convert=True)
        except Exception as e:
            return Failure[list[T], str](f"Error adding entities: {str(e)}", convert=True)
    
    async def update_many(self, entities: Iterable[T]) -> Result[list[T], str]:
        """
        Update multiple entities.
        
        Args:
            entities: Iterable of entities to update
            
        Returns:
            Result containing a list of updated entities or an error message
        """
        try:
            updated_entities = []
            for entity in entities:
                result = await self.update(entity)
                if result.is_failure():
                    return Failure[list[T], str](f"Error updating entity: {result.error()}", convert=True)
                updated_entities.append(result.value())
            
            return Success[list[T], str](updated_entities, convert=True)
        except SQLAlchemyError as e:
            return Failure[list[T], str](f"Database error updating entities: {str(e)}", convert=True)
        except Exception as e:
            return Failure[list[T], str](f"Error updating entities: {str(e)}", convert=True)
    
    async def delete_many(self, entities: Iterable[T]) -> Result[bool, str]:
        """
        Delete multiple entities.
        
        Args:
            entities: Iterable of entities to delete
            
        Returns:
            Result indicating success (True) or failure with an error message
        """
        try:
            for entity in entities:
                result = await self.delete(entity)
                if result.is_failure():
                    return Failure[bool, str](f"Error deleting entity: {result.error()}", convert=True)
            
            return Success[bool, str](True, convert=True)
        except SQLAlchemyError as e:
            return Failure[bool, str](f"Database error deleting entities: {str(e)}", convert=True)
        except Exception as e:
            return Failure[bool, str](f"Error deleting entities: {str(e)}", convert=True)
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> Result[int, str]:
        """
        Delete entities by their IDs.
        
        Args:
            ids: Iterable of entity IDs to delete
            
        Returns:
            Result containing the number of entities deleted or an error message
        """
        try:
            # Convert to list for multiple use
            id_list = list(ids)
            
            # Use a DELETE statement for better performance
            stmt = delete(self.mapper.model_type).where(self.mapper.model_type.id.in_(id_list))
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            # Get number of rows deleted
            return Success[int, str](result.rowcount, convert=True)
        except SQLAlchemyError as e:
            return Failure[int, str](f"Database error deleting entities by IDs: {str(e)}")
        except Exception as e:
            return Failure[int, str](f"Error deleting entities by IDs: {str(e)}")
            
    def _build_query_for_stream(self, specification: Specification[T] | None = None, order_by: list[str] | None = None, batch_size: int = 100) -> Any:
        """Build a query for streaming entities."""
        # Start with a basic select statement
        stmt = select(self.mapper.model_type)
        
        # Apply specification if provided
        if specification is not None:
            where_clause = self._specification_to_where_clause(specification)
            if where_clause is not None:
                stmt = stmt.where(where_clause)
        
        # Apply ordering if provided
        if order_by:
            for sort_field in order_by:
                direction = "asc"
                field_name = sort_field
                if sort_field.startswith('-'):
                    field_name = sort_field[1:]
                    direction = "desc"
                    
                if hasattr(self.mapper.model_type, field_name):
                    order_attr = getattr(self.mapper.model_type, field_name)
                    if direction == "desc":
                        order_attr = order_attr.desc()
                    stmt = stmt.order_by(order_attr)
        
        # Add limit and return
        stmt = stmt.limit(batch_size)
        return stmt
    
    async def stream(
        self,
        specification: Specification[T] | None = None,
        order_by: list[str] | None = None,
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
                for sort_field in order_by:
                    direction = "asc"
                    field_name = sort_field
                    if sort_field.startswith('-'):
                        field_name = sort_field[1:]
                        direction = "desc"
                        
                    if hasattr(self.mapper.model_type, field_name):
                        order_attr = getattr(self.mapper.model_type, field_name)
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
    
    def _specification_to_where_clause(self, specification: Specification[T] | None) -> Any | None:
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