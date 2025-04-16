# DTO Manager

The `DTOManager` class and its service-level integration provide a centralized way to manage Data Transfer Objects (DTOs) for domain entities and data models in your API.

## Overview

The DTO Manager is responsible for:

- Creating and caching DTOs for domain entities and data models
- Enforcing field inclusion/exclusion rules for different DTO types
- Converting between domain entities, data models, and DTOs
- Managing serialization and deserialization of data
- Providing a type-safe approach to data transfer

## Getting Started

### Basic Usage

To use the DTO Manager in your API:

```python
from uno.dto import get_dto_manager, DTOConfig
from typing import Optional
from datetime import datetime

# Define a domain entity class
class User:
    def __init__(self, id: str, username: str, email: str, 
                 created_at: datetime, is_active: bool = True):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at
        self.is_active = is_active

# Get the global DTO manager
dto_manager = get_dto_manager()

# Configure the DTO manager with standard configurations
dto_manager.add_dto_config("view", DTOConfig())
dto_manager.add_dto_config("edit", DTOConfig(exclude_fields={"id", "created_at"}))
dto_manager.add_dto_config("list", DTOConfig(include_fields={"id", "username", "is_active"}))

# Create DTOs for the User entity
user_dtos = dto_manager.create_all_dtos(User)

# Access specific DTOs by name
UserViewDTO = user_dtos["view"]
UserEditDTO = user_dtos["edit"]
UserListDTO = user_dtos["list"]

# Create a DTO instance
user_dto = UserViewDTO(
    id="user123",
    username="johndoe",
    email="john@example.com",
    created_at=datetime.now(),
    is_active=True
)

# Convert DTO to dict
user_dict = user_dto.model_dump()
```

### Using with Dependency Injection

The DTO Manager is available through dependency injection in FastAPI:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_dto_manager, get_repository
from uno.domain.repositories import UserRepository

router = APIRouter()

