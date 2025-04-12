# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Base error classes and utilities for the Uno error handling framework.

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
ErrorContext = Dict[str, Any]

# Thread-local storage for error context
_error_context = contextvars.ContextVar[ErrorContext]("error_context", default={})


def get_error_context() -> ErrorContext:
    """
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


def with_error_context(func: Callable) -> Callable:
    """
    Decorator that adds function parameters to error context.
    
    This decorator adds the function parameters to the error context
    when the function is called, and removes them when the function returns.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get the signature of the function
        sig = inspect.signature(func)
        
        # Bind the arguments to the signature
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        # Get the current context
        current_context = _error_context.get().copy()
        
        # Create a new context with function parameters
        new_context = current_context.copy()
        new_context.update(bound.arguments)
        
        # Set the new context
        token = _error_context.set(new_context)
        
        try:
            return func(*args, **kwargs)
        finally:
            # Restore the previous context
            _error_context.reset(token)
    
    return wrapper


class ErrorCategory(Enum):
    """
    Categories of errors for classification.
    
    These categories help classify errors for appropriate handling
    and reporting.
    """
    
    VALIDATION = auto()      # Input validation errors
    BUSINESS_RULE = auto()   # Business rule violations
    AUTHORIZATION = auto()   # Permission/authorization errors
    AUTHENTICATION = auto()  # Login/identity errors
    DATABASE = auto()        # Database-related errors
    NETWORK = auto()         # Network/connectivity errors
    RESOURCE = auto()        # Resource availability errors
    CONFIGURATION = auto()   # System configuration errors
    INTEGRATION = auto()     # External system integration errors
    INTERNAL = auto()        # Unexpected internal errors
    

class ErrorSeverity(Enum):
    """
    Severity levels for errors.
    
    These severity levels help prioritize error handling and reporting.
    """
    
    INFO = auto()       # Informational message, not an error
    WARNING = auto()    # Warning that might need attention
    ERROR = auto()      # Error that affects operation but not critical
    CRITICAL = auto()   # Critical error that prevents core functionality
    FATAL = auto()      # Fatal error that requires system shutdown


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
    http_status_code: Optional[int] = None
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


class UnoError(Exception):
    """
    Base class for all Uno framework errors.
    
    This class provides standardized error formatting with error codes,
    contextual information, and stacktrace capture.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str, 
        **context: Any
    ):
        """
        Initialize a UnoError.
        
        Args:
            message: The error message
            error_code: A code identifying the error type
            **context: Additional context information
        """
        super().__init__(message)
        self.message: str = message
        self.error_code: str = error_code
        
        # Combine the explicit context with the ambient context
        self.context: Dict[str, Any] = get_error_context().copy()
        self.context.update(context)
        
        # Capture stack trace information
        self.traceback: str = ''.join(traceback.format_exception(*traceback.sys.exc_info()))
        
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
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            A dictionary representation of the error
        """
        result = {
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
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