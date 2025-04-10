# UnoRegistry

The `UnoRegistry` class manages the registration and retrieval of business objects in the Uno framework. It provides a central repository for all business objects used in the application.

## Overview

The registry serves as a service locator that:

- Registers business objects by model type or table name
- Resolves models to business objects
- Manages object relationships
- Enables dependency injection

## Basic Usage

### Getting the Registry Instance

The registry is implemented as a singleton to ensure a single instance throughout the application:

```python
from uno.registry import UnoRegistry

# Get the registry instance
registry = UnoRegistry.get_instance()
```

### Registering a Class

```python
from uno.obj import UnoObj
from uno.model import UnoModel

# Define your model and business object
class CustomerModel(UnoModel):
    __tablename__ = "customer"
    # Fields...

class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    # Methods...

# Register the class
registry = UnoRegistry.get_instance()
registry.register(Customer, "customer")
```

Note that registering typically happens automatically during class definition through the `UnoObj.__init_subclass__` method.

### Finding Classes

```python
# Get a class by table name
customer_class = registry.get_class_by_table_name("customer")

# Get a class by class name
customer_class = registry.get_class_by_name("Customer")

# Get a class by model
customer_class = registry.get_class_by_model(CustomerModel)
```

## Advanced Usage

### Managing Dependencies

The registry can be used to manage dependencies between business objects:

```python
# Get a class by its relationship to another class
order_class = registry.get_class_by_relationship("Order", "Customer")

# Create a related object
order = order_class(customer_id=customer.id)
```

### Class Lookup with Defaults

You can provide defaults when looking up classes:

```python
# Get a class with a default
customer_class = registry.get_class_by_table_name("customer", default=Customer)

# Check if a class is registered
is_registered = registry.has_class("Customer")
```

### Registration Events

You can add event listeners for registration events:

```python
def on_class_registered(cls, table_name):
    print(f"Class {cls.__name__} registered for table {table_name}")

# Add registration listener
registry.add_registration_listener(on_class_registered)

# Register a class (will trigger the listener)
registry.register(Customer, "customer")
```

## Common Patterns

### Service Location

The registry can be used as a service locator:

```python
from uno.registry import UnoRegistry

def get_class(table_name):
    """Get a business object class by table name."""
    registry = UnoRegistry.get_instance()
    return registry.get_class_by_table_name(table_name)

# Get a class dynamically
dynamic_class = get_class("customer")
instance = dynamic_class(name="John Doe")
```

### Factory Methods

The registry can be used to create factory methods:

```python
from uno.registry import UnoRegistry

def create_object(table_name, **kwargs):
    """Create a business object by table name."""
    registry = UnoRegistry.get_instance()
    cls = registry.get_class_by_table_name(table_name)
    return cls(**kwargs)

# Create an object dynamically
customer = create_object("customer", name="John Doe", email="john@example.com")
```

### Dynamic API Creation

The registry can be used to dynamically create API endpoints:

```python
from fastapi import FastAPI
from uno.registry import UnoRegistry
from uno.api.endpoint_factory import UnoEndpointFactory

app = FastAPI()
registry = UnoRegistry.get_instance()
factory = UnoEndpointFactory()

# Get all registered classes
registered_classes = registry.get_all_classes()

# Create endpoints for all registered classes
for cls in registered_classes:
    factory.create_endpoints(app, cls)
```

## Best Practices

1. **Use Singleton Instance**: Always use the singleton instance provided by `UnoRegistry.get_instance()`.

2. **Explicit Registration**: Register classes explicitly when automatic registration is insufficient.

3. **Error Handling**: Handle missing classes gracefully with default values or clear error messages.

4. **Avoid Circular Dependencies**: Be careful not to create circular dependencies between business objects.

5. **Document Relationships**: Document the relationships between business objects to make the code easier to understand.

6. **Keep It Simple**: Avoid overusing the registry for service location; prefer explicit dependencies when possible.

7. **Test Thoroughly**: Test registry lookups with various inputs, including edge cases.

8. **Ensure Thread Safety**: Be aware that the registry is shared across threads.

9. **Use Type Annotations**: Provide proper type annotations for better IDE support and type checking.

10. **Follow Naming Conventions**: Use consistent naming conventions for business objects.