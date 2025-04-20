"""
Common value objects for the Uno framework.

This module provides common value object implementations that can be used across
the application. These are based on the core ValueObject and PrimitiveValueObject
classes defined in uno.domain.core.
"""

from typing import Optional, cast, Dict, Any
from uuid import UUID

from pydantic import field_validator, ConfigDict

from uno.domain.core import ValueObject, PrimitiveValueObject
from uno.core.errors.result import Result

# NOTE: All validate and domain logic now return Result types instead of raising exceptions.


class Email(PrimitiveValueObject[str]):
    """Email address value object."""

    def validate(self) -> Result[None, str]:
        """Validate email address."""
        if not self.value:
            return Result.failure("Email cannot be empty")
        if "@" not in self.value:
            return Result.failure("Email must contain @")
        if "." not in self.value.split("@", 1)[1]:
            return Result.failure("Email must have a valid domain")
        return Result.success(None)

    @field_validator("value")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower() if isinstance(v, str) else v


class Money(ValueObject):
    """Money value object."""

    amount: float
    currency: str = "USD"

    def validate(self) -> Result[None, str]:
        """Validate money."""
        if self.amount < 0:
            return Result.failure("Amount cannot be negative")
        if self.currency not in {"USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"}:
            return Result.failure(f"Unsupported currency: {self.currency}")
        return Result.success(None)

    def add(self, other: "Money") -> Result["Money", str]:
        """
        Add money.
        Returns Result monad.
        """
        if self.currency != other.currency:
            return Result.failure("Cannot add different currencies")
        return Result.success(
            Money(amount=self.amount + other.amount, currency=self.currency)
        )

    def subtract(self, other: "Money") -> Result["Money", str]:
        """
        Subtract money.
        Returns Result monad.
        """
        if self.currency != other.currency:
            return Result.failure("Cannot subtract different currencies")
        result = self.amount - other.amount
        if result < 0:
            return Result.failure("Result cannot be negative")
        return Result.success(Money(amount=result, currency=self.currency))

    def multiply(self, factor: float) -> Result["Money", str]:
        """
        Multiply money by a factor.
        Returns Result monad.
        """
        if factor < 0:
            return Result.failure("Factor cannot be negative")
        return Result.success(
            Money(amount=self.amount * factor, currency=self.currency)
        )


class Address(ValueObject):
    """Address value object."""

    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"

    def validate(self) -> Result[None, str]:
        """Validate address."""
        if not self.street:
            return Result.failure("Street cannot be empty")
        if not self.city:
            return Result.failure("City cannot be empty")
        if not self.zip_code:
            return Result.failure("Zip code cannot be empty")
        return Result.success(None)

    @property
    def formatted(self) -> str:
        """Return formatted address string."""
        return (
            f"{self.street}, {self.city}, {self.state} {self.zip_code}, {self.country}"
        )
