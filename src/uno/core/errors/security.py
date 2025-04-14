# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Security-related errors for the Uno framework.

This module provides error classes for authentication, authorization, and other
security-related concerns.
"""

from typing import Any, Dict, Optional
from uno.core.errors.base import UnoError, ErrorCode


class AuthenticationError(UnoError):
    """
    Error raised when authentication fails.
    
    This error is raised when a user cannot be authenticated, such as when
    credentials are invalid or missing.
    """
    
    def __init__(
        self, 
        message: str = "Authentication failed", 
        error_code: str = ErrorCode.AUTHENTICATION_ERROR,
        **context: Any
    ):
        """
        Initialize an authentication error.
        
        Args:
            message: The error message
            error_code: The error code
            **context: Additional context information
        """
        super().__init__(message, error_code, **context)


class AuthorizationError(UnoError):
    """
    Error raised when authorization fails.
    
    This error is raised when a user does not have permission to perform
    an operation or access a resource.
    """
    
    def __init__(
        self, 
        message: str = "Authorization failed", 
        error_code: str = ErrorCode.AUTHORIZATION_ERROR,
        permission: Optional[str] = None,
        resource: Optional[str] = None,
        **context: Any
    ):
        """
        Initialize an authorization error.
        
        Args:
            message: The error message
            error_code: The error code
            permission: The required permission
            resource: The resource being accessed
            **context: Additional context information
        """
        ctx = context.copy()
        if permission:
            ctx["permission"] = permission
        if resource:
            ctx["resource"] = resource
            
        super().__init__(message, error_code, **ctx)