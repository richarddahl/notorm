"""
Error Framework for UNO.

This module provides a comprehensive error framework for standardizing error handling
across the UNO ecosystem. It includes error catalogs, error context, and utilities
for working with errors in a consistent way.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast
import inspect
import logging
import traceback
import uuid
from datetime import datetime, UTC

from pydantic import BaseModel, Field, field_validator

from .result import Error, Failure, Result, Success

__all__ = [
    "ErrorCode",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorDetail",
    "ErrorLog",
    "ErrorCatalog",
    "FrameworkError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "register_error",
    "create_error",
    "log_error",
    "error_to_dict",
    "get_error_context",
]


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


# Error context collection
@dataclass
class ErrorContext:
    """
    Context information for errors.
    
    This class collects additional information about the context in which an error occurred,
    which can be helpful for debugging and monitoring.
    """
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    query_params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    application: Optional[str] = None
    environment: Optional[str] = None
    component: Optional[str] = None
    function: Optional[str] = None
    module: Optional[str] = None
    line: Optional[int] = None
    stack_trace: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "referer": self.referer,
            "path": self.path,
            "method": self.method,
            "query_params": self.query_params,
            "headers": self.headers,
            "application": self.application,
            "environment": self.environment,
            "component": self.component,
            "function": self.function,
            "module": self.module,
            "line": self.line,
            "stack_trace": self.stack_trace,
            "additional_data": self.additional_data,
        }


# Standard error models
class ErrorDetail(BaseModel):
    """
    Detailed error information.
    
    This class provides a standardized structure for error details that can be
    used for API responses, logging, and monitoring.
    """
    
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    category: ErrorCategory = Field(
        default=ErrorCategory.UNKNOWN, description="Error category"
    )
    severity: ErrorSeverity = Field(
        default=ErrorSeverity.ERROR, description="Error severity level"
    )
    field: Optional[str] = Field(None, description="Field that caused the error (for validation errors)")
    source: Optional[str] = Field(None, description="Source of the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    help_text: Optional[str] = Field(None, description="Help text for resolving the error")
    help_url: Optional[str] = Field(None, description="URL with more information about the error")
    trace_id: Optional[str] = Field(None, description="Trace ID for tracking the error")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When the error occurred")
    
    @field_validator("code")
    def validate_code(cls, v: str) -> str:
        """Validate that the error code is in the expected format."""
        v_upper = v.upper()
        if v != v_upper:
            # Auto-convert to uppercase but warn
            logging.warning(f"Error code '{v}' was not uppercase. Converted to '{v_upper}'.")
            return v_upper
        return v


class ErrorLog(BaseModel):
    """
    Error log entry with context.
    
    This class combines error details with context information for comprehensive
    error logging and analysis.
    """
    
    error: ErrorDetail
    context: Dict[str, Any]
    exception_class: Optional[str] = None
    exception_traceback: Optional[str] = None
    is_handled: bool = False
    resolution: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


# Error catalog for centralized error definition
class ErrorCatalog:
    """
    Centralized catalog of error definitions.
    
    This class manages a catalog of error definitions that can be used throughout
    the application for consistent error handling.
    """
    
    _errors: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(
        cls,
        code: str,
        message_template: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        http_status_code: Optional[int] = None,
        help_text: Optional[str] = None,
        help_url: Optional[str] = None,
    ) -> None:
        """
        Register an error definition in the catalog.
        
        Args:
            code: Unique error code
            message_template: Message template with optional placeholders
            category: Error category
            severity: Error severity
            http_status_code: HTTP status code for API responses
            help_text: Help text for resolving the error
            help_url: URL with more information about the error
        """
        code = code.upper()
        if code in cls._errors:
            logging.warning(f"Error code '{code}' already exists in catalog. Overwriting.")
        
        cls._errors[code] = {
            "code": code,
            "message_template": message_template,
            "category": category,
            "severity": severity,
            "http_status_code": http_status_code,
            "help_text": help_text,
            "help_url": help_url,
        }
    
    @classmethod
    def get(cls, code: str) -> Optional[Dict[str, Any]]:
        """
        Get an error definition from the catalog.
        
        Args:
            code: Error code to retrieve
            
        Returns:
            Error definition or None if not found
        """
        return cls._errors.get(code.upper())
    
    @classmethod
    def create(
        cls,
        code: str,
        params: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        source: Optional[str] = None,
    ) -> ErrorDetail:
        """
        Create an error instance from a catalog definition.
        
        Args:
            code: Error code
            params: Parameters to format the message template
            details: Additional error details
            field: Field that caused the error
            source: Source of the error
            
        Returns:
            Initialized ErrorDetail instance
            
        Raises:
            ValueError: If the error code is not found in the catalog
        """
        error_def = cls.get(code)
        if not error_def:
            raise ValueError(f"Error code '{code}' not found in catalog.")
        
        message = error_def["message_template"]
        if params:
            try:
                message = message.format(**params)
            except KeyError as e:
                logging.warning(f"Missing parameter {e} for error message template: {message}")
                # Fall back to the template
                message = error_def["message_template"]
        
        return ErrorDetail(
            code=error_def["code"],
            message=message,
            category=error_def["category"],
            severity=error_def["severity"],
            field=field,
            source=source,
            details=details,
            help_text=error_def["help_text"],
            help_url=error_def["help_url"],
            trace_id=getattr(ErrorContext().trace_id, "trace_id", None),
        )
    
    @classmethod
    def to_result(
        cls,
        code: str,
        params: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Failure:
        """
        Create a Failure result with an error from the catalog.
        
        Args:
            code: Error code
            params: Parameters to format the message template
            details: Additional error details
            field: Field that caused the error
            source: Source of the error
            
        Returns:
            Failure result with the error
        """
        error = cls.create(code, params, details, field, source)
        return Failure(
            error.message,
            error_code=error.code,
            details=error.details,
            context={"field": error.field, "source": error.source},
        )


# Base error classes that extend the standard Exception hierarchy
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
        context: Optional[ErrorContext] = None,
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
        self.context = context or get_error_context()
        self.original_exception = original_exception
    
    def to_error_detail(self) -> ErrorDetail:
        """Convert to ErrorDetail model."""
        return ErrorDetail(
            code=self.code,
            message=str(self),
            category=self.category,
            severity=self.severity,
            details=self.details,
            trace_id=getattr(self.context, "trace_id", None),
        )
    
    def to_result(self) -> Failure:
        """Convert to a Failure result."""
        return Failure(
            str(self),
            error_code=self.code,
            details=self.details,
        )
    
    def with_context(self, context: ErrorContext) -> "FrameworkError":
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


class NotFoundError(FrameworkError):
    """Error raised when a resource is not found."""
    
    def __init__(
        self,
        message: str,
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize a not found error.
        
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


# Utility functions
def register_error(
    code: str,
    message_template: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    http_status_code: Optional[int] = None,
    help_text: Optional[str] = None,
    help_url: Optional[str] = None,
) -> None:
    """
    Register an error in the catalog.
    
    Args:
        code: Unique error code
        message_template: Message template with optional placeholders
        category: Error category
        severity: Error severity
        http_status_code: HTTP status code for API responses
        help_text: Help text for resolving the error
        help_url: URL with more information about the error
    """
    ErrorCatalog.register(
        code=code,
        message_template=message_template,
        category=category,
        severity=severity,
        http_status_code=http_status_code,
        help_text=help_text,
        help_url=help_url,
    )


def create_error(
    code: str,
    params: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
    field: Optional[str] = None,
    source: Optional[str] = None,
) -> ErrorDetail:
    """
    Create an error from the catalog.
    
    Args:
        code: Error code
        params: Parameters to format the message template
        details: Additional error details
        field: Field that caused the error
        source: Source of the error
        
    Returns:
        Initialized ErrorDetail instance
    """
    return ErrorCatalog.create(
        code=code,
        params=params,
        details=details,
        field=field,
        source=source,
    )


def get_error_context() -> ErrorContext:
    """
    Get error context from the current execution context.
    
    Returns:
        Error context with stack trace information
    """
    context = ErrorContext()
    
    # Add stack trace information
    stack = inspect.stack()
    if len(stack) > 2:
        frame = stack[2]
        context.function = frame.function
        context.module = frame.frame.f_globals.get("__name__", "")
        context.line = frame.lineno
    
    # Add full stack trace
    context.stack_trace = "".join(traceback.format_stack()[:-1])
    
    return context


def log_error(
    error: Union[Exception, ErrorDetail, Error],
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    include_traceback: bool = True,
    context: Optional[ErrorContext] = None,
) -> ErrorLog:
    """
    Log an error with additional context.
    
    Args:
        error: The error to log
        logger: Logger to use (defaults to root logger)
        level: Logging level
        include_traceback: Whether to include traceback information
        context: Error context
        
    Returns:
        Error log entry
    """
    logger = logger or logging.getLogger()
    context = context or get_error_context()
    
    # Convert error to ErrorDetail if needed
    if isinstance(error, Exception) and not isinstance(error, FrameworkError):
        error_detail = ErrorDetail(
            code="EXCEPTION",
            message=str(error),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            details={"exception_type": error.__class__.__name__},
            trace_id=context.trace_id,
        )
    elif isinstance(error, FrameworkError):
        error_detail = error.to_error_detail()
    elif isinstance(error, Error):
        error_detail = ErrorDetail(
            code=getattr(error, "code", "ERROR"),
            message=str(error),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            details=getattr(error, "details", {}),
            trace_id=context.trace_id,
        )
    else:
        error_detail = error
    
    # Create log entry
    log_entry = ErrorLog(
        error=error_detail,
        context=context.to_dict(),
        exception_class=(
            error.__class__.__name__
            if isinstance(error, Exception)
            else None
        ),
        exception_traceback=(
            "".join(traceback.format_exception(type(error), error, error.__traceback__))
            if include_traceback and isinstance(error, Exception)
            else None
        ),
    )
    
    # Log the error
    logger.log(
        level,
        f"{error_detail.code}: {error_detail.message}",
        extra={"error_log": log_entry.model_dump()},
    )
    
    return log_entry


def error_to_dict(error: Union[Exception, ErrorDetail, Error]) -> Dict[str, Any]:
    """
    Convert an error to a dictionary representation.
    
    Args:
        error: The error to convert
        
    Returns:
        Dictionary representation of the error
    """
    if isinstance(error, FrameworkError):
        return error.to_error_detail().model_dump()
    elif isinstance(error, Exception):
        return {
            "code": "EXCEPTION",
            "message": str(error),
            "category": ErrorCategory.SYSTEM.value,
            "severity": ErrorSeverity.ERROR.value,
            "details": {"exception_type": error.__class__.__name__},
        }
    elif isinstance(error, Error):
        return {
            "code": getattr(error, "code", "ERROR"),
            "message": str(error),
            "category": ErrorCategory.UNKNOWN.value,
            "severity": ErrorSeverity.ERROR.value,
            "details": getattr(error, "details", {}),
        }
    else:
        return error.model_dump()


# Type variable for Result generic
T = TypeVar("T")


def error_to_result(error: Union[Exception, ErrorDetail]) -> Failure:
    """
    Convert an error to a Failure result.
    
    Args:
        error: The error to convert
        
    Returns:
        Failure result
    """
    if isinstance(error, FrameworkError):
        return error.to_result()
    elif isinstance(error, Exception):
        return Failure(
            str(error),
            error_code="EXCEPTION",
            details={"exception_type": error.__class__.__name__},
        )
    else:
        return Failure(
            error.message,
            error_code=error.code,
            details=error.details,
        )


# Register common errors
register_error(
    code="VALIDATION_ERROR",
    message_template="Validation error: {message}",
    category=ErrorCategory.VALIDATION,
    severity=ErrorSeverity.ERROR,
    http_status_code=400,
    help_text="Check the request data and ensure it meets the validation requirements.",
)

register_error(
    code="AUTHENTICATION_ERROR",
    message_template="Authentication error: {message}",
    category=ErrorCategory.AUTHENTICATION,
    severity=ErrorSeverity.ERROR,
    http_status_code=401,
    help_text="Check your authentication credentials and try again.",
)

register_error(
    code="AUTHORIZATION_ERROR",
    message_template="Authorization error: {message}",
    category=ErrorCategory.AUTHORIZATION,
    severity=ErrorSeverity.ERROR,
    http_status_code=403,
    help_text="You do not have permission to perform this action.",
)

register_error(
    code="NOT_FOUND",
    message_template="{entity} not found: {id}",
    category=ErrorCategory.RESOURCE,
    severity=ErrorSeverity.ERROR,
    http_status_code=404,
    help_text="The requested resource does not exist.",
)

register_error(
    code="CONFLICT",
    message_template="{message}",
    category=ErrorCategory.RESOURCE,
    severity=ErrorSeverity.ERROR,
    http_status_code=409,
    help_text="The request conflicts with the current state of the resource.",
)

register_error(
    code="RATE_LIMIT_EXCEEDED",
    message_template="Rate limit exceeded: {message}",
    category=ErrorCategory.RESOURCE,
    severity=ErrorSeverity.ERROR,
    http_status_code=429,
    help_text="You have exceeded the maximum number of requests. Please try again later.",
)

register_error(
    code="SERVER_ERROR",
    message_template="Server error: {message}",
    category=ErrorCategory.SYSTEM,
    severity=ErrorSeverity.CRITICAL,
    http_status_code=500,
    help_text="An internal server error occurred. Please try again later.",
)