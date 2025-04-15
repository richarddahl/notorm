# Validation Framework

The Uno framework provides a comprehensive validation framework that integrates with the error handling system, allowing for structured validation with detailed error reporting.

## Core Concepts

- **Validation Context**: A container for collecting validation errors during validation
- **Field Validation Errors**: Structured errors with field paths, messages, and error codes
- **Nested Validation**: Support for validating nested structures
- **Integration with Error Handling**: Validation errors are raised as `ValidationError` instances

## Using Validation Context

### Basic Validation

```python
from uno.core.errors import ValidationContext, ValidationError

def validate_user(user):```

context = ValidationContext("User")
``````

```
```

# Validate username
if not user.username:```

context.add_error(
    field="username",
    message="Username is required",
    error_code="FIELD_REQUIRED"
)
```
elif len(user.username) < 3:```

context.add_error(
    field="username",
    message="Username must be at least 3 characters",
    error_code="FIELD_INVALID",
    value=user.username
)
```
``````

```
```

# Validate email
if not user.email:```

context.add_error(
    field="email",
    message="Email is required",
    error_code="FIELD_REQUIRED"
)
```
elif "@" not in user.email:```

context.add_error(
    field="email",
    message="Invalid email format",
    error_code="FIELD_INVALID",
    value=user.email
)
```
``````

```
```

# Raise if there are any errors
context.raise_if_errors()
```
```

### Nested Validation

```python
def validate_user_with_address(user):```

context = ValidationContext("User")
``````

```
```

# Validate username
if not user.username:```

context.add_error(
    field="username",
    message="Username is required",
    error_code="FIELD_REQUIRED"
)
```
``````

```
```

# Validate address (nested)
if user.address:```

# Create a nested context for address
address_context = context.nested("address")
``````

```
```

# Validate street
if not user.address.street:
    address_context.add_error(
        field="street",
        message="Street is required",
        error_code="FIELD_REQUIRED"
    )
``````

```
```

# Validate city
if not user.address.city:
    address_context.add_error(
        field="city",
        message="City is required",
        error_code="FIELD_REQUIRED"
    )
``````

```
```

# Validate zip code
if not user.address.zip_code:
    address_context.add_error(
        field="zip_code",
        message="Zip code is required",
        error_code="FIELD_REQUIRED"
    )
elif not user.address.zip_code.isdigit():
    address_context.add_error(
        field="zip_code",
        message="Zip code must contain only digits",
        error_code="FIELD_INVALID",
        value=user.address.zip_code
    )
```
else:```

context.add_error(
    field="address",
    message="Address is required",
    error_code="FIELD_REQUIRED"
)
```
``````

```
```

# Raise if there are any errors
context.raise_if_errors()
```
```

### Multiple Levels of Nesting

```python
def validate_order(order):```

context = ValidationContext("Order")
``````

```
```

# Validate order ID
if not order.id:```

context.add_error(
    field="id",
    message="Order ID is required",
    error_code="FIELD_REQUIRED"
)
```
``````

```
```

# Validate customer
if order.customer:```

customer_context = context.nested("customer")
``````

```
```

# Validate customer name
if not order.customer.name:
    customer_context.add_error(
        field="name",
        message="Customer name is required",
        error_code="FIELD_REQUIRED"
    )
``````

```
```

# Validate customer address
if order.customer.address:
    address_context = customer_context.nested("address")
    
    # Validate address fields
    if not order.customer.address.street:
        address_context.add_error(
            field="street",
            message="Street is required",
            error_code="FIELD_REQUIRED"
        )
else:
    customer_context.add_error(
        field="address",
        message="Customer address is required",
        error_code="FIELD_REQUIRED"
    )
```
else:```

context.add_error(
    field="customer",
    message="Customer is required",
    error_code="FIELD_REQUIRED"
)
```
``````

```
```

