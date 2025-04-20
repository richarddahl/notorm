# Value Objects in UNO

This document explains Value Objects in the UNO framework's domain entity package. It covers what value objects are, how to implement them, and best practices for their use.

## Overview

Value Objects are a fundamental building block in Domain-Driven Design. Unlike entities, which have identity, value objects are defined by their attributes and are immutable. In the UNO framework, value objects are implemented in the `uno.domain.entity` module.

Key characteristics of Value Objects:
- **No identity**: Value objects don't have a unique identifier
- **Immutability**: Once created, value objects cannot be changed
- **Value equality**: Two value objects with the same attributes are considered equal
- **Self-validation**: Value objects validate their own data
- **Domain behavior**: Value objects can contain methods for domain operations

## Implementation

### Basic Value Object

```python
from uno.domain.entity import ValueObject
from pydantic import field_validator
from decimal import Decimal

class Money(ValueObject):
    """Represents a monetary value with currency."""
    
    amount: Decimal
    currency: str
    
    @field_validator('amount')
    def validate_amount(cls, value):
        """Validate the amount."""
        if value < 0:
            raise ValueError("Amount cannot be negative")
        return value
    
    @field_validator('currency')
    def validate_currency(cls, value):
        """Validate the currency code."""
        if len(value) != 3:
            raise ValueError("Currency must be a 3-letter code")
        return value.upper()
    
    def add(self, other: "Money") -> "Money":
        """Add another Money value."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        
        return Money(
            amount=self.amount + other.amount,
            currency=self.currency
        )
    
    def multiply(self, factor: Decimal) -> "Money":
        """Multiply by a factor."""
        return Money(
            amount=self.amount * factor,
            currency=self.currency
        )
    
    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
```

### Advanced Value Objects

You can create more complex value objects with composition:

```python
from uno.domain.entity import ValueObject
from pydantic import field_validator
from typing import List

class Address(ValueObject):
    """Represents a postal address."""
    
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    
    @field_validator('postal_code')
    def validate_postal_code(cls, value):
        """Validate postal code format."""
        # Simplified validation
        if not value.strip():
            raise ValueError("Postal code cannot be empty")
        return value
    
    def __str__(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"

class PhoneNumber(ValueObject):
    """Represents a phone number."""
    
    country_code: str
    number: str
    
    def __str__(self) -> str:
        return f"+{self.country_code} {self.number}"

class ContactInfo(ValueObject):
    """Represents contact information with address and phone numbers."""
    
    primary_address: Address
    phone_numbers: list[PhoneNumber] = []
    email: str
    
    @field_validator('email')
    def validate_email(cls, value):
        """Validate email format."""
        if '@' not in value:
            raise ValueError("Invalid email format")
        return value.lower()
```

## Using Value Objects with Entities

Value objects can be used as attributes in entities:

```python
from uno.domain.entity import EntityBase
from uuid import UUID, uuid4

class Customer(EntityBase[UUID]):
    """A customer entity with value objects."""
    
    name: str
    contact_info: ContactInfo
    
    @classmethod
    def create(cls, name: str, contact_info: ContactInfo) -> "Customer":
        """Create a new customer."""
        return cls(
            id=uuid4(),
            name=name,
            contact_info=contact_info
        )
```

## Value Object Collections

Sometimes you need collections of value objects:

