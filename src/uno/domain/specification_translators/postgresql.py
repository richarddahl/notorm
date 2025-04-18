"""
PostgreSQL translator for specification patterns.

This module provides a translator for converting domain specifications
to SQLAlchemy expressions optimized for PostgreSQL.
"""

from typing import (
    TypeVar,
    Generic,
    Dict,
    Any,
    List,
    Optional,
    Type,
    cast,
    Union,
    Callable,
)
from datetime import datetime, date, timezone, timedelta
import re
import json
import uuid

from sqlalchemy import select, and_, or_, not_, Column, Table, func, cast as sql_cast
from sqlalchemy.sql.expression import ColumnElement, BinaryExpression, Select, true
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID

from uno.domain.protocols import EntityProtocol, SpecificationProtocol
from uno.domain.specifications.base import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    AttributeSpecification,
    PredicateSpecification,
    DictionarySpecification,
)
from uno.domain.specifications.enhanced import (
    RangeSpecification,
    DateRangeSpecification,
    TextMatchSpecification,
    InListSpecification,
    NotInListSpecification,
    ComparableSpecification,
    NullSpecification,
    NotNullSpecification,
    RelativeDateSpecification,
    CollectionSizeSpecification,
    CollectionContainsSpecification,
    UUIDSpecification,
    JsonPathSpecification,
    HasAttributeSpecification,
)
from uno.domain.base.model import BaseModel

# Type variable for the entity being specified
T = TypeVar("T", bound=EntityProtocol)
M = TypeVar("M", bound=BaseModel)


