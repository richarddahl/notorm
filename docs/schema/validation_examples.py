# Examples of Schema Validation in Uno Framework

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import date, datetime
from pydantic import Field, field_validator, model_validator

from uno.schema.schema import UnoSchema, UnoSchemaConfig, PaginatedList, WithMetadata
from uno.schema.schema_manager import UnoSchemaManager
from uno.errors import ValidationContext


# ===== Basic Schema Examples =====

class UserSchema(UnoSchema):
    """Basic schema with required and optional fields."""
    id: str
    name: str
    email: str
    age: int = Field(ge=18, le=120)
    is_active: bool = True
    created_at: Optional[str] = None


# ===== Field Validation Examples =====

class UserWithValidation(UnoSchema):
    """Schema with various field validations."""
    
    # String validations
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    
    # Numeric validations
    age: int = Field(..., ge=18, le=120)
    score: float = Field(0.0, ge=0.0, le=100.0)
    
    # Field with description and examples
    bio: Optional[str] = Field(
        None, 
        max_length=500, 
        description="User's biography", 
        examples=["Software developer with 5 years of experience"]
    )


# ===== Custom Validators Examples =====

class UserWithCustomValidators(UnoSchema):
    """Schema with custom validators."""
    
    email: str
    password: str
    password_confirm: str
    
    @field_validator('email')
    def email_must_be_valid(cls, v):
        """Validate email format and normalize to lowercase."""
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        return v.lower()
    
    @field_validator('password_confirm')
    def passwords_match(cls, v, info):
        """Ensure password confirmation matches password."""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


# ===== Model Validators Example =====

class OrderSchema(UnoSchema):
    """Schema with model validators to validate relationships between fields."""
    
    order_date: date
    ship_date: Optional[date] = None
    
    @model_validator(mode='after')
    def check_dates(self) -> 'OrderSchema':
        """Ensure ship date is not before order date."""
        if self.ship_date and self.order_date and self.ship_date < self.order_date:
            raise ValueError('Ship date cannot be before order date')
        return self


# ===== Schema with Enumerations =====

class UserRole(str, Enum):
    """Enum for user roles."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class UserWithRoleSchema(UnoSchema):
    """Schema using enum validation."""
    
    id: str
    name: str
    role: UserRole  # Must be one of the enum values


# ===== Nested Schema Examples =====

class AddressSchema(UnoSchema):
    """Schema for address information."""
    
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str


class UserWithAddressSchema(UnoSchema):
    """Schema with nested address validation."""
    
    id: str
    name: str
    email: str
    address: AddressSchema  # Nested schema


# ===== List Schema Examples =====

class TagSchema(UnoSchema):
    """Schema for a tag."""
    
    name: str
    color: Optional[str] = None


class ArticleSchema(UnoSchema):
    """Schema with a list of nested schemas."""
    
    title: str
    content: str
    author_id: str
    tags: List[TagSchema] = []  # List of nested schemas


# ===== Paginated List Examples =====

class UserListSchema(PaginatedList[UserSchema]):
    """Paginated list of users."""
    pass


# ===== Schema with Metadata Example =====

class ProductWithMetadata(WithMetadata):
    """Schema inheriting metadata fields."""
    
    id: str
    name: str
    price: float
    # Inherits: created_at, updated_at, version, metadata


# ===== Conditional Validation Example =====

class PaymentSchema(UnoSchema):
    """Schema with conditional validation based on payment type."""
    
    payment_type: str  # "credit_card" or "bank_transfer"
    credit_card_number: Optional[str] = None
    bank_account: Optional[str] = None
    
    @model_validator(mode='after')
    def check_payment_fields(self) -> 'PaymentSchema':
        """Validate required fields based on payment type."""
        if self.payment_type == "credit_card" and not self.credit_card_number:
            raise ValueError("Credit card number is required for credit card payments")
        elif self.payment_type == "bank_transfer" and not self.bank_account:
            raise ValueError("Bank account is required for bank transfers")
        return self


# ===== Schema Manager Examples =====

def schema_manager_example():
    """Example usage of schema manager."""
    
    # Create configuration for different schema types
    view_config = UnoSchemaConfig(include_fields={"id", "name", "email"})
    edit_config = UnoSchemaConfig(exclude_fields={"created_at", "updated_at"})
    
    # Create schema manager with configurations
    manager = UnoSchemaManager({
        "view": view_config,
        "edit": edit_config,
    })
    
    # Create schemas for a model
    view_schema = manager.create_schema("view", UserSchema)
    edit_schema = manager.create_schema("edit", UserSchema)
    
    # Use the schemas
    user_data = {
        "id": "user123",
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "is_active": True
    }
    
    # Create instances of each schema
    view_user = view_schema(**user_data)
    edit_user = edit_schema(**user_data)
    
    # Get a list schema
    user_list_schema = manager.get_list_schema(UserSchema)
    
    # Create a list instance
    user_list = user_list_schema(
        items=[view_user, edit_user],
        total=2,
        page=1,
        page_size=10,
        pages=1
    )
    
    return {
        "view_user": view_user,
        "edit_user": edit_user,
        "user_list": user_list
    }


# ===== ValidationContext Example =====

def validate_user_data(user_data: Dict[str, Any]) -> ValidationContext:
    """Example of using ValidationContext for complex validation."""
    
    context = ValidationContext("User")
    
    # Basic field validation
    if not user_data.get("email"):
        context.add_error("email", "Email is required", "REQUIRED_FIELD")
    
    if "age" in user_data:
        age = user_data["age"]
        if not isinstance(age, int):
            context.add_error("age", "Age must be an integer", "TYPE_ERROR")
        elif age < 18 or age > 120:
            context.add_error("age", "Age must be between 18 and 120", "INVALID_AGE_RANGE")
    
    # Nested validation
    if "address" in user_data:
        address_context = context.nested("address")
        address = user_data["address"]
        
        if not isinstance(address, dict):
            address_context.add_error("", "Address must be an object", "TYPE_ERROR")
        else:
            if not address.get("city"):
                address_context.add_error("city", "City is required", "REQUIRED_FIELD")
                
            if not address.get("country"):
                address_context.add_error("country", "Country is required", "REQUIRED_FIELD")
    
    # Business rule validation
    if user_data.get("role") == "admin" and user_data.get("age", 0) < 21:
        context.add_error("role", "Admin users must be at least 21 years old", "INVALID_ROLE_FOR_AGE")
    
    return context


# ===== API Integration Example =====

def api_endpoint_example(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Example of schema validation in an API endpoint."""
    
    try:
        # Validate the request data
        user_schema = UserWithAddressSchema(**request_data)
        
        # Process the validated data (would typically save to database)
        user_id = "generated_id"
        
        # Return a response
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id,
            "data": user_schema.model_dump()
        }
    except Exception as e:
        # Handle validation errors
        return {
            "success": False,
            "message": "Validation failed",
            "errors": str(e)
        }


