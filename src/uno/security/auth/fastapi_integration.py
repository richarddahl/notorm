"""
FastAPI integration for Uno authentication.

This module provides utilities for integrating Uno's authentication system
with FastAPI applications, including JWT authentication middleware and dependencies.
"""

from typing import Optional, Callable, List, Dict, Any, Type, Union, TypeVar
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from uno.security.config import SecurityConfig, AuthenticationConfig
from uno.security.auth.jwt import (
    JWTAuth, JWTConfig, JWTBearer, JWTAuthMiddleware, TokenData,
    get_current_user_id, get_current_user_roles, get_current_tenant_id,
    require_role, require_any_role, require_all_roles
)

T = TypeVar("T")


def configure_jwt_auth(
    app: FastAPI,
    config: Union[SecurityConfig, AuthenticationConfig, JWTConfig],
    user_model: Optional[Type] = None,
    user_loader: Optional[Callable] = None,
    on_auth_success: Optional[Callable] = None,
    on_auth_failure: Optional[Callable] = None,
    exclude_paths: Optional[List[str]] = None
) -> JWTAuth:
    """
    Configure JWT authentication for a FastAPI application.
    
    This function sets up JWT authentication middleware and provides
    authentication-related dependencies.
    
    Args:
        app: The FastAPI application
        config: Security configuration
        user_model: User model class
        user_loader: Function to load a user by ID
        on_auth_success: Callback for successful authentication
        on_auth_failure: Callback for failed authentication
        exclude_paths: Paths to exclude from authentication
        
    Returns:
        The JWT authentication manager
    """
    # Create JWT auth manager
    jwt_auth = JWTAuth(config)
    
    # Get exclude paths
    if exclude_paths is None:
        if isinstance(config, SecurityConfig):
            exclude_paths = config.authentication.jwt_exclude_paths
        elif isinstance(config, AuthenticationConfig):
            exclude_paths = getattr(config, "jwt_exclude_paths", [
                "/auth/login", "/auth/register", "/auth/refresh", 
                "/docs", "/openapi.json"
            ])
        else:
            exclude_paths = [
                "/auth/login", "/auth/register", "/auth/refresh", 
                "/docs", "/openapi.json"
            ]
    
    # Add JWT middleware
    app.add_middleware(
        JWTAuthMiddleware,
        jwt_auth=jwt_auth,
        exclude_paths=exclude_paths
    )
    
    # Create JWT bearer security scheme
    oauth2_scheme = JWTBearer(jwt_auth)
    
    # Register user loader as dependency
    if user_model and user_loader:
        async def get_current_user(token_data: TokenData = Depends(oauth2_scheme)):
            """
            Get the current authenticated user.
            
            Args:
                token_data: The token data from the JWT
                
            Returns:
                The current user
                
            Raises:
                HTTPException: If the user is not found
            """
            try:
                user = await user_loader(token_data.sub)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                # Call success callback if provided
                if on_auth_success:
                    await on_auth_success(user, token_data)
                
                return user
            except Exception as e:
                # Call failure callback if provided
                if on_auth_failure:
                    await on_auth_failure(token_data, str(e))
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        # Register the dependency
        app.dependency_overrides[get_current_user_id] = get_current_user
    
    return jwt_auth


