# Tenant Identification Middleware and Utilities

This document describes the middleware components for tenant identification and utility functions for working with multi-tenant applications.

## Tenant Identification Middleware

The tenant identification middleware automatically identifies the current tenant from HTTP requests using various strategies.

### Core Middleware

The `TenantIdentificationMiddleware` class is the primary middleware component for tenant identification:

```python
class TenantIdentificationMiddleware(BaseHTTPMiddleware):```

"""
Middleware that identifies the current tenant.
``````

```
```

This middleware tries multiple strategies to identify the tenant for the current request.
"""
``````

```
```

def __init__(```

self,
app: ASGIApp,
tenant_service: TenantService,
header_name: str = "X-Tenant-ID",
subdomain_pattern: Optional[str] = None,
path_prefix: bool = False,
jwt_claim: Optional[str] = None,
default_tenant: Optional[str] = None,
exclude_paths: List[str] = None
```
):```

"""Initialize the middleware."""
super().__init__(app)
self.tenant_service = tenant_service
self.header_name = header_name
self.subdomain_pattern = subdomain_pattern
self.path_prefix = path_prefix
self.jwt_claim = jwt_claim
self.default_tenant = default_tenant
self.exclude_paths = exclude_paths or []
```
```
```

The middleware processes requests and sets the tenant context:

```python
async def dispatch(self, request: Request, call_next: Callable) -> Response:```

"""Process the request and set the tenant context."""
# Check if the path should be excluded
if self._should_exclude(request.url.path):```

return await call_next(request)
```
``````

```
```

# Try to identify the tenant
tenant_id = await self._identify_tenant(request)
``````

```
```

if tenant_id:```

# Set the tenant context
async with TenantContext(tenant_id):
    # Store the tenant ID in the request state for easy access
    request.state.tenant_id = tenant_id
    
    # Process the request
    return await call_next(request)
```
else:```

# No tenant identified, use default tenant if specified
if self.default_tenant:
    async with TenantContext(self.default_tenant):
        request.state.tenant_id = self.default_tenant
        return await call_next(request)
else:
    # No tenant identified and no default tenant, proceed without tenant context
    request.state.tenant_id = None
    return await call_next(request)
```
```
```

### Tenant Identification Strategies

The middleware supports multiple strategies for identifying the tenant:

```python
async def _identify_tenant(self, request: Request) -> Optional[str]:```

"""
Identify the tenant for the request.
``````

```
```

This method tries multiple strategies to identify the tenant.
"""
# Strategy 1: Header
tenant_id = self._extract_from_header(request)
if tenant_id:```

return await self._validate_tenant(tenant_id)
```
``````

```
```

# Strategy 2: Subdomain
tenant_id = self._extract_from_subdomain(request)
if tenant_id:```

return await self._validate_tenant(tenant_id)
```
``````

```
```

# Strategy 3: Path prefix
tenant_id = self._extract_from_path(request)
if tenant_id:```

return await self._validate_tenant(tenant_id)
```
``````

```
```

# Strategy 4: JWT claim
tenant_id = await self._extract_from_jwt(request)
if tenant_id:```

return await self._validate_tenant(tenant_id)
```
``````

```
```

# No tenant identified
return None
```
```

#### Header Strategy

Extract tenant ID from a request header:

```python
def _extract_from_header(self, request: Request) -> Optional[str]:```

"""Extract tenant ID from header."""
return request.headers.get(self.header_name)
```
```

#### Subdomain Strategy

Extract tenant ID from a subdomain:

```python
def _extract_from_subdomain(self, request: Request) -> Optional[str]:```

"""Extract tenant ID from subdomain."""
if not self.subdomain_pattern:```

return None
```
``````

```
```

host = request.headers.get("host", "")
if not host:```

return None
```
``````

```
```

# Match the pattern against the host
match = re.match(self.subdomain_pattern, host)
if match and match.group(1):```

return match.group(1)
```
``````

```
```

return None
```
```

#### Path Prefix Strategy

Extract tenant ID from the URL path:

```python
def _extract_from_path(self, request: Request) -> Optional[str]:```

"""Extract tenant ID from path."""
if not self.path_prefix:```

return None
```
``````

```
```

path = request.url.path
if path.startswith("/"):```

path = path[1:]
```
``````

```
```

