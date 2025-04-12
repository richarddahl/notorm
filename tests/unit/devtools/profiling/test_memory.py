# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the memory profiler module.

These tests verify the functionality of the memory profiling tools.
"""

import pytest
import gc
from unittest.mock import patch, MagicMock
import io
import sys

from uno.devtools.profiling.memory import (
    track_memory,
    MemoryTracker,
    MemoryTrackerConfig,
    MemorySnapshot,
    MemoryLeakDetector
)


class TestMemoryTracker:
    """Tests for the MemoryTracker class."""
    
    def test_memory_tracker_as_context_manager(self):
        """Test using the MemoryTracker as a context manager."""
        # Create a memory tracker
        tracker = MemoryTracker("test_operation")
        
        # Use the tracker as a context manager
        with tracker as snapshot:
            # Allocate some memory
            data = [0] * 10000
        
        # Check that the tracker captured memory usage
        assert snapshot is not None
        assert snapshot.peak_usage > 0
        assert snapshot.operation_name == "test_operation"
    
    def test_memory_tracker_start_stop(self):
        """Test starting and stopping the memory tracker manually."""
        # Create a memory tracker
        tracker = MemoryTracker("manual_test")
        
        # Start the tracker
        tracker.start()
        
        # Allocate some memory
        data = [0] * 10000
        
        # Stop the tracker
        snapshot = tracker.stop()
        
        # Check that the tracker captured memory usage
        assert snapshot is not None
        assert snapshot.peak_usage > 0
        assert snapshot.operation_name == "manual_test"
    
    @patch("uno.devtools.profiling.memory.sys")
    def test_memory_snapshot_diff(self, mock_sys):
        """Test computing the difference between memory snapshots."""
        # Mock sys.getsizeof to return consistent values
        mock_sys.getsizeof.return_value = 100
        
        # Create two memory snapshots
        snapshot1 = MemorySnapshot(
            operation_name="operation1",
            start_usage=1000,
            end_usage=2000,
            peak_usage=2500,
            allocated_objects={"list": 10, "dict": 5},
            timestamp=0
        )
        
        snapshot2 = MemorySnapshot(
            operation_name="operation2",
            start_usage=2000,
            end_usage=3000,
            peak_usage=3500,
            allocated_objects={"list": 15, "dict": 10},
            timestamp=1
        )
        
        # Compute the difference
        diff = snapshot2 - snapshot1
        
        # Check the difference
        assert diff.operation_name == "operation2 - operation1"
        assert diff.start_usage == 1000  # 2000 - 1000
        assert diff.end_usage == 1000  # 3000 - 2000
        assert diff.peak_usage == 1000  # 3500 - 2500
        assert diff.allocated_objects == {"list": 5, "dict": 5}
    
    @patch("uno.devtools.profiling.memory.logger")
    def test_memory_tracker_with_logging(self, mock_logger):
        """Test memory tracking with logging enabled."""
        # Create a memory tracker with logging
        config = MemoryTrackerConfig(log=True, log_level="INFO")
        tracker = MemoryTracker("logged_operation", config=config)
        
        # Use the tracker
        with tracker:
            # Allocate some memory
            data = [0] * 10000
        
        # Check that memory usage was logged
        mock_logger.info.assert_called_with(
            pytest.helpers.match_partial_dict({
                "message": "Memory usage",
                "operation": "logged_operation",
                "start_usage": pytest.helpers.any_int,
                "end_usage": pytest.helpers.any_int,
                "peak_usage": pytest.helpers.any_int,
                "net_change": pytest.helpers.any_int
            })
        )
    
    @patch("uno.devtools.profiling.memory.gc")
    def test_memory_tracker_with_gc_tracking(self, mock_gc):
        """Test memory tracking with garbage collection tracking."""
        # Mock the garbage collector
        mock_gc.collect.return_value = 10
        mock_gc.get_objects.return_value = ["obj1", "obj2"]
        
        # Create a memory tracker with GC tracking
        config = MemoryTrackerConfig(track_gc=True)
        tracker = MemoryTracker("gc_operation", config=config)
        
        # Use the tracker
        with tracker as snapshot:
            # Allocate some memory and create garbage
            data = [0] * 10000
            del data
        
        # Check that GC was tracked
        mock_gc.collect.assert_called()
        assert snapshot.gc_collections >= 0
        assert len(snapshot.gc_objects) >= 0
    
    def test_track_memory_decorator(self):
        """Test the track_memory decorator."""
        # Define a function to track
        @track_memory
        def memory_intensive_function():
            # Allocate some memory
            data = [0] * 10000
            return "result"
        
        # Call the decorated function
        result = memory_intensive_function()
        
        # Check that the function executed correctly
        assert result == "result"
        
        # Define a function with custom tracker config
        @track_memory(log=True)
        def custom_tracked_function():
            # Allocate some memory
            data = [0] * 10000
            return "custom result"
        
        # Call the decorated function with custom config
        with patch("uno.devtools.profiling.memory.logger") as mock_logger:
            result = custom_tracked_function()
            
            # Check that the function executed correctly
            assert result == "custom result"
            
            # Check that memory usage was logged
            mock_logger.info.assert_called()


class TestMemoryLeakDetector:
    """Tests for the MemoryLeakDetector class."""
    
    @patch("uno.devtools.profiling.memory.gc")
    def test_memory_leak_detector(self, mock_gc):
        """Test detecting memory leaks."""
        # Mock the garbage collector
        mock_objects = [MagicMock(), MagicMock()]
        mock_gc.get_objects.return_value = mock_objects
        
        # Create a leak detector
        detector = MemoryLeakDetector()
        
        # Take an initial snapshot
        detector.snapshot()
        
        # Simulate some new objects being created
        new_objects = [MagicMock(), MagicMock(), MagicMock()]
        mock_gc.get_objects.return_value = mock_objects + new_objects
        
        # Check for leaks
        leaks = detector.check_leaks()
        
        # Should detect 3 new objects
        assert len(leaks) == 3
    
    @patch("uno.devtools.profiling.memory.gc")
    @patch("uno.devtools.profiling.memory.logger")
    def test_memory_leak_detector_with_logging(self, mock_logger, mock_gc):
        """Test memory leak detection with logging."""
        # Mock the garbage collector
        mock_objects = [MagicMock(), MagicMock()]
        mock_gc.get_objects.return_value = mock_objects
        
        # Create a leak detector with logging
        detector = MemoryLeakDetector(log=True)
        
        # Take an initial snapshot
        detector.snapshot()
        
        # Simulate some new objects being created
        new_objects = [MagicMock(), MagicMock()]
        mock_gc.get_objects.return_value = mock_objects + new_objects
        
        # Check for leaks
        detector.check_leaks()
        
        # Check that leaks were logged
        mock_logger.warning.assert_called_with(
            pytest.helpers.match_partial_dict({
                "message": "Potential memory leaks detected",
                "new_objects": 2
            })
        )