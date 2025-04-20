"""
Data Transfer Objects (DTOs) for the Authorization module.

These DTOs are used to transfer data between the API layer and the domain layer,
providing a clear contract for the API and a clean separation of concerns following
the domain-driven design approach.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict

from uno.enums import SQLOperation, TenantType


class UserBaseDto(BaseModel):
    """Base DTO for user data with common fields."""

    email: EmailStr = Field(..., description="Email address, used as login ID")
    handle: str = Field(..., description="User's displayed name and alternate login ID")
    full_name: str = Field(..., description="User's full name")
    is_superuser: bool = Field(
        False, description="Indicates that the user is a Superuser"
    )
    tenant_id: Optional[str] = Field(
        None, description="The Tenant to which the user is assigned"
    )
    default_group_id: Optional[str] = Field(
        None, description="User's default group, used for creating new objects"
    )

    @model_validator(mode="after")
    def validate_superuser_group(self) -> "UserBaseDto":
        """Validate that superusers don't have default groups and non-superusers do."""
        if self.is_superuser and self.default_group_id:
            raise ValueError("Superuser cannot have a default group")
        if not self.is_superuser and not self.default_group_id and self.tenant_id:
            raise ValueError("Non-superuser must have a default group")
        return self


class UserCreateDto(UserBaseDto):
    """DTO for creating a new user."""

    password: Optional[str] = Field(None, description="Initial password for the user")


class UserUpdateDto(BaseModel):
    """DTO for updating an existing user."""

    email: Optional[EmailStr] = Field(
        None, description="Email address, used as login ID"
    )
    handle: Optional[str] = Field(
        None, description="User's displayed name and alternate login ID"
    )
    full_name: Optional[str] = Field(None, description="User's full name")
    is_superuser: Optional[bool] = Field(
        None, description="Indicates that the user is a Superuser"
    )
    tenant_id: Optional[str] = Field(
        None, description="The Tenant to which the user is assigned"
    )
    default_group_id: Optional[str] = Field(
        None, description="User's default group, used for creating new objects"
    )

    @model_validator(mode="after")
    def validate_fields(self) -> "UserUpdateDto":
        """Validate that at least one field is provided for update."""
        # Count fields that are not None
        fields = [
            self.email,
            self.handle,
            self.full_name,
            self.is_superuser,
            self.tenant_id,
            self.default_group_id,
        ]
        if not any(field is not None for field in fields):
            raise ValueError("At least one field must be provided for update")
        return self


class UserViewDto(UserBaseDto):
    """DTO for viewing user data."""

    id: str = Field(..., description="Unique identifier for the user")
    created_at: datetime = Field(..., description="Timestamp when the user was created")
    updated_at: datetime = Field(
        ..., description="Timestamp when the user was last updated"
    )

    # Navigation properties (returned as IDs, loaded on demand)
    group_ids: list[str] = Field(
        default_factory=list, description="IDs of groups to which the user is assigned"
    )
    role_ids: list[str] = Field(
        default_factory=list, description="IDs of roles assigned to the user"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "user_12345abcde",
                "email": "user@example.com",
                "handle": "user123",
                "full_name": "John Doe",
                "is_superuser": False,
                "tenant_id": "tenant_12345abcde",
                "default_group_id": "group_12345abcde",
                "created_at": "2025-04-01T12:00:00.000Z",
                "updated_at": "2025-04-16T14:30:22.123Z",
                "group_ids": ["group_12345abcde", "group_67890fghij"],
                "role_ids": ["role_12345abcde", "role_67890fghij"],
            }
        }
    )


