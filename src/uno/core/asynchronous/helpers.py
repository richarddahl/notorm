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
import logging
from uno.core.errors.result import Result
from uno.core.errors.result_utils import AsyncResultContext
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


async def setup_signal_handler(
    sig: signal.Signals,
    handler: Callable[[signal.Signals], Awaitable[None]],
) -> Result[None, Exception]:
    """
    Set up a signal handler using modern patterns.
    Returns Result monad for error handling.
    """
    try:
        loop = asyncio.get_running_loop()

        def _handler():
            asyncio.create_task(handler(sig))

        loop.add_signal_handler(sig, _handler)
        return Success(None)
    except Exception as e:
        return Failure(e)


@contextlib.asynccontextmanager
async def transaction(session: Any) -> Result[None, Exception]:
    """
    Context manager for database transactions using the Result monad.
    Yields Success on commit, Failure on error.
    """
    async with AsyncResultContext(Exception) as ctx:
        try:
            yield
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
    yield ctx.result


class TaskGroup:
    """
    TaskGroup for structured concurrency.

    This class provides a way to manage multiple tasks as a group, similar to
    Python 3.11's asyncio.TaskGroup but with additional features.
    """

    def __init__(self, name: str | None = None, logger: logging.Logger | None = None):
        """
        Initialize the task group.
        """
        self.name = name or f"TaskGroup_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self.tasks: set[asyncio.Task] = set()
        self._entered = False
        self._exited = False

    async def __aenter__(self) -> "Result[TaskGroup, Exception]":
        """Enter the async context, enabling task creation. Returns Result."""
        self._entered = True
        return Success(self)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, cancelling all tasks. Errors returned as Failure."""
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
        # Collect exceptions from tasks
        errors = []
        for task in self.tasks:
            if task.done() and not task.cancelled():
                exc = task.exception()
                if exc is not None and exc_type is None:
                    errors.append(exc)
        if errors:
            return Failure(errors)
        return Success(None)

    def create_task(
        self, coro: Awaitable[T], name: str | None = None
    ) -> Result[asyncio.Task, Exception]:
        """
        Create a task in this group. Returns Result.
        """
        if not self._entered or self._exited:
            return Failure(RuntimeError("TaskGroup not active"))
        task_name = name or f"{self.name}_{len(self.tasks)}"
        try:
            task = asyncio.create_task(coro, name=task_name)
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
            return Success(task)
        except Exception as e:
            return Failure(e)

    @property
    def active_tasks(self) -> list[asyncio.Task]:
        """Get the list of active (unfinished) tasks."""
        return [task for task in self.tasks if not task.done()]

    @property
    def completed_tasks(self) -> list[asyncio.Task]:
        """Get the list of completed tasks."""
        return [task for task in self.tasks if task.done() and not task.cancelled()]

    @property
    def cancelled_tasks(self) -> list[asyncio.Task]:
        """Get the list of cancelled tasks."""
        return [task for task in self.tasks if task.cancelled()]

    async def cancel_all(self) -> None:
        """Cancel all tasks in the group."""
        for task in self.tasks:
            if not task.done():
                task.cancel()

        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
