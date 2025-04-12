# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the performance profiler module.

These tests verify the functionality of the performance profiling tools.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
import io
import sys

from uno.devtools.profiling.profiler import (
    profile,
    Profiler,
    ProfilerConfig,
    ProfilerResult,
    ProfilerStats
)


def test_function():
    """Simple test function for profiling."""
    time.sleep(0.01)
    return "test result"


class TestProfileDecorator:
    """Tests for the profile decorator."""
    
    def test_profile_decorator_basic(self):
        """Test basic function profiling."""
        # Decorate the test function
        decorated = profile(test_function)
        
        # Call the decorated function
        result = decorated()
        
        # Check that the function executed correctly
        assert result == "test result"
    
    def test_profile_decorator_with_args(self):
        """Test profiling a function with arguments."""
        # Create a test function with arguments
        @profile
        def func_with_args(a, b, c=None):
            time.sleep(0.01)
            return a + b
        
        # Call the decorated function
        result = func_with_args(1, 2, c=3)
        
        # Check that the function executed correctly
        assert result == 3
    
    @patch("uno.devtools.profiling.profiler.logger")
    def test_profile_decorator_with_logging(self, mock_logger):
        """Test profiling with logging enabled."""
        # Create a test function with profiling and logging
        @profile(log=True)
        def func_to_log():
            time.sleep(0.01)
            return "logged result"
        
        # Call the decorated function
        result = func_to_log()
        
        # Check that the function executed correctly
        assert result == "logged result"
        
        # Check that performance was logged
        mock_logger.info.assert_called_with(
            pytest.helpers.match_partial_dict({
                "message": "Function profile",
                "function": "func_to_log",
                "duration": pytest.helpers.any_float,
                "calls": 1
            })
        )
    
    def test_profile_decorator_with_output(self):
        """Test profiling with output to a custom stream."""
        # Create a string buffer for output
        output = io.StringIO()
        
        # Create a test function with profiling and output
        @profile(output=output)
        def func_with_output():
            time.sleep(0.01)
            return "output result"
        
        # Call the decorated function
        result = func_with_output()
        
        # Check that the function executed correctly
        assert result == "output result"
        
        # Check that performance data was written to the output
        output_text = output.getvalue()
        assert "func_with_output" in output_text
        assert "time" in output_text.lower()


class TestProfilerClass:
    """Tests for the Profiler class."""
    
    def test_profiler_as_context_manager(self):
        """Test using the Profiler as a context manager."""
        # Create a profiler
        profiler = Profiler("test_operation")
        
        # Use the profiler as a context manager
        with profiler:
            time.sleep(0.01)
            result = "context manager result"
        
        # Check that the profiler captured performance data
        assert profiler.result is not None
        assert profiler.result.name == "test_operation"
        assert profiler.result.duration > 0
    
    def test_profiler_start_stop(self):
        """Test starting and stopping the profiler manually."""
        # Create a profiler
        profiler = Profiler("manual_test")
        
        # Start the profiler
        profiler.start()
        
        # Perform some operations
        time.sleep(0.01)
        
        # Stop the profiler
        profiler.stop()
        
        # Check that the profiler captured performance data
        assert profiler.result is not None
        assert profiler.result.name == "manual_test"
        assert profiler.result.duration > 0
    
    def test_profiler_with_nested_operations(self):
        """Test profiling nested operations."""
        # Create a parent profiler
        parent = Profiler("parent_operation")
        
        # Start the parent profiler
        with parent:
            # Do some work in the parent
            time.sleep(0.01)
            
            # Create and use a child profiler
            with Profiler("child_operation") as child:
                time.sleep(0.01)
            
            # Do more work in the parent
            time.sleep(0.01)
        
        # Check that both profilers captured performance data
        assert parent.result is not None
        assert parent.result.name == "parent_operation"
        assert parent.result.duration > 0.02  # Should include all three sleep calls
    
    @patch("uno.devtools.profiling.profiler.cProfile")
    def test_profiler_with_cprofile(self, mock_cprofile):
        """Test profiling with cProfile integration."""
        # Mock the Profile class
        mock_profile = MagicMock()
        mock_cprofile.Profile.return_value = mock_profile
        
        # Create a profiler with cProfile enabled
        config = ProfilerConfig(use_cprofile=True)
        profiler = Profiler("cprofile_test", config=config)
        
        # Use the profiler
        with profiler:
            time.sleep(0.01)
        
        # Check that cProfile was used
        mock_profile.enable.assert_called_once()
        mock_profile.disable.assert_called_once()
        mock_profile.print_stats.assert_called()
    
    def test_profiler_stats(self):
        """Test collecting and analyzing profiler statistics."""
        # Create a profiler stats object
        stats = ProfilerStats()
        
        # Add some sample profile results
        stats.add_result(ProfilerResult(name="op1", duration=0.1, calls=1))
        stats.add_result(ProfilerResult(name="op2", duration=0.2, calls=1))
        stats.add_result(ProfilerResult(name="op1", duration=0.15, calls=1))
        
        # Get the aggregated stats
        agg_stats = stats.get_stats()
        
        # Check the aggregated statistics
        assert len(agg_stats) == 2  # Two unique operations
        assert agg_stats["op1"]["count"] == 2
        assert agg_stats["op1"]["total_duration"] == 0.25
        assert agg_stats["op1"]["avg_duration"] == 0.125
        assert agg_stats["op2"]["count"] == 1
        assert agg_stats["op2"]["total_duration"] == 0.2
        
        # Test sorting by total duration
        sorted_stats = stats.get_sorted_stats(sort_by="total_duration")
        assert sorted_stats[0][0] == "op1"  # op1 has higher total duration