```python
from uno.domain.entity import ValueObject
from typing import List, Optional
from pydantic import field_validator

class LineItem(ValueObject):
    """Represents an order line item."""
    
    product_id: UUID
    quantity: int
    unit_price: Money
    
    @field_validator('quantity')
    def validate_quantity(cls, value):
        """Validate quantity."""
        if value <= 0:
            raise ValueError("Quantity must be positive")
        return value
    
    def total_price(self) -> Money:
        """Calculate the total price."""
        return self.unit_price.multiply(Decimal(self.quantity))

class OrderItems(ValueObject):
    """A collection of order items with business methods."""
    
    items: list[LineItem] = []
    
    def add_item(self, item: LineItem) -> "OrderItems":
        """Add an item to the collection."""
        # Create a new collection with the added item
        return OrderItems(items=self.items + [item])
    
    def remove_item(self, index: int) -> "OrderItems":
        """Remove an item from the collection."""
        if index < 0 or index >= len(self.items):
            raise IndexError("Item index out of range")
        
        new_items = self.items.copy()
        new_items.pop(index)
        return OrderItems(items=new_items)
    
    def total(self) -> Optional[Money]:
        """Calculate the total price of all items."""
        if not self.items:
            return None
        
        result = self.items[0].total_price()
        for item in self.items[1:]:
            result = result.add(item.total_price())
        
        return result
```

## Domain Logic in Value Objects

Value objects can encapsulate domain logic:

```python
from uno.domain.entity import ValueObject
from datetime import date, timedelta
from pydantic import field_validator

class DateRange(ValueObject):
    """Represents a range of dates."""
    
    start_date: date
    end_date: date
    
    @field_validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end_date is after start_date."""
        if 'start_date' in values.data and v < values.data['start_date']:
            raise ValueError("End date must be after start date")
        return v
    
    def overlaps(self, other: "DateRange") -> bool:
        """Check if this date range overlaps with another."""
        return (
            self.start_date <= other.end_date and
            other.start_date <= self.end_date
        )
    
    def contains(self, date_to_check: date) -> bool:
        """Check if this date range contains a specific date."""
        return self.start_date <= date_to_check <= self.end_date
    
    def length_in_days(self) -> int:
        """Calculate the length of the date range in days."""
        return (self.end_date - self.start_date).days + 1
    
    def as_list(self) -> list[date]:
        """Return all dates in this range as a list."""
        days = self.length_in_days()
        return [self.start_date + timedelta(days=i) for i in range(days)]
```

## Identity vs. Value Objects

Understanding when to use entities vs. value objects:

| Entity | Value Object |
| ------ | ------------ |
| Has identity | Defined by attributes |
| Mutable | Immutable |
| Compared by ID | Compared by value |
| "Is a" relationship | "Has a" relationship |
| Example: User, Order | Example: Money, Address |

## Immutability and Modification

Value objects are immutable, so "modifications" create new instances:

```python
# Incorrect - value objects are immutable
money = Money(amount=Decimal("10.00"), currency="USD")
money.amount = Decimal("20.00")  # This would raise an error

# Correct - create a new instance
money = Money(amount=Decimal("10.00"), currency="USD")
doubled_money = Money(amount=money.amount * 2, currency=money.currency)

# Better - use domain methods that return new instances
money = Money(amount=Decimal("10.00"), currency="USD")
doubled_money = money.multiply(Decimal("2"))
```

## Persistence Considerations

When storing value objects in a database:

1. **Embedded in Entity**: Store the value object as part of the entity
   ```python
   class OrderModel(UnoModel):
       id = Column(String, primary_key=True)
       customer_id = Column(String)
       # Value objects stored as JSON columns
       shipping_address = Column(JSON)
       billing_address = Column(JSON)
   ```

2. **Value Object Table**: Create a dedicated table for complex value objects
   ```python
   class AddressModel(UnoModel):
       id = Column(String, primary_key=True)
       street = Column(String)
       city = Column(String)
       state = Column(String)
       postal_code = Column(String)
       country = Column(String)
       
       # Reference from entity
       customer_id = Column(String, ForeignKey("customers.id"))
   ```

3. **Custom Serialization**: Implement custom serialization/deserialization
   ```python
   # In repository implementation
   def _serialize_value_object(self, value_object: ValueObject) -> dict:
       return value_object.model_dump()
       
   def _deserialize_value_object(self, data: dict, value_class: Type[ValueObject]) -> ValueObject:
       return value_class.model_validate(data)
   ```

## Best Practices

### Design Recommendations

