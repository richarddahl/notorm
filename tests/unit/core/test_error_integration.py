# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration tests for the error handling framework.

These tests verify that the different components of the error handling
framework work together correctly.
"""

import pytest
import logging
import io
import json
from typing import Dict, Any, List, Optional

from uno.core.errors import (
    UnoError, ErrorCode, ErrorCategory, ErrorSeverity,
    ValidationContext, ValidationError,
    Result, Success, Failure, of, failure, from_exception,
    ErrorCatalog, register_error, get_all_error_codes,
    configure_logging, get_logger, LogConfig,
    with_error_context, add_error_context, get_error_context,
    with_logging_context, add_logging_context, get_logging_context
)


class TestErrorIntegration:
    """Tests for error handling framework integration."""
    
    def setup_method(self):
        """Set up test environment."""
        # Ensure the test error code is defined
        try:
            # We'll just try to register it every time
            # If it's already registered, catch the exception and continue
            register_error(
                code="TEST-0001",
                message_template="Test error message",
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.ERROR,
                description="Test error description",
                http_status_code=400,
                retry_allowed=True
            )
        except ValueError:
            # Error code already registered, which is fine
            pass
        
        # Configure logging to use a string buffer
        self.log_buffer = io.StringIO()
        handler = logging.StreamHandler(self.log_buffer)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers = [handler]
        
        # Create a test logger
        self.logger = get_logger("test")
    
    def test_error_context_with_logging(self):
        """Test that error context works with logging."""
        # Add to error context
        add_error_context(user_id="user123", action="test")
        
        # Add to logging context
        add_logging_context(request_id="req456", session_id="sess789")
        
        # Log a message
        self.logger.info("Test message")
        
        # Create an error with the current context
        error = UnoError("Test error", "TEST-0001", extra="value")
        
        # Verify error has the context
        assert error.context["user_id"] == "user123"
        assert error.context["action"] == "test"
        assert error.context["extra"] == "value"
        
        # Log the error
        self.logger.error(f"Error occurred: {error}", exc_info=error)
        
        # Check the log output
        log_output = self.log_buffer.getvalue()
        assert "Test message" in log_output
        assert "Error occurred: TEST-0001: Test error" in log_output
    
    def test_validation_with_result(self):
        """Test validation context with Result pattern."""
        # Define a function that validates and returns a Result
        def validate_user(user_data: Dict[str, Any]) -> Result[Dict[str, Any]]:
            try:
                context = ValidationContext("User")
                
                # Validate username
                if "username" not in user_data or not user_data["username"]:
                    context.add_error(
                        field="username",
                        message="Username is required",
                        error_code="FIELD_REQUIRED"
                    )
                
                # Validate email
                if "email" not in user_data or not user_data["email"]:
                    context.add_error(
                        field="email",
                        message="Email is required",
                        error_code="FIELD_REQUIRED"
                    )
                elif "@" not in user_data["email"]:
                    context.add_error(
                        field="email",
                        message="Invalid email format",
                        error_code="FIELD_INVALID",
                        value=user_data["email"]
                    )
                
                # Raise if there are any errors
                context.raise_if_errors()
                
                # If validation passes, return success
                return of(user_data)
                
            except ValidationError as e:
                # If validation fails, return failure
                return failure(e)
        
        # Test with valid data
        valid_user = {
            "username": "johndoe",
            "email": "john@example.com"
        }
        
        result = validate_user(valid_user)
        assert result.is_success
        assert result.value == valid_user
        
        # Test with invalid data
        invalid_user = {
            "username": "",
            "email": "invalid-email"
        }
        
        result = validate_user(invalid_user)
        assert result.is_failure
        assert isinstance(result.error, ValidationError)
        assert len(result.error.validation_errors) == 2
        
        # Test result can be converted to dict
        result_dict = result.to_dict()
        assert result_dict["status"] == "error"
        assert "validation_errors" in result_dict["error"]
        assert len(result_dict["error"]["validation_errors"]) == 2
    
    def test_error_catalog_with_unoerrror(self):
        """Test that ErrorCatalog works with UnoError."""
        # Create an error with a registered error code
        error = UnoError("This is a test", "TEST-0001", param="value")
        
        # Verify error info is populated
        assert error.error_info is not None
        assert error.error_info.code == "TEST-0001"
        assert error.error_info.category == ErrorCategory.INTERNAL
        assert error.error_info.severity == ErrorSeverity.ERROR
        
        # For this test, we'll temporarily remove the error code from the catalog
        # and re-register it with the correct http_status_code
        from uno.core.errors.catalog import _ERROR_CATALOG
        if "TEST-0001" in _ERROR_CATALOG:
            del _ERROR_CATALOG["TEST-0001"]
            
        # Now register with the correct http_status_code
        register_error(
            code="TEST-0001",
            message_template="Test error message",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            description="Test error description",
            http_status_code=400,
            retry_allowed=True
        )
        # Create a new error to get updated catalog information
        updated_error = UnoError("This is a test", "TEST-0001")
        assert updated_error.http_status_code == 400
        
        # Verify error properties use the info
        assert error.category == ErrorCategory.INTERNAL
        assert error.severity == ErrorSeverity.ERROR
        # Use updated_error to check http_status_code
        assert updated_error.http_status_code == 400
        assert error.retry_allowed is True
    
    def test_from_exception_with_context(self):
        """Test that from_exception works with error context."""
        # Add to error context
        add_error_context(user_id="user123", action="test")
        
        # Define a function that uses the decorator
        @from_exception
        def might_fail(value):
            if value < 0:
                raise UnoError("Negative value not allowed", "TEST-0001", value=value)
            return value * 2
        
        # Test success case
        result = might_fail(21)
        assert result.is_success
        assert result.value == 42
        
        # Test failure case
        result = might_fail(-1)
        assert result.is_failure
        assert isinstance(result.error, UnoError)
        assert result.error.error_code == "TEST-0001"
        
        # Verify error has the context
        assert result.error.context["user_id"] == "user123"
        assert result.error.context["action"] == "test"
        assert result.error.context["value"] == -1
    
    def test_result_to_http_response(self):
        """Test converting Result to HTTP response."""
        # Define a function to convert Result to HTTP response
        def result_to_http_response(result: Result[Any]) -> Dict[str, Any]:
            if result.is_success:
                return {
                    "status_code": 200,
                    "body": result.to_dict()
                }
            else:
                # Start with default status code
                status_code = 500
                
                # Check for special error types to determine status code
                error_type = type(result.error).__name__
                if error_type == "ValidationError":
                    status_code = 400
                elif error_type == "UnoError" and hasattr(result.error, "http_status_code"):
                    status_code = result.error.http_status_code
                
                return {
                    "status_code": status_code,
                    "body": result.to_dict()
                }
        
        # Test with success
        success_result = of({"id": "user123", "name": "John Doe"})
        response = result_to_http_response(success_result)
        
        assert response["status_code"] == 200
        assert response["body"]["status"] == "success"
        assert response["body"]["data"]["id"] == "user123"
        
        # For this test, we'll use a test-specific error code that we know has a 404 status
        test_error_code = "TEST-HTTP-404"
        try:
            register_error(
                code=test_error_code,
                message_template="Test 404 error: {resource_id}",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.ERROR,
                description="Test resource not found error",
                http_status_code=404,
                retry_allowed=False
            )
        except ValueError:
            # Error code already registered
            pass
            
        error = UnoError("Resource not found", test_error_code, resource_id="123")
        
        error_result = failure(error)
        response = result_to_http_response(error_result)
        
        assert response["status_code"] == 404  # From error.http_status_code
        assert response["body"]["status"] == "error"
        assert response["body"]["error"]["message"] == "Resource not found"
        assert response["body"]["error"]["error_code"] == test_error_code
        
        # Test with ValidationError
        validation_context = ValidationContext("User")
        validation_context.add_error(
            field="username",
            message="Username is required",
            error_code="FIELD_REQUIRED"
        )
        
        try:
            validation_context.raise_if_errors()
        except ValidationError as e:
            error_result = failure(e)
        
        response = result_to_http_response(error_result)
        
        assert response["status_code"] == 400  # From error.http_status_code
        assert response["body"]["status"] == "error"
        assert response["body"]["error"]["validation_errors"][0]["field"] == "username"