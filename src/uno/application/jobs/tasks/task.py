"""Task definition and registration for the background processing system.

This module provides the core mechanisms for defining tasks that can be
executed by the background processing system.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast, get_type_hints
import asyncio
import functools
import importlib
import inspect
import logging
import time
from datetime import datetime

from uno.jobs.tasks.middleware import TaskMiddleware

T = TypeVar('T')
TaskFunc = TypeVar('TaskFunc', bound=Callable[..., Any])

# Global state
_registry: Dict[str, Dict[str, Any]] = {}
_middleware: List[TaskMiddleware] = []


class TaskRegistry:
    """Registry for tasks in the background processing system.
    
    This class provides methods for registering, retrieving, and managing
    task definitions.
    """
    
    @staticmethod
    def register(
        func: Callable[..., Any],
        name: Optional[str] = None,
        version: Optional[str] = None,
        **options: Any
    ) -> str:
        """Register a function as a task.
        
        Args:
            func: The function to register
            name: Optional custom name for the task
            version: Optional version for the task
            **options: Additional task options
            
        Returns:
            The registered task name
            
        Raises:
            ValueError: If the task is already registered with a different function
        """
        # Determine task name (module.function if not explicitly provided)
        task_name = name or f"{func.__module__}.{func.__qualname__}"
        
        # Generate a unique identifier including version if provided
        if version:
            task_id = f"{task_name}@{version}"
        else:
            task_id = task_name
        
        # Check if already registered with a different function
        if task_id in _registry and _registry[task_id]["func"] is not func:
            raise ValueError(f"Task already registered with name: {task_id}")
        
        # Get type hints for validation
        type_hints = get_type_hints(func)
        return_type = type_hints.get("return")
        
        # Register the task
        _registry[task_id] = {
            "func": func,
            "name": task_name,
            "version": version,
            "type_hints": type_hints,
            "return_type": return_type,
            "is_async": asyncio.iscoroutinefunction(func),
            "options": options,
        }
        
        return task_id
    
    @staticmethod
    def get_task(name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a task by name and optional version.
        
        Args:
            name: The name of the task
            version: Optional version of the task
            
        Returns:
            Task definition or None if not found
        """
        # Generate task ID based on name and version
        task_id = f"{name}@{version}" if version else name
        
        return _registry.get(task_id)
    
    @staticmethod
    def has_task(name: str, version: Optional[str] = None) -> bool:
        """Check if a task exists.
        
        Args:
            name: The name of the task
            version: Optional version of the task
            
        Returns:
            True if the task exists, False otherwise
        """
        # Generate task ID based on name and version
        task_id = f"{name}@{version}" if version else name
        
        return task_id in _registry
    
    @staticmethod
    def get_all_tasks() -> Dict[str, Dict[str, Any]]:
        """Get all registered tasks.
        
        Returns:
            Dictionary of task definitions keyed by task ID
        """
        return _registry.copy()
    
    @staticmethod
    def unregister(name: str, version: Optional[str] = None) -> bool:
        """Unregister a task.
        
        Args:
            name: The name of the task
            version: Optional version of the task
            
        Returns:
            True if the task was unregistered, False if not found
        """
        # Generate task ID based on name and version
        task_id = f"{name}@{version}" if version else name
        
        if task_id in _registry:
            del _registry[task_id]
            return True
        return False
    
    @staticmethod
    def import_task(task_name: str) -> Optional[Dict[str, Any]]:
        """Dynamically import and register a task by its full path.
        
        Args:
            task_name: Full path to the task (module.function)
            
        Returns:
            Task definition or None if not found or failed to import
            
        Raises:
            ImportError: If the module or function cannot be imported
        """
        # Check if already registered
        if task_name in _registry:
            return _registry[task_name]
        
        # Split into module and function parts
        parts = task_name.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(f"Invalid task name format: {task_name}")
        
        module_path, func_name = parts
        
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the function
            func = getattr(module, func_name)
            
            # Register the task
            TaskRegistry.register(func)
            
            return _registry[task_name]
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to import task {task_name}: {e}")


