# Schema Validation in uno Framework

## Overview

Schema validation is a critical component of uno, providing a robust mechanism to validate data at various points in your application:

- When receiving data through API endpoints
- When storing or retrieving data from the database
- When transforming data between different layers of your application
- When implementing business logic rules

The `UnoSchema` system builds upon Pydantic's powerful validation capabilities while adding uno-specific features for better integration with the framework.

## Core Components

### UnoSchema

`UnoSchema` is the base class for all schema definitions in uno. It extends Pydantic's `BaseModel` with additional functionality specific to uno:

```python
from uno.schema.schema import UnoSchema

class UserSchema(UnoSchema):
    id: str
    name: str
    email: str
    age: int
```

Key features of `UnoSchema`:

- Field inspection with `create_field_dict()` and `get_field_annotations()`
- Integration with error handling system
- Enhanced type safety with generics support
- Consistent serialization/deserialization behavior

### UnoSchemaConfig

`UnoSchemaConfig` provides configuration options for creating schemas. It allows you to control which fields are included or excluded from a schema:

```python
from uno.schema.schema import UnoSchemaConfig, UnoSchema

# Create a config that only includes specific fields
view_config = UnoSchemaConfig(include_fields={"id", "name", "email"})

# Create a config that excludes specific fields
edit_config = UnoSchemaConfig(exclude_fields={"created_at", "updated_at"})

# Create a config with a custom base class
class MetadataSchema(UnoSchema):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

metadata_config = UnoSchemaConfig(schema_base=MetadataSchema)
```

### UnoSchemaManager

`UnoSchemaManager` is responsible for creating and managing schemas for your models:

```python
from uno.schema.schema_manager import UnoSchemaManager

# Create a schema manager with configurations
manager = UnoSchemaManager({
    "view": UnoSchemaConfig(include_fields={"id", "name", "email"}),
    "edit": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"})
})

# Create schemas for a model
view_schema = manager.create_schema("view", UserModel)
edit_schema = manager.create_schema("edit", UserModel)

# Or create all schemas at once
schemas = manager.create_all_schemas(UserModel)
```

## Validation Options

### Field Validation

uno leverages Pydantic's field validation features, which include:

#### Basic Type Validation

```python
class UserSchema(UnoSchema):
    id: str  # Must be a string
    age: int  # Must be an integer
    is_active: bool  # Must be a boolean
```

#### Field Constraints

```python
from pydantic import Field

class UserSchema(UnoSchema):
    # String constraints
    username: str = Field(..., min_length=3, max_length=50)
    
    # Numeric constraints
    age: int = Field(..., ge=18, le=120)  # greater than or equal to 18, less than or equal to 120
    
    # String pattern matching with regex
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
```

#### Default Values

```python
class UserSchema(UnoSchema):
    name: str
    email: str
    is_active: bool = True  # Default value
    created_at: Optional[str] = Field(default=None)  # Optional with default None
```

#### Field Metadata

```python
class UserSchema(UnoSchema):
    name: str = Field(..., description="The user's full name")
    email: str = Field(..., description="The user's email address", examples=["user@example.com"])
    role: str = Field(..., description="The user's role", json_schema_extra={"enum": ["admin", "user", "guest"]})
```

### Custom Validators

#### Field Validators

You can add custom validation logic for individual fields using Pydantic's field validators:

```python
from pydantic import field_validator

class UserSchema(UnoSchema):
    email: str
    password: str
    password_confirm: str
    
    @field_validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        return v.lower()  # normalize email by lowercasing it
    
    @field_validator('password_confirm')
    def passwords_match(cls, v, values):
        password = values.data.get('password')
        if password and v != password:
            raise ValueError('Passwords do not match')
        return v
```

#### Model Validators

For validations that involve multiple fields, use model validators:

```python
from pydantic import model_validator

class OrderSchema(UnoSchema):
    order_date: date
    ship_date: Optional[date] = None
    
    @model_validator(mode='after')
    def check_dates(self) -> 'OrderSchema':
        if self.ship_date and self.order_date and self.ship_date < self.order_date:
            raise ValueError('Ship date cannot be before order date')
        return self
```

#### Root Validators (Deprecated in Pydantic v2)

If you're migrating from Pydantic v1, note that root validators have been replaced with model validators:

```python
# Pydantic v1 (deprecated)
@root_validator
def check_dates(cls, values):
    # validation logic
    return values

# Pydantic v2 (current)
@model_validator(mode='after')
def check_dates(self) -> 'ModelType':
    # validation logic
    return self
```

### Compound Validation with ValidationContext

For complex validation scenarios, especially those involving nested structures, uno provides a `ValidationContext` class:

