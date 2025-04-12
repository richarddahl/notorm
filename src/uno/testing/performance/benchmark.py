# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Performance testing utilities for Uno applications.

This module provides functions and classes for performance testing,
allowing developers to measure and track performance metrics over time.
"""

import asyncio
import functools
import json
import os
import inspect
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

import pytest


# Type variable for generic function
F = TypeVar("F", bound=Callable)


def _get_benchmark_dir() -> Path:
    """
    Get the directory where benchmark results are stored.
    
    Returns:
        Path to the benchmark directory
    """
    # Start with the current file's directory
    current_file = inspect.currentframe().f_back.f_back.f_code.co_filename
    current_dir = Path(current_file).parent
    
    # Walk up the directory tree to find tests directory
    test_dir = None
    current_path = current_dir
    while current_path.name and not test_dir:
        if current_path.name == "tests":
            test_dir = current_path
            break
        current_path = current_path.parent
    
    if not test_dir:
        # If we couldn't find a tests directory, use a conventional location
        project_root = Path(os.getcwd())
        test_dir = project_root / "tests"
    
    # Create benchmarks directory if it doesn't exist
    benchmark_dir = test_dir / "benchmarks"
    benchmark_dir.mkdir(exist_ok=True)
    
    return benchmark_dir


def _get_caller_info() -> Dict[str, str]:
    """
    Get information about the caller function.
    
    Returns:
        Dictionary with information about the caller
    """
    # Get info about the test function that called benchmark
    frame = inspect.currentframe().f_back.f_back
    caller_file = frame.f_code.co_filename
    caller_function = frame.f_code.co_name
    caller_class = None
    
    # Try to determine the class name if the caller is a method
    frame_locals = frame.f_locals
    if "self" in frame_locals:
        caller_class = frame_locals["self"].__class__.__name__
    
    # Get the module name
    module_name = inspect.getmodulename(caller_file) or "unknown_module"
    
    return {
        "file": caller_file,
        "module": module_name,
        "function": caller_function,
        "class": caller_class
    }


def _get_benchmark_path(caller_info: Dict[str, str], name: Optional[str] = None) -> Path:
    """
    Get the path to the benchmark file.
    
    Args:
        caller_info: Information about the caller
        name: Optional name to differentiate multiple benchmarks in the same test
        
    Returns:
        Path to the benchmark file
    """
    benchmark_dir = _get_benchmark_dir()
    
    # Create a benchmark filename based on the caller information
    module_part = caller_info["module"]
    class_part = f"{caller_info['class']}_" if caller_info["class"] else ""
    func_part = caller_info["function"]
    name_part = f"_{name}" if name else ""
    
    filename = f"{module_part}_{class_part}{func_part}{name_part}.benchmark.json"
    
    # Create module-specific subdirectory
    module_dir = benchmark_dir / module_part
    module_dir.mkdir(exist_ok=True)
    
    return module_dir / filename


class PerformanceTest:
    """
    Class for running and analyzing performance tests.
    
    This class provides utilities for measuring the performance of functions
    and comparing the results against previous benchmarks.
    
    Example:
        ```python
        def test_database_query_performance():
            test = PerformanceTest(name="db-query")
            
            # Measure the performance of a function
            with test.measure():
                result = db.query(...)
                
            # Assert that the performance is acceptable
            assert test.check_performance()
        ```
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        iterations: int = 5,
        warmup_iterations: int = 2,
        baseline_multiplier: float = 1.2,
    ):
        """
        Initialize a performance test.
        
        Args:
            name: Name of the test (used for the benchmark file)
            iterations: Number of iterations to run
            warmup_iterations: Number of warmup iterations
            baseline_multiplier: Multiplier for the baseline (e.g., 1.2 means 20% slower is considered a regression)
        """
        self.name = name
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.baseline_multiplier = baseline_multiplier
        self.results: List[float] = []
        self.caller_info = _get_caller_info()
        self.benchmark_path = _get_benchmark_path(self.caller_info, name)
    
    def measure(self) -> "PerformanceContextManager":
        """
        Context manager for measuring the execution time of a block of code.
        
        Returns:
            A context manager that measures execution time
            
        Example:
            ```python
            with test.measure():
                # Code to measure
                result = expensive_operation()
            ```
        """
        return PerformanceContextManager(self)
    
    def record_measurement(self, duration: float) -> None:
        """
        Record a measurement.
        
        Args:
            duration: The duration of the operation in seconds
        """
        self.results.append(duration)
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Calculate statistics for the recorded measurements.
        
        Returns:
            Dictionary with statistics (min, max, mean, median, stdev)
        """
        if not self.results:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "stdev": 0.0
            }
        
        return {
            "min": min(self.results),
            "max": max(self.results),
            "mean": statistics.mean(self.results),
            "median": statistics.median(self.results),
            "stdev": statistics.stdev(self.results) if len(self.results) > 1 else 0.0
        }
    
    def save_benchmark(self) -> None:
        """
        Save the current results as a benchmark.
        """
        stats = self.get_statistics()
        timestamp = datetime.now().isoformat()
        
        # Read existing data if available
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {"history": []}
        else:
            data = {"history": []}
        
        # Add current results to history
        data["history"].append({
            "timestamp": timestamp,
            "stats": stats,
            "results": self.results
        })
        
        # Keep only the last 10 benchmark runs
        if len(data["history"]) > 10:
            data["history"] = data["history"][-10:]
        
        # Update current benchmark
        data["current"] = {
            "timestamp": timestamp,
            "stats": stats
        }
        
        # Save to file
        with open(self.benchmark_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def check_performance(self, save: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the current performance meets the baseline.
        
        Args:
            save: If True, save the current results as a benchmark
            
        Returns:
            Tuple of (is_acceptable, details)
        """
        current_stats = self.get_statistics()
        
        # Load baseline if available
        baseline = None
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r") as f:
                try:
                    data = json.load(f)
                    if "current" in data:
                        baseline = data["current"]["stats"]
                except (json.JSONDecodeError, KeyError):
                    pass
        
        # If no baseline, current results become the baseline
        if baseline is None:
            if save:
                self.save_benchmark()
            return True, {
                "baseline": None,
                "current": current_stats,
                "comparison": None,
                "acceptable": True,
                "message": "No baseline available, current results set as baseline"
            }
        
        # Compare with baseline
        baseline_mean = baseline["mean"]
        current_mean = current_stats["mean"]
        ratio = current_mean / baseline_mean if baseline_mean > 0 else 1.0
        acceptable = ratio <= self.baseline_multiplier
        
        comparison = {
            "ratio": ratio,
            "percent_change": (ratio - 1.0) * 100,
            "acceptable": acceptable
        }
        
        # Determine message
        if acceptable:
            if ratio < 0.8:  # 20% improvement
                message = f"Performance improved by {(1.0 - ratio) * 100:.1f}%"
            elif ratio < 0.95:  # 5% improvement
                message = f"Performance slightly improved by {(1.0 - ratio) * 100:.1f}%"
            elif ratio > 1.05:  # 5% regression but still acceptable
                message = f"Performance slightly degraded by {(ratio - 1.0) * 100:.1f}% but still acceptable"
            else:
                message = "Performance is stable"
        else:
            message = f"Performance regression detected: {(ratio - 1.0) * 100:.1f}% slower than baseline"
        
        # Save results if requested
        if save:
            self.save_benchmark()
        
        return acceptable, {
            "baseline": baseline,
            "current": current_stats,
            "comparison": comparison,
            "acceptable": acceptable,
            "message": message
        }
    
    def run(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Run a function and measure its performance.
        
        Args:
            func: Function to measure
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Tuple of (function_result, performance_details)
        """
        # Run warmup iterations
        for _ in range(self.warmup_iterations):
            func(*args, **kwargs)
        
        # Run measured iterations
        self.results = []
        result = None
        
        for _ in range(self.iterations):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            self.record_measurement(duration)
        
        # Check performance and return results
        acceptable, details = self.check_performance()
        return result, details
    
    async def run_async(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Run an async function and measure its performance.
        
        Args:
            func: Async function to measure
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Tuple of (function_result, performance_details)
        """
        # Run warmup iterations
        for _ in range(self.warmup_iterations):
            await func(*args, **kwargs)
        
        # Run measured iterations
        self.results = []
        result = None
        
        for _ in range(self.iterations):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            self.record_measurement(duration)
        
        # Check performance and return results
        acceptable, details = self.check_performance()
        return result, details


class PerformanceContextManager:
    """Context manager for measuring the execution time of a block of code."""
    
    def __init__(self, perf_test: PerformanceTest):
        """
        Initialize the context manager.
        
        Args:
            perf_test: The PerformanceTest instance to record measurements to
        """
        self.perf_test = perf_test
        self.start_time = 0.0
    
    def __enter__(self) -> "PerformanceContextManager":
        """Start measuring time."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop measuring time and record the duration."""
        end_time = time.time()
        duration = end_time - self.start_time
        self.perf_test.record_measurement(duration)


def benchmark(
    name: Optional[str] = None,
    iterations: int = 5,
    warmup_iterations: int = 2,
    baseline_multiplier: float = 1.2,
    skip_regression_fail: bool = False,
) -> Callable[[F], F]:
    """
    Decorator for benchmarking a function's performance.
    
    This decorator will run the function multiple times, measure its performance,
    and compare it against a baseline. It will raise an assertion error if
    the performance is worse than the baseline by more than the specified multiplier.
    
    Args:
        name: Name for the benchmark (defaults to the function name)
        iterations: Number of iterations to run (excluding warmup)
        warmup_iterations: Number of warmup iterations
        baseline_multiplier: Multiplier for the acceptable performance (e.g., 1.2 means 20% slower is acceptable)
        skip_regression_fail: If True, don't fail the test on performance regression
        
    Returns:
        Decorated function
        
    Example:
        ```python
        @benchmark(name="query-users", iterations=10)
        def test_query_users():
            result = db.query(User).all()
            assert len(result) > 0
        ```
    """
    def decorator(func: F) -> F:
        benchmark_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create performance test instance
            perf_test = PerformanceTest(
                name=benchmark_name,
                iterations=iterations,
                warmup_iterations=warmup_iterations,
                baseline_multiplier=baseline_multiplier
            )
            
            # Run warmup iterations
            for _ in range(warmup_iterations):
                func(*args, **kwargs)
            
            # Run measured iterations
            perf_test.results = []
            result = None
            
            for _ in range(iterations):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                perf_test.record_measurement(duration)
            
            # Check performance
            acceptable, details = perf_test.check_performance()
            
            # Fail the test if performance is unacceptable (unless skip_regression_fail is True)
            if not acceptable and not skip_regression_fail:
                assert False, details["message"]
            
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create performance test instance
            perf_test = PerformanceTest(
                name=benchmark_name,
                iterations=iterations,
                warmup_iterations=warmup_iterations,
                baseline_multiplier=baseline_multiplier
            )
            
            # Run warmup iterations
            for _ in range(warmup_iterations):
                await func(*args, **kwargs)
            
            # Run measured iterations
            perf_test.results = []
            result = None
            
            for _ in range(iterations):
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                perf_test.record_measurement(duration)
            
            # Check performance
            acceptable, details = perf_test.check_performance()
            
            # Fail the test if performance is unacceptable (unless skip_regression_fail is True)
            if not acceptable and not skip_regression_fail:
                assert False, details["message"]
            
            return result
        
        # Determine if the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, wrapper)
    
    return decorator