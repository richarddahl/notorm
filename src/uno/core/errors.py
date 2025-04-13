"""
Error handling for the Uno framework.

This module provides a comprehensive error handling system that combines
the best aspects of exceptions with the explicitness of the Result pattern.
It includes rich domain errors with context, categorization, and consistent
error handling patterns.
"""

from enum import Enum, auto
from typing import Any, ClassVar, Self, TypeVar, Generic, Callable, TypeGuard, cast, overload
import traceback
import functools
import inspect
import sys
from datetime import datetime
import contextvars
import json


# =============================================================================
# Error Categories
# =============================================================================

class ErrorCategory(Enum):
    """
    Categories of errors for grouping and handling.
    
    These categories help organize errors by their nature and allow for
    consistent handling strategies based on category.
    """
    
    VALIDATION = auto()    # Input validation errors
    BUSINESS_RULE = auto() # Business rule violations
    NOT_FOUND = auto()     # Resource not found errors
    CONFLICT = auto()      # Resource conflicts (e.g., uniqueness violations)
    AUTHORIZATION = auto() # Permission/authorization errors
    INFRASTRUCTURE = auto() # External system/infrastructure errors
    DATABASE = auto()      # Database-specific errors
    TIMEOUT = auto()       # Timeout errors
    UNEXPECTED = auto()    # Unexpected/unhandled errors


# =============================================================================
# Domain Error Classes
# =============================================================================

class DomainError(Exception):
    """
    Base class for all domain-specific errors.
    
    DomainError provides a rich error model with error codes, categories,
    and additional context to help with debugging and client responses.
    """
    
    def __init__(
        self,
        message: str,
        code: str,
        category: ErrorCategory = ErrorCategory.UNEXPECTED,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        capture_traceback: bool = True,
    ):
        """
        Initialize a domain error.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            category: Error category for grouping
            details: Additional error details
            cause: Original exception that caused this error
            capture_traceback: Whether to capture a traceback
        """
        self.code = code
        self.category = category
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        
        # Capture traceback if requested
        self.traceback = traceback.format_exc() if capture_traceback else None
        
        # Set message and call parent constructor
        super().__init__(message)
    
    @classmethod
    def from_exception(
        cls, 
        exception: Exception, 
        code: str | None = None, 
        category: ErrorCategory | None = None,
        message: str | None = None,
    ) -> Self:
        """
        Create a domain error from another exception.
        
        Args:
            exception: Original exception
            code: Machine-readable error code (defaults to exception class name)
            category: Error category (defaults to UNEXPECTED)
            message: Custom message (defaults to exception message)
            
        Returns:
            A new domain error
        """
        # Default code to exception class name if not provided
        if code is None:
            code = exception.__class__.__name__.upper()
        
        # Default category to UNEXPECTED if not provided
        if category is None:
            category = ErrorCategory.UNEXPECTED
        
        # Default message to exception message if not provided
        if message is None:
            message = str(exception)
        
        return cls(
            message=message,
            code=code,
            category=category,
            cause=exception
        )
    
    def with_detail(self, key: str, value: Any) -> Self:
        """
        Add a detail to this error.
        
        Args:
            key: Detail key
            value: Detail value
            
        Returns:
            Self for method chaining
        """
        self.details[key] = value
        return self
    
    def with_details(self, details: dict[str, Any]) -> Self:
        """
        Add multiple details to this error.
        
        Args:
            details: Dictionary of details to add
            
        Returns:
            Self for method chaining
        """
        self.details.update(details)
        return self
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert error to dictionary representation.
        
        Returns:
            Dictionary representation of the error
        """
        result = {
            "message": str(self),
            "code": self.code,
            "category": self.category.name,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.details:
            result["details"] = {k: self._serialize_value(v) for k, v in self.details.items()}
            
        if self.cause:
            result["cause"] = str(self.cause)
            
        return result
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a value for inclusion in error details.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value
        """
        if hasattr(value, "to_dict") and callable(value.to_dict):
            return value.to_dict()
        
        if isinstance(value, (datetime, Enum)):
            return str(value)
        
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        
        if isinstance(value, (list, tuple, set)):
            return [self._serialize_value(v) for v in value]
        
        return value
    
    def __str__(self) -> str:
        """String representation of the error."""
        return super().__str__()


