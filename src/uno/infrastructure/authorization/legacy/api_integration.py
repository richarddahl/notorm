"""
API integration for the Authorization module.

This module provides functions to register authorization-related API endpoints with FastAPI,
following the domain-driven design approach with a clean separation between domain logic
and API contracts.
"""

from typing import List, Dict, Any, Optional, Union, Callable
from fastapi import APIRouter, FastAPI, Depends, Query, Path, HTTPException, status

from uno.authorization.entities import (
    User, Group, Role, ResponsibilityRole, Permission, Tenant
)
from uno.authorization.dtos import (
    # User DTOs
    UserCreateDto, UserUpdateDto, UserViewDto, UserFilterParams, UserListDto,
    
    # Group DTOs
    GroupCreateDto, GroupUpdateDto, GroupViewDto, GroupFilterParams, GroupListDto,
    
    # Role DTOs
    RoleCreateDto, RoleUpdateDto, RoleViewDto, RoleFilterParams, RoleListDto,
    
    # Responsibility Role DTOs
    ResponsibilityRoleCreateDto, ResponsibilityRoleUpdateDto, 
    ResponsibilityRoleViewDto, ResponsibilityRoleFilterParams, ResponsibilityRoleListDto,
    
    # Permission DTOs
    PermissionCreateDto, PermissionViewDto, PermissionFilterParams, PermissionListDto,
    
    # Tenant DTOs
    TenantCreateDto, TenantUpdateDto, TenantViewDto, TenantFilterParams, TenantListDto,
)
from uno.authorization.schemas import (
    UserSchemaManager,
    GroupSchemaManager,
    RoleSchemaManager,
    ResponsibilityRoleSchemaManager,
    PermissionSchemaManager,
    TenantSchemaManager,
)
from uno.authorization.services import (
    UserService,
    GroupService,
    RoleService,
    ResponsibilityRoleService,
    PermissionService,
    TenantService,
)


