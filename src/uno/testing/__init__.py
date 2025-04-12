"""
Uno Testing Framework.

This module provides a comprehensive testing framework for Uno applications,
including utilities for property-based testing, integration testing with
containerized dependencies, snapshot testing, and performance regression testing.
"""

from uno.testing.property_based import (
    UnoStrategy, 
    ModelStrategy, 
    SQLStrategy,
    register_custom_strategy,
    given_model,
    given_sql,
)
from uno.testing.integration import IntegrationTestHarness
from uno.testing.snapshot import snapshot_test, compare_snapshot
from uno.testing.performance import PerformanceTest, benchmark

__version__ = "0.1.0"

__all__ = [
    "UnoStrategy",
    "ModelStrategy",
    "SQLStrategy",
    "register_custom_strategy",
    "given_model",
    "given_sql",
    "IntegrationTestHarness",
    "snapshot_test",
    "compare_snapshot",
    "PerformanceTest",
    "benchmark",
]