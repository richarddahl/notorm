# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Task management utilities for the Uno framework.

This module provides utilities for managing asyncio tasks, including:
- Task cancellation handling
- Task groups for structured concurrency
- Task context management
"""

import asyncio
import contextlib
import functools
import inspect
import logging
import signal
import sys
import time
import traceback
from asyncio import Task, CancelledError
from contextlib import AsyncExitStack
from typing import (
    Any, Awaitable, Callable, Dict, Generic, List, Optional, Set, 
    TypeVar, Union, cast, overload, Coroutine, Collection,
    AsyncContextManager, AsyncIterator, Iterator
)


T = TypeVar("T")
R = TypeVar("R")


class TaskCancelled(Exception):
    """Exception raised when a task is cancelled by the task manager."""
    pass


class TaskError(Exception):
    """Exception raised when a task fails with an error."""
    
    def __init__(self, task_name: str, original_error: Exception):
        """
        Initialize a TaskError.
        
        Args:
            task_name: Name of the task that failed
            original_error: The original exception that caused the failure
        """
        self.task_name = task_name
        self.original_error = original_error
        super().__init__(f"Task '{task_name}' failed: {original_error}")


class TaskGroup:
    """
    A group of related tasks that can be managed together.
    
    TaskGroup provides a way to organize related tasks and ensures they are
    properly cleaned up when the group is closed or cancelled.
    """
    
    def __init__(
        self, 
        name: str = None, 
        cancel_on_error: bool = True,
        logger: logging.Logger | None = None
    ):
        """
        Initialize a TaskGroup.
        
        Args:
            name: Optional name for the task group
            cancel_on_error: Whether to cancel all tasks if one fails
            logger: Optional logger instance
        """
        self.name = name or f"TaskGroup-{id(self)}"
        self.cancel_on_error = cancel_on_error
        self.logger = logger or logging.getLogger(__name__)
        self._tasks: Set[asyncio.Task] = set()
        self._errors: list[Exception] = []
        self._exit_stack = AsyncExitStack()
        self._closed = False
    
    async def __aenter__(self) -> "TaskGroup":
        """Enter the task group context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the task group context, cancelling all tasks and cleaning up resources.
        
        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised
            
        Returns:
            True if the exception was handled, False otherwise
        """
        try:
            # If exiting with an exception and cancel_on_error is True,
            # or if explicitly closing, cancel all tasks
            if ((exc_type is not None and self.cancel_on_error) or self._closed):
                await self.cancel_all()
            
            # Wait for all tasks to complete
            await self.wait_all()
            
            # Close the exit stack
            await self._exit_stack.aclose()
            
            # If there were task errors and no other exception, raise the first task error
            if not exc_type and self._errors:
                raise self._errors[0]
            
            # Don't suppress any exceptions passed in
            return False
        finally:
            # Clear tasks and errors
            self._tasks.clear()
            self._errors.clear()
            self._closed = True
    
    def create_task(
        self, 
        coro: Coroutine[Any, Any, T], 
        name: str | None = None
    ) -> asyncio.Task[T]:
        """
        Create a task and add it to the group.
        
        Args:
            coro: The coroutine to schedule as a task
            name: Optional name for the task
            
        Returns:
            The created task
            
        Raises:
            RuntimeError: If the task group is closed
        """
        if self._closed:
            raise RuntimeError(f"Task group '{self.name}' is closed")
        
        # Create the task with the name
        task_name = name or f"{self.name}-Task-{len(self._tasks)}"
        task = asyncio.create_task(coro, name=task_name)
        
        # Store the task name for error reporting
        setattr(task, 'custom_name', task_name)
        
        # Add the task to the set and add a callback to remove it when done
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)
        
        self.logger.debug(f"Task '{task_name}' created in group '{self.name}'")
        return task
    
    def add_task(self, task: asyncio.Task[T]) -> asyncio.Task[T]:
        """
        Add an existing task to the group.
        
        Args:
            task: The task to add
            
        Returns:
            The added task
            
        Raises:
            RuntimeError: If the task group is closed
        """
        if self._closed:
            raise RuntimeError(f"Task group '{self.name}' is closed")
        
        # Add the task to the set and add a callback to remove it when done
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)
        
        self.logger.debug(f"Task '{task.get_name()}' added to group '{self.name}'")
        return task
    
    async def wait_all(self) -> None:
        """
        Wait for all tasks in the group to complete.
        
        This method doesn't cancel any tasks, it just waits for them to finish.
        """
        if not self._tasks:
            return
        
        self.logger.debug(f"Waiting for {len(self._tasks)} tasks in group '{self.name}'")
        
        # Create a copy of the tasks to avoid modification during iteration
        pending = list(self._tasks)
        
        # Wait for all tasks to complete
        while pending:
            done, pending = await asyncio.wait(
                pending, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Check for errors in completed tasks
            for task in done:
                if task in self._tasks:
                    # Task is already handled by _on_task_done
                    pass
    
    async def cancel_all(self) -> None:
        """
        Cancel all tasks in the group and wait for them to complete.
        
        This method cancels all tasks and waits for them to finish.
        """
        if not self._tasks:
            return
        
        self.logger.debug(f"Cancelling {len(self._tasks)} tasks in group '{self.name}'")
        
        # Create a copy of the tasks to avoid modification during iteration
        tasks = list(self._tasks)
        
        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.wait(tasks)
    
    @property
    def errors(self) -> list[Exception]:
        """Get a list of errors that occurred in the task group."""
        return self._errors.copy()
    
    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred in the task group."""
        return len(self._errors) > 0
    
    @property
    def tasks(self) -> Set[asyncio.Task]:
        """Get a set of all tasks in the group."""
        return self._tasks.copy()
    
    async def close(self) -> None:
        """
        Close the task group, cancelling all tasks.
        
        This method ensures all tasks are cancelled and resources are cleaned up.
        """
        self._closed = True
        await self.cancel_all()
        await self._exit_stack.aclose()
        self._tasks.clear()
    
    def _on_task_done(self, task: asyncio.Task) -> None:
        """
        Handle task completion.
        
        Args:
            task: The completed task
        """
        # Remove the task from the set
        self._tasks.discard(task)
        
        # Handle task result or exception
        if not task.cancelled():
            try:
                # Get the task result to handle any exceptions
                task.result()
            except Exception as e:
                if not isinstance(e, asyncio.CancelledError):
                    # Use the custom name if available, otherwise fall back to get_name()
                    task_name = getattr(task, 'custom_name', task.get_name())
                    self.logger.error(
                        f"Task '{task_name}' in group '{self.name}' failed: {e}",
                        exc_info=True
                    )
                    
                    # Add the error to the list
                    self._errors.append(TaskError(task_name, e))
                    
                    # Cancel all tasks if configured to do so
                    if self.cancel_on_error and self._tasks:
                        self.logger.debug(
                            f"Cancelling {len(self._tasks)} tasks in group "
                            f"'{self.name}' due to error in task '{task_name}'"
                        )
                        for t in list(self._tasks):
                            if not t.done():
                                t.cancel()


