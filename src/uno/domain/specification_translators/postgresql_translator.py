"""
PostgreSQL specification translator.

This module provides a translator for converting specifications to PostgreSQL queries.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from sqlalchemy import and_, or_, not_, Column, Table
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from ..specifications import (
    Specification,
    AttributeSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
)

T = TypeVar("T")


class PostgreSQLSpecificationTranslator:
    """Translator for converting specifications to PostgreSQL queries."""

    def __init__(self, model_class: Type[Any]):
        """
        Initialize the translator.

        Args:
            model_class: The SQLAlchemy model class
        """
        self.model_class = model_class

    def translate(
        self, specification: Specification[T]
    ) -> Union[BinaryExpression, UnaryExpression, bool]:
        """
        Translate a specification to a SQLAlchemy expression.

        Args:
            specification: The specification to translate

        Returns:
            A SQLAlchemy expression

        Raises:
            ValueError: If the specification type is not supported
        """
        if isinstance(specification, AttributeSpecification):
            return self._translate_attribute_specification(specification)
        elif isinstance(specification, AndSpecification):
            return self._translate_and_specification(specification)
        elif isinstance(specification, OrSpecification):
            return self._translate_or_specification(specification)
        elif isinstance(specification, NotSpecification):
            return self._translate_not_specification(specification)
        else:
            raise ValueError(f"Unsupported specification type: {type(specification)}")

    def _translate_attribute_specification(
        self, specification: AttributeSpecification[T]
    ) -> BinaryExpression:
        """
        Translate an attribute specification to a SQLAlchemy expression.

        Args:
            specification: The attribute specification to translate

        Returns:
            A SQLAlchemy binary expression
        """
        column = getattr(self.model_class, specification.attribute_name)
        return column == specification.expected_value

    def _translate_and_specification(
        self, specification: AndSpecification[T]
    ) -> BinaryExpression:
        """
        Translate an AND specification to a SQLAlchemy expression.

        Args:
            specification: The AND specification to translate

        Returns:
            A SQLAlchemy binary expression
        """
        left_expr = self.translate(specification.left)
        right_expr = self.translate(specification.right)
        return and_(left_expr, right_expr)

    def _translate_or_specification(
        self, specification: OrSpecification[T]
    ) -> BinaryExpression:
        """
        Translate an OR specification to a SQLAlchemy expression.

        Args:
            specification: The OR specification to translate

        Returns:
            A SQLAlchemy binary expression
        """
        left_expr = self.translate(specification.left)
        right_expr = self.translate(specification.right)
        return or_(left_expr, right_expr)

    def _translate_not_specification(
        self, specification: NotSpecification[T]
    ) -> UnaryExpression:
        """
        Translate a NOT specification to a SQLAlchemy expression.

        Args:
            specification: The NOT specification to translate

        Returns:
            A SQLAlchemy unary expression
        """
        expr = self.translate(specification.specification)
        return not_(expr)
