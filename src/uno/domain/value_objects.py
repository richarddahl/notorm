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
from uno.core.errors.result import Result, Success, Failure

# NOTE: All validate and domain logic now return Result types instead of raising exceptions.


class Email(PrimitiveValueObject[str]):
    """Email address value object."""
    
    def validate(self) -> Result[None, str]:
        """Validate email address."""
        if not self.value:
            return Failure[None, str]("Email cannot be empty")
        if "@" not in self.value:
            return Failure[None, str]("Email must contain @")
        if "." not in self.value.split("@", 1)[1]:
            return Failure[None, str]("Email must have a valid domain")
        return Success[None, str](None)
    
    @field_validator('value')
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
            return Failure[None, str]("Amount cannot be negative")
        if self.currency not in {"USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"}:
            return Failure[None, str](f"Unsupported currency: {self.currency}")
        return Success[None, str](None)
    
    def add(self, other: 'Money') -> Result['Money', str]:
        """
        Add money.
        Returns Result monad.
        """
        if self.currency != other.currency:
            return Failure[Money, str]("Cannot add different currencies")
        return Success[Money, str](Money(amount=self.amount + other.amount, currency=self.currency))
    
    def subtract(self, other: 'Money') -> Result['Money', str]:
        """
        Subtract money.
        Returns Result monad.
        """
        if self.currency != other.currency:
            return Failure[Money, str]("Cannot subtract different currencies")
        result = self.amount - other.amount
        if result < 0:
            return Failure[Money, str]("Result cannot be negative")
        return Success[Money, str](Money(amount=result, currency=self.currency))
    
    def multiply(self, factor: float) -> Result['Money', str]:
        """
        Multiply money by a factor.
        Returns Result monad.
        """
        if factor < 0:
            return Failure[Money, str]("Factor cannot be negative")
        return Success[Money, str](Money(amount=self.amount * factor, currency=self.currency))


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
            return Failure[None, str]("Street cannot be empty")
        if not self.city:
            return Failure[None, str]("City cannot be empty")
        if not self.zip_code:
            return Failure[None, str]("Zip code cannot be empty")
        return Success[None, str](None)
    
    @property
    def formatted(self) -> str:
        """Return formatted address string."""
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}, {self.country}"
