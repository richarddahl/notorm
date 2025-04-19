"""
Tests for the Result pattern implementation.

This module tests the Result class that implements the Result pattern
for functional error handling without exceptions.
"""

import pytest
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from uno.core.errors.result import (
    Result,
    ValidationError,
    ErrorSeverity
)


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
        """Test creating a successful Result."""
        # Arrange & Act
        data = TestData("test_success")
        result = Result.success(data)

        # Assert
        assert result.is_success
        assert not result.is_failure
        assert result.value == data
        assert result.error is None

    def test_failure_creation(self):
        """Test creating a failure Result."""
        # Arrange & Act
        error = TestError("Test error")
        result = Result.failure(error)

        # Assert
        assert not result.is_success
        assert result.is_failure
        assert result.value is None
        assert result.error == error

    def test_failures_creation(self):
        """Test creating a Result with multiple errors."""
        # Arrange & Act
        errors = [TestError("Error 1"), TestError("Error 2")]
        result = Result.failures(errors)

        # Assert
        assert not result.is_success
        assert result.is_failure
        assert result.value is None
        assert len(result.errors) == 2
        assert str(result.errors[0]) == "Error 1"
        assert str(result.errors[1]) == "Error 2"

    def test_success_map(self):
        """Test map method on a successful Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        mapped = result.map(lambda data: data.value.upper())

        # Assert
        assert mapped.is_success
        assert mapped.value == "TEST"

    def test_failure_map(self):
        """Test map method on a failure Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act
        mapped = result.map(lambda data: data.value.upper())

        # Assert
        assert mapped.is_failure
        assert mapped.error == error
        assert mapped.value is None

    def test_success_map_error(self):
        """Test map_error method on a successful Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        mapped = result.map_error(lambda err: TestError("Transformed"))

        # Assert
        assert mapped.is_success
        assert mapped.value.value == "test"

    def test_failure_map_error(self):
        """Test map_error method on a failure Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act
        mapped = result.map_error(lambda err: TestError("Transformed"))

        # Assert
        assert mapped.is_failure
        assert str(mapped.error) == "Transformed"

    def test_success_bind(self):
        """Test bind method on a successful Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        bound = result.bind(lambda data: Result.success(data.value.upper()))

        # Assert
        assert bound.is_success
        assert bound.value == "TEST"

    def test_failure_bind(self):
        """Test bind method on a failure Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act
        bound = result.bind(lambda data: Result.success(data.value.upper()))

        # Assert
        assert bound.is_failure
        assert bound.error == error

    def test_success_value(self):
        """Test value property on a successful Result."""
        # Arrange
        data = TestData("test")
        result = Result.success(data)

        # Act
        value = result.value

        # Assert
        assert value == data

    def test_failure_value(self):
        """Test value property on a failure Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act
        value = result.value

        # Assert
        assert value is None

    def test_success_value_or(self):
        """Test value_or method on a successful Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        value = result.value_or(TestData("default"))

        # Assert
        assert value.value == "test"

    def test_failure_value_or(self):
        """Test value_or method on a failure Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act
        value = result.value_or(TestData("default"))

        # Assert
        assert value.value == "default"

    def test_success_value_or_raise(self):
        """Test value_or_raise method on a successful Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        value = result.value_or_raise()

        # Assert
        assert value.value == "test"

    def test_failure_value_or_raise(self):
        """Test value_or_raise method on a failure Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            result.value_or_raise()

        assert "Error" in str(exc_info.value)

    def test_error_property(self):
        """Test error property on a Result."""
        # Arrange
        error = TestError("Error")
        result = Result.failure(error)

        # Act
        result_error = result.error

        # Assert
        assert result_error == error

    def test_error_on_success(self):
        """Test error property on a successful Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        result_error = result.error

        # Assert
        assert result_error is None

    def test_errors_property(self):
        """Test errors property on a Result."""
        # Arrange
        errors = [TestError("Error 1"), TestError("Error 2")]
        result = Result.failures(errors)

        # Act
        result_errors = result.errors

        # Assert
        assert len(result_errors) == 2
        assert str(result_errors[0]) == "Error 1"
        assert str(result_errors[1]) == "Error 2"

    def test_add_metadata(self):
        """Test adding metadata to a Result."""
        # Arrange
        result = Result.success(TestData("test"))

        # Act
        result.add_metadata("key", "value")

        # Assert
        assert result.metadata["key"] == "value"

    def test_combine_results(self):
        """Test combining Results."""
        # Arrange
        result1 = Result.success(TestData("test1"))
        result2 = Result.success(TestData("test2"))
        result1.add_metadata("key1", "value1")
        result2.add_metadata("key2", "value2")

        # Act
        combined = result1.combine(result2)

        # Assert
        assert combined.is_success
        assert combined.metadata["key1"] == "value1"
        assert combined.metadata["key2"] == "value2"

    def test_combine_with_failure(self):
        """Test combining a success with a failure."""
        # Arrange
        result1 = Result.success(TestData("test1"))
        error = TestError("Error")
        result2 = Result.failure(error)

        # Act
        combined = result1.combine(result2)

        # Assert
        assert combined.is_failure
        assert combined.error == error

    def test_from_exception(self):
        """Test Result.from_exception method."""
        # Arrange
        error = TestError("Test exception")

        # Act
        result = Result.from_exception(error)

        # Assert
        assert result.is_failure
        assert result.error == error

    def test_try_catch(self):
        """Test Result.try_catch method."""
        # Arrange & Act
        success_result = Result.try_catch(lambda: TestData("test"))
        failure_result = Result.try_catch(lambda: 1/0)

        # Assert
        assert success_result.is_success
        assert success_result.value.value == "test"
        assert failure_result.is_failure
        assert isinstance(failure_result.error, ZeroDivisionError)

    def test_all_method_success(self):
        """Test Result.all method with successful results."""
        # Arrange
        results = [
            Result.success(TestData("one")),
            Result.success(TestData("two")),
            Result.success(TestData("three"))
        ]

        # Act
        combined = Result.all(results)

        # Assert
        assert combined.is_success
        assert len(combined.value) == 3
        assert combined.value[0].value == "one"
        assert combined.value[1].value == "two"
        assert combined.value[2].value == "three"

    def test_all_method_with_failure(self):
        """Test Result.all method with a failure result."""
        # Arrange
        error = TestError("Error in list")
        results = [
            Result.success(TestData("one")),
            Result.failure(error),
            Result.success(TestData("three"))
        ]

        # Act
        combined = Result.all(results)

        # Assert
        assert combined.is_failure
        assert combined.error == error