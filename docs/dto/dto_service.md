# DTO Manager Service

The DTO Manager Service provides a centralized way to create and manage Data Transfer Objects (DTOs) for domain entities, database models, and API requests/responses with proper dependency injection and configuration.

## Overview

DTOs in Uno are Pydantic BaseModels used to transfer data between layers:
- Domain Layer (Domain Entities)
- Data Access Layer (Database Models)
- Application Layer (DTOs)
- API Layer (FastAPI endpoints)

The DTO Manager Service helps manage these DTOs through dependency injection, making them easier to use, configure, and test.

## Usage

### Accessing the DTO Manager Service

```python
from uno.dependencies import get_dto_manager

# Get the DTO manager
dto_manager = get_dto_manager()
```

### Creating DTOs for Domain Entities

```python
from dataclasses import dataclass
from datetime import datetime
from uno.dependencies import get_dto_manager
from typing import Optional

# Define a domain entity
@dataclass
class User:
    username: str
    email: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    id: str = ""

# Get the DTO manager
dto_manager = get_dto_manager()

# Create a DTO from the domain entity
UserDTO = dto_manager.create_dto_from_entity(User)

# Create a specific DTO for API responses
user_api_dto = dto_manager.create_dto("api", UserDTO)

# Or create all standard DTOs at once
user_dtos = dto_manager.create_api_dtos(User)

# Access a specific DTO
user_view_dto = user_dtos["view"]
```

### Using DTOs for Validation and Serialization

```python
from uno.dependencies import get_dto_manager

# Get the DTO manager
dto_manager = get_dto_manager()

# Create API DTOs for your domain entity
dtos = dto_manager.create_api_dtos(User)

# Use the DTOs for validation and serialization
api_dto = dtos["api"]
view_dto = dtos["view"]
edit_dto = dtos["edit"]

# Create a DTO instance from input data (with validation)
user_data = {
    "username": "johndoe",
    "email": "john@example.com",
    "is_active": True
}
user_dto = api_dto(**user_data)

# Convert DTO to domain entity
user_entity = dto_manager.dto_to_entity(user_dto, User)

# Serialize a domain entity for API response (with field filtering)
api_response = dto_manager.entity_to_dict(user_entity, dto_type="api")

# Serialize a domain entity for viewing (excluding private fields)
view_data = dto_manager.entity_to_dict(user_entity, dto_type="view")

# Serialize a domain entity for editing (excluding system fields)
edit_form = dto_manager.entity_to_dict(user_entity, dto_type="edit")
```

## Standard DTO Configurations

The DTO Manager Service provides several standard DTO configurations for creating DTOs and serialization models:

| Name | Description | Field Handling |
|------|-------------|---------------|
| `data` | For converting between domain entities and database models | All fields |
| `api` | For API responses and comprehensive data transfer | All fields |
| `edit` | For form editing and client-side updates | Excludes: created_at, updated_at, version |
| `view` | For read-only data presentation | Excludes: private_fields, password, secret_key |
| `list` | For paginated list views and summaries | Only includes: id, name, display_name, created_at |

You can add custom DTO configurations using the `add_dto_config` method for specific use cases in your domain.

### List DTOs for Collection Endpoints

The DTO Manager also provides utilities for creating paginated list DTOs:

```python
from uno.dependencies import get_dto_manager

# Get the DTO manager
dto_manager = get_dto_manager()

# Create a list DTO for paginated responses
UserListDTO = dto_manager.get_list_dto(User)

# Example usage in FastAPI endpoint
@router.get("/users/", response_model=UserListDTO)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    users = await user_repository.get_many(skip=skip, limit=limit)
    total = await user_repository.count()
    
    return {
        "items": [dto_manager.entity_to_dict(user, "list") for user in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

## Custom DTO Configurations

```python
from uno.dto import DTOConfig
from uno.dependencies import get_dto_manager

# Get the DTO manager
dto_manager = get_dto_manager()

# Create a custom DTO configuration
admin_config = DTOConfig(
    include_only=False,
    exclude_fields={"deleted_at", "is_deleted"},
    orm_mode=True
)

# Add the custom configuration
dto_manager.add_dto_config("admin", admin_config)

# Create a custom DTO for admin purposes from domain entity
AdminUserDTO = dto_manager.create_dto_from_entity(
    User, 
    dto_config="admin"
)

# Create a DTO using the custom configuration for an existing DTO class
admin_dto = dto_manager.create_dto("admin", UserDTO)
```

## Domain Entity and DTO Conversion

```python
from uno.dependencies import get_dto_manager
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

# Get the DTO manager
dto_manager = get_dto_manager()

# Create DTOs from domain entities
AddressDTO = dto_manager.create_dto_from_entity(Address)
CustomerDTO = dto_manager.create_dto_from_entity(Customer)

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
customer_entity = dto_manager.dto_to_entity(customer_dto, Customer)

# Convert back to DTO
customer_dto_again = dto_manager.entity_to_dto(customer_entity, CustomerDTO)

# Convert to dictionary for API response
api_response = dto_manager.entity_to_dict(customer_entity, dto_type="api")
```

## Integration with FastAPI

The DTO Manager Service integrates well with FastAPI for request validation and response serialization:

```python
from fastapi import APIRouter, Depends
from typing import Annotated
from uno.dependencies import get_dto_manager, get_repository
from uno.domain.repositories import UserRepository

router = APIRouter()

# Define endpoint using appropriate DTOs
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    dto_manager = Depends(get_dto_manager),
    user_repository: UserRepository = Depends(get_repository(UserRepository))
):
    # Convert DTO to domain entity
    user_entity = dto_manager.dto_to_entity(user_data, User)
    
    # Use the repository to create the user
    created_user = await user_repository.create(user_entity)
    
    # Return the created user after converting to response DTO
    return dto_manager.entity_to_dto(created_user, dto_type="view")
```

For more comprehensive API endpoint creation:

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_dto_manager
from uno.api.endpoint_factory import create_crud_endpoints

router = APIRouter()

# Get DTOs for your domain entity
dtos = dto_manager.create_api_dtos(User)

# Create CRUD endpoints automatically
user_endpoints = create_crud_endpoints(
    entity_class=User,
    prefix="/users",
    dtos=dtos,
    tags=["Users"]
)

# Register the endpoints with the router
router.include_router(user_endpoints)
```