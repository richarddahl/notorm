#!/usr/bin/env python
"""
Benchmark Runner for UNO Core Components

This script runs benchmarks for core components of the UNO framework,
measuring performance metrics such as throughput, latency, and resource usage.

The results are stored in JSON format for analysis and visualization.
"""

import asyncio
import argparse
import json
import os
import time
import datetime
import platform
import statistics
import sys
import uuid
from typing import Dict, List, Any, Callable, Awaitable, Optional, Tuple, Type, Union
from pathlib import Path
from functools import wraps
import importlib.util
import inspect
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from uno.core.logging import configure_logging, get_logger


# Benchmark result type
BenchmarkResult = Dict[str, Any]


class BenchmarkConfig:
    """Configuration for benchmarks."""

    def __init__(
        self,
        iterations: int = 100,
        warmup_iterations: int = 10,
        parallel_runs: int = 1,
        timeout: float = 60.0,
        save_results: bool = True,
        results_dir: str | None = None,
        include_resource_metrics: bool = True,
        benchmarks_to_run: list[str] | None = None,
        categories_to_run: list[str] | None = None,
        verbose: bool = False,
    ):
        """
        Initialize benchmark configuration.

        Args:
            iterations: Number of iterations for each benchmark
            warmup_iterations: Number of warm-up iterations (not included in results)
            parallel_runs: Number of parallel benchmark runs
            timeout: Timeout in seconds for each benchmark
            save_results: Whether to save results to disk
            results_dir: Directory to save results to (defaults to ./results)
            include_resource_metrics: Whether to include CPU and memory usage metrics
            benchmarks_to_run: List of specific benchmarks to run (None = all)
            categories_to_run: List of specific categories to run (None = all)
            verbose: Whether to print verbose output
        """
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.parallel_runs = parallel_runs
        self.timeout = timeout
        self.save_results = save_results
        self.results_dir = results_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "results"
        )
        self.include_resource_metrics = include_resource_metrics
        self.benchmarks_to_run = benchmarks_to_run
        self.categories_to_run = categories_to_run
        self.verbose = verbose

        # Create results directory if it doesn't exist
        if self.save_results and not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)


