"""
Example of using the SchemaManagerService with Dependency Injection.

This example demonstrates how to use the SchemaManagerService to create
and manage schemas for UnoObj models through dependency injection.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from uno.dependencies import get_schema_manager


# Define a model
class UserModel(BaseModel):
    """User model for demonstration."""
    id: str = Field(default="")
    username: str
    email: str
    display_name: str = Field(default="")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True
    password: Optional[str] = None
    private_fields: Dict[str, Any] = Field(default_factory=dict)


def demo_schema_management():
    """Demonstrate schema management with DI."""
    # Get the schema manager through dependency injection
    schema_manager = get_schema_manager()
    
    # Create standard schemas for our model
    user_schemas = schema_manager.create_standard_schemas(UserModel)
    
    # Use different schemas for different purposes
    
    # API schema - includes all fields
    api_schema = user_schemas["api"]
    
    # View schema - excludes private fields
    view_schema = user_schemas["view"]
    
    # Edit schema - excludes system fields
    edit_schema = user_schemas["edit"]
    
    # List schema - includes only essential fields
    list_schema = user_schemas["list"]
    
    # Data schema - includes all fields
    data_schema = user_schemas["data"]
    
    # Create a model instance from input data
    user_data = {
        "username": "johndoe",
        "email": "john@example.com",
        "display_name": "John Doe",
        "is_active": True,
        "password": "secret123"
    }
    
    # Validate input data with API schema
    user = api_schema(**user_data)
    
    # Serialize for API response
    api_response = api_schema.model_validate(user).model_dump()
    print("API Response (all fields):", api_response)
    
    # Serialize for view (excluding private fields)
    view_data = view_schema.model_validate(user).model_dump()
    print("View Data (no private fields):", view_data)
    
    # Serialize for editing (excluding system fields)
    edit_form = edit_schema.model_validate(user).model_dump()
    print("Edit Form (no system fields):", edit_form)
    
    # Serialize for list view (only essential fields)
    list_item = list_schema.model_validate(user).model_dump()
    print("List Item (only essential fields):", list_item)
    

if __name__ == "__main__":
    # This would be run in a real application context
    # where the DI container is already configured
    demo_schema_management()