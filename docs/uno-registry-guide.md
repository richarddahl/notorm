# UnoRegistry

The `UnoRegistry` class provides a central registry for all `UnoObj` model classes in the Uno framework. It implements a singleton pattern to ensure there's only one registry instance throughout the application.

## Overview

The registry serves as a lookup mechanism for finding model classes by their table names. This is particularly useful for:

- Ensuring model uniqueness (preventing duplicate models with the same table name)
- Looking up models dynamically at runtime
- Managing model relationships
- Supporting plugin/extension architectures

## Basic Usage

### Getting the Registry Instance

Since `UnoRegistry` implements the singleton pattern, you should always get the instance using the `get_instance()` class method:

```python
from uno.registry import UnoRegistry

# Get the registry instance
registry = UnoRegistry.get_instance()
```

### Registering Models

Models are automatically registered when you define a `UnoObj` subclass. However, you can also register models manually:

```python
from uno.registry import UnoRegistry
from uno.obj import UnoObj
from my_models import CustomerModel

class Customer(UnoObj):
    model = CustomerModel
    # ...

# Manual registration (normally not needed)
registry = UnoRegistry.get_instance()
registry.register(Customer, CustomerModel.__tablename__)
```

### Looking Up Models

You can look up models by their table name:

```python
# Get a model by table name
customer_model = registry.get("customer")

if customer_model:
    # Create an instance
    customer = customer_model(name="John Doe")
```

### Getting All Registered Models

You can get all registered models as a dictionary mapping table names to model classes:

```python
# Get all registered models
all_models = registry.get_all()

# Print all model names
for table_name, model_class in all_models.items():
    print(f"Table: {table_name}, Model: {model_class.__name__}")
```

## Advanced Usage

### Clearing the Registry

In testing scenarios, you might want to clear the registry:

```python
# Clear the registry (mainly for testing)
registry.clear()
```

### Integration with Dependency Injection

You can integrate the registry with a dependency injection system:

```python
from dependency_injector import containers, providers
from uno.registry import UnoRegistry

class Container(containers.DeclarativeContainer):
    registry = providers.Singleton(UnoRegistry.get_instance)
    
    # Other services that depend on the registry
    model_service = providers.Factory(
        ModelService,
        registry=registry
    )
```

### Custom Registry Subclass

You can create a custom registry subclass for additional functionality:

```python
from uno.registry import UnoRegistry
from typing import Dict, Type, Optional, TypeVar

T = TypeVar('T', bound='BaseModel')

class ExtendedRegistry(UnoRegistry):
    def __init__(self):
        super().__init__()
        self._model_metadata: Dict[str, dict] = {}
    
    def register_with_metadata(self, model_class: Type[T], table_name: str, metadata: dict) -> None:
        """Register a model with additional metadata."""
        self.register(model_class, table_name)
        self._model_metadata[table_name] = metadata
    
    def get_metadata(self, table_name: str) -> Optional[dict]:
        """Get metadata for a registered model."""
        return self._model_metadata.get(table_name)

# Usage
extended_registry = ExtendedRegistry()
# Replace the singleton instance
UnoRegistry._instance = extended_registry
```

## Common Patterns

### Model Discovery

Automatically discover and register models in a package:

```python
import importlib
import inspect
import pkgutil
from uno.obj import UnoObj
from uno.registry import UnoRegistry

def discover_models(package_name: str) -> None:
    """Discover and register all UnoObj models in a package."""
    registry = UnoRegistry.get_instance()
    package = importlib.import_module(package_name)
    
    # Find all modules in the package
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        module = importlib.import_module(module_name)
        
        # Find all UnoObj subclasses in the module
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, UnoObj) and obj != UnoObj:
                # Models are automatically registered via __init_subclass__
                pass
                
    return registry.get_all()

# Usage
models = discover_models("my_app.models")
print(f"Discovered {len(models)} models")
```

### Model Relationships

Build a graph of model relationships:

```python
from uno.registry import UnoRegistry
import networkx as nx
import matplotlib.pyplot as plt

def build_model_graph():
    """Build a graph of model relationships."""
    registry = UnoRegistry.get_instance()
    models = registry.get_all()
    
    # Create a graph
    G = nx.DiGraph()
    
    # Add nodes for each model
    for table_name, model_class in models.items():
        G.add_node(table_name)
    
    # Add edges for relationships
    for table_name, model_class in models.items():
        model_table = model_class.model.__table__
        
        # Add edges for foreign keys
        for column in model_table.columns:
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    target_table = fk.column.table.name
                    G.add_edge(table_name, target_table, key=column.name)
    
    return G

# Usage
G = build_model_graph()

# Visualize the graph
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1500)
plt.title("Model Relationships")
plt.show()
```

## Testing

When testing with the registry, it's important to reset it between tests:

```python
import pytest
from uno.registry import UnoRegistry

@pytest.fixture
def clean_registry():
    """Fixture to provide a clean registry for each test."""
    registry = UnoRegistry.get_instance()
    registry.clear()
    return registry

def test_registry_registration(clean_registry):
    """Test model registration."""
    from uno.obj import UnoObj
    
    # Create a test model
    class TestModel:
        __tablename__ = "test_table"
    
    class TestObj(UnoObj):
        model = TestModel
    
    # Model should be registered automatically
    assert "test_table" in clean_registry.get_all()
    
    # Get the model
    model_class = clean_registry.get("test_table")
    assert model_class == TestObj
```

## Best Practices

1. **Use Singleton Instance**: Always use `get_instance()` to get the registry instead of creating a new instance.

2. **Don't Modify Directly**: Avoid modifying the registry's internal data structures directly.

3. **Clear for Tests**: Always clear the registry between tests to ensure test isolation.

4. **Check for Existence**: When looking up models, always check if the result is `None`.

5. **Use Type Annotations**: Use proper type annotations when working with the registry.

6. **Graceful Recovery**: Implement graceful recovery for missing models rather than raising errors.

7. **Lazy Loading**: Consider implementing lazy loading for models to improve startup performance.
