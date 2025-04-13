"""
API endpoints for the Authorization module using the Domain approach.

This module provides FastAPI endpoints for authorization entities using the domain-driven
design approach with domain services and entities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from enum import Enum

from uno.domain.api_integration import (
    create_domain_router,
    domain_endpoint,
)
from uno.dependencies.scoped_container import get_service
from uno.enums import SQLOperation
from uno.authorization.domain_services import (
    UserService,
    GroupService,
    RoleService,
    PermissionService,
    ResponsibilityRoleService,
    TenantService,
)
from uno.authorization.entities import (
    User,
    Group,
    Role,
    Permission,
    ResponsibilityRole,
    Tenant,
)


# Create routers using the domain_router factory
user_router = create_domain_router(
    entity_type=User,
    service_type=UserService,
    prefix="/api/users",
    tags=["Authorization", "Users"],
)

group_router = create_domain_router(
    entity_type=Group,
    service_type=GroupService,
    prefix="/api/groups",
    tags=["Authorization", "Groups"],
)

role_router = create_domain_router(
    entity_type=Role,
    service_type=RoleService,
    prefix="/api/roles",
    tags=["Authorization", "Roles"],
)

permission_router = create_domain_router(
    entity_type=Permission,
    service_type=PermissionService,
    prefix="/api/permissions",
    tags=["Authorization", "Permissions"],
)

responsibility_role_router = create_domain_router(
    entity_type=ResponsibilityRole,
    service_type=ResponsibilityRoleService,
    prefix="/api/responsibility-roles",
    tags=["Authorization", "Responsibility Roles"],
)

tenant_router = create_domain_router(
    entity_type=Tenant,
    service_type=TenantService,
    prefix="/api/tenants",
    tags=["Authorization", "Tenants"],
)


# Custom endpoints for User

@user_router.get("/by-email/{email}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_user_by_email(
    email: str = Path(..., description="The email address of the user"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get a user by email address."""
    result = await service.find_by_email(email)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="User not found")
    
    return result.value.to_dict()


