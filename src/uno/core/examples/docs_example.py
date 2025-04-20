"""
Example showing how to use the documentation generation framework.

This module demonstrates how to configure and use the documentation
generation system to create comprehensive API documentation.
"""

import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs


# Example dataclass with documentation
@dataclass
class UserModel:
    """
    Represents a user in the system.

    This model contains user information including name, email, and roles.
    """

    # Field with documentation
    id: str
    """Unique identifier for the user"""

    name: str
    """Full name of the user"""

    email: str
    """Email address of the user"""

    roles: list[str] = field(default_factory=list)
    """List of roles assigned to the user"""

    is_active: bool = True
    """Whether the user account is active"""

    meta: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for the user"""

    # Example validator method (for documentation extraction)
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re

        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    # Example choices
    __roles_choices__ = ["admin", "user", "guest"]

    # Example metadata
    __metadata__ = {"version": "1.2.0"}

    # Example examples
    __examples__ = [
        {
            "name": "Admin User",
            "description": "Example of an admin user",
            "value": {
                "id": "usr_123456",
                "name": "Admin User",
                "email": "admin@example.com",
                "roles": ["admin"],
                "is_active": True,
                "meta": {"created_at": "2023-01-01T00:00:00Z"},
            },
        },
        {
            "name": "Regular User",
            "description": "Example of a regular user",
            "value": {
                "id": "usr_789012",
                "name": "Regular User",
                "email": "user@example.com",
                "roles": ["user"],
                "is_active": True,
                "meta": {},
            },
        },
    ]


# Example enum
class OrderStatus(Enum):
    """
    Status of an order in the system.

    This enum represents the possible states of an order.
    """

    PENDING = "pending"
    """Order has been created but not yet processed"""

    PROCESSING = "processing"
    """Order is being processed"""

    SHIPPED = "shipped"
    """Order has been shipped"""

    DELIVERED = "delivered"
    """Order has been delivered"""

    CANCELLED = "cancelled"
    """Order has been cancelled"""


# Example API endpoint function
def get_user(user_id: str) -> dict[str, Any]:
    """
    Retrieve a user by ID.

    This endpoint returns the user information for the specified user ID.

    :param user_id: The ID of the user to retrieve
    :return: User information
    :raises UserNotFoundError: If the user does not exist
    """
    # Implementation would go here
    return {
        "id": user_id,
        "name": "Example User",
        "email": "user@example.com",
        "roles": ["user"],
        "is_active": True,
        "meta": {},
    }


# Example API endpoint class
class UserResource:
    """
    API endpoints for user management.

    This resource provides endpoints for creating, retrieving, updating,
    and deleting users.
    """

    __path__ = "/api/users"

    def get(self, user_id: str) -> dict[str, Any]:
        """
        Retrieve a user by ID.

        :param user_id: The ID of the user to retrieve
        :return: User information
        :raises UserNotFoundError: If the user does not exist
        """
        # Implementation would go here
        return {
            "id": user_id,
            "name": "Example User",
            "email": "user@example.com",
            "roles": ["user"],
            "is_active": True,
            "meta": {},
        }

    def post(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new user.

        :param user_data: User information
        :return: Created user information
        :raises ValidationError: If the user data is invalid
        """
        # Implementation would go here
        return {
            "id": "usr_new",
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "roles": user_data.get("roles", []),
            "is_active": user_data.get("is_active", True),
            "meta": user_data.get("meta", {}),
        }

    def put(self, user_id: str, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Update a user.

        :param user_id: The ID of the user to update
        :param user_data: Updated user information
        :return: Updated user information
        :raises UserNotFoundError: If the user does not exist
        :raises ValidationError: If the user data is invalid
        """
        # Implementation would go here
        return {
            "id": user_id,
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "roles": user_data.get("roles", []),
            "is_active": user_data.get("is_active", True),
            "meta": user_data.get("meta", {}),
        }

    def delete(self, user_id: str) -> None:
        """
        Delete a user.

        :param user_id: The ID of the user to delete
        :raises UserNotFoundError: If the user does not exist
        """
        # Implementation would go here
        pass


def main():
    """
    Main function to demonstrate documentation generation.
    """
    # Create output directory
    output_dir = "docs/api_example"
    os.makedirs(output_dir, exist_ok=True)

    # Configure documentation generator
    config = DocGeneratorConfig(
        title="Example API Documentation",
        description="Documentation for the Example API",
        version="1.0.0",
        formats=[DocFormat.MARKDOWN, DocFormat.OPENAPI],
        output_dir=output_dir,
        include_source_links=True,
        include_examples=True,
        modules_to_document=["uno.core.examples.docs_example"],
    )

    # Generate documentation
    result = generate_docs(config)

    # Print results
    print(f"Documentation generated in {output_dir}")
    for format_name, files in result.items():
        print(f"{format_name} documentation: {len(files)} files")
        for filename in files:
            print(f"  - {filename}")


if __name__ == "__main__":
    main()
