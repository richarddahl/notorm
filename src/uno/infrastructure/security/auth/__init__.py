"""
Authentication for Uno applications.

This module provides authentication functionality for Uno applications,
including password management, multi-factor authentication, JWT token authentication,
and single sign-on.
"""

from uno.security.auth.manager import MFAManager
from uno.security.auth.totp import TOTPProvider
from uno.security.auth.password import (
    SecurePasswordPolicy, 
    hash_password, 
    verify_password
)
from uno.security.auth.sso import SSOProvider
from uno.security.auth.jwt import (
    JWTAuth,
    JWTConfig,
    JWTBearer,
    JWTAuthMiddleware,
    TokenData,
    TokenType,
    get_current_user_id,
    get_current_user_roles,
    get_current_tenant_id,
    require_role,
    require_any_role,
    require_all_roles,
    create_jwt_auth
)

__all__ = [
    "MFAManager",
    "TOTPProvider",
    "SecurePasswordPolicy",
    "hash_password",
    "verify_password",
    "SSOProvider",
    "JWTAuth",
    "JWTConfig",
    "JWTBearer",
    "JWTAuthMiddleware",
    "TokenData",
    "TokenType",
    "get_current_user_id",
    "get_current_user_roles",
    "get_current_tenant_id",
    "require_role",
    "require_any_role",
    "require_all_roles",
    "create_jwt_auth"
]