@contextlib.asynccontextmanager
async def task_context(
    name: str = None, 
    cancel_on_error: bool = True,
    logger: logging.Logger | None = None
) -> AsyncIterator[TaskGroup]:
    """
    Context manager for managing a group of related tasks.
    
    Args:
        name: Optional name for the task group
        cancel_on_error: Whether to cancel all tasks if one fails
        logger: Optional logger instance
        
    Yields:
        A TaskGroup instance
    """
    group = TaskGroup(name=name, cancel_on_error=cancel_on_error, logger=logger)
    try:
        yield group
    finally:
        await group.close()


# Module-level singleton instance
_task_manager_instance: Optional["TaskManager"] = None


def get_task_manager(logger: logging.Logger | None = None -> "TaskManager":
    """
    Get the singleton instance of the TaskManager.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        The TaskManager instance
    """
    global _task_manager_instance
    
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager(logger)
    
    return _task_manager_instance


class TaskManager:
    """
    Manager for handling multiple task groups and providing global task management.
    
    The TaskManager provides a centralized way to manage multiple task groups,
    handle signals for graceful shutdown, and provide utilities for task handling.
    """
    
    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize a TaskManager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._groups: Dict[str, TaskGroup] = {}
        self._signal_handlers_installed = False
        self._started = False
        self._shutdown_complete = False
        
    async def start(self) -> None:
        """Start the task manager and install signal handlers."""
        if self._started:
            return
            
        self.logger.info("Starting TaskManager")
        
        # Install signal handlers
        self.add_signal_handlers()
        
        self._started = True
    
    async def shutdown(self) -> None:
        """
        Shut down the task manager and cancel all tasks.
        
        This method waits for all tasks to complete or be cancelled.
        """
        if self._shutdown_complete:
            return
            
        self.logger.info("Shutting down TaskManager")
        
        # Cancel all tasks
        await self.cancel_all_tasks()
        
        self._shutdown_complete = True
        
    async def cancel_all_tasks(self) -> None:
        """Cancel all tasks in all groups."""
        self.logger.info("Cancelling all tasks")
        
        # Cancel all tasks in all groups
        for group in self._groups.values():
            await group.cancel_all()
    
    def create_group(
        self, 
        name: str, 
        cancel_on_error: bool = True
    ) -> TaskGroup:
        """
        Create a new task group.
        
        Args:
            name: Name for the task group
            cancel_on_error: Whether to cancel all tasks if one fails
            
        Returns:
            The created TaskGroup
            
        Raises:
            ValueError: If a group with the same name already exists
        """
        if name in self._groups:
            raise ValueError(f"Task group '{name}' already exists")
        
        group = TaskGroup(name=name, cancel_on_error=cancel_on_error, logger=self.logger)
        self._groups[name] = group
        return group
    
    def get_group(self, name: str) -> Optional[TaskGroup]:
        """
        Get a task group by name.
        
        Args:
            name: Name of the task group
            
        Returns:
            The TaskGroup if found, None otherwise
        """
        return self._groups.get(name)
    
    def create_task(
        self, 
        coro: Coroutine[Any, Any, T], 
        group: str | None = None,
        name: str | None = None
    ) -> asyncio.Task[T]:
        """
        Create a task in the specified group.
        
        Args:
            coro: The coroutine to schedule as a task
            group: Optional name of the task group (creates a default group if None)
            name: Optional name for the task
            
        Returns:
            The created task
        """
        # Use default group if none specified
        group_name = group or "default"
        
        # Create the group if it doesn't exist
        if group_name not in self._groups:
            self._groups[group_name] = TaskGroup(
                name=group_name, 
                logger=self.logger
            )
        
        # Create the task in the group
        return self._groups[group_name].create_task(coro, name=name)
    
    def add_signal_handlers(self) -> None:
        """Add signal handlers for graceful shutdown."""
        if self._signal_handlers_installed:
            return
        
        loop = asyncio.get_running_loop()
        
        # Add signal handlers for SIGINT, SIGTERM
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_shutdown_signal(s))
            )
        
        self._signal_handlers_installed = True
        self.logger.debug("Signal handlers installed")
    
    async def _handle_shutdown_signal(self, sig: signal.Signals) -> None:
        """
        Handle shutdown signal by cancelling all tasks.
        
        Args:
            sig: The signal that triggered the shutdown
        """
        self.logger.info(f"Received signal {sig.name}, shutting down...")
        
        if self._is_shutting_down:
            self.logger.warning("Received second shutdown signal, forcing exit")
            sys.exit(1)
        
        self._is_shutting_down = True
        
        # Set the shutdown event
        self._shutdown_event.set()
        
        # Cancel all tasks in all groups
        for group_name, group in list(self._groups.items()):
            self.logger.debug(f"Cancelling tasks in group '{group_name}'")
            await group.cancel_all()
        
        # Clear all groups
        self._groups.clear()
    
    async def shutdown(self) -> None:
        """
        Initiate a graceful shutdown.
        
        This method cancels all tasks and cleans up resources.
        """
        if self._is_shutting_down:
            return
        
        self._is_shutting_down = True
        self._shutdown_event.set()
        
        # Cancel all tasks in all groups
        for group_name, group in list(self._groups.items()):
            self.logger.debug(f"Cancelling tasks in group '{group_name}'")
            await group.cancel_all()
        
        # Clear all groups
        self._groups.clear()
    
    async def wait_for_shutdown(self) -> None:
        """Wait for the shutdown event to be set."""
        await self._shutdown_event.wait()
    
    @property
    def is_shutting_down(self) -> bool:
        """Check if the TaskManager is shutting down."""
        return self._is_shutting_down