# ===== Database Integration Example =====

async def save_user_example(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Example of schema validation for database operations."""
    
    try:
        # Validate input data
        validated_user = UserSchema(**user_data)
        
        # In a real application, would save to database:
        # db = get_db_client()
        # result = await db.execute(
        #     "INSERT INTO users (id, name, email, age, is_active) VALUES ($1, $2, $3, $4, $5) RETURNING *",
        #     validated_user.id,
        #     validated_user.name,
        #     validated_user.email,
        #     validated_user.age,
        #     validated_user.is_active
        # )
        
        # For this example, we'll just return the validated data
        return {
            "success": True,
            "message": "User validated and would be saved to database",
            "data": validated_user.model_dump()
        }
    except Exception as e:
        return {
            "success": False, 
            "message": "Validation failed",
            "errors": str(e)
        }


# ===== Dynamic Schema Creation Example =====

def create_dynamic_schema(field_definitions: Dict[str, Dict[str, Any]]):
    """Example of creating a schema dynamically based on field definitions."""
    
    from pydantic import create_model
    
    fields = {}
    for name, field_def in field_definitions.items():
        field_type = field_def.get("type", str)
        field_required = field_def.get("required", True)
        field_default = ... if field_required else None
        
        # Add any additional field parameters
        field_params = {}
        if "min_length" in field_def:
            field_params["min_length"] = field_def["min_length"]
        if "max_length" in field_def:
            field_params["max_length"] = field_def["max_length"]
        if "description" in field_def:
            field_params["description"] = field_def["description"]
            
        # Create the field with type, default, and parameters
        if field_params:
            fields[name] = (field_type, Field(default=field_default, **field_params))
        else:
            fields[name] = (field_type, field_default)
    
    # Create schema dynamically
    return create_model("DynamicSchema", __base__=UnoSchema, **fields)


# ===== Usage Examples =====

def demonstrate_schemas():
    """Run through examples of schema usage."""
    
    print("===== Basic Schema Usage =====")
    user = UserSchema(id="123", name="John Doe", email="john@example.com", age=30)
    print(f"User: {user.model_dump()}")
    
    print("\n===== Field Validation =====")
    try:
        # This should fail validation (age < 18)
        UserWithValidation(username="johndoe", email="john@example.com", age=16, score=95.5)
    except Exception as e:
        print(f"Validation error (as expected): {e}")
    
    print("\n===== Nested Schemas =====")
    user_with_address = UserWithAddressSchema(
        id="456",
        name="Jane Smith",
        email="jane@example.com",
        address={
            "street": "123 Main St",
            "city": "Anytown",
            "postal_code": "12345",
            "country": "USA"
        }
    )
    print(f"User with address: {user_with_address.model_dump()}")
    
    print("\n===== Schema Manager =====")
    result = schema_manager_example()
    print(f"View schema fields: {list(result['view_user'].model_fields.keys())}")
    print(f"Edit schema fields: {list(result['edit_user'].model_fields.keys())}")
    print(f"List schema contains {len(result['user_list'].items)} items")
    
    print("\n===== ValidationContext =====")
    context = validate_user_data({
        "email": "",  # Missing email
        "age": 15,    # Age too young
        "role": "admin",  # Admin but too young
        "address": {
            "street": "123 Main St",
            # Missing city and country
        }
    })
    
    if context.has_errors():
        print("Validation errors:")
        for error in context.errors:
            print(f"- Field: {error['field']}, Message: {error['message']}, Code: {error['error_code']}")
    
    print("\n===== Dynamic Schema =====")
    field_defs = {
        "name": {"type": str, "required": True, "min_length": 2, "max_length": 50},
        "email": {"type": str, "required": True},
        "age": {"type": int, "required": False},
        "notes": {"type": str, "required": False, "description": "Additional notes about the user"}
    }
    
    DynamicSchema = create_dynamic_schema(field_defs)
    dynamic_instance = DynamicSchema(name="Dynamic User", email="dynamic@example.com")
    print(f"Dynamic schema fields: {list(dynamic_instance.model_fields.keys())}")
    print(f"Dynamic instance: {dynamic_instance.model_dump()}")


if __name__ == "__main__":
    demonstrate_schemas()