parts = path.split("/")
if parts and parts[0]:```

return parts[0]
```
``````

```
```

return None
```
```

#### JWT Claim Strategy

Extract tenant ID from a JWT claim:

```python
async def _extract_from_jwt(self, request: Request) -> Optional[str]:```

"""Extract tenant ID from JWT."""
if not self.jwt_claim:```

return None
```
``````

```
```

# Try to get the user from the request
user = getattr(request, "user", None)
if not user:```

return None
```
``````

```
```

# Try to get the tenant ID from the JWT claims
try:```

return getattr(user, self.jwt_claim, None)
```
except:```

return None
```
```
```

### Specialized Middleware

For more focused use cases, specialized middleware classes are provided:

#### TenantHeaderMiddleware

A simplified middleware that only checks for a tenant ID in a header:

```python
class TenantHeaderMiddleware(BaseHTTPMiddleware):```

"""
Middleware that identifies the tenant from a header.
``````

```
```

This is a simplified version of TenantIdentificationMiddleware that only
checks for a tenant ID in a header.
"""
``````

```
```

def __init__(```

self,
app: ASGIApp,
tenant_service: TenantService,
header_name: str = "X-Tenant-ID",
default_tenant: Optional[str] = None,
exclude_paths: List[str] = None
```
):```

"""Initialize the middleware."""
super().__init__(app)
self.tenant_service = tenant_service
self.header_name = header_name
self.default_tenant = default_tenant
self.exclude_paths = exclude_paths or []
```
```
```

#### TenantHostMiddleware

Middleware that identifies the tenant from the host:

```python
class TenantHostMiddleware(BaseHTTPMiddleware):```

"""
Middleware that identifies the tenant from the host.
``````

```
```

This middleware extracts the tenant ID from the hostname, either from a subdomain
or by looking up the full domain in the tenant records.
"""
``````

```
```

def __init__(```

self,
app: ASGIApp,
tenant_service: TenantService,
subdomain_pattern: str = r"(.+)\.example\.com",
default_tenant: Optional[str] = None,
exclude_paths: List[str] = None
```
):```

"""Initialize the middleware."""
super().__init__(app)
self.tenant_service = tenant_service
self.subdomain_pattern = subdomain_pattern
self.default_tenant = default_tenant
self.exclude_paths = exclude_paths or []
```
```
```

#### TenantPathMiddleware

Middleware that identifies the tenant from the URL path:

```python
class TenantPathMiddleware(BaseHTTPMiddleware):```

"""
Middleware that identifies the tenant from the URL path.
``````

```
```

This middleware extracts the tenant ID from the path prefix.
"""
``````

```
```

def __init__(```

self,
app: ASGIApp,
tenant_service: TenantService,
default_tenant: Optional[str] = None,
exclude_paths: List[str] = None
```
):```

"""Initialize the middleware."""
super().__init__(app)
self.tenant_service = tenant_service
self.default_tenant = default_tenant
self.exclude_paths = exclude_paths or []
```
```
```

## Utility Functions

Utility functions provide convenient tools for working with multi-tenant applications.

### Tenant ID Extraction

The `get_tenant_id_from_request` function extracts the tenant ID from a request using multiple strategies:

```python
async def get_tenant_id_from_request(```

request: Request,
header_name: str = "X-Tenant-ID",
subdomain_pattern: Optional[str] = None,
path_prefix: bool = False
```
) -> Optional[str]:```

"""Extract tenant ID from request using multiple strategies."""
# Strategy 1: Check request state (if previously identified by middleware)
if hasattr(request.state, "tenant_id") and request.state.tenant_id:```

return request.state.tenant_id
```
``````

```
```

# Strategy 2: Header
tenant_id = request.headers.get(header_name)
if tenant_id:```

return tenant_id
```
``````

```
```

# Strategy 3: Subdomain
if subdomain_pattern:```

host = request.headers.get("host", "")
if host:
    match = re.match(subdomain_pattern, host)
    if match and match.group(1):
        return match.group(1)
```
``````

```
```

# Strategy 4: Path prefix
if path_prefix:```

path = request.url.path
if path.startswith("/"):
    path = path[1:]
    
parts = path.split("/")
if parts and parts[0]:
    return parts[0]
```
``````

```
```

