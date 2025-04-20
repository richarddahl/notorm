"""
Domain entities for the Authorization module.

This module contains domain entities for users, groups, roles, permissions, and tenants
used for authentication and authorization in the system.
"""

from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Dict, Any, Set
from enum import Enum
from datetime import datetime
from pydantic import EmailStr, model_validator

from uno.domain.core import Entity, AggregateRoot
from uno.core.base.error import ValidationError
from uno.enums import SQLOperation, TenantType


@dataclass
class User(AggregateRoot[str]):
    """
    Domain entity for users in the system.

    Users represent individuals who can log into and interact with the system.
    They are associated with a tenant and can belong to multiple groups and roles.
    """

    email: EmailStr
    handle: str
    full_name: str
    is_superuser: bool = False
    tenant_id: Optional[str] = None
    default_group_id: Optional[str] = None

    # Navigation properties (not persisted directly)
    tenant: Optional["Tenant"] = field(default=None, repr=False)
    default_group: Optional["Group"] = field(default=None, repr=False)
    groups: List["Group"] = field(default_factory=list, repr=False)
    roles: List["Role"] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "UserModel"

    def validate(self) -> "Result[User, ValidationError]":
        """
        Validate the user entity. Returns Success(self) if valid, otherwise Failure(ValidationError).
        """
        from uno.core.errors.result import Success, Failure
        if not self.email:
            return Failure(ValidationError("Email cannot be empty"))
        if not self.handle:
            return Failure(ValidationError("Handle cannot be empty"))
        if not self.full_name:
            return Failure(ValidationError("Full name cannot be empty"))
        if self.is_superuser and self.default_group_id:
            return Failure(ValidationError("Superuser cannot have a default group"))
        if not self.is_superuser and not self.default_group_id:
            return Failure(ValidationError("Non-superuser must have a default group"))
        return Success(self)

    def add_to_group(self, group: "Group") -> None:
        """
        Add user to a group.

        Args:
            group: The group to add the user to
        """
        if group not in self.groups:
            self.groups.append(group)

    def remove_from_group(self, group: "Group") -> None:
        """
        Remove user from a group.

        Args:
            group: The group to remove the user from
        """
        if group in self.groups:
            self.groups.remove(group)

    def add_role(self, role: "Role") -> None:
        """
        Add a role to the user.

        Args:
            role: The role to add
        """
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: "Role") -> None:
        """
        Remove a role from the user.

        Args:
            role: The role to remove
        """
        if role in self.roles:
            self.roles.remove(role)

    def has_permission(self, meta_type_id: str, operation: SQLOperation) -> bool:
        """
        Check if the user has a specific permission.

        Args:
            meta_type_id: The meta type ID
            operation: The SQL operation

        Returns:
            True if the user has the permission, False otherwise
        """
        # Superuser has all permissions
        if self.is_superuser:
            return True

        # Check user roles for the permission
        return any(role.has_permission(meta_type_id, operation) for role in self.roles)


@dataclass
class Group(AggregateRoot[str]):
    """
    Domain entity for groups in the system.

    Groups represent collections of users and provide a way to organize users
    and assign permissions collectively.
    """

    name: str
    tenant_id: str

    # Navigation properties (not persisted directly)
    tenant: Optional["Tenant"] = field(default=None, repr=False)
    users: List[User] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "GroupModel"

    def validate(self) -> "Result[Group, ValidationError]":
        """
        Validate the group entity. Returns Success(self) if valid, otherwise Failure(ValidationError).
        """
        from uno.core.errors.result import Success, Failure
        if not self.name:
            return Failure(ValidationError("Name cannot be empty"))
        if not self.tenant_id:
            return Failure(ValidationError("Tenant ID cannot be empty"))
        return Success(self)

    def add_user(self, user: User) -> None:
        """
        Add a user to the group.

        Args:
            user: The user to add
        """
        if user not in self.users:
            self.users.append(user)
            user.add_to_group(self)

    def remove_user(self, user: User) -> None:
        """
        Remove a user from the group.

        Args:
            user: The user to remove
        """
        if user in self.users:
            self.users.remove(user)
            user.remove_from_group(self)


