"""
Authentication and authorization support for the unified endpoint framework.

This module provides authentication and authorization capabilities for API endpoints.
"""

from .exceptions import AuthenticationError, AuthorizationError
from .protocols import AuthenticationBackend
from .models import User, UserContext, Role, Permission
from .middleware import AuthenticationMiddleware, setup_auth
from .dependencies import get_user_context, RequireRoles, RequirePermissions, requires_auth
from .endpoints import SecureBaseEndpoint, SecureCrudEndpoint, SecureCqrsEndpoint
from .backends import JWTAuthBackend

__all__ = [
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    
    # Protocols
    "AuthenticationBackend",
    
    # Models
    "User",
    "UserContext",
    "Role",
    "Permission",
    
    # Middleware
    "AuthenticationMiddleware",
    "setup_auth",
    
    # Dependencies
    "get_user_context",
    "RequireRoles",
    "RequirePermissions",
    "requires_auth",
    
    # Endpoints
    "SecureBaseEndpoint",
    "SecureCrudEndpoint",
    "SecureCqrsEndpoint",
    
    # Backends
    "JWTAuthBackend",
]