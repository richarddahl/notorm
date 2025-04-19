# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Enhanced async context management primitives for the Uno framework.

This module provides utilities for managing async contexts, including:
- Improved async context managers with cancellation handling
- Grouping of multiple context managers
- Async exit stack for dynamic context management
"""

import asyncio
import contextlib
import functools
import inspect
import logging
import sys
import traceback
from collections import deque
from contextlib import AsyncExitStack as _AsyncExitStack
from typing import (
    Any, AsyncIterator, AsyncContextManager, Awaitable, Callable, 
    Coroutine, Dict, Generic, List, Optional, Set, Tuple, TypeVar, 
    Union, cast, overload
)


T = TypeVar("T")
R = TypeVar("R")


# Re-export AsyncExitStack from contextlib with its original functionality
AsyncExitStack = _AsyncExitStack


class AsyncContextGroup(Generic[T]):
    """
    Group of async context managers that can be entered and exited together.
    
    This class provides a way to manage multiple async context managers as a unit,
    entering and exiting them together. It's similar to AsyncExitStack but tracks
    the results of each context manager.
    """
    
    def __init__(
        self, 
        *contexts: AsyncContextManager[T],
        name: str = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize an AsyncContextGroup.
        
        Args:
            *contexts: Async context managers to group
            name: Optional name for the group
            logger: Optional logger instance
        """
        self.contexts = list(contexts)
        self.name = name or f"ContextGroup-{id(self)}"
        self.logger = logger or logging.getLogger(__name__)
        self._exit_stack = AsyncExitStack()
        self._results: Dict[AsyncContextManager[T], T] = {}
    
    async def __aenter__(self) -> "AsyncContextGroup[T]":
        """
        Enter all context managers in the group.
        
        Returns:
            Self, for chaining operations
        """
        self.logger.debug(f"Entering context group '{self.name}' with {len(self.contexts)} contexts")
        
        await self._exit_stack.__aenter__()
        
        try:
            # Enter each context manager and collect results
            for ctx in self.contexts:
                result = await ctx.__aenter__()
                self._results[ctx] = result
                # Also register for exit
                self._exit_stack.push_async_exit(ctx.__aexit__)
            
            return self
        
        except Exception as e:
            # If any context manager fails to enter, exit all entered contexts
            self.logger.error(f"Error entering context group '{self.name}': {e}")
            
            # Use exit stack to handle cleanup
            await self._exit_stack.__aexit__(*sys.exc_info())
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit all context managers in the group.
        
        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised
            
        Returns:
            True if the exception was handled, False otherwise
        """
        self.logger.debug(f"Exiting context group '{self.name}'")
        
        # If there was an exception, log it
        if exc_type is not None:
            self.logger.debug(
                f"Exiting context group '{self.name}' with exception: "
                f"{exc_type.__name__}: {exc_val}"
            )
        
        # Use the exit stack to handle exiting all contexts in reverse order
        return await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
    
    async def enter_async_context(self, context: AsyncContextManager[T]) -> T:
        """
        Enter a context manager and add it to the group.
        
        This method can be used to dynamically add context managers to the group.
        
        Args:
            context: The context manager to enter and add
            
        Returns:
            The value yielded by the context manager
            
        Raises:
            RuntimeError: If the group hasn't been entered yet
        """
        if not hasattr(self._exit_stack, '_exit_callbacks'):
            raise RuntimeError("AsyncContextGroup must be entered before calling enter_async_context")
        
        # Enter the context and store the result
        result = await context.__aenter__()
        self._results[context] = result
        
        # Register for exit
        self._exit_stack.push_async_exit(context.__aexit__)
        
        return result
    
    def add(self, ctx: AsyncContextManager[T]) -> None:
        """
        Add a context manager to the group without entering it.
        
        Args:
            ctx: The context manager to add
            
        Raises:
            RuntimeError: If the group has already been entered
        """
        if hasattr(self._exit_stack, '_exit_callbacks'):
            raise RuntimeError(
                f"Cannot add context to group '{self.name}' after it has been entered"
            )
        
        self.contexts.append(ctx)
    
    @property
    def entered(self) -> bool:
        """Check if the group has been entered."""
        return hasattr(self._exit_stack, '_exit_callbacks')
    
    @property
    def results(self) -> Dict[AsyncContextManager[T], T]:
        """Get the results of all entered context managers."""
        return self._results.copy()


def async_contextmanager(func: Callable[..., Coroutine[Any, Any, AsyncIterator[T]]]) -> Callable[..., AsyncContextManager[T]]:
    """
    Enhanced @contextlib.asynccontextmanager decorator with improved error handling.
    
    This decorator creates an async context manager from a generator function.
    It adds improved error handling and resource cleanup compared to the standard
    contextlib.asynccontextmanager.
    
    Args:
        func: Generator function that yields exactly once
        
    Returns:
        Async context manager
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> AsyncContextManager[T]:
        return _AsyncContextManager(func, args, kwargs)
    
    return wrapper


