"""
Authentication and authorization example for UnoEndpoint-based APIs.

This module demonstrates how to implement various authentication and authorization
mechanisms for UnoEndpoint-based APIs, including:

1. JWT authentication
2. Role-based access control (RBAC)
3. Permission-based authorization
4. API key authentication
5. OAuth2 integration
6. Custom security middleware

These examples show how to secure your APIs while maintaining clean code and separation
of concerns.
"""

import os
import time
import json
import enum
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Type, Callable, Set, Annotated

from fastapi import FastAPI, status, APIRouter, HTTPException, Response, Request, Body, Depends, Query, Header, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ConfigDict, create_model, computed_field, EmailStr

import jwt
from passlib.context import CryptContext

from uno.api.endpoint import UnoEndpoint, UnoRouter
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column


# Set up logging
logger = logging.getLogger(__name__)


# ===== AUTHENTICATION MODELS =====

class User(BaseModel):
    """User model for authentication examples."""
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: bool = False
    # In a real application, store hashed passwords only
    hashed_password: str
    # User role and permissions
    role: str
    permissions: List[str] = []
    # API key (for API key authentication)
    api_key: Optional[str] = None
    # External OAuth2 identifiers
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None


class UserInDB(User):
    """Internal user database model with additional fields."""
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ===== AUTHENTICATION UTILITIES =====

# JWT Configuration
JWT_SECRET_KEY = "example_secret_key"  # In production, use a secure key from environment variables
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key")

# HTTP Bearer auth scheme for custom handling
http_bearer = HTTPBearer()


def get_password_hash(password: str) -> str:
    """Create password hash from plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain text password matches the hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token with expiration."""
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create and return the token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


# ===== MOCK USER DATABASE =====

# This would typically be a database, but for this example, we'll use an in-memory dictionary
USERS_DB = {}


