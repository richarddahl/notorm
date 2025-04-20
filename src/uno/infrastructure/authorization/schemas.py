"""
Schema managers for the Authorization module.

This module contains schema managers that handle conversion between domain entities and DTOs,
following the domain-driven design approach. Each schema manager provides methods to convert
domain entities to DTOs and vice versa.
"""

from typing import List, Optional, Union, Dict, Any, Type
from datetime import datetime

from uno.authorization.entities import (
    User,
    Group,
    Role,
    ResponsibilityRole,
    Permission,
    Tenant,
)
from uno.authorization.dtos import (
    # User DTOs
    UserBaseDto,
    UserCreateDto,
    UserUpdateDto,
    UserViewDto,
    UserFilterParams,
    UserListDto,
    # Group DTOs
    GroupBaseDto,
    GroupCreateDto,
    GroupUpdateDto,
    GroupViewDto,
    GroupFilterParams,
    GroupListDto,
    # Role DTOs
    RoleBaseDto,
    RoleCreateDto,
    RoleUpdateDto,
    RoleViewDto,
    RoleFilterParams,
    RoleListDto,
    # Responsibility Role DTOs
    ResponsibilityRoleBaseDto,
    ResponsibilityRoleCreateDto,
    ResponsibilityRoleUpdateDto,
    ResponsibilityRoleViewDto,
    ResponsibilityRoleFilterParams,
    ResponsibilityRoleListDto,
    # Permission DTOs
    PermissionBaseDto,
    PermissionCreateDto,
    PermissionViewDto,
    PermissionFilterParams,
    PermissionListDto,
    # Tenant DTOs
    TenantBaseDto,
    TenantCreateDto,
    TenantUpdateDto,
    TenantViewDto,
    TenantFilterParams,
    TenantListDto,
)


class UserSchemaManager:
    """Schema manager for user entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": UserViewDto,
            "create_schema": UserCreateDto,
            "update_schema": UserUpdateDto,
            "filter_schema": UserFilterParams,
            "list_schema": UserListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: User) -> UserViewDto:
        """Convert a user entity to a DTO."""
        group_ids = [group.id for group in entity.groups] if entity.groups else []
        role_ids = [role.id for role in entity.roles] if entity.roles else []

        return UserViewDto(
            id=entity.id,
            email=entity.email,
            handle=entity.handle,
            full_name=entity.full_name,
            is_superuser=entity.is_superuser,
            tenant_id=entity.tenant_id,
            default_group_id=entity.default_group_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            group_ids=group_ids,
            role_ids=role_ids,
        )

    def dto_to_entity(
        self,
        dto: Union[UserCreateDto, UserUpdateDto],
        existing_entity: Optional[User] = None,
    ) -> User:
        """
        Convert a DTO to a user entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            User entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, UserUpdateDto):
                if dto.email is not None:
                    existing_entity.email = dto.email
                if dto.handle is not None:
                    existing_entity.handle = dto.handle
                if dto.full_name is not None:
                    existing_entity.full_name = dto.full_name
                if dto.is_superuser is not None:
                    existing_entity.is_superuser = dto.is_superuser
                if dto.tenant_id is not None:
                    existing_entity.tenant_id = dto.tenant_id
                if dto.default_group_id is not None:
                    existing_entity.default_group_id = dto.default_group_id
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, UserCreateDto):
                return User(
                    id=None,  # Will be assigned by repository
                    email=dto.email,
                    handle=dto.handle,
                    full_name=dto.full_name,
                    is_superuser=dto.is_superuser,
                    tenant_id=dto.tenant_id,
                    default_group_id=dto.default_group_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self, entities: list[User], total: int, limit: int, offset: int
    ) -> UserListDto:
        """Convert a list of user entities to a list DTO with pagination data."""
        return UserListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )


class GroupSchemaManager:
    """Schema manager for group entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": GroupViewDto,
            "create_schema": GroupCreateDto,
            "update_schema": GroupUpdateDto,
            "filter_schema": GroupFilterParams,
            "list_schema": GroupListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: Group) -> GroupViewDto:
        """Convert a group entity to a DTO."""
        user_ids = [user.id for user in entity.users] if entity.users else []

        return GroupViewDto(
            id=entity.id,
            name=entity.name,
            tenant_id=entity.tenant_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            user_ids=user_ids,
        )

    def dto_to_entity(
        self,
        dto: Union[GroupCreateDto, GroupUpdateDto],
        existing_entity: Optional[Group] = None,
    ) -> Group:
        """
        Convert a DTO to a group entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            Group entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, GroupUpdateDto):
                if dto.name is not None:
                    existing_entity.name = dto.name
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, GroupCreateDto):
                return Group(
                    id=None,  # Will be assigned by repository
                    name=dto.name,
                    tenant_id=dto.tenant_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self, entities: list[Group], total: int, limit: int, offset: int
    ) -> GroupListDto:
        """Convert a list of group entities to a list DTO with pagination data."""
        return GroupListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )


