# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error catalog for the Uno framework.

This module maintains a registry of all error codes with their
descriptions, categories, and other metadata.
"""

from typing import Dict, List, Optional
from uno.core.errors.base import ErrorInfo, ErrorCategory, ErrorSeverity

# Global registry of error codes
_ERROR_CATALOG: Dict[str, ErrorInfo] = {}


def register_error(
    code: str,
    message_template: str,
    category: ErrorCategory,
    severity: ErrorSeverity,
    description: str,
    http_status_code: Optional[int] = None,
    retry_allowed: bool = True,
) -> None:
    """
    Register an error code in the catalog.

    Args:
        code: The error code (e.g., "DB-0001")
        message_template: A template for error messages with this code
        category: The error category
        severity: The error severity
        description: A detailed description of the error
        http_status_code: The HTTP status code for this error (optional)
        retry_allowed: Whether retry is allowed for this error (default True)

    Raises:
        ValueError: If the error code is already registered
    """
    if code in _ERROR_CATALOG:
        raise ValueError(f"Error code {code} is already registered")

    _ERROR_CATALOG[code] = ErrorInfo(
        code=code,
        message_template=message_template,
        category=category,
        severity=severity,
        description=description,
        http_status_code=http_status_code,
        retry_allowed=retry_allowed,
    )


def get_error_code_info(code: str) -> Optional[ErrorInfo]:
    """
    Get information about an error code.

    Args:
        code: The error code

    Returns:
        ErrorInfo for the code, or None if not found
    """
    return _ERROR_CATALOG.get(code)


def get_all_error_codes() -> List[ErrorInfo]:
    """
    Get all registered error codes.

    Returns:
        A list of all ErrorInfo objects
    """
    return list(_ERROR_CATALOG.values())


class ErrorCatalog:
    """
    Interface to the error catalog.

    This class provides methods for working with the error catalog
    and initializing standard error codes.
    """

    @staticmethod
    def initialize() -> None:
        """
        Initialize the error catalog with standard error codes.

        This method registers all standard error codes defined in the
        system. It should be called during application startup.
        """
        # Core error codes
        register_error(
            code="CORE-0001",
            message_template="Unknown error occurred: {message}",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            description="An unexpected error occurred that doesn't match any known error type",
            http_status_code=500,
        )

        register_error(
            code="CORE-0002",
            message_template="Validation error: {message}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            description="Input validation failed",
            http_status_code=400,
            retry_allowed=True,
        )

        register_error(
            code="CORE-0003",
            message_template="Authorization error: {message}",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.ERROR,
            description="User does not have permission to perform the requested action",
            http_status_code=403,
            retry_allowed=False,
        )

        register_error(
            code="CORE-0004",
            message_template="Authentication error: {message}",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.ERROR,
            description="User authentication failed",
            http_status_code=401,
            retry_allowed=True,
        )

        register_error(
            code="CORE-0005",
            message_template="Resource not found: {resource}",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            description="The requested resource could not be found",
            http_status_code=404,
            retry_allowed=False,
        )

        register_error(
            code="CORE-0006",
            message_template="Resource conflict: {message}",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            description="The request conflicts with the current state of the resource",
            http_status_code=409,
            retry_allowed=False,
        )

        register_error(
            code="CORE-0007",
            message_template="Internal server error: {message}",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            description="An unexpected internal error occurred",
            http_status_code=500,
            retry_allowed=True,
        )

        register_error(
            code="CORE-0008",
            message_template="Configuration error: {message}",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            description="System is improperly configured",
            http_status_code=500,
            retry_allowed=False,
        )

        register_error(
            code="CORE-0009",
            message_template="Dependency error: {message}",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            description="A required dependency is unavailable",
            http_status_code=500,
            retry_allowed=True,
        )

        register_error(
            code="CORE-0010",
            message_template="Timeout error: {message}",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            description="Operation timed out",
            http_status_code=504,
            retry_allowed=True,
        )

        # Database error codes
        register_error(
            code="DB-0001",
            message_template="Database connection error: {message}",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.CRITICAL,
            description="Failed to connect to the database",
            http_status_code=503,
            retry_allowed=True,
        )

        register_error(
            code="DB-0002",
            message_template="Database query error: {message}",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            description="Error executing database query",
            http_status_code=500,
            retry_allowed=True,
        )

        register_error(
            code="DB-0003",
            message_template="Database integrity error: {message}",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            description="Database integrity constraint violation",
            http_status_code=409,
            retry_allowed=False,
        )

        register_error(
            code="DB-0004",
            message_template="Database transaction error: {message}",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            description="Error in database transaction",
            http_status_code=500,
            retry_allowed=True,
        )

        register_error(
            code="DB-0005",
            message_template="Database deadlock error: {message}",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            description="Database deadlock detected",
            http_status_code=409,
            retry_allowed=True,
        )

        # API error codes
        register_error(
            code="API-0001",
            message_template="API request error: {message}",
            category=ErrorCategory.INTEGRATION,
            severity=ErrorSeverity.ERROR,
            description="Error in API request",
            http_status_code=400,
            retry_allowed=True,
        )

        register_error(
            code="API-0002",
            message_template="API response error: {message}",
            category=ErrorCategory.INTEGRATION,
            severity=ErrorSeverity.ERROR,
            description="Error in API response",
            http_status_code=502,
            retry_allowed=True,
        )

        register_error(
            code="API-0003",
            message_template="API rate limit error: {message}",
            category=ErrorCategory.INTEGRATION,
            severity=ErrorSeverity.ERROR,
            description="API rate limit exceeded",
            http_status_code=429,
            retry_allowed=True,
        )

        register_error(
            code="API-0004",
            message_template="API integration error: {message}",
            category=ErrorCategory.INTEGRATION,
            severity=ErrorSeverity.ERROR,
            description="Error integrating with external API",
            http_status_code=502,
            retry_allowed=True,
        )

        register_error(
            code="FILTER-0001",
            message_template="Filter error: {message}",
            category=ErrorCategory.FILTER,
            severity=ErrorSeverity.ERROR,
            description="Error in filter expression",
            http_status_code=400,
            retry_allowed=True,
        )