class ValidationError(DomainError):
    """
    Error indicating a validation failure.
    
    ValidationError includes field-specific error messages to help clients
    understand exactly what validation rules were violated.
    """
    
    def __init__(
        self,
        message: str,
        field_errors: dict[str, list[str]] | None = None,
        code: str = "VALIDATION_ERROR",
    ):
        """
        Initialize a validation error.
        
        Args:
            message: Human-readable error message
            field_errors: Map of field names to error messages
            code: Machine-readable error code
        """
        details = {"field_errors": field_errors or {}}
        
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            details=details,
        )
    
    @property
    def field_errors(self) -> dict[str, list[str]]:
        """Get the field errors."""
        return self.details.get("field_errors", {})
    
    def add_field_error(self, field: str, message: str) -> Self:
        """
        Add a field error.
        
        Args:
            field: Field name
            message: Error message
            
        Returns:
            Self for method chaining
        """
        field_errors = self.details.setdefault("field_errors", {})
        
        if field not in field_errors:
            field_errors[field] = []
            
        field_errors[field].append(message)
        return self
    
    @classmethod
    def from_pydantic_error(cls, error: Exception) -> Self:
        """
        Create validation error from a Pydantic validation error.
        
        Args:
            error: Pydantic validation error
            
        Returns:
            Validation error with field errors from Pydantic
        """
        # Extract field errors from Pydantic error
        field_errors: dict[str, list[str]] = {}
        
        # Pydantic V1 and V2 have different error structures
        if hasattr(error, "errors"):
            # Pydantic V2
            for err in getattr(error, "errors")():
                loc = ".".join(str(loc_part) for loc_part in err["loc"])
                msg = err["msg"]
                
                if loc not in field_errors:
                    field_errors[loc] = []
                field_errors[loc].append(msg)
        elif hasattr(error, "error_dict"):
            # Pydantic V1
            for field, errors in getattr(error, "error_dict").items():
                field_str = ".".join(str(f) for f in field)
                if field_str not in field_errors:
                    field_errors[field_str] = []
                
                for err in errors:
                    field_errors[field_str].append(err["msg"])
        
        return cls(
            message=str(error),
            field_errors=field_errors,
        )


class NotFoundError(DomainError):
    """
    Error indicating a resource was not found.
    
    NotFoundError includes information about the resource type and identifier
    that was not found.
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        message: str | None = None,
        code: str = "NOT_FOUND",
    ):
        """
        Initialize a not found error.
        
        Args:
            resource_type: Type of resource that wasn't found
            resource_id: ID of the resource
            message: Optional custom message
            code: Machine-readable error code
        """
        if message is None:
            message = f"{resource_type} with ID {resource_id} not found"
            
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.NOT_FOUND,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class BusinessRuleError(DomainError):
    """
    Error indicating a business rule violation.
    
    BusinessRuleError represents violations of business rules or invariants
    that prevent an operation from completing.
    """
    
    def __init__(
        self,
        message: str,
        rule: str,
        code: str = "BUSINESS_RULE_VIOLATION",
    ):
        """
        Initialize a business rule error.
        
        Args:
            message: Human-readable error message
            rule: Name of the business rule that was violated
            code: Machine-readable error code
        """
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.BUSINESS_RULE,
            details={"rule": rule}
        )


class ConflictError(DomainError):
    """
    Error indicating a resource conflict.
    
    ConflictError represents situations where an operation cannot be
    completed due to a conflict with the current state of a resource.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        conflict_reason: str,
        code: str = "CONFLICT",
    ):
        """
        Initialize a conflict error.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource with the conflict
            conflict_reason: Reason for the conflict
            code: Machine-readable error code
        """
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.CONFLICT,
            details={
                "resource_type": resource_type,
                "conflict_reason": conflict_reason
            }
        )