def create_auth_router(
    jwt_auth: JWTAuth,
    user_model: Type,
    authenticate_user: Callable,
    register_user: Optional[Callable] = None,
    prefix: str = "/auth"
):
    """
    Create a FastAPI router for authentication endpoints.
    
    This function creates a router with login, refresh token, and
    optionally registration endpoints.
    
    Args:
        jwt_auth: JWT authentication manager
        user_model: User model class
        authenticate_user: Function to authenticate a user
        register_user: Function to register a new user
        prefix: URL prefix for the authentication endpoints
        
    Returns:
        FastAPI router with authentication endpoints
    """
    from fastapi import APIRouter
    
    router = APIRouter(prefix=prefix)
    
    # Define response models
    class TokenResponse(BaseModel):
        access_token: str
        refresh_token: str
        token_type: str
        expires_in: int
    
    class TokenRefresh(BaseModel):
        refresh_token: str
    
    # Login endpoint
    @router.post("/login", response_model=TokenResponse)
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Login endpoint for OAuth2 password flow.
        
        Args:
            form_data: Login form data with username and password
            
        Returns:
            Access and refresh tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        # Authenticate user
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Prepare additional claims
        additional_claims = {}
        
        # Add email if available
        if hasattr(user, "email"):
            additional_claims["email"] = getattr(user, "email")
        
        # Add name if available
        if hasattr(user, "name") or hasattr(user, "full_name"):
            additional_claims["name"] = getattr(user, "name", None) or getattr(user, "full_name", None)
        
        # Add roles if available
        if hasattr(user, "roles"):
            additional_claims["roles"] = getattr(user, "roles", [])
        
        # Add tenant ID if available
        if hasattr(user, "tenant_id"):
            additional_claims["tenant_id"] = getattr(user, "tenant_id")
        
        # Create tokens
        user_id = str(getattr(user, "id"))
        access_token = jwt_auth.create_access_token(
            subject=user_id,
            additional_claims=additional_claims
        )
        
        refresh_token = jwt_auth.create_refresh_token(
            subject=user_id,
            additional_claims=additional_claims
        )
        
        # Create response
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=jwt_auth.config.access_token_expire_minutes * 60
        )
    
    # Token refresh endpoint
    @router.post("/refresh", response_model=TokenResponse)
    async def refresh_token(token_data: TokenRefresh):
        """
        Refresh token endpoint.
        
        Args:
            token_data: Refresh token
            
        Returns:
            New access token and existing refresh token
            
        Raises:
            HTTPException: If the refresh token is invalid
        """
        try:
            # Create new access token
            access_token = jwt_auth.refresh_access_token(token_data.refresh_token)
            
            # Get refresh token data
            refresh_token_data = jwt_auth.decode_token(token_data.refresh_token)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=token_data.refresh_token,
                token_type="bearer",
                expires_in=jwt_auth.config.access_token_expire_minutes * 60
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # User registration endpoint (optional)
    if register_user:
        @router.post("/register", status_code=status.HTTP_201_CREATED)
        async def register(user_data: Any):
            """
            Register a new user.
            
            Args:
                user_data: User registration data
                
            Returns:
                Created user data
                
            Raises:
                HTTPException: If registration fails
            """
            try:
                # Register user
                user = await register_user(user_data)
                
                # Return user data (without password)
                return user
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Registration failed: {str(e)}"
                )
    
    return router


def create_test_user_loader(users_db: Dict[str, Any]):
    """
    Create a test user loader function for development purposes.
    
    This is a helper function for creating a user loader that retrieves
    users from a dictionary, suitable for testing and development.
    
    Args:
        users_db: Dictionary of user data
        
    Returns:
        User loader function
    """
    async def user_loader(user_id: str):
        """
        Load a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        user_data = users_db.get(user_id)
        if not user_data:
            return None
        
        return user_data
    
    return user_loader


def create_test_authenticator(users_db: Dict[str, Any], username_field: str = "username", password_verifier: Optional[Callable] = None):
    """
    Create a test user authenticator function for development purposes.
    
    This is a helper function for creating an authenticator that authenticates
    users against a dictionary, suitable for testing and development.
    
    Args:
        users_db: Dictionary of user data
        username_field: Field name for the username
        password_verifier: Function to verify the password
        
    Returns:
        User authenticator function
    """
    async def authenticator(username: str, password: str):
        """
        Authenticate a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User object or None if authentication fails
        """
        # Find user by username
        for user_id, user_data in users_db.items():
            if user_data.get(username_field) == username:
                # Verify password
                if password_verifier:
                    if password_verifier(password, user_data.get("password") or user_data.get("hashed_password")):
                        return user_data
                else:
                    # Simple equality check if no verifier is provided
                    if password == user_data.get("password"):
                        return user_data
                
                # Password is incorrect
                return None
        
        # User not found
        return None
    
    return authenticator