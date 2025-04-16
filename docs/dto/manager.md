# DTO Manager

The `DTOManager` class is responsible for creating and managing DTOs for domain entities and data models. It provides a clean interface for defining how model data is presented and validated in different contexts.

## Overview

DTOs in Uno are Pydantic models that define how data is structured when being sent to or received from clients. The `DTOManager` helps with:

- Creating DTOs from model and entity classes
- Managing DTO configurations
- Validating DTO definitions
- Accessing DTOs by name
- Converting between entities, models, and DTOs

## Basic Usage

### Creating a DTO Manager

```python
from uno.dto import DTOManager
from uno.dto import DTOConfig

# Create DTO configurations
dto_configs = {
    "view": DTOConfig(),  # All fields
    "edit": DTOConfig(exclude_fields={"created_at", "modified_at"}),
}

# Create the DTO manager
dto_manager = DTOManager(dto_configs)
```

### Creating DTOs for a Model

```python
from uno.domain.model import DomainModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from dataclasses import dataclass

# Define a database model
class CustomerModel(DomainModel):
    __tablename__ = "customer"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    
# Define a domain entity
@dataclass
class Customer:
    id: str
    name: str
    email: str
    created_at: datetime
    modified_at: datetime

# Create DTOs for the domain entity
dtos = dto_manager.create_all_dtos(Customer)

# Now you can access the DTOs
view_dto = dtos["view"]
edit_dto = dtos["edit"]
```

### Getting a DTO

```python
# Get a DTO by name
view_dto = dto_manager.get_dto("view")

if view_dto:
    # Use the DTO
    customer_data = view_dto(
        name="John Doe",
        email="john@example.com"
    )
```

## Advanced Usage

### Custom DTO Configurations

You can create custom DTO configurations for different use cases:

```python
from uno.dto import DTOConfig, UnoDTO

# Define a custom DTO base class
class SummaryDTO(UnoDTO):
    """Base class for summary DTOs with metadata."""
    
    class Config:
        json_schema_extra = {
            "description": "A summary view of the data"
        }

# Create configurations with different options
dto_configs = {
    "view": DTOConfig(),  # All fields
    "edit": DTOConfig(exclude_fields={"created_at", "modified_at"}),
    "summary": DTOConfig(
        dto_base=SummaryDTO,
        include_fields={"id", "name", "email"}
    ),
    "admin": DTOConfig(
        exclude_fields={"deleted_at"}
    ),
}

dto_manager = DTOManager(dto_configs)
```

### Adding DTO Configurations Dynamically

You can add DTO configurations after creating the manager:

```python
# Create a manager
dto_manager = DTOManager()

# Add configurations later
dto_manager.add_dto_config(
    "minimal",
    DTOConfig(include_fields={"id", "name"})
)
```

### Creating a Single DTO

```python
# Create just one DTO
minimal_dto = dto_manager.create_dto(
    "minimal",
    Customer
)
```

## DTO Validation

The `DTOManager` validates DTO configurations when creating DTOs:

1. It checks that all include/exclude fields exist in the entity or model
2. It ensures that a DTO doesn't have both include and exclude fields
3. It verifies that DTOs have at least one field

If validation fails, it raises a `UnoError` with a specific error code.

## Integration with Domain Services

The `DTOManager` is typically used inside domain service classes:

```python
from uno.dto import DTOManager, DTOConfig
from uno.dependencies import inject
from uno.domain.repositories import CustomerRepository

class CustomerService:
    """Service for managing customer entities."""
    
    @inject
    def __init__(self, repository: CustomerRepository):
        self.repository = repository
        self.dto_manager = DTOManager({
            "view": DTOConfig(),
            "edit": DTOConfig(exclude_fields={"created_at", "modified_at"}),
        })
        
        # Create all DTOs
        self.dto_manager.create_all_dtos(Customer)
        
    async def get_customer(self, customer_id: str) -> dict:
        """Get customer by ID."""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            return None
        
        # Convert to DTO and then to dict
        return self.dto_manager.entity_to_dict(customer, "view")
```

## Common Patterns

### DTO Inheritance

You can create DTO hierarchies using DTO base classes:

```python
from pydantic import BaseModel, Field
from uno.dto import UnoDTO, DTOConfig

# Base DTO with common fields
class BaseUserDTO(UnoDTO):
    class Config:
        extra = "forbid"  # Reject unknown fields

# Role-specific DTO
class AdminUserDTO(BaseUserDTO):
    role: str = Field("admin", const=True)
    permissions: list[str] = []

# Create configurations
dto_configs = {
    "view": DTOConfig(dto_base=BaseUserDTO),
    "admin": DTOConfig(dto_base=AdminUserDTO),
}

dto_manager = DTOManager(dto_configs)
```

### Conditional Fields

You can create DTOs with conditional field inclusion:

```python
from uno.dto import DTOConfig
from typing import Set

def get_fields_for_role(role: str) -> Set[str]:
    """Get the fields visible to a specific role."""
    base_fields = {"id", "name", "email"}
    
    if role == "admin":
        return base_fields | {"created_at", "modified_at", "is_active"}
    elif role == "manager":
        return base_fields | {"is_active"}
    else:
        return base_fields

# Create a role-specific DTO configuration
role = "manager"
dto_config = DTOConfig(include_fields=get_fields_for_role(role))

# Add it to the manager
dto_manager.add_dto_config(f"{role}_schema", dto_config)
```

### Using the Global DTO Manager

For convenience, Uno provides a global `DTOManager` instance:

```python
from uno.dto import get_dto_manager

# Get the global DTO manager instance
dto_manager = get_dto_manager()

# Configure it
dto_manager.add_dto_config("view", DTOConfig())
dto_manager.add_dto_config("edit", DTOConfig(exclude_fields={"created_at"}))

# Use it throughout your application
```

## Testing

When testing with the DTO manager, focus on validating DTO creation and field inclusion/exclusion:

```python
import pytest
from uno.dto import DTOManager, DTOConfig
from uno.errors import UnoError

def test_dto_creation():
    """Test creating DTOs for an entity."""
    # Setup
    dto_configs = {
        "view": DTOConfig(),
        "edit": DTOConfig(exclude_fields={"created_at"}),
    }
    
    dto_manager = DTOManager(dto_configs)
    
    # Define a test entity class
    class TestEntity:
        id: str
        name: str
        email: str
        created_at: datetime
    
    # Create DTOs
    dtos = dto_manager.create_all_dtos(TestEntity)
    
    # Assert DTOs were created
    assert "view" in dtos
    assert "edit" in dtos
    
    # Check field inclusion/exclusion
    view_dto = dtos["view"]
    edit_dto = dtos["edit"]
    
    assert "created_at" in view_dto.model_fields
    assert "created_at" not in edit_dto.model_fields

def test_invalid_dto_config():
    """Test validation of DTO configurations."""
    # Both include and exclude fields - should fail
    with pytest.raises(UnoError) as excinfo:
        invalid_config = DTOConfig(
            include_fields={"id", "name"},
            exclude_fields={"created_at"}
        )
        
        class TestEntity:
            id: str
            name: str
            created_at: datetime
            
        dto_manager = DTOManager({"invalid": invalid_config})
        dto_manager.create_dto("invalid", TestEntity)
    
    assert "BOTH_EXCLUDE_INCLUDE_FIELDS" in str(excinfo.value)
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