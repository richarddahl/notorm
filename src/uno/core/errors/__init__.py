"""
Error Handling Framework

This package contains the error handling components used throughout the system.
It provides a Result pattern implementation for handling errors without exceptions.
"""

from uno.core.errors.result import (
    Failure,
    Result,
    Success,
    ValidationError,
    ValidationResult
)
from uno.core.errors.result_utils import (
    AsyncResultContext,
    async_try_catch,
    ensure_result,
    ResultContext,
    to_result,
    try_catch,
    unwrap_or,
    unwrap_or_raise,
)

__all__ = [
    'async_try_catch',
    'ensure_result',
    'Failure',
    'Result', 
    'ResultContext',
    'AsyncResultContext',
    'Success', 
    'to_result', 
    'try_catch', 
    'unwrap_or', 
    'unwrap_or_raise',
    'ValidationError',
    'ValidationResult'
]