# Validate items
if not order.items:```

context.add_error(
    field="items",
    message="Order must have at least one item",
    error_code="FIELD_REQUIRED"
)
```
else:```

for i, item in enumerate(order.items):
    item_context = context.nested(f"items[{i}]")
    
    # Validate item ID
    if not item.id:
        item_context.add_error(
            field="id",
            message="Item ID is required",
            error_code="FIELD_REQUIRED"
        )
    
    # Validate item quantity
    if item.quantity <= 0:
        item_context.add_error(
            field="quantity",
            message="Item quantity must be positive",
            error_code="FIELD_INVALID",
            value=item.quantity
        )
```
``````

```
```

# Raise if there are any errors
context.raise_if_errors()
```
```

### Using validate_fields Utility

```python
from uno.core.errors import validate_fields
from typing import Set, Dict, List, Any, Optional, Callable

def validate_user_data(data: Dict[str, Any]) -> None:```

# Define required fields
required_fields: Set[str] = {"username", "email"}
``````

```
```

# Define validators
def validate_email(value: str) -> Optional[str]:```

if "@" not in value:
    return "Invalid email format"
return None
```
``````

```
```

def validate_username(value: str) -> Optional[str]:```

if len(value) < 3:
    return "Username must be at least 3 characters"
return None
```
``````

```
```

def validate_age(value: int) -> Optional[str]:```

if value < 18:
    return "User must be 18 or older"
return None
```
``````

```
```

# Map fields to validators
validators = {```

"username": [validate_username],
"email": [validate_email],
"age": [validate_age]
```
}
``````

```
```

# Validate fields (raises ValidationError if validation fails)
validate_fields(```

data=data,
required_fields=required_fields,
validators=validators,
entity_name="User"
```
)
```
```

## Handling Validation Errors

### Using Try/Except

```python
from uno.core.errors import ValidationError

try:```

validate_user(user)
# Validation passed
save_user(user)
```
except ValidationError as e:```

# Handle validation errors
print(f"Validation failed: {e.message}")
for error in e.validation_errors:```

print(f"- {error['field']}: {error['message']}")
```
```
```

### Using Result Pattern

```python
from uno.core.errors import Result, of, failure, ValidationError

def create_user(user_data: Dict[str, Any]) -> Result[User]:```

# Create user object
user = User(**user_data)
``````

```
```

# Validate user
try:```

validate_user(user)
```
except ValidationError as e:```

return failure(e)
```
``````

```
```

# User is valid, save to database
try:```

user_id = save_user(user)
user.id = user_id
return of(user)
```
except Exception as e:```

return failure(e)
```
```
```

### Mapping to HTTP Responses

```python
from fastapi import HTTPException
from uno.core.errors import ValidationError

def handle_validation_error(e: ValidationError) -> HTTPException:```

"""Convert ValidationError to HTTP exception."""
return HTTPException(```

status_code=400,
detail={
    "message": e.message,
    "error_code": e.error_code,
    "validation_errors": e.validation_errors
}
```
)
```

@app.post("/users")
async def create_user(user_data: Dict[str, Any]):```

try:```

# Validate user data
validate_user_data(user_data)
```
    ```

# Create user
user = create_user(user_data)
return {"id": user.id}
```
except ValidationError as e:```

# Convert to HTTP exception
raise handle_validation_error(e)
```
```
```

## Best Practices

1. **Use ValidationContext for complex validation**: This enables collecting multiple validation errors.
2. **Provide descriptive error messages**: Error messages should be clear and actionable.
3. **Use appropriate error codes**: Each type of validation error should have a unique error code.
4. **Use nested contexts for nested structures**: This provides clear error paths.
5. **Validate early**: Validate input as early as possible in your application flow.
6. **Return all errors at once**: Avoid returning errors one by one, which forces users to fix issues sequentially.
7. **Include problematic values**: Include the invalid value in error messages to help debug issues.
8. **Match validation to business rules**: Ensure validation rules match your domain's business rules.