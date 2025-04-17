# Domain Specifications

This document explains the specification pattern implementation for domain models in the `uno` framework.

## Overview

The Specification pattern is a pattern that allows you to encapsulate business rules in a single unit – called a specification – that can be reused in different parts of the codebase. It is especially useful for complex querying and for composing business rules.

## Key Components

### Specification Base Class

The `Specification` abstract base class defines the core interface for all specifications:

```python
from uno.domain.specifications import Specification
from uno.domain.models import Entity

class User(Entity):
    username: str
    email: str
    is_active: bool = True
    role: str = "user"

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, entity: User) -> bool:
        return entity.is_active
```

The key method is `is_satisfied_by`, which checks if an entity satisfies the specification.

### Logical Operators

Specifications can be combined using logical operators:

```python
# Define specifications
class AdminUserSpecification(Specification[User]):
    def is_satisfied_by(self, entity: User) -> bool:
        return entity.role == "admin"

# Combine specifications
active_admins = ActiveUserSpecification().and_(AdminUserSpecification())
active_or_admin = ActiveUserSpecification().or_(AdminUserSpecification())
not_active = ActiveUserSpecification().not_()

# Use combined specifications
user = User(username="admin", email="admin@example.com", is_active=True, role="admin")
if active_admins.is_satisfied_by(user):
    print("User is an active admin")
```

### Built-in Specifications

#### AndSpecification

Satisfied when both component specifications are satisfied:

```python
from uno.domain.specifications import AndSpecification

# Explicitly create AND specification
active_and_admin = AndSpecification(
    ActiveUserSpecification(),
    AdminUserSpecification()
)
```

#### OrSpecification

Satisfied when either component specification is satisfied:

```python
from uno.domain.specifications import OrSpecification

# Explicitly create OR specification
active_or_admin = OrSpecification(
    ActiveUserSpecification(),
    AdminUserSpecification()
)
```

#### NotSpecification

Satisfied when the component specification is not satisfied:

```python
from uno.domain.specifications import NotSpecification

# Explicitly create NOT specification
inactive_user = NotSpecification(ActiveUserSpecification())
```

### Predefined Specification Types

#### AttributeSpecification

Checks if an entity's attribute equals a specific value:

```python
from uno.domain.specifications import AttributeSpecification

# Check if user's role is "admin"
admin_spec = AttributeSpecification("role", "admin")

# Use the specification
if admin_spec.is_satisfied_by(user):
    print("User is an admin")
```

#### PredicateSpecification

Uses a predicate function to check an entity:

```python
from uno.domain.specifications import PredicateSpecification

# Check if user's email is from a specific domain
def has_company_email(user: User) -> bool:
    return user.email.endswith("@company.com")

company_email_spec = PredicateSpecification(has_company_email)

# Use the specification
if company_email_spec.is_satisfied_by(user):
    print("User has a company email")
```

#### DictionarySpecification

Checks if a dictionary matches specific conditions:

```python
from uno.domain.specifications import DictionarySpecification

# Check if a dictionary has specific values
admin_role_spec = DictionarySpecification({"role": "admin", "is_active": True})

# Use with a dictionary
user_dict = {"id": "user-1", "username": "admin", "role": "admin", "is_active": True}
if admin_role_spec.is_satisfied_by(user_dict):
    print("Dictionary represents an active admin")
```

### Creating Type-Specific Specifications

The `specification_factory` function creates a specification class for a specific entity type:

```python
from uno.domain.specifications import specification_factory

# Create a User-specific specification class
UserSpecification = specification_factory(User)

# Create specifications using the factory
active_spec = UserSpecification.attribute("is_active", True)
admin_spec = UserSpecification.attribute("role", "admin")

# Combine specifications
active_admin_spec = active_spec.and_(admin_spec)
```

## Use Cases

### Filtering Collections

Specifications are excellent for filtering collections of entities:

```python
users = [
    User(username="user1", email="user1@example.com", is_active=True, role="user"),
    User(username="admin1", email="admin1@example.com", is_active=True, role="admin"),
    User(username="user2", email="user2@example.com", is_active=False, role="user"),
]

# Filter users using a specification
active_admin_spec = ActiveUserSpecification().and_(AdminUserSpecification())
active_admins = [user for user in users if active_admin_spec.is_satisfied_by(user)]
```

### Business Rule Validation

Specifications can represent business rules for validation:

```python
class ValidUserSpecification(Specification[User]):
    def is_satisfied_by(self, entity: User) -> bool:
        # User must have a username with at least 3 characters
        if len(entity.username) < 3:
            return False
        # Email must contain @ and have a domain
        if "@" not in entity.email or "." not in entity.email.split("@")[1]:
            return False
        return True

# Validate user before saving
user = User(username="a", email="invalid")
valid_spec = ValidUserSpecification()
if not valid_spec.is_satisfied_by(user):
    print("User is not valid")
```

### Domain Service Logic

Specifications can encapsulate domain logic in services:

```python
class UserService:
    def __init__(self):
        self.valid_spec = ValidUserSpecification()
        self.active_admin_spec = ActiveUserSpecification().and_(AdminUserSpecification())
    
    def can_delete_user(self, admin: User, user_to_delete: User) -> bool:
        # Only active admins can delete users
        if not self.active_admin_spec.is_satisfied_by(admin):
            return False
        # Cannot delete yourself
        if admin.id == user_to_delete.id:
            return False
        return True
    
    def create_user(self, user: User) -> bool:
        # User must be valid
        if not self.valid_spec.is_satisfied_by(user):
            return False
        # Create user...
        return True
```

### Repository Queries

Specifications can be used in repositories to define query criteria:

```python
class UserRepository:
    def find_by_specification(self, spec: Specification[User]) -> List[User]:
        # In a real implementation, this would query the database
        # For this example, we'll just filter an in-memory list
        users = [/* ... */]
        return [user for user in users if spec.is_satisfied_by(user)]

# Usage
repository = UserRepository()
active_admins = repository.find_by_specification(active_admin_spec)
```

## Best Practices

1. **Keep Specifications Focused**: Each specification should represent a single, well-defined business rule or condition.

2. **Use Composition**: Compose complex specifications from simpler ones using logical operators.

3. **Name Specifications Clearly**: Use descriptive names that reflect the business rules they represent.

4. **Make Specifications Reusable**: Design specifications to be reused across different parts of the application.

5. **Use Type-Specific Factories**: Use the `specification_factory` to create type-specific specification classes.

## Implementation Notes

- The specification pattern is implemented using Python's generic types for type safety
- Specifications use the Composite pattern for logical operators
- The implementation supports both entity and dictionary specifications
- Predicate specifications allow for more complex and dynamic rules