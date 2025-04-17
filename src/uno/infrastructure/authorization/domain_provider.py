"""
Dependency injection provider for the Authorization domain services.

This module integrates the authorization domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

import logging
from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.database.db_manager import DBManager
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
    AuthorizationService,
)


@lru_cache(maxsize=1)
def get_authorization_provider() -> UnoServiceProvider:
    """
    Get the Authorization module service provider.
    
    Returns:
        A configured service provider for the Authorization module
    """
    provider = UnoServiceProvider("authorization")
    logger = logging.getLogger("uno.authorization")
    
    # Register repositories with their dependencies
    provider.register(
        UserRepository,
        lambda container: UserRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        GroupRepository,
        lambda container: GroupRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        RoleRepository,
        lambda container: RoleRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        PermissionRepository,
        lambda container: PermissionRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        ResponsibilityRoleRepository,
        lambda container: ResponsibilityRoleRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        TenantRepository,
        lambda container: TenantRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Tenant service (has no other service dependencies)
    provider.register(
        TenantService,
        lambda container: TenantService(
            repository=container.resolve(TenantRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Permission service (has no other service dependencies)
    provider.register(
        PermissionService,
        lambda container: PermissionService(
            repository=container.resolve(PermissionRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Responsibility role service (depends on tenant service)
    provider.register(
        ResponsibilityRoleService,
        lambda container: ResponsibilityRoleService(
            repository=container.resolve(ResponsibilityRoleRepository),
            tenant_service=container.resolve(TenantService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Group service (depends on tenant service)
    provider.register(
        GroupService,
        lambda container: GroupService(
            repository=container.resolve(GroupRepository),
            tenant_service=container.resolve(TenantService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Role service (depends on permission service, responsibility service, and tenant service)
    provider.register(
        RoleService,
        lambda container: RoleService(
            repository=container.resolve(RoleRepository),
            permission_service=container.resolve(PermissionService),
            responsibility_service=container.resolve(ResponsibilityRoleService),
            tenant_service=container.resolve(TenantService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # User service (depends on group service, role service, and tenant service)
    provider.register(
        UserService,
        lambda container: UserService(
            repository=container.resolve(UserRepository),
            group_service=container.resolve(GroupService),
            role_service=container.resolve(RoleService),
            tenant_service=container.resolve(TenantService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Authorization service (depends on all other services)
    provider.register(
        AuthorizationService,
        lambda container: AuthorizationService(
            user_service=container.resolve(UserService),
            role_service=container.resolve(RoleService),
            permission_service=container.resolve(PermissionService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


def configure_authorization_services(container):
    """
    Configure authorization services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_authorization_provider()
    provider.configure_container(container)