class Benchmark:
    """Base class for benchmarks."""

    # Class attributes for registration
    category: str = "uncategorized"
    name: str = "unnamed_benchmark"
    description: str = "No description provided"
    tags: list[str] = []

    def __init__(self, config: BenchmarkConfig):
        """
        Initialize the benchmark.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.logger = get_logger(f"benchmark.{self.category}.{self.name}")

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        pass

    async def teardown(self) -> None:
        """Clean up the benchmark environment."""
        pass

    async def run_iteration(self) -> Dict[str, Any]:
        """
        Run a single benchmark iteration.

        Returns:
            Metrics for the iteration
        """
        raise NotImplementedError("Subclasses must implement run_iteration")

    async def run(self) -> BenchmarkResult:
        """
        Run the benchmark.

        Returns:
            Benchmark results
        """
        self.logger.info(f"Starting benchmark: {self.name}")

        # Ensure proper setup
        await self.setup()

        try:
            # Track metrics
            start_time = time.time()
            iteration_times: list[float] = []
            iteration_metrics: list[dict[str, Any]] = []

            # Warm-up iterations
            self.logger.debug(
                f"Running {self.config.warmup_iterations} warm-up iterations"
            )
            for i in range(self.config.warmup_iterations):
                await self.run_iteration()

            # Timed iterations
            self.logger.debug(f"Running {self.config.iterations} timed iterations")
            for i in range(self.config.iterations):
                iteration_start = time.perf_counter()
                metrics = await self.run_iteration()
                iteration_end = time.perf_counter()

                # Record time and metrics
                iteration_time = iteration_end - iteration_start
                iteration_times.append(iteration_time)
                iteration_metrics.append(metrics)

                if self.config.verbose:
                    self.logger.debug(
                        f"Iteration {i+1}/{self.config.iterations}: {iteration_time:.6f}s"
                    )

            # Calculate statistics
            total_time = time.time() - start_time
            avg_time = statistics.mean(iteration_times)
            median_time = statistics.median(iteration_times)
            min_time = min(iteration_times)
            max_time = max(iteration_times)
            stddev = (
                statistics.stdev(iteration_times) if len(iteration_times) > 1 else 0
            )

            # Percentiles
            sorted_times = sorted(iteration_times)
            p90 = sorted_times[int(0.9 * len(sorted_times))]
            p95 = sorted_times[int(0.95 * len(sorted_times))]
            p99 = sorted_times[int(0.99 * len(sorted_times))]

            # Resource usage (if available)
            resource_metrics = {}
            if self.config.include_resource_metrics:
                try:
                    import psutil

                    process = psutil.Process()

                    # Memory info
                    memory_info = process.memory_info()
                    resource_metrics["memory_rss"] = memory_info.rss
                    resource_metrics["memory_vms"] = memory_info.vms

                    # CPU info
                    resource_metrics["cpu_percent"] = process.cpu_percent(interval=0.1)
                    resource_metrics["thread_count"] = process.num_threads()

                    # File descriptors
                    if hasattr(process, "num_fds"):
                        resource_metrics["file_descriptors"] = process.num_fds()
                except ImportError:
                    self.logger.warning(
                        "psutil not available, resource metrics will not be included"
                    )

            # Compile results
            results = {
                "name": self.name,
                "category": self.category,
                "description": self.description,
                "tags": self.tags,
                "timestamp": datetime.datetime.now().isoformat(),
                "config": {
                    "iterations": self.config.iterations,
                    "warmup_iterations": self.config.warmup_iterations,
                    "parallel_runs": self.config.parallel_runs,
                },
                "timing": {
                    "total_time": total_time,
                    "avg_time": avg_time,
                    "median_time": median_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "stddev": stddev,
                    "p90": p90,
                    "p95": p95,
                    "p99": p99,
                    "operations_per_second": 1.0 / avg_time if avg_time > 0 else 0,
                },
                "detailed_metrics": iteration_metrics,
                "resource_metrics": resource_metrics,
                "system_info": self._get_system_info(),
            }

            self.logger.info(
                f"Benchmark {self.name} completed in {total_time:.2f}s: "
                f"avg={avg_time:.6f}s, "
                f"median={median_time:.6f}s, "
                f"min={min_time:.6f}s, "
                f"max={max_time:.6f}s, "
                f"p95={p95:.6f}s, "
                f"ops/sec={(1.0 / avg_time) if avg_time > 0 else 0:.2f}"
            )

            return results

        finally:
            # Ensure cleanup
            await self.teardown()

    def _get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.

        Returns:
            Dictionary of system information
        """
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "cpu_count": os.cpu_count(),
            "hostname": platform.node(),
        }

        # Add more system info if available
        try:
            import psutil

            info["total_memory"] = psutil.virtual_memory().total
            info["cpu_freq"] = psutil.cpu_freq().current if psutil.cpu_freq() else None
        except ImportError:
            pass

        return info


