# Authentication and Authorization Implementation Plan

This document outlines the plan for implementing authentication and authorization in the unified endpoint framework as part of Phase 3 of the architecture modernization.

## Current Status

The unified endpoint framework provides a solid foundation for API endpoints, but currently lacks integrated authentication and authorization capabilities. This plan addresses how to implement these critical security features in a way that integrates seamlessly with the existing framework.

## Authentication Components

### 1. Authentication Middleware

We will implement authentication middleware that:

- Validates authentication tokens (JWT, OAuth, etc.)
- Sets the authenticated user in the request context
- Handles authentication errors consistently
- Integrates with various authentication providers

```python
class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authenticating requests."""
    
    def __init__(
        self,
        app: FastAPI,
        auth_backend: AuthenticationBackend,
        exclude_paths: Optional[List[str]] = None,
    ):
        """Initialize the authentication middleware."""
        super().__init__(app)
        self.auth_backend = auth_backend
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and authenticate the user."""
        # Implementation details...
```

### 2. Authentication Backends

We will create a flexible authentication backend system:

```python
class AuthenticationBackend(Protocol):
    """Protocol for authentication backends."""
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """Authenticate a request and return a user if successful."""
        ...

class JWTAuthBackend(AuthenticationBackend):
    """JWT authentication backend."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        token_url: str = "/api/token",
        token_type: str = "Bearer",
    ):
        """Initialize the JWT authentication backend."""
        # Implementation details...
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """Authenticate a request using JWT."""
        # Implementation details...

class OAuth2AuthBackend(AuthenticationBackend):
    """OAuth2 authentication backend."""
    # Implementation details...
```

### 3. User Context

We will implement a user context system:

```python
class User(BaseModel):
    """User model for authentication."""
    
    id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UserContext:
    """Context for the current user."""
    
    def __init__(self, user: Optional[User] = None):
        """Initialize the user context."""
        self.user = user
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.user is not None
    
    def has_role(self, role: str) -> bool:
        """Check if the user has a specific role."""
        if not self.is_authenticated:
            return False
        return role in self.user.roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if the user has a specific permission."""
        if not self.is_authenticated:
            return False
        return permission in self.user.permissions
```

## Authorization Components

### 1. Permission System

We will implement a permission system:

```python
class Permission(str, Enum):
    """Permissions for API endpoints."""
    
    # Resource-level permissions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Special permissions
    ADMIN = "admin"
    EXPORT = "export"
    IMPORT = "import"

class PermissionDependency:
    """Dependency for checking permissions."""
    
    def __init__(self, permission: Union[str, Permission], resource: str):
        """Initialize the permission dependency."""
        self.permission = permission
        self.resource = resource
    
    async def __call__(self, request: Request) -> None:
        """Check if the user has the required permission."""
        # Implementation details...
```

### 2. Role-Based Access Control

We will implement a role-based access control system:

```python
class Role(BaseModel):
    """Role model for authorization."""
    
    name: str
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class RoleService:
    """Service for managing roles."""
    
    async def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        # Implementation details...
    
    async def get_roles_for_user(self, user_id: str) -> List[Role]:
        """Get roles for a user."""
        # Implementation details...
    
    async def get_permissions_for_user(self, user_id: str) -> List[str]:
        """Get permissions for a user."""
        # Implementation details...
```

### 3. Secure Endpoint Decorators

We will implement decorators for securing endpoints:

```python
def requires_auth(
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
):
    """Decorator for requiring authentication and authorization."""
    # Implementation details...

def requires_role(roles: Union[str, List[str]]):
    """Decorator for requiring specific roles."""
    # Implementation details...

def requires_permission(permissions: Union[str, List[str]], resource: str):
    """Decorator for requiring specific permissions on a resource."""
    # Implementation details...
```

## Integration with Unified Endpoint Framework

### 1. SecureBaseEndpoint

We will extend the BaseEndpoint class to support authentication and authorization:

```python
class SecureBaseEndpoint(BaseEndpoint):
    """Base class for secure API endpoints."""
    
    def __init__(
        self,
        *,
        auth_backend: AuthenticationBackend,
        require_auth: bool = True,
        required_roles: Optional[List[str]] = None,
        required_permissions: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize a new secure endpoint instance."""
        super().__init__(**kwargs)
        self.auth_backend = auth_backend
        self.require_auth = require_auth
        self.required_roles = required_roles or []
        self.required_permissions = required_permissions or []
        
        # Add authentication and authorization dependencies
        if self.require_auth:
            self.router.dependencies.append(Depends(get_user_context))
            
            if self.required_roles:
                self.router.dependencies.append(
                    Depends(RequireRoles(self.required_roles))
                )
                
            if self.required_permissions:
                self.router.dependencies.append(
                    Depends(RequirePermissions(self.required_permissions))
                )
```

### 2. SecureCrudEndpoint

We will extend the CrudEndpoint class to support authentication and authorization:

```python
class SecureCrudEndpoint(CrudEndpoint):
    """Base class for secure CRUD endpoints."""
    
    def __init__(
        self,
        *,
        auth_backend: AuthenticationBackend,
        create_permissions: Optional[List[str]] = None,
        read_permissions: Optional[List[str]] = None,
        update_permissions: Optional[List[str]] = None,
        delete_permissions: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize a new secure CRUD endpoint instance."""
        super().__init__(**kwargs)
        self.auth_backend = auth_backend
        self.create_permissions = create_permissions or []
        self.read_permissions = read_permissions or []
        self.update_permissions = update_permissions or []
        self.delete_permissions = delete_permissions or []
        
        # Override route registration to add permissions
        self._register_routes()
    
    def _register_create_route(self) -> None:
        """Register the route for creating a new entity with permissions."""
        # Override implementation to add permission checks
```

