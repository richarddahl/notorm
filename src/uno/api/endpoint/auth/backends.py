"""
Authentication backends.

This module provides authentication backends for the unified endpoint framework.
"""

import logging
import time
from typing import Dict, Optional

import jwt
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from .exceptions import AuthenticationError
from .models import User
from .protocols import AuthenticationBackend

logger = logging.getLogger(__name__)


class JWTAuthBackend(AuthenticationBackend):
    """JWT authentication backend."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        token_url: str = "/api/token",
        token_type: str = "Bearer",
    ):
        """
        Initialize the JWT authentication backend.
        
        Args:
            secret_key: The secret key used to sign JWT tokens
            algorithm: The algorithm used to sign JWT tokens
            token_url: The URL for token generation
            token_type: The token type (e.g. "Bearer")
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_url = token_url
        self.token_type = token_type
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """
        Authenticate a request using JWT.
        
        Args:
            request: The FastAPI request
            
        Returns:
            A user if authentication is successful, None otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Get the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Anonymous user
            return None
        
        # Check the token type
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.token_type:
            raise AuthenticationError(
                message=f"Invalid token format, expected {self.token_type} token",
                code="INVALID_TOKEN_FORMAT",
            )
        
        token = parts[1]
        
        try:
            # Decode the token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if the token has expired
            if "exp" in payload and payload["exp"] < time.time():
                raise AuthenticationError(
                    message="Token has expired",
                    code="TOKEN_EXPIRED",
                )
            
            # Extract user information from the payload
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError(
                    message="Token is missing subject claim",
                    code="INVALID_TOKEN_CLAIMS",
                )
            
            # Create a user from the payload
            user = User(
                id=user_id,
                username=payload.get("username", user_id),
                email=payload.get("email"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                metadata=payload.get("metadata", {}),
            )
            
            return user
            
        except jwt.PyJWTError as e:
            logger.warning(f"JWT authentication failed: {str(e)}")
            raise AuthenticationError(
                message="Invalid authentication token",
                code="INVALID_TOKEN",
                details={"error": str(e)},
            )
    
    async def on_error(self, request: Request, exc: Exception) -> Response:
        """
        Handle an authentication error.
        
        Args:
            request: The FastAPI request
            exc: The exception that occurred
            
        Returns:
            A response to send to the client
        """
        if isinstance(exc, AuthenticationError):
            status_code = exc.status_code
            error = {
                "code": exc.code,
                "message": str(exc),
                "details": exc.details,
            }
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
            error = {
                "code": "AUTHENTICATION_FAILED",
                "message": str(exc),
            }
        
        return JSONResponse(
            status_code=status_code,
            content={"error": error},
            headers={"WWW-Authenticate": f'{self.token_type} realm="{self.token_url}"'},
        )
    
    def create_token(
        self,
        user: User,
        expires_in: int = 3600,
        additional_claims: Optional[Dict] = None,
    ) -> str:
        """
        Create a JWT token for a user.
        
        Args:
            user: The user to create a token for
            expires_in: The token validity period in seconds
            additional_claims: Additional claims to include in the token
            
        Returns:
            A JWT token
        """
        now = int(time.time())
        claims = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "permissions": user.permissions,
            "iat": now,
            "exp": now + expires_in,
        }
        
        if additional_claims:
            claims.update(additional_claims)
        
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)