# Strategy 5: User property (if set by auth middleware)
if hasattr(request, "user") and hasattr(request.user, "tenant_id"):```

return request.user.tenant_id
```
``````

```
```

return None
```
```

### Tenant Access Validation

The `validate_tenant_access` function validates that the current user has access to a tenant:

```python
async def validate_tenant_access(```

request: Request,
tenant_service: TenantService,
tenant_id: Optional[str] = None
```
) -> str:```

"""
Validate that the current user has access to the specified tenant.
``````

```
```

Returns the validated tenant ID or raises an HTTPException.
"""
# Get user ID from request (assuming authentication middleware sets it)
user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
``````

```
```

if not user_id:```

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required"
)
```
``````

```
```

# Get tenant ID (from parameter or request)
if not tenant_id:```

tenant_id = await get_tenant_id_from_request(request)
```
``````

```
```

if not tenant_id:```

raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Tenant ID is required"
)
```
``````

```
```

# Check if tenant exists and is active
tenant = await tenant_service.get_tenant(tenant_id)
if not tenant or tenant.status != "active":```

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Tenant {tenant_id} not found or inactive"
)
```
``````

```
```

# Check if user has access to tenant
has_access = await tenant_service.user_has_access_to_tenant(user_id, tenant_id)
if not has_access:```

raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail=f"User does not have access to tenant {tenant_id}"
)
```
``````

```
```

return tenant_id
```
```

### User Tenants

The `get_user_tenants` function gets all tenants that the current user has access to:

```python
async def get_user_tenants(```

request: Request,
tenant_service: TenantService
```
) -> List[Dict[str, Any]]:```

"""
Get all tenants that the current user has access to.
``````

```
```

Returns a list of tenants with access information.
"""
# Get user ID from request (assuming authentication middleware sets it)
user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
``````

```
```

if not user_id:```

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required"
)
```
``````

```
```

# Get all tenant associations for the user
associations = await tenant_service.get_user_tenants(user_id)
``````

```
```

# Get tenant details for each association
tenants = []
for association in associations:```

tenant = await tenant_service.get_tenant(association.tenant_id)
if tenant and tenant.status == "active":
    tenants.append({
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "roles": association.roles,
        "is_primary": association.is_primary
    })
```
``````

```
```

return tenants
```
```

### Tenant Admin Check

The `is_tenant_admin` function checks if the current user is an admin of a tenant:

```python
async def is_tenant_admin(```

request: Request,
tenant_service: TenantService,
tenant_id: Optional[str] = None
```,```

admin_role: str = "admin"
```
) -> bool:```

"""
Check if the current user is an admin of the specified tenant.
``````

```
```

Returns True if the user is an admin, False otherwise.
"""
# Get user ID from request (assuming authentication middleware sets it)
user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
``````

```
```

if not user_id:```

return False
```
``````

```
```

# Get tenant ID (from parameter or request)
if not tenant_id:```

tenant_id = await get_tenant_id_from_request(request)
```
``````

```
```

if not tenant_id:```

return False
```
``````

```
```

# Get the user-tenant association
association = await tenant_service.get_user_tenant(user_id, tenant_id)
if not association or association.status != "active":```

return False
```
``````

```
```

# Check if the user has the admin role
return admin_role in association.roles
```
```

## FastAPI Dependency Functions

Dependency functions provide a convenient way to validate tenant access in API routes.

### Tenant Required Dependency

The `tenant_required` dependency validates that the current user has access to a tenant:

```python
def tenant_required(```

tenant_service: TenantService = Depends(),
tenant_id_param: Optional[str] = None
```
):```

"""
Dependency for routes that require a valid tenant.
``````

```
```

This dependency validates that the current user has access to the specified tenant
and sets it as the current tenant context for the request.
"""
async def _get_and_validate_tenant(request: Request) -> str:```

# Get tenant ID from path parameter if specified
tenant_id = None
if tenant_id_param and tenant_id_param in request.path_params:
    tenant_id = request.path_params[tenant_id_param]
``````

```
```

# Validate tenant access
validated_tenant_id = await validate_tenant_access(
    request, tenant_service, tenant_id
)
``````

```
```

# Set the tenant ID in the request state for easy access
request.state.tenant_id = validated_tenant_id
``````

```
```

return validated_tenant_id
```
``````

