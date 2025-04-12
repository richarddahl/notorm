"""
Multi-tenancy support for the Uno framework.

This module provides comprehensive support for building multi-tenant applications,
including tenant isolation, tenant-aware repositories, and tenant context management.
"""

from uno.core.multitenancy.models import (
    Tenant, TenantStatus, UserTenantAssociation, UserTenantStatus,
    TenantAwareModel, TenantInvitation, TenantSettings
)
from uno.core.multitenancy.context import (
    TenantContext, get_current_tenant_context, set_current_tenant_context,
    tenant_context, clear_tenant_context
)
from uno.core.multitenancy.middleware import (
    TenantIdentificationMiddleware, TenantHeaderMiddleware,
    TenantHostMiddleware, TenantPathMiddleware
)
from uno.core.multitenancy.repository import (
    TenantAwareRepository, TenantRepository, UserTenantAssociationRepository
)
from uno.core.multitenancy.service import (
    TenantService
)
from uno.core.multitenancy.isolation import (
    RLSIsolationStrategy, SuperuserBypassMixin, AdminTenantMixin
)
from uno.core.multitenancy.utils import (
    get_tenant_id_from_request, validate_tenant_access, get_user_tenants,
    is_tenant_admin, tenant_required, tenant_admin_required
)
from uno.core.multitenancy.admin import (
    TenantAdminService, create_tenant_admin_router
)
from uno.core.multitenancy.config import (
    TenantConfig, TenantConfigService, TenantConfigError
)
from uno.core.multitenancy.config_admin import (
    create_tenant_config_router, DEFAULT_CONFIG, CONFIG_SCHEMA, default_tenant_config_router
)

__all__ = [
    # Models
    "Tenant", "TenantStatus", "UserTenantAssociation", "UserTenantStatus",
    "TenantAwareModel", "TenantInvitation", "TenantSettings",
    
    # Context management
    "TenantContext", "get_current_tenant_context", "set_current_tenant_context",
    "tenant_context", "clear_tenant_context", 
    
    # Middleware
    "TenantIdentificationMiddleware", "TenantHeaderMiddleware",
    "TenantHostMiddleware", "TenantPathMiddleware",
    
    # Repository
    "TenantAwareRepository", "TenantRepository", "UserTenantAssociationRepository",
    
    # Services
    "TenantService", "TenantAdminService", "TenantConfig", "TenantConfigService",
    
    # Isolation
    "RLSIsolationStrategy", "SuperuserBypassMixin", "AdminTenantMixin",
    
    # Utilities
    "get_tenant_id_from_request", "validate_tenant_access", "get_user_tenants",
    "is_tenant_admin", "tenant_required", "tenant_admin_required",
    
    # Admin Interfaces
    "create_tenant_admin_router", "create_tenant_config_router", 
    "default_tenant_config_router",
    
    # Configuration
    "DEFAULT_CONFIG", "CONFIG_SCHEMA", "TenantConfigError",
]