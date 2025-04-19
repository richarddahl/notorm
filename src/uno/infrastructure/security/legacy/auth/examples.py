"""
Examples for using the Uno security authentication system with FastAPI.

This module provides example implementations of authentication routes and
middleware for FastAPI applications using Uno's security framework.
"""

from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from uno.security.auth.jwt import (
    JWTAuth, JWTConfig, JWTBearer, JWTAuthMiddleware, TokenData,
    get_current_user_id, get_current_user_roles, require_role
)
from uno.security.auth.password import (
    hash_password, verify_password, SecurePasswordPolicy, PasswordPolicyLevel
)


# Model for user data
class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []


# Model for user registration
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


# Model for user login
class UserLogin(BaseModel):
    username: str
    password: str


# Model for token response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


# Model for token refresh
class TokenRefresh(BaseModel):
    refresh_token: str


# Simple user database for example purposes
fake_users_db = {
    "user1": {
        "id": "user1",
        "username": "johndoe",
        "email": "john@example.com",
        "hashed_password": hash_password("password123"),
        "full_name": "John Doe",
        "disabled": False,
        "roles": ["user"]
    },
    "user2": {
        "id": "user2",
        "username": "alice",
        "email": "alice@example.com",
        "hashed_password": hash_password("password456"),
        "full_name": "Alice Smith",
        "disabled": False,
        "roles": ["user", "admin"]
    }
}


# JWT Configuration - In a real app, this would use SecurityConfig
jwt_config = JWTConfig(
    secret_key="CHANGE_THIS_TO_A_SECURE_SECRET_KEY_IN_PRODUCTION",
    algorithm="HS256",
    access_token_expire_minutes=30,
    refresh_token_expire_days=7,
    issuer="uno_example",
    audience="uno_app"
)


# Initialize JWT auth
jwt_auth = JWTAuth(jwt_config)


# Password policy
password_policy = SecurePasswordPolicy(
    level=PasswordPolicyLevel.STANDARD,
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_numbers=True,
    require_special_chars=True
)


# Setup JWT bearer for FastAPI dependency injection
oauth2_scheme = JWTBearer(jwt_auth)


# Functions to get users
def get_user_by_username(username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        username: The username to look up
        
    Returns:
        The user object, or None if not found
    """
    for user_id, user_data in fake_users_db.items():
        if user_data["username"] == username:
            return User(**user_data)
    return None


def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        user_id: The user ID to look up
        
    Returns:
        The user object, or None if not found
    """
    user_data = fake_users_db.get(user_id)
    if user_data:
        return User(**user_data)
    return None


# Dependency to get the current user
def get_current_user(token_data: TokenData = Depends(oauth2_scheme)) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token_data: The token data from the JWT
        
    Returns:
        The current user
        
    Raises:
        HTTPException: If the user is not found
    """
    user = get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        user: The current user
        
    Returns:
        The current active user
        
    Raises:
        HTTPException: If the user is disabled
    """
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user


# Create a FastAPI app with JWT auth
def create_auth_app():
    """
    Create a FastAPI app with JWT authentication routes.
    
    Returns:
        FastAPI app with authentication routes
    """
    app = FastAPI(title="Uno Auth Example")
    
    # Add JWT middleware
    app.add_middleware(
        JWTAuthMiddleware,
        jwt_auth=jwt_auth,
        exclude_paths=["/auth/login", "/auth/register", "/auth/refresh", "/docs", "/openapi.json"]
    )
    
    # Login route
    @app.post("/auth/login", response_model=TokenResponse)
    async def login(form_data: UserLogin):
        # Authenticate user
        user = get_user_by_username(form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify password
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Create tokens
        additional_claims = {
            "email": user.email,
            "name": user.full_name,
            "roles": user.roles
        }
        
        access_token = jwt_auth.create_access_token(
            subject=user.id,
            additional_claims=additional_claims
        )
        
        refresh_token = jwt_auth.create_refresh_token(
            subject=user.id,
            additional_claims=additional_claims
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=jwt_config.access_token_expire_minutes * 60
        )
    
    # Register route
    @app.post("/auth/register", status_code=status.HTTP_201_CREATED)
    async def register(user_data: UserCreate):
        # Check if username already exists
        existing_user = get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Validate password
        password_result = password_policy.validate(user_data.password)
        if not password_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_result["message"]
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Generate user ID
        import uuid
        user_id = str(uuid.uuid4())
        
        # Create user
        new_user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "full_name": user_data.full_name,
            "disabled": False,
            "roles": ["user"]
        }
        
        # Add to database
        fake_users_db[user_id] = new_user
        
        return {"id": user_id, "message": "User created successfully"}
    
    # Token refresh route
    @app.post("/auth/refresh", response_model=TokenResponse)
    async def refresh_token(token_data: TokenRefresh):
        try:
            # Create new access token
            access_token = jwt_auth.refresh_access_token(token_data.refresh_token)
            
            # Get refresh token data
            refresh_token_data = jwt_auth.decode_token(token_data.refresh_token)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=token_data.refresh_token,
                token_type="bearer",
                expires_in=jwt_config.access_token_expire_minutes * 60
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # Protected route for any authenticated user
    @app.get("/users/me", response_model=User)
    async def read_users_me(user: User = Depends(get_current_active_user)):
        return user
    
    # Protected route requiring admin role
    @app.get("/admin/dashboard")
    async def admin_dashboard(
        user: User = Depends(get_current_active_user),
        has_role: bool = Depends(require_role("admin"))
    ):
        return {
            "message": "Admin dashboard",
            "user": user.username,
            "roles": user.roles
        }
    
    return app


# FastAPI OAuth2 version (alternative implementation using FastAPI's built-in OAuth2)
def create_oauth2_app():
    """
    Create a FastAPI app with OAuth2 password flow authentication.
    
    Returns:
        FastAPI app with OAuth2 authentication
    """
    app = FastAPI(title="Uno OAuth2 Example")
    
    # OAuth2 scheme
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
    
    # Get current user from OAuth2 token
    async def get_current_user_from_oauth2(token: str = Depends(oauth2_scheme)) -> User:
        try:
            # Decode the token
            token_data = jwt_auth.decode_token(token)
            
            # Get the user
            user = get_user_by_id(token_data.sub)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # Get current active user
    async def get_current_active_user(user: User = Depends(get_current_user_from_oauth2)) -> User:
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        return user
    
    # Token endpoint
    @app.post("/auth/token")
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        # Authenticate user
        user = get_user_by_username(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        additional_claims = {
            "email": user.email,
            "name": user.full_name,
            "roles": user.roles
        }
        
        access_token = jwt_auth.create_access_token(
            subject=user.id,
            additional_claims=additional_claims
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    # Protected route
    @app.get("/users/me", response_model=User)
    async def read_users_me(user: User = Depends(get_current_active_user)):
        return user
    
    return app