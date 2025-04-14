# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Comprehensive error handling framework for the Uno application.

This module provides a unified approach to error handling with
structured errors, error codes, contextual information, and
integration with both exception-based and functional error handling.
"""

from uno.core.errors.base import (
    UnoError,
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorInfo,
    with_error_context,
    with_async_error_context,
    add_error_context,
    get_error_context,
    EntityNotFoundError,
    ConcurrencyError,
    DomainValidationError,
    AggregateInvariantViolationError,
)

from uno.core.errors.catalog import (
    ErrorCatalog,
    register_error,
    get_error_code_info,
    get_all_error_codes,
)

from uno.core.errors.result import (
    Result,
    Success,
    Failure,
    of,
    failure,
    from_exception,
    from_awaitable,
    combine,
    combine_dict,
)

from uno.core.errors.validation import (
    ValidationError,
    ValidationContext,
    FieldValidationError,
    validate_fields,
)

from uno.core.errors.logging import (
    configure_logging,
    get_logger,
    LogConfig,
    with_logging_context,
    add_logging_context,
    get_logging_context,
    clear_logging_context,
)

from uno.core.errors.security import (
    AuthenticationError,
    AuthorizationError,
)

from uno.core.errors.core_errors import (
    CoreErrorCode,
    ConfigNotFoundError,
    ConfigInvalidError,
    ConfigTypeMismatchError,
    InitializationError,
    ComponentInitializationError,
    DependencyNotFoundError,
    DependencyResolutionError,
    DependencyCycleError,
    ObjectNotFoundError,
    ObjectInvalidError,
    ObjectPropertyError,
    SerializationError,
    DeserializationError,
    ProtocolValidationError,
    InterfaceMethodError,
    OperationFailedError,
    NotImplementedError as UnoNotImplementedError,
    InternalError,
    register_core_errors,
)

# Register core errors
register_core_errors()

__all__ = [
    # Base errors
    "UnoError",
    "ErrorCode",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorContext",
    "ErrorInfo",
    "with_error_context",
    "with_async_error_context",
    "add_error_context",
    "get_error_context",
    "EntityNotFoundError",
    "ConcurrencyError",
    "DomainValidationError",
    "AggregateInvariantViolationError",
    
    # Error catalog
    "ErrorCatalog",
    "register_error",
    "get_error_code_info",
    "get_all_error_codes",
    
    # Result pattern
    "Result",
    "Success",
    "Failure",
    "of",
    "failure",
    "from_exception",
    "from_awaitable",
    "combine",
    "combine_dict",
    
    # Validation
    "ValidationError",
    "ValidationContext",
    "FieldValidationError",
    "validate_fields",
    
    # Logging
    "configure_logging",
    "get_logger",
    "LogConfig",
    "with_logging_context",
    "add_logging_context",
    "get_logging_context",
    "clear_logging_context",
    
    # Security
    "AuthenticationError",
    "AuthorizationError",
    
    # Core errors
    "CoreErrorCode",
    "ConfigNotFoundError",
    "ConfigInvalidError", 
    "ConfigTypeMismatchError",
    "InitializationError",
    "ComponentInitializationError",
    "DependencyNotFoundError",
    "DependencyResolutionError",
    "DependencyCycleError",
    "ObjectNotFoundError",
    "ObjectInvalidError",
    "ObjectPropertyError",
    "SerializationError",
    "DeserializationError",
    "ProtocolValidationError",
    "InterfaceMethodError",
    "OperationFailedError",
    "UnoNotImplementedError",
    "InternalError",
]