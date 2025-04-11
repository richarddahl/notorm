"""
Tests for the Result module.
"""

import pytest
from typing import List, Dict

from uno.core.result import Success, Failure, of, failure, from_exception, combine, combine_dict


def test_success_creation():
    """Test creating a Success result."""
    result = Success(42)
    assert result.is_success
    assert not result.is_failure
    assert result.value == 42
    assert result.error is None


def test_failure_creation():
    """Test creating a Failure result."""
    error = ValueError("test error")
    result = Failure(error)
    assert not result.is_success
    assert result.is_failure
    assert result.value is None
    assert result.error == error


def test_success_map():
    """Test mapping a Success result."""
    result = Success(42)
    mapped = result.map(lambda x: x * 2)
    assert mapped.is_success
    assert mapped.value == 84


def test_failure_map():
    """Test mapping a Failure result."""
    error = ValueError("test error")
    result = Failure(error)
    mapped = result.map(lambda x: x * 2)
    assert mapped.is_failure
    assert mapped.error == error


def test_success_flat_map():
    """Test flat mapping a Success result."""
    result = Success(42)
    flat_mapped = result.flat_map(lambda x: Success(x * 2))
    assert flat_mapped.is_success
    assert flat_mapped.value == 84


def test_failure_flat_map():
    """Test flat mapping a Failure result."""
    error = ValueError("test error")
    result = Failure(error)
    flat_mapped = result.flat_map(lambda x: Success(x * 2))
    assert flat_mapped.is_failure
    assert flat_mapped.error == error


def test_success_unwrap():
    """Test unwrapping a Success result."""
    result = Success(42)
    assert result.unwrap() == 42


def test_failure_unwrap():
    """Test unwrapping a Failure result."""
    error = ValueError("test error")
    result = Failure(error)
    with pytest.raises(ValueError):
        result.unwrap()


def test_success_unwrap_or():
    """Test unwrapping a Success result with a default value."""
    result = Success(42)
    assert result.unwrap_or(0) == 42


def test_failure_unwrap_or():
    """Test unwrapping a Failure result with a default value."""
    error = ValueError("test error")
    result = Failure(error)
    assert result.unwrap_or(0) == 0


def test_success_unwrap_or_else():
    """Test unwrapping a Success result with a default function."""
    result = Success(42)
    assert result.unwrap_or_else(lambda e: 0) == 42


def test_failure_unwrap_or_else():
    """Test unwrapping a Failure result with a default function."""
    error = ValueError("test error")
    result = Failure(error)
    assert result.unwrap_or_else(lambda e: 0) == 0


def test_of_function():
    """Test the of function."""
    result = of(42)
    assert result.is_success
    assert result.value == 42


def test_failure_function():
    """Test the failure function."""
    error = ValueError("test error")
    result = failure(error)
    assert result.is_failure
    assert result.error == error


def test_from_exception_success():
    """Test the from_exception decorator with a successful function."""
    @from_exception
    def func(x):
        return x * 2
    
    result = func(21)
    assert result.is_success
    assert result.value == 42


def test_from_exception_failure():
    """Test the from_exception decorator with a failing function."""
    @from_exception
    def func(x):
        raise ValueError(f"Error with {x}")
    
    result = func(21)
    assert result.is_failure
    assert isinstance(result.error, ValueError)
    assert str(result.error) == "Error with 21"


def test_combine_all_success():
    """Test combining multiple Success results."""
    results = [Success(1), Success(2), Success(3)]
    combined = combine(results)
    assert combined.is_success
    assert combined.value == [1, 2, 3]


def test_combine_with_failure():
    """Test combining results with a Failure."""
    error = ValueError("test error")
    results = [Success(1), Failure(error), Success(3)]
    combined = combine(results)
    assert combined.is_failure
    assert combined.error == error


def test_combine_dict_all_success():
    """Test combining a dictionary of Success results."""
    results = {
        "a": Success(1),
        "b": Success(2),
        "c": Success(3)
    }
    combined = combine_dict(results)
    assert combined.is_success
    assert combined.value == {"a": 1, "b": 2, "c": 3}


def test_combine_dict_with_failure():
    """Test combining a dictionary with a Failure."""
    error = ValueError("test error")
    results = {
        "a": Success(1),
        "b": Failure(error),
        "c": Success(3)
    }
    combined = combine_dict(results)
    assert combined.is_failure
    assert combined.error == error


def test_on_success_handler():
    """Test the on_success handler."""
    result = Success(42)
    side_effect = []
    
    new_result = result.on_success(lambda x: side_effect.append(x))
    
    assert new_result is result  # Returns the same result
    assert side_effect == [42]   # Side effect was executed


def test_on_failure_handler_success():
    """Test the on_failure handler with a Success."""
    result = Success(42)
    side_effect = []
    
    new_result = result.on_failure(lambda e: side_effect.append(str(e)))
    
    assert new_result is result  # Returns the same result
    assert side_effect == []     # Side effect was not executed


def test_on_failure_handler_failure():
    """Test the on_failure handler with a Failure."""
    error = ValueError("test error")
    result = Failure(error)
    side_effect = []
    
    new_result = result.on_failure(lambda e: side_effect.append(str(e)))
    
    assert new_result is result                # Returns the same result
    assert side_effect == ["test error"]       # Side effect was executed