class UserFilterParams(BaseModel):
    """Parameters for filtering users."""

    email: Optional[str] = Field(None, description="Filter by email (exact match)")
    email_contains: Optional[str] = Field(
        None, description="Filter by email (contains)"
    )
    handle: Optional[str] = Field(None, description="Filter by handle (exact match)")
    handle_contains: Optional[str] = Field(
        None, description="Filter by handle (contains)"
    )
    full_name_contains: Optional[str] = Field(
        None, description="Filter by full name (contains)"
    )
    is_superuser: Optional[bool] = Field(None, description="Filter by superuser status")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    group_id: Optional[str] = Field(None, description="Filter by group membership")
    role_id: Optional[str] = Field(None, description="Filter by role assignment")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
    updated_after: Optional[datetime] = Field(
        None, description="Filter by update date (after)"
    )
    updated_before: Optional[datetime] = Field(
        None, description="Filter by update date (before)"
    )
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class UserListDto(BaseModel):
    """DTO for a list of users with pagination data."""

    items: list[UserViewDto] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users matching the query")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class GroupBaseDto(BaseModel):
    """Base DTO for group data with common fields."""

    name: str = Field(..., description="Group name")
    tenant_id: str = Field(..., description="The Tenant that owns the group")


class GroupCreateDto(GroupBaseDto):
    """DTO for creating a new group."""

    user_ids: list[str] | None = Field(
        None, description="IDs of users to add to the group"
    )


class GroupUpdateDto(BaseModel):
    """DTO for updating an existing group."""

    name: Optional[str] = Field(None, description="Group name")

    @model_validator(mode="after")
    def validate_fields(self) -> "GroupUpdateDto":
        """Validate that at least one field is provided for update."""
        if self.name is None:
            raise ValueError("At least one field must be provided for update")
        return self


class GroupViewDto(GroupBaseDto):
    """DTO for viewing group data."""

    id: str = Field(..., description="Unique identifier for the group")
    created_at: datetime = Field(
        ..., description="Timestamp when the group was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the group was last updated"
    )

    # Navigation properties (returned as IDs, loaded on demand)
    user_ids: list[str] = Field(
        default_factory=list, description="IDs of users assigned to the group"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "group_12345abcde",
                "name": "Administrators",
                "tenant_id": "tenant_12345abcde",
                "created_at": "2025-04-01T12:00:00.000Z",
                "updated_at": "2025-04-16T14:30:22.123Z",
                "user_ids": ["user_12345abcde", "user_67890fghij"],
            }
        }
    )


class GroupFilterParams(BaseModel):
    """Parameters for filtering groups."""

    name: Optional[str] = Field(None, description="Filter by name (exact match)")
    name_contains: Optional[str] = Field(None, description="Filter by name (contains)")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    user_id: Optional[str] = Field(None, description="Filter by user membership")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
    updated_after: Optional[datetime] = Field(
        None, description="Filter by update date (after)"
    )
    updated_before: Optional[datetime] = Field(
        None, description="Filter by update date (before)"
    )
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class GroupListDto(BaseModel):
    """DTO for a list of groups with pagination data."""

    items: list[GroupViewDto] = Field(..., description="List of groups")
    total: int = Field(..., description="Total number of groups matching the query")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class RoleBaseDto(BaseModel):
    """Base DTO for role data with common fields."""

    name: str = Field(..., description="Role name")
    description: str = Field(..., description="Role description")
    tenant_id: str = Field(..., description="The Tenant that owns the role")
    responsibility_role_id: str = Field(
        ..., description="The Responsibility that the role's assigned user performs"
    )


class RoleCreateDto(RoleBaseDto):
    """DTO for creating a new role."""

    permission_ids: Optional[list[int]] = Field(
        None, description="IDs of permissions to add to the role"
    )
    user_ids: list[str] | None = Field(
        None, description="IDs of users to assign the role to"
    )


