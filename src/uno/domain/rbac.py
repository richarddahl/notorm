"""
Role-Based Access Control (RBAC) for the Uno framework.

This module provides a Role-Based Access Control system that integrates
with the authorization framework to provide fine-grained access control.
"""

import logging
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field

from uno.domain.authorization import (
    Permission,
    Role,
    AuthorizationService,
    get_authorization_service,
)
from uno.domain.application_services import ServiceContext
from uno.core.base.error import AuthorizationError


@dataclass
class User:
    """
    Represents a user in the RBAC system.

    Users can have roles assigned to them, which grant permissions.
    """

    id: str
    roles: Set[str] = field(default_factory=set)
    direct_permissions: Set[str] = field(default_factory=set)

    def add_role(self, role_name: str) -> None:
        """
        Add a role to this user.

        Args:
            role_name: The role name
        """
        self.roles.add(role_name)

    def remove_role(self, role_name: str) -> None:
        """
        Remove a role from this user.

        Args:
            role_name: The role name
        """
        self.roles.discard(role_name)

    def add_permission(self, permission: str) -> None:
        """
        Add a direct permission to this user.

        Args:
            permission: The permission string
        """
        self.direct_permissions.add(permission)

    def remove_permission(self, permission: str) -> None:
        """
        Remove a direct permission from this user.

        Args:
            permission: The permission string
        """
        self.direct_permissions.discard(permission)

    def has_role(self, role_name: str) -> bool:
        """
        Check if this user has a specific role.

        Args:
            role_name: The role name

        Returns:
            True if the user has the role, False otherwise
        """
        return role_name in self.roles

    def has_permission(self, permission: str, rbac_service: "RbacService") -> bool:
        """
        Check if this user has a specific permission.

        Args:
            permission: The permission string
            rbac_service: The RBAC service to use for role lookups

        Returns:
            True if the user has the permission, False otherwise
        """
        # Check direct permissions
        if permission in self.direct_permissions:
            return True

        # Check role permissions
        for role_name in self.roles:
            role = rbac_service.get_role(role_name)
            if role and role.has_permission(Permission.from_string(permission)):
                return True

        return False

    def get_all_permissions(self, rbac_service: "RbacService") -> list[str]:
        """
        Get all permissions this user has.

        Args:
            rbac_service: The RBAC service to use for role lookups

        Returns:
            List of permission strings
        """
        permissions = set(self.direct_permissions)

        # Add permissions from roles
        for role_name in self.roles:
            role = rbac_service.get_role(role_name)
            if role:
                for permission in role.permissions:
                    permissions.add(str(permission))

        return list(permissions)