def register_user_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    user_service: Optional[UserService] = None,
) -> Dict[str, Any]:
    """
    Register API endpoints for user management.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        user_service: Optional UserService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/users",
            tags=["Users"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router
    
    # Create schema manager
    schema_manager = UserSchemaManager()
    
    # GET /users
    @router.get(
        "",
        response_model=UserListDto,
        summary="List users",
        description="Retrieve a paginated list of users with optional filtering",
    )
    async def list_users(
        filters: UserFilterParams = Depends(),
        service: UserService = Depends(lambda: user_service),
    ) -> UserListDto:
        users, total = await service.list_users(filters)
        return schema_manager.entities_to_list_dto(users, total, filters.limit, filters.offset)
    
    # POST /users
    @router.post(
        "",
        response_model=UserViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create user",
        description="Create a new user",
    )
    async def create_user(
        user_data: UserCreateDto,
        service: UserService = Depends(lambda: user_service),
    ) -> UserViewDto:
        user_entity = schema_manager.dto_to_entity(user_data)
        created_user = await service.create_user(user_entity)
        return schema_manager.entity_to_dto(created_user)
    
    # GET /users/{user_id}
    @router.get(
        "/{user_id}",
        response_model=UserViewDto,
        summary="Get user",
        description="Retrieve a specific user by ID",
    )
    async def get_user(
        user_id: str = Path(..., description="The ID of the user to retrieve"),
        service: UserService = Depends(lambda: user_service),
    ) -> UserViewDto:
        user = await service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return schema_manager.entity_to_dto(user)
    
    # PATCH /users/{user_id}
    @router.patch(
        "/{user_id}",
        response_model=UserViewDto,
        summary="Update user",
        description="Update an existing user",
    )
    async def update_user(
        user_data: UserUpdateDto,
        user_id: str = Path(..., description="The ID of the user to update"),
        service: UserService = Depends(lambda: user_service),
    ) -> UserViewDto:
        user = await service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        updated_entity = schema_manager.dto_to_entity(user_data, user)
        updated_user = await service.update_user(updated_entity)
        return schema_manager.entity_to_dto(updated_user)
    
    # DELETE /users/{user_id}
    @router.delete(
        "/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete user",
        description="Delete an existing user",
    )
    async def delete_user(
        user_id: str = Path(..., description="The ID of the user to delete"),
        service: UserService = Depends(lambda: user_service),
    ) -> None:
        user = await service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        await service.delete_user(user_id)
        return None
    
    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    # Return registered endpoints
    return {
        "list_users": list_users,
        "create_user": create_user,
        "get_user": get_user,
        "update_user": update_user,
        "delete_user": delete_user,
    }


def register_group_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    group_service: Optional[GroupService] = None,
) -> Dict[str, Any]:
    """
    Register API endpoints for group management.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        group_service: Optional GroupService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/groups",
            tags=["Groups"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router
    
    # Create schema manager
    schema_manager = GroupSchemaManager()
    
    # GET /groups
    @router.get(
        "",
        response_model=GroupListDto,
        summary="List groups",
        description="Retrieve a paginated list of groups with optional filtering",
    )
    async def list_groups(
        filters: GroupFilterParams = Depends(),
        service: GroupService = Depends(lambda: group_service),
    ) -> GroupListDto:
        groups, total = await service.list_groups(filters)
        return schema_manager.entities_to_list_dto(groups, total, filters.limit, filters.offset)
    
    # POST /groups
    @router.post(
        "",
        response_model=GroupViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create group",
        description="Create a new group",
    )
    async def create_group(
        group_data: GroupCreateDto,
        service: GroupService = Depends(lambda: group_service),
    ) -> GroupViewDto:
        group_entity = schema_manager.dto_to_entity(group_data)
        created_group = await service.create_group(group_entity)
        return schema_manager.entity_to_dto(created_group)
    
    # GET /groups/{group_id}
    @router.get(
        "/{group_id}",
        response_model=GroupViewDto,
        summary="Get group",
        description="Retrieve a specific group by ID",
    )
    async def get_group(
        group_id: str = Path(..., description="The ID of the group to retrieve"),
        service: GroupService = Depends(lambda: group_service),
    ) -> GroupViewDto:
        group = await service.get_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with ID {group_id} not found",
            )
        return schema_manager.entity_to_dto(group)
    
    # PATCH /groups/{group_id}
    @router.patch(
        "/{group_id}",
        response_model=GroupViewDto,
        summary="Update group",
        description="Update an existing group",
    )
    async def update_group(
        group_data: GroupUpdateDto,
        group_id: str = Path(..., description="The ID of the group to update"),
        service: GroupService = Depends(lambda: group_service),
    ) -> GroupViewDto:
        group = await service.get_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with ID {group_id} not found",
            )
        
        updated_entity = schema_manager.dto_to_entity(group_data, group)
        updated_group = await service.update_group(updated_entity)
        return schema_manager.entity_to_dto(updated_group)
    
    # DELETE /groups/{group_id}
    @router.delete(
        "/{group_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete group",
        description="Delete an existing group",
    )
    async def delete_group(
        group_id: str = Path(..., description="The ID of the group to delete"),
        service: GroupService = Depends(lambda: group_service),
    ) -> None:
        group = await service.get_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with ID {group_id} not found",
            )
        
        await service.delete_group(group_id)
        return None
    
    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    # Return registered endpoints
    return {
        "list_groups": list_groups,
        "create_group": create_group,
        "get_group": get_group,
        "update_group": update_group,
        "delete_group": delete_group,
    }


