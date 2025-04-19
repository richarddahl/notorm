# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the uno.core.logging.framework module.
"""

import json
import logging
import io
import sys
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from uno.core.logging.framework import (
    LogLevel,
    LogFormat,
    LogConfig,
    LogContext,
    StructuredLogger,
    configure_logging,
    get_logger,
    add_context,
    get_context,
    clear_context,
    with_logging_context,
    log_error,
    LoggingMiddleware,
)
from uno.core.errors.framework import ValidationError, ErrorDetail


class TestLogLevel:
    """Tests for the LogLevel enum."""
    
    def test_from_string(self):
        """Test converting string to LogLevel."""
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        
        with pytest.raises(ValueError):
            LogLevel.from_string("INVALID")
    
    def test_to_python_level(self):
        """Test converting to Python logging level."""
        assert LogLevel.DEBUG.to_python_level() == logging.DEBUG
        assert LogLevel.INFO.to_python_level() == logging.INFO
        assert LogLevel.WARNING.to_python_level() == logging.WARNING
        assert LogLevel.ERROR.to_python_level() == logging.ERROR
        assert LogLevel.CRITICAL.to_python_level() == logging.CRITICAL


class TestLogContext:
    """Tests for the LogContext class."""
    
    def test_to_dict(self):
        """Test converting context to dictionary."""
        context = LogContext(
            trace_id="123",
            request_id="456",
            user_id="user1",
            additional_data={"custom": "value"}
        )
        
        result = context.to_dict()
        assert result["trace_id"] == "123"
        assert result["request_id"] == "456"
        assert result["user_id"] == "user1"
        assert result["custom"] == "value"
    
    def test_merge(self):
        """Test merging contexts."""
        context1 = LogContext(
            trace_id="123",
            request_id="456",
            additional_data={"a": 1, "b": 2}
        )
        
        context2 = LogContext(
            request_id="789",  # Should override
            tenant_id="tenant1",
            additional_data={"b": 3, "c": 4}  # Should override b and add c
        )
        
        merged = context1.merge(context2)
        
        assert merged.trace_id == "123"
        assert merged.request_id == "789"  # From context2
        assert merged.tenant_id == "tenant1"  # From context2
        assert merged.additional_data["a"] == 1  # From context1
        assert merged.additional_data["b"] == 3  # From context2
        assert merged.additional_data["c"] == 4  # From context2
    
    def test_merge_with_dict(self):
        """Test merging with a dictionary."""
        context = LogContext(
            trace_id="123",
            request_id="456",
            additional_data={"a": 1}
        )
        
        # Merge with dictionary
        merged = context.merge({
            "request_id": "789",
            "b": 2,
            "c": 3
        })
        
        assert merged.trace_id == "123"
        assert merged.request_id == "789"
        assert merged.additional_data["a"] == 1
        assert merged.additional_data["b"] == 2
        assert merged.additional_data["c"] == 3


@pytest.fixture
def reset_logging():
    """Reset logging configuration before and after tests."""
    # Save original handlers
    root = logging.getLogger()
    orig_handlers = root.handlers.copy()
    orig_level = root.level
    
    yield
    
    # Restore original handlers
    root.handlers = orig_handlers
    root.level = orig_level


class TestLoggingConfig:
    """Tests for logging configuration."""
    
    def test_config_from_dict(self):
        """Test creating LogConfig from ConfigProtocol."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "logging.level": "DEBUG",
            "logging.format": "json",
            "logging.console_output": True,
            "logging.file_output": True,
            "logging.file_path": "/tmp/test.log",
            "service.name": "test-service",
            "environment": "test",
        }.get(key, default)
        
        config = LogConfig.from_config(mock_config)
        
        assert config.level == LogLevel.DEBUG
        assert config.format == LogFormat.JSON
        assert config.console_output is True
        assert config.file_output is True
        assert config.file_path == "/tmp/test.log"
        assert config.service_name == "test-service"
        assert config.environment == "test"


class TestStructuredLogger:
    """Tests for the StructuredLogger class."""
    
    @pytest.fixture
    def setup_logger(self, reset_logging):
        """Set up a logger for testing."""
        configure_logging(LogConfig(level=LogLevel.DEBUG, console_output=True))
        yield get_logger("test")
    
    def test_log_methods(self, setup_logger, capsys):
        """Test basic logging methods."""
        logger = setup_logger
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        captured = capsys.readouterr()
        
        assert "Debug message" in captured.out
        assert "Info message" in captured.out
        assert "Warning message" in captured.out
        assert "Error message" in captured.out
        assert "Critical message" in captured.out
    
    def test_bind_context(self, setup_logger, capsys):
        """Test binding context to a logger."""
        logger = setup_logger
        
        bound_logger = logger.bind(user_id="user123", session="session456")
        bound_logger.info("Message with bound context")
        
        captured = capsys.readouterr()
        assert "Message with bound context" in captured.out
        
        # If in JSON format, check the context
        if setup_logger._config.format == LogFormat.JSON:
            log_entries = [json.loads(line) for line in captured.out.strip().split('\n')]
            relevant_entry = [e for e in log_entries if "Message with bound context" in e["message"]]
            assert relevant_entry
            assert relevant_entry[0]["context"]["user_id"] == "user123"
            assert relevant_entry[0]["context"]["session"] == "session456"
    
    def test_log_error(self, setup_logger, capsys):
        """Test logging errors."""
        logger = setup_logger
        
        error = ValidationError("Test validation error", field="test_field")
        logger.log_error(error)
        
        captured = capsys.readouterr()
        assert "Test validation error" in captured.out


