# Business Logic Overview

The Business Logic Layer in uno provides a clean interface for implementing business rules and validation logic, while abstracting away database operations.

## UnoObj

The `UnoObj` class is a Pydantic model that wraps around a SQLAlchemy model, providing a clean interface for business logic. It supports:

- Model registration
- Schema management
- Data validation
- CRUD operations
- Filter generation

### Basic Usage

```python
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

# Define your SQLAlchemy model
class CustomerModel(UnoModel):
    __tablename__ = "customer"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
    phone: Mapped[PostgresTypes.String64] = mapped_column(nullable=True)
    
# Define your business object
class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    
    display_name = "Customer"
    display_name_plural = "Customers"
    
    # Add business logic methods
    async def send_welcome_email(self):
        """Send a welcome email to the customer."""
        if not self.email:
            raise ValueError("Customer has no email address")
        
        # Email sending logic here
        print(f"Sending welcome email to {self.email}")
        return True
```

### Object Lifecycle Methods

```python
# Create a new customer
new_customer = Customer(
    name="John Doe",
    email="john@example.com",
    phone="555-123-4567"
)

# Save to database
await new_customer.save()

# Get by ID
customer = await Customer.get(id="abc123")

# Update fields
customer.name = "John Smith"
await customer.save()

# Delete
await customer.delete()
```

## UnoRegistry

The `UnoRegistry` class maintains a registry of all business objects in the application. This is useful for finding objects by their type or table name.

```python
from uno.registry import UnoRegistry

# Get the registry instance
registry = UnoRegistry.get_instance()

# Register a class
registry.register(Customer, "customer")

# Get a class by table name
customer_class = registry.get_class_by_table_name("customer")

# Get a class by class name
customer_class = registry.get_class_by_name("Customer")
```

## Schema Management

The `UnoSchemaManager` class manages schema configurations for business objects. This allows you to define different views of an object for different purposes.

```python
from uno.schema import UnoSchemaConfig, UnoSchemaManager

# Define schema configurations
schema_configs = {
    "view_schema": UnoSchemaConfig(),  # All fields
    "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
    "summary_schema": UnoSchemaConfig(include_fields={"id", "name", "email"}),
}

# Create a schema manager
schema_manager = UnoSchemaManager(schema_configs)

# Create a schema instance
view_schema = schema_manager.create_schema("view_schema", Customer)

# Create an object from a schema
customer = view_schema(**data)
```

## Best Practices

1. **Separate Business Logic**: Keep database operations in the base class and put business logic in your subclass.

2. **Use Type Annotations**: Always use proper type annotations for better IDE support and type checking.

3. **Validate Input Data**: Use Pydantic's validation features to ensure data integrity.

4. **Handle Exceptions**: Catch and handle specific exceptions to provide meaningful error messages.

5. **Use Schemas Appropriately**: Create different schemas for different use cases (viewing, editing, etc.).

6. **Document Your Code**: Add docstrings to your classes and methods to explain their purpose and usage.

## Next Steps

- [UnoObj](unoobj.md): Learn more about the UnoObj class
- [Registry](registry.md): Understand the object registry
- [Schema Management](schema.md): Learn about schema management
- [API Integration](../api/overview.md): Learn how to expose your business logic through API endpoints