def register_role_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    role_service: Optional[RoleService] = None,
) -> Dict[str, Any]:
    """
    Register API endpoints for role management.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        role_service: Optional RoleService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/roles",
            tags=["Roles"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router
    
    # Create schema manager
    schema_manager = RoleSchemaManager()
    
    # GET /roles
    @router.get(
        "",
        response_model=RoleListDto,
        summary="List roles",
        description="Retrieve a paginated list of roles with optional filtering",
    )
    async def list_roles(
        filters: RoleFilterParams = Depends(),
        service: RoleService = Depends(lambda: role_service),
    ) -> RoleListDto:
        roles, total = await service.list_roles(filters)
        return schema_manager.entities_to_list_dto(roles, total, filters.limit, filters.offset)
    
    # POST /roles
    @router.post(
        "",
        response_model=RoleViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create role",
        description="Create a new role",
    )
    async def create_role(
        role_data: RoleCreateDto,
        service: RoleService = Depends(lambda: role_service),
    ) -> RoleViewDto:
        role_entity = schema_manager.dto_to_entity(role_data)
        created_role = await service.create_role(role_entity)
        return schema_manager.entity_to_dto(created_role)
    
    # GET /roles/{role_id}
    @router.get(
        "/{role_id}",
        response_model=RoleViewDto,
        summary="Get role",
        description="Retrieve a specific role by ID",
    )
    async def get_role(
        role_id: str = Path(..., description="The ID of the role to retrieve"),
        service: RoleService = Depends(lambda: role_service),
    ) -> RoleViewDto:
        role = await service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )
        return schema_manager.entity_to_dto(role)
    
    # PATCH /roles/{role_id}
    @router.patch(
        "/{role_id}",
        response_model=RoleViewDto,
        summary="Update role",
        description="Update an existing role",
    )
    async def update_role(
        role_data: RoleUpdateDto,
        role_id: str = Path(..., description="The ID of the role to update"),
        service: RoleService = Depends(lambda: role_service),
    ) -> RoleViewDto:
        role = await service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )
        
        updated_entity = schema_manager.dto_to_entity(role_data, role)
        updated_role = await service.update_role(updated_entity)
        return schema_manager.entity_to_dto(updated_role)
    
    # DELETE /roles/{role_id}
    @router.delete(
        "/{role_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete role",
        description="Delete an existing role",
    )
    async def delete_role(
        role_id: str = Path(..., description="The ID of the role to delete"),
        service: RoleService = Depends(lambda: role_service),
    ) -> None:
        role = await service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )
        
        await service.delete_role(role_id)
        return None
    
    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    # Return registered endpoints
    return {
        "list_roles": list_roles,
        "create_role": create_role,
        "get_role": get_role,
        "update_role": update_role,
        "delete_role": delete_role,
    }


def register_responsibility_role_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    responsibility_role_service: Optional[ResponsibilityRoleService] = None,
) -> Dict[str, Any]:
    """
    Register API endpoints for responsibility role management.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        responsibility_role_service: Optional ResponsibilityRoleService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/responsibility-roles",
            tags=["Responsibility Roles"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router
    
    # Create schema manager
    schema_manager = ResponsibilityRoleSchemaManager()
    
    # GET /responsibility-roles
    @router.get(
        "",
        response_model=ResponsibilityRoleListDto,
        summary="List responsibility roles",
        description="Retrieve a paginated list of responsibility roles with optional filtering",
    )
    async def list_responsibility_roles(
        filters: ResponsibilityRoleFilterParams = Depends(),
        service: ResponsibilityRoleService = Depends(lambda: responsibility_role_service),
    ) -> ResponsibilityRoleListDto:
        roles, total = await service.list_responsibility_roles(filters)
        return schema_manager.entities_to_list_dto(roles, total, filters.limit, filters.offset)
    
    # POST /responsibility-roles
    @router.post(
        "",
        response_model=ResponsibilityRoleViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create responsibility role",
        description="Create a new responsibility role",
    )
    async def create_responsibility_role(
        role_data: ResponsibilityRoleCreateDto,
        service: ResponsibilityRoleService = Depends(lambda: responsibility_role_service),
    ) -> ResponsibilityRoleViewDto:
        role_entity = schema_manager.dto_to_entity(role_data)
        created_role = await service.create_responsibility_role(role_entity)
        return schema_manager.entity_to_dto(created_role)
    
    # GET /responsibility-roles/{role_id}
    @router.get(
        "/{role_id}",
        response_model=ResponsibilityRoleViewDto,
        summary="Get responsibility role",
        description="Retrieve a specific responsibility role by ID",
    )
    async def get_responsibility_role(
        role_id: str = Path(..., description="The ID of the responsibility role to retrieve"),
        service: ResponsibilityRoleService = Depends(lambda: responsibility_role_service),
    ) -> ResponsibilityRoleViewDto:
        role = await service.get_responsibility_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Responsibility role with ID {role_id} not found",
            )
        return schema_manager.entity_to_dto(role)
    
    # PATCH /responsibility-roles/{role_id}
    @router.patch(
        "/{role_id}",
        response_model=ResponsibilityRoleViewDto,
        summary="Update responsibility role",
        description="Update an existing responsibility role",
    )
    async def update_responsibility_role(
        role_data: ResponsibilityRoleUpdateDto,
        role_id: str = Path(..., description="The ID of the responsibility role to update"),
        service: ResponsibilityRoleService = Depends(lambda: responsibility_role_service),
    ) -> ResponsibilityRoleViewDto:
        role = await service.get_responsibility_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Responsibility role with ID {role_id} not found",
            )
        
        updated_entity = schema_manager.dto_to_entity(role_data, role)
        updated_role = await service.update_responsibility_role(updated_entity)
        return schema_manager.entity_to_dto(updated_role)
    
    # DELETE /responsibility-roles/{role_id}
    @router.delete(
        "/{role_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete responsibility role",
        description="Delete an existing responsibility role",
    )
    async def delete_responsibility_role(
        role_id: str = Path(..., description="The ID of the responsibility role to delete"),
        service: ResponsibilityRoleService = Depends(lambda: responsibility_role_service),
    ) -> None:
        role = await service.get_responsibility_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Responsibility role with ID {role_id} not found",
            )
        
        await service.delete_responsibility_role(role_id)
        return None
    
    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    # Return registered endpoints
    return {
        "list_responsibility_roles": list_responsibility_roles,
        "create_responsibility_role": create_responsibility_role,
        "get_responsibility_role": get_responsibility_role,
        "update_responsibility_role": update_responsibility_role,
        "delete_responsibility_role": delete_responsibility_role,
    }


