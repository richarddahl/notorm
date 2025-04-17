# Domain Models

This document explains the core domain model classes in the `uno` framework.

## Overview

Domain models are the heart of Domain-Driven Design (DDD). They represent the business concepts and rules in a clear, expressive way. The `uno` framework provides a comprehensive set of domain model base classes for implementing DDD patterns.

## Key Components

### DomainEvent

Domain events represent significant occurrences within the domain. They are immutable records of something that happened.

```python
# Example: Creating a domain event
from datetime import datetime, timezone
from uno.domain.models import DomainEvent

class UserCreatedEvent(DomainEvent):
    user_id: str
    username: str

event = UserCreatedEvent(
    user_id="123",
    username="johndoe",
    aggregate_id="123",
    aggregate_type="User"
)
```

Key features:
- Immutable (frozen Pydantic model)
- Standard metadata (event_id, timestamp, etc.)
- Support for serialization/deserialization

### ValueObject

Value objects are immutable objects defined by their attributes. Two value objects are considered equal if all their attributes are equal.

```python
# Example: Creating a value object
from uno.domain.models import ValueObject

class Address(ValueObject):
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    
    def validate(self) -> None:
        if not self.street or not self.city:
            raise ValueError("Street and city are required")

address = Address(
    street="123 Main St",
    city="Anytown",
    state="CA",
    postal_code="12345"
)
```

Key features:
- Immutable (frozen Pydantic model)
- Equality based on attributes, not identity
- Built-in validation support
- Serialization/deserialization methods

### PrimitiveValueObject

A specialized value object that wraps a primitive value, adding domain-specific validation and semantics.

```python
# Example: Creating a primitive value object
from uno.domain.models import PrimitiveValueObject

class Email(PrimitiveValueObject[str]):
    def validate(self) -> None:
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email format")

email = Email(value="user@example.com")
```

Key features:
- Wraps a single primitive value with domain semantics
- Type-safe with generics
- Customizable validation

### Entity

Entities are distinguished by their identity, not their attributes. Two entities are considered equal if they have the same identity, regardless of their attributes.

```python
# Example: Creating an entity
from uno.domain.models import Entity

class User(Entity):
    username: str
    email: str
    is_active: bool = True

user = User(
    id="user-123",
    username="johndoe",
    email="john@example.com"
)
```

Key features:
- Identity-based equality
- Automatic timestamps (created_at, updated_at)
- Support for domain events
- Serialization/deserialization methods

### AggregateRoot

Aggregate roots are entities that serve as the entry point to an aggregate. They ensure the consistency of the aggregate and are the only objects that repositories directly work with.

```python
# Example: Creating an aggregate root
from uno.domain.models import AggregateRoot, Entity

class OrderItem(Entity):
    product_id: str
    quantity: int
    price: float

class Order(AggregateRoot):
    customer_id: str
    status: str = "pending"
    
    def check_invariants(self) -> None:
        # Ensure that an order has at least one item
        if not any(isinstance(e, OrderItem) for e in self.get_child_entities()):
            raise ValueError("An order must have at least one item")
    
    def add_item(self, item: OrderItem) -> None:
        self.add_child_entity(item)
        self.update()

# Create order and add items
order = Order(id="order-123", customer_id="cust-456")
item = OrderItem(id="item-1", product_id="prod-789", quantity=2, price=29.99)
order.add_item(item)
```

Key features:
- Manages child entities
- Ensures consistency through invariants
- Versioning for optimistic concurrency control
- Collects events from all entities in the aggregate

### CommandResult

Represents the result of executing a command, including success status and produced domain events.

```python
# Example: Using command result
from uno.domain.models import CommandResult

def create_user(username: str, email: str) -> CommandResult:
    try:
        user = User(username=username, email=email)
        user.register_event(UserCreatedEvent(
            user_id=str(user.id),
            username=username
        ))
        # Save user to repository...
        return CommandResult.success(user.clear_events())
    except ValueError as e:
        return CommandResult.failure(e)

# Using the command
result = create_user("johndoe", "john@example.com")
if result.is_success:
    # Process events or return success
    print(f"User created with {len(result.events)} events")
else:
    # Handle error
    print(f"Error: {result.error}")
```

Key features:
- Represents success or failure
- Carries domain events for event-sourcing
- Includes error information for failures

## Common Value Objects

The framework provides several common value objects ready to use:

### Email

```python
from uno.domain.models import Email

email = Email(value="user@example.com")
```

### Money

```python
from uno.domain.models import Money

price = Money(amount=29.99, currency="USD")
discount = Money(amount=5.00, currency="USD")
final_price = price.subtract(discount)  # Money(amount=24.99, currency="USD")
```

### Address

```python
from uno.domain.models import Address

address = Address(
    street="123 Main St",
    city="Anytown",
    state="CA",
    postal_code="12345",
    country="US"
)
```

## Best Practices

1. **Make Value Objects Immutable**: Value objects should be immutable. Once created, they should not change.

2. **Keep Entities Focused**: Entities should be focused on their identity and core attributes.

3. **Define Aggregate Boundaries Carefully**: Aggregate boundaries should be defined to maintain consistency while keeping aggregates as small as possible.

4. **Use Domain Events for Changes**: Domain events should be used to represent changes to entities.

5. **Enforce Invariants**: Aggregate roots should enforce invariants to ensure consistency.

6. **Validate in Value Objects**: Value objects should validate their attributes to ensure they represent valid concepts.

## Implementation Notes

- All domain model classes are built on top of Pydantic's BaseModel
- The implementation uses Python 3.12+ features such as Self type
- Generic types are used extensively for type safety
- Domain events are designed to work with event sourcing patterns
- Command results support the CQRS pattern