"""
Authentication and authorization exceptions.

This module defines exceptions related to authentication and authorization in the unified endpoint framework.
"""

from typing import Any, Dict, Optional


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTHENTICATION_FAILED",
        status_code: int = 401,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new authentication error.
        
        Args:
            message: The error message
            code: The error code
            status_code: The HTTP status code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthorizationError(Exception):
    """Exception raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        code: str = "AUTHORIZATION_FAILED",
        status_code: int = 403,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new authorization error.
        
        Args:
            message: The error message
            code: The error code
            status_code: The HTTP status code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)