class BenchmarkRegistry:
    """Registry for benchmarks."""

    _benchmarks: Dict[str, Type[Benchmark]] = {}

    @classmethod
    def register(cls, benchmark_class: Type[Benchmark]) -> Type[Benchmark]:
        """
        Register a benchmark class.

        Args:
            benchmark_class: The benchmark class to register

        Returns:
            The registered benchmark class
        """
        key = f"{benchmark_class.category}.{benchmark_class.name}"
        cls._benchmarks[key] = benchmark_class
        return benchmark_class

    @classmethod
    def get_all_benchmarks(cls) -> Dict[str, Type[Benchmark]]:
        """
        Get all registered benchmarks.

        Returns:
            Dictionary of benchmark classes
        """
        return cls._benchmarks

    @classmethod
    def get_benchmarks_by_category(cls, category: str) -> Dict[str, Type[Benchmark]]:
        """
        Get registered benchmarks by category.

        Args:
            category: Category to filter by

        Returns:
            Dictionary of benchmark classes in the category
        """
        return {
            name: benchmark_class
            for name, benchmark_class in cls._benchmarks.items()
            if benchmark_class.category == category
        }

    @classmethod
    def get_benchmark(cls, fullname: str) -> Optional[Type[Benchmark]]:
        """
        Get a benchmark by its full name (category.name).

        Args:
            fullname: Full name of the benchmark

        Returns:
            The benchmark class, or None if not found
        """
        return cls._benchmarks.get(fullname)

    @classmethod
    def get_categories(cls) -> list[str]:
        """
        Get all benchmark categories.

        Returns:
            List of unique categories
        """
        return sorted(
            list(
                set(
                    benchmark_class.category
                    for benchmark_class in cls._benchmarks.values()
                )
            )
        )


def register_benchmark(cls: Type[Benchmark]) -> Type[Benchmark]:
    """
    Decorator to register a benchmark class.

    Args:
        cls: The benchmark class to register

    Returns:
        The registered benchmark class
    """
    return BenchmarkRegistry.register(cls)


