"""
Function and class tracing utilities for debugging.

This module provides decorators and utilities for tracing function calls, method calls, and
module functions with detailed argument and return value information, execution time, and
call stack context.
"""

import inspect
import functools
import time
import logging
import traceback
import sys
import os
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, TypeVar, cast
from types import ModuleType


logger = logging.getLogger("uno.debug.trace")


# Type variables for better typing support
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


class FunctionTracer:
    """Tracer for function and method calls."""

    def __init__(
        self,
        log_args: bool = True,
        log_return: bool = True,
        log_exceptions: bool = True,
        log_time: bool = True,
        log_caller: bool = True,
        indent: bool = True,
        level: int = logging.DEBUG,
        logger_instance: logging.Logger | None = None,
        max_arg_length: int = 500,
        max_return_length: int = 500,
    ):
        """Initialize the function tracer.

        Args:
            log_args: Whether to log function arguments
            log_return: Whether to log return values
            log_exceptions: Whether to log exceptions
            log_time: Whether to log execution time
            log_caller: Whether to log the caller information
            indent: Whether to indent nested calls
            level: Logging level to use
            logger_instance: Logger instance to use (defaults to uno.debug.trace)
            max_arg_length: Maximum length for logged arguments
            max_return_length: Maximum length for logged return values
        """
        self.log_args = log_args
        self.log_return = log_return
        self.log_exceptions = log_exceptions
        self.log_time = log_time
        self.log_caller = log_caller
        self.indent = indent
        self.level = level
        self.logger = logger_instance or logger
        self.max_arg_length = max_arg_length
        self.max_return_length = max_return_length

        # Call depth for indentation
        self._call_depth = 0

    def __call__(self, func: F) -> F:
        """Make the tracer callable as a decorator.

        Args:
            func: The function to trace

        Returns:
            The wrapped function
        """

        @functools.wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return self.trace_call(func, args, kwargs)

        return cast(F, wrapped)

    def trace_call(self, func: Callable[..., Any], args: tuple, kwargs: dict) -> Any:
        """Trace a function call.

        Args:
            func: The function being called
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The return value of the function
        """
        func_name = self._get_func_name(func)

        # Get caller information if enabled
        caller_info = ""
        if self.log_caller:
            caller = self._get_caller()
            if caller:
                caller_info = f" (called from {caller})"

        # Prepare indentation
        indent = ""
        if self.indent:
            indent = "  " * self._call_depth
            self._call_depth += 1

        # Log entry
        entry_msg = f"{indent}→ {func_name}{caller_info}"

        # Add arguments if enabled
        if self.log_args and (args or kwargs):
            args_str = self._format_args(func, args, kwargs)
            entry_msg += f" with args: {args_str}"

        self.logger.log(self.level, entry_msg)

        # Execute the function
        start_time = time.time()
        try:
            result = func(*args, **kwargs)

            # Calculate execution time
            execution_time = time.time() - start_time
            time_str = f" [{execution_time:.6f}s]" if self.log_time else ""

            # Log return
            if self.log_return:
                return_str = self._truncate_value(repr(result), self.max_return_length)
                self.logger.log(
                    self.level,
                    f"{indent}← {func_name} returned: {return_str}{time_str}",
                )
            else:
                self.logger.log(
                    self.level, f"{indent}← {func_name} completed{time_str}"
                )

            return result
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            time_str = f" [{execution_time:.6f}s]" if self.log_time else ""

            # Log exception
            if self.log_exceptions:
                self.logger.log(
                    self.level,
                    f"{indent}! {func_name} raised {type(e).__name__}: {str(e)}{time_str}",
                    exc_info=True,
                )

            raise
        finally:
            if self.indent:
                self._call_depth -= 1

    def _get_func_name(self, func: Callable[..., Any]) -> str:
        """Get a readable name for a function.

        Args:
            func: The function

        Returns:
            A string representation of the function name
        """
        if hasattr(func, "__qualname__"):
            return func.__qualname__

        if hasattr(func, "__name__"):
            if hasattr(func, "__module__") and func.__module__ != "__main__":
                return f"{func.__module__}.{func.__name__}"
            return func.__name__

        return str(func)

    def _get_caller(self) -> str | None:
        """Get information about the caller of the traced function.

        Returns:
            A string representation of the caller or None if not available
        """
        stack = inspect.stack()

        # Skip first 3 frames (this function, trace_call, and the wrapper)
        # to get to the actual caller
        if len(stack) >= 4:
            frame = stack[3]
            filename = os.path.basename(frame.filename)
            lineno = frame.lineno
            function = frame.function
            return f"{filename}:{lineno} in {function}"

        return None

    def _format_args(self, func: Callable[..., Any], args: tuple, kwargs: dict) -> str:
        """Format function arguments for logging.

        Args:
            func: The function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            A string representation of the arguments
        """
        arg_parts = []

        # Get function signature if possible
        try:
            sig = inspect.signature(func)
            parameters = list(sig.parameters.values())

            # Handle positional arguments
            for i, arg in enumerate(args):
                if i < len(parameters):
                    param_name = parameters[i].name
                    if param_name == "self" or param_name == "cls":
                        continue
                    arg_parts.append(f"{param_name}={self._format_value(arg)}")
                else:
                    arg_parts.append(self._format_value(arg))

            # Handle keyword arguments
            for name, value in kwargs.items():
                arg_parts.append(f"{name}={self._format_value(value)}")

        except (ValueError, TypeError):
            # Fallback if we can't get the signature
            arg_parts = [self._format_value(arg) for arg in args]
            arg_parts.extend(
                f"{name}={self._format_value(value)}" for name, value in kwargs.items()
            )

        return ", ".join(arg_parts)

    def _format_value(self, value: Any) -> str:
        """Format a value for logging.

        Args:
            value: The value to format

        Returns:
            A string representation of the value
        """
        # Handle common types with potentially large representations
        if hasattr(value, "__class__"):
            if value.__class__.__name__ in ("DataFrame", "Series") and hasattr(
                value, "shape"
            ):
                return (
                    f"<{value.__class__.__name__} shape={getattr(value, 'shape', '?')}>"
                )

            if value.__class__.__name__ in ("ndarray", "Tensor") and hasattr(
                value, "shape"
            ):
                return f"<{value.__class__.__name__} shape={getattr(value, 'shape', '?')} dtype={getattr(value, 'dtype', '?')}>"

            if value.__class__.__name__ in ("list", "tuple", "set") and len(value) > 5:
                return f"<{value.__class__.__name__} with {len(value)} items>"

            if value.__class__.__name__ == "dict" and len(value) > 5:
                return f"<dict with {len(value)} keys: {', '.join(repr(k) for k in list(value.keys())[:3])}...>"

            if value.__class__.__name__ == "str" and len(value) > self.max_arg_length:
                return f"'{value[:self.max_arg_length-3]}...'"

        # For other types, use repr with truncation
        return self._truncate_value(repr(value), self.max_arg_length)

    def _truncate_value(self, value: str, max_length: int) -> str:
        """Truncate a string value if it's too long.

        Args:
            value: The string to truncate
            max_length: Maximum allowed length

        Returns:
            Truncated string
        """
        if len(value) > max_length:
            return value[: max_length - 3] + "..."
        return value


