"""
Result Pattern Implementation

This module provides a Result class for handling errors without exceptions.
The Result pattern is a way to represent either a successful value or an error.
"""

from typing import Generic, TypeVar, Optional, List, Any, Union, Callable

T = TypeVar('T')  # Success value type
E = TypeVar('E')  # Error type


class Result(Generic[T, E]):
    """
    A container for return values or errors.
    
    This class implements the Result pattern, providing a way to
    handle errors without exceptions.
    """
    
    def __init__(
        self, 
        value: Optional[T] = None, 
        error: Optional[E] = None,
        errors: Optional[List[E]] = None
    ):
        """
        Create a new Result.
        
        Args:
            value: The success value, if any
            error: The error, if any
            errors: A list of errors, if any
        """
        self._value = value
        self._errors = errors or []
        
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
    
    def map(self, fn: Callable[[T], Any]) -> 'Result':
        """
        Apply a function to the success value.
        
        Args:
            fn: The function to apply to the success value
            
        Returns:
            A new Result with the function applied to the success value,
            or the original error if the operation failed
        """
        if self.is_success:
            return Result(value=fn(self._value))
        return Result(errors=self._errors)
    
    def bind(self, fn: Callable[[T], 'Result']) -> 'Result':
        """
        Chain operations that might fail.
        
        Args:
            fn: A function that takes the success value and returns a new Result
            
        Returns:
            The new Result from the function, or the original error
            if the operation failed
        """
        if self.is_success:
            return fn(self._value)
        return Result(errors=self._errors)
    
    @staticmethod
    def success(value: T) -> 'Result[T, Any]':
        """
        Create a successful result.
        
        Args:
            value: The success value
            
        Returns:
            A successful Result with the given value
        """
        return Result(value=value)
    
    @staticmethod
    def failure(error: E) -> 'Result[Any, E]':
        """
        Create a failed result.
        
        Args:
            error: The error
            
        Returns:
            A failed Result with the given error
        """
        return Result(error=error)
    
    @staticmethod
    def failures(errors: List[E]) -> 'Result[Any, E]':
        """
        Create a failed result with multiple errors.
        
        Args:
            errors: The list of errors
            
        Returns:
            A failed Result with the given errors
        """
        return Result(errors=errors)