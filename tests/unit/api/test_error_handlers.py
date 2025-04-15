# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the API error handlers.

These tests verify the functionality of the error handling system for the API endpoints,
ensuring that different types of errors are correctly converted to standardized HTTP responses.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError as PydanticValidationError

from uno.api.error_handlers import (
    ErrorResponse,
    find_exception_handler,
    global_exception_handler,
    configure_error_handlers,
    handle_validation_error,
    handle_not_found_error,
    handle_authorization_error,
    handle_pydantic_validation_error,
    handle_request_validation_error,
    handle_error_result,
    handle_generic_exception
)
from uno.core.errors.base import UnoError, ValidationError, NotFoundError, AuthorizationError
from uno.core.errors.result import ErrorResult


class TestErrorResponse:
    """Tests for the ErrorResponse class."""

    def test_initialization(self):
        """Test initialization of ErrorResponse."""
        response = ErrorResponse(
            code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "value"},
            help_text="This is help text"
        )
        
        assert response.code == "TEST_ERROR"
        assert response.message == "Test error message"
        assert response.status_code == 400
        assert response.details == {"field": "value"}
        assert response.help_text == "This is help text"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        response = ErrorResponse(
            code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "value"},
            help_text="This is help text"
        )
        
        response_dict = response.to_dict()
        assert response_dict["code"] == "TEST_ERROR"
        assert response_dict["message"] == "Test error message"
        assert response_dict["details"] == {"field": "value"}
        assert response_dict["help_text"] == "This is help text"
    
    def test_to_dict_without_help_text(self):
        """Test conversion to dictionary without help text."""
        response = ErrorResponse(
            code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "value"}
        )
        
        response_dict = response.to_dict()
        assert "help_text" not in response_dict
    
    def test_to_json_response(self):
        """Test conversion to JSONResponse."""
        response = ErrorResponse(
            code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "value"}
        )
        
        json_response = response.to_json_response()
        assert isinstance(json_response, JSONResponse)
        assert json_response.status_code == 400
        
        # Parse content to verify it
        content = json.loads(json_response.body.decode())
        assert content["code"] == "TEST_ERROR"
        assert content["message"] == "Test error message"
        assert content["details"] == {"field": "value"}


class TestExceptionHandlers:
    """Tests for the exception handlers."""

    def test_handle_validation_error(self):
        """Test handling of ValidationError."""
        error = ValidationError("Invalid input")
        error.details = {"field": "value"}
        
        response = handle_validation_error(error)
        
        assert response.code == "VALIDATION_ERROR"
        assert response.message == "Invalid input"
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.details == {"field": "value"}
        assert "validation requirements" in response.help_text.lower()
    
    def test_handle_not_found_error(self):
        """Test handling of NotFoundError."""
        error = NotFoundError("Resource not found")
        
        response = handle_not_found_error(error)
        
        assert response.code == "NOT_FOUND"
        assert response.message == "Resource not found"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.help_text.lower()
    
    def test_handle_authorization_error(self):
        """Test handling of AuthorizationError."""
        error = AuthorizationError("Permission denied")
        
        response = handle_authorization_error(error)
        
        assert response.code == "FORBIDDEN"
        assert response.message == "Permission denied"
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permissions" in response.help_text.lower()
    
    def test_handle_pydantic_validation_error(self):
        """Test handling of Pydantic ValidationError."""
        class TestModel(BaseModel):
            name: str
            age: int
        
        try:
            TestModel(name="Test", age="not an int")
            pytest.fail("Should have raised ValidationError")
        except PydanticValidationError as e:
            response = handle_pydantic_validation_error(e)
            
            assert response.code == "VALIDATION_ERROR"
            assert "validation failed" in response.message.lower()
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "errors" in response.details
            assert len(response.details["errors"]) > 0
            assert "required fields" in response.help_text.lower()
    
    def test_handle_request_validation_error(self):
        """Test handling of RequestValidationError."""
        # Create a mock RequestValidationError
        error = MagicMock(spec=RequestValidationError)
        error.errors.return_value = [
            {"loc": ["body", "name"], "msg": "field required", "type": "missing"}
        ]
        
        response = handle_request_validation_error(error)
        
        assert response.code == "VALIDATION_ERROR"
        assert "validation failed" in response.message.lower()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "errors" in response.details
        assert "required fields" in response.help_text.lower()
    
    def test_handle_error_result(self):
        """Test handling of ErrorResult."""
        error = ErrorResult(
            error_message="Business rule violated",
            error_code="VALIDATION_ERROR",
            error_details={"field": "value"}
        )
        
        response = handle_error_result(error)
        
        assert response.code == "VALIDATION_ERROR"
        assert response.message == "Business rule violated"
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.details == {"field": "value"}
    
    def test_handle_error_result_mapping(self):
        """Test status code mapping for ErrorResult."""
        # Test each status mapping
        mappings = {
            "NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "FORBIDDEN": status.HTTP_403_FORBIDDEN,
            "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
            "CONFLICT": status.HTTP_409_CONFLICT,
            "UNKNOWN_ERROR": status.HTTP_400_BAD_REQUEST  # Default for unknown codes
        }
        
        for error_code, expected_status in mappings.items():
            error = ErrorResult(
                error_message="Test error",
                error_code=error_code
            )
            
            response = handle_error_result(error)
            assert response.status_code == expected_status
    
    def test_handle_generic_exception(self):
        """Test handling of generic exceptions."""
        error = ValueError("Something went wrong")
        
        with patch("uno.api.error_handlers.logger") as mock_logger:
            response = handle_generic_exception(error)
            
            # Verify logging
            mock_logger.error.assert_called()
            
            # Verify response
            assert response.code == "INTERNAL_SERVER_ERROR"
            assert "unexpected error" in response.message.lower()
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "try again later" in response.help_text.lower()


