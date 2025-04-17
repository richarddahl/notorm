"""
Composite specification implementations.

This module provides composite classes for the specification pattern.
"""

from typing import TypeVar, Generic
from .base_specifications import Specification

T = TypeVar("T")


class AndSpecification(Specification[T]):
    """Specification that is satisfied when both of its components are satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize the AND specification.

        Args:
            left: The left specification
            right: The right specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        Args:
            candidate: The candidate to check

        Returns:
            True if the candidate satisfies both specifications, False otherwise
        """
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(
            candidate
        )


class OrSpecification(Specification[T]):
    """Specification that is satisfied when either of its components is satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize the OR specification.

        Args:
            left: The left specification
            right: The right specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        Args:
            candidate: The candidate to check

        Returns:
            True if the candidate satisfies either specification, False otherwise
        """
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(
            candidate
        )


class NotSpecification(Specification[T]):
    """Specification that is satisfied when its component is not satisfied."""

    def __init__(self, specification: Specification[T]):
        """
        Initialize the NOT specification.

        Args:
            specification: The specification to negate
        """
        self.specification = specification

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        Args:
            candidate: The candidate to check

        Returns:
            True if the candidate does not satisfy the specification, False otherwise
        """
        return not self.specification.is_satisfied_by(candidate)
