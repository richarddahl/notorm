"""
Result Pattern Implementation

This module provides a Result class for handling errors without exceptions.
The Result pattern is a way to represent either a successful value or an error.
"""

from typing import (
    Any, Callable, Dict, Generic, Iterator, List, 
    Optional, Set, Tuple, TypeVar, Union, cast, overload
)
from datetime import datetime, UTC
from enum import Enum, auto
from dataclasses import dataclass, field

T = TypeVar('T')  # Success value type
E = TypeVar('E')  # Error type
R = TypeVar('R')  # Return type for functions


class ErrorSeverity(Enum):
    """Defines the severity levels for validation errors."""
    
    CRITICAL = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class ValidationError:
    """
    Represents a validation error with context information.
    
    This class contains detailed information about a validation error,
    including field path, error message, error code, and severity.
    """
    
    message: str
    path: Optional[str] = None
    code: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the validation error to a dictionary representation."""
        return {
            "message": self.message,
            "path": self.path,
            "code": self.code,
            "severity": self.severity.name,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ValidationError':
        """Create a validation error from a dictionary representation."""
        severity_str = data.get("severity", "ERROR")
        severity = ErrorSeverity[severity_str] if isinstance(severity_str, str) else ErrorSeverity.ERROR
        
        timestamp_str = data.get("timestamp")
        if timestamp_str and isinstance(timestamp_str, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                timestamp = datetime.now(UTC)
        else:
            timestamp = datetime.now(UTC)
        
        return ValidationError(
            message=data["message"],
            path=data.get("path"),
            code=data.get("code"),
            severity=severity,
            context=data.get("context", {}),
            timestamp=timestamp
        )


class Result(Generic[T, E]):
    """
    A container for return values or errors.
    
    This class implements the Result pattern, providing a way to
    handle errors without exceptions. It can be used for validation
    results, service operation results, or any operation that can fail.
    """
    
    def __init__(
        self, 
        value: Optional[T] = None, 
        error: Optional[E] = None,
        errors: Optional[List[E]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new Result.
        
        Args:
            value: The success value, if any
            error: The error, if any
            errors: A list of errors, if any
            metadata: Additional metadata about the result
        """
        self._value = value
        self._errors = errors or []
        self._metadata = metadata or {}
        
        if error is not None:
            self._errors.append(error)
        
        self._is_success = not self._errors
    
    @property
    def is_success(self) -> bool:
        """
        Check if the operation was successful.
        
        Returns:
            True if successful, False otherwise
        """
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        """
        Check if the operation failed.
        
        Returns:
            True if failed, False otherwise
        """
        return not self._is_success
    
    @property
    def value(self) -> Optional[T]:
        """
        Get the success value, if any.
        
        Returns:
            The success value, or None if the operation failed
        """
        return self._value
    
    def value_or(self, default: R) -> Union[T, R]:
        """
        Get the success value or a default value.
        
        Args:
            default: The default value to return if the operation failed
            
        Returns:
            The success value if successful, or the default value if failed
        """
        return self._value if self.is_success and self._value is not None else default
    
    def value_or_raise(self, exception_factory: Optional[Callable[[List[E]], Exception]] = None) -> T:
        """
        Get the success value or raise an exception.
        
        Args:
            exception_factory: A function that takes the errors and returns an exception
            
        Returns:
            The success value
            
        Raises:
            Exception: If the operation failed
        """
        if self.is_failure:
            if exception_factory:
                raise exception_factory(self._errors)
            raise ValueError(f"Operation failed with errors: {self._errors}")
        
        if self._value is None:
            raise ValueError("Operation succeeded but returned None")
            
        return self._value
    
    @property
    def error(self) -> Optional[E]:
        """
        Get the first error, if any.
        
        Returns:
            The first error, or None if the operation succeeded
        """
        return self._errors[0] if self._errors else None
    
    @property
    def errors(self) -> List[E]:
        """
        Get all errors.
        
        Returns:
            A list of all errors
        """
        return self._errors.copy()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get the metadata associated with this result.
        
        Returns:
            A dictionary of metadata
        """
        return self._metadata.copy()
    
    def add_metadata(self, key: str, value: Any) -> 'Result[T, E]':
        """
        Add metadata to the result.
        
        Args:
            key: The metadata key
            value: The metadata value
            
        Returns:
            Self for chaining
        """
        self._metadata[key] = value
        return self
    
    def map(self, fn: Callable[[T], R]) -> 'Result[R, E]':
        """
        Apply a function to the success value.
        
        Args:
            fn: The function to apply to the success value
            
        Returns:
            A new Result with the function applied to the success value,
            or the original error if the operation failed
        """
        if self.is_success:
            try:
                new_value = fn(self._value)
                return Result(value=new_value, metadata=self._metadata)
            except Exception as e:
                return Result(error=cast(E, e), metadata=self._metadata)
        return Result(errors=self._errors, metadata=self._metadata)
    
    def map_error(self, fn: Callable[[E], R]) -> Union['Result[T, R]', 'Result[T, E]']:
        """
        Apply a function to the error(s).
        
        Args:
            fn: The function to apply to each error
            
        Returns:
            A new Result with the function applied to the errors,
            or the original success value if the operation succeeded
        """
        if self.is_failure:
            try:
                new_errors = [fn(error) for error in self._errors]
                return Result(errors=cast(List[R], new_errors), metadata=self._metadata)
            except Exception as e:
                return Result(error=cast(E, e), metadata=self._metadata)
        return self
    
    def bind(self, fn: Callable[[T], 'Result[R, E]']) -> 'Result[R, E]':
        """
        Chain operations that might fail.
        
        Args:
            fn: A function that takes the success value and returns a new Result
            
        Returns:
            The new Result from the function, or the original error
            if the operation failed
        """
        if self.is_success:
            try:
                result = fn(self._value)
                # Merge metadata
                for key, value in self._metadata.items():
                    if key not in result._metadata:
                        result._metadata[key] = value
                return result
            except Exception as e:
                return Result(error=cast(E, e), metadata=self._metadata)
        return Result(errors=self._errors, metadata=self._metadata)
    
    def combine(self, other: 'Result[Any, E]') -> 'Result[T, E]':
        """
        Combine this result with another result, accumulating errors.
        
        Args:
            other: Another result to combine with this one
            
        Returns:
            A new result with all errors from both results
        """
        if self.is_success and other.is_success:
            return self
        
        combined_errors = self._errors.copy()
        combined_errors.extend(other._errors)
        
        # Merge metadata
        combined_metadata = self._metadata.copy()
        for key, value in other._metadata.items():
            if key not in combined_metadata:
                combined_metadata[key] = value
        
        return Result(errors=combined_errors, metadata=combined_metadata)
    
    def tap(self, fn: Callable[[T], None]) -> 'Result[T, E]':
        """
        Execute a function with the success value without changing the result.
        
        Args:
            fn: The function to execute with the success value
            
        Returns:
            The original result
        """
        if self.is_success and self._value is not None:
            try:
                fn(self._value)
            except Exception:
                # Ignore exceptions in tap functions
                pass
        return self
    
    def tap_error(self, fn: Callable[[List[E]], None]) -> 'Result[T, E]':
        """
        Execute a function with the errors without changing the result.
        
        Args:
            fn: The function to execute with the errors
            
        Returns:
            The original result
        """
        if self.is_failure:
            try:
                fn(self._errors)
            except Exception:
                # Ignore exceptions in tap functions
                pass
        return self
    
    @staticmethod
    def success(value: T, metadata: Optional[Dict[str, Any]] = None) -> 'Result[T, Any]':
        """
        Create a successful result.
        
        Args:
            value: The success value
            metadata: Additional metadata about the result
            
        Returns:
            A successful Result with the given value
        """
        return Result(value=value, metadata=metadata)
    
    @staticmethod
    def failure(error: E, metadata: Optional[Dict[str, Any]] = None) -> 'Result[Any, E]':
        """
        Create a failed result.
        
        Args:
            error: The error
            metadata: Additional metadata about the result
            
        Returns:
            A failed Result with the given error
        """
        return Result(error=error, metadata=metadata)
    
    @staticmethod
    def failures(errors: List[E], metadata: Optional[Dict[str, Any]] = None) -> 'Result[Any, E]':
        """
        Create a failed result with multiple errors.
        
        Args:
            errors: The list of errors
            metadata: Additional metadata about the result
            
        Returns:
            A failed Result with the given errors
        """
        return Result(errors=errors, metadata=metadata)
    
    @staticmethod
    def from_exception(e: Exception, metadata: Optional[Dict[str, Any]] = None) -> 'Result[Any, Exception]':
        """
        Create a failed result from an exception.
        
        Args:
            e: The exception
            metadata: Additional metadata about the result
            
        Returns:
            A failed Result with the exception as the error
        """
        return Result(error=e, metadata=metadata)
    
    @staticmethod
    def try_catch(fn: Callable[[], T], metadata: Optional[Dict[str, Any]] = None) -> 'Result[T, Exception]':
        """
        Execute a function and return a Result.
        
        Args:
            fn: The function to execute
            metadata: Additional metadata about the result
            
        Returns:
            A Result containing either the function's return value or any exception raised
        """
        try:
            return Result.success(fn(), metadata=metadata)
        except Exception as e:
            return Result.failure(e, metadata=metadata)
    
    @staticmethod
    def all(results: List['Result[T, E]']) -> 'Result[List[T], E]':
        """
        Combine multiple results into a single result.
        
        This method returns a success result with a list of all success values
        if all results are successful, or a failure result with all errors if
        any result is a failure.
        
        Args:
            results: The results to combine
            
        Returns:
            A combined result
        """
        if not results:
            return Result.success([])
        
        success_values = []
        all_errors = []
        combined_metadata = {}
        
        for result in results:
            if result.is_success:
                if result.value is not None:
                    success_values.append(result.value)
            else:
                all_errors.extend(result.errors)
            
            # Merge metadata
            for key, value in result.metadata.items():
                if key not in combined_metadata:
                    combined_metadata[key] = value
        
        if all_errors:
            return Result.failures(all_errors, metadata=combined_metadata)
        
        return Result.success(success_values, metadata=combined_metadata)


# Type alias for validation results
ValidationResult = Result[T, ValidationError]