class TestContextManagement:
    """Tests for context management functions."""
    
    def test_add_get_clear_context(self):
        """Test adding, getting, and clearing context."""
        clear_context()  # Start with clean state
        
        # Add context
        add_context(user_id="user123", action="login")
        
        # Get context
        context = get_context()
        assert context["user_id"] == "user123"
        assert context["action"] == "login"
        
        # Add more context
        add_context(session_id="sess456")
        context = get_context()
        assert context["user_id"] == "user123"
        assert context["action"] == "login"
        assert context["session_id"] == "sess456"
        
        # Clear context
        clear_context()
        assert get_context() == {}
    
    def test_with_logging_context_decorator(self, reset_logging):
        """Test the with_logging_context decorator."""
        # Configure for test
        configure_logging(LogConfig(level=LogLevel.DEBUG, console_output=True))
        logger = get_logger("test")
        
        # Define a function with the decorator
        @with_logging_context
        def test_function(param1, param2):
            # Inside the function, context should be set
            context = get_context()
            assert "function" in context
            assert "module" in context
            assert "args" in context
            assert context["args"]["param1"] == param1
            assert context["args"]["param2"] == param2
            
            logger.info("Inside decorated function")
            return param1 + param2
        
        # Call the function
        result = test_function("a", "b")
        assert result == "ab"
        
        # Context should be cleared after function call
        assert "function" not in get_context()
    
    def test_with_logging_context_static(self, reset_logging):
        """Test the with_logging_context decorator with static context."""
        # Configure for test
        configure_logging(LogConfig(level=LogLevel.DEBUG, console_output=True))
        logger = get_logger("test")
        
        # Define a function with the decorator and static context
        @with_logging_context(component="test_component", operation="test_op")
        def test_function():
            # Inside the function, static context should be set
            context = get_context()
            assert context["component"] == "test_component"
            assert context["operation"] == "test_op"
            
            logger.info("Inside function with static context")
            return True
        
        # Call the function
        result = test_function()
        assert result is True
        
        # Context should be cleared after function call
        assert "component" not in get_context()


@pytest.fixture
def mock_fastapi_app():
    """Create a mock FastAPI app."""
    app = FastAPI()
    return app


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""
    
    def test_middleware_initialization(self, mock_fastapi_app):
        """Test middleware initialization."""
        middleware = LoggingMiddleware(
            mock_fastapi_app,
            include_headers=True,
            include_query_params=True,
            exclude_paths=["/health", "/metrics"],
            sensitive_headers=["authorization", "cookie"]
        )
        
        assert middleware.include_headers is True
        assert middleware.include_query_params is True
        assert middleware.exclude_paths == ["/health", "/metrics"]
        assert middleware.sensitive_headers == ["authorization", "cookie"]
    
    @pytest.mark.asyncio
    async def test_middleware_excluded_path(self, mock_fastapi_app):
        """Test middleware skips excluded paths."""
        middleware = LoggingMiddleware(
            mock_fastapi_app,
            exclude_paths=["/health"]
        )
        
        # Create a mock request for an excluded path
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.client = MagicMock(host="127.0.0.1", port=12345)
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create a mock call_next function
        async def mock_call_next(request):
            return mock_response
        
        # Call the middleware
        with patch.object(middleware.logger, 'info') as mock_info:
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the middleware skipped logging
            mock_info.assert_not_called()
            
            # Verify the response was passed through
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_middleware_logs_request_response(self, mock_fastapi_app):
        """Test middleware logs requests and responses."""
        middleware = LoggingMiddleware(
            mock_fastapi_app,
            include_headers=True,
            include_query_params=True
        )
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {"user-agent": "Test-Agent", "authorization": "Bearer token123"}
        mock_request.query_params = {"param1": "value1"}
        mock_request.client = MagicMock(host="127.0.0.1", port=12345)
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create a mock call_next function
        async def mock_call_next(request):
            return mock_response
        
        # Call the middleware
        with patch.object(middleware.logger, 'info') as mock_info:
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the request was logged
            assert mock_info.call_count >= 2  # At least request and response logs
            
            # Check first call (request logging)
            request_call_args = mock_info.call_args_list[0]
            assert "HTTP GET /api/test" in request_call_args[0][0]
            
            # Check last call (response logging)
            response_call_args = mock_info.call_args_list[-1]
            assert "HTTP GET /api/test 200" in response_call_args[0][0]
            
            # Verify response
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_middleware_handles_exceptions(self, mock_fastapi_app):
        """Test middleware handles exceptions."""
        middleware = LoggingMiddleware(mock_fastapi_app)
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.client = MagicMock(host="127.0.0.1", port=12345)
        
        # Create a mock call_next function that raises an exception
        test_exception = ValueError("Test exception")
        async def mock_call_next(request):
            raise test_exception
        
        # Call the middleware
        with patch.object(middleware.logger, 'exception') as mock_exception_log:
            with pytest.raises(ValueError):
                await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the exception was logged
            mock_exception_log.assert_called_once()
            args = mock_exception_log.call_args[0]
            assert "Error processing HTTP GET /api/test" in args[0]
            assert "Test exception" in args[0]