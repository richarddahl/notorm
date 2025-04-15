# Type Safety in uno Framework

## Overview

The uno framework now features enhanced type safety and validation mechanisms to help catch errors at compile time and runtime. This document explains the key components and how to use them effectively.

## Key Components

### Protocol Definitions

Protocol classes define interfaces that objects must conform to, enabling better static type checking and code completion:

```python
from uno.protocols import SchemaManagerProtocol, FilterManagerProtocol, DBClientProtocol

# Use protocols as type annotations
def process_schema(schema_manager: SchemaManagerProtocol):```

# The IDE and type checker will ensure you're only using methods defined in the protocol
schema = schema_manager.get_schema("view_schema")
```
```

### Generic Types

We use generic types like `PaginatedList[T]` to create type-safe collections:

```python
from uno.schema.schema import PaginatedList
from myapp.models import User

# Create a strongly-typed paginated list of users
class UserListSchema(PaginatedList[User]):```

pass
```

# Type checkers will know that items is a List[User]
users = UserListSchema(items=[user1, user2], total=2, page=1, page_size=10, pages=1)
```

### ValidationContext

The `ValidationContext` class provides structured validation with error accumulation:

```python
from uno.errors import ValidationContext

def validate_user(user_data: dict) -> ValidationContext:```

context = ValidationContext("User")
``````

```
```

if not user_data.get("email"):```

context.add_error("email", "Email is required", "REQUIRED_FIELD")
```
``````

```
```

if "password" in user_data and len(user_data["password"]) < 8:```

context.add_error("password", "Password must be at least 8 characters", "SHORT_PASSWORD")
```
``````

```
```

# Validate nested fields with a nested context
if "address" in user_data:```

address_context = context.nested("address")
if not user_data["address"].get("city"):
    address_context.add_error("city", "City is required", "REQUIRED_FIELD")
```
``````

```
```

return context
```
```

## Enhanced Schema Validation

### Type-Safe Schemas

Schemas now use stronger typing and validation to catch errors early:

```python
from uno.schema.schema import UnoSchema

class UserSchema(UnoSchema):```

id: str
name: str
email: str
age: int
``````

```
```

# Access type information at class level
field_types = UserSchema.get_field_annotations()  # Returns Dict[str, Type]
```
```

### Paginated List Schemas

The framework provides a generic `PaginatedList` for handling collections:

```python
from uno.schema.schema import PaginatedList
from myapp.schemas import UserSchema

# UserListSchema will be a paginated list of UserSchema objects
user_list_schema = schema_manager.get_list_schema(UserSchema)

# Create an instance
result = user_list_schema(```

items=[user1, user2],
total=2,
page=1,
page_size=10,
pages=1
```
)
```

## Filter Validation

Filters now use structured validation for more precise error messages:

```python
# Create filter parameters
filter_params = UserObject.create_filter_params()

# Validate filter parameters
try:```

validated_filters = UserObject.validate_filter_params(filter_params)
```
except ValidationError as e:```

# Access detailed error information
for error in e.validation_errors:```

print(f"Field: {error['field']}, Error: {error['message']}")
```
```
```

## Error Hierarchy

The error system is now more structured:

- `UnoError` - Base error class with error codes and context
- `ValidationError` - For validation failures, including detailed error information
- `SchemaError` - For schema-related errors
- `UnoRegistryError` - For registry-related errors

## Best Practices

1. **Use Protocol Classes**: When defining interfaces, use protocols instead of abstract base classes.
2. **Add Type Annotations**: Always include type annotations for parameters and return values.
3. **Validate Early**: Use the `validate()` method to check data before processing.
4. **Accumulate Errors**: Use `ValidationContext` to collect all errors instead of failing on the first one.
5. **Include Error Codes**: Always include error codes for better client-side error handling.
6. **Leverage Generic Types**: Use generics like `List[T]` and `PaginatedList[T]` for type-safe collections.

## Example: Validating a Business Object

```python
async def create_user(user_data: dict):```

# Create a user object from the data
user = UserObject(**user_data)
``````

```
```

# Validate against the edit schema
validation_context = user.validate("edit_schema")
``````

```
```

# Check for validation errors
if validation_context.has_errors():```

# Handle validation errors
return {"errors": validation_context.errors}
```
``````

```
```

# Save the user
saved_user = await user.save()
``````

```
```

return saved_user
```
```