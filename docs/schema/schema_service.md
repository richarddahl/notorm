# Schema Manager Service

The Schema Manager Service provides a centralized way to create and manage schemas for UnoObj models, with proper dependency injection and configuration.

## Overview

Schemas in Uno are Pydantic BaseModels used to communicate data between layers:
- Business logic (UnoObj)
- Database (UnoDB)
- FastAPI endpoints (UnoEndpoints)

The Schema Manager Service helps manage these schemas through dependency injection, making them easier to use, configure, and test.

## Usage

### Accessing the Schema Manager Service

```python
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()
```

### Creating Schemas for Models

```python
from pydantic import BaseModel, Field
from uno.dependencies import get_schema_manager
from typing import Optional

# Define your model
class UserModel(BaseModel):```

id: str = Field(default="")
username: str
email: str
created_at: Optional[str] = None
is_active: bool = True
```

# Get the schema manager
schema_manager = get_schema_manager()

# Create a specific schema
user_api_schema = schema_manager.create_schema("api", UserModel)

# Or create all standard schemas at once
user_schemas = schema_manager.create_standard_schemas(UserModel)

# Access a specific schema
user_view_schema = user_schemas["view"]
```

### Using Schemas for Validation and Serialization

```python
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()

# Create schemas for your model
schemas = schema_manager.create_standard_schemas(UserModel)

# Use the schemas for validation and serialization
api_schema = schemas["api"]
view_schema = schemas["view"]
edit_schema = schemas["edit"]

# Create a model instance from input data (with validation)
user_data = {```

"username": "johndoe",
"email": "john@example.com",
"is_active": True
```
}
user = api_schema(**user_data)

# Serialize a model for API response (with field filtering)
api_response = api_schema.from_orm(user_obj).dict()

# Serialize a model for viewing (excluding private fields)
view_data = view_schema.from_orm(user_obj).dict()

# Serialize a model for editing (excluding system fields)
edit_form = edit_schema.from_orm(user_obj).dict()
```

## Standard Schema Configurations

The Schema Manager Service provides several standard schema configurations:

| Name | Description | Field Handling |
|------|-------------|---------------|
| `data` | For storing data in the database | All fields |
| `api` | For API responses | All fields |
| `edit` | For form editing | Excludes: created_at, updated_at, version |
| `view` | For viewing data | Excludes: private_fields, password, secret_key |
| `list` | For list views | Only includes: id, name, display_name, created_at |

You can add custom schema configurations using the `add_schema_config` method.

## Custom Schema Configurations

```python
from uno.schema.schema import UnoSchemaConfig
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()

# Create a custom schema configuration
admin_config = UnoSchemaConfig(```

include_only=False,
exclude_fields={"deleted_at", "is_deleted"}
```
)

# Add the custom configuration
schema_manager.add_schema_config("admin", admin_config)

# Create a schema using the custom configuration
admin_schema = schema_manager.create_schema("admin", UserModel)
```

## Integration with FastAPI

The Schema Manager Service integrates well with FastAPI for request validation and response serialization:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_schema_manager

router = APIRouter()

@router.post("/users/")
async def create_user(```

user_data: dict,
schema_manager = Depends(get_schema_manager)
```
):```

# Get the API schema
user_schema = schema_manager.get_schema("api")
``````

```
```

# Validate the input data
validated_user = user_schema(**user_data)
``````

```
```

# Create the user
user_obj = await user_service.create_user(validated_user.dict())
``````

```
```

# Return the created user using the view schema
view_schema = schema_manager.get_schema("view")
return view_schema.from_orm(user_obj).dict()
```
```