@router.post("/users/", response_model=UserViewDTO)
async def create_user(
    user_data: UserCreateDTO,
    dto_manager = Depends(get_dto_manager),
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    # Convert DTO to domain entity
    user_entity = dto_manager.dto_to_entity(user_data, User)
    
    # Use the repository to create the user
    created_user = await user_repository.create(user_entity)
    
    # Convert entity to DTO and return
    return dto_manager.entity_to_dto(created_user, "view")
```

## Core Features

### Creating DTOs from Entities

```python
# Create a DTO for a specific configuration
UserViewDTO = dto_manager.create_dto("view", User)

# Create all configured DTOs at once
user_dtos = dto_manager.create_all_dtos(User)

# Create standard API DTOs (view, edit, list, create, detail)
api_dtos = dto_manager.create_api_dtos(User)
```

### Field Filtering

```python
# View DTO with all fields
view_config = DTOConfig()

# Edit DTO excluding system fields
edit_config = DTOConfig(exclude_fields={"id", "created_at", "updated_at"})

# List DTO with only essential fields
list_config = DTOConfig(include_fields={"id", "name", "status"})
```

### Entity-DTO Conversion

```python
# Convert an entity to a DTO
user_dto = dto_manager.entity_to_dto(user_entity, "view")

# Convert a DTO to an entity
user_entity = dto_manager.dto_to_entity(user_dto, User)

# Convert an entity to a dictionary using DTO rules
user_dict = dto_manager.entity_to_dict(user_entity, "view")

# Create an entity from a dictionary using DTO rules
user_entity = dto_manager.dict_to_entity(user_dict, User)
```

### List DTOs for Pagination

```python
# Get a list DTO for paginated responses
UserListDTO = dto_manager.get_list_dto(User)

# Create a paginated response
paginated_response = {
    "items": [dto_manager.entity_to_dict(user, "list") for user in users],
    "total": total_count,
    "page": page,
    "page_size": page_size
}
```

## Advanced Features

### Custom DTO Base Classes

```python
from uno.dto import UnoDTO, DTOConfig

# Create a custom DTO base class
class BaseUserDTO(UnoDTO):
    class Config:
        json_schema_extra = {
            "description": "User data transfer object"
        }

# Use it in a configuration
admin_config = DTOConfig(
    dto_base=BaseUserDTO,
    exclude_fields={"deleted_at"}
)

dto_manager.add_dto_config("admin", admin_config)
```

### Dynamic Field Selection

```python
from typing import Set

def get_fields_for_role(role: str) -> Set[str]:
    """Get fields visible to a specific role."""
    base_fields = {"id", "username", "email"}
    
    if role == "admin":
        return base_fields | {"created_at", "updated_at", "is_active", "role"}
    elif role == "manager":
        return base_fields | {"is_active", "role"}
    else:
        return base_fields

# Create a role-specific DTO
role = "manager"
fields = get_fields_for_role(role)
role_config = DTOConfig(include_fields=fields)

dto_manager.add_dto_config(f"{role}_view", role_config)
```

### Nested DTOs

```python
# Convert nested entities to DTOs
order_with_items_dto = dto_manager.entity_to_dto(
    order_entity, 
    "detail",
    nested_conversions={
        "items": ("list", ItemEntity),
        "customer": ("view", CustomerEntity)
    }
)
```

## Integration with FastAPI

### CRUD Endpoint Creation

```python
from uno.api.endpoint_factory import create_crud_endpoints
from fastapi import APIRouter, Depends
from uno.dependencies import get_dto_manager

router = APIRouter()
dto_manager = get_dto_manager()

# Create DTOs for the User entity
user_dtos = dto_manager.create_api_dtos(User)

# Create CRUD endpoints
user_router = create_crud_endpoints(
    entity_class=User,
    prefix="/users",
    tags=["Users"],
    dtos=user_dtos,
    repository_type=UserRepository
)

# Include the router
router.include_router(user_router)
```

### Request Body Validation

```python
from fastapi import APIRouter, Depends, HTTPException
from uno.dependencies import get_dto_manager, get_repository
from uno.domain.repositories import UserRepository

router = APIRouter()

@router.put("/users/{user_id}", response_model=UserViewDTO)
async def update_user(
    user_id: str,
    user_data: UserEditDTO,
    dto_manager = Depends(get_dto_manager),
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    # Get the existing user
    existing_user = await user_repository.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the user entity with DTO data
    updated_user = dto_manager.update_entity_from_dto(user_data, existing_user)
    
    # Save the updated user
    saved_user = await user_repository.update(updated_user)
    
    # Return the updated user as a view DTO
    return dto_manager.entity_to_dto(saved_user, "view")
```

## Best Practices

### 1. Define Clear DTO Purposes

Each DTO should have a clear, single purpose:

- **View DTOs**: For read-only presentation, may exclude sensitive fields
- **Edit DTOs**: For form editing, excludes read-only and system fields
- **List DTOs**: For collection listings, includes only essential fields
- **Detail DTOs**: For detailed views, includes relationships
- **Create DTOs**: For entity creation, includes required fields
- **Update DTOs**: For partial updates, all fields optional

### 2. Centralize DTO Configuration

Define DTO configurations in a central location:

```python
# In a config.py file
from uno.dto import DTOConfig

DEFAULT_DTO_CONFIGS = {
    "view": DTOConfig(),
    "edit": DTOConfig(exclude_fields={"id", "created_at", "updated_at"}),
    "list": DTOConfig(include_fields={"id", "name", "status"}),
    "create": DTOConfig(exclude_fields={"id", "created_at", "updated_at"}),
    "update": DTOConfig(exclude_fields={"id", "created_at", "updated_at"}, 
                        make_optional=True)
}
```

### 3. Use Type Annotations

Always use proper type annotations to leverage type checking:

```python
from typing import Dict, Type, TypeVar, Generic, List

T = TypeVar('T')
E = TypeVar('E')

def entity_to_dtos(
    entities: List[E], 
    entity_class: Type[E], 
    dto_type: str = "view"
) -> List[Dict]:
    """Convert a list of entities to DTOs."""
    return [dto_manager.entity_to_dict(entity, dto_type) for entity in entities]
```

### 4. Document DTOs

Add field descriptions using Pydantic's Field class:

```python
from pydantic import Field
from uno.dto import UnoDTO

class UserDTO(UnoDTO):
    id: str = Field(description="Unique identifier")
    username: str = Field(
        description="Username for login", 
        min_length=3, 
        max_length=50
    )
    email: str = Field(description="Email address")
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active"
    )
```

### 5. Validate at Boundaries

Use DTOs to validate data at application boundaries:

```python
@router.post("/users/")
async def create_user(user_data: UserCreateDTO):
    # Data is already validated by Pydantic
    # UserCreateDTO ensures all required fields are present
    # and validates field types, constraints, etc.
    ...
```