# Data Transfer Objects (DTOs)

## Overview

In uno, Data Transfer Objects (DTOs) are used to control how domain entity and model data is serialized and deserialized for different operations (viewing, editing, API requests/responses, etc.). The DTO system provides powerful validation capabilities to ensure data integrity throughout your application.

DTOs help enforce clear boundaries between:
- Domain models and API contracts
- Business logic and presentation layer
- Read and write operations

## Core Concepts

### UnoDTO

The `UnoDTO` class is the base class for all DTOs in uno. It extends Pydantic's `BaseModel` and provides additional functionality for field management, validation, and serialization.

```python
from uno.dto import UnoDTO
from pydantic import Field
from typing import Optional
from datetime import datetime

class UserDTO(UnoDTO):
    id: str
    username: str
    email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True, description="Whether the user is active")
```

### DTOConfig

The `DTOConfig` class allows you to customize how DTOs are generated:

```python
from uno.dto import DTOConfig

# Create configurations for different purposes
view_config = DTOConfig()  # All fields
edit_config = DTOConfig(exclude_fields={"id", "created_at", "updated_at"})
list_config = DTOConfig(include_fields={"id", "username", "is_active"})
```

### DTOManager

The `DTOManager` class creates and manages DTOs for different entities and purposes:

```python
from uno.dto import DTOManager, DTOConfig
from uno.dto import UnoDTO

# Create DTO configurations
dto_configs = {
    "view": DTOConfig(),  # All fields
    "edit": DTOConfig(exclude_fields={"created_at", "updated_at"}),
    "list": DTOConfig(include_fields={"id", "name", "email"}),
}

# Create the DTO manager
dto_manager = DTOManager(dto_configs)

# Create all configured DTOs for an entity
user_dtos = dto_manager.create_all_dtos(User)

# Access specific DTOs
UserViewDTO = user_dtos["view"]
UserEditDTO = user_dtos["edit"]
UserListDTO = user_dtos["list"]
```

## Using DTOs in UnoObj

When working with the UnoObj pattern, you can configure DTO generation at the class level:

```python
from uno.obj import UnoObj
from uno.dto import DTOConfig
from myapp.models import UserModel

class User(UnoObj[UserModel]):
    model = UserModel
    
    dto_configs = {
        "view": DTOConfig(),
        "edit": DTOConfig(exclude_fields={"created_at", "modified_at"}),
        "list": DTOConfig(include_fields={"id", "name", "email"}),
    }
    
    def __init__(self, **data):
        super().__init__(**data)
        # DTO manager is created with the provided dto_configs
        self.dto_manager = DTOManager(self.__class__.dto_configs)
        # Create all DTOs
        self.dto_manager.create_all_dtos(self.__class__)
```

## Accessing DTOs

Once you've created a DTO manager and DTOs, you can access them in two ways:

1. **Through the DTO manager** - Using `dto_manager.get_dto("dto_name")`
2. **Through the created DTO classes** - Directly using the returned DTO classes

## Using DTOs with FastAPI

DTOs integrate seamlessly with FastAPI for request/response handling:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_dto_manager

router = APIRouter()

@router.post("/users/", response_model=UserViewDTO)
async def create_user(
    user_data: UserCreateDTO,
    dto_manager = Depends(get_dto_manager)
):
    # Convert validated DTO to entity
    user_entity = dto_manager.dto_to_entity(user_data, User)
    
    # Process entity...
    created_user = await user_service.create(user_entity)
    
    # Return response DTO
    return dto_manager.entity_to_dto(created_user, "view")
```

## Specialized DTO Types

### PaginatedListDTO

For returning paginated collections of items:

```python
from uno.dto import PaginatedListDTO
from typing import List, Generic, TypeVar

T = TypeVar('T')

# Create a paginated response
response = PaginatedListDTO[UserListDTO](
    items=[user1_dto, user2_dto],
    total=100,
    page=1,
    page_size=10
)
```

### WithMetadataDTO

For objects that include common metadata fields:

```python
from uno.dto import WithMetadataDTO
from datetime import datetime

class AuditedDTO(WithMetadataDTO):
    name: str
    content: str
    
    # Automatically includes:
    # created_at: datetime
    # updated_at: Optional[datetime]
    # version: int
```

## Best Practices

1. **Clear Purpose**: Each DTO should have a specific purpose (view, edit, list, etc.)

2. **Field Documentation**: Document DTO fields with descriptions and examples

3. **Validation Rules**: Use Pydantic validators for field-level validation

4. **Security First**: Exclude sensitive fields from public-facing DTOs

5. **Consistent Naming**: Use consistent naming patterns for DTOs

6. **Minimize Duplication**: Use inheritance for common fields and validation rules

7. **Test Thoroughly**: Test DTO creation, validation, and serialization

8. **Keep DTOs Simple**: Avoid including complex business logic in DTOs

## Example: Complete DTO Configuration

```python
from uno.dto import UnoDTO, DTOConfig, DTOManager, PaginatedListDTO
from pydantic import Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# Base DTO with common fields
class BaseUserDTO(UnoDTO):
    id: str = Field(description="Unique identifier")
    created_at: datetime = Field(description="When the user was created")
    updated_at: Optional[datetime] = Field(None, description="When the user was last updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user123",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z"
            }
        }

# DTO for user creation
class UserCreateDTO(UnoDTO):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v

# Define DTO configurations
dto_configs = {
    "base": DTOConfig(dto_base=BaseUserDTO),
    "create": DTOConfig(dto_base=UserCreateDTO),
    "view": DTOConfig(
        dto_base=BaseUserDTO,
        exclude_fields={"password"}
    ),
    "edit": DTOConfig(
        exclude_fields={"id", "created_at", "updated_at", "password"}
    ),
    "list": DTOConfig(
        include_fields={"id", "username", "full_name", "is_active"}
    ),
}

# Create DTO manager
dto_manager = DTOManager(dto_configs)

# Create DTOs for User entity
user_dtos = dto_manager.create_all_dtos(User)

# Access DTOs
UserViewDTO = user_dtos["view"]
UserEditDTO = user_dtos["edit"]
UserListDTO = user_dtos["list"]
UserCreateDTO = user_dtos["create"]

# Create a paginated list DTO
UserPaginatedListDTO = PaginatedListDTO[UserListDTO]
```