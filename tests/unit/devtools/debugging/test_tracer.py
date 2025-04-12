# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the function tracer module.

These tests verify the functionality of the function tracing utilities.
"""

import pytest
from unittest.mock import patch, MagicMock

from uno.devtools.debugging.tracer import trace_function, trace_class, TracerConfig


def test_function():
    """Simple test function used for testing the tracer."""
    return "test result"


class TestClass:
    """Simple test class used for testing the tracer."""
    
    def test_method(self, arg1, arg2=None):
        """Test method with args and kwargs."""
        return f"{arg1}:{arg2}"


class TestTraceFunctionDecorator:
    """Tests for the trace_function decorator."""
    
    @patch("uno.devtools.debugging.tracer.logger")
    def test_trace_function_basic(self, mock_logger):
        """Test basic function tracing."""
        # Decorate the test function
        decorated = trace_function(test_function)
        
        # Call the decorated function
        result = decorated()
        
        # Check that the function executed correctly
        assert result == "test result"
        
        # Check that entry and exit were logged
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Function call",
                "function": "test_function",
                "args": [],
                "kwargs": {}
            })
        )
        
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Function return",
                "function": "test_function",
                "result": "test result",
                "duration": pytest.helpers.any_float
            })
        )
    
    @patch("uno.devtools.debugging.tracer.logger")
    def test_trace_function_with_args(self, mock_logger):
        """Test tracing a function with arguments."""
        # Create a test function with arguments
        def func_with_args(a, b, c=None):
            return a + b
        
        # Decorate the function
        decorated = trace_function(func_with_args)
        
        # Call the decorated function
        result = decorated(1, 2, c=3)
        
        # Check that the function executed correctly
        assert result == 3
        
        # Check that args and kwargs were logged correctly
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Function call",
                "function": "func_with_args",
                "args": [1, 2],
                "kwargs": {"c": 3}
            })
        )
    
    @patch("uno.devtools.debugging.tracer.logger")
    def test_trace_function_exception(self, mock_logger):
        """Test tracing a function that raises an exception."""
        # Create a test function that raises an exception
        def func_with_exception():
            raise ValueError("Test exception")
        
        # Decorate the function
        decorated = trace_function(func_with_exception)
        
        # Call the decorated function
        with pytest.raises(ValueError):
            decorated()
        
        # Check that the exception was logged
        mock_logger.error.assert_called_once_with(
            pytest.helpers.match_partial_dict({
                "message": "Function exception",
                "function": "func_with_exception",
                "exception": "ValueError: Test exception",
                "traceback": pytest.helpers.any_string
            })
        )
    
    @patch("uno.devtools.debugging.tracer.logger")
    def test_trace_function_config(self, mock_logger):
        """Test tracing with custom configuration."""
        # Create a custom tracer config
        config = TracerConfig(
            log_args=True,
            log_result=False,
            log_entry=True,
            log_exit=True,
            log_level="INFO"
        )
        
        # Decorate a function with the custom config
        decorated = trace_function(test_function, config=config)
        
        # Call the decorated function
        result = decorated()
        
        # Check that the function executed correctly
        assert result == "test result"
        
        # Check that logs used the correct log level
        mock_logger.info.assert_called()
        mock_logger.debug.assert_not_called()


class TestTraceClassDecorator:
    """Tests for the trace_class decorator."""
    
    @patch("uno.devtools.debugging.tracer.logger")
    def test_trace_class(self, mock_logger):
        """Test tracing all methods in a class."""
        # Decorate the test class
        DecoratedClass = trace_class(TestClass)
        
        # Create an instance and call a method
        instance = DecoratedClass()
        result = instance.test_method("test", arg2="value")
        
        # Check that the method executed correctly
        assert result == "test:value"
        
        # Check that method entry and exit were logged
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Function call",
                "function": "TestClass.test_method",
                "args": [pytest.helpers.instance_of(DecoratedClass), "test"],
                "kwargs": {"arg2": "value"}
            })
        )
        
        mock_logger.debug.assert_any_call(
            pytest.helpers.match_partial_dict({
                "message": "Function return",
                "function": "TestClass.test_method",
                "result": "test:value"
            })
        )
    
    @patch("uno.devtools.debugging.tracer.logger")
    def test_trace_class_with_config(self, mock_logger):
        """Test tracing a class with custom configuration."""
        # Create a custom tracer config
        config = TracerConfig(
            log_args=True,
            log_result=True,
            log_entry=True,
            log_exit=True,
            log_level="INFO",
            include_methods=["test_method"],
            exclude_methods=["__init__"]
        )
        
        # Decorate the test class with the custom config
        DecoratedClass = trace_class(TestClass, config=config)
        
        # Create an instance and call a method
        instance = DecoratedClass()
        result = instance.test_method("test", arg2="value")
        
        # Check that the method executed correctly
        assert result == "test:value"
        
        # Check that logs used the correct log level
        mock_logger.info.assert_called()
        mock_logger.debug.assert_not_called()