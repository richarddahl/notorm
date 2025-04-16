# Data Transfer Objects (DTOs) Overview

The DTO module in Uno provides a structured approach to data transfer between different layers of your application, following Domain-Driven Design principles.

## Introduction

Data Transfer Objects (DTOs) are immutable objects used to transfer data between different layers of an application. They help to:

- Decouple the domain model from the presentation layer
- Control what data is exposed through APIs
- Validate data during transfer and transformation
- Serialize and deserialize data efficiently
- Document API contracts

In Uno, DTOs are implemented using Pydantic `BaseModel` classes, which provide:
- Type validation
- Data conversion
- Schema generation for API documentation
- Serialization/deserialization to multiple formats (JSON, Dict, etc.)

## Core Components

The DTO module consists of several key components:

### `UnoDTO`

Base class for all DTOs in the Uno framework. It extends Pydantic's `BaseModel` and provides:

- Consistent configuration across all DTOs
- Additional utility methods for field information and manipulation
- Integration with Uno's dependency injection system

### `DTOConfig`

Configuration class for customizing how DTOs are created:

- Include/exclude specific fields
- Set base classes for inheritance
- Configure model validation settings
- Specify model configuration options

### `DTOManager`

Service for creating and managing DTOs:

- Create DTOs from domain entities or database models
- Cache DTOs for reuse
- Apply field filtering based on DTOs configuration
- Convert between different data representations (dict, entity, model)

### Specialized DTO Types

- `PaginatedListDTO`: For paginated responses with metadata
- `WithMetadataDTO`: For entities with common metadata fields (timestamps, version, etc.)

## Basic Usage

### Creating DTOs

```python
from uno.dto import UnoDTO
from typing import Optional, List
from datetime import datetime

# Define a basic DTO
class UserDTO(UnoDTO):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    is_active: bool = True

# Create an instance
user_dto = UserDTO(
    id="user123",
    username="johndoe",
    email="john@example.com",
    full_name="John Doe",
    created_at=datetime.now(),
    is_active=True
)

# Serialize to dictionary
user_dict = user_dto.model_dump()

# Serialize to JSON
user_json = user_dto.model_dump_json()
```

### Using DTOManager

```python
from uno.dto import UnoDTO, DTOConfig
from uno.dto.manager import DTOManager, get_dto_manager
from typing import Optional
from datetime import datetime

# Create a domain entity
class User:
    def __init__(self, id: str, username: str, email: str, password: str, 
                 full_name: Optional[str] = None, created_at: Optional[datetime] = None,
                 is_active: bool = True):
        self.id = id
        self.username = username
        self.email = email
        self.password = password  # This should not be exposed in API responses
        self.full_name = full_name
        self.created_at = created_at or datetime.now()
        self.is_active = is_active

# Create DTO configurations
dto_configs = {
    "view": DTOConfig(exclude_fields={"password"}),
    "edit": DTOConfig(exclude_fields={"password", "created_at", "id"}),
    "list": DTOConfig(include_fields={"id", "username", "full_name", "is_active"})
}

# Initialize the DTO manager
dto_manager = DTOManager(dto_configs)

# Create DTOs for the User entity
user_dtos = dto_manager.create_all_dtos(User)

# Access specific DTOs
UserViewDTO = user_dtos["view"]
UserEditDTO = user_dtos["edit"]
UserListDTO = user_dtos["list"]

# Create a user entity
user = User(
    id="user123",
    username="johndoe",
    email="john@example.com",
    password="secret_hash",
    full_name="John Doe"
)

# Convert entity to DTO
user_view_dto = dto_manager.entity_to_dto(user, "view")

# Serialize to dictionary for API response
user_response = user_view_dto.model_dump()
```

## Advanced Usage

### Custom Base Classes

```python
from uno.dto import UnoDTO, DTOConfig
from pydantic import Field

# Create a base DTO with common fields
class BaseUserDTO(UnoDTO):
    id: str = Field(description="Unique user identifier")
    created_at: datetime = Field(description="When the user was created")
    updated_at: Optional[datetime] = Field(None, description="When the user was last updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user123",
                "created_at": "2023-08-15T10:00:00Z",
                "updated_at": "2023-08-16T15:30:00Z"
            }
        }

# Create a DTO configuration that uses this base class
admin_config = DTOConfig(
    dto_base=BaseUserDTO,
    exclude_fields={"deleted_at"}
)

# Add the configuration to the manager
dto_manager.add_dto_config("admin", admin_config)

# Create a DTO using this configuration
AdminUserDTO = dto_manager.create_dto("admin", User)
```

### List DTOs for Pagination

```python
from uno.dto import PaginatedListDTO
from typing import List, Generic, TypeVar

T = TypeVar('T')

# Get the list DTO
UserListDTO = dto_manager.get_dto("list")

# Create a paginated list
paginated_users = PaginatedListDTO[UserListDTO](
    items=[
        UserListDTO(id="user1", username="user1", full_name="User One", is_active=True),
        UserListDTO(id="user2", username="user2", full_name="User Two", is_active=False)
    ],
    total=10,
    page=1,
    page_size=2
)

# Serialize to dictionary for API response
response = paginated_users.model_dump()
```

## Integration with FastAPI

DTOs integrate seamlessly with FastAPI for request validation and response serialization:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_dto_manager, get_repository
from uno.domain.repositories import UserRepository

router = APIRouter()
dto_manager = get_dto_manager()

# Create DTOs for the User entity
user_dtos = dto_manager.create_all_dtos(User)
UserCreateDTO = user_dtos["create"]
UserViewDTO = user_dtos["view"]

@router.post("/users/", response_model=UserViewDTO)
async def create_user(
    user_data: UserCreateDTO,
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    # Convert DTO to domain entity
    user_entity = dto_manager.dto_to_entity(user_data, User)
    
    # Use the repository to create the user
    created_user = await user_repository.create(user_entity)
    
    # Return the created user as a DTO
    return dto_manager.entity_to_dto(created_user, "view")
```

## Best Practices

1. **Define Clear DTO Purposes**: Each DTO should have a clear purpose (viewing, editing, summarizing, etc.).

2. **Use DTO Base Classes**: Create base DTO classes for common patterns to ensure consistency.

3. **Validate at Boundaries**: Use DTOs to validate data at application boundaries.

4. **Keep DTOs Simple**: Avoid complex logic in DTOs; use the domain layer for business logic.

5. **Document DTO Fields**: Add descriptions to DTO fields to improve API documentation.

6. **Be Consistent**: Use consistent naming conventions for DTOs across your application.

7. **Security First**: Always exclude sensitive fields from DTOs that will be exposed publicly.

8. **Test Thoroughly**: Test DTO creation, validation, and serialization/deserialization.

## Migration from Schema

If you're migrating from the legacy `UnoSchema` system, please see the [Schema to DTO Transition](/modernization/dto_transition.md) guide.