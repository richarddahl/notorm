"""
Example of using the DTOManager with Dependency Injection.

This example demonstrates how to use the DTOManager to create
and manage DTOs for domain entities through dependency injection.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from uno.dependencies import get_dto_manager


# Define a model
class UserModel(BaseModel):
    """User model for demonstration."""
    id: str = Field(default="")
    username: str
    email: str
    display_name: str = Field(default="")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    password: Optional[str] = None
    private_fields: Dict[str, Any] = Field(default_factory=dict)


def demo_dto_management():
    """Demonstrate DTO management with DI."""
    # Get the DTO manager through dependency injection
    dto_manager = get_dto_manager()
    
    # Create standard DTOs for our model
    user_dtos = dto_manager.create_standard_dtos(UserModel)
    
    # Use different DTOs for different purposes
    
    # API DTO - includes all fields
    api_dto = user_dtos["api"]
    
    # View DTO - excludes private fields
    view_dto = user_dtos["view"]
    
    # Edit DTO - excludes system fields
    edit_dto = user_dtos["edit"]
    
    # List DTO - includes only essential fields
    list_dto = user_dtos["list"]
    
    # Data DTO - includes all fields
    data_dto = user_dtos["data"]
    
    # Create a model instance from input data
    user_data = {
        "username": "johndoe",
        "email": "john@example.com",
        "display_name": "John Doe",
        "is_active": True,
        "password": "secret123"
    }
    
    # Validate input data with API DTO
    user = api_dto(**user_data)
    
    # Serialize for API response
    api_response = api_dto.model_validate(user).model_dump()
    print("API Response (all fields):", api_response)
    
    # Serialize for view (excluding private fields)
    view_data = view_dto.model_validate(user).model_dump()
    print("View Data (no private fields):", view_data)
    
    # Serialize for editing (excluding system fields)
    edit_form = edit_dto.model_validate(user).model_dump()
    print("Edit Form (no system fields):", edit_form)
    
    # Serialize for list view (only essential fields)
    list_item = list_dto.model_validate(user).model_dump()
    print("List Item (only essential fields):", list_item)
    

if __name__ == "__main__":
    # This would be run in a real application context
    # where the DI container is already configured
    demo_dto_management()