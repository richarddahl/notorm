# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Structured logging framework for the Uno application.

This module provides a comprehensive logging framework with structured logging,
context propagation, and integration with the error system.

Features:
- Structured JSON logging
- Context propagation across async boundaries
- Middleware for HTTP request logging
- Integration with error framework
- Configurable outputs and formats
"""

import functools
import inspect
import json
import logging
import logging.config
import sys
import traceback
import contextvars
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast, Tuple, TypeVar, Protocol, ClassVar

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.errors.framework import ErrorContext, ErrorDetail, FrameworkError, log_error as framework_log_error
from uno.dependencies.interfaces import ConfigProtocol

# Type variables
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Context variable for logging context
_logging_context = contextvars.ContextVar[Dict[str, Any]]("logging_context", default={})


class LogLevel(str, Enum):
    """Log levels with string values for configuration."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """Convert string to LogLevel."""
        try:
            return cls[level_str.upper()]
        except KeyError:
            valid_levels = ", ".join([l.name for l in cls])
            raise ValueError(f"Invalid log level: {level_str}. Valid levels are: {valid_levels}")
    
    def to_python_level(self) -> int:
        """Convert to Python logging level."""
        return getattr(logging, self.value)


class LogFormat(str, Enum):
    """Log format types."""
    
    TEXT = "text"
    JSON = "json"


@dataclass
class LogContext:
    """
    Context information for logging.
    
    This class collects additional information about the context in which a log is emitted,
    which can be helpful for filtering and analysis.
    """
    
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    service_name: Optional[str] = None
    environment: Optional[str] = None
    component: Optional[str] = None
    function: Optional[str] = None
    module: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary."""
        result = {}
        
        # Add fields that are not None
        for key, value in self.__dict__.items():
            if value is not None and key != "additional_data":
                result[key] = value
        
        # Add additional data
        result.update(self.additional_data)
        
        return result
    
    def merge(self, other: Union["LogContext", Dict[str, Any]]) -> "LogContext":
        """
        Merge with another context.
        
        This creates a new LogContext with the combined properties of both contexts,
        with the other context taking precedence for conflicting keys.
        
        Args:
            other: Another LogContext or a dictionary
            
        Returns:
            New LogContext with merged properties
        """
        if isinstance(other, dict):
            other_dict = other
        else:
            other_dict = other.to_dict()
        
        this_dict = self.to_dict()
        merged = {**this_dict, **other_dict}
        
        # Create a new instance with the merged data
        result = LogContext()
        
        # Set direct properties
        for key in ["trace_id", "request_id", "user_id", "tenant_id", 
                    "service_name", "environment", "component", "function", "module"]:
            if key in merged:
                setattr(result, key, merged.pop(key))
        
        # Set remaining keys as additional data
        result.additional_data = merged
        
        return result