@dataclass
class ResponsibilityRole(AggregateRoot[str]):
    """
    Domain entity for responsibility roles in the system.

    Responsibility roles represent job functions or responsibilities that can be
    assigned to users through roles.
    """

    name: str
    description: str
    tenant_id: str

    # Navigation properties (not persisted directly)
    tenant: Optional["Tenant"] = field(default=None, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "ResponsibilityRoleModel"

    def validate(self) -> "Result[ResponsibilityRole, ValidationError]":
        """
        Validate the responsibility role entity. Returns Success(self) if valid, otherwise Failure(ValidationError).
        """
        from uno.core.errors.result import Success, Failure
        if not self.name:
            return Failure(ValidationError("Name cannot be empty"))
        if not self.description:
            return Failure(ValidationError("Description cannot be empty"))
        if not self.tenant_id:
            return Failure(ValidationError("Tenant ID cannot be empty"))
        return Success(self)


@dataclass
class Permission(Entity[int]):
    """
    Domain entity for permissions in the system.

    Permissions represent the ability to perform specific operations on specific
    meta types. They are assigned to roles.
    """

    meta_type_id: str
    operation: SQLOperation
    id: int = 0  # Will be assigned by the database

    # Navigation properties (not persisted directly)
    roles: List["Role"] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "PermissionModel"

    def validate(self) -> "Result[Permission, ValidationError]":
        """
        Validate the permission entity. Returns Success(self) if valid, otherwise Failure(ValidationError).
        """
        from uno.core.errors.result import Success, Failure
        if not self.meta_type_id:
            return Failure(ValidationError("Meta type ID cannot be empty"))
        if not self.operation:
            return Failure(ValidationError("Operation cannot be empty"))
        return Success(self)

    def __eq__(self, other: Any) -> bool:
        """
        Compare permissions based on meta type and operation.

        Args:
            other: The other permission to compare with

        Returns:
            True if the permissions are equal, False otherwise
        """
        if not isinstance(other, Permission):
            return False
        return (
            self.meta_type_id == other.meta_type_id
            and self.operation == other.operation
        )


@dataclass
class Role(AggregateRoot[str]):
    """
    Domain entity for roles in the system.

    Roles represent collections of permissions that can be assigned to users.
    They provide a way to group permissions and assign them collectively.
    """

    name: str
    description: str
    tenant_id: str
    responsibility_role_id: str

    # Navigation properties (not persisted directly)
    tenant: Optional["Tenant"] = field(default=None, repr=False)
    responsibility: Optional[ResponsibilityRole] = field(default=None, repr=False)
    permissions: List[Permission] = field(default_factory=list, repr=False)
    users: List[User] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "RoleModel"

    def validate(self) -> "Result[Role, ValidationError]":
        """
        Validate the role entity. Returns Success(self) if valid, otherwise Failure(ValidationError).
        """
        from uno.core.errors.result import Success, Failure
        if not self.name:
            return Failure(ValidationError("Name cannot be empty"))
        if not self.description:
            return Failure(ValidationError("Description cannot be empty"))
        if not self.tenant_id:
            return Failure(ValidationError("Tenant ID cannot be empty"))
        if not self.responsibility_role_id:
            return Failure(ValidationError("Responsibility role ID cannot be empty"))
        return Success(self)

    def add_permission(self, permission: Permission) -> None:
        """
        Add a permission to the role.

        Args:
            permission: The permission to add
        """
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: Permission) -> None:
        """
        Remove a permission from the role.

        Args:
            permission: The permission to remove
        """
        if permission in self.permissions:
            self.permissions.remove(permission)

    def add_user(self, user: User) -> None:
        """
        Add a user to the role.

        Args:
            user: The user to add
        """
        if user not in self.users:
            self.users.append(user)
            user.add_role(self)

    def remove_user(self, user: User) -> None:
        """
        Remove a user from the role.

        Args:
            user: The user to remove
        """
        if user in self.users:
            self.users.remove(user)
            user.remove_role(self)

    def has_permission(self, meta_type_id: str, operation: SQLOperation) -> bool:
        """
        Check if the role has a specific permission.

        Args:
            meta_type_id: The meta type ID
            operation: The SQL operation

        Returns:
            True if the role has the permission, False otherwise
        """
        return any(
            p.meta_type_id == meta_type_id and p.operation == operation
            for p in self.permissions
        )


@dataclass
class Tenant(AggregateRoot[str]):
    """
    Domain entity for tenants in the system.

    Tenants represent organizations or individuals who use the system.
    They provide a way to isolate data and users in a multi-tenant system.
    """

    name: str
    tenant_type: TenantType = TenantType.INDIVIDUAL

    # Navigation properties (not persisted directly)
    users: List[User] = field(default_factory=list, repr=False)
    groups: List[Group] = field(default_factory=list, repr=False)
    roles: List[Role] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "TenantModel"

    def validate(self) -> "Result[Tenant, ValidationError]":
        """
        Validate the tenant entity. Returns Success(self) if valid, otherwise Failure(ValidationError).
        """
        from uno.core.errors.result import Success, Failure
        if not self.name:
            return Failure(ValidationError("Name cannot be empty"))
        return Success(self)

    def add_user(self, user: User) -> None:
        """
        Add a user to the tenant.

        Args:
            user: The user to add
        """
        if user not in self.users:
            self.users.append(user)
            user.tenant_id = self.id
            user.tenant = self