```
```

return _get_and_validate_tenant
```
```

### Tenant Admin Required Dependency

The `tenant_admin_required` dependency validates that the current user is an admin of a tenant:

```python
def tenant_admin_required(```

tenant_service: TenantService = Depends(),
tenant_id_param: Optional[str] = None
```,```

admin_role: str = "admin"
```
):```

"""
Dependency for routes that require tenant admin privileges.
``````

```
```

This dependency validates that the current user is an admin of the specified tenant
and sets it as the current tenant context for the request.
"""
async def _get_and_validate_tenant_admin(request: Request) -> str:```

# Get tenant ID from path parameter if specified
tenant_id = None
if tenant_id_param and tenant_id_param in request.path_params:
    tenant_id = request.path_params[tenant_id_param]
``````

```
```

# Validate tenant access
validated_tenant_id = await validate_tenant_access(
    request, tenant_service, tenant_id
)
``````

```
```

# Check if the user is an admin
is_admin = await is_tenant_admin(
    request, tenant_service, validated_tenant_id, admin_role
)
``````

```
```

if not is_admin:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required"
    )
``````

```
```

# Set the tenant ID in the request state for easy access
request.state.tenant_id = validated_tenant_id
``````

```
```

return validated_tenant_id
```
``````

```
```

return _get_and_validate_tenant
```_admin
```

## Usage Examples

### Configuring Middleware

```python
from fastapi import FastAPI
from uno.core.multitenancy import (```

TenantIdentificationMiddleware, TenantService
```
)

app = FastAPI()

# Configure tenant identification middleware
app.add_middleware(```

TenantIdentificationMiddleware,
tenant_service=TenantService(session_factory),
header_name="X-Tenant-ID",
subdomain_pattern=r"(.+)\.example\.com",
path_prefix=True,
jwt_claim="tenant_id",
default_tenant=None,
exclude_paths=["/api/docs", "/api/auth"]
```
)
```

### Using Dependency Functions

```python
from fastapi import APIRouter, Depends
from uno.core.multitenancy import tenant_required, tenant_admin_required

router = APIRouter()

@router.get("/tenant/products")
async def list_products(```

tenant_id: str = Depends(tenant_required()),
product_repo: ProductRepository = Depends()
```
):```

# tenant_id is validated and tenant context is set
products = await product_repo.list()
return products
```

@router.post("/tenant/settings")
async def update_settings(```

settings: dict,
tenant_id: str = Depends(tenant_admin_required())
```
):```

# Only tenant admins can access this endpoint
# tenant_id is validated and tenant context is set
return {"message": "Settings updated", "tenant_id": tenant_id}
```

@router.get("/tenants/{tenant_id}/users")
async def list_tenant_users(```

tenant_id: str = Depends(tenant_admin_required(tenant_id_param="tenant_id"))
```
):```

# Uses tenant_id from path parameter
# Only tenant admins can access this endpoint
# tenant_id is validated and tenant context is set
return {"message": "Users list", "tenant_id": tenant_id}
```
```

### Utility Function Usage

```python
from fastapi import APIRouter, Depends, Request
from uno.core.multitenancy import (```

get_tenant_id_from_request, get_user_tenants, 
is_tenant_admin, TenantService
```
)

router = APIRouter()

@router.get("/me/current-tenant")
async def get_current_tenant(```

request: Request,
tenant_service: TenantService
``` = Depends()
):```

tenant_id = await get_tenant_id_from_request(request)
if not tenant_id:```

return {"message": "No tenant selected"}
```
``````

```
```

tenant = await tenant_service.get_tenant(tenant_id)
return {"tenant": tenant}
```

@router.get("/me/tenants")
async def list_my_tenants(```

request: Request,
tenant_service: TenantService
``` = Depends()
):```

tenants = await get_user_tenants(request, tenant_service)
return {"tenants": tenants}
```

@router.get("/me/is-admin")
async def check_admin_status(```

request: Request,
tenant_service: TenantService
``` = Depends()
):```

tenant_id = await get_tenant_id_from_request(request)
if not tenant_id:```

return {"is_admin": False}
```
``````

```
```

is_admin = await is_tenant_admin(request, tenant_service, tenant_id)
return {"is_admin": is_admin, "tenant_id": tenant_id}
```
```