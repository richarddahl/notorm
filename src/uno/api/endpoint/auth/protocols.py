"""
Authentication and authorization protocols.

This module defines protocols for authentication and authorization components in the unified endpoint framework.
"""

from typing import Any, Dict, List, Optional, Protocol

from fastapi import Request, Response

from .models import User


class AuthenticationBackend(Protocol):
    """Protocol for authentication backends."""
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """
        Authenticate a request and return a user if successful.
        
        Args:
            request: The FastAPI request
            
        Returns:
            A user if authentication is successful, None otherwise
        """
        ...
    
    async def on_error(self, request: Request, exc: Exception) -> Response:
        """
        Handle an authentication error.
        
        Args:
            request: The FastAPI request
            exc: The exception that occurred
            
        Returns:
            A response to send to the client
        """
        ...


class AuthorizationBackend(Protocol):
    """Protocol for authorization backends."""
    
    async def has_permission(self, user: User, permission: str, resource: Optional[str] = None) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: The user to check
            permission: The permission to check
            resource: Optional resource to check permission against
            
        Returns:
            True if the user has the permission, False otherwise
        """
        ...
    
    async def has_role(self, user: User, role: str) -> bool:
        """
        Check if a user has a specific role.
        
        Args:
            user: The user to check
            role: The role to check
            
        Returns:
            True if the user has the role, False otherwise
        """
        ...
    
    async def get_permissions(self, user: User) -> List[str]:
        """
        Get all permissions for a user.
        
        Args:
            user: The user to get permissions for
            
        Returns:
            List of permissions
        """
        ...
    
    async def get_roles(self, user: User) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            user: The user to get roles for
            
        Returns:
            List of roles
        """
        ...