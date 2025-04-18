"""
Multi-tenant authorization for the Uno framework.

This module provides multi-tenant authorization support, allowing
the system to isolate data and access control between tenants.
"""

import logging
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field

from uno.domain.authorization import (
    Permission,
    AuthorizationService,
    AuthorizationPolicy,
    TenantPolicy,
)
from uno.domain.rbac import RbacService, User, Role
from uno.domain.application_services import ServiceContext
from uno.core.base.error import AuthorizationError


@dataclass
class Tenant:
    """
    Represents a tenant in the system.

    Tenants are isolated domains within the system, with their own
    users, roles, and permissions.
    """

    id: str
    name: str
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: Any) -> bool:
        """
        Check if this tenant equals another.

        Args:
            other: The object to compare with

        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, Tenant):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash based on tenant ID.

        Returns:
            Hash value
        """
        return hash(self.id)


class TenantRbacService(RbacService):
    """
    RBAC service with multi-tenant support.

    This service extends the RbacService to provide
    tenant-specific roles and permissions.
    """

    def __init__(self, authorization_service: Optional[AuthorizationService] = None):
        """
        Initialize the tenant-aware RBAC service.

        Args:
            authorization_service: Optional authorization service
        """
        super().__init__(authorization_service)

        # Tenant-specific roles and users
        self._tenant_roles: Dict[str, Dict[str, Role]] = {}
        self._tenant_users: Dict[str, Dict[str, User]] = {}

        # Tenant info
        self._tenants: Dict[str, Tenant] = {}

        # User-tenant memberships
        self._user_tenants: Dict[str, Set[str]] = {}

    def create_tenant(
        self, tenant_id: str, name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """
        Create a new tenant.

        Args:
            tenant_id: The tenant ID
            name: The tenant name
            metadata: Optional tenant metadata

        Returns:
            The created tenant

        Raises:
            ValueError: If a tenant with the same ID already exists
        """
        if tenant_id in self._tenants:
            raise ValueError(f"Tenant already exists: {tenant_id}")

        # Create the tenant
        tenant = Tenant(id=tenant_id, name=name, metadata=metadata or {})

        # Initialize tenant-specific collections
        self._tenants[tenant_id] = tenant
        self._tenant_roles[tenant_id] = {}
        self._tenant_users[tenant_id] = {}

        self._logger.debug(f"Created tenant: {tenant_id}")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by ID.

        Args:
            tenant_id: The tenant ID

        Returns:
            The tenant if found, None otherwise
        """
        return self._tenants.get(tenant_id)

    def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tenant]:
        """
        Update a tenant.

        Args:
            tenant_id: The tenant ID
            name: Optional new name
            active: Optional new active status
            metadata: Optional new metadata (replaces all metadata)

        Returns:
            The updated tenant if found, None otherwise
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        # Update fields
        if name is not None:
            tenant.name = name

        if active is not None:
            tenant.active = active

        if metadata is not None:
            tenant.metadata = metadata

        self._logger.debug(f"Updated tenant: {tenant_id}")
        return tenant

    def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.

        Args:
            tenant_id: The tenant ID

        Returns:
            True if the tenant was deleted, False if not found
        """
        if tenant_id not in self._tenants:
            return False

        # Remove the tenant
        del self._tenants[tenant_id]

        # Remove tenant-specific roles and users
        if tenant_id in self._tenant_roles:
            del self._tenant_roles[tenant_id]

        if tenant_id in self._tenant_users:
            del self._tenant_users[tenant_id]

        # Remove tenant from user memberships
        for user_id, tenants in list(self._user_tenants.items()):
            tenants.discard(tenant_id)
            if not tenants:
                del self._user_tenants[user_id]

        self._logger.debug(f"Deleted tenant: {tenant_id}")
        return True

    def create_role(
        self,
        name: str,
        permissions: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> Role:
        """
        Create a new role, optionally tenant-specific.

        Args:
            name: The role name
            permissions: Optional list of permission strings
            tenant_id: Optional tenant ID for tenant-specific roles

        Returns:
            The created role

        Raises:
            ValueError: If a role with the same name already exists in the tenant
        """
        if tenant_id is not None:
            # Tenant-specific role
            if tenant_id not in self._tenants:
                raise ValueError(f"Tenant not found: {tenant_id}")

            if tenant_id not in self._tenant_roles:
                self._tenant_roles[tenant_id] = {}

            if name in self._tenant_roles[tenant_id]:
                raise ValueError(f"Role already exists in tenant {tenant_id}: {name}")

            # Convert permission strings to Permission objects
            permission_objects = []
            if permissions:
                for permission_str in permissions:
                    permission_objects.append(Permission.from_string(permission_str))

            # Create the role
            role = Role(name, permission_objects)

            # Store the role
            self._tenant_roles[tenant_id][name] = role
            self._logger.debug(f"Created role {name} in tenant {tenant_id}")

            return role
        else:
            # Global role (use parent implementation)
            return super().create_role(name, permissions)

    def get_role(self, name: str, tenant_id: Optional[str] = None) -> Optional[Role]:
        """
        Get a role by name, optionally from a specific tenant.

        Args:
            name: The role name
            tenant_id: Optional tenant ID for tenant-specific roles

        Returns:
            The role if found, None otherwise
        """
        if tenant_id is not None:
            # Tenant-specific role
            tenant_roles = self._tenant_roles.get(tenant_id, {})
            return tenant_roles.get(name)
        else:
            # Global role
            return super().get_role(name)

    def update_role(
        self, name: str, permissions: List[str], tenant_id: Optional[str] = None
    ) -> Optional[Role]:
        """
        Update a role's permissions, optionally in a specific tenant.

        Args:
            name: The role name
            permissions: List of permission strings
            tenant_id: Optional tenant ID for tenant-specific roles

        Returns:
            The updated role if found, None otherwise
        """
        if tenant_id is not None:
            # Tenant-specific role
            role = self.get_role(name, tenant_id)
            if not role:
                return None

            # Convert permission strings to Permission objects
            permission_objects = [Permission.from_string(p) for p in permissions]

            # Update the role permissions (replace all)
            role = Role(name, permission_objects)
            self._tenant_roles[tenant_id][name] = role

            self._logger.debug(f"Updated role {name} in tenant {tenant_id}")
            return role
        else:
            # Global role
            return super().update_role(name, permissions)

    def delete_role(self, name: str, tenant_id: Optional[str] = None) -> bool:
        """
        Delete a role, optionally from a specific tenant.

        Args:
            name: The role name
            tenant_id: Optional tenant ID for tenant-specific roles

        Returns:
            True if the role was deleted, False if not found
        """
        if tenant_id is not None:
            # Tenant-specific role
            tenant_roles = self._tenant_roles.get(tenant_id, {})
            if name not in tenant_roles:
                return False

            # Remove the role
            del tenant_roles[name]
            self._logger.debug(f"Deleted role {name} from tenant {tenant_id}")

            # Remove this role from all users in the tenant
            tenant_users = self._tenant_users.get(tenant_id, {})
            for user in tenant_users.values():
                user.remove_role(name)

            return True
        else:
            # Global role
            return super().delete_role(name)

    def create_user(
        self,
        user_id: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> User:
        """
        Create a new user, optionally in a specific tenant.

        Args:
            user_id: The user ID
            roles: Optional list of role names
            permissions: Optional list of direct permission strings
            tenant_id: Optional tenant ID for tenant-specific users

        Returns:
            The created user

        Raises:
            ValueError: If a user with the same ID already exists in the tenant
        """
        if tenant_id is not None:
            # Tenant-specific user
            if tenant_id not in self._tenants:
                raise ValueError(f"Tenant not found: {tenant_id}")

            if tenant_id not in self._tenant_users:
                self._tenant_users[tenant_id] = {}

            if user_id in self._tenant_users[tenant_id]:
                raise ValueError(
                    f"User already exists in tenant {tenant_id}: {user_id}"
                )

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
            self._tenant_users[tenant_id][user_id] = user

            # Add user to tenant memberships
            if user_id not in self._user_tenants:
                self._user_tenants[user_id] = set()
            self._user_tenants[user_id].add(tenant_id)

            self._logger.debug(f"Created user {user_id} in tenant {tenant_id}")

            return user
        else:
            # Global user (use parent implementation)
            return super().create_user(user_id, roles, permissions)

    def get_user(self, user_id: str, tenant_id: Optional[str] = None) -> Optional[User]:
        """
        Get a user by ID, optionally from a specific tenant.

        Args:
            user_id: The user ID
            tenant_id: Optional tenant ID for tenant-specific users

        Returns:
            The user if found, None otherwise
        """
        if tenant_id is not None:
            # Tenant-specific user
            tenant_users = self._tenant_users.get(tenant_id, {})
            return tenant_users.get(user_id)
        else:
            # Global user
            return super().get_user(user_id)

    def get_user_tenants(self, user_id: str) -> List[str]:
        """
        Get the IDs of all tenants a user belongs to.

        Args:
            user_id: The user ID

        Returns:
            List of tenant IDs
        """
        return list(self._user_tenants.get(user_id, set()))

    def add_user_to_tenant(
        self,
        user_id: str,
        tenant_id: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
    ) -> bool:
        """
        Add a user to a tenant.

        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            roles: Optional list of role names to assign
            permissions: Optional list of direct permissions to assign

        Returns:
            True if the user was added, False if the tenant doesn't exist

        Raises:
            ValueError: If the user already exists in the tenant
        """
        # Check if tenant exists
        if tenant_id not in self._tenants:
            return False

        # Check if user already exists in tenant
        if tenant_id in self._tenant_users and user_id in self._tenant_users[tenant_id]:
            raise ValueError(f"User {user_id} already exists in tenant {tenant_id}")

        # Create or get user
        global_user = self.get_user(user_id)

        if global_user:
            # User exists globally, create tenant-specific user with same ID
            return self.create_user(user_id, roles, permissions, tenant_id) is not None
        else:
            # Create new user in tenant
            return self.create_user(user_id, roles, permissions, tenant_id) is not None

    def remove_user_from_tenant(self, user_id: str, tenant_id: str) -> bool:
        """
        Remove a user from a tenant.

        Args:
            user_id: The user ID
            tenant_id: The tenant ID

        Returns:
            True if the user was removed, False if not found
        """
        # Check if user exists in tenant
        if (
            tenant_id not in self._tenant_users
            or user_id not in self._tenant_users[tenant_id]
        ):
            return False

        # Remove user from tenant
        del self._tenant_users[tenant_id][user_id]

        # Remove tenant from user memberships
        if user_id in self._user_tenants:
            self._user_tenants[user_id].discard(tenant_id)
            if not self._user_tenants[user_id]:
                del self._user_tenants[user_id]

        self._logger.debug(f"Removed user {user_id} from tenant {tenant_id}")
        return True

    def has_permission(
        self, user_id: str, permission: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if a user has a specific permission, optionally in a specific tenant.

        Args:
            user_id: The user ID
            permission: The permission string
            tenant_id: Optional tenant ID to check in a specific tenant

        Returns:
            True if the user has the permission, False otherwise
        """
        if tenant_id is not None:
            # Check tenant-specific permission
            user = self.get_user(user_id, tenant_id)
            if not user:
                return False

            return user.has_permission(permission, self)
        else:
            # Check global permission
            return super().has_permission(user_id, permission)

    def get_user_permissions(
        self, user_id: str, tenant_id: Optional[str] = None
    ) -> List[str]:
        """
        Get all permissions a user has, optionally in a specific tenant.

        Args:
            user_id: The user ID
            tenant_id: Optional tenant ID to get permissions in a specific tenant

        Returns:
            List of permission strings
        """
        if tenant_id is not None:
            # Get tenant-specific permissions
            user = self.get_user(user_id, tenant_id)
            if not user:
                return []

            return user.get_all_permissions(self)
        else:
            # Get global permissions
            return super().get_user_permissions(user_id)

    def create_service_context(
        self, user_id: str, tenant_id: Optional[str] = None
    ) -> ServiceContext:
        """
        Create a service context for a user, optionally in a specific tenant.

        Args:
            user_id: The user ID
            tenant_id: Optional tenant ID to create context for a specific tenant

        Returns:
            Service context with user's permissions

        Raises:
            ValueError: If the user does not exist
        """
        # Get all permissions
        permissions = []

        # Add global permissions
        global_user = self.get_user(user_id)
        if global_user:
            permissions.extend(global_user.get_all_permissions(self))

        # Add tenant-specific permissions if requested
        if tenant_id is not None:
            tenant_user = self.get_user(user_id, tenant_id)
            if tenant_user:
                permissions.extend(tenant_user.get_all_permissions(self))

        # Create and return the service context
        context = ServiceContext(
            user_id=user_id,
            tenant_id=tenant_id,
            is_authenticated=True,
            permissions=permissions,
        )

        return context

    async def authorize_user(
        self,
        user_id: str,
        resource: str,
        action: str,
        target: Optional[Any] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a user is authorized to perform an action on a resource.

        Args:
            user_id: The user ID
            resource: The resource
            action: The action
            target: Optional target object
            tenant_id: Optional tenant ID for tenant-specific authorization

        Returns:
            True if authorized, False otherwise
        """
        # Create a service context
        context = self.create_service_context(user_id, tenant_id)

        # Check authorization
        return await self.authorization_service.authorize(
            context, resource, action, target
        )


class MultiTenantAuthorizationService(AuthorizationService):
    """
    Authorization service with multi-tenant support.

    This service extends the AuthorizationService to provide
    tenant-specific authorization policies.
    """

    def __init__(
        self,
        rbac_service: Optional[TenantRbacService] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the multi-tenant authorization service.

        Args:
            rbac_service: Optional RBAC service with tenant support
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.rbac_service = rbac_service or TenantRbacService()

        # Tenant-specific policies
        self._tenant_policies: Dict[str, Dict[str, AuthorizationPolicy]] = {}

    def register_policy(
        self, policy: AuthorizationPolicy, tenant_id: Optional[str] = None
    ) -> None:
        """
        Register an authorization policy, optionally for a specific tenant.

        Args:
            policy: The policy to register
            tenant_id: Optional tenant ID for tenant-specific policies
        """
        if tenant_id is not None:
            # Register tenant-specific policy
            if tenant_id not in self._tenant_policies:
                self._tenant_policies[tenant_id] = {}

            key = f"{policy.resource}:{policy.action}"
            self._tenant_policies[tenant_id][key] = policy
            self.logger.debug(f"Registered policy for {key} in tenant {tenant_id}")
        else:
            # Register global policy
            super().register_policy(policy)

    def get_policy(
        self, resource: str, action: str, tenant_id: Optional[str] = None
    ) -> Optional[AuthorizationPolicy]:
        """
        Get a policy for a specific resource and action, optionally from a specific tenant.

        Args:
            resource: The resource
            action: The action
            tenant_id: Optional tenant ID for tenant-specific policies

        Returns:
            The policy if found, None otherwise
        """
        key = f"{resource}:{action}"

        if tenant_id is not None:
            # Try to get tenant-specific policy first
            tenant_policies = self._tenant_policies.get(tenant_id, {})
            tenant_policy = tenant_policies.get(key)

            if tenant_policy:
                return tenant_policy

        # Fall back to global policy
        return super().get_policy(resource, action)

    async def authorize(
        self,
        context: ServiceContext,
        resource: str,
        action: str,
        target: Optional[Any] = None,
    ) -> bool:
        """
        Check if the user is authorized to perform the action on the resource.

        Args:
            context: The service context
            resource: The resource
            action: The action
            target: Optional target object

        Returns:
            True if authorized, False otherwise
        """
        # Get the policy
        policy = self.get_policy(resource, action, context.tenant_id)

        # If no policy is registered, check permissions
        if policy is None:
            # Create a simple policy that checks permissions
            from uno.domain.authorization import SimplePolicy

            policy = SimplePolicy(resource, action)

        # Apply the policy
        return await policy.authorize(context, target)

    def register_tenant_ownership_policy(
        self, resource: str, action: str, tenant_id: str, owner_field: str = "owner_id"
    ) -> None:
        """
        Register a tenant-specific ownership policy.

        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            tenant_id: The tenant ID
            owner_field: The field in the entity that identifies the owner
        """
        from uno.domain.authorization import OwnershipPolicy

        policy = OwnershipPolicy(resource, action, owner_field)
        self.register_policy(policy, tenant_id)

    def register_tenant_isolation_policy(
        self,
        resource: str,
        action: str,
        tenant_id: str,
        tenant_field: str = "tenant_id",
    ) -> None:
        """
        Register a tenant isolation policy.

        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            tenant_id: The tenant ID
            tenant_field: The field in the entity that identifies the tenant
        """
        policy = TenantPolicy(resource, action, tenant_field)
        self.register_policy(policy, tenant_id)


# Create a default multi-tenant authorization service
default_multi_tenant_auth_service = MultiTenantAuthorizationService()


def get_multi_tenant_auth_service() -> MultiTenantAuthorizationService:
    """Get the default multi-tenant authorization service."""
    return default_multi_tenant_auth_service
