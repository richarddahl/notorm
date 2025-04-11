# Migrating to Type-Safe Code

## Introduction

This guide explains how to migrate existing code to use the enhanced type safety features of the Uno framework. The migration process can be done incrementally, allowing you to improve type safety gradually.

## Migration Steps

### 1. Add Type Annotations

Start by adding type annotations to function parameters and return values:

#### Before:

```python
def get_user(user_id):
    # Get user from database
    user = User.get(id=user_id)
    return user
```

#### After:

```python
from typing import Optional
from myapp.models import User

def get_user(user_id: str) -> Optional[User]:
    # Get user from database
    user = User.get(id=user_id)
    return user
```

### 2. Replace Generic Types with Specific Types

Replace generic collections with typed collections:

#### Before:

```python
def get_users():
    users = User.filter()
    return {
        "items": users,
        "total": len(users)
    }
```

#### After:

```python
from typing import List, Dict, Any
from myapp.models import User
from uno.schema.schema import PaginatedList

def get_users() -> PaginatedList[User]:
    users = User.filter()
    return PaginatedList(
        items=users,
        total=len(users),
        page=1,
        page_size=len(users),
        pages=1
    )
```

### 3. Replace Class Inheritance with Protocols

Replace abstract base classes with protocols:

#### Before:

```python
from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def get(self, id):
        pass
    
    @abstractmethod
    def save(self, entity):
        pass

class UserRepository(Repository):
    def get(self, id):
        # Implementation
        pass
    
    def save(self, entity):
        # Implementation
        pass
```

#### After:

```python
from typing import Protocol, TypeVar, Any, Optional, runtime_checkable

T = TypeVar('T')

@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    def get(self, id: str) -> Optional[T]:
        ...
    
    def save(self, entity: T) -> T:
        ...

class UserRepository:
    def get(self, id: str) -> Optional[User]:
        # Implementation
        pass
    
    def save(self, entity: User) -> User:
        # Implementation
        pass

# Type checking will verify that UserRepository implements RepositoryProtocol
repo: RepositoryProtocol[User] = UserRepository()
```

### 4. Improve Error Handling

Replace generic exceptions with structured error classes:

#### Before:

```python
def create_user(user_data):
    try:
        # Validate user data
        if not user_data.get("email"):
            raise Exception("Email is required")
        
        # Create user
        user = User(**user_data)
        user.save()
        return user
    except Exception as e:
        # Handle error
        return {"error": str(e)}
```

#### After:

```python
from uno.errors import ValidationContext, ValidationError

def create_user(user_data: Dict[str, Any]) -> Union[User, Dict[str, Any]]:
    # Create validation context
    context = ValidationContext("User")
    
    # Validate user data
    if not user_data.get("email"):
        context.add_error("email", "Email is required", "REQUIRED_FIELD")
    
    # Check for validation errors
    if context.has_errors():
        return {"errors": context.errors}
    
    # Create user
    user = User(**user_data)
    user.save()
    return user
```

### 5. Update Schema Definitions

Update schema definitions to use the enhanced schema classes:

#### Before:

```python
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    age: int
```

#### After:

```python
from uno.schema.schema import UnoSchema

class UserSchema(UnoSchema):
    id: str
    name: str
    email: str
    age: int
    
    # Now you can use the enhanced schema methods
    @classmethod
    def get_required_fields(cls) -> Set[str]:
        return {
            name for name, field in cls.model_fields.items() 
            if field.is_required()
        }
```

### 6. Convert to Type-Safe Query Methods

Update query methods to use type-safe filters and return types:

#### Before:

```python
def search_users(filters):
    query = User.objects.all()
    
    if "name" in filters:
        query = query.filter(name__contains=filters["name"])
    
    return query
```

#### After:

```python
from typing import List
from myapp.models import User
from myapp.filters import UserFilter

def search_users(filters: UserFilter) -> List[User]:
    # Validate filters
    validated_filters = User.validate_filter_params(filters)
    
    # Perform query with validated filters
    return User.filter(filters=validated_filters)
```

### 7. Implement Validation Contexts

Replace ad-hoc validation with structured validation contexts:

#### Before:

```python
def validate_product(product_data):
    errors = []
    
    if not product_data.get("name"):
        errors.append("Name is required")
    
    if not product_data.get("price"):
        errors.append("Price is required")
    elif product_data["price"] <= 0:
        errors.append("Price must be positive")
    
    return errors
```

#### After:

```python
from uno.errors import ValidationContext

def validate_product(product_data: Dict[str, Any]) -> ValidationContext:
    context = ValidationContext("Product")
    
    if not product_data.get("name"):
        context.add_error("name", "Name is required", "REQUIRED_FIELD")
    
    if not product_data.get("price"):
        context.add_error("price", "Price is required", "REQUIRED_FIELD")
    elif product_data["price"] <= 0:
        context.add_error("price", "Price must be positive", "INVALID_VALUE", product_data["price"])
    
    # Validate nested fields
    if "category" in product_data:
        category_context = context.nested("category")
        if not product_data["category"].get("id"):
            category_context.add_error("id", "Category ID is required", "REQUIRED_FIELD")
    
    return context
```

## Testing Migration Success

### Running Type Checkers

Use mypy to check for type errors:

```bash
mypy --install-types --non-interactive src/uno tests
```

### Adding Migration Tests

Create tests to verify that your migrated code works correctly:

```python
import pytest
from typing import get_origin, get_args
from myapp.schemas import UserSchema, UserListSchema

def test_user_schema_types():
    """Test that user schemas maintain type information."""
    
    # Check field annotations
    annotations = UserSchema.get_field_annotations()
    assert annotations["id"] == str
    assert annotations["name"] == str
    assert annotations["email"] == str
    assert annotations["age"] == int
    
    # Check list schema
    items_field = UserListSchema.model_fields["items"]
    assert get_origin(items_field.annotation) == list
    assert get_args(items_field.annotation)[0] == UserSchema
```

## Migration Checklist

- [ ] Add type annotations to function parameters and return values
- [ ] Replace generic collections with typed collections
- [ ] Replace abstract base classes with protocols
- [ ] Improve error handling with structured error classes
- [ ] Update schema definitions to use enhanced schema classes
- [ ] Convert to type-safe query methods
- [ ] Implement validation contexts
- [ ] Add tests to verify type safety
- [ ] Run type checkers to catch errors
- [ ] Update documentation to reflect type information

## Tips for Successful Migration

1. **Start Small**: Begin with a small, self-contained module to understand the process.
2. **Add Tests First**: Write tests that verify type safety before making changes.
3. **Use Type Annotations Gradually**: Start with function signatures, then move to variables.
4. **Run Type Checkers Regularly**: Run mypy frequently to catch errors early.
5. **Update Documentation**: Document the types you're using to help other developers.
6. **Combine with Refactoring**: Use the migration as an opportunity to improve code quality.
7. **Use IDE Support**: Modern IDEs can help identify type issues and suggest annotations.
8. **Be Pragmatic**: Focus on high-value areas first, such as public APIs and complex logic.