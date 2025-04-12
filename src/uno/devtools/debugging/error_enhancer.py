"""
Error enhancement utilities for better debugging.

This module provides tools to enhance error information with additional context,
including SQL queries, request information, and stack context.
"""

import sys
import traceback
import inspect
import logging
from typing import Dict, List, Optional, Any, Callable, Type, Union
from functools import wraps
from contextlib import contextmanager

from uno.core.errors.base import UnoError


logger = logging.getLogger("uno.debug.error")


class ErrorContext:
    """Context information for errors."""
    
    def __init__(self):
        """Initialize the error context."""
        self.context: Dict[str, Any] = {}
    
    def add(self, key: str, value: Any) -> None:
        """Add context information.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
    
    def get(self, key: str) -> Optional[Any]:
        """Get context information.
        
        Args:
            key: Context key
            
        Returns:
            The context value if found, None otherwise
        """
        return self.context.get(key)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all context information.
        
        Returns:
            Dictionary with all context information
        """
        return self.context.copy()
    
    def clear(self) -> None:
        """Clear all context information."""
        self.context.clear()


# Global error context
_error_context = ErrorContext()


def get_error_context() -> ErrorContext:
    """Get the global error context instance.
    
    Returns:
        The global ErrorContext instance
    """
    return _error_context


class EnhancedUnoError(UnoError):
    """Enhanced version of UnoError with additional debugging information."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize the enhanced error.
        
        Args:
            message: Error message
            error_code: Error code
            status_code: HTTP status code
            detail: Additional error details
            context: Error context
            cause: Original exception causing this error
        """
        super().__init__(message, error_code=error_code, status_code=status_code)
        self.detail = detail or {}
        self.context = context or {}
        self.cause = cause
        
        # Add debug information if available
        if _error_context:
            self.context.update(_error_context.get_all())
        
        # Add stack trace
        self.context["stack_trace"] = self._get_simplified_traceback()
    
    def _get_simplified_traceback(self) -> List[Dict[str, Any]]:
        """Get a simplified traceback for debugging.
        
        Returns:
            List of frame information dictionaries
        """
        frames = []
        tb = traceback.extract_tb(sys.exc_info()[2]) if sys.exc_info()[2] else []
        
        for frame in tb:
            frames.append({
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line,
            })
        
        return frames


class ErrorEnhancer:
    """Enhances errors with additional context and information."""
    
    def __init__(self):
        """Initialize the error enhancer."""
        self.error_hooks: List[Callable[[Exception], Optional[Exception]]] = []
    
    def register_hook(self, hook: Callable[[Exception], Optional[Exception]]) -> None:
        """Register an error hook.
        
        Args:
            hook: Function that takes an exception and returns an enhanced exception or None
        """
        self.error_hooks.append(hook)
    
    def enhance_error(self, error: Exception) -> Exception:
        """Enhance an error with additional information.
        
        Args:
            error: The original error
            
        Returns:
            The enhanced error
        """
        enhanced_error = error
        
        # Apply hooks
        for hook in self.error_hooks:
            try:
                result = hook(enhanced_error)
                if result is not None:
                    enhanced_error = result
            except Exception as e:
                logger.error(f"Error in error hook: {str(e)}")
        
        return enhanced_error
    
    @contextmanager
    def capture_context(self, **kwargs) -> None:
        """Capture error context within a block.
        
        Args:
            **kwargs: Context values to add
        """
        # Save existing context
        previous_context = _error_context.get_all()
        
        try:
            # Add new context
            for key, value in kwargs.items():
                _error_context.add(key, value)
            
            yield
        finally:
            # Restore previous context
            _error_context.clear()
            for key, value in previous_context.items():
                _error_context.add(key, value)
    
    def wrap_function(self, func: Callable) -> Callable:
        """Wrap a function to enhance errors.
        
        Args:
            func: The function to wrap
            
        Returns:
            The wrapped function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                enhanced = self.enhance_error(e)
                raise enhanced from e
        
        return wrapper


# Global error enhancer
_error_enhancer = ErrorEnhancer()


def get_error_enhancer() -> ErrorEnhancer:
    """Get the global error enhancer instance.
    
    Returns:
        The global ErrorEnhancer instance
    """
    return _error_enhancer


def enhance_error_info(error: Exception) -> Exception:
    """Enhance an error with additional information.
    
    Args:
        error: The original error
        
    Returns:
        The enhanced error
    """
    return _error_enhancer.enhance_error(error)


def with_error_context(**kwargs) -> Callable:
    """Decorator to add error context to a function.
    
    Args:
        **kwargs: Context values to add
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **func_kwargs):
            with _error_enhancer.capture_context(**kwargs):
                return func(*args, **func_kwargs)
        return wrapper
    return decorator