class RoleSchemaManager:
    """Schema manager for role entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": RoleViewDto,
            "create_schema": RoleCreateDto,
            "update_schema": RoleUpdateDto,
            "filter_schema": RoleFilterParams,
            "list_schema": RoleListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: Role) -> RoleViewDto:
        """Convert a role entity to a DTO."""
        user_ids = [user.id for user in entity.users] if entity.users else []
        permission_ids = (
            [permission.id for permission in entity.permissions]
            if entity.permissions
            else []
        )

        return RoleViewDto(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            tenant_id=entity.tenant_id,
            responsibility_role_id=entity.responsibility_role_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            user_ids=user_ids,
            permission_ids=permission_ids,
        )

    def dto_to_entity(
        self,
        dto: Union[RoleCreateDto, RoleUpdateDto],
        existing_entity: Optional[Role] = None,
    ) -> Role:
        """
        Convert a DTO to a role entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            Role entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, RoleUpdateDto):
                if dto.name is not None:
                    existing_entity.name = dto.name
                if dto.description is not None:
                    existing_entity.description = dto.description
                if dto.responsibility_role_id is not None:
                    existing_entity.responsibility_role_id = dto.responsibility_role_id
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, RoleCreateDto):
                return Role(
                    id=None,  # Will be assigned by repository
                    name=dto.name,
                    description=dto.description,
                    tenant_id=dto.tenant_id,
                    responsibility_role_id=dto.responsibility_role_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self, entities: list[Role], total: int, limit: int, offset: int
    ) -> RoleListDto:
        """Convert a list of role entities to a list DTO with pagination data."""
        return RoleListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )


class ResponsibilityRoleSchemaManager:
    """Schema manager for responsibility role entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ResponsibilityRoleViewDto,
            "create_schema": ResponsibilityRoleCreateDto,
            "update_schema": ResponsibilityRoleUpdateDto,
            "filter_schema": ResponsibilityRoleFilterParams,
            "list_schema": ResponsibilityRoleListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: ResponsibilityRole) -> ResponsibilityRoleViewDto:
        """Convert a responsibility role entity to a DTO."""
        return ResponsibilityRoleViewDto(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            tenant_id=entity.tenant_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def dto_to_entity(
        self,
        dto: Union[ResponsibilityRoleCreateDto, ResponsibilityRoleUpdateDto],
        existing_entity: Optional[ResponsibilityRole] = None,
    ) -> ResponsibilityRole:
        """
        Convert a DTO to a responsibility role entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            ResponsibilityRole entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, ResponsibilityRoleUpdateDto):
                if dto.name is not None:
                    existing_entity.name = dto.name
                if dto.description is not None:
                    existing_entity.description = dto.description
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, ResponsibilityRoleCreateDto):
                return ResponsibilityRole(
                    id=None,  # Will be assigned by repository
                    name=dto.name,
                    description=dto.description,
                    tenant_id=dto.tenant_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self, entities: list[ResponsibilityRole], total: int, limit: int, offset: int
    ) -> ResponsibilityRoleListDto:
        """Convert a list of responsibility role entities to a list DTO with pagination data."""
        return ResponsibilityRoleListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )


class PermissionSchemaManager:
    """Schema manager for permission entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": PermissionViewDto,
            "create_schema": PermissionCreateDto,
            "filter_schema": PermissionFilterParams,
            "list_schema": PermissionListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: Permission) -> PermissionViewDto:
        """Convert a permission entity to a DTO."""
        role_ids = [role.id for role in entity.roles] if entity.roles else []

        return PermissionViewDto(
            id=entity.id,
            meta_type_id=entity.meta_type_id,
            operation=entity.operation,
            role_ids=role_ids,
        )

    def dto_to_entity(self, dto: PermissionCreateDto) -> Permission:
        """
        Convert a DTO to a permission entity.

        Args:
            dto: The DTO to convert

        Returns:
            Permission entity
        """
        return Permission(
            id=0,  # Will be assigned by database
            meta_type_id=dto.meta_type_id,
            operation=dto.operation,
        )

    def entities_to_list_dto(
        self, entities: list[Permission], total: int, limit: int, offset: int
    ) -> PermissionListDto:
        """Convert a list of permission entities to a list DTO with pagination data."""
        return PermissionListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )


class TenantSchemaManager:
    """Schema manager for tenant entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": TenantViewDto,
            "create_schema": TenantCreateDto,
            "update_schema": TenantUpdateDto,
            "filter_schema": TenantFilterParams,
            "list_schema": TenantListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: Tenant) -> TenantViewDto:
        """Convert a tenant entity to a DTO."""
        user_count = len(entity.users) if entity.users else 0
        group_count = len(entity.groups) if entity.groups else 0
        role_count = len(entity.roles) if entity.roles else 0

        return TenantViewDto(
            id=entity.id,
            name=entity.name,
            tenant_type=entity.tenant_type,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            user_count=user_count,
            group_count=group_count,
            role_count=role_count,
        )

    def dto_to_entity(
        self,
        dto: Union[TenantCreateDto, TenantUpdateDto],
        existing_entity: Optional[Tenant] = None,
    ) -> Tenant:
        """
        Convert a DTO to a tenant entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            Tenant entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, TenantUpdateDto):
                if dto.name is not None:
                    existing_entity.name = dto.name
                if dto.tenant_type is not None:
                    existing_entity.tenant_type = dto.tenant_type
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, TenantCreateDto):
                return Tenant(
                    id=None,  # Will be assigned by repository
                    name=dto.name,
                    tenant_type=dto.tenant_type,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self, entities: list[Tenant], total: int, limit: int, offset: int
    ) -> TenantListDto:
        """Convert a list of tenant entities to a list DTO with pagination data."""
        return TenantListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )
