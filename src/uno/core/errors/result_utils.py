"""
Result Pattern Utilities

This module provides utility functions and decorators to facilitate
working with the Result monad pattern throughout the codebase.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar, cast, overload

from uno.core.errors.result import Result

T = TypeVar("T")  # Success value type
E = TypeVar("E", bound=Exception)  # Error type
R = TypeVar("R")  # Return type for functions
F = TypeVar("F", bound=Callable)  # Function type


def to_result(error_type: type[E] = Exception):
    """
    Decorator for converting exception-based functions to Result-returning functions.

    This decorator wraps a function and catches any exceptions it raises,
    returning them as a Failure result.

    Args:
        error_type: The error type to catch and convert to Failure

    Returns:
        A decorator function

    Example:
        @to_result(ValueError)
        def parse_int(s: str) -> int:
            return int(s)

        # Returns Success(123) or Failure(ValueError)
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs) -> Result[Any, E]:
            try:
                result = await fn(*args, **kwargs)
                return Success(result)
            except Exception as e:
                if isinstance(e, error_type):
                    return Failure(e)
                return Failure(error_type(str(e)))

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs) -> Result[Any, E]:
            try:
                result = fn(*args, **kwargs)
                return Success(result)
            except Exception as e:
                if isinstance(e, error_type):
                    return Failure(e)
                return Failure(error_type(str(e)))

        if asyncio.iscoroutinefunction(fn):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


@overload
def try_catch(fn: Callable[..., T]) -> Result[T, Exception]: ...


@overload
def try_catch(fn: Callable[..., T], *args, **kwargs) -> Result[T, Exception]: ...


def try_catch(fn, *args, **kwargs):
    """
    Execute a function and wrap its result or exception in a Result.

    This function is a convenience wrapper for Result.try_catch
    that directly accepts arguments for the function.

    Args:
        fn: The function to execute
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        A Result containing either the function's return value or any exception raised

    Example:
        # Instead of:
        result = Result.try_catch(lambda: int("123"))

        # You can write:
        result = try_catch(int, "123")
    """
    if args or kwargs:
        return Result.try_catch(lambda: fn(*args, **kwargs))
    return Result.try_catch(fn)


async def async_try_catch(fn, *args, **kwargs) -> Result[Any, Exception]:
    """
    Execute an async function and wrap its result or exception in a Result.

    Args:
        fn: The async function to execute
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        A Result containing either the function's return value or any exception raised
    """
    try:
        if args or kwargs:
            result = await fn(*args, **kwargs)
        else:
            result = await fn()
        return Success(result)
    except Exception as e:
        return Failure(e)


def ensure_result(value_or_result: T | Result[T, E]) -> Result[T, E]:
    """
    Ensure that a value is wrapped in a Result.

    If the value is already a Result, it is returned as is.
    Otherwise, it is wrapped in a Success result.

    Args:
        value_or_result: A value or a Result

    Returns:
        A Result containing the value
    """
    if isinstance(value_or_result, Result):
        return value_or_result
    return Success(value_or_result)


def unwrap_or(result: Result[T, Any], default: R) -> T | R:
    """
    Unwrap a Result or return a default value if it's a Failure.

    Args:
        result: The Result to unwrap
        default: The default value to return if the Result is a Failure

    Returns:
        The value inside the Result, or the default value
    """
    return result.value_or(default)


def unwrap_or_raise(result: Result[T, E]) -> T:
    """
    Unwrap a Result or raise its error if it's a Failure.

    Args:
        result: The Result to unwrap

    Returns:
        The value inside the Result

    Raises:
        The error inside the Result if it's a Failure
    """
    return result.value_or_raise()


class ResultContext:
    """
    A context manager for converting exceptions to Results.

    Example:
        with ResultContext(ValueError) as ctx:
            value = int("abc")  # Raises ValueError

        result = ctx.result  # Failure(ValueError)
    """

    def __init__(self, error_type: type[E] = Exception):
        self.error_type = error_type
        self.result: Result[Any, E] | None = None

    def __enter__(self) -> "ResultContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self.result = Success(None)
        elif issubclass(exc_type, self.error_type):
            self.result = Failure(exc_val)
            return True  # Suppress the exception
        else:
            # Don't handle exceptions that aren't the specified type
            return False

    @property
    def is_success(self) -> bool:
        """Check if the result is a Success."""
        return self.result is not None and self.result.is_success

    @property
    def is_failure(self) -> bool:
        """Check if the result is a Failure."""
        return self.result is not None and self.result.is_failure

    @property
    def value(self) -> Any:
        """Get the value inside the Result."""
        return None if self.result is None else self.result.value

    @property
    def error(self) -> E | None:
        """Get the error inside the Result."""
        return None if self.result is None else self.result.error()


class AsyncResultContext:
    """
    An async context manager for converting exceptions to Results.

    Example:
        async with AsyncResultContext(ValueError) as ctx:
            value = await async_function_that_may_raise()

        result = ctx.result  # Success or Failure
    """

    def __init__(self, error_type: type[E] = Exception):
        self.error_type = error_type
        self.result: Result[Any, E] | None = None

    async def __aenter__(self) -> "AsyncResultContext":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self.result = Success(None)
        elif issubclass(exc_type, self.error_type):
            self.result = Failure(exc_val)
            return True  # Suppress the exception
        else:
            # Don't handle exceptions that aren't the specified type
            return False

    @property
    def is_success(self) -> bool:
        """Check if the result is a Success."""
        return self.result is not None and self.result.is_success

    @property
    def is_failure(self) -> bool:
        """Check if the result is a Failure."""
        return self.result is not None and self.result.is_failure

    @property
    def value(self) -> Any:
        """Get the value inside the Result."""
        return None if self.result is None else self.result.value

    @property
    def error(self) -> E | None:
        """Get the error inside the Result."""
        return None if self.result is None else self.result.error()