def capture_error_context(**kwargs) -> Any:
    """Context manager to capture error context.
    
    Args:
        **kwargs: Context values to add
        
    Returns:
        Context manager
    """
    return _error_enhancer.capture_context(**kwargs)


def _uno_error_hook(error: Exception) -> Optional[Exception]:
    """Hook to enhance UnoError instances.
    
    Args:
        error: The original error
        
    Returns:
        Enhanced error if applicable, None otherwise
    """
    if isinstance(error, UnoError) and not isinstance(error, EnhancedUnoError):
        return EnhancedUnoError(
            message=str(error),
            error_code=getattr(error, "error_code", None),
            status_code=getattr(error, "status_code", 500),
            detail=getattr(error, "detail", None),
            context=getattr(error, "context", None),
            cause=error.__cause__,
        )
    return None


def _sql_error_hook(error: Exception) -> Optional[Exception]:
    """Hook to enhance database errors.
    
    Args:
        error: The original error
        
    Returns:
        Enhanced error if applicable, None otherwise
    """
    # Check if it's a database error
    if (
        error.__class__.__name__ in (
            "OperationalError", "IntegrityError", "DataError", 
            "ProgrammingError", "NotSupportedError", "DatabaseError"
        )
        or "sqlalchemy" in error.__class__.__module__
        or "psycopg" in error.__class__.__module__
        or "asyncpg" in error.__class__.__module__
    ):
        # Get the last executed SQL query if available
        last_query = None
        try:
            from uno.devtools.debugging.sql_debug import get_query_tracker
            tracker = get_query_tracker()
            if tracker.queries:
                last_query = tracker.queries[-1]
        except ImportError:
            pass
        
        if isinstance(error, UnoError):
            # Create an enhanced UnoError
            enhanced = EnhancedUnoError(
                message=str(error),
                error_code=getattr(error, "error_code", "database_error"),
                status_code=getattr(error, "status_code", 500),
                detail=getattr(error, "detail", {}),
                context=getattr(error, "context", {}),
                cause=error.__cause__,
            )
            
            if last_query:
                enhanced.context["last_sql_query"] = {
                    "query": last_query.query,
                    "parameters": last_query.parameters,
                    "duration_ms": last_query.duration_ms,
                }
            
            return enhanced
        else:
            # Create a new UnoError
            context = {}
            if last_query:
                context["last_sql_query"] = {
                    "query": last_query.query,
                    "parameters": last_query.parameters,
                    "duration_ms": last_query.duration_ms,
                }
            
            return EnhancedUnoError(
                message=str(error),
                error_code="database_error",
                status_code=500,
                detail={"type": error.__class__.__name__},
                context=context,
                cause=error,
            )
    
    return None


def _general_exception_hook(error: Exception) -> Optional[Exception]:
    """Hook to enhance general exceptions.
    
    Args:
        error: The original error
        
    Returns:
        Enhanced error if applicable, None otherwise
    """
    if not isinstance(error, UnoError) and not isinstance(error, EnhancedUnoError):
        # Add variable values from the frame where the exception occurred
        local_vars = {}
        
        tb = getattr(error, "__traceback__", None)
        if tb:
            while tb.tb_next:
                tb = tb.tb_next
            
            frame = tb.tb_frame
            local_vars = {
                name: repr(value)
                for name, value in frame.f_locals.items()
                if not name.startswith("__") and not callable(value)
            }
        
        return EnhancedUnoError(
            message=str(error),
            error_code="internal_server_error",
            status_code=500,
            detail={"type": error.__class__.__name__},
            context={"local_variables": local_vars},
            cause=error,
        )
    
    return None


def setup_error_hooks() -> ErrorEnhancer:
    """Set up error hooks for enhanced debugging.
    
    Returns:
        The global error enhancer
    """
    _error_enhancer.register_hook(_uno_error_hook)
    _error_enhancer.register_hook(_sql_error_hook)
    _error_enhancer.register_hook(_general_exception_hook)
    
    return _error_enhancer