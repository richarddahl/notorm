"""
Dependency injection provider for the Authorization domain services.

This module integrates the authorization domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

import logging
from uno.database.db_manager import DBManager
from uno.dependencies.modern_provider import ServiceLifecycle
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




def configure_authorization_services(container):
    """
    Configure authorization services in the DI container.
    """
    logger = logging.getLogger("uno.authorization")

    # Register repositories
    container.register(UserRepository, lambda c: UserRepository(db_factory=c.resolve(DBManager)), lifecycle=ServiceLifecycle.SCOPED)
    container.register(GroupRepository, lambda c: GroupRepository(db_factory=c.resolve(DBManager)), lifecycle=ServiceLifecycle.SCOPED)
    container.register(RoleRepository, lambda c: RoleRepository(db_factory=c.resolve(DBManager)), lifecycle=ServiceLifecycle.SCOPED)
    container.register(PermissionRepository, lambda c: PermissionRepository(db_factory=c.resolve(DBManager)), lifecycle=ServiceLifecycle.SCOPED)
    container.register(ResponsibilityRoleRepository, lambda c: ResponsibilityRoleRepository(db_factory=c.resolve(DBManager)), lifecycle=ServiceLifecycle.SCOPED)
    container.register(TenantRepository, lambda c: TenantRepository(db_factory=c.resolve(DBManager)), lifecycle=ServiceLifecycle.SCOPED)

    # Register services
    container.register(TenantService, lambda c: TenantService(
        repository=c.resolve(TenantRepository), logger=logger), lifecycle=ServiceLifecycle.SCOPED)
    container.register(PermissionService, lambda c: PermissionService(
        repository=c.resolve(PermissionRepository), logger=logger), lifecycle=ServiceLifecycle.SCOPED)
    container.register(ResponsibilityRoleService, lambda c: ResponsibilityRoleService(
        repository=c.resolve(ResponsibilityRoleRepository),
        tenant_service=c.resolve(TenantService), logger=logger), lifecycle=ServiceLifecycle.SCOPED)
    container.register(GroupService, lambda c: GroupService(
        repository=c.resolve(GroupRepository),
        tenant_service=c.resolve(TenantService), logger=logger), lifecycle=ServiceLifecycle.SCOPED)
    container.register(RoleService, lambda c: RoleService(
        repository=c.resolve(RoleRepository),
        permission_service=c.resolve(PermissionService),
        responsibility_service=c.resolve(ResponsibilityRoleService),
        tenant_service=c.resolve(TenantService), logger=logger), lifecycle=ServiceLifecycle.SCOPED)
    container.register(UserService, lambda c: UserService(
        repository=c.resolve(UserRepository),
        group_service=c.resolve(GroupService),
        role_service=c.resolve(RoleService),
        tenant_service=c.resolve(TenantService), logger=logger), lifecycle=ServiceLifecycle.SCOPED)
    container.register(AuthorizationService, lambda c: AuthorizationService(
        user_service=c.resolve(UserService),
        role_service=c.resolve(RoleService),
        permission_service=c.resolve(PermissionService), logger=logger), lifecycle=ServiceLifecycle.SCOPED)

