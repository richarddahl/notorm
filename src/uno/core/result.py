"""
Result objects for error handling in the Uno framework.

This module implements the Result pattern (also known as the Either pattern)
for handling errors in a functional way without relying on exceptions.
"""

from typing import TypeVar, Generic, Optional, Callable, cast, Any, List, Dict, Union
import traceback
import inspect
import functools
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E', bound=Exception)
U = TypeVar('U')


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
    
    def on_success(self, func: Callable[[T], Any]) -> 'Result[T]':
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
    
    def on_failure(self, func: Callable[[Exception], Any]) -> 'Result[T]':
        """
        Execute a function with the error if the result is a failure.
        
        Args:
            func: The function to execute
            
        Returns:
            The original Result
        """
        # No-op for Success
        return self
    
    def unwrap(self) -> T:
        """
        Unwrap the value of a successful result.
        
        Returns:
            The value
            
        Raises:
            ValueError: If the result is a failure
        """
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        """
        Unwrap the value of a successful result, or return a default value.
        
        Args:
            default: The default value to return if the result is a failure
            
        Returns:
            The value or the default
        """
        return self.value
    
    def unwrap_or_else(self, func: Callable[[Exception], T]) -> T:
        """
        Unwrap the value of a successful result, or compute a default value.
        
        Args:
            func: The function to compute the default value
            
        Returns:
            The value or the computed default
        """
        return self.value
    
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
    
    def unwrap(self) -> T:
        """
        Unwrap the value of a successful result.
        
        Returns:
            The value
            
        Raises:
            Exception: The original error
        """
        raise self.error
    
    def unwrap_or(self, default: T) -> T:
        """
        Unwrap the value of a successful result, or return a default value.
        
        Args:
            default: The default value to return if the result is a failure
            
        Returns:
            The value or the default
        """
        return default
    
    def unwrap_or_else(self, func: Callable[[Exception], T]) -> T:
        """
        Unwrap the value of a successful result, or compute a default value.
        
        Args:
            func: The function to compute the default value
            
        Returns:
            The value or the computed default
        """
        return func(self.error)
    
    def __str__(self) -> str:
        """String representation of a failed result."""
        return f"Failure({self.error})"
    
    def __repr__(self) -> str:
        """Detailed string representation of a failed result."""
        return f"Failure({repr(self.error)})"


# Type alias for Result
Result = Union[Success[T], Failure[T]]


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