class TestErrorHandlerRegistry:
    """Tests for the error handler registry."""
    
    def test_find_exception_handler_direct_match(self):
        """Test finding a handler with a direct match."""
        error = ValidationError("Invalid input")
        
        handler = find_exception_handler(error)
        
        assert handler == handle_validation_error
    
    def test_find_exception_handler_base_class_match(self):
        """Test finding a handler with a base class match."""
        # Create a subclass of ValidationError
        class CustomValidationError(ValidationError):
            pass
        
        error = CustomValidationError("Custom validation error")
        
        handler = find_exception_handler(error)
        
        assert handler == handle_validation_error
    
    def test_find_exception_handler_fallback(self):
        """Test fallback to generic handler."""
        error = KeyError("Key not found")
        
        handler = find_exception_handler(error)
        
        assert handler == handle_generic_exception


class TestGlobalExceptionHandler:
    """Tests for the global exception handler."""
    
    @pytest.mark.asyncio
    async def test_global_exception_handler(self):
        """Test the global exception handler."""
        # Create a mock request
        request = MagicMock(spec=Request)
        request.url = "http://example.com/api/test"
        
        # Create an error
        error = ValidationError("Invalid input")
        
        # Mock the logger
        with patch("uno.api.error_handlers.logger") as mock_logger:
            response = await global_exception_handler(request, error)
            
            # Check the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            # Parse content to verify it
            content = json.loads(response.body.decode())
            assert content["code"] == "VALIDATION_ERROR"
            assert content["message"] == "Invalid input"
            
            # Verify logging for client errors
            mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_server_error(self):
        """Test the global exception handler with a server error."""
        # Create a mock request
        request = MagicMock(spec=Request)
        request.url = "http://example.com/api/test"
        
        # Create an error that will be treated as a server error
        error = Exception("Internal server error")
        
        # Mock the logger
        with patch("uno.api.error_handlers.logger") as mock_logger:
            response = await global_exception_handler(request, error)
            
            # Check the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Parse content to verify it
            content = json.loads(response.body.decode())
            assert content["code"] == "INTERNAL_SERVER_ERROR"
            
            # Verify logging for server errors
            mock_logger.error.assert_called()


class TestFastAPIIntegration:
    """Tests for FastAPI integration."""
    
    def test_configure_error_handlers(self):
        """Test configuring error handlers for a FastAPI app."""
        app = FastAPI()
        
        # Check that the app has the expected number of exception handlers before configuration
        initial_handler_count = len(app.exception_handlers)
        
        # Configure error handlers
        configure_error_handlers(app)
        
        # Check that exception handlers were added
        assert len(app.exception_handlers) > initial_handler_count
        
        # Verify that the global exception handler was added
        assert Exception in app.exception_handlers
    
    def test_integration_with_fastapi(self):
        """Test integration with FastAPI."""
        app = FastAPI()
        configure_error_handlers(app)
        
        # Add a route that raises an error
        @app.get("/test-validation-error")
        async def test_validation_error():
            raise ValidationError("Test validation error")
        
        @app.get("/test-not-found-error")
        async def test_not_found_error():
            raise NotFoundError("Test not found error")
        
        @app.get("/test-authorization-error")
        async def test_authorization_error():
            raise AuthorizationError("Test authorization error")
        
        @app.get("/test-generic-error")
        async def test_generic_error():
            raise ValueError("Test generic error")
        
        # Create a test client
        client = TestClient(app)
        
        # Test validation error
        response = client.get("/test-validation-error")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["code"] == "VALIDATION_ERROR"
        
        # Test not found error
        response = client.get("/test-not-found-error")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["code"] == "NOT_FOUND"
        
        # Test authorization error
        response = client.get("/test-authorization-error")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["code"] == "FORBIDDEN"
        
        # Test generic error
        response = client.get("/test-generic-error")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["code"] == "INTERNAL_SERVER_ERROR"