class _AsyncContextManager(AsyncContextManager[T]):
    """
    Async context manager created by @async_contextmanager decorator.
    
    This is an internal class used by the @async_contextmanager decorator.
    """
    
    def __init__(
        self, 
        func: Callable[..., Coroutine[Any, Any, AsyncIterator[T]]], 
        args: Tuple[Any, ...], 
        kwargs: Dict[str, Any]
    ):
        """
        Initialize an _AsyncContextManager.
        
        Args:
            func: Generator function
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.gen: Optional[AsyncIterator[T]] = None
        
        # Set name and qualname from the function
        self.__name__ = func.__name__
        self.__qualname__ = func.__qualname__
    
    async def __aenter__(self) -> T:
        """
        Enter the context manager.
        
        Returns:
            Value yielded by the generator
            
        Raises:
            RuntimeError: If the generator doesn't yield exactly once
        """
        # Create and advance the generator to the first yield
        self.gen = await self.func(*self.args, **self.kwargs).__aiter__()
        
        try:
            # Get the yielded value
            return await self.gen.__anext__()
        except StopAsyncIteration:
            # Generator didn't yield
            raise RuntimeError(
                f"{self.func.__qualname__} didn't yield (expected exactly one yield)"
            ) from None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context manager.
        
        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised
            
        Returns:
            True if the exception was handled, False otherwise
            
        Raises:
            RuntimeError: If the generator yields more than once
        """
        if self.gen is None:
            return False
        
        # If there was an exception, send it to the generator
        if exc_type is not None:
            try:
                # Send exception to generator and process the response
                try:
                    await self.gen.athrow(exc_type, exc_val, exc_tb)
                except StopAsyncIteration:
                    # Generator returned normally after handling exception
                    return True
                except RuntimeError as e:
                    # If the exception is due to the generator already being closed,
                    # just return False
                    if "generator already closed" in str(e):
                        return False
                    raise
                
                # Generator yielded again after handling exception
                raise RuntimeError(
                    f"{self.func.__qualname__} yielded multiple values (expected exactly one yield)"
                )
            
            except Exception as e:
                # If the generator raised an exception other than StopAsyncIteration,
                # let it propagate
                if isinstance(e, StopAsyncIteration):
                    return True
                
                # The generator raised a different exception - let it propagate
                if exc_type is e.__class__:
                    # Same exception type, assume it's just propagating
                    return False
                
                # Different exception type, replace the original exception
                # but keep the original traceback for context
                raise
        
        # No exception, advance the generator to completion
        try:
            # Send None to the generator and process the response
            try:
                await self.gen.__anext__()
            except StopAsyncIteration:
                # Generator returned normally
                return False
            
            # Generator yielded again
            raise RuntimeError(
                f"{self.func.__qualname__} yielded multiple values (expected exactly one yield)"
            )
        
        except Exception as e:
            # If the generator raised an exception, raise it
            raise