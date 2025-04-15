# Business Logic Layer

The Business Logic Layer in Uno provides a clean interface for implementing business rules and validation logic, while abstracting away database operations. It forms the core of your application, implementing the domain logic that drives your business processes.

## In This Section

- [UnoObj](unoobj.md) - Core business object class with CRUD operations and validation
- [Registry](registry.md) - Object registry for type-safe class lookup
- [Schema](schema.md) - Schema management for flexible data serialization

## Overview

The Business Logic Layer in Uno is designed to separate business concerns from database and API concerns, allowing you to focus on implementing domain-specific behavior. It provides a rich set of tools for data validation, object lifecycle management, and integration with the web application.

## Key Concepts

### Business Objects (UnoObj)

The `UnoObj` class is the foundation of the Business Logic Layer. It is a Pydantic model that wraps around a SQLAlchemy model, providing a clean interface for implementing business logic. Key capabilities include:

- **Model Integration**: Tight integration with SQLAlchemy models
- **Schema Management**: Flexible data serialization and validation
- **CRUD Operations**: Asynchronous create, read, update, delete operations
- **Filter Generation**: Automatic filter creation for queries
- **Validation**: Data validation with detailed error reporting

### Registry System

The `UnoRegistry` provides a global registry for all business objects in your application, enabling:

- **Type-Safe Lookups**: Find object classes by their table name
- **Single Instance Pattern**: Ensures consistent registration across the application
- **Automatic Registration**: Objects are registered when their classes are defined

### Schema Management

The `UnoSchemaManager` gives you fine-grained control over how data is serialized and validated through:

- **Multiple View Schemas**: Define different schemas for different contexts (editing, viewing, etc.)
- **Field Inclusion/Exclusion**: Control exactly which fields appear in each schema
- **Automatic Schema Generation**: Create schemas based on model definitions
- **Pagination Support**: Built-in support for paginated lists of items

## Getting Started

### 1. Define Your Models and Business Objects

```python
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

# Define your SQLAlchemy model
class CustomerModel(UnoModel):```

__tablename__ = "customer"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
phone: Mapped[PostgresTypes.String64] = mapped_column(nullable=True)
```
    
# Define your business object
class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
``````

```
```

# Define schemas for different contexts
schema_configs = {```

"view_schema": UnoSchemaConfig(),  # All fields
"edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
"summary_schema": UnoSchemaConfig(include_fields={"id", "name", "email"}),
```
}
``````

```
```

# Configure API endpoints
endpoints = ["Create", "View", "List", "Update", "Delete"]
endpoint_tags = ["Customers"]
``````

```
```

# Add business logic methods
async def send_welcome_email(self) -> bool:```

"""Send a welcome email to the customer."""
if not self.email:
    raise ValidationError([{
        "field": "email",
        "message": "Customer has no email address",
        "error_code": "EMAIL_REQUIRED"
    }])
```
    ```

# Email sending logic here
return True
```
```
```

### 2. Use Object Lifecycle Methods

```python
# Create a new customer
new_customer = Customer(```

name="John Doe",
email="john@example.com",
phone="555-123-4567"
```
)

# Save to database (creates a new record)
await new_customer.save()

# Retrieve an object by ID
customer = await Customer.get(id="abc123")

# Update fields
customer.name = "John Smith"
await customer.save()

# Delete the object
await customer.delete()

# Use the merge operation for upserts
model, action = await customer.merge()
print(f"Object was {action}ed")  # "inserted" or "updated"

# Filter objects
customers = await Customer.filter({"name__contains": "John"})
```

### 3. Configure for API Integration

```python
from fastapi import FastAPI

app = FastAPI()

# Configure the business object for API integration
Customer.configure(app)
# This automatically creates API endpoints: 
# /customers, /customers/{id}, etc.
```

## Best Practices

1. **Keep Logic in Business Objects**: Place all domain-specific logic in your UnoObj subclasses, not in API endpoints or database code.

2. **Use Custom Validation**: Implement domain-specific validation in your business objects.
   ```python
   def validate(self, schema_name: str) -> ValidationContext:```

   context = super().validate(schema_name)
   if self.email and not self.email.endswith("@company.com"):```

   context.add_error("email", "Must use company email", "INVALID_EMAIL_DOMAIN")
```
   return context
```
   ```

3. **Create Purpose-Specific Schemas**: Define different schemas for different use cases (view, edit, list, etc.).

4. **Leverage Type Annotations**: Use proper type annotations throughout for better IDE support and type checking.

5. **Standardize Error Handling**: Use the provided error classes and validation context for consistent error reporting.

6. **Prefer Composition**: Build complex business logic through composition rather than deep inheritance hierarchies.

## Related Sections

- [API Layer](/docs/api/overview.md) - Learn how to expose your business logic through API endpoints
- [Database Layer](/docs/database/overview.md) - Understand how business objects interact with the database
- [Schema Management](/docs/schema/schema_service.md) - Advanced schema management techniques