class AuthorizationError(DomainError):
    """
    Error indicating an authorization failure.
    
    AuthorizationError represents situations where a user lacks the
    necessary permissions to perform an operation.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: Any = None,
        permission: str | None = None,
        code: str = "AUTHORIZATION_ERROR",
    ):
        """
        Initialize an authorization error.
        
        Args:
            message: Human-readable error message
            resource_type: Optional type of resource access was denied for
            resource_id: Optional ID of resource access was denied for
            permission: Optional permission that was denied
            code: Machine-readable error code
        """
        details = {}
        
        if resource_type is not None:
            details["resource_type"] = resource_type
            
        if resource_id is not None:
            details["resource_id"] = resource_id
            
        if permission is not None:
            details["permission"] = permission
            
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHORIZATION,
            details=details
        )


# =============================================================================
# Type Guards
# =============================================================================

def is_validation_error(error: Exception) -> TypeGuard[ValidationError]:
    """
    Type guard to check if an error is a validation error.
    
    Args:
        error: The error to check
        
    Returns:
        True if the error is a validation error
    """
    return isinstance(error, ValidationError)


def is_not_found_error(error: Exception) -> TypeGuard[NotFoundError]:
    """
    Type guard to check if an error is a not found error.
    
    Args:
        error: The error to check
        
    Returns:
        True if the error is a not found error
    """
    return isinstance(error, NotFoundError)


def is_business_rule_error(error: Exception) -> TypeGuard[BusinessRuleError]:
    """
    Type guard to check if an error is a business rule error.
    
    Args:
        error: The error to check
        
    Returns:
        True if the error is a business rule error
    """
    return isinstance(error, BusinessRuleError)


def is_conflict_error(error: Exception) -> TypeGuard[ConflictError]:
    """
    Type guard to check if an error is a conflict error.
    
    Args:
        error: The error to check
        
    Returns:
        True if the error is a conflict error
    """
    return isinstance(error, ConflictError)


def is_authorization_error(error: Exception) -> TypeGuard[AuthorizationError]:
    """
    Type guard to check if an error is an authorization error.
    
    Args:
        error: The error to check
        
    Returns:
        True if the error is an authorization error
    """
    return isinstance(error, AuthorizationError)


def is_domain_error(error: Exception) -> TypeGuard[DomainError]:
    """
    Type guard to check if an error is a domain error.
    
    Args:
        error: The error to check
        
    Returns:
        True if the error is a domain error
    """
    return isinstance(error, DomainError)


# =============================================================================
# Result Pattern Implementation
# =============================================================================

T = TypeVar("T")
E = TypeVar("E", bound=Exception)
U = TypeVar("U")

# Current error context
error_context = contextvars.ContextVar[dict[str, Any]]("error_context", default={})


class Success[T]:
    """
    Represents a successful operation result.
    
    Success wraps a value that resulted from a successful operation.
    
    Type Parameters:
        T: The type of the success value
    """
    
    __slots__ = ("_value",)
    
    def __init__(self, value: T):
        """
        Initialize a success result.
        
        Args:
            value: The success value
        """
        self._value = value
    
    @property
    def is_success(self) -> bool:
        """Check if this result is a success."""
        return True
    
    @property
    def is_failure(self) -> bool:
        """Check if this result is a failure."""
        return False
    
    @property
    def value(self) -> T:
        """Get the success value."""
        return self._value
    
    @property
    def error(self) -> None:
        """Get the error (always None for Success)."""
        return None
    
    def map[U](self, func: Callable[[T], U]) -> "Success[U] | Failure[U]":
        """
        Map the success value using a function.
        
        Args:
            func: Function to apply to the success value
            
        Returns:
            New Success with the transformed value, or Failure if the function raises
        """
        try:
            return Success(func(self._value))
        except Exception as e:
            # Add context to the error
            current_context = error_context.get()
            
            if is_domain_error(e):
                # Add context to domain error
                if current_context:
                    e.with_details(current_context)
                return Failure(e)
            
            # Wrap other exceptions in DomainError
            return Failure(DomainError.from_exception(e).with_details(current_context))
    
    def flat_map[U](self, func: Callable[[T], "Result[U]"]) -> "Result[U]":
        """
        Apply a function that itself returns a Result.
        
        Args:
            func: Function to apply to the success value
            
        Returns:
            The Result returned by the function, or Failure if the function raises
        """
        try:
            return func(self._value)
        except Exception as e:
            # Add context to the error
            current_context = error_context.get()
            
            if is_domain_error(e):
                # Add context to domain error
                if current_context:
                    e.with_details(current_context)
                return Failure(e)
            
            # Wrap other exceptions in DomainError
            return Failure(DomainError.from_exception(e).with_details(current_context))
    
    def __repr__(self) -> str:
        """Get a string representation of this Success."""
        return f"Success({repr(self._value)})"


class Failure[T]:
    """
    Represents a failed operation result.
    
    Failure wraps an error that occurred during an operation.
    
    Type Parameters:
        T: The type that would have been returned on success
    """
    
    __slots__ = ("_error",)
    
    def __init__(self, error: Exception):
        """
        Initialize a failure result.
        
        Args:
            error: The error that caused the failure
        """
        self._error = error
    
    @property
    def is_success(self) -> bool:
        """Check if this result is a success."""
        return False
    
    @property
    def is_failure(self) -> bool:
        """Check if this result is a failure."""
        return True
    
    @property
    def value(self) -> None:
        """Get the success value (always None for Failure)."""
        return None
    
    @property
    def error(self) -> Exception:
        """Get the error."""
        return self._error
    
    def map[U](self, func: Callable[[T], U]) -> "Failure[U]":
        """
        Map the success value using a function.
        
        Args:
            func: Function to apply to the success value
            
        Returns:
            This Failure (unchanged)
        """
        return cast(Failure[U], self)
    
    def flat_map[U](self, func: Callable[[T], "Result[U]"]) -> "Failure[U]":
        """
        Apply a function that itself returns a Result.
        
        Args:
            func: Function to apply to the success value
            
        Returns:
            This Failure (unchanged)
        """
        return cast(Failure[U], self)
    
    def __repr__(self) -> str:
        """Get a string representation of this Failure."""
        return f"Failure({repr(self._error)})"


# Type alias for the Result pattern
Result = Success[T] | Failure[T]


# =============================================================================
# Result Pattern Helpers
# =============================================================================

def success[T](value: T) -> Success[T]:
    """
    Create a success result.
    
    Args:
        value: The success value
        
    Returns:
        A Success result
    """
    return Success(value)


def failure[T](error: Exception) -> Failure[T]:
    """
    Create a failure result.
    
    Args:
        error: The error
        
    Returns:
        A Failure result
    """
    return Failure(error)


async def from_awaitable[T](awaitable: Any) -> Result[T]:
    """
    Convert an awaitable to a Result.
    
    Args:
        awaitable: The awaitable to convert
        
    Returns:
        Success with the awaitable's result or Failure with the exception
    """
    try:
        return Success(await awaitable)
    except Exception as e:
        # Add context to the error
        current_context = error_context.get()
        
        if is_domain_error(e):
            # Add context to domain error
            if current_context:
                e.with_details(current_context)
            return Failure(e)
        
        # Wrap other exceptions in DomainError
        return Failure(DomainError.from_exception(e).with_details(current_context))


def from_callable[T](func: Callable[..., T]) -> Callable[..., Result[T]]:
    """
    Convert a function to one that returns a Result.
    
    Args:
        func: The function to convert
        
    Returns:
        A function that returns a Result
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Result[T]:
        try:
            return Success(func(*args, **kwargs))
        except Exception as e:
            # Add context to the error
            current_context = error_context.get()
            
            if is_domain_error(e):
                # Add context to domain error
                if current_context:
                    e.with_details(current_context)
                return Failure(e)
            
            # Wrap other exceptions in DomainError
            return Failure(DomainError.from_exception(e).with_details(current_context))
    
    return wrapper