def register_permission_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    permission_service: Optional[PermissionService] = None,
) -> Dict[str, Any]:
    """
    Register API endpoints for permission management.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        permission_service: Optional PermissionService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/permissions",
            tags=["Permissions"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router
    
    # Create schema manager
    schema_manager = PermissionSchemaManager()
    
    # GET /permissions
    @router.get(
        "",
        response_model=PermissionListDto,
        summary="List permissions",
        description="Retrieve a paginated list of permissions with optional filtering",
    )
    async def list_permissions(
        filters: PermissionFilterParams = Depends(),
        service: PermissionService = Depends(lambda: permission_service),
    ) -> PermissionListDto:
        permissions, total = await service.list_permissions(filters)
        return schema_manager.entities_to_list_dto(permissions, total, filters.limit, filters.offset)
    
    # POST /permissions
    @router.post(
        "",
        response_model=PermissionViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create permission",
        description="Create a new permission",
    )
    async def create_permission(
        permission_data: PermissionCreateDto,
        service: PermissionService = Depends(lambda: permission_service),
    ) -> PermissionViewDto:
        permission_entity = schema_manager.dto_to_entity(permission_data)
        created_permission = await service.create_permission(permission_entity)
        return schema_manager.entity_to_dto(created_permission)
    
    # GET /permissions/{permission_id}
    @router.get(
        "/{permission_id}",
        response_model=PermissionViewDto,
        summary="Get permission",
        description="Retrieve a specific permission by ID",
    )
    async def get_permission(
        permission_id: int = Path(..., description="The ID of the permission to retrieve"),
        service: PermissionService = Depends(lambda: permission_service),
    ) -> PermissionViewDto:
        permission = await service.get_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID {permission_id} not found",
            )
        return schema_manager.entity_to_dto(permission)
    
    # DELETE /permissions/{permission_id}
    @router.delete(
        "/{permission_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete permission",
        description="Delete an existing permission",
    )
    async def delete_permission(
        permission_id: int = Path(..., description="The ID of the permission to delete"),
        service: PermissionService = Depends(lambda: permission_service),
    ) -> None:
        permission = await service.get_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID {permission_id} not found",
            )
        
        await service.delete_permission(permission_id)
        return None
    
    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    # Return registered endpoints
    return {
        "list_permissions": list_permissions,
        "create_permission": create_permission,
        "get_permission": get_permission,
        "delete_permission": delete_permission,
    }


def register_tenant_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    tenant_service: Optional[TenantService] = None,
) -> Dict[str, Any]:
    """
    Register API endpoints for tenant management.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        tenant_service: Optional TenantService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/tenants",
            tags=["Tenants"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router
    
    # Create schema manager
    schema_manager = TenantSchemaManager()
    
    # GET /tenants
    @router.get(
        "",
        response_model=TenantListDto,
        summary="List tenants",
        description="Retrieve a paginated list of tenants with optional filtering",
    )
    async def list_tenants(
        filters: TenantFilterParams = Depends(),
        service: TenantService = Depends(lambda: tenant_service),
    ) -> TenantListDto:
        tenants, total = await service.list_tenants(filters)
        return schema_manager.entities_to_list_dto(tenants, total, filters.limit, filters.offset)
    
    # POST /tenants
    @router.post(
        "",
        response_model=TenantViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create tenant",
        description="Create a new tenant",
    )
    async def create_tenant(
        tenant_data: TenantCreateDto,
        service: TenantService = Depends(lambda: tenant_service),
    ) -> TenantViewDto:
        tenant_entity = schema_manager.dto_to_entity(tenant_data)
        created_tenant = await service.create_tenant(tenant_entity)
        return schema_manager.entity_to_dto(created_tenant)
    
    # GET /tenants/{tenant_id}
    @router.get(
        "/{tenant_id}",
        response_model=TenantViewDto,
        summary="Get tenant",
        description="Retrieve a specific tenant by ID",
    )
    async def get_tenant(
        tenant_id: str = Path(..., description="The ID of the tenant to retrieve"),
        service: TenantService = Depends(lambda: tenant_service),
    ) -> TenantViewDto:
        tenant = await service.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID {tenant_id} not found",
            )
        return schema_manager.entity_to_dto(tenant)
    
    # PATCH /tenants/{tenant_id}
    @router.patch(
        "/{tenant_id}",
        response_model=TenantViewDto,
        summary="Update tenant",
        description="Update an existing tenant",
    )
    async def update_tenant(
        tenant_data: TenantUpdateDto,
        tenant_id: str = Path(..., description="The ID of the tenant to update"),
        service: TenantService = Depends(lambda: tenant_service),
    ) -> TenantViewDto:
        tenant = await service.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID {tenant_id} not found",
            )
        
        updated_entity = schema_manager.dto_to_entity(tenant_data, tenant)
        updated_tenant = await service.update_tenant(updated_entity)
        return schema_manager.entity_to_dto(updated_tenant)
    
    # DELETE /tenants/{tenant_id}
    @router.delete(
        "/{tenant_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete tenant",
        description="Delete an existing tenant",
    )
    async def delete_tenant(
        tenant_id: str = Path(..., description="The ID of the tenant to delete"),
        service: TenantService = Depends(lambda: tenant_service),
    ) -> None:
        tenant = await service.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID {tenant_id} not found",
            )
        
        await service.delete_tenant(tenant_id)
        return None
    
    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    # Return registered endpoints
    return {
        "list_tenants": list_tenants,
        "create_tenant": create_tenant,
        "get_tenant": get_tenant,
        "update_tenant": update_tenant,
        "delete_tenant": delete_tenant,
    }


