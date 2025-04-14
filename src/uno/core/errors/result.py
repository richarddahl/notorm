# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Result objects for functional error handling in the Uno framework.

This module implements the Result pattern (also known as the Either pattern)
for handling errors in a functional way without relying on exceptions.
"""

from typing import TypeVar, Generic, Optional, Callable, cast, Any, List, Dict, Union, Protocol, runtime_checkable
import traceback
import inspect
import functools
from dataclasses import dataclass
from uno.core.errors.base import UnoError, ErrorCode, get_error_context

T = TypeVar('T')
E = TypeVar('E', bound=Exception)
U = TypeVar('U')


@runtime_checkable
class HasToDict(Protocol):
    """
    Protocol for objects that can be converted to dictionaries.
    """
    def to_dict(self) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class Success(Generic[T]):
    """
    Represents a successful result with a value.
    
    Attributes:
        value: The successful result value
    """
    
    value: T
    
    @property
    def is_success(self) -> bool:
        """Check if the result is successful."""
        return True
    
    @property
    def is_failure(self) -> bool:
        """Check if the result is a failure."""
        return False
    
    @property
    def error(self) -> None:
        """Get the error if the result is a failure."""
        return None
    
    def map(self, func: Callable[[T], U]) -> 'Result[U]':
        """
        Map the value of a successful result.
        
        Args:
            func: The function to apply to the value
            
        Returns:
            A new Success with the mapped value, or the original Failure
        """
        try:
            return Success(func(self.value))
        except Exception as e:
            return Failure(e)
    
    def flat_map(self, func: Callable[[T], 'Result[U]']) -> 'Result[U]':
        """
        Apply a function that returns a Result to the value of a successful result.
        
        Args:
            func: The function to apply to the value
            
        Returns:
            The Result returned by the function, or the original Failure
        """
        try:
            return func(self.value)
        except Exception as e:
            return Failure(e)
    
    def on_success(self, func: Callable[[T], Any]) -> 'Success[T]':
        """
        Execute a function with the value if the result is successful.
        
        Args:
            func: The function to execute
            
        Returns:
            The original Result
        """
        try:
            func(self.value)
        except Exception:
            # Ignore exceptions in the handler
            pass
        return self
    
    def on_failure(self, func: Callable[[Exception], Any]) -> 'Success[T]':
        """
        Execute a function with the error if the result is a failure.
        
        Args:
            func: The function to execute
            
        Returns:
            The original Result
        """
        # No-op for Success
        return self
    
    # Backward compatibility methods for tests
    def unwrap(self) -> T:
        """
        Unwrap a successful result to get its value.
        
        Returns:
            The value of the successful result
            
        Raises:
            RuntimeError: If the result is a failure
        """
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        """
        Unwrap a result, returning a default value if it's a failure.
        
        Args:
            default: The default value to return if the result is a failure
            
        Returns:
            The value of the successful result, or the default value
        """
        return self.value
    
    def unwrap_or_else(self, func: Callable[[Exception], T]) -> T:
        """
        Unwrap a result, computing a default value from the error if it's a failure.
        
        Args:
            func: The function to compute the default value from the error
            
        Returns:
            The value of the successful result, or the computed default value
        """
        return self.value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary.
        
        Returns:
            A dictionary representation of the result
        """
        if isinstance(self.value, dict):
            return {"status": "success", "data": self.value}
        elif isinstance(self.value, HasToDict):
            return {"status": "success", "data": self.value.to_dict()}
        else:
            return {"status": "success", "data": self.value}
    
    def __str__(self) -> str:
        """String representation of a successful result."""
        return f"Success({self.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of a successful result."""
        return f"Success({repr(self.value)})"


