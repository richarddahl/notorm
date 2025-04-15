# UnoObj

The `UnoObj` class serves as the primary business logic layer for models in uno. It handles object lifecycle, data validation, and business logic operations.

## Overview

`UnoObj` is a Pydantic model that wraps around a SQLAlchemy model, providing a clean interface for business logic while abstracting away database operations. It supports:

- Model registration
- Schema management
- Data validation
- CRUD operations
- Filter generation

## Basic Usage

### Defining a UnoObj Class

To define a business object, create a class that inherits from `UnoObj` with your model class as a type parameter:

```python
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig

# Define your SQLAlchemy model
class CustomerModel(UnoModel):```

__tablename__ = "customer"
``````

```
```

name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
phone: Mapped[PostgresTypes.String64] = mapped_column(nullable=True)
```
    
# Define your business object
class Customer(UnoObj[CustomerModel]):```

# The model is automatically set from the type parameter
# No need to set model = CustomerModel
``````

```
```

display_name = "Customer"
display_name_plural = "Customers"
``````

```
```

schema_configs = {```

"view_schema": UnoSchemaConfig(),  # All fields
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
```
}
``````

```
```

# Add business logic methods
async def send_welcome_email(self):```

"""Send a welcome email to the customer."""
if not self.email:
    raise ValueError("Customer has no email address")
``````

```
```

# Email sending logic here
print(f"Sending welcome email to {self.email}")
return True
```
```
```

The model class is automatically set from the type parameter `UnoObj[CustomerModel]`, eliminating the need to set it explicitly with `model = CustomerModel`.

### Creating a New Object

```python
# Create a new customer
new_customer = Customer(```

name="John Doe",
email="john@example.com",
phone="555-123-4567"
```
)

# Save to database
await new_customer.save()
```

### Retrieving Objects

```python
# Get by ID
customer = await Customer.get(id="abc123")

# Get by natural key
customer = await Customer.get(email="john@example.com")

# Filter with parameters
from uno.database.db import FilterParam

# Create filter parameters
filter_params = FilterParam(```

limit=10,
offset=0,
name__contains="John"
```
)

# Get filtered customers
customers = await Customer.filter(filters=filter_params)
```

### Updating Objects

```python
# Get an existing customer
customer = await Customer.get(id="abc123")

# Update fields
customer.name = "John Smith"
customer.phone = "555-987-6543"

# Save changes
await customer.save()
```

### Merging Objects

The merge operation performs an upsert (insert or update) based on the primary key:

```python
customer = Customer(```

id="abc123",  # Existing ID
name="John Smith",
email="john@example.com",
phone="555-555-5555"
```
)

# Merge will update if ID exists, or create if it doesn't
model, action = await customer.merge()
print(f"Action performed: {action}")  # "insert" or "update"
```

### Deleting Objects

```python
# Get an existing customer
customer = await Customer.get(id="abc123")

# Delete
await customer.delete()
```

## Integration Architecture

The complete integration between UnoObj, UnoModel, and UnoDB follows a structured flow that ensures data integrity and proper transformation at each step.

### UnoObj -> UnoModel -> UnoDB -> UnoModel -> UnoObj Roundtrip

1. **UnoObj Creation (Starting Point)**
   - Create an instance of UnoObj with data
   - Data is validated through Pydantic validation
   - Example: `user = User(email="example@domain.com", handle="username")`

2. **UnoObj -> UnoModel Conversion**
   - UnoObj uses the schema system to convert to a model instance
   - Conversion happens via the `to_model(schema_name)` method
   - Example: `model = user.to_model(schema_name="edit_schema")`

3. **UnoDB Database Operations**
   - The model is passed to the appropriate UnoDB operation
   - Operations include create, update, delete, get, filter, and merge
   - Example: `result = await user.db.create(schema=model)`

4. **UnoModel -> UnoObj Conversion**
   - Results from the database are converted back to UnoObj instances
   - This happens automatically in methods like `get()` and `filter()`
   - Example: `retrieved_user = await User.get(id="123")`

This roundtrip flow ensures that:
- Data is properly validated before reaching the database
- Business logic is consistently applied at the object level
- Database operations are abstracted away from business logic
- Data retrieval automatically populates business objects

