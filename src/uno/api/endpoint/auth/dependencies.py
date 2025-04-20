"""
Authentication and authorization dependencies.

This module provides FastAPI dependencies for authentication and authorization in the unified endpoint framework.
"""

from typing import Callable, List, Optional, Union

from fastapi import Depends, Request

from .exceptions import AuthenticationError, AuthorizationError
from .models import UserContext, Permission


def get_user_context(request: Request) -> UserContext:
    """
    Get the user context from the request.

    Args:
        request: The FastAPI request

    Returns:
        The user context

    Raises:
        AuthenticationError: If the user context is not found in the request state
    """
    if not hasattr(request.state, "user_context"):
        raise AuthenticationError("User context not found")
    return request.state.user_context


class RequireRoles:
    """Dependency for requiring specific roles."""

    def __init__(self, roles: list[str]):
        """
        Initialize the role requirement.

        Args:
            roles: List of required roles (user must have at least one)
        """
        self.roles = roles

    async def __call__(
        self, user_context: UserContext = Depends(get_user_context)
    ) -> None:
        """
        Check if the user has any of the required roles.

        Args:
            user_context: The user context

        Raises:
            AuthenticationError: If the user is not authenticated
            AuthorizationError: If the user does not have any of the required roles
        """
        if not user_context.is_authenticated:
            raise AuthenticationError("Authentication required")

        for role in self.roles:
            if user_context.has_role(role):
                return

        raise AuthorizationError(f"Required role not found: {', '.join(self.roles)}")


class RequirePermissions:
    """Dependency for requiring specific permissions."""

    def __init__(self, permissions: list[str]):
        """
        Initialize the permission requirement.

        Args:
            permissions: List of required permissions (user must have all)
        """
        self.permissions = permissions

    async def __call__(
        self, user_context: UserContext = Depends(get_user_context)
    ) -> None:
        """
        Check if the user has all of the required permissions.

        Args:
            user_context: The user context

        Raises:
            AuthenticationError: If the user is not authenticated
            AuthorizationError: If the user does not have all of the required permissions
        """
        if not user_context.is_authenticated:
            raise AuthenticationError("Authentication required")

        for permission in self.permissions:
            if not user_context.has_permission(permission):
                raise AuthorizationError(f"Required permission not found: {permission}")


def requires_auth(
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> Callable:
    """
    Decorator for requiring authentication and authorization.

    This decorator adds dependencies for user context and optionally roles and permissions.

    Args:
        roles: Optional list of required roles (user must have at least one)
        permissions: Optional list of required permissions (user must have all)

    Returns:
        A callable dependency that checks authentication and authorization
    """
    dependencies = [Depends(get_user_context)]

    if roles:
        dependencies.append(Depends(RequireRoles(roles)))

    if permissions:
        dependencies.append(Depends(RequirePermissions(permissions)))

    def dependency() -> None:
        pass

    dependency.__dependencies__ = dependencies
    return Depends(dependency)
