"""
Error types for UNO.

This module defines the base error classes and specific error types
used throughout the UNO framework.
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional


# Error classification enums
class ErrorSeverity(str, Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    NETWORK = "network"
    RESOURCE = "resource"
    BUSINESS = "business"
    SYSTEM = "system"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


# Base error class
class FrameworkError(Exception):
    """
    Base class for all framework-specific errors.

    This class extends the standard Exception class with additional properties
    and utilities for working with the UNO error framework.
    """

    def __init__(
        self,
        message: str,
        code: str = "FRAMEWORK_ERROR",
        details: Optional[Dict[str, Any]] = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        http_status_code: Optional[int] = None,
        context: Optional["ErrorContext"] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize a framework error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            category: Error category
            severity: Error severity
            http_status_code: HTTP status code for API responses
            context: Error context information
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.code = code.upper()
        self.details = details or {}
        self.category = category
        self.severity = severity
        self.http_status_code = http_status_code
        # Import here to avoid circular imports
        from .framework import get_error_context

        self.context = context or get_error_context()
        self.original_exception = original_exception

    def to_error_detail(self) -> "ErrorDetail":
        """Convert to ErrorDetail model."""
        # Import here to avoid circular imports
        from .framework import ErrorDetail

        return ErrorDetail(
            code=self.code,
            message=str(self),
            category=self.category,
            severity=self.severity,
            details=self.details,
            trace_id=getattr(self.context, "trace_id", None),
        )

    def to_result(self):
        """Convert to a Failure result."""
        # Import here to avoid circular imports
        from .result import Result

        return Result.failure(
            str(self),
            error_code=self.code,
            details=self.details,
        )

    def with_context(self, context: "ErrorContext") -> "FrameworkError":
        """Create a new instance with updated context."""
        return self.__class__(
            message=str(self),
            code=self.code,
            details=self.details,
            category=self.category,
            severity=self.severity,
            http_status_code=self.http_status_code,
            context=context,
            original_exception=self.original_exception,
        )


# Specific error types
class ValidationError(FrameworkError):
    """Error raised when validation fails."""

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a validation error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            field: Field that failed validation
            **kwargs: Additional error properties
        """
        details = details or {}
        if field:
            details["field"] = field

        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.VALIDATION,
            **kwargs,
        )
        self.field = field


class DatabaseError(FrameworkError):
    """Error raised for database-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize a database error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            **kwargs: Additional error properties
        """
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.DATABASE,
            **kwargs,
        )


class AuthenticationError(FrameworkError):
    """Error raised for authentication failures."""

    def __init__(
        self,
        message: str,
        code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize an authentication error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            **kwargs: Additional error properties
        """
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.AUTHENTICATION,
            **kwargs,
        )


class AuthorizationError(FrameworkError):
    """Error raised for authorization failures."""

    def __init__(
        self,
        message: str,
        code: str = "AUTHORIZATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize an authorization error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            **kwargs: Additional error properties
        """
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.AUTHORIZATION,
            **kwargs,
        )


class ResourceNotFoundError(FrameworkError):
    """Error raised when a resource is not found."""

    def __init__(
        self,
        message: str,
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.RESOURCE,
            **kwargs,
        )


class ConflictError(FrameworkError):
    """Error raised when a conflict occurs (e.g., duplicate key)."""

    def __init__(
        self,
        message: str,
        code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize a conflict error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            **kwargs: Additional error properties
        """
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.RESOURCE,
            **kwargs,
        )


class RateLimitError(FrameworkError):
    """Error raised when a rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize a rate limit error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            **kwargs: Additional error properties
        """
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.RESOURCE,
            **kwargs,
        )


class ServerError(FrameworkError):
    """Error raised for server-side issues."""

    def __init__(
        self,
        message: str,
        code: str = "SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize a server error.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
            **kwargs: Additional error properties
        """
        super().__init__(
            message=message,
            code=code,
            details=details,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            **kwargs,
        )
