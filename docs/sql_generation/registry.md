# Emission Registry

The `EmissionRegistry` class in uno manages the registration and retrieval of SQL emitters. It provides a central repository for all SQL emitters used in the application.

## Overview

The emission registry:

- Registers SQL emitters by type
- Retrieves emitters when needed
- Manages emitter configurations
- Provides a factory pattern for emitter creation

## Basic Usage

### Creating a Registry

```python
from uno.sql.registry import EmissionRegistry

# Create a registry
registry = EmissionRegistry()
```

### Registering Emitters

```python
from uno.sql.registry import EmissionRegistry
from uno.sql.emitters.table import TableEmitter
from uno.sql.builders.function import FunctionEmitter
from uno.sql.builders.trigger import TriggerEmitter

# Create a registry
registry = EmissionRegistry()

# Register emitters
registry.register_emitter("table", TableEmitter)
registry.register_emitter("function", FunctionEmitter)
registry.register_emitter("trigger", TriggerEmitter)
```

### Retrieving Emitters

```python
from uno.sql.registry import EmissionRegistry

# Get an emitter class
table_emitter_class = registry.get_emitter("table")

# Create an instance
table_emitter = table_emitter_class(model=CustomerModel)

# Generate SQL
sql = table_emitter.emit()
```

### Creating Emitters with Factory Methods

```python
from uno.sql.registry import EmissionRegistry

# Create a registry with factory methods
registry = EmissionRegistry()

# Register emitters
registry.register_emitter("table", TableEmitter)
registry.register_emitter("function", FunctionEmitter)
registry.register_emitter("trigger", TriggerEmitter)

# Create an emitter using the registry as a factory
table_emitter = registry.create_emitter("table", model=CustomerModel)
function_emitter = registry.create_emitter("function", name="my_function", body="...", return_type="INT")

# Generate SQL
table_sql = table_emitter.emit()
function_sql = function_emitter.emit()
```

## Advanced Usage

### Custom Emitter Registration

```python
from uno.sql.registry import EmissionRegistry
from uno.sql.emitter import BaseEmitter

# Create a custom emitter
class CustomEmitter(BaseEmitter):
    def __init__(self, custom_param):
        super().__init__()
        self.custom_param = custom_param
    
    def emit(self):
        return f"-- Custom SQL with {self.custom_param}"

# Register the custom emitter
registry = EmissionRegistry()
registry.register_emitter("custom", CustomEmitter)

# Create and use the custom emitter
custom_emitter = registry.create_emitter("custom", custom_param="example")
sql = custom_emitter.emit()
```

### Registry Configuration

```python
from uno.sql.registry import EmissionRegistry

# Create a registry with configuration
registry = EmissionRegistry(
    default_schema="app",
    default_owner="app_user"
)

# Retrieve configuration
schema = registry.get_config("default_schema")  # "app"
owner = registry.get_config("default_owner")    # "app_user"

# Update configuration
registry.set_config("default_schema", "new_schema")
```

### Batch Emission

```python
from uno.sql.registry import EmissionRegistry

# Create and configure registry
registry = EmissionRegistry()
registry.register_emitter("table", TableEmitter)
registry.register_emitter("function", FunctionEmitter)
registry.register_emitter("trigger", TriggerEmitter)

# Define models, functions, triggers
# ...

# Batch generate SQL
sql_statements = []

# Generate table SQL for multiple models
for model in [CustomerModel, OrderModel, ProductModel]:
    emitter = registry.create_emitter("table", model=model)
    sql_statements.append(emitter.emit())

# Generate function SQL
function_emitter = registry.create_emitter(
    "function",
    name="update_customer_status",
    params=[{"name": "customer_id", "type": "TEXT"}, {"name": "new_status", "type": "TEXT"}],
    return_type="INTEGER",
    body="UPDATE customer SET status = new_status WHERE id = customer_id; RETURN 1;",
    language="plpgsql"
)
sql_statements.append(function_emitter.emit())

# Combine all SQL
complete_sql = "\n\n".join(sql_statements)
```

## Common Patterns

### Application Initialization

```python
from uno.sql.registry import EmissionRegistry
from uno.sql.emitters.table import TableEmitter
from uno.sql.builders.function import FunctionEmitter
from uno.sql.emitters.security import SecurityEmitter

def initialize_emission_registry():
    """Initialize the emission registry for the application."""
    registry = EmissionRegistry(
        default_schema="app",
        default_owner="app_user"
    )
    
    # Register standard emitters
    registry.register_emitter("table", TableEmitter)
    registry.register_emitter("function", FunctionEmitter)
    registry.register_emitter("security", SecurityEmitter)
    
    # Register custom emitters
    registry.register_emitter("custom", CustomEmitter)
    
    return registry

# Initialize registry at application startup
app_registry = initialize_emission_registry()
```

### SQL Schema Generation

```python
from uno.sql.registry import EmissionRegistry

async def generate_schema_sql(models, registry):
    """Generate SQL for creating a database schema."""
    sql_statements = []
    
    # Generate SQL for each model
    for model in models:
        emitter = registry.create_emitter("table", model=model)
        sql_statements.append(emitter.emit())
    
    # Add custom SQL
    sql_statements.append("-- Custom SQL goes here")
    
    # Combine all SQL
    return "\n\n".join(sql_statements)
```

### Migration Generation

```python
from uno.sql.registry import EmissionRegistry

async def generate_migration(old_models, new_models, registry):
    """Generate a migration between old and new models."""
    sql_statements = []
    
    # Generate drop statements for removed models
    for model in old_models:
        if model not in new_models:
            emitter = registry.create_emitter("drop_table", model=model)
            sql_statements.append(emitter.emit())
    
    # Generate create statements for new models
    for model in new_models:
        if model not in old_models:
            emitter = registry.create_emitter("table", model=model)
            sql_statements.append(emitter.emit())
    
    # Generate alter statements for modified models
    for model in new_models:
        if model in old_models:
            emitter = registry.create_emitter("alter_table", old_model=old_models[model], new_model=model)
            sql_statements.append(emitter.emit())
    
    # Combine all SQL
    return "\n\n".join(sql_statements)
```

## Best Practices

1. **Centralize Registry**: Use a single emission registry instance throughout your application.

2. **Register at Startup**: Register all emitters during application initialization.

3. **Use Factory Methods**: Use the registry as a factory to create emitters.

4. **Configure Appropriately**: Set appropriate configuration values for your environment.

5. **Handle Missing Emitters**: Implement proper error handling for missing emitters.

6. **Test Thoroughly**: Test SQL generation with various models and parameters.

7. **Document Emitters**: Document custom emitters and their parameters.

8. **Validate Input**: Validate input parameters before passing them to emitters.

9. **Use Type Annotations**: Provide proper type annotations for better IDE support.

10. **Keep It Simple**: Avoid overly complex emitter hierarchies.