class RoleUpdateDto(BaseModel):
    """DTO for updating an existing role."""

    name: Optional[str] = Field(None, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    responsibility_role_id: Optional[str] = Field(
        None, description="The Responsibility that the role's assigned user performs"
    )

    @model_validator(mode="after")
    def validate_fields(self) -> "RoleUpdateDto":
        """Validate that at least one field is provided for update."""
        fields = [self.name, self.description, self.responsibility_role_id]
        if not any(field is not None for field in fields):
            raise ValueError("At least one field must be provided for update")
        return self


class RoleViewDto(RoleBaseDto):
    """DTO for viewing role data."""

    id: str = Field(..., description="Unique identifier for the role")
    created_at: datetime = Field(..., description="Timestamp when the role was created")
    updated_at: datetime = Field(
        ..., description="Timestamp when the role was last updated"
    )

    # Navigation properties (returned as IDs, loaded on demand)
    permission_ids: list[int] = Field(
        default_factory=list, description="IDs of permissions assigned to the role"
    )
    user_ids: list[str] = Field(
        default_factory=list, description="IDs of users assigned to the role"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "role_12345abcde",
                "name": "Product Manager",
                "description": "Manages product catalog and inventory",
                "tenant_id": "tenant_12345abcde",
                "responsibility_role_id": "resp_12345abcde",
                "created_at": "2025-04-01T12:00:00.000Z",
                "updated_at": "2025-04-16T14:30:22.123Z",
                "permission_ids": [1, 2, 3, 4],
                "user_ids": ["user_12345abcde", "user_67890fghij"],
            }
        }
    )


class RoleFilterParams(BaseModel):
    """Parameters for filtering roles."""

    name: Optional[str] = Field(None, description="Filter by name (exact match)")
    name_contains: Optional[str] = Field(None, description="Filter by name (contains)")
    description_contains: Optional[str] = Field(
        None, description="Filter by description (contains)"
    )
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    responsibility_role_id: Optional[str] = Field(
        None, description="Filter by responsibility role ID"
    )
    user_id: Optional[str] = Field(None, description="Filter by user assignment")
    permission_id: Optional[int] = Field(None, description="Filter by permission ID")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
    updated_after: Optional[datetime] = Field(
        None, description="Filter by update date (after)"
    )
    updated_before: Optional[datetime] = Field(
        None, description="Filter by update date (before)"
    )
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class RoleListDto(BaseModel):
    """DTO for a list of roles with pagination data."""

    items: list[RoleViewDto] = Field(..., description="List of roles")
    total: int = Field(..., description="Total number of roles matching the query")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class ResponsibilityRoleBaseDto(BaseModel):
    """Base DTO for responsibility role data with common fields."""

    name: str = Field(..., description="Responsibility role name")
    description: str = Field(..., description="Responsibility role description")
    tenant_id: str = Field(
        ..., description="The Tenant that owns the responsibility role"
    )


class ResponsibilityRoleCreateDto(ResponsibilityRoleBaseDto):
    """DTO for creating a new responsibility role."""

    pass


class ResponsibilityRoleUpdateDto(BaseModel):
    """DTO for updating an existing responsibility role."""

    name: Optional[str] = Field(None, description="Responsibility role name")
    description: Optional[str] = Field(
        None, description="Responsibility role description"
    )

    @model_validator(mode="after")
    def validate_fields(self) -> "ResponsibilityRoleUpdateDto":
        """Validate that at least one field is provided for update."""
        if self.name is None and self.description is None:
            raise ValueError("At least one field must be provided for update")
        return self


class ResponsibilityRoleViewDto(ResponsibilityRoleBaseDto):
    """DTO for viewing responsibility role data."""

    id: str = Field(..., description="Unique identifier for the responsibility role")
    created_at: datetime = Field(
        ..., description="Timestamp when the responsibility role was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the responsibility role was last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "resp_12345abcde",
                "name": "Product Management",
                "description": "Responsible for product catalog and inventory",
                "tenant_id": "tenant_12345abcde",
                "created_at": "2025-04-01T12:00:00.000Z",
                "updated_at": "2025-04-16T14:30:22.123Z",
            }
        }
    )