class RbacService:
    """
    Service for managing Role-Based Access Control.

    This service provides methods for managing users, roles, and permissions,
    and for performing access control checks.
    """

    def __init__(self, authorization_service: Optional[AuthorizationService] = None):
        """
        Initialize the RBAC service.

        Args:
            authorization_service: Optional authorization service
        """
        self.authorization_service = (
            authorization_service or get_authorization_service()
        )
        self._roles: Dict[str, Role] = {}
        self._users: Dict[str, User] = {}
        self._logger = logging.getLogger(__name__)

    def create_role(self, name: str, permissions: list[str] | None = None) -> Role:
        """
        Create a new role.

        Args:
            name: The role name
            permissions: Optional list of permission strings

        Returns:
            The created role

        Raises:
            ValueError: If a role with the same name already exists
        """
        if name in self._roles:
            raise ValueError(f"Role already exists: {name}")

        # Convert permission strings to Permission objects
        permission_objects = []
        if permissions:
            for permission_str in permissions:
                permission_objects.append(Permission.from_string(permission_str))

        # Create the role
        role = Role(name, permission_objects)

        # Store the role
        self._roles[name] = role
        self._logger.debug(f"Created role: {name}")

        return role

    def get_role(self, name: str) -> Optional[Role]:
        """
        Get a role by name.

        Args:
            name: The role name

        Returns:
            The role if found, None otherwise
        """
        return self._roles.get(name)

    def update_role(self, name: str, permissions: list[str]) -> Optional[Role]:
        """
        Update a role's permissions.

        Args:
            name: The role name
            permissions: List of permission strings

        Returns:
            The updated role if found, None otherwise
        """
        role = self.get_role(name)
        if not role:
            return None

        # Convert permission strings to Permission objects
        permission_objects = [Permission.from_string(p) for p in permissions]

        # Update the role permissions (replace all)
        role = Role(name, permission_objects)
        self._roles[name] = role

        self._logger.debug(f"Updated role: {name}")
        return role

    def delete_role(self, name: str) -> bool:
        """
        Delete a role.

        Args:
            name: The role name

        Returns:
            True if the role was deleted, False if not found
        """
        if name not in self._roles:
            return False

        # Remove the role
        del self._roles[name]
        self._logger.debug(f"Deleted role: {name}")

        # Remove this role from all users
        for user in self._users.values():
            user.remove_role(name)

        return True

    def add_permission_to_role(self, role_name: str, permission: str) -> bool:
        """
        Add a permission to a role.

        Args:
            role_name: The role name
            permission: The permission string

        Returns:
            True if the permission was added, False if the role was not found
        """
        role = self.get_role(role_name)
        if not role:
            return False

        # Add the permission
        role.add_permission(Permission.from_string(permission))
        self._logger.debug(f"Added permission {permission} to role {role_name}")

        return True

    def remove_permission_from_role(self, role_name: str, permission: str) -> bool:
        """
        Remove a permission from a role.

        Args:
            role_name: The role name
            permission: The permission string

        Returns:
            True if the permission was removed, False if the role was not found
        """
        role = self.get_role(role_name)
        if not role:
            return False

        # Remove the permission
        role.remove_permission(Permission.from_string(permission))
        self._logger.debug(f"Removed permission {permission} from role {role_name}")

        return True

    def create_user(
        self,
        user_id: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            user_id: The user ID
            roles: Optional list of role names
            permissions: Optional list of direct permission strings

        Returns:
            The created user

        Raises:
            ValueError: If a user with the same ID already exists
        """
        if user_id in self._users:
            raise ValueError(f"User already exists: {user_id}")

        # Create the user
        user = User(id=user_id)

        # Add roles
        if roles:
            for role_name in roles:
                user.add_role(role_name)

        # Add direct permissions
        if permissions:
            for permission in permissions:
                user.add_permission(permission)

        # Store the user
        self._users[user_id] = user
        self._logger.debug(f"Created user: {user_id}")

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            The user if found, None otherwise
        """
        return self._users.get(user_id)

    def update_user(
        self,
        user_id: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> Optional[User]:
        """
        Update a user's roles and permissions.

        Args:
            user_id: The user ID
            roles: Optional list of role names (replaces all roles)
            permissions: Optional list of direct permission strings (replaces all direct permissions)

        Returns:
            The updated user if found, None otherwise
        """
        user = self.get_user(user_id)
        if not user:
            return None

        # Update roles if provided
        if roles is not None:
            user.roles = set(roles)

        # Update direct permissions if provided
        if permissions is not None:
            user.direct_permissions = set(permissions)

        self._logger.debug(f"Updated user: {user_id}")
        return user

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: The user ID

        Returns:
            True if the user was deleted, False if not found
        """
        if user_id not in self._users:
            return False

        # Remove the user
        del self._users[user_id]
        self._logger.debug(f"Deleted user: {user_id}")

        return True

    def add_role_to_user(self, user_id: str, role_name: str) -> bool:
        """
        Add a role to a user.

        Args:
            user_id: The user ID
            role_name: The role name

        Returns:
            True if the role was added, False if the user was not found
        """
        user = self.get_user(user_id)
        if not user:
            return False

        # Add the role
        user.add_role(role_name)
        self._logger.debug(f"Added role {role_name} to user {user_id}")

        return True

    def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: The user ID
            role_name: The role name

        Returns:
            True if the role was removed, False if the user was not found
        """
        user = self.get_user(user_id)
        if not user:
            return False

        # Remove the role
        user.remove_role(role_name)
        self._logger.debug(f"Removed role {role_name} from user {user_id}")

        return True

    def add_permission_to_user(self, user_id: str, permission: str) -> bool:
        """
        Add a direct permission to a user.

        Args:
            user_id: The user ID
            permission: The permission string

        Returns:
            True if the permission was added, False if the user was not found
        """
        user = self.get_user(user_id)
        if not user:
            return False

        # Add the permission
        user.add_permission(permission)
        self._logger.debug(f"Added permission {permission} to user {user_id}")

        return True

    def remove_permission_from_user(self, user_id: str, permission: str) -> bool:
        """
        Remove a direct permission from a user.

        Args:
            user_id: The user ID
            permission: The permission string

        Returns:
            True if the permission was removed, False if the user was not found
        """
        user = self.get_user(user_id)
        if not user:
            return False

        # Remove the permission
        user.remove_permission(permission)
        self._logger.debug(f"Removed permission {permission} from user {user_id}")

        return True

    def has_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: The user ID
            permission: The permission string

        Returns:
            True if the user has the permission, False otherwise
        """
        user = self.get_user(user_id)
        if not user:
            return False

        return user.has_permission(permission, self)

    def get_user_permissions(self, user_id: str) -> list[str]:
        """
        Get all permissions a user has.

        Args:
            user_id: The user ID

        Returns:
            List of permission strings
        """
        user = self.get_user(user_id)
        if not user:
            return []

        return user.get_all_permissions(self)

    def create_service_context(self, user_id: str) -> ServiceContext:
        """
        Create a service context for a user.

        Args:
            user_id: The user ID

        Returns:
            Service context with user's permissions

        Raises:
            ValueError: If the user does not exist
        """
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Get all permissions
        permissions = user.get_all_permissions(self)

        # Create and return the service context
        return ServiceContext(
            user_id=user_id, is_authenticated=True, permissions=permissions
        )

    async def authorize_user(
        self, user_id: str, resource: str, action: str, target: Optional[Any] = None
    ) -> bool:
        """
        Check if a user is authorized to perform an action on a resource.

        Args:
            user_id: The user ID
            resource: The resource
            action: The action
            target: Optional target object

        Returns:
            True if authorized, False otherwise
        """
        user = self.get_user(user_id)
        if not user:
            return False

        # Create a service context
        context = self.create_service_context(user_id)

        # Check authorization
        return await self.authorization_service.authorize(
            context, resource, action, target
        )

    async def authorize_user_or_raise(
        self, user_id: str, resource: str, action: str, target: Optional[Any] = None
    ) -> None:
        """
        Check if a user is authorized and raise an exception if not.

        Args:
            user_id: The user ID
            resource: The resource
            action: The action
            target: Optional target object

        Raises:
            AuthorizationError: If authorization fails
        """
        if not await self.authorize_user(user_id, resource, action, target):
            permission = f"{resource}:{action}"
            raise AuthorizationError(
                f"User {user_id} is not authorized to {action} {resource}"
            )


# Create a default RBAC service
default_rbac_service = RbacService()


def get_rbac_service() -> RbacService:
    """Get the default RBAC service."""
    return default_rbac_service
