# Implementing Type Safety

## Introduction

This guide explains how to implement type safety in your code when extending uno. Following these guidelines will help catch errors at compile time and make your code more maintainable.

## Using Protocols

### When to Use Protocols

Use protocols when:

1. You want to define an interface that multiple classes can implement
2. You need to describe the structure of an object without inheritance
3. You want to enable static type checking for duck-typed objects

### Creating a Protocol

```python
from typing import Protocol, runtime_checkable, Dict, Any, Optional

@runtime_checkable
class DataProviderProtocol(Protocol):```

"""Protocol for data provider objects."""
``````

```
```

async def get_data(self, key: str) -> Optional[Dict[str, Any]]:```

"""Get data by key."""
...
```
``````

```
```

async def set_data(self, key: str, value: Dict[str, Any]) -> None:```

"""Set data by key."""
...
```
``````

```
```

async def delete_data(self, key: str) -> bool:```

"""Delete data by key."""
...
```
```
```

### Using a Protocol

```python
class CacheService:```

def __init__(self, provider: DataProviderProtocol):```

self.provider = provider
```
    
async def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:```

return await self.provider.get_data(key)
```
```
```

## Generic Types

### When to Use Generics

Use generics when:

1. You need to create containers or collections of a specific type
2. You want to reuse logic across different types
3. You need to maintain type information through a transformation

### Creating Generic Classes

```python
from typing import Generic, TypeVar, List

T = TypeVar('T')

class ResultSet(Generic[T]):```

"""A generic result set that maintains type information."""
``````

```
```

def __init__(self, items: List[T], total: int):```

self.items = items
self.total = total
```
    
def first(self) -> T:```

"""Get the first item."""
if not self.items:
    raise IndexError("Result set is empty")
return self.items[0]
```
```
```

### Using Generic Classes

```python
from myapp.models import User

# Type checkers will know this is a ResultSet[User]
user_results = ResultSet[User](items=[user1, user2], total=2)

# Type checkers will know this is a User
first_user = user_results.first()
```

## Type Variables and Bounds

### Bounded Type Variables

Use bounded type variables to restrict the types that can be used:

```python
from typing import TypeVar, List
from uno.model import UnoModel

# T must be a subclass of UnoModel
T = TypeVar('T', bound=UnoModel)

def get_table_name(model_class: Type[T]) -> str:```

"""Get the table name for a model class."""
return model_class.__tablename__
```
```

### Covariant and Contravariant Type Variables

Use covariance and contravariance to express subtype relationships:

```python
from typing import TypeVar, Protocol, List

# Covariant type variable (can use subtypes)
T_co = TypeVar('T_co', covariant=True)

# Contravariant type variable (can use supertypes)
T_contra = TypeVar('T_contra', contravariant=True)

class Producer(Protocol[T_co]):```

def produce(self) -> T_co:```

...
```
```

class Consumer(Protocol[T_contra]):```

def consume(self, item: T_contra) -> None:```

...
```
```
```

## ValidationContext Usage

### Creating a Validation Context

```python
from uno.errors import ValidationContext

def validate_product(product_data: dict) -> ValidationContext:```

context = ValidationContext("Product")
``````

```
```

# Validate required fields
if not product_data.get("name"):```

context.add_error("name", "Name is required", "REQUIRED_FIELD")
```
``````

```
```

if not product_data.get("price"):```

context.add_error("price", "Price is required", "REQUIRED_FIELD")
```
elif product_data["price"] <= 0:```

context.add_error("price", "Price must be positive", "INVALID_VALUE", product_data["price"])
```
``````

```
```

# Validate nested fields
if "category" in product_data:```

category_context = context.nested("category")
if not product_data["category"].get("id"):
    category_context.add_error("id", "Category ID is required", "REQUIRED_FIELD")
```
``````

```
```

return context
```
```

### Using the Validation Context

```python
def create_product_handler(product_data: dict):```

# Validate the product data
context = validate_product(product_data)
``````

```
```

# Check for validation errors
if context.has_errors():```

return {"status": "error", "errors": context.errors}
```
``````

```
```

# Create the product
product = Product(**product_data)
product.save()
``````

```
```

return {"status": "success", "product": product.to_dict()}
```
```

## Error Handling

### Creating Custom Error Types

```python
from uno.errors import UnoError

class ProductError(UnoError):```

"""Error related to product operations."""
pass
```

class ProductNotFoundError(ProductError):```

"""Error raised when a product is not found."""
``````

```
```

def __init__(self, product_id: str):```

super().__init__(
    f"Product with ID {product_id} not found",
    "PRODUCT_NOT_FOUND",
    product_id=product_id
)
```
```
```

### Using Custom Error Types

```python
async def get_product(product_id: str) -> Product:```

product = await Product.get(id=product_id)
if not product:```

raise ProductNotFoundError(product_id)
```
return product
```
```

## Testing Type Safety

### Creating Type Tests

```python
import pytest
from typing import get_origin, get_args
from myapp.schemas import ProductListSchema

def test_product_list_schema():```

"""Test that ProductListSchema maintains type information."""
``````

```
```

# Check that items field is a List[ProductSchema]
items_field = ProductListSchema.model_fields["items"]
assert get_origin(items_field.annotation) == list
``````

```
```

item_type = get_args(items_field.annotation)[0]
assert item_type.__name__ == "ProductSchema"
```
```

### Testing Validation

```python
def test_product_validation():```

"""Test that product validation works correctly."""
``````

```
```

# Create invalid product data
invalid_data = {```

"name": "",  # Empty name
"price": -10  # Negative price
```
}
``````

```
```

# Validate the data
context = validate_product(invalid_data)
``````

```
```

# Check that validation failed
assert context.has_errors()
``````

```
```

# Check specific errors
errors_by_field = {error["field"]: error for error in context.errors}
assert "name" in errors_by_field
assert errors_by_field["name"]["error_code"] == "REQUIRED_FIELD"
``````

```
```

assert "price" in errors_by_field
assert errors_by_field["price"]["error_code"] == "INVALID_VALUE"
```
```

## Best Practices

1. **Be Explicit with Types**: Always add type annotations to function parameters and return values.
2. **Prefer Protocol over ABC**: Use Protocol for interface definitions to enable static type checking without inheritance.
3. **Use Type Variables**: Use TypeVar to create generic functions and classes.
4. **Validate Early**: Validate data as early as possible in the processing chain.
5. **Accumulate Errors**: Collect all validation errors instead of failing on the first one.
6. **Test Type Safety**: Write tests to ensure type safety is maintained.
7. **Document Types**: Document the expected types in docstrings.
8. **Use mypy**: Run mypy regularly to catch type errors.
9. **Avoid Any**: Minimize the use of `Any` type, which disables type checking.
10. **Be Consistent**: Follow a consistent pattern for type annotations throughout your codebase.