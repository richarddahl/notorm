"""
Domain services for the Authorization module.

This module provides domain services that implement business logic for authorization entities,
coordinating entity validation and persistence through repositories.
"""

from typing import List, Dict, Any, Optional, Set, cast, Type, Generic, TypeVar
import logging

from uno.core.errors.result import Result
from uno.domain.service import UnoEntityService
from uno.enums import SQLOperation
from uno.authorization.entities import (
    User,
    Group,
    Role,
    Permission,
    ResponsibilityRole,
    Tenant,
)
from uno.authorization.domain_repositories import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    PermissionRepository,
    ResponsibilityRoleRepository,
    TenantRepository,
)


T = TypeVar("T")


class AuthorizationServiceError(Exception):
    """Base error class for authorization service errors."""

    pass


class UserService(UnoEntityService[User]):
    """Service for user entities."""

    def __init__(
        self,
        repository: Optional[UserRepository] = None,
        group_service: Optional["GroupService"] = None,
        role_service: Optional["RoleService"] = None,
        tenant_service: Optional["TenantService"] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the user service.

        Args:
            repository: The repository for data access
            group_service: Optional service for group operations
            role_service: Optional service for role operations
            tenant_service: Optional service for tenant operations
            logger: Optional logger
        """
        if repository is None:
            repository = UserRepository()

        super().__init__(User, repository, logger)

        self.group_service = group_service
        self.role_service = role_service
        self.tenant_service = tenant_service

    async def find_by_email(self, email: str) -> Result[Optional[User]]:
        """
        Find a user by email address.

        Args:
            email: The email address to search for

        Returns:
            Result containing the user if found
        """
        try:
            repository = cast(UserRepository, self.repository)
            result = await repository.find_by_email(email)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding user by email: {e}")
            return Failure(AuthorizationServiceError(f"Error finding user: {str(e)}"))

    async def find_by_handle(
        self, handle: str, tenant_id: str | None = None
    ) -> Result[Optional[User]]:
        """
        Find a user by handle, optionally within a specific tenant.

        Args:
            handle: The user handle to search for
            tenant_id: Optional tenant ID to restrict the search

        Returns:
            Result containing the user if found
        """
        try:
            repository = cast(UserRepository, self.repository)
            result = await repository.find_by_handle(handle, tenant_id)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding user by handle: {e}")
            return Failure(AuthorizationServiceError(f"Error finding user: {str(e)}"))

    async def find_by_tenant(
        self, tenant_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[User]]:
        """
        Find all users in a specific tenant.

        Args:
            tenant_id: The tenant ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of users
        """
        try:
            repository = cast(UserRepository, self.repository)
            results = await repository.find_by_tenant(tenant_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding users by tenant: {e}")
            return Failure(AuthorizationServiceError(f"Error finding users: {str(e)}"))

    async def find_by_group(
        self, group_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[User]]:
        """
        Find all users in a specific group.

        Args:
            group_id: The group ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of users
        """
        try:
            repository = cast(UserRepository, self.repository)
            results = await repository.find_by_group(group_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding users by group: {e}")
            return Failure(AuthorizationServiceError(f"Error finding users: {str(e)}"))

    async def find_by_role(
        self, role_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[User]]:
        """
        Find all users with a specific role.

        Args:
            role_id: The role ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of users
        """
        try:
            repository = cast(UserRepository, self.repository)
            results = await repository.find_by_role(role_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding users by role: {e}")
            return Failure(AuthorizationServiceError(f"Error finding users: {str(e)}"))

    async def find_superusers(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[User]]:
        """
        Find all superusers.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of superusers
        """
        try:
            repository = cast(UserRepository, self.repository)
            results = await repository.find_superusers(limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding superusers: {e}")
            return Failure(
                AuthorizationServiceError(f"Error finding superusers: {str(e)}")
            )

    async def get_with_relationships(self, id: str) -> Result[User]:
        """
        Get a user with its related entities.

        Args:
            id: The ID of the user

        Returns:
            Result containing the user with loaded relationships
        """
        try:
            repository = cast(UserRepository, self.repository)

            # Get repositories for related entities if services are available
            group_repo = None
            if self.group_service:
                group_repo = cast(GroupRepository, self.group_service.repository)

            role_repo = None
            if self.role_service:
                role_repo = cast(RoleRepository, self.role_service.repository)

            tenant_repo = None
            if self.tenant_service:
                tenant_repo = cast(TenantRepository, self.tenant_service.repository)

            # Get the user with relationships
            result = await repository.get_with_relationships(
                id, group_repo=group_repo, role_repo=role_repo, tenant_repo=tenant_repo
            )

            if not result:
                return Failure(AuthorizationServiceError(f"User {id} not found"))

            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting user with relationships: {e}")
            return Failure(AuthorizationServiceError(f"Error getting user: {str(e)}"))

    async def add_to_group(self, user_id: str, group_id: str) -> Result[User]:
        """
        Add a user to a group.

        Args:
            user_id: The ID of the user
            group_id: The ID of the group

        Returns:
            Result containing the updated user
        """
        try:
            # Get the user
            user_result = await self.get_by_id(user_id)
            if not user_result:
                return Failure(AuthorizationServiceError(f"User {user_id} not found"))

            user = user_result

            # Get the group
            if not self.group_service:
                return Failure(AuthorizationServiceError("Group service not available"))

            group_result = await self.group_service.get_by_id(group_id)
            if not group_result:
                return Failure(AuthorizationServiceError(f"Group {group_id} not found"))

            group = group_result

            # Add user to group
            user.add_to_group(group)

            # Save changes
            updated_user = await self.save(user)
            if not updated_user:
                return Failure(AuthorizationServiceError("Failed to save user"))

            return Success(updated_user)
        except Exception as e:
            self.logger.error(f"Error adding user to group: {e}")
            return Failure(
                AuthorizationServiceError(f"Error adding user to group: {str(e)}")
            )

    async def add_role(self, user_id: str, role_id: str) -> Result[User]:
        """
        Add a role to a user.

        Args:
            user_id: The ID of the user
            role_id: The ID of the role

        Returns:
            Result containing the updated user
        """
        try:
            # Get the user
            user_result = await self.get_by_id(user_id)
            if not user_result:
                return Failure(AuthorizationServiceError(f"User {user_id} not found"))

            user = user_result

            # Get the role
            if not self.role_service:
                return Failure(AuthorizationServiceError("Role service not available"))

            role_result = await self.role_service.get_by_id(role_id)
            if not role_result:
                return Failure(AuthorizationServiceError(f"Role {role_id} not found"))

            role = role_result

            # Add role to user
            user.add_role(role)

            # Save changes
            updated_user = await self.save(user)
            if not updated_user:
                return Failure(AuthorizationServiceError("Failed to save user"))

            return Success(updated_user)
        except Exception as e:
            self.logger.error(f"Error adding role to user: {e}")
            return Failure(
                AuthorizationServiceError(f"Error adding role to user: {str(e)}")
            )

    async def check_permission(
        self, user_id: str, meta_type_id: str, operation: SQLOperation
    ) -> Result[bool]:
        """
        Check if a user has a specific permission.

        Args:
            user_id: The ID of the user
            meta_type_id: The meta type ID
            operation: The SQL operation

        Returns:
            Result containing True if the user has the permission, False otherwise
        """
        try:
            # Get the user with relationships
            user_result = await self.get_with_relationships(user_id)
            if user_result.is_failure:
                return user_result

            user = user_result.value

            # Check if user is a superuser
            if user.is_superuser:
                return Success(True)

            # Check user's roles for the permission
            has_permission = user.has_permission(meta_type_id, operation)

            return Success(has_permission)
        except Exception as e:
            self.logger.error(f"Error checking user permission: {e}")
            return Failure(
                AuthorizationServiceError(f"Error checking permission: {str(e)}")
            )


class GroupService(UnoEntityService[Group]):
    """Service for group entities."""

    def __init__(
        self,
        repository: Optional[GroupRepository] = None,
        user_service: Optional[UserService] = None,
        tenant_service: Optional["TenantService"] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the group service.

        Args:
            repository: The repository for data access
            user_service: Optional service for user operations
            tenant_service: Optional service for tenant operations
            logger: Optional logger
        """
        if repository is None:
            repository = GroupRepository()

        super().__init__(Group, repository, logger)

        self.user_service = user_service
        self.tenant_service = tenant_service

    async def find_by_name(self, name: str, tenant_id: str) -> Result[Optional[Group]]:
        """
        Find a group by name in a specific tenant.

        Args:
            name: The group name to search for
            tenant_id: The tenant ID to restrict the search

        Returns:
            Result containing the group if found
        """
        try:
            repository = cast(GroupRepository, self.repository)
            result = await repository.find_by_name(name, tenant_id)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding group by name: {e}")
            return Failure(AuthorizationServiceError(f"Error finding group: {str(e)}"))

    async def find_by_tenant(
        self, tenant_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[Group]]:
        """
        Find all groups in a specific tenant.

        Args:
            tenant_id: The tenant ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of groups
        """
        try:
            repository = cast(GroupRepository, self.repository)
            results = await repository.find_by_tenant(tenant_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding groups by tenant: {e}")
            return Failure(AuthorizationServiceError(f"Error finding groups: {str(e)}"))

    async def find_by_user(
        self, user_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[Group]]:
        """
        Find all groups for a specific user.

        Args:
            user_id: The user ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of groups
        """
        try:
            repository = cast(GroupRepository, self.repository)
            results = await repository.find_by_user(user_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding groups by user: {e}")
            return Failure(AuthorizationServiceError(f"Error finding groups: {str(e)}"))

    async def get_with_relationships(self, id: str) -> Result[Group]:
        """
        Get a group with its related entities.

        Args:
            id: The ID of the group

        Returns:
            Result containing the group with loaded relationships
        """
        try:
            repository = cast(GroupRepository, self.repository)

            # Get repositories for related entities if services are available
            user_repo = None
            if self.user_service:
                user_repo = cast(UserRepository, self.user_service.repository)

            tenant_repo = None
            if self.tenant_service:
                tenant_repo = cast(TenantRepository, self.tenant_service.repository)

            # Get the group with relationships
            result = await repository.get_with_relationships(
                id, user_repo=user_repo, tenant_repo=tenant_repo
            )

            if not result:
                return Failure(AuthorizationServiceError(f"Group {id} not found"))

            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting group with relationships: {e}")
            return Failure(AuthorizationServiceError(f"Error getting group: {str(e)}"))

    async def add_user(self, group_id: str, user_id: str) -> Result[Group]:
        """
        Add a user to a group.

        Args:
            group_id: The ID of the group
            user_id: The ID of the user

        Returns:
            Result containing the updated group
        """
        try:
            # Get the group
            group_result = await self.get_by_id(group_id)
            if not group_result:
                return Failure(AuthorizationServiceError(f"Group {group_id} not found"))

            group = group_result

            # Get the user
            if not self.user_service:
                return Failure(AuthorizationServiceError("User service not available"))

            user_result = await self.user_service.get_by_id(user_id)
            if not user_result:
                return Failure(AuthorizationServiceError(f"User {user_id} not found"))

            user = user_result

            # Add user to group
            group.add_user(user)

            # Save changes
            updated_group = await self.save(group)
            if not updated_group:
                return Failure(AuthorizationServiceError("Failed to save group"))

            return Success(updated_group)
        except Exception as e:
            self.logger.error(f"Error adding user to group: {e}")
            return Failure(
                AuthorizationServiceError(f"Error adding user to group: {str(e)}")
            )


class RoleService(UnoEntityService[Role]):
    """Service for role entities."""

    def __init__(
        self,
        repository: Optional[RoleRepository] = None,
        user_service: Optional[UserService] = None,
        permission_service: Optional["PermissionService"] = None,
        tenant_service: Optional["TenantService"] = None,
        responsibility_service: Optional["ResponsibilityRoleService"] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the role service.

        Args:
            repository: The repository for data access
            user_service: Optional service for user operations
            permission_service: Optional service for permission operations
            tenant_service: Optional service for tenant operations
            responsibility_service: Optional service for responsibility role operations
            logger: Optional logger
        """
        if repository is None:
            repository = RoleRepository()

        super().__init__(Role, repository, logger)

        self.user_service = user_service
        self.permission_service = permission_service
        self.tenant_service = tenant_service
        self.responsibility_service = responsibility_service

    async def find_by_name(self, name: str, tenant_id: str) -> Result[Optional[Role]]:
        """
        Find a role by name in a specific tenant.

        Args:
            name: The role name to search for
            tenant_id: The tenant ID to restrict the search

        Returns:
            Result containing the role if found
        """
        try:
            repository = cast(RoleRepository, self.repository)
            result = await repository.find_by_name(name, tenant_id)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding role by name: {e}")
            return Failure(AuthorizationServiceError(f"Error finding role: {str(e)}"))

    async def find_by_tenant(
        self, tenant_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[Role]]:
        """
        Find all roles in a specific tenant.

        Args:
            tenant_id: The tenant ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of roles
        """
        try:
            repository = cast(RoleRepository, self.repository)
            results = await repository.find_by_tenant(tenant_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding roles by tenant: {e}")
            return Failure(AuthorizationServiceError(f"Error finding roles: {str(e)}"))

    async def find_by_user(
        self, user_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[Role]]:
        """
        Find all roles for a specific user.

        Args:
            user_id: The user ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of roles
        """
        try:
            repository = cast(RoleRepository, self.repository)
            results = await repository.find_by_user(user_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding roles by user: {e}")
            return Failure(AuthorizationServiceError(f"Error finding roles: {str(e)}"))

    async def find_by_responsibility(
        self,
        responsibility_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[list[Role]]:
        """
        Find all roles with a specific responsibility.

        Args:
            responsibility_id: The responsibility ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of roles
        """
        try:
            repository = cast(RoleRepository, self.repository)
            results = await repository.find_by_responsibility(
                responsibility_id, limit, offset
            )
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding roles by responsibility: {e}")
            return Failure(AuthorizationServiceError(f"Error finding roles: {str(e)}"))

    async def get_with_relationships(self, id: str) -> Result[Role]:
        """
        Get a role with its related entities.

        Args:
            id: The ID of the role

        Returns:
            Result containing the role with loaded relationships
        """
        try:
            repository = cast(RoleRepository, self.repository)

            # Get repositories for related entities if services are available
            user_repo = None
            if self.user_service:
                user_repo = cast(UserRepository, self.user_service.repository)

            permission_repo = None
            if self.permission_service:
                permission_repo = cast(
                    PermissionRepository, self.permission_service.repository
                )

            tenant_repo = None
            if self.tenant_service:
                tenant_repo = cast(TenantRepository, self.tenant_service.repository)

            responsibility_repo = None
            if self.responsibility_service:
                responsibility_repo = cast(
                    ResponsibilityRoleRepository, self.responsibility_service.repository
                )

            # Get the role with relationships
            result = await repository.get_with_relationships(
                id,
                user_repo=user_repo,
                permission_repo=permission_repo,
                tenant_repo=tenant_repo,
                responsibility_repo=responsibility_repo,
            )

            if not result:
                return Failure(AuthorizationServiceError(f"Role {id} not found"))

            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting role with relationships: {e}")
            return Failure(AuthorizationServiceError(f"Error getting role: {str(e)}"))

    async def add_permission(self, role_id: str, permission_id: int) -> Result[Role]:
        """
        Add a permission to a role.

        Args:
            role_id: The ID of the role
            permission_id: The ID of the permission

        Returns:
            Result containing the updated role
        """
        try:
            # Get the role
            role_result = await self.get_by_id(role_id)
            if not role_result:
                return Failure(AuthorizationServiceError(f"Role {role_id} not found"))

            role = role_result

            # Get the permission
            if not self.permission_service:
                return Failure(
                    AuthorizationServiceError("Permission service not available")
                )

            permission_result = await self.permission_service.get_by_id(
                str(permission_id)
            )
            if not permission_result:
                return Failure(
                    AuthorizationServiceError(f"Permission {permission_id} not found")
                )

            permission = permission_result

            # Add permission to role
            role.add_permission(permission)

            # Save changes
            updated_role = await self.save(role)
            if not updated_role:
                return Failure(AuthorizationServiceError("Failed to save role"))

            return Success(updated_role)
        except Exception as e:
            self.logger.error(f"Error adding permission to role: {e}")
            return Failure(
                AuthorizationServiceError(f"Error adding permission to role: {str(e)}")
            )

    async def add_user(self, role_id: str, user_id: str) -> Result[Role]:
        """
        Add a user to a role.

        Args:
            role_id: The ID of the role
            user_id: The ID of the user

        Returns:
            Result containing the updated role
        """
        try:
            # Get the role
            role_result = await self.get_by_id(role_id)
            if not role_result:
                return Failure(AuthorizationServiceError(f"Role {role_id} not found"))

            role = role_result

            # Get the user
            if not self.user_service:
                return Failure(AuthorizationServiceError("User service not available"))

            user_result = await self.user_service.get_by_id(user_id)
            if not user_result:
                return Failure(AuthorizationServiceError(f"User {user_id} not found"))

            user = user_result

            # Add user to role
            role.add_user(user)

            # Save changes
            updated_role = await self.save(role)
            if not updated_role:
                return Failure(AuthorizationServiceError("Failed to save role"))

            return Success(updated_role)
        except Exception as e:
            self.logger.error(f"Error adding user to role: {e}")
            return Failure(
                AuthorizationServiceError(f"Error adding user to role: {str(e)}")
            )

    async def has_permission(
        self, role_id: str, meta_type_id: str, operation: SQLOperation
    ) -> Result[bool]:
        """
        Check if a role has a specific permission.

        Args:
            role_id: The ID of the role
            meta_type_id: The meta type ID
            operation: The SQL operation

        Returns:
            Result containing True if the role has the permission, False otherwise
        """
        try:
            # Get the role with relationships
            role_result = await self.get_with_relationships(role_id)
            if role_result.is_failure:
                return role_result

            role = role_result.value

            # Check if role has the permission
            has_permission = role.has_permission(meta_type_id, operation)

            return Success(has_permission)
        except Exception as e:
            self.logger.error(f"Error checking role permission: {e}")
            return Failure(
                AuthorizationServiceError(f"Error checking permission: {str(e)}")
            )


class PermissionService(UnoEntityService[Permission]):
    """Service for permission entities."""

    def __init__(
        self,
        repository: Optional[PermissionRepository] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the permission service.

        Args:
            repository: The repository for data access
            logger: Optional logger
        """
        if repository is None:
            repository = PermissionRepository()

        super().__init__(Permission, repository, logger)

    async def find_by_meta_type(
        self,
        meta_type_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[list[Permission]]:
        """
        Find all permissions for a specific meta type.

        Args:
            meta_type_id: The meta type ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of permissions
        """
        try:
            repository = cast(PermissionRepository, self.repository)
            results = await repository.find_by_meta_type(meta_type_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding permissions by meta type: {e}")
            return Failure(
                AuthorizationServiceError(f"Error finding permissions: {str(e)}")
            )

    async def find_by_operation(
        self, operation: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[Permission]]:
        """
        Find all permissions for a specific operation.

        Args:
            operation: The operation to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of permissions
        """
        try:
            repository = cast(PermissionRepository, self.repository)
            results = await repository.find_by_operation(operation, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding permissions by operation: {e}")
            return Failure(
                AuthorizationServiceError(f"Error finding permissions: {str(e)}")
            )

    async def find_by_meta_type_and_operation(
        self, meta_type_id: str, operation: str
    ) -> Result[Optional[Permission]]:
        """
        Find a permission by meta type and operation.

        Args:
            meta_type_id: The meta type ID to search for
            operation: The operation to search for

        Returns:
            Result containing the permission if found
        """
        try:
            repository = cast(PermissionRepository, self.repository)
            result = await repository.find_by_meta_type_and_operation(
                meta_type_id, operation
            )
            return Success(result)
        except Exception as e:
            self.logger.error(
                f"Error finding permission by meta type and operation: {e}"
            )
            return Failure(
                AuthorizationServiceError(f"Error finding permission: {str(e)}")
            )

    async def find_by_role(
        self, role_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[Permission]]:
        """
        Find all permissions for a specific role.

        Args:
            role_id: The role ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of permissions
        """
        try:
            repository = cast(PermissionRepository, self.repository)
            results = await repository.find_by_role(role_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding permissions by role: {e}")
            return Failure(
                AuthorizationServiceError(f"Error finding permissions: {str(e)}")
            )


class ResponsibilityRoleService(UnoEntityService[ResponsibilityRole]):
    """Service for responsibility role entities."""

    def __init__(
        self,
        repository: Optional[ResponsibilityRoleRepository] = None,
        tenant_service: Optional["TenantService"] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the responsibility role service.

        Args:
            repository: The repository for data access
            tenant_service: Optional service for tenant operations
            logger: Optional logger
        """
        if repository is None:
            repository = ResponsibilityRoleRepository()

        super().__init__(ResponsibilityRole, repository, logger)

        self.tenant_service = tenant_service

    async def find_by_name(
        self, name: str, tenant_id: str
    ) -> Result[Optional[ResponsibilityRole]]:
        """
        Find a responsibility role by name in a specific tenant.

        Args:
            name: The responsibility role name to search for
            tenant_id: The tenant ID to restrict the search

        Returns:
            Result containing the responsibility role if found
        """
        try:
            repository = cast(ResponsibilityRoleRepository, self.repository)
            result = await repository.find_by_name(name, tenant_id)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding responsibility role by name: {e}")
            return Failure(
                AuthorizationServiceError(
                    f"Error finding responsibility role: {str(e)}"
                )
            )

    async def find_by_tenant(
        self, tenant_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Result[list[ResponsibilityRole]]:
        """
        Find all responsibility roles in a specific tenant.

        Args:
            tenant_id: The tenant ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of responsibility roles
        """
        try:
            repository = cast(ResponsibilityRoleRepository, self.repository)
            results = await repository.find_by_tenant(tenant_id, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding responsibility roles by tenant: {e}")
            return Failure(
                AuthorizationServiceError(
                    f"Error finding responsibility roles: {str(e)}"
                )
            )

    async def get_with_relationships(self, id: str) -> Result[ResponsibilityRole]:
        """
        Get a responsibility role with its related entities.

        Args:
            id: The ID of the responsibility role

        Returns:
            Result containing the responsibility role with loaded relationships
        """
        try:
            repository = cast(ResponsibilityRoleRepository, self.repository)

            # Get repositories for related entities if services are available
            tenant_repo = None
            if self.tenant_service:
                tenant_repo = cast(TenantRepository, self.tenant_service.repository)

            # Get the responsibility role with relationships
            result = await repository.get_with_relationships(
                id, tenant_repo=tenant_repo
            )

            if not result:
                return Failure(
                    AuthorizationServiceError(f"Responsibility role {id} not found")
                )

            return Success(result)
        except Exception as e:
            self.logger.error(
                f"Error getting responsibility role with relationships: {e}"
            )
            return Failure(
                AuthorizationServiceError(
                    f"Error getting responsibility role: {str(e)}"
                )
            )


class TenantService(UnoEntityService[Tenant]):
    """Service for tenant entities."""

    def __init__(
        self,
        repository: Optional[TenantRepository] = None,
        user_service: Optional[UserService] = None,
        group_service: Optional[GroupService] = None,
        role_service: Optional[RoleService] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the tenant service.

        Args:
            repository: The repository for data access
            user_service: Optional service for user operations
            group_service: Optional service for group operations
            role_service: Optional service for role operations
            logger: Optional logger
        """
        if repository is None:
            repository = TenantRepository()

        super().__init__(Tenant, repository, logger)

        self.user_service = user_service
        self.group_service = group_service
        self.role_service = role_service

    async def find_by_name(self, name: str) -> Result[Optional[Tenant]]:
        """
        Find a tenant by name.

        Args:
            name: The tenant name to search for

        Returns:
            Result containing the tenant if found
        """
        try:
            repository = cast(TenantRepository, self.repository)
            result = await repository.find_by_name(name)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding tenant by name: {e}")
            return Failure(AuthorizationServiceError(f"Error finding tenant: {str(e)}"))

    async def find_by_type(
        self,
        tenant_type: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[list[Tenant]]:
        """
        Find all tenants of a specific type.

        Args:
            tenant_type: The tenant type to search for
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing the list of tenants
        """
        try:
            repository = cast(TenantRepository, self.repository)
            results = await repository.find_by_type(tenant_type, limit, offset)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding tenants by type: {e}")
            return Failure(
                AuthorizationServiceError(f"Error finding tenants: {str(e)}")
            )

    async def get_with_relationships(self, id: str) -> Result[Tenant]:
        """
        Get a tenant with its related entities.

        Args:
            id: The ID of the tenant

        Returns:
            Result containing the tenant with loaded relationships
        """
        try:
            repository = cast(TenantRepository, self.repository)

            # Get repositories for related entities if services are available
            user_repo = None
            if self.user_service:
                user_repo = cast(UserRepository, self.user_service.repository)

            group_repo = None
            if self.group_service:
                group_repo = cast(GroupRepository, self.group_service.repository)

            role_repo = None
            if self.role_service:
                role_repo = cast(RoleRepository, self.role_service.repository)

            # Get the tenant with relationships
            result = await repository.get_with_relationships(
                id, user_repo=user_repo, group_repo=group_repo, role_repo=role_repo
            )

            if not result:
                return Failure(AuthorizationServiceError(f"Tenant {id} not found"))

            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting tenant with relationships: {e}")
            return Failure(AuthorizationServiceError(f"Error getting tenant: {str(e)}"))

    async def add_user(self, tenant_id: str, user_id: str) -> Result[Tenant]:
        """
        Add a user to a tenant.

        Args:
            tenant_id: The ID of the tenant
            user_id: The ID of the user

        Returns:
            Result containing the updated tenant
        """
        try:
            # Get the tenant
            tenant_result = await self.get_by_id(tenant_id)
            if not tenant_result:
                return Failure(
                    AuthorizationServiceError(f"Tenant {tenant_id} not found")
                )

            tenant = tenant_result

            # Get the user
            if not self.user_service:
                return Failure(AuthorizationServiceError("User service not available"))

            user_result = await self.user_service.get_by_id(user_id)
            if not user_result:
                return Failure(AuthorizationServiceError(f"User {user_id} not found"))

            user = user_result

            # Add user to tenant
            tenant.add_user(user)

            # Save changes
            updated_tenant = await self.save(tenant)
            if not updated_tenant:
                return Failure(AuthorizationServiceError("Failed to save tenant"))

            return Success(updated_tenant)
        except Exception as e:
            self.logger.error(f"Error adding user to tenant: {e}")
            return Failure(
                AuthorizationServiceError(f"Error adding user to tenant: {str(e)}")
            )
