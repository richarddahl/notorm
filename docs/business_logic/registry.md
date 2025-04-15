# Object Registry

The UnoRegistry is a centralized registry system that manages the registration and lookup of business objects in uno, providing a type-safe way to discover and instantiate business objects at runtime.

## Overview

The UnoRegistry serves as a global registry that:

- Maintains a single point of registration for all business objects
- Provides type-safe lookup methods for business objects by table name
- Automatically registers UnoObj subclasses during class definition
- Implements the singleton pattern for consistent global access

## Key Features

### Singleton Pattern

The registry implements the singleton pattern to ensure a single, consistent instance throughout the application:

```python
from uno.registry import UnoRegistry

# Get the registry instance - same instance everywhere
registry = UnoRegistry.get_instance()
```

### Automatic Registration

When you define a UnoObj subclass, it automatically registers with the registry:

```python
from uno.obj import UnoObj
from uno.model import UnoModel

class CustomerModel(UnoModel):```

__tablename__ = "customer"
# Fields...
```

class Customer(UnoObj[CustomerModel]):```

model = CustomerModel
# No explicit registration needed!
```
```

The registration happens in the `__init_subclass__` method of UnoObj, which is called when a subclass is defined.

### Type-Safe Object Lookup

The registry provides methods to look up business object classes:

```python
# Get the registry instance
registry = UnoRegistry.get_instance()

# Get a class by table name
customer_class = registry.get("customer")

# Check if a class is registered
if customer_class:```

# Create an instance
customer = customer_class(name="John Doe")
```
```

## API Reference

### Core Methods

| Method | Description |
|--------|-------------|
| `get_instance()` | Get the singleton registry instance |
| `register(model_class, table_name)` | Register a model class with the registry |
| `get(table_name)` | Get a model class by its table name |
| `get_all()` | Get all registered model classes |
| `clear()` | Clear all registered models (primarily for testing) |

### Implementation Details

The registry is implemented as a Python class with a class variable to store the singleton instance:

```python
class UnoRegistry:```

_instance: Optional["UnoRegistry"] = None
_models: Dict[str, Type[BaseModel]] = {}

@classmethod
def get_instance(cls) -> "UnoRegistry":```

if cls._instance is None:
    cls._instance = cls()
return cls._instance
```
    
# Other methods...
```
```

## Usage Examples

### Basic Usage

```python
from uno.registry import UnoRegistry

# Get the registry instance
registry = UnoRegistry.get_instance()

# Get a class by table name
customer_class = registry.get("customer")
if customer_class:```

# Create an instance
customer = customer_class(name="John Doe")
``````

```
```

# Use the instance
await customer.save()
```
```

### Manual Registration

While automatic registration is usually sufficient, you can register classes manually:

```python
from uno.registry import UnoRegistry

# Get the registry instance
registry = UnoRegistry.get_instance()

# Register a class manually
registry.register(Customer, "customer")
```

### Dynamic Object Creation

The registry enables dynamic object creation based on table names:

```python
def create_object(table_name: str, **kwargs: Any) -> Optional[UnoObj]:```

"""Create a business object by table name."""
registry = UnoRegistry.get_instance()
cls = registry.get(table_name)
if cls:```

return cls(**kwargs)
```
return None
```

# Create objects dynamically
customer = create_object("customer", name="John Doe")
product = create_object("product", name="Widget")
```

### Batch Registration

You can register multiple classes at once using a dictionary:

```python
def register_all_models(models_dict: Dict[str, Type[UnoObj]]) -> None:```

"""Register multiple models at once."""
registry = UnoRegistry.get_instance()
for table_name, model_class in models_dict.items():```

try:
    registry.register(model_class, table_name)
except UnoRegistryError as e:
    print(f"Registration error: {e}")
```
```

# Register multiple models
register_all_models({```

"customer": Customer,
"product": Product,
"order": Order
```
})
```

## Best Practices

1. **Use the Singleton**: Always access the registry through `UnoRegistry.get_instance()`.

2. **Let Automatic Registration Work**: In most cases, let the automatic registration handle things rather than manually registering classes.

3. **Handle Missing Classes**: Always check if a class was found before using it:
   ```python
   cls = registry.get("customer")
   if cls:```

   # Use the class
```
   else:```

   # Handle the case where the class wasn't found
```
   ```

4. **Clear the Registry in Tests**: When testing, clear the registry between tests to ensure isolation:
   ```python
   def setUp(self):```

   UnoRegistry.get_instance().clear()
```
   ```

5. **Avoid Circular Dependencies**: Be careful when creating classes that depend on each other through the registry.

## Related Topics

- [UnoObj](unoobj.md) - Learn how business objects automatically register with the registry
- [API Integration](/docs/api/overview.md) - See how the registry enables automatic API endpoint creation
- [Dependency Injection](/docs/dependency_injection/overview.md) - Learn how the registry works with the dependency injection system