@dataclass(frozen=True)
class Failure(Generic[T]):
    """
    Represents a failed result with an error.
    
    Attributes:
        error: The error that caused the failure
        traceback: The traceback at the time of failure (optional)
    """
    
    error: Exception
    traceback: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Initialize the traceback if not provided."""
        if self.traceback is None:
            # We can't set attributes directly due to frozen=True
            object.__setattr__(self, 'traceback', ''.join(traceback.format_exc()))
    
    @property
    def is_success(self) -> bool:
        """Check if the result is successful."""
        return False
    
    @property
    def is_failure(self) -> bool:
        """Check if the result is a failure."""
        return True
    
    @property
    def value(self) -> None:
        """Get the value if the result is successful."""
        return None
    
    def map(self, func: Callable[[T], U]) -> 'Failure[U]':
        """
        Map the value of a successful result.
        
        Args:
            func: The function to apply to the value
            
        Returns:
            The original Failure
        """
        # For type correctness, we need to cast to Failure[U]
        return cast(Failure[U], self)
    
    def flat_map(self, func: Callable[[T], 'Result[U]']) -> 'Failure[U]':
        """
        Apply a function that returns a Result to the value of a successful result.
        
        Args:
            func: The function to apply to the value
            
        Returns:
            The original Failure
        """
        # For type correctness, we need to cast to Failure[U]
        return cast(Failure[U], self)
    
    def on_success(self, func: Callable[[T], Any]) -> 'Failure[T]':
        """
        Execute a function with the value if the result is successful.
        
        Args:
            func: The function to execute
            
        Returns:
            The original Result
        """
        # No-op for Failure
        return self
    
    def on_failure(self, func: Callable[[Exception], Any]) -> 'Failure[T]':
        """
        Execute a function with the error if the result is a failure.
        
        Args:
            func: The function to execute
            
        Returns:
            The original Result
        """
        try:
            func(self.error)
        except Exception:
            # Ignore exceptions in the handler
            pass
        return self
    
    # Backward compatibility methods for tests
    def unwrap(self) -> T:
        """
        Unwrap a successful result to get its value.
        
        Raises:
            RuntimeError: Since this is a failure
        """
        raise RuntimeError(f"Cannot unwrap a Failure: {self.error}")
    
    def unwrap_or(self, default: T) -> T:
        """
        Unwrap a result, returning a default value if it's a failure.
        
        Args:
            default: The default value to return if the result is a failure
            
        Returns:
            The default value since this is a failure
        """
        return default
    
    def unwrap_or_else(self, func: Callable[[Exception], T]) -> T:
        """
        Unwrap a result, computing a default value from the error if it's a failure.
        
        Args:
            func: The function to compute the default value from the error
            
        Returns:
            The computed default value since this is a failure
        """
        return func(self.error)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary.
        
        Returns:
            A dictionary representation of the result
        """
        if isinstance(self.error, UnoError):
            return {
                "status": "error",
                "error": self.error.to_dict()
            }
        else:
            # Create a generic error structure
            error_detail = {
                "message": str(self.error),
                "error_code": ErrorCode.UNKNOWN_ERROR,
                "context": get_error_context()
            }
            if hasattr(self.error, "__dict__"):
                # Include any public attributes of the exception
                for key, value in self.error.__dict__.items():
                    if not key.startswith("_") and key not in error_detail:
                        error_detail[key] = value
                        
            return {
                "status": "error",
                "error": error_detail
            }
    
    def __str__(self) -> str:
        """String representation of a failed result."""
        return f"Failure({self.error})"
    
    def __repr__(self) -> str:
        """Detailed string representation of a failed result."""
        return f"Failure({repr(self.error)})"


# Type alias for Result
Result = Union[Success[T], Failure[T]]

# Alias Ok for backward compatibility
Ok = Success

# Alias Err for backward compatibility
Err = Failure


def of(value: T) -> Result[T]:
    """
    Create a successful result with a value.
    
    Args:
        value: The value
        
    Returns:
        A successful result
    """
    return Success(value)


def failure(error: Exception) -> Result[T]:
    """
    Create a failed result with an error.
    
    Args:
        error: The error
        
    Returns:
        A failed result
    """
    return Failure(error)


def from_exception(func: Callable[..., T]) -> Callable[..., Result[T]]:
    """
    Decorator to convert a function that might raise exceptions to one that returns a Result.
    
    Args:
        func: The function to decorate
        
    Returns:
        A function that returns a Result
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Result[T]:
        try:
            return Success(func(*args, **kwargs))
        except Exception as e:
            return Failure(e)
    return wrapper


async def from_awaitable(awaitable: Any) -> Result[T]:
    """
    Convert an awaitable that might raise exceptions to a Result.
    
    Args:
        awaitable: The awaitable
        
    Returns:
        A Result
    """
    try:
        return Success(await awaitable)
    except Exception as e:
        return Failure(e)


def combine(results: List[Result[T]]) -> Result[List[T]]:
    """
    Combine multiple Results into a single Result.
    
    Args:
        results: The Results to combine
        
    Returns:
        A Success with a list of values if all Results are successful,
        or the first Failure
    """
    values: List[T] = []
    for result in results:
        if result.is_failure:
            return cast(Failure[List[T]], result)
        if result.value is not None:  # Check for None to satisfy type checker
            values.append(result.value)
    return Success(values)


def combine_dict(results: Dict[str, Result[T]]) -> Result[Dict[str, T]]:
    """
    Combine multiple Results in a dictionary into a single Result.
    
    Args:
        results: The Results to combine
        
    Returns:
        A Success with a dictionary of values if all Results are successful,
        or the first Failure
    """
    values: Dict[str, T] = {}
    for key, result in results.items():
        if result.is_failure:
            return cast(Failure[Dict[str, T]], result)
        if result.value is not None:  # Check for None to satisfy type checker
            values[key] = result.value
    return Success(values)