```python
from uno.errors import ValidationContext

def validate_user_data(user_data: dict) -> ValidationContext:
    context = ValidationContext("User")
    
    # Basic field validation
    if not user_data.get("email"):
        context.add_error("email", "Email is required", "REQUIRED_FIELD")
    
    if "age" in user_data and (user_data["age"] < 18 or user_data["age"] > 120):
        context.add_error("age", "Age must be between 18 and 120", "INVALID_AGE_RANGE")
    
    # Nested validation
    if "address" in user_data:
        address_context = context.nested("address")
        
        if not user_data["address"].get("city"):
            address_context.add_error("city", "City is required", "REQUIRED_FIELD")
            
        if not user_data["address"].get("country"):
            address_context.add_error("country", "Country is required", "REQUIRED_FIELD")
    
    # Business rule validation
    if user_data.get("role") == "admin" and user_data.get("age", 0) < 21:
        context.add_error("role", "Admin users must be at least 21 years old", "INVALID_ROLE_FOR_AGE")
    
    return context
```

## Advanced Schema Features

### Generic Schemas with PaginatedList

uno provides a generic `PaginatedList` schema for working with paginated collections:

```python
from uno.schema.schema import PaginatedList
from typing import List, Optional

class UserSchema(UnoSchema):
    id: str
    name: str
    email: str

# Create a paginated list schema for users
class UserList(PaginatedList[UserSchema]):
    pass

# Use the schema
user_list = UserList(
    items=[
        UserSchema(id="1", name="John", email="john@example.com"),
        UserSchema(id="2", name="Jane", email="jane@example.com")
    ],
    total=2,
    page=1,
    page_size=10,
    pages=1
)
```

You can also create paginated list schemas dynamically using the schema manager:

```python
from uno.schema.schema_manager import UnoSchemaManager

manager = UnoSchemaManager()
user_list_schema = manager.get_list_schema(UserSchema)

# Create an instance
result = user_list_schema(
    items=[user1, user2],
    total=2,
    page=1,
    page_size=10,
    pages=1
)
```

### Metadata Schemas

uno includes a predefined `WithMetadata` schema for objects that have standard metadata fields:

```python
from uno.schema.schema import WithMetadata

class UserWithMetadata(WithMetadata):
    id: str
    name: str
    email: str
    # Inherits: created_at, updated_at, version, metadata fields
```

### Schema Transformation

You can transform data between different schemas:

```python
from uno.schema.schema import UnoSchema

class UserBase(UnoSchema):
    id: str
    name: str
    email: str
    password: str

class UserView(UnoSchema):
    id: str
    name: str
    email: str
    # password is excluded for security

# Transform a UserBase instance to UserView
user_base = UserBase(id="1", name="John", email="john@example.com", password="secret")
user_view = UserView(**user_base.model_dump(exclude={"password"}))
```

## Error Handling for Schemas

### Schema-Specific Errors

uno defines specific error types for schema operations:

- `SchemaNotFoundError`: When a schema is not found
- `SchemaAlreadyExistsError`: When attempting to create a duplicate schema
- `SchemaInvalidError`: When a schema is invalid
- `SchemaValidationError`: When schema validation fails
- `SchemaFieldMissingError`: When a required field is missing
- `SchemaFieldTypeMismatchError`: When a field type doesn't match the expected type
- `SchemaConversionError`: When schema conversion fails

These errors include detailed context information:

```python
try:
    validated_user = UserSchema(**user_data)
except ValidationError as e:
    # Access validation error details
    for error in e.validation_errors:
        print(f"Field: {error['field']}, Error: {error['message']}, Code: {error['error_code']}")
```

### Customizing Error Messages

You can customize error messages in field definitions:

```python
from pydantic import Field

class UserSchema(UnoSchema):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="The user's username",
        json_schema_extra={
            "error_messages": {
                "min_length": "Username must be at least 3 characters",
                "max_length": "Username cannot exceed 50 characters"
            }
        }
    )
```

## Integration Examples

### With API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException
from uno.schema.schema import UnoSchema
from uno.schema.schema_manager import get_schema_manager

router = APIRouter()

class UserCreateSchema(UnoSchema):
    name: str
    email: str
    password: str

@router.post("/users/")
async def create_user(
    user_data: UserCreateSchema,
    schema_manager = Depends(get_schema_manager)
):
    try:
        # Get the view schema for the response
        UserViewSchema = schema_manager.get_schema("user_view")
        
        # Create the user (implementation details omitted)
        user = await create_user_in_db(user_data.model_dump())
        
        # Return the view representation
        return UserViewSchema(**user).model_dump()
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.validation_errors)
```

### With Database Operations

```python
from uno.schema.schema import UnoSchema
from uno.database.db_manager import get_db_client

class UserSchema(UnoSchema):
    id: str
    name: str
    email: str
    is_active: bool = True

async def save_user(user_data: dict):
    # Validate input data
    validated_user = UserSchema(**user_data)
    
    # Get database client
    db = get_db_client()
    
    # Save to database
    result = await db.execute(
        "INSERT INTO users (id, name, email, is_active) VALUES ($1, $2, $3, $4) RETURNING *",
        validated_user.id,
        validated_user.name,
        validated_user.email,
        validated_user.is_active
    )
    
    return result