async def run_task(
    coro: Coroutine[Any, Any, T], 
    name: str | None = None,
    group: str | None = None,
    handle_errors: bool = True
) -> T:
    """
    Run a coroutine as a task with proper error handling.
    
    Args:
        coro: The coroutine to run
        name: Optional name for the task
        group: Optional task group name
        handle_errors: Whether to handle errors
        
    Returns:
        The result of the coroutine
        
    Raises:
        Exception: If the task fails and handle_errors is False
    """
    manager = get_task_manager()
    
    if group is not None:
        # Run in the specified group
        task = manager.create_task(coro, group=group, name=name)
    else:
        # Run as a standalone task
        task = asyncio.create_task(coro, name=name)
    
    try:
        return await task
    except asyncio.CancelledError:
        raise
    except Exception as e:
        if handle_errors:
            logging.getLogger(__name__).error(
                f"Task '{task.get_name()}' failed: {e}",
                exc_info=True
            )
            raise TaskError(task.get_name(), e) from e
        else:
            raise


async def run_tasks(
    coros: list[Coroutine[Any, Any, Any]], 
    group_name: str | None = None,
    return_when: str = "ALL_COMPLETED",
    handle_errors: bool = True
) -> list[Any]:
    """
    Run multiple coroutines as tasks and wait for them to complete.
    
    Args:
        coros: List of coroutines to run
        group_name: Optional task group name
        return_when: When to return (ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION)
        handle_errors: Whether to handle errors
        
    Returns:
        List of results from the coroutines
        
    Raises:
        TaskError: If any task fails and handle_errors is True
    """
    manager = get_task_manager()
    
    # Create tasks
    if group_name:
        # Get or create group
        group = manager.get_group(group_name)
        if not group:
            group = manager.create_group(group_name)
        
        # Create tasks in the group
        tasks = [group.create_task(coro) for coro in coros]
    else:
        # Create standalone tasks
        tasks = [asyncio.create_task(coro) for coro in coros]
    
    # Wait for tasks to complete
    try:
        done, pending = await asyncio.wait(tasks, return_when=return_when)
        
        # If return_when is not ALL_COMPLETED, cancel any pending tasks
        if return_when != "ALL_COMPLETED" and pending:
            for task in pending:
                task.cancel()
            
            # Wait for cancelled tasks to complete
            await asyncio.wait(pending)
        
        # Get results or handle errors
        results = []
        for task in tasks:
            try:
                results.append(task.result())
            except asyncio.CancelledError:
                results.append(None)
            except Exception as e:
                if handle_errors:
                    logging.getLogger(__name__).error(
                        f"Task '{task.get_name()}' failed: {e}",
                        exc_info=True
                    )
                    results.append(None)
                else:
                    raise
        
        return results
    except Exception as e:
        if handle_errors:
            logging.getLogger(__name__).error(
                f"Error running tasks: {e}",
                exc_info=True
            )
            return [None] * len(coros)
        else:
            raise


@contextlib.asynccontextmanager
async def cancel_on_exit(task: asyncio.Task[T]) -> AsyncIterator[asyncio.Task[T]]:
    """
    Context manager that cancels a task when exiting the context.
    
    Args:
        task: The task to cancel on exit
        
    Yields:
        The task
    """
    try:
        yield task
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass