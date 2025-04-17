"""
JWT authentication utilities for Uno applications.

This module provides JWT token generation, validation, and related utilities
for implementing token-based authentication in Uno applications.
"""

import time
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import jwt
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from uno.security.config import SecurityConfig, AuthenticationConfig
from uno.security.auth.token_cache import TokenCache, TokenCacheConfig, create_token_cache


@dataclass
class JWTConfig:
    """Configuration for JWT generation and validation."""
    
    secret_key: str
    """Secret key for signing JWTs."""
    
    algorithm: str = "HS256"
    """Algorithm for signing JWTs."""
    
    access_token_expire_minutes: int = 60
    """Expiration time for access tokens in minutes."""
    
    refresh_token_expire_days: int = 7
    """Expiration time for refresh tokens in days."""
    
    issuer: Optional[str] = None
    """Issuer claim for the JWT."""
    
    audience: Optional[str] = None
    """Audience claim for the JWT."""
    
    token_type: str = "Bearer"
    """Type of token for the Authorization header."""


class TokenType(str, Enum):
    """Type of JWT token."""
    
    ACCESS = "access"
    REFRESH = "refresh"


class TokenData(BaseModel):
    """Data contained in a JWT token."""
    
    sub: str
    """Subject of the token (typically user ID)."""
    
    exp: int
    """Expiration time (Unix timestamp)."""
    
    iat: int
    """Issued at time (Unix timestamp)."""
    
    token_type: TokenType
    """Type of token (access or refresh)."""
    
    jti: str
    """JWT ID (unique identifier for the token)."""
    
    roles: List[str] = []
    """User roles for authorization."""
    
    tenant_id: Optional[str] = None
    """Tenant ID for multi-tenancy."""
    
    email: Optional[str] = None
    """User email address."""
    
    name: Optional[str] = None
    """User name."""
    
    custom_claims: Dict[str, Any] = field(default_factory=dict)
    """Custom claims for application-specific data."""