class BenchmarkRunner:
    """Runner for benchmarks."""

    def __init__(self, config: BenchmarkConfig):
        """
        Initialize the benchmark runner.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.logger = get_logger("benchmark.runner")
        self.results: Dict[str, BenchmarkResult] = {}

    async def run_all(self) -> Dict[str, BenchmarkResult]:
        """
        Run all registered benchmarks.

        Returns:
            Dictionary of benchmark results
        """
        benchmarks = BenchmarkRegistry.get_all_benchmarks()

        # Filter by category if specified
        if self.config.categories_to_run:
            benchmarks = {
                name: benchmark
                for name, benchmark in benchmarks.items()
                if benchmark.category in self.config.categories_to_run
            }

        # Filter by name if specified
        if self.config.benchmarks_to_run:
            benchmarks = {
                name: benchmark
                for name, benchmark in benchmarks.items()
                if name in self.config.benchmarks_to_run
                or benchmark.name in self.config.benchmarks_to_run
            }

        if not benchmarks:
            self.logger.warning("No benchmarks found to run")
            return {}

        self.logger.info(f"Running {len(benchmarks)} benchmarks")

        # Run each benchmark
        for name, benchmark_class in benchmarks.items():
            self.logger.info(f"Running benchmark: {name}")

            try:
                # Create and run the benchmark
                benchmark = benchmark_class(self.config)
                result = await benchmark.run()

                # Store results
                self.results[name] = result

                # Save individual result if configured
                if self.config.save_results:
                    result_file = os.path.join(
                        self.config.results_dir,
                        f"{name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json",
                    )
                    with open(result_file, "w") as f:
                        json.dump(result, f, indent=2)

                    self.logger.info(f"Saved benchmark result to {result_file}")

            except Exception as e:
                self.logger.error(f"Error running benchmark {name}: {e}")
                traceback.print_exc()

        # Save summary results if configured
        if self.config.save_results:
            summary_file = os.path.join(
                self.config.results_dir,
                f"summary_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json",
            )

            # Create a reduced-size summary
            summary = {}
            for name, result in self.results.items():
                # Copy only the essential information, not detailed metrics
                summary[name] = {
                    "name": result["name"],
                    "category": result["category"],
                    "description": result["description"],
                    "timestamp": result["timestamp"],
                    "timing": result["timing"],
                    "resource_metrics": result.get("resource_metrics", {}),
                }

            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)

            self.logger.info(f"Saved benchmark summary to {summary_file}")

        return self.results


async def discover_benchmarks(directory: str) -> list[str]:
    """
    Discover benchmark modules in a directory.

    Args:
        directory: Directory to search for benchmark modules

    Returns:
        List of discovered benchmark module files
    """
    logger = get_logger("benchmark.discovery")
    logger.info(f"Discovering benchmarks in {directory}")

    benchmark_files = []

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("bench_") and file.endswith(".py"):
                # This looks like a benchmark file
                file_path = os.path.join(root, file)
                benchmark_files.append(file_path)

    logger.info(f"Discovered {len(benchmark_files)} benchmark files")
    return benchmark_files


async def load_benchmark_modules(benchmark_files: list[str]) -> None:
    """
    Load benchmark modules from files.

    Args:
        benchmark_files: List of benchmark module files to load
    """
    logger = get_logger("benchmark.loading")

    for file_path in benchmark_files:
        try:
            # Load the module
            module_name = os.path.basename(file_path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(f"Loaded benchmark module: {module_name}")
            else:
                logger.warning(f"Failed to load module spec for {file_path}")
        except Exception as e:
            logger.error(f"Error loading benchmark module {file_path}: {e}")


# Define some core benchmarks


@register_benchmark
class EventCreationBenchmark(Benchmark):
    """Benchmark for event creation."""

    category = "events"
    name = "event_creation"
    description = "Measures the performance of creating event objects"
    tags = ["events", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Import necessary modules
        from uno.core.events import Event

        # Define a test event class
        class TestEvent(Event):
            data: str
            value: int

        self.event_class = TestEvent

    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Create a new event
        event = self.event_class(event_id=str(uuid.uuid4()), data="test data", value=42)

        # Return metrics
        return {"event_id": event.event_id, "event_size": len(event.to_json())}


@register_benchmark
class ErrorHandlingBenchmark(Benchmark):
    """Benchmark for error handling."""

    category = "errors"
    name = "error_creation"
    description = "Measures the performance of creating and handling errors"
    tags = ["errors", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Import necessary modules
        from uno.core.errors import Error, Result

        self.Error = Error
        self.Result = Result

    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Create error and result objects
        error = self.Error(
            message="Test error", error_code="TEST_ERROR", context={"test": "value"}
        )

        result = self.Result.err(error)

        # Check if result is error
        is_error = result.is_error()

        # Unwrap the error
        unwrapped = result.unwrap_error()

        # Return metrics
        return {
            "is_error": is_error,
            "error_code": unwrapped.error_code,
            "has_context": bool(unwrapped.context),
        }


@register_benchmark
class LoggingBenchmark(Benchmark):
    """Benchmark for logging."""

    category = "logging"
    name = "structured_logging"
    description = "Measures the performance of structured logging"
    tags = ["logging", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Import necessary modules
        from uno.core.logging import get_logger

        # Create a test logger
        self.logger = get_logger("benchmark.test")

        # Disable actual logging for the benchmark
        handler = logging.NullHandler()
        self.logger.logger.handlers = [handler]
        self.logger.logger.propagate = False

    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Log messages at different levels
        self.logger.debug("Debug message", extra={"test": "value"})
        self.logger.info("Info message", extra={"test": "value"})
        self.logger.warning("Warning message", extra={"test": "value"})
        self.logger.error("Error message", extra={"test": "value"})

        # Return metrics
        return {"messages_logged": 4}


@register_benchmark
class InMemoryEventStoreBenchmark(Benchmark):
    """Benchmark for the in-memory event store."""

    category = "events"
    name = "in_memory_event_store"
    description = "Measures the performance of the in-memory event store"
    tags = ["events", "event_store", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Import necessary modules
        from uno.core.events import Event, InMemoryEventStore

        # Define a test event class
        class TestEvent(Event):
            data: str
            value: int

        self.event_class = TestEvent

        # Create an event store
        self.event_store = InMemoryEventStore()

        # Create some test events
        self.test_events = [
            self.event_class(
                event_id=str(uuid.uuid4()),
                data=f"test data {i}",
                value=i,
                aggregate_id="test-aggregate",
                aggregate_type="TestAggregate",
            )
            for i in range(10)
        ]

    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Store events
        version = await self.event_store.append_events(self.test_events)

        # Get events
        events = await self.event_store.get_events_by_aggregate("test-aggregate")

        # Return metrics
        return {
            "events_stored": len(self.test_events),
            "events_retrieved": len(events),
            "aggregate_version": version,
        }


@register_benchmark
class UnitOfWorkBenchmark(Benchmark):
    """Benchmark for the unit of work pattern."""

    category = "uow"
    name = "in_memory_uow"
    description = "Measures the performance of the in-memory unit of work"
    tags = ["uow", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Import necessary modules
        from uno.core.uow import InMemoryUnitOfWork

        # Create a unit of work
        self.uow = InMemoryUnitOfWork()

    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Start time
        start = time.perf_counter()

        # Use the unit of work
        async with self.uow:
            # Simulate some work
            await asyncio.sleep(0.001)

        # End time
        duration = time.perf_counter() - start

        # Return metrics
        return {"transaction_duration": duration}


async def main() -> None:
    """Run the benchmark runner."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UNO Core Benchmarks")
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations for each benchmark",
    )
    parser.add_argument(
        "--warmup", type=int, default=10, help="Number of warmup iterations"
    )
    parser.add_argument(
        "--parallel", type=int, default=1, help="Number of parallel benchmark runs"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Timeout in seconds for each benchmark",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save results to disk"
    )
    parser.add_argument(
        "--results-dir", type=str, default=None, help="Directory to save results to"
    )
    parser.add_argument(
        "--no-resource-metrics",
        action="store_true",
        help="Don't include resource usage metrics",
    )
    parser.add_argument(
        "--benchmark",
        action="append",
        dest="benchmarks",
        help="Specific benchmark to run (can be specified multiple times)",
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="Specific category to run (can be specified multiple times)",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover and run all benchmarks in the current directory",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available benchmarks and exit"
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")

    args = parser.parse_args()

    # Configure logging
    configure_logging()
    logger = get_logger("benchmark")

    # Create benchmark config
    config = BenchmarkConfig(
        iterations=args.iterations,
        warmup_iterations=args.warmup,
        parallel_runs=args.parallel,
        timeout=args.timeout,
        save_results=not args.no_save,
        results_dir=args.results_dir,
        include_resource_metrics=not args.no_resource_metrics,
        benchmarks_to_run=args.benchmarks,
        categories_to_run=args.categories,
        verbose=args.verbose,
    )

    # Discover benchmarks if requested
    if args.discover:
        logger.info("Discovering benchmarks")
        benchmark_files = await discover_benchmarks(".")
        await load_benchmark_modules(benchmark_files)

    # List benchmarks if requested
    if args.list:
        logger.info("Available benchmarks:")
        for category in BenchmarkRegistry.get_categories():
            logger.info(f"  Category: {category}")
            for name, benchmark_class in BenchmarkRegistry.get_benchmarks_by_category(
                category
            ).items():
                logger.info(f"    {name}: {benchmark_class.description}")
        return

    # Create and run the benchmark runner
    runner = BenchmarkRunner(config)
    results = await runner.run_all()

    # Print summary
    if results:
        logger.info("Benchmark Summary:")
        for name, result in results.items():
            timing = result["timing"]
            logger.info(f"  {name}:")
            logger.info(f"    Avg: {timing['avg_time']:.6f}s")
            logger.info(f"    Min: {timing['min_time']:.6f}s")
            logger.info(f"    Max: {timing['max_time']:.6f}s")
            logger.info(f"    P95: {timing['p95']:.6f}s")
            logger.info(f"    Ops/sec: {timing['operations_per_second']:.2f}")
    else:
        logger.warning("No benchmark results were produced")


if __name__ == "__main__":
    asyncio.run(main())
