"""
Value object protocol interfaces.

This module defines protocol interfaces for ValueObject.
"""

from typing import Protocol, Dict, Any, TypeVar, Generic

T = TypeVar("T")


class ValueObjectProtocol(Protocol):
    """Protocol interface for ValueObject."""

    def equals(self, other: Any) -> bool:
        """Check if this value object equals another."""
        ...

    def validate(self) -> None:
        """Validate the value object."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert value object to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValueObjectProtocol":
        """Create value object from dictionary."""
        ...


class PrimitiveValueObjectProtocol(ValueObjectProtocol, Generic[T], Protocol):
    """Protocol interface for PrimitiveValueObject."""

    value: T

    @classmethod
    def create(cls, value: T) -> "PrimitiveValueObjectProtocol[T]":
        """Create a primitive value object."""
        ...
