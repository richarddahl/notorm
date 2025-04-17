"""
Base specification implementations.

This module provides base classes for the specification pattern.
"""

from typing import TypeVar, Generic, Any, Callable, Optional
from abc import ABC, abstractmethod

T = TypeVar("T")


class Specification(Generic[T], ABC):
    """Base class for all specifications."""

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        Args:
            candidate: The candidate to check

        Returns:
            True if the candidate satisfies the specification, False otherwise
        """
        pass

    def and_(self, other: "Specification[T]") -> "Specification[T]":
        """
        Combine this specification with another using AND.

        Args:
            other: The other specification

        Returns:
            A new specification that is the AND of this and the other
        """
        from .composite_specifications import AndSpecification

        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "Specification[T]":
        """
        Combine this specification with another using OR.

        Args:
            other: The other specification

        Returns:
            A new specification that is the OR of this and the other
        """
        from .composite_specifications import OrSpecification

        return OrSpecification(self, other)

    def not_(self) -> "Specification[T]":
        """
        Negate this specification.

        Returns:
            A new specification that is the negation of this one
        """
        from .composite_specifications import NotSpecification

        return NotSpecification(self)


class AttributeSpecification(Specification[T]):
    """Specification that checks an attribute of a candidate."""

    def __init__(
        self,
        attribute_name: str,
        expected_value: Any,
        comparator: Optional[Callable[[Any, Any], bool]] = None,
    ):
        """
        Initialize the attribute specification.

        Args:
            attribute_name: The name of the attribute to check
            expected_value: The expected value of the attribute
            comparator: Optional function to compare the attribute value with the expected value
        """
        self.attribute_name = attribute_name
        self.expected_value = expected_value
        self.comparator = comparator or (lambda a, b: a == b)

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        Args:
            candidate: The candidate to check

        Returns:
            True if the candidate satisfies the specification, False otherwise
        """
        attribute_value = getattr(candidate, self.attribute_name)
        return self.comparator(attribute_value, self.expected_value)