def trace_function(
    func: Optional[F] = None,
    *,
    log_args: bool = True,
    log_return: bool = True,
    log_exceptions: bool = True,
    log_time: bool = True,
    log_caller: bool = True,
    indent: bool = True,
    level: int = logging.DEBUG,
    logger: logging.Logger | None = None,
    max_arg_length: int = 500,
    max_return_length: int = 500,
) -> Union[F, Callable[[F], F]]:
    """Decorator for tracing function calls.

    This can be used as:
    @trace_function
    def my_function():
        ...

    Or with parameters:
    @trace_function(log_args=False)
    def my_function():
        ...

    Args:
        func: The function to decorate (when used without arguments)
        log_args: Whether to log function arguments
        log_return: Whether to log return values
        log_exceptions: Whether to log exceptions
        log_time: Whether to log execution time
        log_caller: Whether to log the caller information
        indent: Whether to indent nested calls
        level: Logging level to use
        logger: Logger instance to use
        max_arg_length: Maximum length for logged arguments
        max_return_length: Maximum length for logged return values

    Returns:
        The decorated function or a decorator function
    """
    tracer = FunctionTracer(
        log_args=log_args,
        log_return=log_return,
        log_exceptions=log_exceptions,
        log_time=log_time,
        log_caller=log_caller,
        indent=indent,
        level=level,
        logger_instance=logger,
        max_arg_length=max_arg_length,
        max_return_length=max_return_length,
    )

    if func is None:
        return tracer

    return tracer(func)


