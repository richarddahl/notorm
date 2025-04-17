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


class Email(PrimitiveValueObject[str]):
    """Email address value object."""
    
    def validate(self) -> None:
        """Validate email address."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        if "@" not in self.value:
            raise ValueError("Email must contain @")
        if "." not in self.value.split("@")[1]:
            raise ValueError("Email must have a valid domain")
    
    @field_validator('value')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower() if isinstance(v, str) else v


class Money(ValueObject):
    """Money value object."""
    
    amount: float
    currency: str = "USD"
    
    def validate(self) -> None:
        """Validate money."""
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in {"USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"}:
            raise ValueError(f"Unsupported currency: {self.currency}")
    
    def add(self, other: 'Money') -> 'Money':
        """
        Add money.
        
        Args:
            other: Money to add
            
        Returns:
            New money value
            
        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """
        Subtract money.
        
        Args:
            other: Money to subtract
            
        Returns:
            New money value
            
        Raises:
            ValueError: If currencies don't match or result is negative
        """
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(amount=result, currency=self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        """
        Multiply money by a factor.
        
        Args:
            factor: Factor to multiply by
            
        Returns:
            New money value
            
        Raises:
            ValueError: If factor is negative
        """
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        return Money(amount=self.amount * factor, currency=self.currency)


class Address(ValueObject):
    """Address value object."""
    
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"
    
    def validate(self) -> None:
        """Validate address."""
        if not self.street:
            raise ValueError("Street cannot be empty")
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.zip_code:
            raise ValueError("Zip code cannot be empty")
    
    @property
    def formatted(self) -> str:
        """Return formatted address string."""
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}, {self.country}"
