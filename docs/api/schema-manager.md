# UnoSchemaManager

The `UnoSchemaManager` class is responsible for creating and managing schemas for `UnoObj` models. It provides a clean interface for defining how model data is presented and validated in different contexts.

## Overview

Schemas in the Uno framework are Pydantic models that define how data is structured when being sent to or received from clients. The `UnoSchemaManager` helps with:

- Creating schemas from model classes
- Managing schema configurations
- Validating schema definitions
- Accessing schemas by name

## Basic Usage

### Creating a Schema Manager

```python
from uno.schema_manager import UnoSchemaManager
from uno.schema import UnoSchemaConfig

# Create schema configurations
schema_configs = {```

"view_schema": UnoSchemaConfig(),  # All fields
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
```
}

# Create the schema manager
schema_manager = UnoSchemaManager(schema_configs)
```

### Creating Schemas for a Model

```python
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

# Define a model
class CustomerModel(UnoModel):```

__tablename__ = "customer"
``````

```
```

name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
```
    
# Define a business object
class Customer(UnoObj):```

model = CustomerModel
# ...
```

# Create schemas for the model
schemas = schema_manager.create_all_schemas(Customer)

# Now you can access the schemas
view_schema = schemas["view_schema"]
edit_schema = schemas["edit_schema"]
```

### Getting a Schema

```python
# Get a schema by name
view_schema = schema_manager.get_schema("view_schema")

if view_schema:```

# Use the schema
customer_data = view_schema(```

name="John Doe",
email="john@example.com"
```
)
```
```

## Advanced Usage

### Custom Schema Configurations

You can create custom schema configurations for different use cases:

```python
from uno.schema import UnoSchemaConfig, UnoSchema

# Define a custom schema base class
class SummarySchema(UnoSchema):```

"""Base class for summary schemas with metadata."""
``````

```
```

class Config:```

json_schema_extra = {
    "description": "A summary view of the data"
}
```
```

# Create configurations with different options
schema_configs = {```

"view_schema": UnoSchemaConfig(),  # All fields
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
``````

"summary_schema": UnoSchemaConfig(
    schema_base=SummarySchema,
    include_fields={"id", "name", "email"}
),
"admin_schema": UnoSchemaConfig(
    exclude_fields={"deleted_at"}
),
```
}

schema_manager = UnoSchemaManager(schema_configs)
```

### Adding Schema Configurations Dynamically

You can add schema configurations after creating the manager:

```python
# Create a manager
schema_manager = UnoSchemaManager()

# Add configurations later
schema_manager.add_schema_config(```

"minimal_schema",
UnoSchemaConfig(include_fields={"id", "name"})
```
)
```

### Creating a Single Schema

```python
# Create just one schema
minimal_schema = schema_manager.create_schema(```

"minimal_schema",
Customer
```
)
```

## Schema Validation

The `UnoSchemaManager` validates schema configurations when creating schemas:

1. It checks that all include/exclude fields exist in the model
2. It ensures that a schema doesn't have both include and exclude fields
3. It verifies that schemas have at least one field

If validation fails, it raises a `UnoError` with a specific error code.

## Integration with UnoObj

The `UnoSchemaManager` is typically used inside `UnoObj` subclasses:

```python
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

```
```

schema_configs = {```

"view_schema": UnoSchemaConfig(),
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
```
}
``````

```
```

def __init__(self, **data):```

super().__init__(**data)
# Schema manager is created with the provided schema_configs
self.schema_manager = UnoSchemaManager(self.__class__.schema_configs)
# Create all schemas
self.schema_manager.create_all_schemas(self.__class__)
```
```
```

## Common Patterns

### Schema Inheritance

You can create schema hierarchies using schema base classes:

```python
from pydantic import BaseModel, Field
from uno.schema import UnoSchema, UnoSchemaConfig

# Base schema with common fields
class BaseUserSchema(UnoSchema):```

class Config:```

extra = "forbid"  # Reject unknown fields
```
```

# Role-specific schema
class AdminUserSchema(BaseUserSchema):```

role: str = Field("admin", const=True)
permissions: list[str] = []
```

# Create configurations
schema_configs = {```

"view_schema": UnoSchemaConfig(schema_base=BaseUserSchema),
"admin_schema": UnoSchemaConfig(schema_base=AdminUserSchema),
```
}

schema_manager = UnoSchemaManager(schema_configs)
```

### Conditional Fields

You can create schemas with conditional field inclusion:

```python
from uno.schema import UnoSchemaConfig
from typing import Set

def get_fields_for_role(role: str) -> Set[str]:```

"""Get the fields visible to a specific role."""
base_fields = {"id", "name", "email"}
``````

```
```

if role == "admin":```

return base_fields | {"created_at", "modified_at", "is_active"}
```
elif role == "manager":```

return base_fields | {"is_active"}
```
else:```

return base_fields
```
```

# Create a role-specific schema configuration
role = "manager"
schema_config = UnoSchemaConfig(include_fields=get_fields_for_role(role))

# Add it to the manager
schema_manager.add_schema_config(f"{role}_schema", schema_config)
```

## Testing

When testing with the schema manager, focus on validating schema creation and field inclusion/exclusion:

```python
import pytest
from uno.schema_manager import UnoSchemaManager
from uno.schema import UnoSchemaConfig
from uno.errors import UnoError

def test_schema_creation():```

"""Test creating schemas for a model."""
# Setup
schema_configs = {```

"view_schema": UnoSchemaConfig(),
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at"}),
```
}
``````

```
```

schema_manager = UnoSchemaManager(schema_configs)
``````

```
```

# Define a test model
class TestModel:```

model_fields = {
    "id": None,
    "name": None,
    "email": None,
    "created_at": None,
}
```
``````

```
```

# Create schemas
schemas = schema_manager.create_all_schemas(TestModel)
``````

```
```

# Assert schemas were created
assert "view_schema" in schemas
assert "edit_schema" in schemas
``````

```
```

# Check field inclusion/exclusion
view_schema = schemas["view_schema"]
edit_schema = schemas["edit_schema"]
``````

```
```

assert "created_at" in view_schema.model_fields
assert "created_at" not in edit_schema.model_fields
```

def test_invalid_schema_config():```

"""Test validation of schema configurations."""
# Both include and exclude fields - should fail
with pytest.raises(UnoError) as excinfo:```

invalid_config = UnoSchemaConfig(
    include_fields={"id", "name"},
    exclude_fields={"created_at"}
)
``````

```
```

class TestModel:
    model_fields = {
        "id": None,
        "name": None,
        "created_at": None,
    }
    
schema_manager = UnoSchemaManager({"invalid": invalid_config})
schema_manager.create_schema("invalid", TestModel)
```
``````

```
```

assert "BOTH_EXCLUDE_INCLUDE_FIELDS" in str(excinfo.value)
```
```

## Best Practices

1. **Define Clear Schema Purposes**: Each schema should have a clear purpose (viewing, editing, summarizing, etc.).

2. **Use Schema Base Classes**: Create base schema classes for common patterns to ensure consistency.

3. **Validate Against Pydantic**: Use Pydantic's validation features to ensure data integrity.

4. **Keep Schemas Simple**: Avoid complex logic in schemas; use the business object for complicated operations.

5. **Document Schema Fields**: Add descriptions to schema fields to improve API documentation.

6. **Be Consistent**: Use consistent naming conventions for schemas across your application.

7. **Security First**: Always exclude sensitive fields from schemas that will be exposed publicly.

8. **Test Thoroughly**: Test schema creation, validation, and serialization/deserialization.