```

### With Business Logic

```python
from uno.schema.schema import UnoSchema
from uno.errors import ValidationContext
from typing import Optional

class UserUpdateSchema(UnoSchema):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class UserService:
    async def update_user(self, user_id: str, update_data: dict):
        # Validate input with schema
        validated_data = UserUpdateSchema(**update_data).model_dump(exclude_unset=True)
        
        # Additional business rule validation
        context = ValidationContext("User")
        
        # Only admins can update roles
        if "role" in validated_data and not self.current_user.is_admin:
            context.add_error("role", "Only admins can update roles", "PERMISSION_DENIED")
        
        # Email must be unique
        if "email" in validated_data and await self.email_exists(validated_data["email"], exclude_id=user_id):
            context.add_error("email", "Email already exists", "DUPLICATE_EMAIL")
        
        # Check for validation errors
        if context.has_errors():
            context.raise_if_errors()
        
        # Proceed with update
        return await self.user_repository.update(user_id, validated_data)
```

## Best Practices

1. **Define Clear Schema Purposes**: Create separate schemas for different operations (view, edit, create, etc.)

2. **Validate Early**: Validate input data as early as possible to prevent invalid data from propagating

3. **Use Descriptive Error Messages**: Provide clear error messages that guide users on how to fix issues

4. **Leverage Schema Hierarchy**: Use inheritance to create schema hierarchies that reflect your domain model

5. **Add Documentation to Fields**: Use the `description` parameter to document fields for better API docs

6. **Separate Validation Logic**: For complex validation, separate business logic from schema definition

7. **Use Typed Schemas**: Leverage type annotations for better code completion and type checking

8. **Follow Naming Conventions**:
   - `CreateSchema` - For schemas used in creation operations
   - `UpdateSchema` - For schemas used in update operations
   - `ResponseSchema` - For schemas used in API responses
   - `ListSchema` - For schemas used in list operations

9. **Include Examples**: Add examples to schema definitions to improve API documentation

10. **Test Validation Logic**: Write comprehensive tests for schema validation, especially edge cases

## Common Validation Patterns

### Required vs Optional Fields

```python
class UserSchema(UnoSchema):
    # Required fields
    id: str
    name: str
    
    # Optional fields
    email: Optional[str] = None
    phone: Optional[str] = None
```

### Conditional Validation

```python
from pydantic import model_validator

class PaymentSchema(UnoSchema):
    payment_type: str  # "credit_card" or "bank_transfer"
    credit_card_number: Optional[str] = None
    bank_account: Optional[str] = None
    
    @model_validator(mode='after')
    def check_payment_fields(self) -> 'PaymentSchema':
        if self.payment_type == "credit_card" and not self.credit_card_number:
            raise ValueError("Credit card number is required for credit card payments")
        if self.payment_type == "bank_transfer" and not self.bank_account:
            raise ValueError("Bank account is required for bank transfers")
        return self
```

### Nested Validation

```python
class AddressSchema(UnoSchema):
    street: str
    city: str
    postal_code: str
    country: str

class UserSchema(UnoSchema):
    id: str
    name: str
    address: AddressSchema  # Nested schema validation
```

### List Validation

```python
class TagSchema(UnoSchema):
    name: str
    color: Optional[str] = None

class ArticleSchema(UnoSchema):
    title: str
    content: str
    tags: List[TagSchema] = []  # List of nested schemas
```

### Enum Validation

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

class UserSchema(UnoSchema):
    id: str
    name: str
    role: UserRole  # Must be one of the enum values
```

## Advanced Validation Techniques

### Custom Field Types

```python
from pydantic import constr, conint

class UserSchema(UnoSchema):
    # Constrained string with pattern
    username: constr(pattern=r"^[a-zA-Z0-9_]+$", min_length=3, max_length=50)
    
    # Constrained integer with range
    age: conint(ge=18, le=120)
```

### Custom Value Parsing

```python
from pydantic import field_validator
from datetime import datetime

class EventSchema(UnoSchema):
    name: str
    date: str  # ISO format date string
    
    @field_validator('date')
    def parse_date(cls, v):
        try:
            return datetime.fromisoformat(v).date()
        except ValueError:
            raise ValueError('Invalid date format. Use ISO format (YYYY-MM-DD)')
```

### Dynamic Field Validation

```python
from pydantic import create_model
from typing import Dict, Any

def create_dynamic_schema(field_definitions: Dict[str, Any]):
    fields = {}
    for name, field_def in field_definitions.items():
        field_type = field_def.get("type", str)
        field_required = field_def.get("required", True)
        field_default = ... if field_required else None
        
        fields[name] = (field_type, field_default)
    
    # Create schema dynamically
    return create_model("DynamicSchema", __base__=UnoSchema, **fields)
```