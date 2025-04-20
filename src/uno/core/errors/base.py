# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Base error classes and utilities for the Uno framework.

This module provides the foundation for structured error handling with
error codes, contextual information, and error categories.
"""

from typing import Any, Dict, Optional, Type, TypeVar, cast, Callable
import functools
import inspect
import traceback
import contextvars
from dataclasses import dataclass
from enum import Enum, auto

# Type for error context dict
ErrorContext = dict[str, Any]

# Thread-local storage for error context
_error_context = contextvars.ContextVar[ErrorContext]("error_context", default={})


def get_error_context() -> ErrorContext:
    """
    from uno.core.base.error import BaseError
        Get the current error context.

        Returns:
            The current error context dictionary
    """
    return _error_context.get().copy()


def add_error_context(**context: Any) -> None:
    """
    Add key-value pairs to the current error context.

    Args:
        **context: Key-value pairs to add to the context
    """
    current = _error_context.get().copy()
    current.update(context)
    _error_context.set(current)


class _ErrorContextManager:
    """Context manager for error context."""

    def __init__(self, **context_kwargs: Any):
        """Initialize with context key-value pairs."""
        self.context_kwargs = context_kwargs
        self.token = None

    def __enter__(self):
        """Enter the error context, updating the current context."""
        current_context = _error_context.get().copy()
        new_context = current_context.copy()
        new_context.update(self.context_kwargs)
        self.token = _error_context.set(new_context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the error context, restoring the previous context."""
        if self.token is not None:
            _error_context.reset(self.token)


def with_error_context(*args, **kwargs) -> Any:
    """
    Decorator or context manager for adding context to errors.

    Can be used as:
    1. Decorator: @with_error_context
    2. Context manager: with with_error_context(key=value):

    Args:
        *args: Function to decorate (if used as decorator)
        **kwargs: Key-value pairs to add to the context (if used as context manager)

    Returns:
        Decorated function or context manager
    """
    # If used as a decorator (no kwargs and one positional arg which is callable)
    if kwargs == {} and len(args) == 1 and callable(args[0]):
        func = args[0]

        @functools.wraps(func)
        def wrapper(*f_args: Any, **f_kwargs: Any) -> Any:
            # Get the signature of the function
            sig = inspect.signature(func)

            # Bind the arguments to the signature
            bound = sig.bind(*f_args, **f_kwargs)
            bound.apply_defaults()

            # Use the context manager
            with _ErrorContextManager(**bound.arguments):
                return func(*f_args, **f_kwargs)

        return wrapper

    # If used as a context manager
    return _ErrorContextManager(**kwargs)


