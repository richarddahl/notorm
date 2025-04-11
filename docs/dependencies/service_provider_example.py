"""
Example of using the Unified Service Provider pattern.

This example demonstrates how to use the ServiceProvider to access
various services in a type-safe and consistent manner.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from uno.dependencies import get_service_provider, initialize_services
from uno.dependencies.interfaces import SchemaManagerProtocol


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


def initialize_application():
    """Initialize the application's services."""
    print("Initializing application services...")
    
    # Initialize all services at the application's entry point
    initialize_services()
    
    # This demonstrates that the ServiceProvider is initialized
    provider = get_service_provider()
    config = provider.get_config()
    print(f"Application initialized with config: {config}")


def demo_service_provider():
    """Demonstrate the service provider pattern."""
    print("Demonstrating Service Provider pattern...")

    # Get the service provider
    service_provider = get_service_provider()
    
    # Get services by type
    config = service_provider.get_service(UnoConfigProtocol)
    print(f"Got config service: {config}")
    
    # Or use the specialized getters
    db_manager = service_provider.get_db_manager()
    print(f"Got DB manager service: {db_manager}")
    
    schema_manager = service_provider.get_schema_manager()
    print(f"Got schema manager service: {schema_manager}")


def demo_schema_management():
    """Demonstrate schema management with the service provider."""
    print("Demonstrating schema management through the service provider...")
    
    # Get the service provider
    service_provider = get_service_provider()
    
    # Get the schema manager service
    schema_manager = service_provider.get_schema_manager()
    
    # Create standard schemas for our model
    user_schemas = schema_manager.create_standard_schemas(UserModel)
    
    # Use different schemas for different purposes
    print(f"Created {len(user_schemas)} schemas for UserModel")
    
    # API schema - includes all fields
    api_schema = user_schemas["api"]
    
    # View schema - excludes private fields
    view_schema = user_schemas["view"]
    
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


if __name__ == "__main__":
    # This would be run in a real application context
    initialize_application()
    demo_service_provider()
    demo_schema_management()