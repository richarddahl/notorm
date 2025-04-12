"""
Utility functions for multi-tenancy.

This module provides utility functions for working with multi-tenant applications,
such as validating tenant access and extracting tenant information from requests.
"""

from typing import Dict, List, Optional, Any, Callable, Union
import re
from functools import wraps

from starlette.requests import Request
from fastapi import HTTPException, Depends, status

from uno.core.multitenancy.context import get_current_tenant_context
from uno.core.multitenancy.service import TenantService


async def get_tenant_id_from_request(
    request: Request,
    header_name: str = "X-Tenant-ID",
    subdomain_pattern: Optional[str] = None,
    path_prefix: bool = False
) -> Optional[str]:
    """
    Extract tenant ID from request using multiple strategies.
    
    Args:
        request: The HTTP request
        header_name: Name of the header containing the tenant ID
        subdomain_pattern: Pattern for extracting tenant ID from subdomain
        path_prefix: Whether to extract tenant ID from path prefix
        
    Returns:
        The tenant ID if found, None otherwise
    """
    # Strategy 1: Check request state (if previously identified by middleware)
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id
    
    # Strategy 2: Header
    tenant_id = request.headers.get(header_name)
    if tenant_id:
        return tenant_id
    
    # Strategy 3: Subdomain
    if subdomain_pattern:
        host = request.headers.get("host", "")
        if host:
            match = re.match(subdomain_pattern, host)
            if match and match.group(1):
                return match.group(1)
    
    # Strategy 4: Path prefix
    if path_prefix:
        path = request.url.path
        if path.startswith("/"):
            path = path[1:]
            
        parts = path.split("/")
        if parts and parts[0]:
            return parts[0]
    
    # Strategy 5: User property (if set by auth middleware)
    if hasattr(request, "user") and hasattr(request.user, "tenant_id"):
        return request.user.tenant_id
    
    return None


async def validate_tenant_access(
    request: Request,
    tenant_service: TenantService,
    tenant_id: Optional[str] = None
) -> str:
    """
    Validate that the current user has access to the specified tenant.
    
    Args:
        request: The HTTP request
        tenant_service: Service for tenant operations
        tenant_id: Optional tenant ID to validate (if not provided, extracted from request)
        
    Returns:
        The validated tenant ID
        
    Raises:
        HTTPException: If the tenant ID is invalid or the user doesn't have access
    """
    # Get user ID from request (assuming authentication middleware sets it)
    user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get tenant ID (from parameter or request)
    if not tenant_id:
        tenant_id = await get_tenant_id_from_request(request)
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required"
        )
    
    # Check if tenant exists and is active
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant or tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found or inactive"
        )
    
    # Check if user has access to tenant
    has_access = await tenant_service.user_has_access_to_tenant(user_id, tenant_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have access to tenant {tenant_id}"
        )
    
    return tenant_id


async def get_user_tenants(
    request: Request,
    tenant_service: TenantService
) -> List[Dict[str, Any]]:
    """
    Get all tenants that the current user has access to.
    
    Args:
        request: The HTTP request
        tenant_service: Service for tenant operations
        
    Returns:
        List of tenants with access information
        
    Raises:
        HTTPException: If the user is not authenticated
    """
    # Get user ID from request (assuming authentication middleware sets it)
    user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get all tenant associations for the user
    associations = await tenant_service.get_user_tenants(user_id)
    
    # Get tenant details for each association
    tenants = []
    for association in associations:
        tenant = await tenant_service.get_tenant(association.tenant_id)
        if tenant and tenant.status == "active":
            tenants.append({
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "roles": association.roles,
                "is_primary": association.is_primary
            })
    
    return tenants


async def is_tenant_admin(
    request: Request,
    tenant_service: TenantService,
    tenant_id: Optional[str] = None,
    admin_role: str = "admin"
) -> bool:
    """
    Check if the current user is an admin of the specified tenant.
    
    Args:
        request: The HTTP request
        tenant_service: Service for tenant operations
        tenant_id: Optional tenant ID to check (if not provided, extracted from request)
        admin_role: Role name that indicates admin privileges
        
    Returns:
        True if the user is an admin, False otherwise
    """
    # Get user ID from request (assuming authentication middleware sets it)
    user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
    
    if not user_id:
        return False
    
    # Get tenant ID (from parameter or request)
    if not tenant_id:
        tenant_id = await get_tenant_id_from_request(request)
    
    if not tenant_id:
        return False
    
    # Get the user-tenant association
    association = await tenant_service.get_user_tenant(user_id, tenant_id)
    if not association or association.status != "active":
        return False
    
    # Check if the user has the admin role
    return admin_role in association.roles


def tenant_required(
    tenant_service: TenantService = Depends(),
    tenant_id_param: Optional[str] = None
):
    """
    Dependency for routes that require a valid tenant.
    
    This dependency validates that the current user has access to the specified tenant
    and sets it as the current tenant context for the request.
    
    Args:
        tenant_service: Service for tenant operations
        tenant_id_param: Optional name of the path parameter containing the tenant ID
        
    Returns:
        Dependency function that returns the validated tenant ID
    """
    async def _get_and_validate_tenant(request: Request) -> str:
        # Get tenant ID from path parameter if specified
        tenant_id = None
        if tenant_id_param and tenant_id_param in request.path_params:
            tenant_id = request.path_params[tenant_id_param]
        
        # Validate tenant access
        validated_tenant_id = await validate_tenant_access(
            request, tenant_service, tenant_id
        )
        
        # Set the tenant ID in the request state for easy access
        request.state.tenant_id = validated_tenant_id
        
        return validated_tenant_id
    
    return _get_and_validate_tenant


def tenant_admin_required(
    tenant_service: TenantService = Depends(),
    tenant_id_param: Optional[str] = None,
    admin_role: str = "admin"
):
    """
    Dependency for routes that require tenant admin privileges.
    
    This dependency validates that the current user is an admin of the specified tenant
    and sets it as the current tenant context for the request.
    
    Args:
        tenant_service: Service for tenant operations
        tenant_id_param: Optional name of the path parameter containing the tenant ID
        admin_role: Role name that indicates admin privileges
        
    Returns:
        Dependency function that returns the validated tenant ID
    """
    async def _get_and_validate_tenant_admin(request: Request) -> str:
        # Get tenant ID from path parameter if specified
        tenant_id = None
        if tenant_id_param and tenant_id_param in request.path_params:
            tenant_id = request.path_params[tenant_id_param]
        
        # Validate tenant access
        validated_tenant_id = await validate_tenant_access(
            request, tenant_service, tenant_id
        )
        
        # Check if the user is an admin
        is_admin = await is_tenant_admin(
            request, tenant_service, validated_tenant_id, admin_role
        )
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # Set the tenant ID in the request state for easy access
        request.state.tenant_id = validated_tenant_id
        
        return validated_tenant_id
    
    return _get_and_validate_tenant_admin