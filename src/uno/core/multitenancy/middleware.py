"""
Middleware for tenant identification.

This module provides middleware components for identifying the current tenant
from requests, based on various identification strategies like headers, hostnames,
or path parameters.
"""

import re
from typing import Optional, Callable, List, Dict, Any
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from uno.core.multitenancy.context import TenantContext, get_current_tenant_context
from uno.core.multitenancy.service import TenantService


class TenantIdentificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that identifies the current tenant.
    
    This middleware tries multiple strategies to identify the tenant for the current request.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_service: TenantService,
        header_name: str = "X-Tenant-ID",
        subdomain_pattern: Optional[str] = None,
        path_prefix: bool = False,
        jwt_claim: Optional[str] = None,
        default_tenant: Optional[str] = None,
        exclude_paths: List[str] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            tenant_service: Service for tenant operations
            header_name: Name of the header containing the tenant ID
            subdomain_pattern: Pattern for extracting tenant ID from subdomain
            path_prefix: Whether to extract tenant ID from path prefix
            jwt_claim: JWT claim containing the tenant ID
            default_tenant: Default tenant ID to use if no tenant is identified
            exclude_paths: List of paths to exclude from tenant identification
        """
        super().__init__(app)
        self.tenant_service = tenant_service
        self.header_name = header_name
        self.subdomain_pattern = subdomain_pattern
        self.path_prefix = path_prefix
        self.jwt_claim = jwt_claim
        self.default_tenant = default_tenant
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and set the tenant context.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Check if the path should be excluded
        if self._should_exclude(request.url.path):
            return await call_next(request)
        
        # Try to identify the tenant
        tenant_id = await self._identify_tenant(request)
        
        if tenant_id:
            # Set the tenant context
            async with TenantContext(tenant_id):
                # Store the tenant ID in the request state for easy access
                request.state.tenant_id = tenant_id
                
                # Process the request
                return await call_next(request)
        else:
            # No tenant identified, use default tenant if specified
            if self.default_tenant:
                async with TenantContext(self.default_tenant):
                    # Store the tenant ID in the request state for easy access
                    request.state.tenant_id = self.default_tenant
                    
                    # Process the request
                    return await call_next(request)
            else:
                # No tenant identified and no default tenant, proceed without tenant context
                request.state.tenant_id = None
                return await call_next(request)
    
    async def _identify_tenant(self, request: Request) -> Optional[str]:
        """
        Identify the tenant for the request.
        
        This method tries multiple strategies to identify the tenant.
        
        Args:
            request: The HTTP request
            
        Returns:
            The identified tenant ID, or None if no tenant was identified
        """
        # Strategy 1: Header
        tenant_id = self._extract_from_header(request)
        if tenant_id:
            return await self._validate_tenant(tenant_id)
        
        # Strategy 2: Subdomain
        tenant_id = self._extract_from_subdomain(request)
        if tenant_id:
            return await self._validate_tenant(tenant_id)
        
        # Strategy 3: Path prefix
        tenant_id = self._extract_from_path(request)
        if tenant_id:
            return await self._validate_tenant(tenant_id)
        
        # Strategy 4: JWT claim
        tenant_id = await self._extract_from_jwt(request)
        if tenant_id:
            return await self._validate_tenant(tenant_id)
        
        # No tenant identified
        return None
    
    def _extract_from_header(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from header.
        
        Args:
            request: The HTTP request
            
        Returns:
            The tenant ID from the header, or None if not found
        """
        return request.headers.get(self.header_name)
    
    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from subdomain.
        
        Args:
            request: The HTTP request
            
        Returns:
            The tenant ID from the subdomain, or None if not found
        """
        if not self.subdomain_pattern:
            return None
        
        host = request.headers.get("host", "")
        if not host:
            return None
        
        # Match the pattern against the host
        match = re.match(self.subdomain_pattern, host)
        if match and match.group(1):
            return match.group(1)
        
        return None
    
    def _extract_from_path(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from path.
        
        Args:
            request: The HTTP request
            
        Returns:
            The tenant ID from the path, or None if not found
        """
        if not self.path_prefix:
            return None
        
        path = request.url.path
        if path.startswith("/"):
            path = path[1:]
        
        parts = path.split("/")
        if parts and parts[0]:
            return parts[0]
        
        return None
    
    async def _extract_from_jwt(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from JWT.
        
        Args:
            request: The HTTP request
            
        Returns:
            The tenant ID from the JWT, or None if not found
        """
        if not self.jwt_claim:
            return None
        
        # Try to get the user from the request
        user = getattr(request, "user", None)
        if not user:
            return None
        
        # Try to get the tenant ID from the JWT claims
        try:
            return getattr(user, self.jwt_claim, None)
        except:
            return None
    
    async def _validate_tenant(self, tenant_id: str) -> Optional[str]:
        """
        Validate that the tenant exists and is active.
        
        Args:
            tenant_id: The tenant ID to validate
            
        Returns:
            The validated tenant ID, or None if the tenant is not valid
        """
        try:
            tenant = await self.tenant_service.get_tenant(tenant_id)
            if tenant and tenant.status == "active":
                return tenant_id
        except:
            pass
        
        return None
    
    def _should_exclude(self, path: str) -> bool:
        """
        Check if the path should be excluded from tenant identification.
        
        Args:
            path: The request path
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        for exclude_path in self.exclude_paths:
            if exclude_path.endswith("*"):
                if path.startswith(exclude_path[:-1]):
                    return True
            elif path == exclude_path:
                return True
        
        return False


class TenantHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware that identifies the tenant from a header.
    
    This is a simplified version of TenantIdentificationMiddleware that only
    checks for a tenant ID in a header.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_service: TenantService,
        header_name: str = "X-Tenant-ID",
        default_tenant: Optional[str] = None,
        exclude_paths: List[str] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            tenant_service: Service for tenant operations
            header_name: Name of the header containing the tenant ID
            default_tenant: Default tenant ID to use if no tenant is identified
            exclude_paths: List of paths to exclude from tenant identification
        """
        super().__init__(app)
        self.tenant_service = tenant_service
        self.header_name = header_name
        self.default_tenant = default_tenant
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and set the tenant context.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Check if the path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get tenant ID from header
        tenant_id = request.headers.get(self.header_name)
        
        if tenant_id:
            # Validate the tenant
            try:
                tenant = await self.tenant_service.get_tenant(tenant_id)
                if tenant and tenant.status == "active":
                    # Set the tenant context
                    async with TenantContext(tenant_id):
                        # Store the tenant ID in the request state for easy access
                        request.state.tenant_id = tenant_id
                        
                        # Process the request
                        return await call_next(request)
            except:
                pass
        
        # No valid tenant identified, use default tenant if specified
        if self.default_tenant:
            async with TenantContext(self.default_tenant):
                # Store the tenant ID in the request state for easy access
                request.state.tenant_id = self.default_tenant
                
                # Process the request
                return await call_next(request)
        
        # No tenant identified and no default tenant, proceed without tenant context
        request.state.tenant_id = None
        return await call_next(request)


class TenantHostMiddleware(BaseHTTPMiddleware):
    """
    Middleware that identifies the tenant from the host.
    
    This middleware extracts the tenant ID from the hostname, either from a subdomain
    or by looking up the full domain in the tenant records.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_service: TenantService,
        subdomain_pattern: str = r"(.+)\.example\.com",
        default_tenant: Optional[str] = None,
        exclude_paths: List[str] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            tenant_service: Service for tenant operations
            subdomain_pattern: Regex pattern for extracting tenant ID from subdomain
            default_tenant: Default tenant ID to use if no tenant is identified
            exclude_paths: List of paths to exclude from tenant identification
        """
        super().__init__(app)
        self.tenant_service = tenant_service
        self.subdomain_pattern = subdomain_pattern
        self.default_tenant = default_tenant
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and set the tenant context.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Check if the path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get the host
        host = request.headers.get("host", "")
        if not host:
            # No host header, use default tenant if specified
            if self.default_tenant:
                async with TenantContext(self.default_tenant):
                    request.state.tenant_id = self.default_tenant
                    return await call_next(request)
            else:
                request.state.tenant_id = None
                return await call_next(request)
        
        # Try to extract tenant ID from subdomain
        tenant_id = None
        match = re.match(self.subdomain_pattern, host)
        if match and match.group(1):
            tenant_id = match.group(1)
        
        if not tenant_id:
            # Try to look up the full domain in tenant records
            try:
                tenant = await self.tenant_service.get_tenant_by_domain(host)
                if tenant and tenant.status == "active":
                    tenant_id = tenant.id
            except:
                pass
        
        if tenant_id:
            # Set the tenant context
            async with TenantContext(tenant_id):
                # Store the tenant ID in the request state for easy access
                request.state.tenant_id = tenant_id
                
                # Process the request
                return await call_next(request)
        
        # No tenant identified, use default tenant if specified
        if self.default_tenant:
            async with TenantContext(self.default_tenant):
                request.state.tenant_id = self.default_tenant
                return await call_next(request)
        
        # No tenant identified and no default tenant, proceed without tenant context
        request.state.tenant_id = None
        return await call_next(request)


class TenantPathMiddleware(BaseHTTPMiddleware):
    """
    Middleware that identifies the tenant from the URL path.
    
    This middleware extracts the tenant ID from the path prefix.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_service: TenantService,
        default_tenant: Optional[str] = None,
        exclude_paths: List[str] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            tenant_service: Service for tenant operations
            default_tenant: Default tenant ID to use if no tenant is identified
            exclude_paths: List of paths to exclude from tenant identification
        """
        super().__init__(app)
        self.tenant_service = tenant_service
        self.default_tenant = default_tenant
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and set the tenant context.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Check if the path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get the path
        path = request.url.path
        if path.startswith("/"):
            path = path[1:]
        
        # Extract tenant ID from path prefix
        parts = path.split("/")
        tenant_slug = parts[0] if parts and parts[0] else None
        
        if tenant_slug:
            # Try to look up the tenant by slug
            try:
                tenant = await self.tenant_service.get_tenant_by_slug(tenant_slug)
                if tenant and tenant.status == "active":
                    # Set the tenant context
                    async with TenantContext(tenant.id):
                        # Store the tenant ID in the request state for easy access
                        request.state.tenant_id = tenant.id
                        
                        # Rewrite the path to remove the tenant slug
                        path_without_tenant = "/" + "/".join(parts[1:])
                        request.scope["path"] = path_without_tenant
                        
                        # Process the request
                        return await call_next(request)
            except:
                pass
        
        # No tenant identified, use default tenant if specified
        if self.default_tenant:
            async with TenantContext(self.default_tenant):
                request.state.tenant_id = self.default_tenant
                return await call_next(request)
        
        # No tenant identified and no default tenant, proceed without tenant context
        request.state.tenant_id = None
        return await call_next(request)