def task(
    _func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    version: Optional[str] = None,
    max_retries: int = 0,
    retry_delay: int = 60,
    timeout: Optional[int] = None,
    queue: str = "default",
    priority: str = "normal",
    description: Optional[str] = None,
    asynchronous: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    unique: bool = False,
    unique_key: Optional[Callable[..., str]] = None,
    retry_for_exceptions: Optional[List[Type[Exception]]] = None,
    retry_backoff: bool = False,
    retry_backoff_factor: float = 2.0,
    retry_jitter: bool = False,
    middleware: Optional[List[TaskMiddleware]] = None,
    base: Optional[Type['Task']] = None,
    **kwargs: Any
) -> Any:
    """Decorator to mark a function as a task.
    
    This decorator registers a function as a task that can be executed by
    the background processing system. It supports both synchronous and
    asynchronous functions.
    
    Args:
        _func: The function to decorate (used for bare decorator)
        name: Optional custom name for the task
        version: Optional version for the task
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Optional timeout in seconds
        queue: Default queue for this task
        priority: Default priority for this task
        description: Optional description of the task
        asynchronous: Whether the task is asynchronous (auto-detected if None)
        tags: Optional tags for categorization
        unique: Whether the task should be unique (only one running instance)
        unique_key: Function to generate a unique key from the task arguments
        retry_for_exceptions: List of exceptions that should trigger a retry
        retry_backoff: Whether to use exponential backoff for retries
        retry_backoff_factor: Multiplier for exponential backoff
        retry_jitter: Whether to add random jitter to retry delays
        middleware: List of middleware to apply to this task
        base: Base task class to inherit options from
        **kwargs: Additional task-specific options
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Determine if the task is asynchronous
        is_async = asynchronous
        if is_async is None:
            is_async = asyncio.iscoroutinefunction(func)
        
        # Prepare options
        task_options = {
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "timeout": timeout,
            "queue": queue,
            "priority": priority,
            "description": description or func.__doc__,
            "asynchronous": is_async,
            "tags": tags or [],
            "unique": unique,
            "unique_key": unique_key,
            "retry_for_exceptions": retry_for_exceptions,
            "retry_backoff": retry_backoff,
            "retry_backoff_factor": retry_backoff_factor,
            "retry_jitter": retry_jitter,
            "middleware": middleware or [],
            "base": base,
            **kwargs
        }
        
        # If a base class is provided, inherit options
        if base is not None:
            for key, value in base.__dict__.items():
                if key not in task_options or task_options[key] is None:
                    task_options[key] = value
        
        # Register the task
        task_id = TaskRegistry.register(func, name=name, version=version, **task_options)
        
        @functools.wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        
        # Add task info to the wrapped function
        wrapped.__task_id__ = task_id  # type: ignore
        wrapped.name = name or f"{func.__module__}.{func.__qualname__}"  # type: ignore
        wrapped.version = version  # type: ignore
        wrapped.options = task_options  # type: ignore
        
        # Add hooks
        wrapped.on_success = lambda callback: _add_success_callback(task_id, callback)  # type: ignore
        wrapped.on_failure = lambda callback: _add_failure_callback(task_id, callback)  # type: ignore
        wrapped.on_retry = lambda callback: _add_retry_callback(task_id, callback)  # type: ignore
        
        # Add signature manipulation method
        wrapped.s = lambda *a, **kw: _signature(wrapped, args=a, kwargs=kw)  # type: ignore
        
        return wrapped
    
    # Handle both @task and @task(...) forms
    if _func is None:
        return decorator
    return decorator(_func)


def _add_success_callback(task_id: str, callback: Callable[[Any, Any], Any]) -> None:
    """Add a success callback to a task.
    
    Args:
        task_id: ID of the task
        callback: Callback function to add
    """
    if task_id in _registry:
        options = _registry[task_id]["options"]
        success_callbacks = options.get("success_callbacks", [])
        success_callbacks.append(callback)
        options["success_callbacks"] = success_callbacks


def _add_failure_callback(task_id: str, callback: Callable[[Any, Any], Any]) -> None:
    """Add a failure callback to a task.
    
    Args:
        task_id: ID of the task
        callback: Callback function to add
    """
    if task_id in _registry:
        options = _registry[task_id]["options"]
        failure_callbacks = options.get("failure_callbacks", [])
        failure_callbacks.append(callback)
        options["failure_callbacks"] = failure_callbacks


def _add_retry_callback(task_id: str, callback: Callable[[Any, Any, int], Any]) -> None:
    """Add a retry callback to a task.
    
    Args:
        task_id: ID of the task
        callback: Callback function to add
    """
    if task_id in _registry:
        options = _registry[task_id]["options"]
        retry_callbacks = options.get("retry_callbacks", [])
        retry_callbacks.append(callback)
        options["retry_callbacks"] = retry_callbacks


def _signature(func: Callable[..., Any], args: tuple = (), kwargs: dict = None) -> Dict[str, Any]:
    """Create a task signature for delayed execution.
    
    Args:
        func: Function to create a signature for
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        
    Returns:
        Task signature as a dictionary
    """
    kwargs = kwargs or {}
    
    # Get task ID from the wrapped function
    task_id = getattr(func, "__task_id__", None)
    if task_id is None:
        raise ValueError("Function is not a registered task")
    
    return {
        "task": task_id,
        "args": args,
        "kwargs": kwargs,
    }


class Task:
    """Base class for task definitions.
    
    This class can be subclassed to create tasks with shared behavior
    and default options. Subclasses can define hooks and common functionality
    that will be inherited by tasks using this class as a base.
    """
    
    # Default options that can be overridden by subclasses
    max_retries = 0
    retry_delay = 60
    timeout = None
    queue = "default"
    priority = "normal"
    tags = []
    unique = False
    retry_backoff = False
    retry_backoff_factor = 2.0
    retry_jitter = False
    
    async def validate_input(self, *args: Any, **kwargs: Any) -> None:
        """Validate task input before execution.
        
        This method can be overridden to implement input validation.
        
        Args:
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task
            
        Raises:
            ValueError: If input validation fails
        """
        pass
    
    async def pre_execute(self, *args: Any, **kwargs: Any) -> tuple:
        """Pre-execution hook.
        
        This method is called before the actual task execution and can
        modify the arguments passed to the task.
        
        Args:
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task
            
        Returns:
            Tuple of (args, kwargs) to use for execution
        """
        return args, kwargs
    
    async def post_execute(self, result: Any) -> Any:
        """Post-execution hook.
        
        This method is called after successful task execution and can
        modify the result before it's stored.
        
        Args:
            result: The result of the task execution
            
        Returns:
            Modified result
        """
        return result
    
    async def on_error(self, error: Exception) -> None:
        """Error handling hook.
        
        This method is called when an error occurs during task execution.
        
        Args:
            error: The exception that occurred
        """
        pass
    
    async def report_result(self, result: Any) -> None:
        """Result reporting hook.
        
        This method is called after the task result has been stored.
        
        Args:
            result: The result of the task execution
        """
        pass