# Authentication and Authorization

This guide explains how to use the authentication and authorization features of the unified endpoint framework.

## Authentication Framework

The unified endpoint framework provides a flexible authentication framework that integrates with various authentication providers, including JWT and OAuth2.

### Authentication Components

The main components of the authentication framework are:

1. **Authentication Protocols**: Defines the interface for authentication backends.
2. **Authentication Backends**: Implements authentication for specific providers (JWT, OAuth2, etc.).
3. **User and UserContext**: Represents the authenticated user and provides access to user information.
4. **Authentication Middleware**: Authenticates requests and sets the user context.
5. **Secure Endpoint Classes**: Extends the standard endpoint classes with authentication and authorization support.

## Setting Up Authentication

### 1. Create an Authentication Backend

First, create an authentication backend that implements the `AuthenticationBackend` protocol:

```python
from uno.api.endpoint.auth import JWTAuthBackend

# Create JWT authentication backend
auth_backend = JWTAuthBackend(
    secret_key="your-secret-key-here",  # Use a secure secret key in production
    algorithm="HS256",
    token_url="/api/token",
)
```

### 2. Set Up Authentication Middleware

Next, set up the authentication middleware:

```python
from uno.api.endpoint.auth import setup_auth

# Set up authentication
setup_auth(
    app=app,
    auth_backend=auth_backend,
    exclude_paths=["/api/token", "/docs", "/openapi.json"],  # Paths to exclude from authentication
)
```

### 3. Create a Token Endpoint

Create an endpoint for generating authentication tokens:

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from uno.api.endpoint.auth import User

class TokenRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(..., description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

@app.post("/api/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """Get an access token."""
    # Validate credentials
    if not validate_credentials(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"}},
        )
    
    # Create a user
    user = User(
        id="user-id",
        username=request.username,
        roles=["user"],
        permissions=["products:read"],
    )
    
    # Create a token
    token = auth_backend.create_token(user, expires_in=3600)
    
    # Return the token response
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
    }
```

## Using Secure Endpoints

### Secure CRUD Endpoint

The `SecureCrudEndpoint` extends `CrudEndpoint` to add authentication and authorization support:

```python
from uno.api.endpoint.auth import SecureCrudEndpoint

# Create secure CRUD endpoint
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

This endpoint requires different permissions for different operations:
- Create: requires the `products:create` permission
- Read: requires the `products:read` permission
- Update: requires the `products:update` permission
- Delete: requires the `products:delete` permission

### Secure CQRS Endpoint

The `SecureCqrsEndpoint` extends `CqrsEndpoint` to add authentication and authorization support:

```python
from uno.api.endpoint.auth import SecureCqrsEndpoint
from uno.api.endpoint import QueryHandler, CommandHandler

# Create query handler
search_query = QueryHandler(
    service=search_service,
    response_model=List[ProductResponse],
    query_model=ProductSearchQuery,
    path="/search",
    method="get",
)

# Create command handler
create_command = CommandHandler(
    service=create_service,
    command_model=CreateProductCommand,
    response_model=ProductCreatedResponse,
    path="",
    method="post",
)

# Create secure CQRS endpoint
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
        "default": ["products:create"],
    },
)
endpoint.register(app)
```

This endpoint requires different permissions for different handlers:
- Search query: requires the `products:read` permission
- Create command: requires the `products:create` permission

## Using Authentication Dependencies

### Get User Context

You can get the current user context from a request:

```python
from fastapi import Depends
from uno.api.endpoint.auth import get_user_context, UserContext

@app.get("/api/me")
async def get_current_user(user_context: UserContext = Depends(get_user_context)):
    """Get information about the current user."""
    return {
        "id": user_context.user.id,
        "username": user_context.user.username,
        "roles": user_context.user.roles,
        "permissions": user_context.user.permissions,
    }
```

### Require Roles

You can require specific roles for an endpoint:

```python
from uno.api.endpoint.auth import requires_auth

@app.get("/api/admin", dependencies=[Depends(requires_auth(roles=["admin"]))])
async def admin_only():
    """Admin-only endpoint."""
    return {"message": "You have admin access!"}
```

### Require Permissions

You can require specific permissions for an endpoint:

```python
from uno.api.endpoint.auth import requires_auth

@app.get("/api/reports", dependencies=[Depends(requires_auth(permissions=["reports:read"]))])
async def read_reports():
    """Reports endpoint."""
    return {"message": "You can read reports!"}
```

## JWT Authentication

The JWT authentication backend provides token-based authentication:

### Creating Tokens

You can create JWT tokens for users:

```python
from uno.api.endpoint.auth import JWTAuthBackend, User

# Create JWT authentication backend
auth_backend = JWTAuthBackend(
    secret_key="your-secret-key-here",
    algorithm="HS256",
)

# Create a user
user = User(
    id="user-id",
    username="username",
    roles=["user"],
    permissions=["products:read"],
)

# Create a token
token = auth_backend.create_token(user, expires_in=3600)
```

### Token Claims

The JWT token includes the following claims:
- `sub`: User ID
- `username`: Username
- `email`: User email (if available)
- `roles`: User roles
- `permissions`: User permissions
- `iat`: Token issued at timestamp
- `exp`: Token expiration timestamp

### Token Validation

Tokens are validated by the authentication middleware during requests.

## Permission System

The permission system uses string-based permissions that can be checked during requests:

### Permission Format

Permissions are typically formatted as `resource:action`, such as:
- `products:create`
- `products:read`
- `products:update`
- `products:delete`
- `reports:export`
- `admin:access`

### Checking Permissions

You can check permissions in several ways:

1. Using the `SecureCrudEndpoint` with permission requirements
2. Using the `SecureCqrsEndpoint` with permission mappings
3. Using the `requires_auth` dependency with permission requirements
4. Manually checking permissions with the `UserContext`

```python
# Manual permission check
if user_context.has_permission("products:create"):
    # Allow product creation
```

## Role System

The role system uses string-based roles that can be checked during requests:

### Checking Roles

You can check roles in several ways:

1. Using the `requires_auth` dependency with role requirements
2. Manually checking roles with the `UserContext`

```python
# Manual role check
if user_context.has_role("admin"):
    # Allow admin access
```

## Implementing Custom Authentication

You can implement custom authentication by creating a class that implements the `AuthenticationBackend` protocol:

```python
from typing import Optional
from fastapi import Request, Response
from uno.api.endpoint.auth import AuthenticationBackend, User

class CustomAuthBackend(AuthenticationBackend):
    """Custom authentication backend."""
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """Authenticate a request and return a user if successful."""
        # Implement custom authentication logic
        # ...
        
        # Return a user if authentication is successful, None otherwise
        return user
    
    async def on_error(self, request: Request, exc: Exception) -> Response:
        """Handle an authentication error."""
        # Implement custom error handling
        # ...
        
        # Return a response
        return response
```

## Best Practices

### 1. Use Environment Variables for Secrets

Store secret keys in environment variables:

```python
import os
from uno.api.endpoint.auth import JWTAuthBackend

# Create JWT authentication backend with secret from environment
auth_backend = JWTAuthBackend(
    secret_key=os.environ.get("JWT_SECRET_KEY"),
    algorithm="HS256",
)
```

### 2. Use HTTPS in Production

Always use HTTPS in production to protect authentication tokens and sensitive data.

### 3. Set Appropriate Token Expirations

Set appropriate token expiration times based on security requirements:

```python
# Short-lived token (1 hour)
token = auth_backend.create_token(user, expires_in=3600)

# Longer-lived token (1 day)
token = auth_backend.create_token(user, expires_in=86400)
```

### 4. Use Granular Permissions

Define granular permissions for different operations:

```python
# User with granular permissions
user = User(
    id="user-id",
    username="username",
    roles=["user"],
    permissions=[
        "products:read",
        "products:create",
        "reports:read",
    ],
)
```

### 5. Implement Refresh Tokens

For long-lived sessions, implement refresh tokens instead of extending access token lifetimes.

## Conclusion

The authentication and authorization system in the unified endpoint framework provides a flexible and secure way to protect your API endpoints. By using the secure endpoint classes and authentication dependencies, you can easily implement role-based and permission-based access control for your API.