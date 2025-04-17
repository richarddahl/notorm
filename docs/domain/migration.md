# Domain Model Migration Guide

This document explains how to migrate from the legacy domain model implementation to the new standardized implementation in the uno framework.

## Overview

The uno framework has updated its domain model implementation to follow modern Python practices and provide a more comprehensive domain-driven design (DDD) experience. This guide will help you migrate your code to use the new implementation.

## Key Changes

1. **Module Organization**: Domain model components are now organized into separate modules:
   - `uno.domain.models`: Core domain model classes (Entity, ValueObject, etc.)
   - `uno.domain.protocols`: Protocol interfaces for domain components
   - `uno.domain.specifications`: Specification pattern implementation
   - `uno.domain.factories`: Factory pattern implementation

2. **Protocol-Based Interfaces**: Domain components now use Python's Protocol system for interfaces, enabling better type checking and code completion.

3. **Enhanced Value Objects**: Value objects are now implemented with enhanced validation and equality semantics.

4. **Specification Pattern**: Business rules can now be expressed as specifications and combined using logical operators.

5. **Factory Pattern**: Entity and value object creation is now standardized using the factory pattern.

6. **Command Results**: A standardized way to return results from domain operations, including success/failure status and domain events.

7. **Comprehensive Type Hints**: All components have comprehensive type hints for better developer experience and static analysis.

## Migration Steps

### 1. Update Imports

Replace imports from `uno.domain.core` with the appropriate new module:

```python
# Old imports
from uno.domain.core import Entity, ValueObject, AggregateRoot, DomainEvent

# New imports
from uno.domain.models import Entity, ValueObject, AggregateRoot, DomainEvent
```

For protocol interfaces:

```python
from uno.domain.protocols import EntityProtocol, ValueObjectProtocol
```

### 2. Update Entity Definitions

Entity definitions should use the new base classes:

```python
# Old definition
from uno.domain.core import Entity

class User(Entity):
    def __init__(self, id, username, email):
        super().__init__(id=id)
        self.username = username
        self.email = email

# New definition
from uno.domain.models import Entity

class User(Entity):
    username: str
    email: str
```

### 3. Update Value Object Definitions

Value objects should use the new base classes:

```python
# Old definition
from uno.domain.core import ValueObject

class Address(ValueObject):
    def __init__(self, street, city, state, zip_code):
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code

# New definition
from uno.domain.models import ValueObject

class Address(ValueObject):
    street: str
    city: str
    state: str
    zip_code: str
    
    def validate(self) -> None:
        if not self.street or not self.city:
            raise ValueError("Street and city are required")
```

### 4. Update Event Handling

The event handling methods have been updated:

```python
# Old code
entity.register_domain_event(event)
events = entity.get_domain_events()

# New code
entity.register_event(event)
events = entity.clear_events()
```

### 5. Use Specifications for Business Rules

Instead of imperative business rules, use the specification pattern:

```python
# Old code
def is_active_admin(user):
    return user.is_active and user.role == "admin"

active_admins = [user for user in users if is_active_admin(user)]

# New code
from uno.domain.specifications import Specification

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, entity: User) -> bool:
        return entity.is_active

class AdminUserSpecification(Specification[User]):
    def is_satisfied_by(self, entity: User) -> bool:
        return entity.role == "admin"

# Combine specifications
active_admin_spec = ActiveUserSpecification().and_(AdminUserSpecification())

# Use the specification
active_admins = [user for user in users if active_admin_spec.is_satisfied_by(user)]
```

### 6. Use Factories for Entity Creation

Instead of direct instantiation, use factories for entity creation:

```python
# Old code
user = User(id="user-1", username="johndoe", email="john@example.com")

# New code
from uno.domain.factories import create_entity_factory

UserFactory = create_entity_factory(User)
user = UserFactory.create(username="johndoe", email="john@example.com")
```

### 7. Use Command Results for Operations

Return standardized command results from domain operations:

```python
# Old code
def create_user(username, email):
    try:
        user = User(id=str(uuid4()), username=username, email=email)
        # Save user...
        return user
    except Exception as e:
        return None

# New code
from uno.domain.models import CommandResult

def create_user(username, email):
    try:
        user = UserFactory.create(
            username=username,
            email=email
        )
        user.register_event(UserCreatedEvent(
            user_id=str(user.id),
            username=username
        ))
        # Save user...
        return CommandResult.success(user.clear_events())
    except Exception as e:
        return CommandResult.failure(e)
```

## Common Value Objects

The new implementation provides several common value objects ready to use:

```python
from uno.domain.models import Email, Money, Address

# Create and validate email
email = Email(value="user@example.com")

# Create and validate money
price = Money(amount=29.99, currency="USD")

# Create and validate address
address = Address(
    street="123 Main St",
    city="Anytown",
    state="CA",
    postal_code="12345",
    country="US"
)
```

## Best Practices

1. **Prefer Direct Imports**: Import domain components directly from their specific modules rather than from `uno.domain`.

2. **Use Protocol Interfaces**: Use protocol interfaces for type hints in function signatures:

   ```python
   from uno.domain.protocols import EntityProtocol
   
   def process_entity(entity: EntityProtocol) -> None:
       # Process the entity
   ```

3. **Implement Validations**: Always implement the `validate()` method in value objects to ensure they represent valid concepts.

4. **Use Factory Methods**: Create factory methods for complex entity creation logic:

   ```python
   class UserFactory(EntityFactory[User]):
       @classmethod
       def create_admin(cls, username: str, email: str) -> User:
           user = cls.create(
               username=username,
               email=email,
               role="admin",
               is_active=True
           )
           user.register_event(AdminUserCreatedEvent(
               user_id=str(user.id),
               username=username
           ))
           return user
   ```

5. **Combine Specifications**: Create complex business rules by combining simple specifications:

   ```python
   active_users = ActiveUserSpecification()
   premium_users = PremiumUserSpecification()
   
   # Active premium users
   active_premium_users = active_users.and_(premium_users)
   
   # Active users or premium users
   active_or_premium_users = active_users.or_(premium_users)
   
   # Not active users
   inactive_users = active_users.not_()
   ```

## Automatic Migration

You can use the `modernize_domain.py` script to automatically migrate your codebase:

```shell
python src/scripts/modernize_domain.py
```

This script will:
1. Find all Python files in your project
2. Update imports to use the new domain model modules
3. Update class definitions to extend the new base classes
4. Update method calls to match the new interfaces

For files with complex or custom logic, you may need to manually review and update the code.

## Compatibility

The legacy domain model implementation is still available for backward compatibility but is deprecated and will be removed in a future version. All imports from `uno.domain.core` will show deprecation warnings.