"""
Re-exports for the async module to avoid keyword conflicts.

This module re-exports all names from the uno.core.async module to avoid
the 'async' keyword usage in imports, which can cause syntax errors in
Python 3.7+.
"""

# Import modules individually with a workaround for the 'async' keyword
import importlib.util
import sys
import os

# Get the directory path
base_dir = os.path.dirname(os.path.abspath(__file__))

# Import modules dynamically
def _import_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Import task_manager.py
task_manager = _import_module(
    "task_manager", 
    os.path.join(base_dir, "async", "task_manager.py")
)

# Import concurrency.py
concurrency = _import_module(
    "concurrency", 
    os.path.join(base_dir, "async", "concurrency.py")
)

# Import context.py
context = _import_module(
    "context", 
    os.path.join(base_dir, "async", "context.py")
)

# Re-export all names
TaskManager = task_manager.TaskManager
TaskGroup = task_manager.TaskGroup
task_context = task_manager.task_context
run_task = task_manager.run_task
run_tasks = task_manager.run_tasks
cancel_on_exit = task_manager.cancel_on_exit

AsyncLock = concurrency.AsyncLock
AsyncSemaphore = concurrency.AsyncSemaphore
AsyncEvent = concurrency.AsyncEvent
Limiter = concurrency.Limiter
RateLimiter = concurrency.RateLimiter
timeout = concurrency.timeout

AsyncContextGroup = context.AsyncContextGroup
async_contextmanager = context.async_contextmanager
AsyncExitStack = context.AsyncExitStack

__all__ = [
    # Task management
    "TaskManager",
    "TaskGroup",
    "task_context",
    "run_task",
    "run_tasks",
    "cancel_on_exit",
    
    # Concurrency primitives
    "AsyncLock",
    "AsyncSemaphore",
    "AsyncEvent",
    "Limiter",
    "RateLimiter",
    "timeout",
    
    # Context managers
    "AsyncContextGroup",
    "async_contextmanager",
    "AsyncExitStack",
]