async def from_async_callable[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[Result[T]]]:
    """
    Convert an async function to one that returns a Result.
    
    Args:
        func: The async function to convert
        
    Returns:
        An async function that returns a Result
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Result[T]:
        try:
            return Success(await func(*args, **kwargs))
        except Exception as e:
            # Add context to the error
            current_context = error_context.get()
            
            if is_domain_error(e):
                # Add context to domain error
                if current_context:
                    e.with_details(current_context)
                return Failure(e)
            
            # Wrap other exceptions in DomainError
            return Failure(DomainError.from_exception(e).with_details(current_context))
    
    return wrapper


@contextmanager
def error_context_manager(**context: Any):
    """
    Context manager for adding context to errors.
    
    Args:
        **context: Context key-value pairs
    """
    # Get current context
    current_context = error_context.get().copy()
    
    # Update with new context
    current_context.update(context)
    
    # Set new context
    token = error_context.set(current_context)
    
    try:
        yield
    finally:
        # Restore previous context
        error_context.reset(token)


def with_error_context(**context: Any):
    """
    Decorator for adding context to errors.
    
    Args:
        **context: Context key-value pairs
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with error_context_manager(**context):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def with_async_error_context(**context: Any):
    """
    Decorator for adding context to errors in async functions.
    
    Args:
        **context: Context key-value pairs
        
    Returns:
        Decorated async function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with error_context_manager(**context):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator