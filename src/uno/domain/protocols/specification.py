"""
Specification pattern protocols for domain models.

This module defines protocols for implementing the specification pattern,
which allows for encapsulating query criteria in separate objects.
"""

from typing import TypeVar, Generic, Protocol, Any

T = TypeVar("T")


class SpecificationProtocol(Protocol, Generic[T]):
    """
    Protocol for the Specification pattern.

    The Specification pattern allows for encapsulating query criteria in separate objects,
    making them reusable and composable.
    """

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        Args:
            candidate: The object to check against the specification

        Returns:
            True if the candidate satisfies the specification, False otherwise
        """
        ...

    def and_(self, other: "SpecificationProtocol[T]") -> "SpecificationProtocol[T]":
        """
        Combine this specification with another using logical AND.

        Args:
            other: Another specification to combine with

        Returns:
            A new specification that is satisfied only when both specifications are satisfied
        """
        ...

    def or_(self, other: "SpecificationProtocol[T]") -> "SpecificationProtocol[T]":
        """
        Combine this specification with another using logical OR.

        Args:
            other: Another specification to combine with

        Returns:
            A new specification that is satisfied when either specification is satisfied
        """
        ...

    def not_(self) -> "SpecificationProtocol[T]":
        """
        Negate this specification.

        Returns:
            A new specification that is satisfied when this specification is not satisfied
        """
        ...