### Sequence Diagram

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│  UnoObj  │         │ UnoModel │         │  UnoDB  │
└────┬────┘         └────┬────┘         └────┬────┘```

 │                    │                   │
 │ create             │                   │
 ├───────────────────►│                   │
 │                    │                   │
 │ to_model()         │                   │
 ├───────────────────►│                   │
 │                    │                   │
 │                    │ save()            │
 │                    ├──────────────────►│
 │                    │                   │
 │                    │                   │ DB operation
 │                    │                   │◄─────────┐
 │                    │                   │          │
 │                    │ DB result         │          │
 │                    │◄──────────────────┤          │
 │                    │                   │          │
 │ convert to UnoObj  │                   │          │
 │◄───────────────────┤                   │          │
 │                    │                   │          │
 │ business logic     │                   │          │
 │◄─────────┐         │                   │          │
 │          │         │                   │          │
 │          │         │                   │          │
```
```

## Web Application Integration

`UnoObj` integrates with FastAPI to automatically create endpoints:

```python
from fastapi import FastAPI

app = FastAPI()

# Configure endpoints for all models
Customer.configure(app)
```

This will create the following endpoints:
- `POST /api/v1/customer` - Create
- `GET /api/v1/customer/{id}` - View
- `GET /api/v1/customer` - List
- `PATCH /api/v1/customer/{id}` - Update
- `DELETE /api/v1/customer/{id}` - Delete
- `PUT /api/v1/customer` - Import

## Advanced Features

### Custom Schemas

You can define custom schemas beyond the default `view_schema` and `edit_schema`:

```python
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

```
```

schema_configs = {```

"view_schema": UnoSchemaConfig(),
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
"summary_schema": UnoSchemaConfig(include_fields={"id", "name", "email"}),
```
}
``````

```
```

# Later use:
def get_summary(self):```

return self.to_model(schema_name="summary_schema")
```
```
```

### Custom Endpoints

You can customize which endpoints are created:

```python
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

endpoints = ["Create", "View", "List"]  # Only these endpoints will be created
```
```

### Filter Customization

You can exclude specific fields from filtering:

```python
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

terminate_field_filters = ["created_at", "modified_at"]  # These fields won't be filterable
```
```

Or exclude the entire model from filters:

```python
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

exclude_from_filters = True  # This model won't generate any filters
```
```

## Testing

When testing `UnoObj` classes, it's recommended to create unit tests that verify both:

1. **Data Transformation**: Test the conversion between UnoObj and UnoModel
2. **Database Operations**: Test the interaction with UnoDB

### Example Test for UnoObj -> UnoModel Conversion:

```python
class TestUserIntegration(IsolatedAsyncioTestCase):```

async def test_create_superuser_obj_model_conversion(self):```

# Create a superuser UnoObj instance
superuser = User(
    email="test_integration@notorm.tech",
    handle="test_integration",
    full_name="Test Integration User",
    is_superuser=True
)
```
    ```

# Convert to UnoModel using the schema
superuser._ensure_schemas_created()
model = superuser.to_model(schema_name="edit_schema")
```
    ```

# Verify model instance
assert isinstance(model, UserModel)
assert model.email == "test_integration@notorm.tech"
assert model.handle == "test_integration"
assert model.full_name == "Test Integration User"
assert model.is_superuser is True
```
```
```

### Mocking Database Access:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_customer_save():```

# Setup - mock the database access
with patch('uno.database.db.UnoDBFactory') as mock_db_factory:```

mock_db = AsyncMock()
mock_db_factory.return_value = mock_db
mock_db.create.return_value = (CustomerModel(id="test123", name="Test"), True)
```
    ```

# Create a customer
customer = Customer(name="Test", email="test@example.com")
```
    ```

# Save it
await customer.save()
```
    ```

# Verify
mock_db.create.assert_called_once()
```
```
```

## Best Practices

1. **Separate Business Logic**: Keep database operations in the base class and put business logic in your subclass.

2. **Use Type Annotations**: Always use proper type annotations for better IDE support and type checking.

3. **Validate Input Data**: Use Pydantic's validation features to ensure data integrity.

4. **Handle Exceptions**: Catch and handle specific exceptions to provide meaningful error messages.

5. **Use Schemas Appropriately**: Create different schemas for different use cases (viewing, editing, etc.).

6. **Document Your Code**: Add docstrings to your classes and methods to explain their purpose and usage.

7. **Test the Roundtrip Flow**: Ensure that objects can be correctly converted to models, saved to the database, and retrieved as objects again.

8. **Consider Authorization**: When designing the integration, consider how authorization will affect database operations and object access.