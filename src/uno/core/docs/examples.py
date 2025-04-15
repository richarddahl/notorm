"""
Example documentation components for the documentation system.

This module contains examples and patterns for using the documentation system effectively.
"""

from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs
from uno.core.docs.extractors import extend_doc_extractor, DocExtractor
from typing import Dict, Any, List, Type, Optional


def generate_docs_example() -> None:
    """
    Example of generating documentation for the Uno framework.
    
    This example demonstrates how to generate documentation for your application
    using the Uno documentation system.
    """
    # Basic configuration
    config = DocGeneratorConfig(
        title="My API Documentation",
        description="Documentation for my API",
        version="1.0.0",
        formats=[DocFormat.MARKDOWN, DocFormat.OPENAPI],
        output_dir="docs/api",
        modules_to_document=["myapp.api", "myapp.models"]
    )
    
    # Generate documentation
    generate_docs(config)


def custom_extractor_example() -> None:
    """
    Example of creating a custom documentation extractor.
    
    This example demonstrates how to extend the documentation extraction system
    to handle custom components or metadata.
    """
    @extend_doc_extractor
    class CustomExtractor(DocExtractor):
        """Custom extractor for special components."""
        
        def can_extract(self, obj: Any) -> bool:
            """Check if this extractor can handle the given object."""
            return hasattr(obj, "__custom_doc__")
        
        def extract(self, obj: Any) -> Dict[str, Any]:
            """Extract documentation from the given object."""
            result = super().extract(obj)
            
            # Add custom documentation
            result["custom_docs"] = obj.__custom_doc__
            
            return result


def model_documentation_example() -> str:
    """
    Example of how to document models effectively.
    
    This example demonstrates best practices for documenting models in your application.
    """
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class User:
        """
        User model representing an application user.
        
        This model contains all the data associated with a user in the system,
        including their profile information and preferences.
        
        Attributes:
            id: Unique identifier for the user
            username: The user's login name
            email: The user's email address
            is_active: Whether the user account is active
            roles: List of roles assigned to the user
        
        Examples:
            ```python
            # Create a new user
            user = User(
                id="123",
                username="johndoe",
                email="john@example.com",
                is_active=True,
                roles=["user"]
            )
            ```
        """
        id: str
        username: str
        email: str
        is_active: bool = True
        roles: List[str] = None

    return inspect.getsource(User)


def endpoint_documentation_example() -> str:
    """
    Example of how to document API endpoints effectively.
    
    This example demonstrates best practices for documenting endpoints in your application.
    """
    async def get_user(user_id: str):
        """
        Retrieve a user by ID.
        
        This endpoint returns detailed information about a specific user,
        including their profile data and account status.
        
        Args:
            user_id: The unique identifier of the user to retrieve
            
        Returns:
            User information including profile and status
            
        Raises:
            404: If the user does not exist
            403: If the current user lacks permission to view this user
            
        Examples:
            ```
            GET /users/123
            
            Response:
            {
                "id": "123",
                "username": "johndoe",
                "email": "john@example.com",
                "is_active": true,
                "roles": ["user"]
            }
            ```
        """
        # Implementation would go here
        pass

    return inspect.getsource(get_user)


def comprehensive_docs_example() -> None:
    """
    Example of generating comprehensive documentation.
    
    This example demonstrates how to generate comprehensive documentation
    including API reference, guides, and examples.
    """
    # Configure documentation generation
    config = DocGeneratorConfig(
        title="Comprehensive API Documentation",
        description="Complete documentation for the application",
        version="1.0.0",
        formats=[
            DocFormat.MARKDOWN,
            DocFormat.OPENAPI,
            DocFormat.HTML
        ],
        output_dir="docs/complete",
        include_examples=True,
        include_source_links=True,
        include_toc=True,
        modules_to_document=[
            "myapp.api",
            "myapp.models",
            "myapp.services"
        ]
    )
    
    # Generate documentation
    generate_docs(config)


# Import inspect module for the source code examples
import inspect