# Schema Management

The Schema Management system in uno provides a flexible way to define, validate, and transform data schemas for business objects.

## Overview

The schema management system:

- Defines the structure of business objects
- Validates data against schemas
- Transforms data between different representations
- Supports multiple schema variants for different use cases

## Key Components

### UnoSchemaConfig

The `UnoSchemaConfig` class defines the configuration for a schema:

```python
from uno.schema import UnoSchemaConfig

# Create a schema configuration
view_schema = UnoSchemaConfig(
    include_fields={"id", "name", "email"},  # Only include these fields
    exclude_fields={"password"},             # Exclude these fields
    read_only=True                           # Schema is read-only
)
```

### UnoSchemaManager

The `UnoSchemaManager` class manages schema configurations and creates schema models:

```python
from uno.schema import UnoSchemaManager, UnoSchemaConfig

# Define schema configurations
schema_configs = {

"view_schema": UnoSchemaConfig(),  # All fields
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
"summary_schema": UnoSchemaConfig(include_fields={"id", "name", "email"}),
}

# Create a schema manager
schema_manager = UnoSchemaManager(schema_configs)

# Create a schema model for a business object
view_schema = schema_manager.create_schema("view_schema", Customer)

# Create an object from schema
customer = view_schema(id="abc123", name="John Doe", email="john@example.com")
```

## Basic Usage

### Defining Schemas in Business Objects

Typically, schemas are defined as part of the business object class:

```python
from uno.obj import UnoObj
from uno.model import UnoModel
from uno.schema import UnoSchemaConfig

class CustomerModel(UnoModel):```

__tablename__ = "customer"
# Fields...
```

class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

```
```

# Define schema configurations
schema_configs = {```

"view_schema": UnoSchemaConfig(),  # All fields
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
"summary_schema": UnoSchemaConfig(include_fields={"id", "name", "email"}),
```
}
```
```

### Using Schemas

```python
# Create a customer with the edit schema
edit_schema = customer.schema_manager.create_schema("edit_schema", Customer)
new_customer = edit_schema(name="John Doe", email="john@example.com")

# Convert to a model instance
model_instance = new_customer.to_model()

# Save to database
await new_customer.save()

# Get a summary representation
summary = customer.to_dict(schema_name="summary_schema")
```

## Advanced Usage

### Custom Field Transformations

You can define custom field transformations:

```python
from uno.schema import UnoSchemaConfig, FieldTransformer

# Define a field transformer
class PasswordHasher(FieldTransformer):```

def transform(self, value, obj=None):```

"""Transform a password to a hashed value."""
import hashlib
return hashlib.sha256(value.encode()).hexdigest()
```
```

# Create a schema config with transformers
schema_config = UnoSchemaConfig(```

field_transformers={```

"password": PasswordHasher()
```
}
```
)

# Create a schema
schema = schema_manager.create_schema("register_schema", User, schema_config)

# Create a user with the schema
user = schema(username="johndoe", password="secret")
# user.password will be hashed
```

### Schema Inheritance

Schemas can inherit from other schemas:

```python
from uno.schema import UnoSchemaConfig

# Base schema config
base_schema = UnoSchemaConfig(```

exclude_fields={"password", "internal_notes"}
```
)

# Extended schema config
extended_schema = UnoSchemaConfig(```

base_schema=base_schema,
include_fields={"id", "name", "email", "address"}
```
)
```

### Dynamic Schemas

You can create schemas dynamically based on runtime conditions:

```python
from uno.schema import UnoSchemaConfig

def get_schema_for_user(user, obj_class):```

"""Get a schema based on user permissions."""
# Base fields that everyone can see
base_fields = {"id", "name", "email"}
``````

```
```

# Add additional fields based on user permissions
if user.has_permission("view_phone_numbers"):```

base_fields.add("phone")
```
``````

```
```

if user.has_permission("view_addresses"):```

base_fields.add("address")
```
``````

```
```

# Create a schema config
schema_config = UnoSchemaConfig(include_fields=base_fields)
``````

```
```

# Create and return the schema
return schema_manager.create_schema("dynamic_schema", obj_class, schema_config)
```
```

## Common Patterns

### API Request/Response Schemas

Use schemas to define API request and response models:

```python
from fastapi import FastAPI, Depends
from uno.schema import UnoSchemaManager

app = FastAPI()
schema_manager = UnoSchemaManager()

# Create schemas for API
create_schema = schema_manager.create_schema("edit_schema", Customer)
view_schema = schema_manager.create_schema("view_schema", Customer)

@app.post("/api/customers", response_model=view_schema)
async def create_customer(customer: create_schema):```

"""Create a new customer."""
# Create and save the customer
new_customer = Customer(**customer.dict())
await new_customer.save()
``````

```
```

# Return the customer as a view schema
return new_customer.to_dict(schema_name="view_schema")
```
```

### Data Validation

Use schemas to validate data:

```python
from uno.schema import UnoSchemaManager
from pydantic import ValidationError

# Create a schema for validation
schema = schema_manager.create_schema("edit_schema", Customer)

try:```

# Validate data
validated_data = schema(name="John Doe", email="invalid-email")
```
except ValidationError as e:```

print(f"Validation error: {e}")
```
```

### Data Transformation

Use schemas to transform data between formats:

```python
from uno.schema import UnoSchemaManager

# Create schemas for different formats
internal_schema = schema_manager.create_schema("internal_schema", Customer)
api_schema = schema_manager.create_schema("api_schema", Customer)
database_schema = schema_manager.create_schema("database_schema", Customer)

# Transform between formats
internal_data = internal_schema(**user_input)
api_data = api_schema(**internal_data.dict())
database_data = database_schema(**internal_data.dict())
```

## Best Practices

1. **Define Clear Schemas**: Create clear, well-documented schemas for different use cases.

2. **Use Consistent Naming**: Use consistent naming for schemas (e.g., "view_schema", "edit_schema", etc.).

3. **Validate Input**: Always validate input data against schemas before processing.

4. **Separate Concerns**: Use different schemas for different concerns (viewing, editing, importing, etc.).

5. **Document Schemas**: Document the purpose and structure of each schema.

6. **Use Field Exclusion**: Prefer `exclude_fields` over `include_fields` for safer schema evolution.

7. **Handle Validation Errors**: Implement proper error handling for validation errors.

8. **Test Schemas**: Write tests to ensure schemas validate and transform data correctly.

9. **Check for Required Fields**: Ensure required fields are present in schemas.

10. **Use Type Annotations**: Provide proper type annotations for better IDE support and type checking.