# Schema Manager Service

The Schema Manager Service provides a centralized way to create and manage schemas for domain entities, data transfer objects (DTOs), and database models with proper dependency injection and configuration.

## Overview

Schemas in uno are Pydantic BaseModels used to communicate data between layers:
- Domain Layer (Domain Entities)
- Data Access Layer (Database Models)
- Application Layer (DTOs)
- API Layer (FastAPI endpoints)

The Schema Manager Service helps manage these schemas through dependency injection, making them easier to use, configure, and test.

## Usage

### Accessing the Schema Manager Service

```python
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()
```

### Creating Schemas for Domain Entities

```python
from dataclasses import dataclass
from datetime import datetime
from uno.dependencies import get_schema_manager
from typing import Optional

# Define a domain entity
@dataclass
class User:
    username: str
    email: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    id: str = ""

# Get the schema manager
schema_manager = get_schema_manager()

# Create a DTO from the domain entity
UserDTO = schema_manager.create_dto_from_entity(User)

# Create a specific schema for API responses
user_api_schema = schema_manager.create_schema("api", UserDTO)

# Or create all standard schemas at once
user_schemas = schema_manager.create_api_schemas(User)

# Access a specific schema
user_view_schema = user_schemas["view"]
```

### Using Schemas for Validation and Serialization

```python
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()

# Create API schemas for your domain entity
schemas = schema_manager.create_api_schemas(User)

# Use the schemas for validation and serialization
api_schema = schemas["api"]
view_schema = schemas["view"]
edit_schema = schemas["edit"]

# Create a DTO instance from input data (with validation)
user_data = {
    "username": "johndoe",
    "email": "john@example.com",
    "is_active": True
}
user_dto = api_schema(**user_data)

# Convert DTO to domain entity
user_entity = schema_manager.dto_to_entity(user_dto, User)

# Serialize a domain entity for API response (with field filtering)
api_response = schema_manager.entity_to_dict(user_entity, schema_type="api")

# Serialize a domain entity for viewing (excluding private fields)
view_data = schema_manager.entity_to_dict(user_entity, schema_type="view")

# Serialize a domain entity for editing (excluding system fields)
edit_form = schema_manager.entity_to_dict(user_entity, schema_type="edit")
```

## Standard Schema Configurations

The Schema Manager Service provides several standard schema configurations for creating DTOs and serialization schemas:

| Name | Description | Field Handling |
|------|-------------|---------------|
| `data` | For converting between domain entities and database models | All fields |
| `api` | For API responses and comprehensive data transfer | All fields |
| `edit` | For form editing and client-side updates | Excludes: created_at, updated_at, version |
| `view` | For read-only data presentation | Excludes: private_fields, password, secret_key |
| `list` | For paginated list views and summaries | Only includes: id, name, display_name, created_at |

You can add custom schema configurations using the `add_schema_config` method for specific use cases in your domain.

### List Schemas for Collection Endpoints

The Schema Manager also provides utilities for creating paginated list schemas:

```python
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()

# Create a list schema for paginated responses
UserListSchema = schema_manager.get_list_schema(User)

# Example usage in FastAPI endpoint
@router.get("/users/", response_model=UserListSchema)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    users = await user_repository.get_many(skip=skip, limit=limit)
    total = await user_repository.count()
    
    return {
        "items": [schema_manager.entity_to_dict(user, "list") for user in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

## Custom Schema Configurations

```python
from uno.schema.schema import UnoSchemaConfig
from uno.dependencies import get_schema_manager

# Get the schema manager
schema_manager = get_schema_manager()

# Create a custom schema configuration
admin_config = UnoSchemaConfig(
    include_only=False,
    exclude_fields={"deleted_at", "is_deleted"},
    orm_mode=True
)

# Add the custom configuration
schema_manager.add_schema_config("admin", admin_config)

# Create a custom DTO for admin purposes from domain entity
AdminUserDTO = schema_manager.create_dto_from_entity(
    User, 
    schema_config="admin"
)

# Create a schema using the custom configuration for an existing DTO
admin_schema = schema_manager.create_schema("admin", UserDTO)
```

## Domain Entity and DTO Conversion

```python
from uno.dependencies import get_schema_manager
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

# Define domain entities
@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    id: str = ""

@dataclass
class Customer:
    name: str
    email: str
    addresses: List[Address]
    created_at: Optional[datetime] = None
    id: str = ""

# Get the schema manager
schema_manager = get_schema_manager()

# Create DTOs from domain entities
AddressDTO = schema_manager.create_dto_from_entity(Address)
CustomerDTO = schema_manager.create_dto_from_entity(Customer)

# Convert between domain entities and DTOs
customer_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "addresses": [
        {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip_code": "12345"}
    ]
}

# Create DTO from data
customer_dto = CustomerDTO(**customer_data)

# Convert DTO to domain entity
customer_entity = schema_manager.dto_to_entity(customer_dto, Customer)

# Convert back to DTO
customer_dto_again = schema_manager.entity_to_dto(customer_entity, CustomerDTO)

# Convert to dictionary for API response
api_response = schema_manager.entity_to_dict(customer_entity, schema_type="api")
```

## Integration with FastAPI

The Schema Manager Service integrates well with FastAPI for request validation and response serialization:

```python
from fastapi import APIRouter, Depends
from typing import Annotated
from uno.dependencies import get_schema_manager, get_repository
from uno.domain.repositories import UserRepository

router = APIRouter()

# Define endpoint using appropriate DTOs
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    schema_manager = Depends(get_schema_manager),
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    # Convert DTO to domain entity
    user_entity = schema_manager.dto_to_entity(user_data, User)
    
    # Use the repository to create the user
    created_user = await user_repository.create(user_entity)
    
    # Return the created user after converting to response DTO
    return schema_manager.entity_to_dto(created_user, schema_type="view")
```

For more comprehensive API endpoint creation:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_schema_manager
from uno.api.endpoint_factory import create_crud_endpoints

router = APIRouter()

# Get schemas for your domain entity
schemas = schema_manager.create_api_schemas(User)

# Create CRUD endpoints automatically
user_endpoints = create_crud_endpoints(
    entity_class=User,
    prefix="/users",
    schemas=schemas,
    tags=["Users"]
)

# Register the endpoints with the router
router.include_router(user_endpoints)
```