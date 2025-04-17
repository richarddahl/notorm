"""
Specification translators for converting domain specifications to database queries.

This module provides implementations for translating domain specifications to
various database query languages, with a focus on PostgreSQL.
"""

from typing import (
    TypeVar, Generic, Dict, Any, List, Tuple, Optional, Type, cast,
    Union, Callable
)
from abc import ABC, abstractmethod

from sqlalchemy import select, and_, or_, not_, Column, Table
from sqlalchemy.sql.expression import ColumnElement, BinaryExpression, Select

from uno.domain.protocols import EntityProtocol, SpecificationProtocol
from uno.domain.specifications import (
    Specification, AndSpecification, OrSpecification, NotSpecification,
    AttributeSpecification, PredicateSpecification
)
from uno.model import UnoModel

# Type variable for the entity being specified
T = TypeVar('T', bound=EntityProtocol)
M = TypeVar('M', bound=UnoModel)


class SpecificationTranslator(Generic[T], ABC):
    """Base class for specification translators."""
    
    @abstractmethod
    def translate(self, specification: SpecificationProtocol[T]) -> Any:
        """
        Translate a specification to a database query.
        
        Args:
            specification: The specification to translate
            
        Returns:
            A database query
        """
        pass


class PostgreSQLSpecificationTranslator(SpecificationTranslator[T]):
    """
    Translator for converting domain specifications to SQLAlchemy expressions
    for PostgreSQL.
    
    This implementation specifically targets PostgreSQL 16+ and integrates with
    SQLAlchemy's query building.
    """
    
    def __init__(self, model_class: Type[UnoModel]):
        """
        Initialize the PostgreSQL specification translator.
        
        Args:
            model_class: The SQLAlchemy model class for the entity
        """
        self.model_class = model_class
        self.table = model_class.__table__
    
    def translate(self, specification: SpecificationProtocol[T]) -> Select:
        """
        Translate a specification to a SQLAlchemy SELECT statement.
        
        Args:
            specification: The specification to translate
            
        Returns:
            A SQLAlchemy SELECT statement
        """
        # Start with a basic select
        query = select(self.model_class)
        
        # Add the where clause from the specification
        where_clause = self._translate_to_where_clause(specification)
        if where_clause is not None:
            query = query.where(where_clause)
        
        return query
    
    def _translate_to_where_clause(
        self, specification: SpecificationProtocol[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a specification to a SQLAlchemy WHERE clause.
        
        Args:
            specification: The specification to translate
            
        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Handle different specification types
        if isinstance(specification, AndSpecification):
            left = self._translate_to_where_clause(specification.left)
            right = self._translate_to_where_clause(specification.right)
            if left is not None and right is not None:
                return and_(left, right)
            elif left is not None:
                return left
            elif right is not None:
                return right
            else:
                return None
        
        elif isinstance(specification, OrSpecification):
            left = self._translate_to_where_clause(specification.left)
            right = self._translate_to_where_clause(specification.right)
            if left is not None and right is not None:
                return or_(left, right)
            elif left is not None:
                return left
            elif right is not None:
                return right
            else:
                return None
        
        elif isinstance(specification, NotSpecification):
            inner = self._translate_to_where_clause(specification.specification)
            if inner is not None:
                return not_(inner)
            else:
                return None
        
        elif isinstance(specification, AttributeSpecification):
            return self._translate_attribute_specification(specification)
        
        elif isinstance(specification, PredicateSpecification):
            # For predicate specifications, we need to use a more complex approach
            # Since we can't directly translate a Python predicate function to SQL,
            # we'll need to fetch all records and filter them in Python
            # This is inefficient for large datasets, so we'll return None
            # and handle this case specially in the repository implementation
            return None
        
        else:
            # Unknown specification type
            return None
    
    def _translate_attribute_specification(
        self, specification: AttributeSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate an attribute specification to a SQLAlchemy WHERE clause.
        
        Args:
            specification: The attribute specification to translate
            
        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None
        
        # Get the column
        column = getattr(self.model_class, specification.attribute)
        
        # Compare with the value
        return column == specification.value


class PostgreSQLRepository(Generic[T, M]):
    """
    PostgreSQL repository that uses the specification translator.
    
    This repository implementation translates domain specifications to
    SQLAlchemy queries and executes them against a PostgreSQL database.
    """
    
    def __init__(
        self, 
        entity_type: Type[T], 
        model_class: Type[M],
        session_factory: Callable
    ):
        """
        Initialize the PostgreSQL repository.
        
        Args:
            entity_type: The domain entity type
            model_class: The SQLAlchemy model class
            session_factory: Factory function for database sessions
        """
        self.entity_type = entity_type
        self.model_class = model_class
        self.session_factory = session_factory
        self.translator = PostgreSQLSpecificationTranslator(model_class)
    
    async def find_by_specification(
        self, specification: SpecificationProtocol[T]
    ) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        # Translate the specification to a SQLAlchemy query
        query = self.translator.translate(specification)
        
        # Execute the query
        async with self.session_factory() as session:
            result = await session.execute(query)
            models = result.scalars().all()
        
        # Convert models to domain entities
        return [self._to_entity(model) for model in models]
    
    def _to_entity(self, model: M) -> T:
        """
        Convert a model to a domain entity.
        
        Args:
            model: The model to convert
            
        Returns:
            The corresponding domain entity
        """
        # This is a simple implementation that assumes the model can be
        # directly converted to a dictionary for entity creation
        data = self._model_to_dict(model)
        entity = self.entity_type(**data)
        return entity
    
    def _model_to_dict(self, model: M) -> Dict[str, Any]:
        """
        Convert a model to a dictionary.
        
        Args:
            model: The model to convert
            
        Returns:
            Dictionary representation of the model
        """
        # Convert the model to a dictionary using SQLAlchemy's __dict__
        # Exclude SQLAlchemy internal attributes
        return {
            k: v for k, v in model.__dict__.items()
            if not k.startswith('_')
        }


class AsyncPostgreSQLRepository(PostgreSQLRepository[T, M]):
    """
    Asynchronous PostgreSQL repository that uses the specification translator.
    
    This repository implementation provides asynchronous methods for working
    with PostgreSQL and domain specifications.
    """
    
    async def find_by_specification(
        self, specification: SpecificationProtocol[T]
    ) -> List[T]:
        """
        Find entities matching a specification asynchronously.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        # Translate the specification to a SQLAlchemy query
        query = self.translator.translate(specification)
        
        # Execute the query asynchronously
        async with self.session_factory() as session:
            result = await session.execute(query)
            models = result.scalars().all()
        
        # Convert models to domain entities
        return [self._to_entity(model) for model in models]
    
    async def count_by_specification(
        self, specification: SpecificationProtocol[T]
    ) -> int:
        """
        Count entities matching a specification asynchronously.
        
        Args:
            specification: The specification to match
            
        Returns:
            Number of matching entities
        """
        # Translate the specification to a SQLAlchemy query
        query = self.translator.translate(specification)
        
        # Modify query to count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        
        # Execute the query asynchronously
        async with self.session_factory() as session:
            result = await session.execute(count_query)
            count = result.scalar_one()
        
        return count