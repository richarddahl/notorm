"""
Tests for the error framework.
"""

import pytest
from datetime import datetime, UTC

from uno.core.errors.framework import (
    ErrorCatalog,
    ValidationError,
    NotFoundError,
    DatabaseError,
    AuthorizationError,
    register_error,
    create_error,
    get_error_context,
    ErrorCategory,
    ErrorSeverity,
)
from uno.core.errors.result import Result, Success, Failure


def test_error_catalog_registration():
    """Test registering errors in the catalog."""
    # Register a test error
    register_error(
        code="TEST_ERROR",
        message_template="Test error with {param}",
        category=ErrorCategory.BUSINESS,
        severity=ErrorSeverity.WARNING,
        http_status_code=400,
        help_text="This is a test error.",
    )
    
    # Get the error definition
    error_def = ErrorCatalog.get("TEST_ERROR")
    
    # Verify the definition
    assert error_def is not None
    assert error_def["code"] == "TEST_ERROR"
    assert error_def["message_template"] == "Test error with {param}"
    assert error_def["category"] == ErrorCategory.BUSINESS
    assert error_def["severity"] == ErrorSeverity.WARNING
    assert error_def["http_status_code"] == 400
    assert error_def["help_text"] == "This is a test error."


def test_error_creation():
    """Test creating errors from the catalog."""
    # Register a test error
    register_error(
        code="TEST_ERROR",
        message_template="Test error with {param}",
        category=ErrorCategory.BUSINESS,
        severity=ErrorSeverity.WARNING,
    )
    
    # Create an error instance
    error = create_error(
        code="TEST_ERROR",
        params={"param": "value"},
        details={"additional": "info"},
        field="test_field",
    )
    
    # Verify the error
    assert error.code == "TEST_ERROR"
    assert error.message == "Test error with value"
    assert error.category == ErrorCategory.BUSINESS
    assert error.severity == ErrorSeverity.WARNING
    assert error.field == "test_field"
    assert error.details == {"additional": "info"}


def test_error_to_result():
    """Test converting errors to Result objects."""
    # Register a test error
    register_error(
        code="TEST_ERROR",
        message_template="Test error with {param}",
        category=ErrorCategory.BUSINESS,
        severity=ErrorSeverity.WARNING,
    )
    
    # Create a Result from the catalog
    result = ErrorCatalog.to_result(
        code="TEST_ERROR",
        params={"param": "value"},
        details={"additional": "info"},
        field="test_field",
    )
    
    # Verify the result
    assert isinstance(result, Failure)
    assert result.error.code == "TEST_ERROR"
    assert "Test error with value" in str(result.error)
    assert result.error.details == {"additional": "info"}


def test_validation_error():
    """Test the ValidationError class."""
    # Create a validation error
    error = ValidationError(
        "Invalid value",
        code="INVALID_VALUE",
        field="test_field",
        details={"min": 1, "max": 10},
    )
    
    # Verify the error
    assert error.code == "INVALID_VALUE"
    assert str(error) == "Invalid value"
    assert error.category == ErrorCategory.VALIDATION
    assert error.field == "test_field"
    assert error.details == {"min": 1, "max": 10}
    
    # Convert to Result
    result = error.to_result()
    assert isinstance(result, Failure)
    assert result.error.code == "INVALID_VALUE"


def test_not_found_error():
    """Test the NotFoundError class."""
    # Create a not found error
    error = NotFoundError(
        "User not found",
        code="USER_NOT_FOUND",
        details={"user_id": "123"},
    )
    
    # Verify the error
    assert error.code == "USER_NOT_FOUND"
    assert str(error) == "User not found"
    assert error.category == ErrorCategory.RESOURCE
    assert error.details == {"user_id": "123"}


def test_error_context():
    """Test the error context functionality."""
    # Get error context
    context = get_error_context()
    
    # Set some values
    context.request_id = "req-123"
    context.user_id = "user-456"
    context.application = "test-app"
    context.additional_data = {"custom": "value"}
    
    # Verify the context
    assert context.request_id == "req-123"
    assert context.user_id == "user-456"
    assert context.application == "test-app"
    assert context.additional_data == {"custom": "value"}
    
    # Convert to dict
    context_dict = context.to_dict()
    assert context_dict["request_id"] == "req-123"
    assert context_dict["user_id"] == "user-456"
    assert context_dict["application"] == "test-app"
    assert context_dict["additional_data"] == {"custom": "value"}


def test_standard_error_classes():
    """Test the standard error classes."""
    # ValidationError
    error1 = ValidationError("Invalid input", field="name")
    assert error1.category == ErrorCategory.VALIDATION
    assert error1.field == "name"
    
    # DatabaseError
    error2 = DatabaseError("Database connection failed")
    assert error2.category == ErrorCategory.DATABASE
    
    # AuthorizationError
    error3 = AuthorizationError("Permission denied")
    assert error3.category == ErrorCategory.AUTHORIZATION
    
    # NotFoundError
    error4 = NotFoundError("Resource not found")
    assert error4.category == ErrorCategory.RESOURCE