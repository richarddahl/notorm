# Data Transfer Objects (DTOs)

> **Note**: As part of aligning with Domain-Driven Design principles, the schema classes have been renamed to use DTO terminology. This documentation has been updated to reflect these changes. For more details, see the [Schema to DTO Transition](/modernization/dto_transition.md) guide.

The DTO system in uno provides a flexible way to define, validate, and transform data transfer objects for business objects.

## Overview

The DTO system:

- Defines the structure of data transfer between layers
- Validates data against DTO definitions
- Transforms data between different representations
- Supports multiple DTO variants for different use cases

## Key Components

### DTOConfig

The `DTOConfig` class defines the configuration for a DTO:

```python
from uno.dto import DTOConfig

# Create a DTO configuration
view_dto = DTOConfig(
    include_fields={"id", "name", "email"},  # Only include these fields
    exclude_fields={"password"},             # Exclude these fields
    read_only=True                           # DTO is read-only
)
```

### DTOManager

The `DTOManager` class manages DTO configurations and creates DTO models:

```python
from uno.dto import DTOManager, DTOConfig

# Define DTO configurations
dto_configs = {
    "view": DTOConfig(),  # All fields
    "edit": DTOConfig(exclude_fields={"created_at", "modified_at"}),
    "summary": DTOConfig(include_fields={"id", "name", "email"}),
}

# Create a DTO manager
dto_manager = DTOManager(dto_configs)

# Create a DTO model for a business object
view_dto = dto_manager.create_dto("view", Customer)

# Create an object from DTO
customer = view_dto(id="abc123", name="John Doe", email="john@example.com")
```

## Basic Usage

### Defining DTOs in Business Objects

Typically, DTOs are defined as part of the business object class:

```python
from uno.obj import UnoObj
from uno.model import UnoModel
from uno.dto import DTOConfig

class CustomerModel(UnoModel):
    __tablename__ = "customer"
    # Fields...

class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    
    # Define DTO configurations
    dto_configs = {
        "view": DTOConfig(),  # All fields
        "edit": DTOConfig(exclude_fields={"created_at", "modified_at"}),
        "summary": DTOConfig(include_fields={"id", "name", "email"}),
    }
```

### Using DTOs

```python
# Create a customer with the edit DTO
edit_dto = customer.dto_manager.create_dto("edit", Customer)
new_customer = edit_dto(name="John Doe", email="john@example.com")

# Convert to a model instance
model_instance = new_customer.to_model()

# Save to database
await new_customer.save()

# Get a summary representation
summary = customer.to_dict(dto_name="summary")
```

## Advanced Usage

### Custom Field Transformations

You can define custom field transformations:

```python
from uno.dto import DTOConfig, FieldTransformer

# Define a field transformer
class PasswordHasher(FieldTransformer):
    def transform(self, value, obj=None):
        """Transform a password to a hashed value."""
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()

# Create a DTO config with transformers
dto_config = DTOConfig(
    field_transformers={
        "password": PasswordHasher()
    }
)

# Create a DTO
dto = dto_manager.create_dto("register", User, dto_config)

# Create a user with the DTO
user = dto(username="johndoe", password="secret")
# user.password will be hashed
```

### DTO Inheritance

DTOs can inherit from other DTOs:

```python
from uno.dto import DTOConfig

# Base DTO config
base_dto = DTOConfig(
    exclude_fields={"password", "internal_notes"}
)

# Extended DTO config
extended_dto = DTOConfig(
    base_dto=base_dto,
    include_fields={"id", "name", "email", "address"}
)
```

### Dynamic DTOs

You can create DTOs dynamically based on runtime conditions:

```python
from uno.dto import DTOConfig

def get_dto_for_user(user, obj_class):
    """Get a DTO based on user permissions."""
    # Base fields that everyone can see
    base_fields = {"id", "name", "email"}
    
    # Add additional fields based on user permissions
    if user.has_permission("view_phone_numbers"):
        base_fields.add("phone")
    
    if user.has_permission("view_addresses"):
        base_fields.add("address")
    
    # Create a DTO config
    dto_config = DTOConfig(include_fields=base_fields)
    
    # Create and return the DTO
    return dto_manager.create_dto("dynamic", obj_class, dto_config)
```

## Common Patterns

### API Request/Response DTOs

Use DTOs to define API request and response models:

```python
from fastapi import FastAPI, Depends
from uno.dto import DTOManager

app = FastAPI()
dto_manager = DTOManager()

# Create DTOs for API
create_dto = dto_manager.create_dto("edit", Customer)
view_dto = dto_manager.create_dto("view", Customer)

@app.post("/api/customers", response_model=view_dto)
async def create_customer(customer: create_dto):
    """Create a new customer."""
    # Create and save the customer
    new_customer = Customer(**customer.dict())
    await new_customer.save()
    
    # Return the customer as a view DTO
    return new_customer.to_dict(dto_name="view")
```

### Data Validation

Use DTOs to validate data:

```python
from uno.dto import DTOManager
from pydantic import ValidationError

# Create a DTO for validation
dto = dto_manager.create_dto("edit", Customer)

try:
    # Validate data
    validated_data = dto(name="John Doe", email="invalid-email")
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Data Transformation

Use DTOs to transform data between formats:

```python
from uno.dto import DTOManager

# Create DTOs for different formats
internal_dto = dto_manager.create_dto("internal", Customer)
api_dto = dto_manager.create_dto("api", Customer)
database_dto = dto_manager.create_dto("database", Customer)

# Transform between formats
internal_data = internal_dto(**user_input)
api_data = api_dto(**internal_data.dict())
database_data = database_dto(**internal_data.dict())
```

## Best Practices

1. **Define Clear DTOs**: Create clear, well-documented DTOs for different use cases.

2. **Use Consistent Naming**: Use consistent naming for DTOs (e.g., "view", "edit", etc.).

3. **Validate Input**: Always validate input data against DTOs before processing.

4. **Separate Concerns**: Use different DTOs for different concerns (viewing, editing, importing, etc.).

5. **Document DTOs**: Document the purpose and structure of each DTO.

6. **Use Field Exclusion**: Prefer `exclude_fields` over `include_fields` for safer DTO evolution.

7. **Handle Validation Errors**: Implement proper error handling for validation errors.

8. **Test DTOs**: Write tests to ensure DTOs validate and transform data correctly.

9. **Check for Required Fields**: Ensure required fields are present in DTOs.

10. **Use Type Annotations**: Provide proper type annotations for better IDE support and type checking.