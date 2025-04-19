"""
Value objects shared across the e-commerce application bounded contexts.

This module defines value objects that are used across multiple bounded contexts,
ensuring consistent validation and behavior.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import EmailStr, field_validator

from uno.domain.core import ValueObject, PrimitiveValueObject


class Money(ValueObject):
    """Value object representing a monetary amount with currency."""
    
    amount: Decimal
    currency: str = "USD"
    
    def validate(self) -> None:
        """Validate the money value object."""
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in {"USD", "EUR", "GBP", "JPY", "CAD", "AUD"}:
            raise ValueError(f"Unsupported currency: {self.currency}")
    
    def add(self, other: "Money") -> "Money":
        """Add another money value."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add money with different currencies: {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        """Subtract another money value."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract money with different currencies: {self.currency} and {other.currency}")
        result = self.amount - other.amount
        return Money(amount=result, currency=self.currency)
    
    def multiply(self, factor: Decimal) -> "Money":
        """Multiply the amount by a factor."""
        return Money(amount=self.amount * factor, currency=self.currency)
    
    def __str__(self) -> str:
        """String representation of money."""
        # Format based on currency
        if self.currency == "USD":
            return f"${self.amount:.2f}"
        elif self.currency == "EUR":
            return f"€{self.amount:.2f}"
        elif self.currency == "GBP":
            return f"£{self.amount:.2f}"
        else:
            return f"{self.amount:.2f} {self.currency}"


class Email(PrimitiveValueObject[str]):
    """Value object representing an email address."""
    
    def validate(self) -> None:
        """Validate the email address."""
        # Basic validation - for production, Pydantic's EmailStr is better
        if not self.value:
            raise ValueError("Email cannot be empty")
        if "@" not in self.value:
            raise ValueError("Email must contain @")
        if "." not in self.value.split("@")[1]:
            raise ValueError("Email must have a valid domain")
    
    @field_validator("value")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower() if isinstance(v, str) else v


class PhoneNumber(PrimitiveValueObject[str]):
    """Value object representing a phone number."""
    
    def validate(self) -> None:
        """Validate the phone number."""
        if not self.value:
            raise ValueError("Phone number cannot be empty")
        # Simple validation for demonstration - in production, use a more robust approach
        digits = "".join(c for c in self.value if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")


class Address(ValueObject):
    """Value object representing a physical address."""
    
    street1: str
    street2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "US"
    
    def validate(self) -> None:
        """Validate the address."""
        if not self.street1:
            raise ValueError("Street cannot be empty")
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.state:
            raise ValueError("State cannot be empty")
        if not self.postal_code:
            raise ValueError("Postal code cannot be empty")
    
    def format(self) -> str:
        """Format address as a string."""
        lines = [self.street1]
        if self.street2:
            lines.append(self.street2)
        lines.append(f"{self.city}, {self.state} {self.postal_code}")
        lines.append(self.country)
        return "\n".join(lines)


class Percentage(PrimitiveValueObject[Decimal]):
    """Value object representing a percentage value."""
    
    def validate(self) -> None:
        """Validate the percentage."""
        if self.value < 0 or self.value > 100:
            raise ValueError("Percentage must be between 0 and 100")
    
    def apply_to(self, amount: Decimal) -> Decimal:
        """Apply the percentage to an amount."""
        return amount * (self.value / 100)
    
    def __str__(self) -> str:
        """String representation of percentage."""
        return f"{self.value}%"