# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the debugging middleware module.

These tests verify the functionality of the FastAPI middleware for debugging.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from uno.devtools.debugging.middleware import DebugMiddleware


class TestDebugMiddleware:
    """Tests for the DebugMiddleware class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.middleware = DebugMiddleware(
            enabled=True,
            log_requests=True,
            log_responses=True,
            log_sql=True,
            log_level="DEBUG"
        )
        self.app.add_middleware(DebugMiddleware, 
            enabled=True,
            log_requests=True,
            log_responses=True,
            log_sql=True,
            log_level="DEBUG"
        )
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "Test response"}
        
        self.client = TestClient(self.app)
    
    @patch("uno.devtools.debugging.middleware.logger")
    def test_log_request(self, mock_logger):
        """Test that requests are logged correctly."""
        # Call the test endpoint
        response = self.client.get("/test", headers={"X-Test": "value"})
        
        # Check that the request was logged
        assert response.status_code == 200
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Request received",
                "method": "GET",
                "path": "/test",
                "headers": pytest.helpers.match_partial_dict({
                    "x-test": "value"
                })
            })
        )
    
    @patch("uno.devtools.debugging.middleware.logger")
    def test_log_response(self, mock_logger):
        """Test that responses are logged correctly."""
        # Call the test endpoint
        response = self.client.get("/test")
        
        # Check that the response was logged
        assert response.status_code == 200
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Response sent",
                "status_code": 200,
                "headers": pytest.helpers.match_partial_dict({
                    "content-type": "application/json"
                }),
                "body": '{"message":"Test response"}'
            })
        )
    
    @patch("uno.devtools.debugging.middleware.logger")
    @patch("uno.devtools.debugging.sql_debug.capture_sql_queries")
    def test_log_sql_queries(self, mock_capture_sql, mock_logger):
        """Test that SQL queries are logged correctly."""
        # Mock the SQL capture function to return some queries
        mock_queries = [
            {"query": "SELECT * FROM users", "duration": 0.1, "params": {}}
        ]
        mock_capture_sql.return_value.__enter__.return_value = mock_queries
        
        # Call the test endpoint
        response = self.client.get("/test")
        
        # Check that the SQL queries were logged
        assert response.status_code == 200
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "SQL queries executed",
                "count": 1,
                "queries": mock_queries
            })
        )
    
    def test_middleware_disabled(self):
        """Test that middleware doesn't log when disabled."""
        # Create a new app with disabled middleware
        app = FastAPI()
        app.add_middleware(DebugMiddleware, enabled=False)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "Test response"}
        
        client = TestClient(app)
        
        # Patch the logger
        with patch("uno.devtools.debugging.middleware.logger") as mock_logger:
            # Call the test endpoint
            response = client.get("/test")
            
            # Check that the response was successful but no logging occurred
            assert response.status_code == 200
            mock_logger.debug.assert_not_called()

    @patch("uno.devtools.debugging.middleware.logger")
    @patch("uno.devtools.debugging.middleware.traceback")
    def test_log_error(self, mock_traceback, mock_logger):
        """Test that errors are logged correctly."""
        # Create a new app with error endpoint
        app = FastAPI()
        app.add_middleware(DebugMiddleware, enabled=True, log_errors=True)
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        client = TestClient(app)
        
        # Mock the traceback formatting
        mock_traceback.format_exc.return_value = "Test traceback"
        
        # Call the error endpoint
        with pytest.raises(ValueError):
            client.get("/error")
        
        # Check that the error was logged
        mock_logger.error.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Exception in request",
                "exception": "ValueError: Test error",
                "traceback": "Test traceback"
            })
        )