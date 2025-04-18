"""
Tests for the Result pattern implementation.

This module tests the Result, Success, and Failure classes that implement
the Result pattern for functional error handling without exceptions.
"""

import pytest
from typing import List, Dict, Any, Optional, Generic, TypeVar, cast
from dataclasses import dataclass

from uno.core.errors.result import (
    Success,
    Failure,
    Result,
    of,
    failure,
    from_exception,
    combine,
    from_awaitable,
)
from uno.core.base.error import BaseError


# Test Data and Classes
class TestData:
    """Test data class for result values."""

    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, TestData):
            return False
        return self.value == other.value

    def to_dict(self):
        """Convert to dictionary for testing."""
        return {"value": self.value}


class TestError(Exception):
    """Test error for testing failure results."""

    def __init__(self, message: str, code: str = "TEST_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


# Test Cases
class TestResultPattern:
    """Tests for the Result pattern implementation."""

    def test_success_creation(self):
        """Test creating a Success result."""
        # Arrange
        data = TestData("test_success")

        # Act
        result = Success(data)

        # Assert
        assert result.is_success
        assert not result.is_failure
        assert result.value == data
        assert result.error is None

    def test_failure_creation(self):
        """Test creating a Failure result."""
        # Arrange & Act
        error = TestError("Test error")
        result = Failure(error)

        # Assert
        assert not result.is_success
        assert result.is_failure
        assert result.value is None
        assert result.error == error

    def test_success_map(self):
        """Test map method on Success."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        result = success.map(lambda data: data.value.upper())

        # Assert
        assert result.is_success
        assert result.value == "TEST"

    def test_failure_map(self):
        """Test map method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)

        # Act
        result = failure.map(lambda data: data.value.upper())

        # Assert
        assert result.is_failure
        assert result.error == error
        assert result.value is None

    def test_success_flat_map(self):
        """Test flat_map method on Success."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        result = success.flat_map(lambda data: Success(data.value.upper()))

        # Assert
        assert result.is_success
        assert result.value == "TEST"

    def test_success_flat_map_to_failure(self):
        """Test flat_map method on Success that returns Failure."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        result = success.flat_map(
            lambda data: Failure(TestError(f"Failed with {data.value}"))
        )

        # Assert
        assert result.is_failure
        assert isinstance(result.error, TestError)
        assert str(result.error) == "Failed with test"

    def test_failure_flat_map(self):
        """Test flat_map method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)

        # Act
        result = failure.flat_map(lambda data: Success(data.value.upper()))

        # Assert
        assert result.is_failure
        assert result.error == error

    def test_success_on_success(self):
        """Test on_success method on Success."""
        # Arrange
        success = Success(TestData("test"))
        results = []

        # Act
        result = success.on_success(lambda data: results.append(data.value))

        # Assert
        assert result is success
        assert results == ["test"]

    def test_failure_on_success(self):
        """Test on_success method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)
        results = []

        # Act
        result = failure.on_success(lambda data: results.append(data.value))

        # Assert
        assert result is failure
        assert results == []  # Handler not called

    def test_success_on_failure(self):
        """Test on_failure method on Success."""
        # Arrange
        success = Success(TestData("test"))
        errors = []

        # Act
        result = success.on_failure(lambda err: errors.append(str(err)))

        # Assert
        assert result is success
        assert errors == []  # Handler not called

    def test_failure_on_failure(self):
        """Test on_failure method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)
        errors = []

        # Act
        result = failure.on_failure(lambda err: errors.append(str(err)))

        # Assert
        assert result is failure
        assert errors == ["Error"]  # Handler called

    def test_success_unwrap(self):
        """Test unwrap method on Success."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        value = success.unwrap()

        # Assert
        assert value.value == "test"

    def test_failure_unwrap(self):
        """Test unwrap method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            failure.unwrap()

        assert "Error" in str(exc_info.value)

    def test_success_unwrap_or(self):
        """Test unwrap_or method on Success."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        value = success.unwrap_or(TestData("default"))

        # Assert
        assert value.value == "test"

    def test_failure_unwrap_or(self):
        """Test unwrap_or method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)

        # Act
        value = failure.unwrap_or(TestData("default"))

        # Assert
        assert value.value == "default"

    def test_success_unwrap_or_else(self):
        """Test unwrap_or_else method on Success."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        value = success.unwrap_or_else(lambda: TestData("computed"))

        # Assert
        assert value.value == "test"

    def test_failure_unwrap_or_else(self):
        """Test unwrap_or_else method on Failure."""
        # Arrange
        error = TestError("Error")
        failure = Failure(error)

        # Act
        value = failure.unwrap_or_else(lambda: TestData("computed"))

        # Assert
        assert value.value == "computed"

    def test_success_to_dict(self):
        """Test to_dict method on Success."""
        # Arrange
        success = Success(TestData("test"))

        # Act
        result_dict = success.to_dict()

        # Assert
        assert result_dict["status"] == "success"
        assert result_dict["data"]["value"] == "test"

    def test_failure_to_dict(self):
        """Test to_dict method on Failure."""
        # Arrange
        error = TestError("Error", "TEST_CODE")
        failure = Failure(error)

        # Act
        result_dict = failure.to_dict()

        # Assert
        assert result_dict["status"] == "error"
        assert "error" in result_dict

    def test_of_factory_function(self):
        """Test the of factory function."""
        # Arrange & Act
        result = of(TestData("test"))

        # Assert
        assert result.is_success
        assert result.value.value == "test"

    def test_failure_factory_function(self):
        """Test the failure factory function."""
        # Arrange
        error = TestError("Error")

        # Act
        result = failure(error)

        # Assert
        assert result.is_failure
        assert result.error == error

    def test_from_exception_decorator_success(self):
        """Test the from_exception decorator with success."""

        # Arrange
        @from_exception
        def func(value):
            return TestData(value)

        # Act
        result = func("test")

        # Assert
        assert result.is_success
        assert result.value.value == "test"

    def test_from_exception_decorator_failure(self):
        """Test the from_exception decorator with failure."""

        # Arrange
        @from_exception
        def func(value):
            if value == "error":
                raise TestError("Error from func")
            return TestData(value)

        # Act
        result = func("error")

        # Assert
        assert result.is_failure
        assert str(result.error) == "Error from func"

    @pytest.mark.asyncio
    async def test_from_awaitable_success(self):
        """Test the from_awaitable function with success."""

        # Arrange
        async def async_func():
            return TestData("async")

        # Act
        result = await from_awaitable(async_func())

        # Assert
        assert result.is_success
        assert result.value.value == "async"

    @pytest.mark.asyncio
    async def test_from_awaitable_failure(self):
        """Test the from_awaitable function with failure."""

        # Arrange
        async def async_func():
            raise TestError("Async error")

        # Act
        result = await from_awaitable(async_func())

        # Assert
        assert result.is_failure
        assert str(result.error) == "Async error"

    def test_combine_all_success(self):
        """Test the combine function with all successful results."""
        # Arrange
        results = [
            Success(TestData("one")),
            Success(TestData("two")),
            Success(TestData("three")),
        ]

        # Act
        combined = combine(results)

        # Assert
        assert combined.is_success
        assert len(combined.value) == 3
        assert [r.value for r in combined.value] == ["one", "two", "three"]

    def test_combine_with_failure(self):
        """Test the combine function with a failure result."""
        # Arrange
        error = TestError("Error in result")
        results = [
            Success(TestData("one")),
            Failure(error),
            Success(TestData("three")),
        ]

        # Act
        combined = combine(results)

        # Assert
        assert combined.is_failure
        assert combined.error == error
