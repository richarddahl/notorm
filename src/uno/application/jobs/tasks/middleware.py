"""Middleware for tasks in the background processing system.

This module defines the middleware interface for intercepting and modifying
task execution.
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar, cast
import logging

# Global middleware registry
_middleware: list['TaskMiddleware'] = []

T = TypeVar('T')


class TaskMiddleware:
    """Middleware for intercepting and modifying task execution.
    
    This class defines the interface for middleware that can intercept and
    modify task execution at various points in the lifecycle.
    """
    
    def __init__(self, logger: logging.Logger | None = None -> None:
        """Initialize the middleware.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    async def before_task(self, task_func: Callable[..., Any], args: tuple, kwargs: dict, job: Dict[str, Any]) -> tuple:
        """Called before a task is executed.
        
        This method can modify the arguments passed to the task.
        
        Args:
            task_func: The task function to be executed
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            job: The job context
            
        Returns:
            Tuple of (args, kwargs) to use for execution
        """
        return args, kwargs
    
    async def after_task(self, task_func: Callable[..., Any], args: tuple, kwargs: dict, result: T, job: Dict[str, Any]) -> T:
        """Called after a task is successfully executed.
        
        This method can modify the result of the task.
        
        Args:
            task_func: The task function that was executed
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            result: The result of the task execution
            job: The job context
            
        Returns:
            Modified result
        """
        return result
    
    async def on_error(self, task_func: Callable[..., Any], args: tuple, kwargs: dict, error: Exception, job: Dict[str, Any]) -> Exception:
        """Called when a task raises an exception.
        
        This method can modify the exception or perform cleanup actions.
        
        Args:
            task_func: The task function that raised the exception
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            error: The exception that was raised
            job: The job context
            
        Returns:
            Modified exception
        """
        return error


def register_middleware(middleware: TaskMiddleware) -> None:
    """Register a middleware globally.
    
    Args:
        middleware: The middleware to register
    """
    _middleware.append(middleware)


def unregister_middleware(middleware: TaskMiddleware) -> bool:
    """Unregister a middleware globally.
    
    Args:
        middleware: The middleware to unregister
        
    Returns:
        True if the middleware was unregistered, False if not found
    """
    if middleware in _middleware:
        _middleware.remove(middleware)
        return True
    return False


def get_registered_middleware() -> list[TaskMiddleware]:
    """Get all registered middleware.
    
    Returns:
        List of registered middleware
    """
    return _middleware.copy()