# UnoObj Schema Initialization Guide

## Overview

In the Uno framework, schemas are used to control how model data is serialized and deserialized for different operations (viewing, editing, etc.). There are two main ways to initialize schemas for a `UnoObj` subclass:

1. **Automatic initialization** - happens when you create an instance of a `UnoObj` subclass
2. **Manual initialization** - explicitly creating schemas when needed

## Automatic Schema Initialization

When you create an instance of a `UnoObj` subclass, the schemas are automatically initialized in the `__init__` method:

```python
def __init__(self, **data: Any):```

"""
Initialize a UnoObj instance.
"""
super().__init__(**data)

# Initialize the db factory
self.db = UnoDBFactory(obj=self.__class__)

# Get the registry instance
self.registry = UnoRegistry.get_instance()

# Initialize the schema manager
self.schema_manager = UnoSchemaManager(self.__class__.schema_configs)

# Initialize the filter manager
self.filter_manager = UnoFilterManager()
```
```

The key part is `self.schema_manager = UnoSchemaManager(self.__class__.schema_configs)`, which creates a schema manager with the class's schema configurations.

## Accessing Schemas

Once an instance is created, you can access schemas in two ways:

1. **Through schema properties** - Many `UnoObj` subclasses define properties like `view_schema` and `edit_schema`
2. **Through the schema manager** - Using `obj.schema_manager.get_schema("schema_name")`

## Ensuring Schemas Are Created

Before using schemas, you should ensure they're created. The `UnoObj` class includes a helper method for this:

```python
def _ensure_schemas_created(self):```

"""
Ensure that schemas have been created.
"""
if not self.schema_manager.schemas:```

self.schema_manager.create_all_schemas(self.__class__)
```
```
```

This method is called by various operations like `to_model()` and `merge()`.

## Defining Custom Schema Configurations

To customize schemas for your `UnoObj` subclass, define the `schema_configs` class variable:

```python
class MyObj(UnoObj[MyModel]):```

model = MyModel
schema_configs = {```

"view_schema": UnoSchemaConfig(
    include={"id", "name", "description"},
    exclude={"created_by", "modified_by"}
),
"edit_schema": UnoSchemaConfig(
    include={"name", "description"},
    exclude={"id", "created_at", "modified_at"}
)
```
}
```
```

## Example Usage

Here's a complete example of defining and using schemas:

```python
from uno.obj import UnoObj
from uno.schema import UnoSchemaConfig
from myapp.models import MyModel

class MyObj(UnoObj[MyModel]):```

model = MyModel
schema_configs = {```

"view_schema": UnoSchemaConfig(
    include={"id", "name", "description"},
    exclude={"created_by", "modified_by"}
),
"edit_schema": UnoSchemaConfig(
    include={"name", "description"},
    exclude={"id", "created_at", "modified_at"}
)
```
}
```

# Create an instance
obj = MyObj(name="Test", description="A test object")

# Access schemas
view_schema_class = obj.schema_manager.get_schema("view_schema")
edit_schema_class = obj.schema_manager.get_schema("edit_schema")

# Or use the schema properties if defined
view_data = obj.view_schema.model_dump()
edit_data = obj.edit_schema.model_dump()

# Convert to model using a schema
model_instance = obj.to_model("edit_schema")
```
</qodoArtifact>