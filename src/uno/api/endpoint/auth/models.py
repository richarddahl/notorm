"""
Authentication and authorization models.

This module defines models related to authentication and authorization in the unified endpoint framework.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Permission(str, Enum):
    """Permissions for API endpoints."""

    # Resource-level permissions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Special permissions
    ADMIN = "admin"
    EXPORT = "export"
    IMPORT = "import"


class Role(BaseModel):
    """Role model for authorization."""

    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: list[str] = Field(default_factory=list, description="Role permissions")


class User(BaseModel):
    """User model for authentication."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")
    roles: list[str] = Field(default_factory=list, description="User roles")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="User metadata")


class UserContext:
    """Context for the current user."""

    def __init__(self, user: Optional[User] = None):
        """
        Initialize the user context.

        Args:
            user: The authenticated user, or None if not authenticated
        """
        self.user = user

    @property
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.

        Returns:
            True if the user is authenticated, False otherwise
        """
        return self.user is not None

    def has_role(self, role: str) -> bool:
        """
        Check if the user has a specific role.

        Args:
            role: The role to check

        Returns:
            True if the user has the role, False otherwise
        """
        if not self.is_authenticated:
            return False
        return role in self.user.roles

    def has_permission(self, permission: str) -> bool:
        """
        Check if the user has a specific permission.

        Args:
            permission: The permission to check

        Returns:
            True if the user has the permission, False otherwise
        """
        if not self.is_authenticated:
            return False
        return permission in self.user.permissions
