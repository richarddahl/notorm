# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the error handling framework.

These tests verify the functionality of the error handling components
including structured errors, error codes, contextual information,
validation, and logging.
"""

import pytest
import time
from typing import Dict, Any, Optional

from uno.core.errors.base import (
    UnoError, ErrorCode, ErrorCategory, ErrorSeverity,
    get_error_context, add_error_context, with_error_context
)
from uno.core.errors.catalog import (
    register_error, get_error_code_info, get_all_error_codes
)
from uno.core.errors.validation import (
    ValidationContext, ValidationError, validate_fields
)
from uno.core.errors.result import (
    Success, Failure, of, failure, from_exception,
    combine, combine_dict
)


class TestErrorCode:
    """Tests for the ErrorCode class and utilities."""
    
    def test_error_codes(self):
        """Test error code constants."""
        assert ErrorCode.UNKNOWN_ERROR == "CORE-0001"
        assert ErrorCode.VALIDATION_ERROR == "CORE-0002"
        assert ErrorCode.AUTHORIZATION_ERROR == "CORE-0003"
        assert ErrorCode.AUTHENTICATION_ERROR == "CORE-0004"
    
    def test_is_valid(self):
        """Test error code validation."""
        # Register a test error code if it doesn't exist
        try:
            register_error(
                code="TEST-0001",  # The code we want to validate
                message_template="Test error message",
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.ERROR,
                description="Test error description"
            )
        except ValueError:
            # Error code already registered, which is fine
            pass
        
        assert ErrorCode.is_valid("TEST-0001")
        assert not ErrorCode.is_valid("NONEXISTENT-CODE")
    
    def test_get_http_status(self):
        """Test getting HTTP status code for an error code."""
        # Register a test error code with HTTP status if it doesn't exist
        test_code = "TEST-0003"  # Use a new code
        try:
            register_error(
                code=test_code,
                message_template="Test error message",
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.ERROR,
                description="Test error description",
                http_status_code=418  # I'm a teapot
            )
        except ValueError:
            # Error code already registered - we'll use it anyway
            pass
        
        assert ErrorCode.get_http_status(test_code) == 418
        assert ErrorCode.get_http_status("NONEXISTENT-CODE") == 500  # Default


class TestUnoError:
    """Tests for the UnoError base class."""
    
    def test_init(self):
        """Test initialization of UnoError."""
        error = UnoError("Test error message", "TEST-0001", key="value")
        
        assert error.message == "Test error message"
        assert error.error_code == "TEST-0001"
        assert "key" in error.context
        assert error.context["key"] == "value"
    
    def test_to_dict(self):
        """Test converting error to dictionary."""
        error = UnoError("Test error message", "TEST-0001", key="value")
        
        error_dict = error.to_dict()
        assert error_dict["message"] == "Test error message"
        assert error_dict["error_code"] == "TEST-0001"
        assert error_dict["context"]["key"] == "value"
    
    def test_str(self):
        """Test string representation of error."""
        error = UnoError("Test error message", "TEST-0001")
        
        assert str(error) == "TEST-0001: Test error message"


class TestErrorContext:
    """Tests for error context utilities."""
    
    def test_get_error_context(self):
        """Test getting error context."""
        # Clear context first (since it may have been set by other tests)
        import contextvars
        from uno.core.errors.base import _error_context
        # Reset the context variable to its default (empty dictionary)
        _error_context.set({})
        
        # Now get the context which should be empty
        context = get_error_context()
        assert isinstance(context, dict)
        assert len(context) == 0
    
    def test_add_error_context(self):
        """Test adding to error context."""
        add_error_context(key1="value1", key2="value2")
        
        context = get_error_context()
        assert context["key1"] == "value1"
        assert context["key2"] == "value2"
    
    def test_with_error_context(self):
        """Test with_error_context decorator."""
        @with_error_context
        def test_function(arg1, arg2=None):
            return get_error_context()
        
        context = test_function("value1", arg2="value2")
        
        assert context["arg1"] == "value1"
        assert context["arg2"] == "value2"


class TestErrorCatalog:
    """Tests for the error catalog."""
    
    def test_register_error(self):
        """Test registering an error code."""
        # Get a unique test code using timestamp
        test_code = f"TEST-{int(time.time())}"
        
        # Register the code
        register_error(
            code=test_code,
            message_template="Test error message",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            description="Test error description",
            http_status_code=400,
            retry_allowed=False
        )
        
        # Verify the code was registered
        all_codes = get_all_error_codes()
        codes = [info.code for info in all_codes]
        assert test_code in codes
        
        info = get_error_code_info(test_code)
        assert info is not None
        assert info.code == test_code
        assert info.message_template == "Test error message"
        assert info.category == ErrorCategory.INTERNAL
        assert info.severity == ErrorSeverity.ERROR
        assert info.description == "Test error description"
        assert info.http_status_code == 400
        assert info.retry_allowed is False
    
    def test_get_all_error_codes(self):
        """Test getting all error codes."""
        # Register a few test error codes with unique timestamps
        timestamp = int(time.time())
        test_codes = []
        
        for i in range(3):
            code = f"TEST-{timestamp}-{i}"
            register_error(
                code=code,
                message_template=f"Test error message {i}",
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.ERROR,
                description=f"Test error description {i}"
            )
            test_codes.append(code)
        
        # Get all error codes
        all_codes = get_all_error_codes()
        
        # Verify test codes exist
        codes = [info.code for info in all_codes]
        for code in test_codes:
            assert code in codes
        
        # Verify at least one of the standard error codes exists
        assert "CORE-0001" in codes  # This is a standard error code


class TestValidationContext:
    """Tests for the ValidationContext class."""
    
    def test_init(self):
        """Test initialization of ValidationContext."""
        context = ValidationContext("User")
        
        assert context.entity_name == "User"
        assert len(context.errors) == 0
        assert len(context.current_path) == 0
    
    def test_add_error(self):
        """Test adding an error to the context."""
        context = ValidationContext("User")
        context.add_error(
            field="username",
            message="Username is required",
            error_code="FIELD_REQUIRED"
        )
        
        assert len(context.errors) == 1
        assert context.errors[0]["field"] == "username"
        assert context.errors[0]["message"] == "Username is required"
        assert context.errors[0]["error_code"] == "FIELD_REQUIRED"
    
    def test_nested(self):
        """Test creating a nested validation context."""
        context = ValidationContext("User")
        nested = context.nested("address")
        
        nested.add_error(
            field="city",
            message="City is required",
            error_code="FIELD_REQUIRED"
        )
        
        assert len(context.errors) == 1
        assert context.errors[0]["field"] == "address.city"
    
    def test_has_errors(self):
        """Test checking if context has errors."""
        context = ValidationContext("User")
        assert not context.has_errors()
        
        context.add_error(
            field="username",
            message="Username is required",
            error_code="FIELD_REQUIRED"
        )
        
        assert context.has_errors()
    
    def test_raise_if_errors(self):
        """Test raising if context has errors."""
        context = ValidationContext("User")
        
        # No errors, should not raise
        context.raise_if_errors()
        
        # Add an error
        context.add_error(
            field="username",
            message="Username is required",
            error_code="FIELD_REQUIRED"
        )
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as excinfo:
            context.raise_if_errors()
        
        assert excinfo.value.error_code == ErrorCode.VALIDATION_ERROR
        assert len(excinfo.value.validation_errors) == 1


class TestValidationError:
    """Tests for the ValidationError class."""
    
    def test_init(self):
        """Test initialization of ValidationError."""
        validation_errors = [
            {
                "field": "username",
                "message": "Username is required",
                "error_code": "FIELD_REQUIRED",
                "value": None
            }
        ]
        
        error = ValidationError(
            "Validation failed for User",
            ErrorCode.VALIDATION_ERROR,
            validation_errors=validation_errors,
            entity="User"
        )
        
        assert error.message == "Validation failed for User"
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert len(error.validation_errors) == 1
        assert error.context["entity"] == "User"
    
    def test_to_dict(self):
        """Test converting validation error to dictionary."""
        validation_errors = [
            {
                "field": "username",
                "message": "Username is required",
                "error_code": "FIELD_REQUIRED",
                "value": None
            }
        ]
        
        error = ValidationError(
            "Validation failed for User",
            ErrorCode.VALIDATION_ERROR,
            validation_errors=validation_errors
        )
        
        error_dict = error.to_dict()
        assert error_dict["message"] == "Validation failed for User"
        assert error_dict["error_code"] == ErrorCode.VALIDATION_ERROR
        assert len(error_dict["validation_errors"]) == 1
        assert error_dict["validation_errors"][0]["field"] == "username"


class TestValidateFields:
    """Tests for the validate_fields utility."""
    
    def test_validate_fields_success(self):
        """Test successful field validation."""
        data = {
            "username": "johndoe",
            "email": "john@example.com",
            "age": 30
        }
        
        required_fields = {"username", "email"}
        
        def validate_email(value: str) -> Optional[str]:
            if "@" not in value:
                return "Invalid email format"
            return None
        
        def validate_age(value: int) -> Optional[str]:
            if value < 18:
                return "Must be 18 or older"
            return None
        
        validators = {
            "email": [validate_email],
            "age": [validate_age]
        }
        
        # Should not raise
        validate_fields(data, required_fields, validators, "User")
    
    def test_validate_fields_failure(self):
        """Test field validation failure."""
        data = {
            "username": "",
            "email": "invalid-email",
            "age": 17
        }
        
        required_fields = {"username", "email"}
        
        def validate_email(value: str) -> Optional[str]:
            if "@" not in value:
                return "Invalid email format"
            return None
        
        def validate_age(value: int) -> Optional[str]:
            if value < 18:
                return "Must be 18 or older"
            return None
        
        validators = {
            "email": [validate_email],
            "age": [validate_age]
        }
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as excinfo:
            validate_fields(data, required_fields, validators, "User")
        
        assert len(excinfo.value.validation_errors) == 3
        
        fields = [error["field"] for error in excinfo.value.validation_errors]
        assert "username" in fields
        assert "email" in fields
        assert "age" in fields


class TestResult:
    """Tests for the Result pattern."""
    
    def test_success(self):
        """Test Success result."""
        result = Success(42)
        
        assert result.is_success
        assert not result.is_failure
        assert result.value == 42
        assert result.error is None
    
    def test_failure(self):
        """Test Failure result."""
        error = UnoError("Test error", "TEST-0001")
        result = Failure(error)
        
        assert not result.is_success
        assert result.is_failure
        assert result.value is None
        assert result.error == error
    
    def test_of(self):
        """Test of function for creating Success."""
        result = of(42)
        
        assert result.is_success
        assert result.value == 42
    
    def test_failure_func(self):
        """Test failure function for creating Failure."""
        error = UnoError("Test error", "TEST-0001")
        result = failure(error)
        
        assert result.is_failure
        assert result.error == error
    
    def test_map(self):
        """Test mapping a result."""
        # Success
        success = Success(21)
        mapped_success = success.map(lambda x: x * 2)
        
        assert mapped_success.is_success
        assert mapped_success.value == 42
        
        # Failure
        error = UnoError("Test error", "TEST-0001")
        failure_result = Failure(error)
        mapped_failure = failure_result.map(lambda x: x * 2)
        
        assert mapped_failure.is_failure
        assert mapped_failure.error == error
    
    def test_flat_map(self):
        """Test flat mapping a result."""
        # Success
        success = Success(21)
        flat_mapped_success = success.flat_map(lambda x: Success(x * 2))
        
        assert flat_mapped_success.is_success
        assert flat_mapped_success.value == 42
        
        # Failure
        error = UnoError("Test error", "TEST-0001")
        failure_result = Failure(error)
        flat_mapped_failure = failure_result.flat_map(lambda x: Success(x * 2))
        
        assert flat_mapped_failure.is_failure
        assert flat_mapped_failure.error == error
    
    def test_unwrap(self):
        """Test unwrapping a result."""
        # Success
        success = Success(42)
        assert success.unwrap() == 42
        
        # Failure
        error = UnoError("Test error", "TEST-0001")
        failure_result = Failure(error)
        
        with pytest.raises(RuntimeError):
            failure_result.unwrap()
    
    def test_unwrap_or(self):
        """Test unwrap_or for providing default value."""
        # Success
        success = Success(42)
        assert success.unwrap_or(0) == 42
        
        # Failure
        error = UnoError("Test error", "TEST-0001")
        failure_result = Failure(error)
        
        assert failure_result.unwrap_or(0) == 0
    
    def test_unwrap_or_else(self):
        """Test unwrap_or_else for computing default value."""
        # Success
        success = Success(42)
        assert success.unwrap_or_else(lambda e: 0) == 42
        
        # Failure
        error = UnoError("Test error", "TEST-0001")
        failure_result = Failure(error)
        
        assert failure_result.unwrap_or_else(lambda e: len(e.message)) == 10
    
    def test_from_exception(self):
        """Test from_exception decorator."""
        @from_exception
        def may_fail(x: int) -> int:
            if x < 0:
                raise UnoError("Negative input", "TEST-0001", input=x)
            return x * 2
        
        # Success case
        success_result = may_fail(21)
        assert success_result.is_success
        assert success_result.value == 42
        
        # Failure case
        failure_result = may_fail(-1)
        assert failure_result.is_failure
        assert isinstance(failure_result.error, UnoError)
        assert failure_result.error.error_code == "TEST-0001"
        assert failure_result.error.context["input"] == -1
    
    def test_combine(self):
        """Test combining multiple results."""
        # All success
        results = [Success(1), Success(2), Success(3)]
        combined = combine(results)
        
        assert combined.is_success
        assert combined.value == [1, 2, 3]
        
        # With failure
        error = UnoError("Test error", "TEST-0001")
        results = [Success(1), Failure(error), Success(3)]
        combined = combine(results)
        
        assert combined.is_failure
        assert combined.error == error
    
    def test_combine_dict(self):
        """Test combining dictionary of results."""
        # All success
        results = {
            "a": Success(1),
            "b": Success(2),
            "c": Success(3)
        }
        combined = combine_dict(results)
        
        assert combined.is_success
        assert combined.value == {"a": 1, "b": 2, "c": 3}
        
        # With failure
        error = UnoError("Test error", "TEST-0001")
        results = {
            "a": Success(1),
            "b": Failure(error),
            "c": Success(3)
        }
        combined = combine_dict(results)
        
        assert combined.is_failure
        assert combined.error == error
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        # Success with simple value
        success = Success(42)
        success_dict = success.to_dict()
        
        assert success_dict["status"] == "success"
        assert success_dict["data"] == 42
        
        # Success with dictionary
        data = {"id": 1, "name": "Test"}
        success = Success(data)
        success_dict = success.to_dict()
        
        assert success_dict["status"] == "success"
        assert success_dict["data"] == data
        
        # Failure with UnoError
        error = UnoError("Test error", "TEST-0001", key="value")
        failure_result = Failure(error)
        failure_dict = failure_result.to_dict()
        
        assert failure_dict["status"] == "error"
        assert failure_dict["error"]["message"] == "Test error"
        assert failure_dict["error"]["error_code"] == "TEST-0001"
        assert failure_dict["error"]["context"]["key"] == "value"