1. **Make value objects immutable**: Once created, value objects should not be changed
2. **Use self-validation**: Add validation rules for all attributes
3. **Add domain methods**: Include methods for domain operations on the value object
4. **Keep value objects small and focused**: Each value object should represent a single concept
5. **Use composition**: Build complex value objects by composing simpler ones
6. **Override equality methods**: Ensure value-based equality is implemented correctly
7. **Consider serialization**: Make sure value objects can be properly serialized/deserialized

### Example: Value-Based Equality

```python
from uno.domain.entity import ValueObject
from dataclasses import dataclass
from decimal import Decimal

class Amount(ValueObject):
    """Represents an amount with a unit."""
    
    value: Decimal
    unit: str
    
    def __eq__(self, other):
        """Check if this amount equals another."""
        if not isinstance(other, Amount):
            return False
        return self.value == other.value and self.unit == other.unit
    
    def __hash__(self):
        """Hash function for Amount."""
        return hash((self.value, self.unit))
```

### Validation Rules

Always add validation to value objects:

```python
from uno.domain.entity import ValueObject
from pydantic import field_validator, EmailStr
from typing import Optional

class EmailAddress(ValueObject):
    """Email address value object with validation."""
    
    email: EmailStr
    verified: bool = False
    
    @field_validator('email')
    def normalize_email(cls, v):
        """Normalize the email address."""
        return v.lower().strip()
    
    def __str__(self) -> str:
        status = "verified" if self.verified else "unverified"
        return f"{self.email} ({status})"
    
    def with_verification(self, verified: bool = True) -> "EmailAddress":
        """Create a new instance with updated verification status."""
        return EmailAddress(email=self.email, verified=verified)
```

## Real-World Example: E-commerce

Here's how value objects might be used in an e-commerce application:

```python
# Value objects
class ProductCategory(ValueObject):
    name: str
    parent_category: str | None = None

class Price(ValueObject):
    amount: Decimal
    currency: str
    tax_rate: Decimal = Decimal("0.0")
    
    def with_tax(self) -> "Price":
        """Calculate price with tax included."""
        tax_amount = self.amount * self.tax_rate
        return Price(
            amount=self.amount + tax_amount,
            currency=self.currency,
            tax_rate=self.tax_rate
        )
    
    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

class ProductDimensions(ValueObject):
    width: float
    height: float
    depth: float
    unit: str = "cm"
    
    def volume(self) -> float:
        """Calculate volume."""
        return self.width * self.height * self.depth

# Entity using value objects
class Product(EntityBase[UUID]):
    name: str
    description: str
    category: ProductCategory
    price: Price
    dimensions: Optional[ProductDimensions] = None
    is_active: bool = True
    
    def update_price(self, new_price: Price) -> None:
        """Update the product price."""
        self.price = new_price
        self.record_event(ProductPriceUpdated(
            product_id=self.id,
            new_price=float(new_price.amount),
            currency=new_price.currency
        ))
```

## Migration from Legacy Value Objects

If you have legacy value objects that don't follow UNO patterns:

```python
# Legacy value object
class LegacyAddress:
    def __init__(self, street, city, state, postal_code, country):
        self.street = street
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
    
    def format(self):
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"

# Modern UNO value object
class Address(ValueObject):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    
    @classmethod
    def from_legacy(cls, legacy_address: LegacyAddress) -> "Address":
        """Convert from legacy address format."""
        return cls(
            street=legacy_address.street,
            city=legacy_address.city,
            state=legacy_address.state,
            postal_code=legacy_address.postal_code,
            country=legacy_address.country
        )
    
    def format(self) -> str:
        """Format the address."""
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"
```

## Further Reading

- [Domain-Driven Design](https://domaindrivendesign.org/)
- [Value Object Pattern](https://martinfowler.com/bliki/ValueObject.html)
- [Entity Framework](entity_framework.md)
- [Aggregates](aggregates.md)
- [Domain Events](domain_events.md)