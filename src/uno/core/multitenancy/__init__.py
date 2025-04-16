"""
Multi-tenancy support for the Uno framework.

This module provides comprehensive support for building multi-tenant applications,
including tenant isolation, tenant-aware repositories, and tenant context management.
It follows a domain-driven design approach with clear separation of concerns between
entities, repositories, services, and endpoints.
"""

# Domain entities
from uno.core.multitenancy.entities import (
    Tenant, TenantId, TenantSlug, TenantStatus,
    UserTenantAssociation, UserTenantAssociationId, UserTenantStatus,
    TenantInvitation, TenantInvitationId,
    TenantSetting, TenantSettingId, UserId
)

# Domain repositories
from uno.core.multitenancy.domain_repositories import (
    TenantRepositoryProtocol, UserTenantAssociationRepositoryProtocol,
    TenantInvitationRepositoryProtocol, TenantSettingRepositoryProtocol,
    TenantAwareRepositoryProtocol,
    TenantSQLAlchemyRepository, UserTenantAssociationSQLAlchemyRepository
)

# Domain services
from uno.core.multitenancy.domain_services import (
    TenantServiceProtocol, UserTenantServiceProtocol, TenantInvitationServiceProtocol,
    TenantService, UserTenantService, TenantInvitationService
)

# Domain provider
from uno.core.multitenancy.domain_provider import (
    MultitenancyProvider, TestingMultitenancyProvider
)

# Domain endpoints
from uno.core.multitenancy.domain_endpoints import router as multitenancy_router

# Context management
from uno.core.multitenancy.context import (
    TenantContext, get_current_tenant_context, set_current_tenant_context,
    tenant_context, clear_tenant_context
)

# Middleware
from uno.core.multitenancy.middleware import (
    TenantIdentificationMiddleware, TenantHeaderMiddleware,
    TenantHostMiddleware, TenantPathMiddleware
)

# Legacy components (deprecated)
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
    # Domain Entities
    "Tenant", "TenantId", "TenantSlug", "TenantStatus",
    "UserTenantAssociation", "UserTenantAssociationId", "UserTenantStatus",
    "TenantInvitation", "TenantInvitationId",
    "TenantSetting", "TenantSettingId", "UserId",
    
    # Domain Repositories
    "TenantRepositoryProtocol", "UserTenantAssociationRepositoryProtocol",
    "TenantInvitationRepositoryProtocol", "TenantSettingRepositoryProtocol",
    "TenantAwareRepositoryProtocol",
    "TenantSQLAlchemyRepository", "UserTenantAssociationSQLAlchemyRepository",
    
    # Domain Services
    "TenantServiceProtocol", "UserTenantServiceProtocol", "TenantInvitationServiceProtocol",
    "TenantService", "UserTenantService", "TenantInvitationService",
    
    # Domain Provider
    "MultitenancyProvider", "TestingMultitenancyProvider",
    
    # Domain Endpoints
    "multitenancy_router",
    
    # Context management
    "TenantContext", "get_current_tenant_context", "set_current_tenant_context",
    "tenant_context", "clear_tenant_context", 
    
    # Middleware
    "TenantIdentificationMiddleware", "TenantHeaderMiddleware",
    "TenantHostMiddleware", "TenantPathMiddleware",
    
    # Legacy components (deprecated)
    "TenantAwareRepository", "TenantRepository", "UserTenantAssociationRepository",
    "TenantService", "TenantAdminService", "TenantConfig", "TenantConfigService",
    "RLSIsolationStrategy", "SuperuserBypassMixin", "AdminTenantMixin",
    "get_tenant_id_from_request", "validate_tenant_access", "get_user_tenants",
    "is_tenant_admin", "tenant_required", "tenant_admin_required",
    "create_tenant_admin_router", "create_tenant_config_router", 
    "default_tenant_config_router",
    "DEFAULT_CONFIG", "CONFIG_SCHEMA", "TenantConfigError",
]