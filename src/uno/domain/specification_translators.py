"""
Specification translators for the domain layer.

This module provides translators that convert domain specifications to database
queries, enabling the specification pattern to be used with different database technologies.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Any, Optional, Dict, cast, List, Callable
import logging

from sqlalchemy import and_, or_, not_, Column, select, func, Table
from sqlalchemy.sql.expression import ColumnElement, Select
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.core import Entity
from uno.domain.specifications import (
    Specification, AndSpecification, OrSpecification, NotSpecification,
    AttributeSpecification, PredicateSpecification
)


T = TypeVar("T", bound=Entity)
M = TypeVar("M")  # Model type


class SpecificationTranslator(Generic[T], ABC):
    """
    Abstract base class for specification translators.
    
    Specification translators convert domain specifications to database queries,
    enabling the specification pattern to be used with different database technologies.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the specification translator.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def translate(self, specification: Specification[T]) -> Any:
        """
        Translate a specification to a database query.
        
        Args:
            specification: The specification to translate
            
        Returns:
            A database-specific query object
        """
        pass


class SQLAlchemySpecificationTranslator(SpecificationTranslator[T], Generic[T, M]):
    """
    SQLAlchemy implementation of the specification translator.
    
    This translator converts domain specifications to SQLAlchemy query expressions.
    """
    
    def __init__(
        self, 
        model_class: Type[M], 
        logger: Optional[logging.Logger] = None,
        field_mappings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the SQLAlchemy specification translator.
        
        Args:
            model_class: The SQLAlchemy model class
            logger: Optional logger for diagnostic output
            field_mappings: Optional mapping from entity field names to model field names
        """
        super().__init__(logger)
        self.model_class = model_class
        self.field_mappings = field_mappings or {}
        
        # Get the table if available
        self.table = getattr(model_class, "__table__", None)
    
    def translate(self, specification: Specification[T]) -> Select:
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
    
    def _translate_to_where_clause(self, specification: Specification[T]) -> Optional[ColumnElement]:
        """
        Translate a specification to a SQLAlchemy WHERE clause.
        
        Args:
            specification: The specification to translate
            
        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None if the 
            specification cannot be translated
        """
        # Handle different specification types
        if isinstance(specification, AndSpecification):
            return self._translate_and(specification)
        elif isinstance(specification, OrSpecification):
            return self._translate_or(specification)
        elif isinstance(specification, NotSpecification):
            return self._translate_not(specification)
        elif isinstance(specification, AttributeSpecification):
            return self._translate_attribute(specification)
        elif isinstance(specification, PredicateSpecification):
            # Predicates can't be directly translated, but we can provide support
            # for some common predicate patterns based on their name
            return self._translate_predicate(specification)
        else:
            # Custom specification types - try to infer intent from class name
            return self._translate_custom(specification)
    
    def _translate_and(self, specification: AndSpecification) -> Optional[ColumnElement]:
        """
        Translate an AND specification.
        
        Args:
            specification: The AND specification
            
        Returns:
            A SQLAlchemy AND expression
        """
        left = self._translate_to_where_clause(specification.left)
        right = self._translate_to_where_clause(specification.right)
        
        if left is None and right is None:
            return None
        elif left is None:
            return right
        elif right is None:
            return left
        else:
            return and_(left, right)
    
    def _translate_or(self, specification: OrSpecification) -> Optional[ColumnElement]:
        """
        Translate an OR specification.
        
        Args:
            specification: The OR specification
            
        Returns:
            A SQLAlchemy OR expression
        """
        left = self._translate_to_where_clause(specification.left)
        right = self._translate_to_where_clause(specification.right)
        
        if left is None and right is None:
            return None
        elif left is None:
            return right
        elif right is None:
            return left
        else:
            return or_(left, right)
    
    def _translate_not(self, specification: NotSpecification) -> Optional[ColumnElement]:
        """
        Translate a NOT specification.
        
        Args:
            specification: The NOT specification
            
        Returns:
            A SQLAlchemy NOT expression
        """
        inner = self._translate_to_where_clause(specification.specification)
        
        if inner is None:
            return None
        else:
            return not_(inner)
    
    def _translate_attribute(self, specification: AttributeSpecification) -> Optional[ColumnElement]:
        """
        Translate an attribute specification.
        
        Args:
            specification: The attribute specification
            
        Returns:
            A SQLAlchemy equality expression
        """
        # Get the model field name (might be different from entity field name)
        field_name = self.field_mappings.get(specification.attribute, specification.attribute)
        
        # Check if the field exists on the model
        if not hasattr(self.model_class, field_name):
            self.logger.warning(
                f"Field '{field_name}' not found on model {self.model_class.__name__}"
            )
            return None
        
        # Get the model column
        column = getattr(self.model_class, field_name)
        
        # Create equality expression
        return column == specification.value
    
    def _translate_predicate(self, specification: PredicateSpecification) -> Optional[ColumnElement]:
        """
        Translate a predicate specification.
        
        Args:
            specification: The predicate specification
            
        Returns:
            A SQLAlchemy expression if the predicate can be translated, None otherwise
        """
        # Try to infer intent from the predicate name
        name = specification.name
        
        # Look for patterns like field_op_value
        if "_gt_" in name:
            field, value = name.split("_gt_", 1)
            return self._create_comparison(field, ">", self._parse_value(value))
        elif "_gte_" in name:
            field, value = name.split("_gte_", 1)
            return self._create_comparison(field, ">=", self._parse_value(value))
        elif "_lt_" in name:
            field, value = name.split("_lt_", 1)
            return self._create_comparison(field, "<", self._parse_value(value))
        elif "_lte_" in name:
            field, value = name.split("_lte_", 1)
            return self._create_comparison(field, "<=", self._parse_value(value))
        elif "_contains_" in name:
            field, value = name.split("_contains_", 1)
            return self._create_like(field, value)
        elif "_in_" in name:
            field, value = name.split("_in_", 1)
            return self._create_in(field, self._parse_list(value))
        elif "_is_null" in name:
            field = name.replace("_is_null", "")
            return self._create_is_null(field)
        
        # Unknown predicate pattern - warn but don't fail
        self.logger.warning(
            f"Unable to translate predicate specification with name '{name}'"
        )
        return None
    
    def _translate_custom(self, specification: Specification[T]) -> Optional[ColumnElement]:
        """
        Translate a custom specification.
        
        Args:
            specification: The custom specification
            
        Returns:
            A SQLAlchemy expression if the specification can be translated, None otherwise
        """
        # Try to infer intent from the class name
        class_name = specification.__class__.__name__
        
        # We could add more patterns here based on common naming conventions
        if "Equals" in class_name and hasattr(specification, "field") and hasattr(specification, "value"):
            return self._create_comparison(specification.field, "==", specification.value)
        elif "GreaterThan" in class_name and hasattr(specification, "field") and hasattr(specification, "value"):
            return self._create_comparison(specification.field, ">", specification.value)
        elif "LessThan" in class_name and hasattr(specification, "field") and hasattr(specification, "value"):
            return self._create_comparison(specification.field, "<", specification.value)
        elif "Contains" in class_name and hasattr(specification, "field") and hasattr(specification, "value"):
            return self._create_like(specification.field, specification.value)
        
        # Unknown custom specification - warn but don't fail
        self.logger.warning(
            f"Unable to translate custom specification of type '{class_name}'"
        )
        return None
    
    def _create_comparison(self, field: str, op: str, value: Any) -> Optional[ColumnElement]:
        """
        Create a comparison expression.
        
        Args:
            field: The field name
            op: The operator (>, >=, <, <=, ==)
            value: The value to compare
            
        Returns:
            A SQLAlchemy comparison expression
        """
        # Get the model field name
        field_name = self.field_mappings.get(field, field)
        
        # Check if the field exists on the model
        if not hasattr(self.model_class, field_name):
            self.logger.warning(
                f"Field '{field_name}' not found on model {self.model_class.__name__}"
            )
            return None
        
        # Get the model column
        column = getattr(self.model_class, field_name)
        
        # Create comparison expression
        if op == ">":
            return column > value
        elif op == ">=":
            return column >= value
        elif op == "<":
            return column < value
        elif op == "<=":
            return column <= value
        elif op == "==" or op == "=":
            return column == value
        elif op == "!=" or op == "<>":
            return column != value
        else:
            self.logger.warning(f"Unknown comparison operator: {op}")
            return None
    
    def _create_like(self, field: str, value: str) -> Optional[ColumnElement]:
        """
        Create a LIKE expression.
        
        Args:
            field: The field name
            value: The substring to search for
            
        Returns:
            A SQLAlchemy LIKE expression
        """
        # Get the model field name
        field_name = self.field_mappings.get(field, field)
        
        # Check if the field exists on the model
        if not hasattr(self.model_class, field_name):
            self.logger.warning(
                f"Field '{field_name}' not found on model {self.model_class.__name__}"
            )
            return None
        
        # Get the model column
        column = getattr(self.model_class, field_name)
        
        # Create LIKE expression with wildcards
        return column.like(f"%{value}%")
    
    def _create_in(self, field: str, values: list) -> Optional[ColumnElement]:
        """
        Create an IN expression.
        
        Args:
            field: The field name
            values: The list of values
            
        Returns:
            A SQLAlchemy IN expression
        """
        # Get the model field name
        field_name = self.field_mappings.get(field, field)
        
        # Check if the field exists on the model
        if not hasattr(self.model_class, field_name):
            self.logger.warning(
                f"Field '{field_name}' not found on model {self.model_class.__name__}"
            )
            return None
        
        # Get the model column
        column = getattr(self.model_class, field_name)
        
        # Create IN expression
        return column.in_(values)
    
    def _create_is_null(self, field: str) -> Optional[ColumnElement]:
        """
        Create an IS NULL expression.
        
        Args:
            field: The field name
            
        Returns:
            A SQLAlchemy IS NULL expression
        """
        # Get the model field name
        field_name = self.field_mappings.get(field, field)
        
        # Check if the field exists on the model
        if not hasattr(self.model_class, field_name):
            self.logger.warning(
                f"Field '{field_name}' not found on model {self.model_class.__name__}"
            )
            return None
        
        # Get the model column
        column = getattr(self.model_class, field_name)
        
        # Create IS NULL expression
        return column.is_(None)
    
    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a value string to the appropriate type.
        
        Args:
            value_str: The value string
            
        Returns:
            The parsed value
        """
        # Try to convert to int
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Boolean values
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False
        
        # Default to string
        return value_str
    
    def _parse_list(self, value_str: str) -> list:
        """
        Parse a list string to a list.
        
        Args:
            value_str: The list string (e.g., "[1, 2, 3]")
            
        Returns:
            The parsed list
        """
        import ast
        
        try:
            # Try to parse as a Python literal
            return ast.literal_eval(value_str)
        except (SyntaxError, ValueError):
            # Fall back to simple splitting
            value_str = value_str.strip("[]")
            items = [item.strip() for item in value_str.split(",")]
            return [self._parse_value(item) for item in items]


class PostgreSQLSpecificationTranslator(SQLAlchemySpecificationTranslator[T, M], Generic[T, M]):
    """
    PostgreSQL-specific implementation of the specification translator.
    
    This translator extends the SQLAlchemy translator with PostgreSQL-specific features.
    """
    
    def __init__(
        self, 
        model_class: Type[M], 
        logger: Optional[logging.Logger] = None,
        field_mappings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the PostgreSQL specification translator.
        
        Args:
            model_class: The SQLAlchemy model class
            logger: Optional logger for diagnostic output
            field_mappings: Optional mapping from entity field names to model field names
        """
        super().__init__(model_class, logger, field_mappings)
    
    def _create_ts_query(self, field: str, value: str) -> Optional[ColumnElement]:
        """
        Create a PostgreSQL text search query.
        
        Args:
            field: The field name
            value: The text to search for
            
        Returns:
            A PostgreSQL text search expression
        """
        # Get the model field name
        field_name = self.field_mappings.get(field, field)
        
        # Check if the field exists on the model
        if not hasattr(self.model_class, field_name):
            self.logger.warning(
                f"Field '{field_name}' not found on model {self.model_class.__name__}"
            )
            return None
        
        # Get the model column
        column = getattr(self.model_class, field_name)
        
        # Create text search expression using PostgreSQL to_tsvector and to_tsquery
        from sqlalchemy import text
        return text(f"to_tsvector('english', {field_name}::text) @@ to_tsquery('english', :query)").\
            bindparams(query=value)


class EnhancedSpecificationTranslator(SQLAlchemySpecificationTranslator[T, M], Generic[T, M]):
    """
    Enhanced specification translator with additional capabilities.
    
    This translator provides additional translation methods and support for
    custom specification types.
    """
    
    def __init__(
        self, 
        model_class: Type[M],
        entity_type: Type[T],
        logger: Optional[logging.Logger] = None,
        field_mappings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the enhanced specification translator.
        
        Args:
            model_class: The SQLAlchemy model class
            entity_type: The entity type
            logger: Optional logger for diagnostic output
            field_mappings: Optional mapping from entity field names to model field names
        """
        super().__init__(model_class, logger, field_mappings)
        self.entity_type = entity_type
        
        # Register custom translators
        self._custom_translators = {}
        self._register_translators()
    
    def _register_translators(self) -> None:
        """Register custom specification translators."""
        # This method is meant to be overridden by subclasses
        pass
    
    def register_translator(
        self, 
        spec_type: Type[Specification], 
        translator: Callable[[Specification], Optional[ColumnElement]]
    ) -> None:
        """
        Register a custom translator for a specification type.
        
        Args:
            spec_type: The specification type
            translator: The translator function
        """
        self._custom_translators[spec_type] = translator
    
    def _translate_custom(self, specification: Specification[T]) -> Optional[ColumnElement]:
        """
        Translate a custom specification.
        
        Args:
            specification: The custom specification
            
        Returns:
            A SQLAlchemy expression if the specification can be translated, None otherwise
        """
        # Check for registered translators
        for spec_type, translator in self._custom_translators.items():
            if isinstance(specification, spec_type):
                return translator(specification)
        
        # Fall back to parent implementation
        return super()._translate_custom(specification)


# Establish backward compatibility with the existing API
class AsyncPostgreSQLRepository:
    """
    Backward compatibility class for the existing API.
    
    This class provides the same interface as the old AsyncPostgreSQLRepository
    but uses the new standardized repository implementation internally.
    """
    
    def __init__(
        self, 
        entity_type: Type[T], 
        model_class: Type[M],
        session_factory: Callable[[], AsyncSession]
    ):
        """
        Initialize the PostgreSQL repository.
        
        Args:
            entity_type: The domain entity type
            model_class: The SQLAlchemy model class
            session_factory: Factory function for database sessions
        """
        from uno.core.base.respository import SQLAlchemyRepository
        
        self.entity_type = entity_type
        self.model_class = model_class
        self.session_factory = session_factory
        self.translator = PostgreSQLSpecificationTranslator(model_class)
        
        # Create a standardized repository
        self._repository = None
    
    async def _get_repository(self) -> Any:
        """Get the standardized repository instance."""
        from uno.core.base.respository import SQLAlchemyRepository
        
        if self._repository is None:
            session = self.session_factory()
            self._repository = SQLAlchemyRepository(
                self.entity_type,
                session,
                self.model_class
            )
        return self._repository
    
    async def find_by_specification(
        self, specification: Specification[T]
    ) -> List[T]:
        """
        Find entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            List of matching entities
        """
        repository = await self._get_repository()
        return await repository.find(specification)
    
    async def count_by_specification(
        self, specification: Specification[T]
    ) -> int:
        """
        Count entities matching a specification.
        
        Args:
            specification: The specification to match
            
        Returns:
            Number of matching entities
        """
        repository = await self._get_repository()
        return await repository.count(specification)
    
    def _to_entity(self, model: M) -> T:
        """
        Convert a model to a domain entity.
        
        Args:
            model: The model to convert
            
        Returns:
            The corresponding domain entity
        """
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
        return {
            k: v for k, v in model.__dict__.items()
            if not k.startswith('_')
        }


def create_translator(
    model_class: Type[M],
    entity_type: Type[T],
    logger: Optional[logging.Logger] = None,
    field_mappings: Optional[Dict[str, str]] = None,
    enhanced: bool = True,
    postgres_specific: bool = True
) -> SpecificationTranslator[T]:
    """
    Create a specification translator.
    
    Args:
        model_class: The SQLAlchemy model class
        entity_type: The entity type
        logger: Optional logger for diagnostic output
        field_mappings: Optional mapping from entity field names to model field names
        enhanced: Whether to create an enhanced translator
        postgres_specific: Whether to use PostgreSQL-specific features
        
    Returns:
        A specification translator
    """
    if enhanced:
        return EnhancedSpecificationTranslator(
            model_class, entity_type, logger, field_mappings
        )
    elif postgres_specific:
        return PostgreSQLSpecificationTranslator(
            model_class, logger, field_mappings
        )
    else:
        return SQLAlchemySpecificationTranslator(
            model_class, logger, field_mappings
        )
"""