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

# Models
from uno.authorization.models import (
    UserModel,
    GroupModel,
    RoleModel,
    ResponsibilityRoleModel,
    PermissionModel,
    TenantModel,
)

# Repositories
from uno.authorization.repositories import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    ResponsibilityRoleRepository,
    PermissionRepository,
    TenantRepository,
)

# Services
from uno.authorization.services import (
    UserService,
    GroupService,
    RoleService,
    ResponsibilityRoleService,
    PermissionService,
    TenantService,
    AuthorizationService,
)

# Error types
from uno.authorization.errors import (
    AuthorizationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    AuthenticationError,
)

# RLS integration
from uno.authorization.rlssql import (
    setup_rls_for_table,
    setup_bypass_rls_for_admin,
    set_tenant_context,
    clear_tenant_context,
)

__all__ = [
    # Domain Entities (DDD)
    "User",
    "Group",
    "Role",
    "ResponsibilityRole",
    "Permission",
    "Tenant",
    
    # Models
    "UserModel",
    "GroupModel",
    "RoleModel",
    "ResponsibilityRoleModel",
    "PermissionModel",
    "TenantModel",
    
    # Repositories
    "UserRepository",
    "GroupRepository",
    "RoleRepository",
    "ResponsibilityRoleRepository",
    "PermissionRepository",
    "TenantRepository",
    
    # Services
    "UserService",
    "GroupService",
    "RoleService",
    "ResponsibilityRoleService",
    "PermissionService",
    "TenantService",
    "AuthorizationService",
    
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