def trace_class(
    cls: Optional[Type[T]] = None,
    *,
    log_args: bool = True,
    log_return: bool = True,
    log_exceptions: bool = True,
    log_time: bool = True,
    log_caller: bool = True,
    indent: bool = True,
    level: int = logging.DEBUG,
    logger: logging.Logger | None = None,
    max_arg_length: int = 500,
    max_return_length: int = 500,
    method_filter: Optional[Callable[[str], bool]] = None,
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """Decorator for tracing all methods of a class.

    Args:
        cls: The class to decorate (when used without arguments)
        log_args: Whether to log method arguments
        log_return: Whether to log return values
        log_exceptions: Whether to log exceptions
        log_time: Whether to log execution time
        log_caller: Whether to log the caller information
        indent: Whether to indent nested calls
        level: Logging level to use
        logger: Logger instance to use
        max_arg_length: Maximum length for logged arguments
        max_return_length: Maximum length for logged return values
        method_filter: Optional function to filter which methods to trace

    Returns:
        The decorated class or a decorator function
    """

    def apply_class_tracer(cls: Type[T]) -> Type[T]:
        tracer = FunctionTracer(
            log_args=log_args,
            log_return=log_return,
            log_exceptions=log_exceptions,
            log_time=log_time,
            log_caller=log_caller,
            indent=indent,
            level=level,
            logger_instance=logger,
            max_arg_length=max_arg_length,
            max_return_length=max_return_length,
        )

        # Apply tracer to methods
        for name, obj in inspect.getmembers(cls):
            # Skip special methods and non-function attributes
            if name.startswith("__") or not inspect.isfunction(obj):
                continue

            # Apply filter if provided
            if method_filter and not method_filter(name):
                continue

            # Apply tracer to the method
            setattr(cls, name, tracer(obj))

        return cls

    if cls is None:
        return apply_class_tracer

    return apply_class_tracer(cls)


def trace_module(
    module: Optional[ModuleType] = None,
    *,
    log_args: bool = True,
    log_return: bool = True,
    log_exceptions: bool = True,
    log_time: bool = True,
    log_caller: bool = True,
    indent: bool = True,
    level: int = logging.DEBUG,
    logger: logging.Logger | None = None,
    max_arg_length: int = 500,
    max_return_length: int = 500,
    function_filter: Optional[Callable[[str], bool]] = None,
) -> ModuleType:
    """Trace all functions in a module.

    Args:
        module: The module to trace
        log_args: Whether to log function arguments
        log_return: Whether to log return values
        log_exceptions: Whether to log exceptions
        log_time: Whether to log execution time
        log_caller: Whether to log the caller information
        indent: Whether to indent nested calls
        level: Logging level to use
        logger: Logger instance to use
        max_arg_length: Maximum length for logged arguments
        max_return_length: Maximum length for logged return values
        function_filter: Optional function to filter which functions to trace

    Returns:
        The modified module
    """
    if module is None:
        # Get the calling module
        frame = inspect.currentframe()
        if frame is None or frame.f_back is None:
            raise ValueError("Could not determine calling module")
        module_name = frame.f_back.f_globals.get("__name__")
        if not module_name:
            raise ValueError("Could not determine calling module name")
        module = sys.modules.get(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")

    tracer = FunctionTracer(
        log_args=log_args,
        log_return=log_return,
        log_exceptions=log_exceptions,
        log_time=log_time,
        log_caller=log_caller,
        indent=indent,
        level=level,
        logger_instance=logger,
        max_arg_length=max_arg_length,
        max_return_length=max_return_length,
    )

    # Apply tracer to functions
    for name, obj in inspect.getmembers(module):
        # Skip imported objects (only trace functions defined in this module)
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            # Apply filter if provided
            if function_filter and not function_filter(name):
                continue

            # Apply tracer to the function
            setattr(module, name, tracer(obj))

    return module