class _AsyncErrorContextManager:
    """Async context manager for error context."""

    def __init__(self, **context_kwargs: Any):
        """Initialize with context key-value pairs."""
        self.context_kwargs = context_kwargs
        self.token = None

    async def __aenter__(self):
        """Enter the error context, updating the current context."""
        current_context = _error_context.get().copy()
        new_context = current_context.copy()
        new_context.update(self.context_kwargs)
        self.token = _error_context.set(new_context)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the error context, restoring the previous context."""
        if self.token is not None:
            _error_context.reset(self.token)


def with_async_error_context(*args, **kwargs) -> Any:
    """
    Decorator or async context manager for adding context to errors.

    Can be used as:
    1. Decorator: @with_async_error_context
    2. Async context manager: async with with_async_error_context(key=value):

    Args:
        *args: Function to decorate (if used as decorator)
        **kwargs: Key-value pairs to add to the context (if used as context manager)

    Returns:
        Decorated async function or async context manager
    """
    # If used as a decorator (no kwargs and one positional arg which is callable)
    if kwargs == {} and len(args) == 1 and callable(args[0]):
        func = args[0]

        @functools.wraps(func)
        async def wrapper(*f_args: Any, **f_kwargs: Any) -> Any:
            # Get the signature of the function
            sig = inspect.signature(func)

            # Bind the arguments to the signature
            bound = sig.bind(*f_args, **f_kwargs)
            bound.apply_defaults()

            # Use the async context manager
            async with _AsyncErrorContextManager(**bound.arguments):
                return await func(*f_args, **f_kwargs)

        return wrapper

    # If used as an async context manager
    return _AsyncErrorContextManager(**kwargs)


class ErrorCategory(Enum):
    """
    Categories of errors for classification.

    These categories help classify errors for appropriate handling
    and reporting.
    """

    VALIDATION = auto()  # Input validation errors
    BUSINESS_RULE = auto()  # Business rule violations
    AUTHORIZATION = auto()  # Permission/authorization errors
    AUTHENTICATION = auto()  # Login/identity errors
    DATABASE = auto()  # Database-related errors
    NETWORK = auto()  # Network/connectivity errors
    RESOURCE = auto()  # Resource availability errors
    CONFIGURATION = auto()  # System configuration errors
    INTEGRATION = auto()  # External system integration errors
    INTERNAL = auto()  # Unexpected internal errors
    INITIALIZATION = auto()  # Initialization errors
    SERIALIZATION = auto()  # Serialization/deserialization errors
    DEPENDENCY = auto()  # Dependency resolution errors
    EXECUTION = auto()  # Execution/processing errors
    SECURITY = auto()  # Security-related errors
    CONFLICT = auto()  # Resource conflicts
    NOT_FOUND = auto()  # Resource not found
    UNEXPECTED = auto()  # Unexpected errors
    FILTER = auto()  # Filtering errors


class ErrorSeverity(Enum):
    """
    Severity levels for errors.

    These severity levels help prioritize error handling and reporting.
    """

    INFO = auto()  # Informational message, not an error
    WARNING = auto()  # Warning that might need attention
    ERROR = auto()  # Error that affects operation but not critical
    CRITICAL = auto()  # Critical error that prevents core functionality
    FATAL = auto()  # Fatal error that requires system shutdown


@dataclass(frozen=True)
class ErrorInfo:
    """
    Information about an error code.

    This class stores metadata about error codes for documentation
    and consistent handling.
    """

    code: str
    message_template: str
    category: ErrorCategory
    severity: ErrorSeverity
    description: str
    http_status_code: int | None = None
    retry_allowed: bool = True


class ErrorCode:
    """
    Error code constants and utilities.

    This class provides standardized error codes and utilities
    for working with them.
    """

    # Core error codes
    UNKNOWN_ERROR = "CORE-0001"
    VALIDATION_ERROR = "CORE-0002"
    AUTHORIZATION_ERROR = "CORE-0003"
    AUTHENTICATION_ERROR = "CORE-0004"
    RESOURCE_NOT_FOUND = "CORE-0005"
    RESOURCE_CONFLICT = "CORE-0006"
    INTERNAL_ERROR = "CORE-0007"
    CONFIGURATION_ERROR = "CORE-0008"
    DEPENDENCY_ERROR = "CORE-0009"
    TIMEOUT_ERROR = "CORE-0010"

    # Database error codes
    DB_CONNECTION_ERROR = "DB-0001"
    DB_QUERY_ERROR = "DB-0002"
    DB_INTEGRITY_ERROR = "DB-0003"
    DB_TRANSACTION_ERROR = "DB-0004"
    DB_DEADLOCK_ERROR = "DB-0005"

    # API error codes
    API_REQUEST_ERROR = "API-0001"
    API_RESPONSE_ERROR = "API-0002"
    API_RATE_LIMIT_ERROR = "API-0003"
    API_INTEGRATION_ERROR = "API-0004"

    @staticmethod
    def is_valid(code: str) -> bool:
        """
        Check if an error code is valid.

        Args:
            code: The error code to check

        Returns:
            True if the code is valid, False otherwise
        """
        from uno.core.errors.catalog import get_error_code_info

        return get_error_code_info(code) is not None

    @staticmethod
    def get_http_status(code: str) -> int:
        """
        Get the HTTP status code for an error code.

        Args:
            code: The error code

        Returns:
            The HTTP status code (defaults to 500 if not specified)
        """
        from uno.core.errors.catalog import get_error_code_info

        info = get_error_code_info(code)
        return info.http_status_code if info and info.http_status_code else 500


class BaseError(Exception):
    """
    Base class for all Uno framework errors.

    This class provides standardized error formatting with error codes,
    contextual information, and stacktrace capture.
    """

    def __init__(self, message: str, error_code: str, **context: Any):
        """
        Initialize a BaseError.

        Args:
            message: The error message
            error_code: A code identifying the error type
            **context: Additional context information
        """
        super().__init__(message)
        self.message: str = message
        self.error_code: str = error_code

        # Combine the explicit context with the ambient context
        self.context: dict[str, Any] = get_error_context().copy()
        self.context.update(context)

        # Capture stack trace information
        self.traceback: str = "".join(
            traceback.format_exception(*traceback.sys.exc_info())
        )

        # Get error info from catalog if available
        from uno.core.errors.catalog import get_error_code_info

        self.error_info: Optional[ErrorInfo] = get_error_code_info(error_code)

    @property
    def category(self) -> Optional[ErrorCategory]:
        """
        Get the error category.

        Returns:
            The error category, or None if not available
        """
        return self.error_info.category if self.error_info else None

    @property
    def severity(self) -> Optional[ErrorSeverity]:
        """
        Get the error severity.

        Returns:
            The error severity, or None if not available
        """
        return self.error_info.severity if self.error_info else None

    @property
    def http_status_code(self) -> int:
        """
        Get the HTTP status code for this error.

        Returns:
            The HTTP status code (defaults to 500)
        """
        if self.error_info and self.error_info.http_status_code:
            return self.error_info.http_status_code
        return 500

    @property
    def retry_allowed(self) -> bool:
        """
        Check if retry is allowed for this error.

        Returns:
            True if retry is allowed, False otherwise
        """
        if self.error_info:
            return self.error_info.retry_allowed
        return True

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the error to a dictionary.

        Returns:
            A dictionary representation of the error
        """
        result = {
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }

        # Add additional information if available
        if self.category:
            result["category"] = self.category.name

        if self.severity:
            result["severity"] = self.severity.name

        return result

    def __str__(self) -> str:
        """
        String representation of the error.

        Returns:
            A string representation of the error
        """
        return f"{self.error_code}: {self.message}"