@dataclass
class LogConfig:
    """
    Configuration for logging.
    
    This class provides a structured way to configure logging with sensible defaults.
    """
    
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.TEXT
    console_output: bool = True
    file_output: bool = False
    file_path: Optional[str] = None
    backup_count: int = 5
    max_bytes: int = 10 * 1024 * 1024  # 10 MB
    service_name: str = "uno"
    environment: str = "development"
    include_trace_id: bool = True
    include_caller_info: bool = True
    include_timestamp: bool = True
    include_exception_traceback: bool = True
    propagate: bool = False
    
    @classmethod
    def from_config(cls, config: ConfigProtocol) -> "LogConfig":
        """
        Create LogConfig from ConfigProtocol.
        
        Args:
            config: Configuration provider
            
        Returns:
            LogConfig instance
        """
        return cls(
            level=LogLevel.from_string(config.get("logging.level", LogLevel.INFO.value)),
            format=LogFormat(config.get("logging.format", LogFormat.TEXT.value)),
            console_output=config.get("logging.console_output", True),
            file_output=config.get("logging.file_output", False),
            file_path=config.get("logging.file_path"),
            backup_count=config.get("logging.backup_count", 5),
            max_bytes=config.get("logging.max_bytes", 10 * 1024 * 1024),
            service_name=config.get("service.name", "uno"),
            environment=config.get("environment", "development"),
            include_trace_id=config.get("logging.include_trace_id", True),
            include_caller_info=config.get("logging.include_caller_info", True),
            include_timestamp=config.get("logging.include_timestamp", True),
            include_exception_traceback=config.get("logging.include_exception_traceback", True),
            propagate=config.get("logging.propagate", False),
        )


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logs.
    
    This formatter converts log records to JSON format with additional contextual information.
    """
    
    def __init__(
        self,
        service_name: str = "uno",
        environment: str = "development",
        include_timestamp: bool = True,
        include_trace_id: bool = True,
        include_caller_info: bool = True,
        include_exception_traceback: bool = True,
    ):
        """
        Initialize the formatter.
        
        Args:
            service_name: Name of the service
            environment: Deployment environment
            include_timestamp: Whether to include timestamp in logs
            include_trace_id: Whether to include trace ID in logs
            include_caller_info: Whether to include caller info in logs
            include_exception_traceback: Whether to include exception traceback in logs
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_timestamp = include_timestamp
        self.include_trace_id = include_trace_id
        self.include_caller_info = include_caller_info
        self.include_exception_traceback = include_exception_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON string representation of the log record
        """
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }
        
        # Add timestamp if enabled
        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(record.created, UTC).isoformat()
        
        # Add caller info if enabled
        if self.include_caller_info:
            log_data["caller"] = {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "process": record.process,
                "thread": record.thread,
            }
        
        # Add context if available
        context_dict = {}
        
        # Add context from error_context if available
        if hasattr(record, "error_context") and record.error_context:
            context_dict.update(record.error_context)
        
        # Add context from logging_context if available
        if hasattr(record, "logging_context") and record.logging_context:
            context_dict.update(record.logging_context)
        
        # Add trace_id if available and enabled
        if self.include_trace_id and hasattr(record, "trace_id") and record.trace_id:
            log_data["trace_id"] = record.trace_id
        
        # Add context if not empty
        if context_dict:
            log_data["context"] = context_dict
        
        # Add extra attributes if available
        if hasattr(record, "extras") and record.extras:
            for key, value in record.extras.items():
                if key not in log_data and key not in ("error_context", "logging_context", "trace_id"):
                    log_data[key] = value
        
        # Add exception info if available
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
            }
            
            if self.include_exception_traceback and exc_tb:
                log_data["exception"]["traceback"] = self.formatException(record.exc_info)
            
            # Add FrameworkError specific fields
            if isinstance(exc_value, FrameworkError):
                log_data["exception"]["error_code"] = exc_value.code
                if hasattr(exc_value, "context") and exc_value.context:
                    log_data["exception"]["error_context"] = exc_value.context.to_dict()
            
        # Add error details if available
        if hasattr(record, "error_detail") and record.error_detail:
            error_detail = record.error_detail
            if isinstance(error_detail, ErrorDetail):
                log_data["error"] = {
                    "code": error_detail.code,
                    "message": error_detail.message,
                    "category": error_detail.category,
                    "severity": error_detail.severity,
                }
                if error_detail.details:
                    log_data["error"]["details"] = error_detail.details
            elif isinstance(error_detail, dict):
                log_data["error"] = error_detail
        
        return json.dumps(log_data, default=str)


class StructuredLogAdapter(logging.LoggerAdapter):
    """
    Adapter for structured logging.
    
    This adapter enhances log messages with contextual information.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process the log message and inject context.
        
        Args:
            msg: The log message
            kwargs: Additional logging parameters
            
        Returns:
            Tuple of (message, kwargs) with context injected
        """
        # Get a copy of the current logging context
        logging_context = _logging_context.get().copy()
        
        # Initialize extras dictionary
        extras = kwargs.get("extra", {}).copy() if "extra" in kwargs else {}
        
        # Add logging context to extras
        extras["logging_context"] = logging_context
        
        # Add trace_id if available
        if "trace_id" in logging_context:
            extras["trace_id"] = logging_context["trace_id"]
        
        # Update kwargs with extras
        kwargs["extra"] = extras
        
        return msg, kwargs


class StructuredLogger:
    """
    Enhanced logger with structured logging capabilities.
    
    This class wraps the standard logger with additional functionality for
    structured logging, context propagation, and error integration.
    """
    
    def __init__(self, name: str, adapter: Optional[logging.LoggerAdapter] = None):
        """
        Initialize a structured logger.
        
        Args:
            name: Logger name
            adapter: Optional logger adapter
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.adapter = adapter or StructuredLogAdapter(self.logger, {})
    
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self.adapter.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self.adapter.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self.adapter.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self.adapter.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self.adapter.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args: Any, exc_info: Any = True, **kwargs: Any) -> None:
        """Log an exception message."""
        self.adapter.exception(msg, *args, exc_info=exc_info, **kwargs)
    
    def log_error(
        self,
        error: Union[Exception, ErrorDetail],
        level: int = logging.ERROR,
        include_traceback: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an error with the error framework.
        
        Args:
            error: The error to log
            level: Logging level
            include_traceback: Whether to include traceback information
            context: Additional context to include
        """
        # Get current logging context
        logging_context = _logging_context.get().copy()
        
        # Merge with provided context
        if context:
            logging_context.update(context)
        
        # Create error context from logging context
        error_context = ErrorContext(
            trace_id=logging_context.get("trace_id"),
            request_id=logging_context.get("request_id"),
            user_id=logging_context.get("user_id"),
            application=logging_context.get("service_name"),
            environment=logging_context.get("environment"),
            component=logging_context.get("component"),
            additional_data=logging_context,
        )
        
        # Log the error using the error framework
        error_log = framework_log_error(
            error=error,
            logger=self.logger,
            level=level,
            include_traceback=include_traceback,
            context=error_context,
        )
        
        # No need to log again as framework_log_error already logs
    
    def with_context(self, **context: Any) -> "StructuredLogger":
        """
        Create a new logger with additional context.
        
        Args:
            **context: Context key-value pairs
            
        Returns:
            New logger with the updated context
        """
        # Create a new logger with the same name
        new_logger = StructuredLogger(self.name)
        
        # Add context to the new logger
        add_context(**context)
        
        return new_logger
    
    def bind(self, **context: Any) -> "StructuredLogger":
        """
        Alias for with_context.
        
        Args:
            **context: Context key-value pairs
            
        Returns:
            New logger with the updated context
        """
        return self.with_context(**context)


def configure_logging(config: Optional[LogConfig] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        config: Logging configuration (optional, uses defaults if not provided)
    """
    config = config or LogConfig()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level.to_python_level())
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure console handler
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if config.format == LogFormat.JSON:
            formatter = StructuredJsonFormatter(
                service_name=config.service_name,
                environment=config.environment,
                include_timestamp=config.include_timestamp,
                include_trace_id=config.include_trace_id,
                include_caller_info=config.include_caller_info,
                include_exception_traceback=config.include_exception_traceback,
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Configure file handler
    if config.file_output and config.file_path:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
        )
        
        if config.format == LogFormat.JSON:
            formatter = StructuredJsonFormatter(
                service_name=config.service_name,
                environment=config.environment,
                include_timestamp=config.include_timestamp,
                include_trace_id=config.include_trace_id,
                include_caller_info=config.include_caller_info,
                include_exception_traceback=config.include_exception_traceback,
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure propagation
    root_logger.propagate = config.propagate
    
    # Log configuration completion
    logger = get_logger("uno.logging")
    logger.info(
        f"Logging configured with level={config.level.value}, format={config.format.value}, "
        f"console={config.console_output}, file={config.file_output}"
    )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return StructuredLogger(name)


def add_context(**context: Any) -> None:
    """
    Add key-value pairs to the current logging context.
    
    Args:
        **context: Key-value pairs to add to the context
    """
    current = _logging_context.get().copy()
    current.update(context)
    _logging_context.set(current)


def get_context() -> Dict[str, Any]:
    """
    Get the current logging context.
    
    Returns:
        The current logging context dictionary
    """
    return _logging_context.get().copy()


def clear_context() -> None:
    """Clear the current logging context."""
    _logging_context.set({})


def with_logging_context(func: Optional[F] = None, **context: Any) -> Union[F, Callable[[F], F]]:
    """
    Decorator that adds context to logging.
    
    This can be used in two ways:
    1. with_logging_context(func): Adds function parameters to logging context
    2. with_logging_context(param1="value"): Adds specified context to logging
    
    Args:
        func: The function to decorate
        **context: Context key-value pairs
        
    Returns:
        The decorated function
    """
    # Check if called as @with_logging_context or @with_logging_context(param="value")
    if func is None:
        # Called as @with_logging_context(param="value")
        def decorator(f: F) -> F:
            @functools.wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Get the current context
                current_context = _logging_context.get().copy()
                
                # Add static context provided in the decorator
                new_context = {**current_context, **context}
                
                # Set the new context
                token = _logging_context.set(new_context)
                
                try:
                    return f(*args, **kwargs)
                finally:
                    # Restore the previous context
                    _logging_context.reset(token)
            
            return cast(F, wrapper)
        
        return decorator
    
    # Called as @with_logging_context
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get the signature of the function
        sig = inspect.signature(func)
        
        # Bind the arguments to the signature
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        # Get arguments as a dict, filtering out self/cls for methods
        arg_dict = {}
        for key, value in bound.arguments.items():
            # Skip 'self' and 'cls' parameters
            if key not in ("self", "cls"):
                # Avoid including large objects or sensitive data
                if isinstance(value, (str, int, float, bool)) or value is None:
                    arg_dict[key] = value
                else:
                    # Just include the type for complex objects
                    arg_dict[key] = f"<{type(value).__name__}>"
        
        # Get the current context
        current_context = _logging_context.get().copy()
        
        # Create a new context with function info and parameters
        new_context = {
            **current_context,
            "function": func.__name__,
            "module": func.__module__,
            "args": arg_dict,
        }
        
        # Set the new context
        token = _logging_context.set(new_context)
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the exception with context
            logger = get_logger(func.__module__)
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise
        finally:
            # Restore the previous context
            _logging_context.reset(token)
    
    return cast(F, wrapper)


def log_error(
    error: Union[Exception, ErrorDetail],
    logger: Optional[Union[logging.Logger, StructuredLogger]] = None,
    level: int = logging.ERROR,
    include_traceback: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error with the error framework.
    
    This function is a convenience wrapper for structured_logger.log_error().
    
    Args:
        error: The error to log
        logger: Logger to use (defaults to getting one based on frame info)
        level: Logging level
        include_traceback: Whether to include traceback information
        context: Additional context to include
    """
    # Get logger if not provided
    if logger is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            module_name = frame.f_back.f_globals.get("__name__", "unknown")
            logger = get_logger(module_name)
        else:
            logger = get_logger("uno.error")
    
    # Convert standard logger to structured logger if needed
    if isinstance(logger, logging.Logger):
        structured_logger = StructuredLogger(logger.name)
    else:
        structured_logger = logger
    
    # Log the error
    structured_logger.log_error(
        error=error,
        level=level,
        include_traceback=include_traceback,
        context=context,
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for HTTP request logging.
    
    This middleware logs HTTP requests and responses with context information.
    """
    
    def __init__(
        self,
        app: FastAPI,
        logger: Optional[StructuredLogger] = None,
        level: int = logging.INFO,
        include_headers: bool = True,
        include_query_params: bool = True,
        include_client_info: bool = True,
        include_timing: bool = True,
        exclude_paths: Optional[List[str]] = None,
        sensitive_headers: Optional[List[str]] = None,
    ):
        """
        Initialize the logging middleware.
        
        Args:
            app: FastAPI application
            logger: Logger to use
            level: Logging level for request/response logs
            include_headers: Whether to include headers in logs
            include_query_params: Whether to include query parameters in logs
            include_client_info: Whether to include client information in logs
            include_timing: Whether to include timing information in logs
            exclude_paths: Paths to exclude from logging
            sensitive_headers: Headers to redact from logs
        """
        super().__init__(app)
        self.logger = logger or get_logger("uno.http")
        self.level = level
        self.include_headers = include_headers
        self.include_query_params = include_query_params
        self.include_client_info = include_client_info
        self.include_timing = include_timing
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.sensitive_headers = [h.lower() for h in (sensitive_headers or ["authorization", "cookie", "x-api-key"])]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """
        Process a request and log it.
        
        Args:
            request: HTTP request
            call_next: Function to call the next handler
            
        Returns:
            HTTP response
        """
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get request info
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers)
        
        # Redact sensitive headers
        if self.include_headers:
            headers_to_log = {}
            for name, value in headers.items():
                if name.lower() in self.sensitive_headers:
                    headers_to_log[name] = "REDACTED"
                else:
                    headers_to_log[name] = value
        else:
            headers_to_log = {}
        
        # Get client info
        client_info = {}
        if self.include_client_info:
            client_info = {
                "client_host": request.client.host if request.client else None,
                "client_port": request.client.port if request.client else None,
                "user_agent": headers.get("user-agent"),
            }
        
        # Generate trace ID if not present
        trace_id = headers.get("x-trace-id") or headers.get("x-request-id")
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())
        
        # Add context for the request
        context = {
            "trace_id": trace_id,
            "request_id": headers.get("x-request-id"),
            "user_id": headers.get("x-user-id"),
            "tenant_id": headers.get("x-tenant-id"),
            "path": path,
            "method": method,
        }
        
        # Add context to logging context
        add_context(**context)
        
        # Log the request
        request_log = {
            "event": "http_request",
            "method": method,
            "path": path,
        }
        
        if self.include_query_params and query_params:
            request_log["query_params"] = query_params
        
        if self.include_headers and headers_to_log:
            request_log["headers"] = headers_to_log
        
        if self.include_client_info and client_info:
            request_log.update(client_info)
        
        self.logger.info(f"HTTP {method} {path}", extra={"extras": request_log})
        
        # Process the request
        start_time = datetime.now(UTC)
        
        try:
            response = await call_next(request)
            
            # Log the response
            end_time = datetime.now(UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            response_log = {
                "event": "http_response",
                "method": method,
                "path": path,
                "status_code": response.status_code,
            }
            
            if self.include_timing:
                response_log["duration_ms"] = duration_ms
            
            # Determine log level based on status code
            if response.status_code >= 500:
                log_method = self.logger.error
            elif response.status_code >= 400:
                log_method = self.logger.warning
            else:
                log_method = self.logger.info
            
            log_method(
                f"HTTP {method} {path} {response.status_code}",
                extra={"extras": response_log},
            )
            
            return response
            
        except Exception as exc:
            # Log the exception
            end_time = datetime.now(UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            error_log = {
                "event": "http_error",
                "method": method,
                "path": path,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
            }
            
            if self.include_timing:
                error_log["duration_ms"] = duration_ms
            
            self.logger.exception(
                f"Error processing HTTP {method} {path}: {str(exc)}",
                extra={"extras": error_log},
            )
            
            raise
        
        finally:
            # Clear the context
            clear_context()