### 3. SecureCqrsEndpoint

We will extend the CqrsEndpoint class to support authentication and authorization:

```python
class SecureCqrsEndpoint(CqrsEndpoint):
    """Endpoint that implements the CQRS pattern with security."""
    
    def __init__(
        self,
        *,
        auth_backend: AuthenticationBackend,
        query_permissions: Optional[Dict[str, List[str]]] = None,
        command_permissions: Optional[Dict[str, List[str]]] = None,
        **kwargs,
    ):
        """Initialize a new secure CQRS endpoint instance."""
        super().__init__(**kwargs)
        self.auth_backend = auth_backend
        self.query_permissions = query_permissions or {}
        self.command_permissions = command_permissions or {}
        
        # Override handler registration to add permissions
        self._register_handlers()
```

## FastAPI Integration

### 1. Authentication Middleware Setup

We will add utilities for setting up authentication with FastAPI:

```python
def setup_auth(
    app: FastAPI,
    auth_backend: AuthenticationBackend,
    exclude_paths: Optional[List[str]] = None,
) -> None:
    """Set up authentication for a FastAPI application."""
    app.add_middleware(
        AuthenticationMiddleware,
        auth_backend=auth_backend,
        exclude_paths=exclude_paths,
    )
    
    # Register authentication error handlers
    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        """Handle authentication errors."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": {"code": "UNAUTHORIZED", "message": str(exc)}},
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 2. Authorization Dependency

We will add utilities for authorization dependencies:

```python
def get_user_context(request: Request) -> UserContext:
    """Get the user context from the request."""
    return request.state.user_context

class RequireRoles:
    """Dependency for requiring specific roles."""
    
    def __init__(self, roles: List[str]):
        """Initialize the role requirement."""
        self.roles = roles
    
    async def __call__(self, user_context: UserContext = Depends(get_user_context)) -> None:
        """Check if the user has any of the required roles."""
        if not user_context.is_authenticated:
            raise AuthenticationError("Authentication required")
        
        for role in self.roles:
            if user_context.has_role(role):
                return
                
        raise AuthorizationError(f"Required role not found: {', '.join(self.roles)}")

class RequirePermissions:
    """Dependency for requiring specific permissions."""
    
    def __init__(self, permissions: List[str]):
        """Initialize the permission requirement."""
        self.permissions = permissions
    
    async def __call__(self, user_context: UserContext = Depends(get_user_context)) -> None:
        """Check if the user has all of the required permissions."""
        if not user_context.is_authenticated:
            raise AuthenticationError("Authentication required")
        
        for permission in self.permissions:
            if not user_context.has_permission(permission):
                raise AuthorizationError(f"Required permission not found: {permission}")
```

## Example Usage

### 1. Basic Authentication

```python
from fastapi import FastAPI
from uno.api.endpoint import create_api
from uno.api.endpoint.auth import JWTAuthBackend, setup_auth

# Create the API
app = create_api(title="Secure API", description="API with authentication")

# Set up authentication
auth_backend = JWTAuthBackend(
    secret_key="your-secret-key",
    algorithm="HS256",
)
setup_auth(app, auth_backend)

# Create secure endpoints
# ...
```

### 2. Secure CRUD Endpoint

```python
from fastapi import FastAPI
from uno.api.endpoint.auth import JWTAuthBackend, SecureCrudEndpoint

# Create the API
app = FastAPI()

# Create secure endpoint
endpoint = SecureCrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    tags=["Products"],
    path="/api/products",
    auth_backend=auth_backend,
    create_permissions=["products:create"],
    read_permissions=["products:read"],
    update_permissions=["products:update"],
    delete_permissions=["products:delete"],
)
endpoint.register(app)
```

### 3. Secure CQRS Endpoint

```python
from fastapi import FastAPI
from uno.api.endpoint.auth import JWTAuthBackend, SecureCqrsEndpoint

# Create the API
app = FastAPI()

# Create secure endpoint
endpoint = SecureCqrsEndpoint(
    queries=[search_query],
    commands=[create_command],
    tags=["Products"],
    base_path="/api/products",
    auth_backend=auth_backend,
    query_permissions={
        "search": ["products:read"],
    },
    command_permissions={
        "create": ["products:create"],
    },
)
endpoint.register(app)
```

## Implementation Tasks

### 1. Authentication Framework

- [ ] Implement AuthenticationBackend protocol
- [ ] Implement JWTAuthBackend
- [ ] Implement OAuth2AuthBackend
- [ ] Implement User and UserContext classes
- [ ] Implement AuthenticationMiddleware

### 2. Authorization Framework

- [ ] Implement Permission enum
- [ ] Implement Role model and RoleService
- [ ] Implement authorization dependencies
- [ ] Implement authorization decorators

### 3. Secure Endpoint Classes

- [ ] Implement SecureBaseEndpoint
- [ ] Implement SecureCrudEndpoint
- [ ] Implement SecureCqrsEndpoint

### 4. Integration Utilities

- [ ] Implement setup_auth function
- [ ] Implement authentication error handlers
- [ ] Update create_api to support authentication

### 5. Documentation and Examples

- [ ] Update API documentation with authentication details
- [ ] Create authentication and authorization examples
- [ ] Update developer guide with security best practices

## Timeline

- Days 1-2: Authentication Framework
- Days 3-4: Authorization Framework
- Days 5-6: Secure Endpoint Classes
- Day 7: Integration Utilities
- Day 8: Documentation and Examples
- Days 9-10: Testing and Refinement

## Conclusion

This plan outlines a comprehensive approach to implementing authentication and authorization in the unified endpoint framework. By following this plan, we will create a secure, flexible, and user-friendly system that integrates seamlessly with the existing framework while providing robust security features.