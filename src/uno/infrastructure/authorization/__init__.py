# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Authorization module for Uno.

This module provides a comprehensive authorization system that supports:
- User authentication and management
- Role-based access control (RBAC)
- Permission management
- Multi-tenant isolation
- Row-level security (RLS) in PostgreSQL

Key components:
- Domain Entities: Core business objects with behavior
  - User: Represents system users with authentication information
  - Group: Represents collections of users
  - Role: Represents sets of permissions assigned to users
  - Permission: Represents the ability to perform operations
  - Tenant: Represents organizations in a multi-tenant system
- Repository Pattern: Data access following domain-driven design
- Domain Services: Business logic for authorization
- API Integration: Register standardized API endpoints
- Row-Level Security: Database-level access controls
"""

# Domain entities (DDD)
from uno.authorization.entities import (
    User,
    Group,
    Role,
    ResponsibilityRole, 
    Permission,
    Tenant,
)

# Domain repositories (DDD)
from uno.authorization.domain_repositories import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    ResponsibilityRoleRepository,
    PermissionRepository,
    TenantRepository,
)

# Domain services (DDD)
from uno.authorization.domain_services import (
    UserService,
    GroupService,
    RoleService,
    ResponsibilityRoleService,
    PermissionService,
    TenantService,
    AuthorizationService,
)

# Dependency provider

    get_authorization_provider,
    configure_authorization_services,
)

# Domain API endpoints
from uno.authorization.domain_endpoints import (
    register_auth_endpoints,
)

# RLS integration
from uno.authorization.rlssql import (
    setup_rls_for_table,
    setup_bypass_rls_for_admin,
    set_tenant_context,
    clear_tenant_context,
)

# Error types
from uno.authorization.errors import (
    AuthorizationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    AuthenticationError,
)

__all__ = [
    # Domain Entities (DDD)
    "User",
    "Group",
    "Role",
    "ResponsibilityRole",
    "Permission",
    "Tenant",
    
    # Domain Repositories (DDD)
    "UserRepository",
    "GroupRepository",
    "RoleRepository",
    "ResponsibilityRoleRepository",
    "PermissionRepository",
    "TenantRepository",
    
    # Domain Services (DDD)
    "UserService",
    "GroupService",
    "RoleService",
    "ResponsibilityRoleService",
    "PermissionService",
    "TenantService",
    "AuthorizationService",
    
    # Dependency Injection
    "get_authorization_provider",
    "configure_authorization_services",
    
    # API Integration
    "register_auth_endpoints",
    
    # Error types
    "AuthorizationError",
    "PermissionDeniedError",
    "ResourceNotFoundError",
    "AuthenticationError",
    
    # RLS integration
    "setup_rls_for_table",
    "setup_bypass_rls_for_admin",
    "set_tenant_context",
    "clear_tenant_context",
]