def initialize_mock_users():
    """Initialize the mock user database with some example users."""
    # Create some example users with different roles and permissions
    users = [
        {
            "id": "user1",
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "hashed_password": get_password_hash("adminpassword"),
            "role": "admin",
            "permissions": ["read", "write", "delete", "manage_users"],
            "api_key": generate_api_key(),
            "oauth_provider": None,
            "oauth_id": None,
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "user2",
            "username": "editor",
            "email": "editor@example.com",
            "full_name": "Editor User",
            "hashed_password": get_password_hash("editorpassword"),
            "role": "editor",
            "permissions": ["read", "write"],
            "api_key": generate_api_key(),
            "oauth_provider": None,
            "oauth_id": None,
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "user3",
            "username": "viewer",
            "email": "viewer@example.com",
            "full_name": "Viewer User",
            "hashed_password": get_password_hash("viewerpassword"),
            "role": "viewer",
            "permissions": ["read"],
            "api_key": generate_api_key(),
            "oauth_provider": None,
            "oauth_id": None,
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "user4",
            "username": "oauthuser",
            "email": "oauth@example.com",
            "full_name": "OAuth User",
            "hashed_password": "",  # No password for OAuth users
            "role": "user",
            "permissions": ["read"],
            "api_key": None,
            "oauth_provider": "google",
            "oauth_id": "123456789",
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Add users to the database
    for user in users:
        USERS_DB[user["username"]] = UserInDB(**user)


# Call this to initialize the database
initialize_mock_users()


# ===== USER AUTHENTICATION FUNCTIONS =====

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get a user from the database by username."""
    return USERS_DB.get(username)


def get_user_by_api_key(api_key: str) -> Optional[UserInDB]:
    """Get a user from the database by API key."""
    for user in USERS_DB.values():
        if user.api_key == api_key:
            return user
    return None


def get_user_by_oauth(provider: str, oauth_id: str) -> Optional[UserInDB]:
    """Get a user from the database by OAuth provider and ID."""
    for user in USERS_DB.values():
        if user.oauth_provider == provider and user.oauth_id == oauth_id:
            return user
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with username and password."""
    user = get_user_by_username(username)
    if not user:
        return None
    
    # OAuth users can't log in with password
    if user.oauth_provider:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# ===== FASTAPI DEPENDENCY FUNCTIONS =====

async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from a JWT token."""
    # Decode the token
    payload = decode_jwt_token(token)
    
    # Extract username
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user from database
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_user_from_api_key(api_key: str = Depends(api_key_header)) -> User:
    """Get the current user from an API key."""
    # Get user from database
    user = get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Check if user is disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_user_from_custom_header(authorization: HTTPAuthorizationCredentials = Security(http_bearer)) -> User:
    """Get the current user from a custom Authorization header."""
    # Extract the token
    token = authorization.credentials
    
    # Decode the token
    payload = decode_jwt_token(token)
    
    # Extract username
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user from database
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user_from_token)) -> User:
    """Get the current active user (wrapper around get_current_user)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ===== PERMISSION AND ROLE DEPENDENCIES =====

def has_role(required_role: str):
    """Dependency factory for role-based access control."""
    async def role_dependency(current_user: User = Depends(get_current_user_from_token)) -> User:
        # Admin role has access to everything
        if current_user.role == "admin":
            return current_user
        
        # Check if the user has the required role
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return current_user
    
    return role_dependency


def has_permission(required_permission: str):
    """Dependency factory for permission-based access control."""
    async def permission_dependency(current_user: User = Depends(get_current_user_from_token)) -> User:
        # Check if the user has the required permission
        if required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        
        return current_user
    
    return permission_dependency


def has_any_permission(required_permissions: List[str]):
    """Dependency factory for permission-based access control (any permission)."""
    async def permission_dependency(current_user: User = Depends(get_current_user_from_token)) -> User:
        # Check if the user has any of the required permissions
        if not any(perm in current_user.permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Any of these permissions required: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return permission_dependency


def has_all_permissions(required_permissions: List[str]):
    """Dependency factory for permission-based access control (all permissions)."""
    async def permission_dependency(current_user: User = Depends(get_current_user_from_token)) -> User:
        # Check if the user has all of the required permissions
        if not all(perm in current_user.permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of these permissions required: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return permission_dependency


# ===== AUTHENTICATION RESPONSES =====

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    username: str
    role: str


class TokenData(BaseModel):
    """Token data model for JWT claims."""
    username: Optional[str] = None
    scopes: List[str] = []


# ===== AUTHENTICATION ROUTERS =====

class SecureRouter(UnoRouter):
    """Base router for secure endpoints with authentication requirements."""
    
    # List of possible dependencies to use for authentication
    # Concrete subclasses should override this to select the desired dependency
    auth_dependency: Callable = get_current_user_from_token


class RBACRouter(SecureRouter):
    """Router for endpoints with role-based access control."""
    
    # Required role for this endpoint
    required_role: str
    
    def __init__(self, *args, **kwargs):
        # Set up role-based dependency
        self.auth_dependency = has_role(self.required_role)
        super().__init__(*args, **kwargs)


class PermissionRouter(SecureRouter):
    """Router for endpoints with permission-based access control."""
    
    # Required permission for this endpoint
    required_permission: str
    
    def __init__(self, *args, **kwargs):
        # Set up permission-based dependency
        self.auth_dependency = has_permission(self.required_permission)
        super().__init__(*args, **kwargs)


class APIKeyRouter(SecureRouter):
    """Router for endpoints with API key authentication."""
    
    def __init__(self, *args, **kwargs):
        # Use API key authentication
        self.auth_dependency = get_current_user_from_api_key
        super().__init__(*args, **kwargs)


# ===== EXAMPLE RESOURCE MODELS =====

class ResourceModel(UnoModel):
    """Example resource model for demonstrating authentication."""
    
    __tablename__ = "resources"
    
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    owner_id: Mapped[str] = mapped_column(nullable=False)
    is_public: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== CUSTOM AUTHENTICATED ROUTERS =====

class SecureListRouter(SecureRouter):
    """Secure router for listing resources with authentication."""
    
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"List {self.model.display_name_plural} (Authenticated)"
    
    @property
    def description(self) -> str:
        return f"""
            List {self.model.display_name_plural} with authentication.
            Only resources owned by the current user or marked as public will be returned.
        """
    
    def endpoint_factory(self):
        from typing import List, Dict, Any
        
        async def endpoint(
            self,
            current_user: User = Depends(self.auth_dependency)
        ) -> List[Dict[str, Any]]:
            # Get all resources
            all_resources = await self.model.filter()
            
            # Filter to only show resources owned by the user or public resources
            # Admin users can see all resources
            if current_user.role == "admin":
                filtered_resources = all_resources
            else:
                filtered_resources = [
                    r for r in all_resources 
                    if r.owner_id == current_user.id or r.is_public
                ]
            
            # Return the resources
            return [r.dict() for r in filtered_resources]
        
        endpoint.__annotations__["return"] = List[Dict[str, Any]]
        setattr(self.__class__, "endpoint", endpoint)


class SecureCreateRouter(SecureRouter):
    """Secure router for creating resources with authentication."""
    
    path_suffix: str = ""
    method: str = "POST"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Create {self.model.display_name} (Authenticated)"
    
    @property
    def description(self) -> str:
        return f"""
            Create a new {self.model.display_name} with authentication.
            The current user will be set as the owner of the resource.
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any
        
        async def endpoint(
            self,
            resource_data: Dict[str, Any],
            current_user: User = Depends(self.auth_dependency)
        ) -> Dict[str, Any]:
            # Set the owner to the current user
            resource_data["owner_id"] = current_user.id
            
            # Create the resource
            resource = self.model(**resource_data)
            await resource.save()
            
            # Return the created resource
            return resource.dict()
        
        endpoint.__annotations__["resource_data"] = Dict[str, Any]
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class SecureUpdateRouter(PermissionRouter):
    """Secure router for updating resources with permission checks."""
    
    path_suffix: str = "/{id}"
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: List[str] = None
    required_permission: str = "write"
    
    @property
    def summary(self) -> str:
        return f"Update {self.model.display_name} (Authenticated + Permission)"
    
    @property
    def description(self) -> str:
        return f"""
            Update a {self.model.display_name} with authentication and permission checks.
            Users can only update resources they own, unless they are administrators.
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any
        from fastapi import Path
        
        async def endpoint(
            self,
            id: str = Path(..., description="Resource ID"),
            resource_data: Dict[str, Any] = Body(...),
            current_user: User = Depends(self.auth_dependency)
        ) -> Dict[str, Any]:
            # Get the resource
            resource = await self.model.get(id)
            if not resource:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resource not found: {id}"
                )
            
            # Check ownership (admins can update any resource)
            if resource.owner_id != current_user.id and current_user.role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="You can only update resources you own"
                )
            
            # Update the resource
            for key, value in resource_data.items():
                # Don't allow changing the owner
                if key != "owner_id" and key != "id":
                    setattr(resource, key, value)
            
            # Save the updated resource
            await resource.save()
            
            # Return the updated resource
            return resource.dict()
        
        endpoint.__annotations__["resource_data"] = Dict[str, Any]
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class SecureDeleteRouter(RBACRouter):
    """Secure router for deleting resources with role checks."""
    
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: List[str] = None
    required_role: str = "admin"  # Only admins can delete resources
    
    @property
    def summary(self) -> str:
        return f"Delete {self.model.display_name} (Authenticated + Role)"
    
    @property
    def description(self) -> str:
        return f"""
            Delete a {self.model.display_name} with authentication and role checks.
            Only administrators can delete resources.
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any
        from fastapi import Path
        
        async def endpoint(
            self,
            id: str = Path(..., description="Resource ID"),
            current_user: User = Depends(self.auth_dependency)
        ) -> Dict[str, Any]:
            # Get the resource
            resource = await self.model.get(id)
            if not resource:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resource not found: {id}"
                )
            
            # Delete the resource
            await resource.delete()
            
            # Return success
            return {"id": id, "deleted": True}
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class APIKeyListRouter(APIKeyRouter):
    """Router for listing resources with API key authentication."""
    
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api/key"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"List {self.model.display_name_plural} (API Key)"
    
    @property
    def description(self) -> str:
        return f"""
            List {self.model.display_name_plural} using API key authentication.
            Provide your API key in the X-API-Key header.
        """
    
    def endpoint_factory(self):
        from typing import List, Dict, Any
        
        async def endpoint(
            self,
            current_user: User = Depends(self.auth_dependency)
        ) -> List[Dict[str, Any]]:
            # Get all resources
            all_resources = await self.model.filter()
            
            # Filter to only show resources owned by the user or public resources
            # Admin users can see all resources
            if current_user.role == "admin":
                filtered_resources = all_resources
            else:
                filtered_resources = [
                    r for r in all_resources 
                    if r.owner_id == current_user.id or r.is_public
                ]
            
            # Return the resources
            return [r.dict() for r in filtered_resources]
        
        endpoint.__annotations__["return"] = List[Dict[str, Any]]
        setattr(self.__class__, "endpoint", endpoint)


# ===== SECURE ENDPOINTS =====

class SecureListEndpoint(UnoEndpoint):
    """Secure endpoint for listing resources."""
    
    router: UnoRouter = SecureListRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class SecureCreateEndpoint(UnoEndpoint):
    """Secure endpoint for creating resources."""
    
    router: UnoRouter = SecureCreateRouter
    body_model: Optional[str] = "edit_schema"
    response_model: Optional[str] = "view_schema"


class SecureUpdateEndpoint(UnoEndpoint):
    """Secure endpoint for updating resources."""
    
    router: UnoRouter = SecureUpdateRouter
    body_model: Optional[str] = "edit_schema"
    response_model: Optional[str] = "view_schema"


class SecureDeleteEndpoint(UnoEndpoint):
    """Secure endpoint for deleting resources."""
    
    router: UnoRouter = SecureDeleteRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class APIKeyListEndpoint(UnoEndpoint):
    """Endpoint for listing resources with API key authentication."""
    
    router: UnoRouter = APIKeyListRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


# ===== APPLICATION SETUP =====

def create_app():
    """Create a FastAPI application with authentication and authorization."""
    # Create the app
    app = FastAPI(title="Authentication Example", description="API with authentication and authorization")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this to your frontend domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create the endpoint factory
    factory = UnoEndpointFactory()
    
    # Register secure endpoint types
    factory.register_endpoint_type("SecureList", SecureListEndpoint)
    factory.register_endpoint_type("SecureCreate", SecureCreateEndpoint)
    factory.register_endpoint_type("SecureUpdate", SecureUpdateEndpoint)
    factory.register_endpoint_type("SecureDelete", SecureDeleteEndpoint)
    factory.register_endpoint_type("APIKeyList", APIKeyListEndpoint)
    
    # Create secure endpoints
    secure_endpoints = factory.create_endpoints(
        app=app,
        model_obj=ResourceModel,
        endpoints=["SecureList", "SecureCreate", "SecureUpdate", "SecureDelete", "APIKeyList"],
        endpoint_tags=["Secure Resources"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Add authentication endpoints
    
    @app.post("/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Get an access token for authentication.
        
        Provide your username and password to get a JWT token that can be used
        to authenticate with the API.
        """
        # Authenticate user
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create token expiration
        access_token_expires = timedelta(minutes=JWT_EXPIRATION_MINUTES)
        
        # Create the JWT token
        access_token = create_jwt_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Update last login time
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # Return the token and user information
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_MINUTES * 60,
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
    
    @app.get("/users/me", response_model=User)
    async def read_users_me(current_user: User = Depends(get_current_active_user)):
        """
        Get information about the currently authenticated user.
        
        This endpoint requires authentication with a valid JWT token.
        """
        return current_user
    
    @app.get("/users/me/items")
    async def read_own_items(
        current_user: User = Depends(get_current_active_user)
    ):
        """
        Get items belonging to the currently authenticated user.
        
        This endpoint requires authentication with a valid JWT token.
        """
        # In a real application, you would query the database for the user's items
        return {"items": [], "owner": current_user.username}
    
    @app.get("/admin", dependencies=[Depends(has_role("admin"))])
    async def admin_only():
        """
        Admin-only endpoint.
        
        This endpoint requires the user to have the 'admin' role.
        """
        return {"message": "You are an admin!"}
    
    @app.get("/require-permission", dependencies=[Depends(has_permission("manage_users"))])
    async def require_permission():
        """
        Endpoint requiring a specific permission.
        
        This endpoint requires the user to have the 'manage_users' permission.
        """
        return {"message": "You have the required permission!"}
    
    @app.get("/require-any-permission", dependencies=[Depends(has_any_permission(["read", "write"]))])
    async def require_any_permission():
        """
        Endpoint requiring any of several permissions.
        
        This endpoint requires the user to have either the 'read' or 'write' permission.
        """
        return {"message": "You have at least one of the required permissions!"}
    
    @app.get("/require-all-permissions", dependencies=[Depends(has_all_permissions(["read", "write"]))])
    async def require_all_permissions():
        """
        Endpoint requiring all of several permissions.
        
        This endpoint requires the user to have both the 'read' and 'write' permissions.
        """
        return {"message": "You have all required permissions!"}
    
    @app.get("/api-key-only")
    async def api_key_only(current_user: User = Depends(get_current_user_from_api_key)):
        """
        Endpoint requiring API key authentication.
        
        This endpoint requires authentication with a valid API key.
        """
        return {
            "message": "Valid API key",
            "user": current_user.username,
            "role": current_user.role
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Create the app
    app = create_app()
    
    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8000)