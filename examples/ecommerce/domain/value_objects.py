"""
Value objects for the e-commerce domain.

This module contains value objects that represent concepts in the e-commerce domain
that are defined by their attributes rather than identity.
"""

from typing import List, Optional
from datetime import date

from uno.domain.core import ValueObject


class Money(ValueObject):
    """
    Money value object representing a monetary amount in a specific currency.
    
    Money is immutable and operates using value semantics - two money objects with
    the same amount and currency are considered equal.
    """
    
    amount: float
    currency: str = "USD"
    
    def __add__(self, other: "Money") -> "Money":
        """Add two money objects together."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add money in {self.currency} to {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        """Subtract one money object from another."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract money in {other.currency} from {self.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)
    
    def __mul__(self, factor: float) -> "Money":
        """Multiply money by a factor."""
        return Money(amount=self.amount * factor, currency=self.currency)
    
    def __lt__(self, other: "Money") -> bool:
        """Check if this money amount is less than another."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money in {self.currency} to {other.currency}")
        return self.amount < other.amount
    
    def __gt__(self, other: "Money") -> bool:
        """Check if this money amount is greater than another."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money in {self.currency} to {other.currency}")
        return self.amount > other.amount
    
    def is_zero(self) -> bool:
        """Check if the money amount is zero."""
        return self.amount == 0
    
    def is_positive(self) -> bool:
        """Check if the money amount is positive."""
        return self.amount > 0
    
    def is_negative(self) -> bool:
        """Check if the money amount is negative."""
        return self.amount < 0
    
    def format(self) -> str:
        """Format the money amount as a string."""
        if self.currency == "USD":
            return f"${self.amount:.2f}"
        return f"{self.amount:.2f} {self.currency}"


class Address(ValueObject):
    """
    Address value object representing a physical location.
    
    Addresses are immutable and don't have a specific identity - they are
    defined entirely by their properties.
    """
    
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "USA"
    
    def format(self) -> str:
        """Format the address as a single-line string."""
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"
    
    def format_multi_line(self) -> List[str]:
        """Format the address as multiple lines."""
        return [
            self.street,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country
        ]


class Rating(ValueObject):
    """
    Rating value object representing a customer's product rating.
    
    Ratings include a numeric score and optional text feedback.
    """
    
    score: int  # 1-5 stars
    comment: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize the rating, validating the score range."""
        super().__init__(**data)
        if not 1 <= self.score <= 5:
            raise ValueError("Rating score must be between 1 and 5")


class EmailAddress(ValueObject):
    """
    Email address value object with validation.
    
    Email addresses are represented as their own value object to
    encapsulate validation and formatting logic.
    """
    
    address: str
    
    def __init__(self, **data):
        """Initialize the email address with validation."""
        super().__init__(**data)
        if "@" not in self.address or "." not in self.address:
            raise ValueError(f"Invalid email address: {self.address}")
    
    def domain(self) -> str:
        """Get the domain part of the email address."""
        return self.address.split("@")[1]
    
    def username(self) -> str:
        """Get the username part of the email address."""
        return self.address.split("@")[0]


class PhoneNumber(ValueObject):
    """
    Phone number value object with formatting and validation.
    
    Phone numbers are represented as their own value object to
    encapsulate formatting and validation logic.
    """
    
    number: str
    country_code: str = "1"  # Default to US
    
    def __init__(self, **data):
        """Initialize the phone number with validation."""
        super().__init__(**data)
        # Strip all non-digits
        self.number = "".join(c for c in self.number if c.isdigit())
        if len(self.number) < 10:
            raise ValueError(f"Invalid phone number: {self.number}")
    
    def format(self) -> str:
        """Format the phone number as a string."""
        if len(self.number) == 10:  # US number
            return f"({self.number[0:3]}) {self.number[3:6]}-{self.number[6:10]}"
        return f"+{self.country_code} {self.number}"


class CreditCard(ValueObject):
    """
    Credit card value object representing payment information.
    
    Credit cards are immutable and include validation logic.
    """
    
    number: str
    expiry_month: int
    expiry_year: int
    holder_name: str
    
    def __init__(self, **data):
        """Initialize the credit card with validation."""
        super().__init__(**data)
        # Strip all non-digits from the number
        self.number = "".join(c for c in self.number if c.isdigit())
        if len(self.number) < 13 or len(self.number) > 19:
            raise ValueError("Invalid credit card number length")
        if not 1 <= self.expiry_month <= 12:
            raise ValueError("Invalid expiry month")
        
    def is_expired(self, current_date: Optional[date] = None) -> bool:
        """Check if the credit card is expired."""
        if current_date is None:
            current_date = date.today()
        
        if self.expiry_year < current_date.year:
            return True
        if self.expiry_year == current_date.year and self.expiry_month < current_date.month:
            return True
        return False
    
    def masked_number(self) -> str:
        """Get the masked credit card number for display."""
        return f"{'*' * (len(self.number) - 4)}{self.number[-4:]}"