class ResponsibilityRoleFilterParams(BaseModel):
    """Parameters for filtering responsibility roles."""

    name: Optional[str] = Field(None, description="Filter by name (exact match)")
    name_contains: Optional[str] = Field(None, description="Filter by name (contains)")
    description_contains: Optional[str] = Field(
        None, description="Filter by description (contains)"
    )
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
    updated_after: Optional[datetime] = Field(
        None, description="Filter by update date (after)"
    )
    updated_before: Optional[datetime] = Field(
        None, description="Filter by update date (before)"
    )
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class ResponsibilityRoleListDto(BaseModel):
    """DTO for a list of responsibility roles with pagination data."""

    items: list[ResponsibilityRoleViewDto] = Field(
        ..., description="List of responsibility roles"
    )
    total: int = Field(
        ..., description="Total number of responsibility roles matching the query"
    )
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class PermissionBaseDto(BaseModel):
    """Base DTO for permission data with common fields."""

    meta_type_id: str = Field(..., description="Foreign Key to MetaRecord Type")
    operation: SQLOperation = Field(..., description="SQL Operation")


class PermissionCreateDto(PermissionBaseDto):
    """DTO for creating a new permission."""

    pass


class PermissionViewDto(PermissionBaseDto):
    """DTO for viewing permission data."""

    id: int = Field(..., description="Unique identifier for the permission")

    # Navigation properties (returned as IDs, loaded on demand)
    role_ids: list[str] = Field(
        default_factory=list, description="IDs of roles with this permission"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "meta_type_id": "product",
                "operation": "SELECT",
                "role_ids": ["role_12345abcde", "role_67890fghij"],
            }
        }
    )


class PermissionFilterParams(BaseModel):
    """Parameters for filtering permissions."""

    meta_type_id: Optional[str] = Field(None, description="Filter by meta type ID")
    operation: Optional[SQLOperation] = Field(None, description="Filter by operation")
    role_id: Optional[str] = Field(None, description="Filter by role assignment")
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class PermissionListDto(BaseModel):
    """DTO for a list of permissions with pagination data."""

    items: list[PermissionViewDto] = Field(..., description="List of permissions")
    total: int = Field(
        ..., description="Total number of permissions matching the query"
    )
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class TenantBaseDto(BaseModel):
    """Base DTO for tenant data with common fields."""

    name: str = Field(..., description="Tenant name")
    tenant_type: TenantType = Field(TenantType.INDIVIDUAL, description="Tenant type")


class TenantCreateDto(TenantBaseDto):
    """DTO for creating a new tenant."""

    pass


class TenantUpdateDto(BaseModel):
    """DTO for updating an existing tenant."""

    name: Optional[str] = Field(None, description="Tenant name")
    tenant_type: Optional[TenantType] = Field(None, description="Tenant type")

    @model_validator(mode="after")
    def validate_fields(self) -> "TenantUpdateDto":
        """Validate that at least one field is provided for update."""
        if self.name is None and self.tenant_type is None:
            raise ValueError("At least one field must be provided for update")
        return self


class TenantViewDto(TenantBaseDto):
    """DTO for viewing tenant data."""

    id: str = Field(..., description="Unique identifier for the tenant")
    created_at: datetime = Field(
        ..., description="Timestamp when the tenant was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the tenant was last updated"
    )

    # Navigation properties (returned as counts, loaded on demand)
    user_count: int = Field(0, description="Number of users in the tenant")
    group_count: int = Field(0, description="Number of groups in the tenant")
    role_count: int = Field(0, description="Number of roles in the tenant")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tenant_12345abcde",
                "name": "Acme Corporation",
                "tenant_type": "ORGANIZATION",
                "created_at": "2025-04-01T12:00:00.000Z",
                "updated_at": "2025-04-16T14:30:22.123Z",
                "user_count": 42,
                "group_count": 8,
                "role_count": 15,
            }
        }
    )


class TenantFilterParams(BaseModel):
    """Parameters for filtering tenants."""

    name: Optional[str] = Field(None, description="Filter by name (exact match)")
    name_contains: Optional[str] = Field(None, description="Filter by name (contains)")
    tenant_type: Optional[TenantType] = Field(None, description="Filter by tenant type")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
    updated_after: Optional[datetime] = Field(
        None, description="Filter by update date (after)"
    )
    updated_before: Optional[datetime] = Field(
        None, description="Filter by update date (before)"
    )
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class TenantListDto(BaseModel):
    """DTO for a list of tenants with pagination data."""

    items: list[TenantViewDto] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total number of tenants matching the query")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")
