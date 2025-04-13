"""
Dependency injection provider for the Authorization domain services.

This module integrates the authorization domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
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
from uno.authorization.domain_services import (
    UserService,
    GroupService,
    RoleService,
    PermissionService,
    ResponsibilityRoleService,
    TenantService,
)


@lru_cache(maxsize=1)
def get_authorization_provider() -> UnoServiceProvider:
    """
    Get the Authorization module service provider.
    
    Returns:
        A configured service provider for the Authorization module
    """
    provider = UnoServiceProvider("authorization")
    
    # Register repositories
    provider.register(UserRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(GroupRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(RoleRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(PermissionRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ResponsibilityRoleRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(TenantRepository, lifecycle=ServiceLifecycle.SCOPED)
    
    # Register services
    provider.register(UserService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(GroupService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(RoleService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(PermissionService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ResponsibilityRoleService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(TenantService, lifecycle=ServiceLifecycle.SCOPED)
    
    return provider


def configure_authorization_services(container):
    """
    Configure authorization services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_authorization_provider()
    provider.configure_container(container)


def create_user_service_factory(
    user_repo: Optional[UserRepository] = None,
    group_service: Optional[GroupService] = None,
    role_service: Optional[RoleService] = None,
    tenant_service: Optional[TenantService] = None
):
    """
    Create a factory function for UserService.
    
    This function creates a factory that can be used with the dependency
    injection system to create UserService instances with specific
    dependencies.
    
    Args:
        user_repo: Optional repository for users
        group_service: Optional service for groups
        role_service: Optional service for roles
        tenant_service: Optional service for tenants
        
    Returns:
        A factory function for creating UserService instances
    """
    def create_service():
        return UserService(
            repository=user_repo,
            group_service=group_service,
            role_service=role_service,
            tenant_service=tenant_service
        )
    
    return create_service


def create_group_service_factory(
    group_repo: Optional[GroupRepository] = None,
    user_service: Optional[UserService] = None,
    tenant_service: Optional[TenantService] = None
):
    """
    Create a factory function for GroupService.
    
    This function creates a factory that can be used with the dependency
    injection system to create GroupService instances with specific
    dependencies.
    
    Args:
        group_repo: Optional repository for groups
        user_service: Optional service for users
        tenant_service: Optional service for tenants
        
    Returns:
        A factory function for creating GroupService instances
    """
    def create_service():
        return GroupService(
            repository=group_repo,
            user_service=user_service,
            tenant_service=tenant_service
        )
    
    return create_service


def create_role_service_factory(
    role_repo: Optional[RoleRepository] = None,
    user_service: Optional[UserService] = None,
    permission_service: Optional[PermissionService] = None,
    tenant_service: Optional[TenantService] = None,
    responsibility_service: Optional[ResponsibilityRoleService] = None
):
    """
    Create a factory function for RoleService.
    
    This function creates a factory that can be used with the dependency
    injection system to create RoleService instances with specific
    dependencies.
    
    Args:
        role_repo: Optional repository for roles
        user_service: Optional service for users
        permission_service: Optional service for permissions
        tenant_service: Optional service for tenants
        responsibility_service: Optional service for responsibility roles
        
    Returns:
        A factory function for creating RoleService instances
    """
    def create_service():
        return RoleService(
            repository=role_repo,
            user_service=user_service,
            permission_service=permission_service,
            tenant_service=tenant_service,
            responsibility_service=responsibility_service
        )
    
    return create_service


def create_permission_service_factory(
    permission_repo: Optional[PermissionRepository] = None
):
    """
    Create a factory function for PermissionService.
    
    This function creates a factory that can be used with the dependency
    injection system to create PermissionService instances with specific
    dependencies.
    
    Args:
        permission_repo: Optional repository for permissions
        
    Returns:
        A factory function for creating PermissionService instances
    """
    def create_service():
        return PermissionService(
            repository=permission_repo
        )
    
    return create_service


def create_responsibility_role_service_factory(
    responsibility_repo: Optional[ResponsibilityRoleRepository] = None,
    tenant_service: Optional[TenantService] = None
):
    """
    Create a factory function for ResponsibilityRoleService.
    
    This function creates a factory that can be used with the dependency
    injection system to create ResponsibilityRoleService instances with specific
    dependencies.
    
    Args:
        responsibility_repo: Optional repository for responsibility roles
        tenant_service: Optional service for tenants
        
    Returns:
        A factory function for creating ResponsibilityRoleService instances
    """
    def create_service():
        return ResponsibilityRoleService(
            repository=responsibility_repo,
            tenant_service=tenant_service
        )
    
    return create_service


def create_tenant_service_factory(
    tenant_repo: Optional[TenantRepository] = None,
    user_service: Optional[UserService] = None,
    group_service: Optional[GroupService] = None,
    role_service: Optional[RoleService] = None
):
    """
    Create a factory function for TenantService.
    
    This function creates a factory that can be used with the dependency
    injection system to create TenantService instances with specific
    dependencies.
    
    Args:
        tenant_repo: Optional repository for tenants
        user_service: Optional service for users
        group_service: Optional service for groups
        role_service: Optional service for roles
        
    Returns:
        A factory function for creating TenantService instances
    """
    def create_service():
        return TenantService(
            repository=tenant_repo,
            user_service=user_service,
            group_service=group_service,
            role_service=role_service
        )
    
    return create_service