class JWTAuth:
    """
    JWT authentication manager.
    
    This class provides methods for creating, validating, and managing JWT tokens
    for authentication in Uno applications.
    """
    
    def __init__(
        self,
        config: Union[JWTConfig, SecurityConfig, AuthenticationConfig],
        logger: Optional[logging.Logger] = None,
        token_cache: Optional[TokenCache] = None
    ):
        """
        Initialize the JWT authentication manager.
        
        Args:
            config: JWT configuration or security configuration
            logger: Logger instance
            token_cache: Optional token cache for improved performance
        """
        self.logger = logger or logging.getLogger("uno.security.auth.jwt")
        
        # Extract JWT configuration from various config types
        if isinstance(config, JWTConfig):
            self.config = config
        elif isinstance(config, SecurityConfig):
            auth_config = config.authentication
            self.config = JWTConfig(
                secret_key=auth_config.jwt_secret_key,
                algorithm=auth_config.jwt_algorithm,
                access_token_expire_minutes=auth_config.jwt_expiration_minutes,
                refresh_token_expire_days=auth_config.refresh_token_expiration_days,
                issuer=auth_config.jwt_issuer,
                audience=auth_config.jwt_audience
            )
        elif isinstance(config, AuthenticationConfig):
            self.config = JWTConfig(
                secret_key=getattr(config, "jwt_secret_key", ""),
                algorithm=getattr(config, "jwt_algorithm", "HS256"),
                access_token_expire_minutes=config.jwt_expiration_minutes,
                refresh_token_expire_days=config.refresh_token_expiration_days,
                issuer=getattr(config, "jwt_issuer", None),
                audience=getattr(config, "jwt_audience", None)
            )
        else:
            raise TypeError(f"Unsupported config type: {type(config)}")
        
        if not self.config.secret_key:
            self.logger.warning("No JWT secret key provided. Using an insecure default key.")
            self.config.secret_key = "INSECURE_DEFAULT_KEY_CHANGE_THIS_IN_PRODUCTION"
        
        # Initialize token cache if provided or create a default one
        self.token_cache = token_cache or create_token_cache(config, logger)
    
    def create_access_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new access token.
        
        Args:
            subject: Subject of the token (typically user ID)
            additional_claims: Additional claims to include in the token
            expires_delta: Custom expiration time delta
            
        Returns:
            Encoded JWT access token
        """
        return self._create_token(
            subject=subject,
            token_type=TokenType.ACCESS,
            additional_claims=additional_claims,
            expires_delta=expires_delta or timedelta(minutes=self.config.access_token_expire_minutes)
        )
    
    def create_refresh_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new refresh token.
        
        Args:
            subject: Subject of the token (typically user ID)
            additional_claims: Additional claims to include in the token
            expires_delta: Custom expiration time delta
            
        Returns:
            Encoded JWT refresh token
        """
        return self._create_token(
            subject=subject,
            token_type=TokenType.REFRESH,
            additional_claims=additional_claims,
            expires_delta=expires_delta or timedelta(days=self.config.refresh_token_expire_days)
        )
    
    def _create_token(
        self,
        subject: str,
        token_type: TokenType,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: timedelta = timedelta(minutes=15)
    ) -> str:
        """
        Create a new JWT token.
        
        Args:
            subject: Subject of the token (typically user ID)
            token_type: Type of token (access or refresh)
            additional_claims: Additional claims to include in the token
            expires_delta: Expiration time delta
            
        Returns:
            Encoded JWT token
        """
        import uuid
        
        now = datetime.now(datetime.UTC)
        expires_at = now + expires_delta
        
        # Prepare claims
        claims = {
            "sub": subject,
            "exp": int(expires_at.timestamp()),
            "iat": int(now.timestamp()),
            "token_type": token_type,
            "jti": str(uuid.uuid4())
        }
        
        # Add optional standard claims
        if self.config.issuer:
            claims["iss"] = self.config.issuer
            
        if self.config.audience:
            claims["aud"] = self.config.audience
        
        # Add additional claims
        if additional_claims:
            # Extract known claims
            if "roles" in additional_claims:
                claims["roles"] = additional_claims.pop("roles")
                
            if "tenant_id" in additional_claims:
                claims["tenant_id"] = additional_claims.pop("tenant_id")
                
            if "email" in additional_claims:
                claims["email"] = additional_claims.pop("email")
                
            if "name" in additional_claims:
                claims["name"] = additional_claims.pop("name")
            
            # Add remaining claims as custom_claims
            if additional_claims:
                claims["custom_claims"] = additional_claims
        
        # Encode the token
        return jwt.encode(
            claims,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
    
    def decode_token(self, token: str) -> TokenData:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The JWT token to decode and validate
            
        Returns:
            The decoded token data
            
        Raises:
            jwt.InvalidTokenError: If the token is invalid
        """
        try:
            # Check token cache first
            cached_payload = None
            if self.token_cache:
                cached_payload = self.token_cache.get(token)
                
                if cached_payload:
                    self.logger.debug("Token found in cache")
                    
                    # Verify expiration
                    exp = cached_payload["exp"]
                    if exp < time.time():
                        self.logger.debug("Cached token expired")
                        self.token_cache.invalidate(token)
                        raise jwt.ExpiredSignatureError("Token has expired")
                    
                    # Check for token JTI in blacklist
                    if self.token_cache.is_blacklisted(cached_payload["jti"]):
                        self.logger.warning(f"Token {cached_payload['jti']} is blacklisted")
                        raise jwt.InvalidTokenError("Token has been revoked")
            
            # Not in cache or cache disabled, decode token
            if not cached_payload:
                payload = jwt.decode(
                    token,
                    self.config.secret_key,
                    algorithms=[self.config.algorithm],
                    options={"verify_signature": True, "verify_exp": True}
                )
                
                # Check for token JTI in blacklist
                if self.token_cache and self.token_cache.is_blacklisted(payload["jti"]):
                    self.logger.warning(f"Token {payload['jti']} is blacklisted")
                    raise jwt.InvalidTokenError("Token has been revoked")
                
                # Cache the token for future use
                if self.token_cache:
                    self.token_cache.set(token, payload)
                    self.logger.debug("Token added to cache")
            else:
                # Use cached payload
                payload = cached_payload
            
            # Extract custom claims if present
            custom_claims = payload.pop("custom_claims", {}) if "custom_claims" in payload else {}
            
            # Create TokenData object
            token_data = TokenData(
                sub=payload["sub"],
                exp=payload["exp"],
                iat=payload["iat"],
                token_type=payload["token_type"],
                jti=payload["jti"],
                roles=payload.get("roles", []),
                tenant_id=payload.get("tenant_id"),
                email=payload.get("email"),
                name=payload.get("name"),
                custom_claims=custom_claims
            )
            
            return token_data
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {str(e)}")
            raise
            
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding its JTI to the blacklist.
        
        Args:
            token: The token to revoke
            
        Returns:
            True if the token was revoked, False otherwise
        """
        if not self.token_cache:
            self.logger.warning("Cannot revoke token: token cache not available")
            return False
        
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                options={"verify_signature": True, "verify_exp": False}  # Don't verify exp to allow revoking expired tokens
            )
            
            # Get JTI and expiry
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if not jti or not exp:
                self.logger.warning("Cannot revoke token: missing jti or exp claim")
                return False
            
            # Blacklist the token
            self.token_cache.blacklist(jti, exp)
            
            # Invalidate from token cache
            self.token_cache.invalidate(token)
            
            self.logger.info(f"Revoked token with JTI: {jti}")
            return True
        except Exception as e:
            self.logger.error(f"Error revoking token: {e}")
            return False
            raise
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create a new access token from a refresh token.
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            A new access token
            
        Raises:
            ValueError: If the token is not a refresh token
            jwt.InvalidTokenError: If the token is invalid
        """
        # Decode the refresh token
        token_data = self.decode_token(refresh_token)
        
        # Check that it's a refresh token
        if token_data.token_type != TokenType.REFRESH:
            raise ValueError("Not a refresh token")
        
        # Create a new access token with the same claims
        additional_claims = {
            "roles": token_data.roles,
            "tenant_id": token_data.tenant_id,
            "email": token_data.email,
            "name": token_data.name,
            **token_data.custom_claims
        }
        
        return self.create_access_token(
            subject=token_data.sub,
            additional_claims=additional_claims
        )


class JWTBearer(HTTPBearer):
    """
    JWT Bearer authentication for FastAPI.
    
    This class implements the FastAPI security dependency for JWT bearer
    token authentication.
    """
    
    def __init__(
        self,
        jwt_auth: JWTAuth,
        auto_error: bool = True,
        token_type: TokenType = TokenType.ACCESS
    ):
        """
        Initialize the JWT bearer authentication.
        
        Args:
            jwt_auth: JWT authentication manager
            auto_error: Whether to raise an error for missing or invalid tokens
            token_type: Type of token to accept (access or refresh)
        """
        super().__init__(auto_error=auto_error)
        self.jwt_auth = jwt_auth
        self.token_type = token_type
    
    async def __call__(self, request: Request) -> TokenData:
        """
        Check and process the authorization header.
        
        Args:
            request: The HTTP request
            
        Returns:
            The decoded token data
            
        Raises:
            HTTPException: If the token is missing or invalid
        """
        # Get credentials from the request
        credentials = await super().__call__(request)
        
        # Handle missing credentials
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            else:
                return None
        
        # Validate the token
        try:
            token_data = self.jwt_auth.decode_token(credentials.credentials)
            
            # Check token type
            if token_data.token_type != self.token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {self.token_type}, got {token_data.token_type}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return token_data
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )


class JWTAuthMiddleware:
    """
    JWT authentication middleware for FastAPI.
    
    This middleware extracts and validates JWT tokens from requests,
    and attaches the decoded token data to the request state.
    """
    
    def __init__(
        self,
        app: Any,
        jwt_auth: JWTAuth,
        token_type: TokenType = TokenType.ACCESS,
        exclude_paths: List[str] = None,
        token_in_headers: bool = True,
        token_in_cookies: bool = False,
        token_in_query: bool = False,
        header_name: str = "Authorization",
        cookie_name: str = "access_token",
        query_param_name: str = "token"
    ):
        """
        Initialize the JWT authentication middleware.
        
        Args:
            app: The ASGI application
            jwt_auth: JWT authentication manager
            token_type: Type of token to accept (access or refresh)
            exclude_paths: List of paths to exclude from authentication
            token_in_headers: Whether to look for tokens in HTTP headers
            token_in_cookies: Whether to look for tokens in cookies
            token_in_query: Whether to look for tokens in query parameters
            header_name: Name of the header containing the token
            cookie_name: Name of the cookie containing the token
            query_param_name: Name of the query parameter containing the token
        """
        self.app = app
        self.jwt_auth = jwt_auth
        self.token_type = token_type
        self.exclude_paths = exclude_paths or []
        self.token_in_headers = token_in_headers
        self.token_in_cookies = token_in_cookies
        self.token_in_query = token_in_query
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.query_param_name = query_param_name
    
    async def __call__(self, scope, receive, send):
        """
        Process the ASGI request.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive function
            send: ASGI send function
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests
            return await self.app(scope, receive, send)
        
        # Get the request path
        path = scope.get("path", "")
        
        # Check if the path should be excluded
        if self._should_exclude(path):
            return await self.app(scope, receive, send)
        
        # Create a request object
        from starlette.requests import Request
        request = Request(scope, receive=receive)
        
        # Extract the token
        token = await self._extract_token(request)
        
        if token:
            try:
                # Validate the token
                token_data = self.jwt_auth.decode_token(token)
                
                # Check token type
                if token_data.token_type != self.token_type:
                    return await self.app(scope, receive, send)
                
                # Attach the token data to the request state
                request.state.token_data = token_data
                request.state.user_id = token_data.sub
                
                # Add user roles for authorization
                request.state.user_roles = token_data.roles or []
                
                # Add tenant ID for multi-tenancy
                if token_data.tenant_id:
                    request.state.tenant_id = token_data.tenant_id
            except jwt.InvalidTokenError:
                # Invalid token, continue without authentication
                pass
        
        return await self.app(scope, receive, send)
    
    async def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract the JWT token from the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The JWT token, or None if not found
        """
        token = None
        
        # Try to extract from header
        if self.token_in_headers:
            auth_header = request.headers.get(self.header_name)
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        # Try to extract from cookies
        if not token and self.token_in_cookies:
            token = request.cookies.get(self.cookie_name)
        
        # Try to extract from query parameters
        if not token and self.token_in_query:
            token = request.query_params.get(self.query_param_name)
        
        return token
    
    def _should_exclude(self, path: str) -> bool:
        """
        Check if the path should be excluded from authentication.
        
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


def get_token_data(
    token_data: TokenData = Depends(JWTBearer(JWTAuth(JWTConfig("placeholder"))))
) -> TokenData:
    """
    FastAPI dependency to get the token data.
    
    This is a placeholder dependency that should be overridden with a properly
    configured JWTBearer instance.
    
    Args:
        token_data: The token data from JWTBearer
        
    Returns:
        The token data
    """
    return token_data


def get_current_user_id(token_data: TokenData = Depends(get_token_data)) -> str:
    """
    FastAPI dependency to get the current user ID.
    
    Args:
        token_data: The token data from get_token_data
        
    Returns:
        The current user ID
    """
    return token_data.sub


def get_current_user_roles(token_data: TokenData = Depends(get_token_data)) -> List[str]:
    """
    FastAPI dependency to get the current user's roles.
    
    Args:
        token_data: The token data from get_token_data
        
    Returns:
        The current user's roles
    """
    return token_data.roles


def get_current_tenant_id(token_data: TokenData = Depends(get_token_data)) -> Optional[str]:
    """
    FastAPI dependency to get the current tenant ID.
    
    Args:
        token_data: The token data from get_token_data
        
    Returns:
        The current tenant ID, or None if not set
    """
    return token_data.tenant_id


def create_jwt_auth(
    config: Optional[Union[JWTConfig, SecurityConfig, AuthenticationConfig]] = None,
    secret_key: Optional[str] = None,
    algorithm: str = "HS256",
    access_token_expire_minutes: int = 60,
    refresh_token_expire_days: int = 7,
    issuer: Optional[str] = None,
    audience: Optional[str] = None
) -> JWTAuth:
    """
    Create a JWT authentication manager.
    
    Args:
        config: JWT, Security, or Authentication configuration
        secret_key: Secret key for signing JWTs
        algorithm: Algorithm for signing JWTs
        access_token_expire_minutes: Expiration time for access tokens in minutes
        refresh_token_expire_days: Expiration time for refresh tokens in days
        issuer: Issuer claim for the JWT
        audience: Audience claim for the JWT
        
    Returns:
        JWT authentication manager
    """
    if config:
        return JWTAuth(config)
    else:
        jwt_config = JWTConfig(
            secret_key=secret_key or "",
            algorithm=algorithm,
            access_token_expire_minutes=access_token_expire_minutes,
            refresh_token_expire_days=refresh_token_expire_days,
            issuer=issuer,
            audience=audience
        )
        return JWTAuth(jwt_config)


def require_role(required_role: str):
    """
    FastAPI dependency to require a specific role.
    
    Args:
        required_role: The required role
    
    Returns:
        A dependency that checks if the user has the required role
    """
    def _require_role(roles: List[str] = Depends(get_current_user_roles)):
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return True
    
    return _require_role


def require_any_role(required_roles: List[str]):
    """
    FastAPI dependency to require any of the specified roles.
    
    Args:
        required_roles: List of roles, any of which is sufficient
    
    Returns:
        A dependency that checks if the user has any of the required roles
    """
    def _require_any_role(roles: List[str] = Depends(get_current_user_roles)):
        if not any(role in required_roles for role in roles):
            roles_str = ", ".join(required_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Any of these roles required: {roles_str}"
            )
        return True
    
    return _require_any_role


def require_all_roles(required_roles: List[str]):
    """
    FastAPI dependency to require all of the specified roles.
    
    Args:
        required_roles: List of roles, all of which are required
    
    Returns:
        A dependency that checks if the user has all of the required roles
    """
    def _require_all_roles(roles: List[str] = Depends(get_current_user_roles)):
        if not all(role in roles for role in required_roles):
            roles_str = ", ".join(required_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of these roles required: {roles_str}"
            )
        return True
    
    return _require_all_roles