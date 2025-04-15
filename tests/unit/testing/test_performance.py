# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the performance testing module.

These tests verify the functionality of the performance testing utilities.
"""

import json
import os
import time
import pytest
import asyncio
from pathlib import Path

from uno.testing.performance import PerformanceTest, benchmark


def test_performance_test_measure():
    """Test the PerformanceTest measure context manager."""
    # Create a performance test
    perf_test = PerformanceTest(name="measure_example")
    
    # Use the measure context manager
    with perf_test.measure():
        # Simulate work
        time.sleep(0.01)
    
    # Check that a measurement was recorded
    assert len(perf_test.results) == 1
    assert perf_test.results[0] >= 0.01
    
    # Get statistics
    stats = perf_test.get_statistics()
    assert "min" in stats
    assert "max" in stats
    assert "mean" in stats
    assert "median" in stats
    assert "stdev" in stats


def test_performance_test_run():
    """Test the PerformanceTest run method."""
    # Create a performance test
    perf_test = PerformanceTest(
        name="run_example",
        iterations=3,
        warmup_iterations=1
    )
    
    # Define a test function
    def test_func(x, y):
        time.sleep(0.01)
        return x + y
    
    # Run the test function
    result, details = perf_test.run(test_func, 2, 3)
    
    # Check the function result
    assert result == 5
    
    # Check that measurements were recorded
    assert len(perf_test.results) == 3
    for duration in perf_test.results:
        assert duration >= 0.01
    
    # Check performance details
    assert "current" in details
    assert "message" in details


@pytest.mark.asyncio
async def test_performance_test_run_async():
    """Test the PerformanceTest run_async method."""
    # Create a performance test
    perf_test = PerformanceTest(
        name="run_async_example",
        iterations=3,
        warmup_iterations=1
    )
    
    # Define an async test function
    async def test_async_func(x, y):
        await asyncio.sleep(0.01)
        return x + y
    
    # Run the async test function
    result, details = await perf_test.run_async(test_async_func, 2, 3)
    
    # Check the function result
    assert result == 5
    
    # Check that measurements were recorded
    assert len(perf_test.results) == 3
    for duration in perf_test.results:
        assert duration >= 0.01
    
    # Check performance details
    assert "current" in details
    assert "message" in details


def test_performance_test_save_benchmark():
    """Test saving a performance benchmark."""
    # Create a performance test with a unique name
    test_name = "save_benchmark_example"
    perf_test = PerformanceTest(name=test_name)
    
    # Record some measurements
    perf_test.record_measurement(0.01)
    perf_test.record_measurement(0.02)
    perf_test.record_measurement(0.03)
    
    # Save the benchmark
    perf_test.save_benchmark()
    
    # Check that the benchmark file was created
    benchmark_path = perf_test.benchmark_path
    assert benchmark_path.exists()
    
    # Check the content of the benchmark file
    with open(benchmark_path, "r") as f:
        data = json.load(f)
    
    assert "current" in data
    assert "history" in data
    # The history length could vary depending on previous test runs
    # Just check that it contains at least our entry
    assert len(data["history"]) >= 1
    assert "stats" in data["current"]
    assert "timestamp" in data["current"]


def test_performance_test_check_performance():
    """Test checking performance against a baseline."""
    # Create a performance test with a unique name
    test_name = "check_performance_example"
    perf_test = PerformanceTest(name=test_name)
    
    # Record some measurements
    perf_test.record_measurement(0.01)
    perf_test.record_measurement(0.02)
    perf_test.record_measurement(0.03)
    
    # Check performance (first run creates baseline)
    acceptable, details = perf_test.check_performance()
    assert acceptable is True
    assert "baseline" in details
    assert "current" in details
    assert "message" in details
    
    # Create a new test with slightly worse performance
    perf_test2 = PerformanceTest(
        name=test_name,
        baseline_multiplier=1.5  # Allow up to 50% slower
    )
    
    # Record measurements that are 30% slower
    perf_test2.record_measurement(0.013)
    perf_test2.record_measurement(0.026)
    perf_test2.record_measurement(0.039)
    
    # Check performance (should be acceptable)
    acceptable, details = perf_test2.check_performance()
    assert acceptable is True
    assert "comparison" in details
    assert details["comparison"]["percent_change"] > 0
    
    # Create a new test with much worse performance
    perf_test3 = PerformanceTest(
        name=test_name,
        baseline_multiplier=1.2  # Allow up to 20% slower
    )
    
    # Record measurements that are 100% slower
    perf_test3.record_measurement(0.02)
    perf_test3.record_measurement(0.04)
    perf_test3.record_measurement(0.06)
    
    # Check performance (should not be acceptable)
    acceptable, details = perf_test3.check_performance(save=False)  # Don't save as baseline
    assert acceptable is False
    assert "comparison" in details
    assert details["comparison"]["percent_change"] > 0


@benchmark(name="benchmark_decorator_example", iterations=3, warmup_iterations=1)
def test_benchmark_decorator():
    """Test the benchmark decorator."""
    # Function is automatically benchmarked by the decorator
    time.sleep(0.01)
    return 42


@benchmark(name="benchmark_decorator_example_skip", skip_regression_fail=True)
def test_benchmark_decorator_skip_regression():
    """Test the benchmark decorator with skip_regression_fail=True."""
    # This function is much slower than the baseline but won't fail
    time.sleep(0.05)
    return 42


@pytest.mark.asyncio
@benchmark(name="benchmark_decorator_async_example", iterations=3, warmup_iterations=1)
async def test_benchmark_decorator_async():
    """Test the benchmark decorator with an async function."""
    # Async function is automatically benchmarked by the decorator
    await asyncio.sleep(0.01)
    return 42