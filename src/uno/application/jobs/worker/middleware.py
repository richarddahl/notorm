"""Middleware for workers in the background processing system.

This module defines the middleware interface for intercepting and modifying
worker job execution.
"""

from typing import Any, Callable, List, Optional, Tuple, TypeVar, Dict, cast
import logging

from uno.jobs.queue import Job

T = TypeVar('T')


class Middleware:
    """Middleware for intercepting and modifying worker job execution.
    
    This class defines the interface for middleware that can intercept and
    modify job execution at various points in the lifecycle.
    """
    
    def __init__(self, logger: logging.Logger | None = None -> None:
        """Initialize the middleware.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    async def before_execution(self, job: Job, task_func: Callable[..., Any], args: tuple, kwargs: dict) -> Tuple[tuple, dict]:
        """Called before a job is executed.
        
        This method can modify the arguments passed to the task.
        
        Args:
            job: The job being executed
            task_func: The task function to be executed
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            
        Returns:
            Tuple of (args, kwargs) to use for execution
        """
        return args, kwargs
    
    async def after_execution(self, job: Job, task_func: Callable[..., Any], args: tuple, kwargs: dict, result: T) -> T:
        """Called after a job is successfully executed.
        
        This method can modify the result of the task.
        
        Args:
            job: The job that was executed
            task_func: The task function that was executed
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            result: The result of the task execution
            
        Returns:
            Modified result
        """
        return result
    
    async def on_error(self, job: Job, task_func: Callable[..., Any], args: tuple, kwargs: dict, error: Exception) -> Exception:
        """Called when a job raises an exception.
        
        This method can modify the exception or perform cleanup actions.
        
        Args:
            job: The job that raised the exception
            task_func: The task function that raised the exception
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            error: The exception that was raised
            
        Returns:
            Modified exception
        """
        return error