# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Comprehensive error handling system for the Uno framework.

This module provides a cohesive approach to error handling with:
1. Structured exceptions with error codes (UnoError)
2. Functional error handling with Result objects (Success/Failure)
3. Contextual information for rich error diagnostics
4. Error catalog for consistent error documentation
5. Validation utilities for input validation
"""

# Import core components
from uno.core.errors.base import (
    UnoError,
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
    get_error_context,
    add_error_context,
    with_error_context,
    with_async_error_context,
    ValidationError,
    EntityNotFoundError,
    AuthorizationError,
    DatabaseError,
    ConfigurationError,
    DependencyError,
)

# Import Result pattern components
from uno.core.errors.result import (
    Result,
    Success,
    Failure,
    success,
    failure,
    from_exception,
    from_awaitable,
    combine,
    combine_dict,
)

# Import validation components
from uno.core.errors.validation import (
    ValidationContext,
    validate_fields,
)

# Initialize the error catalog (automatically registers standard errors)
from uno.core.errors.catalog import ErrorCatalog

# Initialize error catalog with standard errors
ErrorCatalog.initialize()

__all__ = [
    # Base error components
    "UnoError",
    "ErrorCode",
    "ErrorCategory",
    "ErrorSeverity",
    "get_error_context",
    "add_error_context",
    "with_error_context",
    "with_async_error_context",
    
    # Common error types
    "ValidationError",
    "EntityNotFoundError",
    "AuthorizationError",
    "DatabaseError",
    "ConfigurationError",
    "DependencyError",
    
    # Result pattern
    "Result",
    "Success",
    "Failure",
    "success",
    "failure",
    "from_exception",
    "from_awaitable",
    "combine",
    "combine_dict",
    
    # Validation
    "ValidationContext",
    "validate_fields",
    
    # Error catalog
    "ErrorCatalog",
]