class PostgreSQLSpecificationTranslator(Generic[T]):
    """
    Translator for converting domain specifications to SQLAlchemy expressions
    for PostgreSQL.

    This implementation specifically targets PostgreSQL 16+ and integrates with
    SQLAlchemy's query building.
    """

    def __init__(self, model_class: Type[BaseModel]):
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

        elif isinstance(specification, RangeSpecification):
            return self._translate_range_specification(specification)

        elif isinstance(specification, DateRangeSpecification):
            return self._translate_date_range_specification(specification)

        elif isinstance(specification, RelativeDateSpecification):
            return self._translate_relative_date_specification(specification)

        elif isinstance(specification, TextMatchSpecification):
            return self._translate_text_match_specification(specification)

        elif isinstance(specification, InListSpecification):
            return self._translate_in_list_specification(specification)

        elif isinstance(specification, NotInListSpecification):
            return self._translate_not_in_list_specification(specification)

        elif isinstance(specification, ComparableSpecification):
            return self._translate_comparable_specification(specification)

        elif isinstance(specification, NullSpecification):
            return self._translate_null_specification(specification)

        elif isinstance(specification, NotNullSpecification):
            return self._translate_not_null_specification(specification)

        elif isinstance(specification, CollectionSizeSpecification):
            return self._translate_collection_size_specification(specification)

        elif isinstance(specification, CollectionContainsSpecification):
            return self._translate_collection_contains_specification(specification)

        elif isinstance(specification, UUIDSpecification):
            return self._translate_uuid_specification(specification)

        elif isinstance(specification, JsonPathSpecification):
            return self._translate_json_path_specification(specification)

        elif isinstance(specification, HasAttributeSpecification):
            return self._translate_has_attribute_specification(specification)

        elif isinstance(specification, PredicateSpecification):
            # For predicate specifications, we need to use a more complex approach
            # Since we can't directly translate a Python predicate function to SQL,
            # we'll need to fetch all records and filter them in Python
            # This is inefficient for large datasets, so we'll return None
            # and handle this case specially in the repository implementation
            return None

        elif isinstance(specification, DictionarySpecification):
            # For dictionary specifications, we'll create an AND clause of attribute specifications
            clauses = []
            for key, value in specification.conditions.items():
                attr_spec = AttributeSpecification(key, value)
                clause = self._translate_attribute_specification(attr_spec)
                if clause is not None:
                    clauses.append(clause)

            if clauses:
                return and_(*clauses)
            else:
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

    def _translate_range_specification(
        self, specification: RangeSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a range specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The range specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create range conditions
        min_condition = (
            column > specification.min_value
            if not specification.include_min
            else column >= specification.min_value
        )
        max_condition = (
            column < specification.max_value
            if not specification.include_max
            else column <= specification.max_value
        )

        # Combine conditions
        return and_(min_condition, max_condition)

    def _translate_date_range_specification(
        self, specification: DateRangeSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a date range specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The date range specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create date range conditions
        start_condition = (
            column > specification.start_date
            if not specification.include_start
            else column >= specification.start_date
        )
        end_condition = (
            column < specification.end_date
            if not specification.include_end
            else column <= specification.end_date
        )

        # Combine conditions
        return and_(start_condition, end_condition)

    def _translate_relative_date_specification(
        self, specification: RelativeDateSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a relative date specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The relative date specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Calculate the relative date
        now = datetime.now(timezone.utc)
        delta = timedelta(
            days=specification.days,
            hours=specification.hours,
            minutes=specification.minutes,
        )

        if specification.mode == "past":
            boundary_date = now - delta
            if specification.include_boundary:
                return column >= boundary_date
            else:
                return column > boundary_date
        else:  # mode == "future"
            boundary_date = now + delta
            if specification.include_boundary:
                return column <= boundary_date
            else:
                return column < boundary_date

    def _translate_text_match_specification(
        self, specification: TextMatchSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a text match specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The text match specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create text match condition based on match type
        if specification.match_type == "contains":
            if specification.case_sensitive:
                return column.contains(specification.text)
            else:
                return column.ilike(f"%{specification.text}%")

        elif specification.match_type == "starts_with":
            if specification.case_sensitive:
                return column.startswith(specification.text)
            else:
                return column.ilike(f"{specification.text}%")

        elif specification.match_type == "ends_with":
            if specification.case_sensitive:
                return column.endswith(specification.text)
            else:
                return column.ilike(f"%{specification.text}")

        elif specification.match_type == "exact":
            if specification.case_sensitive:
                return column == specification.text
            else:
                return func.lower(column) == func.lower(specification.text)

        elif specification.match_type == "regex":
            # Use PostgreSQL's REGEXP operator (~) for regex matching
            if specification.case_sensitive:
                return column.op("~")(specification.text)
            else:
                return column.op("~*")(specification.text)

        else:
            raise ValueError(f"Unknown match type: {specification.match_type}")

    def _translate_in_list_specification(
        self, specification: InListSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate an in-list specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The in-list specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create in-list condition
        return column.in_(specification.values)

    def _translate_not_in_list_specification(
        self, specification: NotInListSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a not-in-list specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The not-in-list specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create not-in-list condition
        return ~column.in_(specification.values)

    def _translate_comparable_specification(
        self, specification: ComparableSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a comparable specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The comparable specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create comparison condition based on operator
        if specification.operator == "eq":
            return column == specification.value
        elif specification.operator == "neq":
            return column != specification.value
        elif specification.operator == "gt":
            return column > specification.value
        elif specification.operator == "gte":
            return column >= specification.value
        elif specification.operator == "lt":
            return column < specification.value
        elif specification.operator == "lte":
            return column <= specification.value
        else:
            raise ValueError(f"Unknown operator: {specification.operator}")

    def _translate_null_specification(
        self, specification: NullSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a null specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The null specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create null condition
        return column.is_(None)

    def _translate_not_null_specification(
        self, specification: NotNullSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a not-null specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The not-null specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Create not-null condition
        return column.isnot(None)

    def _translate_collection_size_specification(
        self, specification: CollectionSizeSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a collection size specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The collection size specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # For array columns in PostgreSQL, use the array_length function
        # This assumes the column is an ARRAY type
        size_expr = func.array_length(column, 1)

        # Handle null arrays (array_length returns null for empty arrays)
        if specification.size == 0:
            if specification.operator == "eq":
                return or_(size_expr.is_(None), size_expr == 0)
            elif specification.operator == "neq":
                return and_(size_expr.isnot(None), size_expr != 0)

        # Compare based on operator
        if specification.operator == "eq":
            return size_expr == specification.size
        elif specification.operator == "neq":
            return size_expr != specification.size
        elif specification.operator == "gt":
            return size_expr > specification.size
        elif specification.operator == "gte":
            return size_expr >= specification.size
        elif specification.operator == "lt":
            return size_expr < specification.size
        elif specification.operator == "lte":
            return size_expr <= specification.size
        else:
            raise ValueError(f"Unknown operator: {specification.operator}")

    def _translate_collection_contains_specification(
        self, specification: CollectionContainsSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a collection contains specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The collection contains specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Use the ANY operator for PostgreSQL arrays
        # This assumes the column is an ARRAY type
        return specification.value == any_(column)

    def _translate_uuid_specification(
        self, specification: UUIDSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a UUID specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The UUID specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # For UUID columns, ensure the value is properly typed
        if isinstance(specification.uuid_value, uuid.UUID):
            return column == specification.uuid_value
        elif isinstance(specification.uuid_value, str):
            # Try to convert to UUID
            try:
                uuid_value = uuid.UUID(specification.uuid_value)
                return column == uuid_value
            except ValueError:
                # If not a valid UUID, compare as string
                return column == specification.uuid_value
        else:
            # Fall back to direct comparison
            return column == specification.uuid_value

    def _translate_json_path_specification(
        self, specification: JsonPathSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a JSON path specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The JSON path specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # Get the column
        column = getattr(self.model_class, specification.attribute)

        # Build the JSON path
        path_expr = column
        for key in specification.path:
            # Use -> operator for text keys and ->> for text output
            is_last = key == specification.path[-1]
            if is_last:
                path_expr = path_expr.op("->>")(key)
            else:
                path_expr = path_expr.op("->")(key)

        # For comparing with non-string values when using ->>
        if isinstance(specification.value, (int, float, bool)):
            if is_last:
                # Cast the string result to the appropriate type
                if isinstance(specification.value, int):
                    path_expr = sql_cast(path_expr, sa.Integer)
                elif isinstance(specification.value, float):
                    path_expr = sql_cast(path_expr, sa.Float)
                elif isinstance(specification.value, bool):
                    path_expr = sql_cast(path_expr, sa.Boolean)

        # Compare based on operator
        if specification.operator == "eq":
            return path_expr == specification.value
        elif specification.operator == "neq":
            return path_expr != specification.value
        elif specification.operator == "gt":
            return path_expr > specification.value
        elif specification.operator == "gte":
            return path_expr >= specification.value
        elif specification.operator == "lt":
            return path_expr < specification.value
        elif specification.operator == "lte":
            return path_expr <= specification.value
        else:
            raise ValueError(f"Unknown operator: {specification.operator}")

    def _translate_has_attribute_specification(
        self, specification: HasAttributeSpecification[T]
    ) -> Optional[ColumnElement]:
        """
        Translate a has-attribute specification to a SQLAlchemy WHERE clause.

        Args:
            specification: The has-attribute specification to translate

        Returns:
            A SQLAlchemy ColumnElement for the WHERE clause, or None
        """
        # Ensure the attribute exists in the model
        if not hasattr(self.model_class, specification.attribute):
            return None

        # For database tables, if a column exists in the model, it always exists in the entity
        # So we just need to check if it's not null
        column = getattr(self.model_class, specification.attribute)
        return column.isnot(None)
