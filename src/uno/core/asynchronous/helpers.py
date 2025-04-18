"""
Helper functions for modern async patterns.

This module provides utility functions for modern async patterns, including:
- Signal handling without direct event loop access
- TaskGroup for structured concurrency
- Transaction context manager
"""

import asyncio
import signal
import contextlib
from typing import Any, Awaitable, Callable, TypeVar, List, Set, Optional
import logging

T = TypeVar('T')


async def setup_signal_handler(
    sig: signal.Signals,
    handler: Callable[[signal.Signals], Awaitable[None]],
) -> None:
    """
    Set up a signal handler using modern patterns.
    
    Args:
        sig: Signal to handle
        handler: Async handler function
    """
    loop = asyncio.get_running_loop()
    
    def _handler():
        asyncio.create_task(handler(sig))
    
    loop.add_signal_handler(sig, _handler)


@contextlib.asynccontextmanager
async def transaction(session: Any) -> None:
    """
    Context manager for database transactions.
    
    Args:
        session: Database session
        
    Yields:
        None
    """
    try:
        yield
        await session.commit()
    except Exception:
        await session.rollback()
        raise


class TaskGroup:
    """
    TaskGroup for structured concurrency.
    
    This class provides a way to manage multiple tasks as a group, similar to
    Python 3.11's asyncio.TaskGroup but with additional features.
    """
    
    def __init__(self, name: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the task group.
        
        Args:
            name: Optional name for the task group
            logger: Optional logger instance
        """
        self.name = name or f"TaskGroup_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self.tasks: Set[asyncio.Task] = set()
        self._entered = False
        self._exited = False
    
    async def __aenter__(self) -> 'TaskGroup':
        """Enter the async context, enabling task creation."""
        self._entered = True
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, cancelling all tasks."""
        if self._exited:
            return
        
        self._exited = True
        
        if not self.tasks:
            return
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Raise any exceptions from tasks
        for task in self.tasks:
            if task.done() and not task.cancelled():
                exc = task.exception()
                if exc is not None and exc_type is None:
                    raise exc
    
    def create_task(self, coro: Awaitable[T], name: Optional[str] = None) -> asyncio.Task[T]:
        """
        Create a task in this group.
        
        Args:
            coro: Coroutine to run as a task
            name: Optional name for the task
            
        Returns:
            The created task
        """
        if not self._entered or self._exited:
            raise RuntimeError("TaskGroup not active")
        
        task_name = name or f"{self.name}_{len(self.tasks)}"
        task = asyncio.create_task(coro, name=task_name)
        self.tasks.add(task)
        
        # Remove the task from the set when it's done
        task.add_done_callback(self.tasks.discard)
        
        return task
    
    @property
    def active_tasks(self) -> List[asyncio.Task]:
        """Get the list of active (unfinished) tasks."""
        return [task for task in self.tasks if not task.done()]
    
    @property
    def completed_tasks(self) -> List[asyncio.Task]:
        """Get the list of completed tasks."""
        return [task for task in self.tasks if task.done() and not task.cancelled()]
    
    @property
    def cancelled_tasks(self) -> List[asyncio.Task]:
        """Get the list of cancelled tasks."""
        return [task for task in self.tasks if task.cancelled()]
    
    async def cancel_all(self) -> None:
        """Cancel all tasks in the group."""
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