@user_router.get("/by-handle/{handle}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_user_by_handle(
    handle: str = Path(..., description="The handle of the user"),
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID to filter by"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get a user by handle, optionally within a specific tenant."""
    result = await service.find_by_handle(handle, tenant_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="User not found")
    
    return result.value.to_dict()


@user_router.get("/in-tenant/{tenant_id}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_users_by_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get all users in a specific tenant."""
    result = await service.find_by_tenant(tenant_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [user.to_dict() for user in result.value]


@user_router.get("/in-group/{group_id}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_users_by_group(
    group_id: str = Path(..., description="The ID of the group"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get all users in a specific group."""
    result = await service.find_by_group(group_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [user.to_dict() for user in result.value]


@user_router.get("/with-role/{role_id}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_users_by_role(
    role_id: str = Path(..., description="The ID of the role"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get all users with a specific role."""
    result = await service.find_by_role(role_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [user.to_dict() for user in result.value]


@user_router.get("/superusers")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_superusers(
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get all superusers."""
    result = await service.find_superusers(limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [user.to_dict() for user in result.value]


@user_router.get("/{id}/with-relationships")
@domain_endpoint(entity_type=User, service_type=UserService)
async def get_user_with_relationships(
    id: str = Path(..., description="The ID of the user"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Get a user with its related entities (groups, roles, tenant)."""
    result = await service.get_with_relationships(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@user_router.post("/{user_id}/groups/{group_id}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def add_user_to_group(
    user_id: str = Path(..., description="The ID of the user"),
    group_id: str = Path(..., description="The ID of the group"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Add a user to a group."""
    result = await service.add_to_group(user_id, group_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@user_router.post("/{user_id}/roles/{role_id}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def add_role_to_user(
    user_id: str = Path(..., description="The ID of the user"),
    role_id: str = Path(..., description="The ID of the role"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Add a role to a user."""
    result = await service.add_role(user_id, role_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@user_router.get("/{user_id}/check-permission/{meta_type_id}/{operation}")
@domain_endpoint(entity_type=User, service_type=UserService)
async def check_user_permission(
    user_id: str = Path(..., description="The ID of the user"),
    meta_type_id: str = Path(..., description="The meta type ID"),
    operation: SQLOperation = Path(..., description="The SQL operation"),
    service: UserService = Depends(lambda: get_service(UserService))
):
    """Check if a user has a specific permission."""
    result = await service.check_permission(user_id, meta_type_id, operation)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return {"has_permission": result.value}


# Custom endpoints for Group

@group_router.get("/by-name/{name}")
@domain_endpoint(entity_type=Group, service_type=GroupService)
async def get_group_by_name(
    name: str = Path(..., description="The name of the group"),
    tenant_id: str = Query(..., description="The tenant ID"),
    service: GroupService = Depends(lambda: get_service(GroupService))
):
    """Get a group by name in a specific tenant."""
    result = await service.find_by_name(name, tenant_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return result.value.to_dict()


@group_router.get("/in-tenant/{tenant_id}")
@domain_endpoint(entity_type=Group, service_type=GroupService)
async def get_groups_by_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: GroupService = Depends(lambda: get_service(GroupService))
):
    """Get all groups in a specific tenant."""
    result = await service.find_by_tenant(tenant_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [group.to_dict() for group in result.value]


@group_router.get("/for-user/{user_id}")
@domain_endpoint(entity_type=Group, service_type=GroupService)
async def get_groups_by_user(
    user_id: str = Path(..., description="The ID of the user"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: GroupService = Depends(lambda: get_service(GroupService))
):
    """Get all groups for a specific user."""
    result = await service.find_by_user(user_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [group.to_dict() for group in result.value]


@group_router.get("/{id}/with-relationships")
@domain_endpoint(entity_type=Group, service_type=GroupService)
async def get_group_with_relationships(
    id: str = Path(..., description="The ID of the group"),
    service: GroupService = Depends(lambda: get_service(GroupService))
):
    """Get a group with its related entities (users, tenant)."""
    result = await service.get_with_relationships(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@group_router.post("/{group_id}/users/{user_id}")
@domain_endpoint(entity_type=Group, service_type=GroupService)
async def add_user_to_group_from_group(
    group_id: str = Path(..., description="The ID of the group"),
    user_id: str = Path(..., description="The ID of the user"),
    service: GroupService = Depends(lambda: get_service(GroupService))
):
    """Add a user to a group."""
    result = await service.add_user(group_id, user_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


# Custom endpoints for Role

@role_router.get("/by-name/{name}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def get_role_by_name(
    name: str = Path(..., description="The name of the role"),
    tenant_id: str = Query(..., description="The tenant ID"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Get a role by name in a specific tenant."""
    result = await service.find_by_name(name, tenant_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return result.value.to_dict()


@role_router.get("/in-tenant/{tenant_id}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def get_roles_by_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Get all roles in a specific tenant."""
    result = await service.find_by_tenant(tenant_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [role.to_dict() for role in result.value]


@role_router.get("/for-user/{user_id}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def get_roles_by_user(
    user_id: str = Path(..., description="The ID of the user"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Get all roles for a specific user."""
    result = await service.find_by_user(user_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [role.to_dict() for role in result.value]


@role_router.get("/for-responsibility/{responsibility_id}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def get_roles_by_responsibility(
    responsibility_id: str = Path(..., description="The ID of the responsibility"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Get all roles with a specific responsibility."""
    result = await service.find_by_responsibility(responsibility_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [role.to_dict() for role in result.value]


@role_router.get("/{id}/with-relationships")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def get_role_with_relationships(
    id: str = Path(..., description="The ID of the role"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Get a role with its related entities (users, permissions, tenant, responsibility)."""
    result = await service.get_with_relationships(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@role_router.post("/{role_id}/permissions/{permission_id}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def add_permission_to_role(
    role_id: str = Path(..., description="The ID of the role"),
    permission_id: int = Path(..., description="The ID of the permission"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Add a permission to a role."""
    result = await service.add_permission(role_id, permission_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@role_router.post("/{role_id}/users/{user_id}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def add_user_to_role(
    role_id: str = Path(..., description="The ID of the role"),
    user_id: str = Path(..., description="The ID of the user"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Add a user to a role."""
    result = await service.add_user(role_id, user_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@role_router.get("/{role_id}/check-permission/{meta_type_id}/{operation}")
@domain_endpoint(entity_type=Role, service_type=RoleService)
async def check_role_permission(
    role_id: str = Path(..., description="The ID of the role"),
    meta_type_id: str = Path(..., description="The meta type ID"),
    operation: SQLOperation = Path(..., description="The SQL operation"),
    service: RoleService = Depends(lambda: get_service(RoleService))
):
    """Check if a role has a specific permission."""
    result = await service.has_permission(role_id, meta_type_id, operation)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return {"has_permission": result.value}


# Custom endpoints for Permission

@permission_router.get("/for-meta-type/{meta_type_id}")
@domain_endpoint(entity_type=Permission, service_type=PermissionService)
async def get_permissions_by_meta_type(
    meta_type_id: str = Path(..., description="The ID of the meta type"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: PermissionService = Depends(lambda: get_service(PermissionService))
):
    """Get all permissions for a specific meta type."""
    result = await service.find_by_meta_type(meta_type_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [permission.to_dict() for permission in result.value]


@permission_router.get("/for-operation/{operation}")
@domain_endpoint(entity_type=Permission, service_type=PermissionService)
async def get_permissions_by_operation(
    operation: str = Path(..., description="The operation"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: PermissionService = Depends(lambda: get_service(PermissionService))
):
    """Get all permissions for a specific operation."""
    result = await service.find_by_operation(operation, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [permission.to_dict() for permission in result.value]


@permission_router.get("/exact/{meta_type_id}/{operation}")
@domain_endpoint(entity_type=Permission, service_type=PermissionService)
async def get_permission_by_meta_type_and_operation(
    meta_type_id: str = Path(..., description="The ID of the meta type"),
    operation: str = Path(..., description="The operation"),
    service: PermissionService = Depends(lambda: get_service(PermissionService))
):
    """Get a permission by meta type and operation."""
    result = await service.find_by_meta_type_and_operation(meta_type_id, operation)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return result.value.to_dict()


@permission_router.get("/for-role/{role_id}")
@domain_endpoint(entity_type=Permission, service_type=PermissionService)
async def get_permissions_by_role(
    role_id: str = Path(..., description="The ID of the role"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: PermissionService = Depends(lambda: get_service(PermissionService))
):
    """Get all permissions for a specific role."""
    result = await service.find_by_role(role_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [permission.to_dict() for permission in result.value]


# Custom endpoints for ResponsibilityRole

@responsibility_role_router.get("/by-name/{name}")
@domain_endpoint(entity_type=ResponsibilityRole, service_type=ResponsibilityRoleService)
async def get_responsibility_role_by_name(
    name: str = Path(..., description="The name of the responsibility role"),
    tenant_id: str = Query(..., description="The tenant ID"),
    service: ResponsibilityRoleService = Depends(lambda: get_service(ResponsibilityRoleService))
):
    """Get a responsibility role by name in a specific tenant."""
    result = await service.find_by_name(name, tenant_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="Responsibility role not found")
    
    return result.value.to_dict()


@responsibility_role_router.get("/in-tenant/{tenant_id}")
@domain_endpoint(entity_type=ResponsibilityRole, service_type=ResponsibilityRoleService)
async def get_responsibility_roles_by_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: ResponsibilityRoleService = Depends(lambda: get_service(ResponsibilityRoleService))
):
    """Get all responsibility roles in a specific tenant."""
    result = await service.find_by_tenant(tenant_id, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [responsibility.to_dict() for responsibility in result.value]


@responsibility_role_router.get("/{id}/with-relationships")
@domain_endpoint(entity_type=ResponsibilityRole, service_type=ResponsibilityRoleService)
async def get_responsibility_role_with_relationships(
    id: str = Path(..., description="The ID of the responsibility role"),
    service: ResponsibilityRoleService = Depends(lambda: get_service(ResponsibilityRoleService))
):
    """Get a responsibility role with its related entities (tenant)."""
    result = await service.get_with_relationships(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


# Custom endpoints for Tenant

@tenant_router.get("/by-name/{name}")
@domain_endpoint(entity_type=Tenant, service_type=TenantService)
async def get_tenant_by_name(
    name: str = Path(..., description="The name of the tenant"),
    service: TenantService = Depends(lambda: get_service(TenantService))
):
    """Get a tenant by name."""
    result = await service.find_by_name(name)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return result.value.to_dict()


@tenant_router.get("/by-type/{tenant_type}")
@domain_endpoint(entity_type=Tenant, service_type=TenantService)
async def get_tenants_by_type(
    tenant_type: str = Path(..., description="The type of the tenant"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    service: TenantService = Depends(lambda: get_service(TenantService))
):
    """Get all tenants of a specific type."""
    result = await service.find_by_type(tenant_type, limit, offset)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [tenant.to_dict() for tenant in result.value]


@tenant_router.get("/{id}/with-relationships")
@domain_endpoint(entity_type=Tenant, service_type=TenantService)
async def get_tenant_with_relationships(
    id: str = Path(..., description="The ID of the tenant"),
    service: TenantService = Depends(lambda: get_service(TenantService))
):
    """Get a tenant with its related entities (users, groups, roles)."""
    result = await service.get_with_relationships(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@tenant_router.post("/{tenant_id}/users/{user_id}")
@domain_endpoint(entity_type=Tenant, service_type=TenantService)
async def add_user_to_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant"),
    user_id: str = Path(..., description="The ID of the user"),
    service: TenantService = Depends(lambda: get_service(TenantService))
):
    """Add a user to a tenant."""
    result = await service.add_user(tenant_id, user_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


def register_authorization_routers(app):
    """
    Register all authorization routers with a FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    app.include_router(user_router)
    app.include_router(group_router)
    app.include_router(role_router)
    app.include_router(permission_router)
    app.include_router(responsibility_role_router)
    app.include_router(tenant_router)