def register_authorization_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    user_service: Optional[UserService] = None,
    group_service: Optional[GroupService] = None,
    role_service: Optional[RoleService] = None,
    responsibility_role_service: Optional[ResponsibilityRoleService] = None,
    permission_service: Optional[PermissionService] = None,
    tenant_service: Optional[TenantService] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Register all authorization-related API endpoints.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        user_service: Optional UserService instance (for testing)
        group_service: Optional GroupService instance (for testing)
        role_service: Optional RoleService instance (for testing)
        responsibility_role_service: Optional ResponsibilityRoleService instance (for testing)
        permission_service: Optional PermissionService instance (for testing)
        tenant_service: Optional TenantService instance (for testing)
        
    Returns:
        Dictionary of registered endpoints by resource type
    """
    # Create routers for each resource type
    if isinstance(app_or_router, FastAPI):
        user_router = APIRouter(prefix=f"{path_prefix}/users", tags=["Users"], dependencies=dependencies or [])
        group_router = APIRouter(prefix=f"{path_prefix}/groups", tags=["Groups"], dependencies=dependencies or [])
        role_router = APIRouter(prefix=f"{path_prefix}/roles", tags=["Roles"], dependencies=dependencies or [])
        responsibility_role_router = APIRouter(prefix=f"{path_prefix}/responsibility-roles", tags=["Responsibility Roles"], dependencies=dependencies or [])
        permission_router = APIRouter(prefix=f"{path_prefix}/permissions", tags=["Permissions"], dependencies=dependencies or [])
        tenant_router = APIRouter(prefix=f"{path_prefix}/tenants", tags=["Tenants"], dependencies=dependencies or [])
    else:
        # Use the provided router for everything
        user_router = group_router = role_router = responsibility_role_router = permission_router = tenant_router = app_or_router
    
    # Register endpoints for each resource type
    user_endpoints = register_user_endpoints(user_router, path_prefix="", dependencies=None, include_auth=include_auth, user_service=user_service)
    group_endpoints = register_group_endpoints(group_router, path_prefix="", dependencies=None, include_auth=include_auth, group_service=group_service)
    role_endpoints = register_role_endpoints(role_router, path_prefix="", dependencies=None, include_auth=include_auth, role_service=role_service)
    responsibility_role_endpoints = register_responsibility_role_endpoints(responsibility_role_router, path_prefix="", dependencies=None, include_auth=include_auth, responsibility_role_service=responsibility_role_service)
    permission_endpoints = register_permission_endpoints(permission_router, path_prefix="", dependencies=None, include_auth=include_auth, permission_service=permission_service)
    tenant_endpoints = register_tenant_endpoints(tenant_router, path_prefix="", dependencies=None, include_auth=include_auth, tenant_service=tenant_service)
    
    # Include routers in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(user_router)
        app_or_router.include_router(group_router)
        app_or_router.include_router(role_router)
        app_or_router.include_router(responsibility_role_router)
        app_or_router.include_router(permission_router)
        app_or_router.include_router(tenant_router)
    
    # Return all registered endpoints
    return {
        "users": user_endpoints,
        "groups": group_endpoints,
        "roles": role_endpoints,
        "responsibility_roles": responsibility_role_endpoints,
        "permissions": permission_endpoints,
        "tenants": tenant_endpoints,
    }