class ValidationError(BaseError):
    """Error raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Optional[Any] = None,
        validation_errors: Optional[list] = None,
        **context: Any,
    ):
        """
        Initialize a ValidationError.

        Args:
            message: The error message
            field: The field that failed validation
            value: The value that failed validation
            validation_errors: A list of validation errors
            **context: Additional context information
        """
        context_dict = context.copy()
        if field:
            context_dict["field"] = field
        if value is not None:
            context_dict["value"] = value

        super().__init__(
            message=message, error_code=ErrorCode.VALIDATION_ERROR, **context_dict
        )
        self.validation_errors = validation_errors or []

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the error to a dictionary.

        Returns:
            A dictionary representation of the error
        """
        result = super().to_dict()
        if self.validation_errors:
            result["validation_errors"] = self.validation_errors
        return result


class EntityNotFoundError(BaseError):
    """Error raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: Any, **context: Any):
        """
        Initialize an EntityNotFoundError.

        Args:
            entity_type: The type of entity that was not found
            entity_id: The ID of the entity that was not found
            **context: Additional context information
        """
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            entity_type=entity_type,
            entity_id=entity_id,
            **context,
        )


class AuthorizationError(BaseError):
    """Error raised when user is not authorized to perform an operation."""

    def __init__(
        self,
        message: str = "User is not authorized to perform this operation",
        resource_type: str | None = None,
        resource_id: Optional[Any] = None,
        permission: str | None = None,
        **context: Any,
    ):
        """
        Initialize an AuthorizationError.

        Args:
            message: The error message
            resource_type: The type of resource the user tried to access
            resource_id: The ID of the resource the user tried to access
            permission: The permission the user was missing
            **context: Additional context information
        """
        context_dict = context.copy()
        if resource_type:
            context_dict["resource_type"] = resource_type
        if resource_id:
            context_dict["resource_id"] = resource_id
        if permission:
            context_dict["permission"] = permission

        super().__init__(
            message=message, error_code=ErrorCode.AUTHORIZATION_ERROR, **context_dict
        )


class DatabaseError(BaseError):
    """Error raised for database-related issues."""

    def __init__(
        self,
        message: str,
        error_code: str = ErrorCode.DB_QUERY_ERROR,
        query: str | None = None,
        params: dict[str, Any] | None = None,
        **context: Any,
    ):
        """
        Initialize a DatabaseError.

        Args:
            message: The error message
            error_code: The database error code
            query: The SQL query that caused the error
            params: The parameters for the query
            **context: Additional context information
        """
        context_dict = context.copy()
        if query:
            context_dict["query"] = query
        if params:
            context_dict["params"] = params

        super().__init__(message=message, error_code=error_code, **context_dict)


class ConfigurationError(BaseError):
    """Error raised for configuration issues."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        **context: Any,
    ):
        """
        Initialize a ConfigurationError.

        Args:
            message: The error message
            config_key: The configuration key that caused the issue
            **context: Additional context information
        """
        context_dict = context.copy()
        if config_key:
            context_dict["config_key"] = config_key

        super().__init__(
            message=message, error_code=ErrorCode.CONFIGURATION_ERROR, **context_dict
        )


class DependencyError(BaseError):
    """Error raised for dependency resolution issues."""

    def __init__(
        self,
        message: str,
        dependency_name: str | None = None,
        **context: Any,
    ):
        """
        Initialize a DependencyError.

        Args:
            message: The error message
            dependency_name: The name of the dependency that couldn't be resolved
            **context: Additional context information
        """
        context_dict = context.copy()
        if dependency_name:
            context_dict["dependency_name"] = dependency_name

        super().__init__(
            message=message, error_code=ErrorCode.DEPENDENCY_ERROR, **context_dict
        )


class ConcurrencyError(BaseError):
    """Error raised when optimistic concurrency control fails."""

    def __init__(
        self,
        message: str,
        aggregate_id: str | None = None,
        expected_version: int | None = None,
        actual_version: int | None = None,
        **context: Any,
    ):
        """
        Initialize a ConcurrencyError.

        Args:
            message: The error message
            aggregate_id: The ID of the aggregate with version conflict
            expected_version: The version that was expected
            actual_version: The actual version found
            **context: Additional context information
        """
        context_dict = context.copy()
        if aggregate_id:
            context_dict["aggregate_id"] = aggregate_id
        if expected_version is not None:
            context_dict["expected_version"] = expected_version
        if actual_version is not None:
            context_dict["actual_version"] = actual_version

        super().__init__(
            message=message, error_code=ErrorCode.RESOURCE_CONFLICT, **context_dict
        )
