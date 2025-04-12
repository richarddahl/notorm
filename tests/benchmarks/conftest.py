"""
Configuration for benchmark tests.

This module provides fixtures and configuration for benchmark tests,
allowing performance measurement under different conditions.
"""

import pytest


def pytest_addoption(parser):
    """Add options to control benchmark tests."""
    parser.addoption(
        "--run-benchmark", 
        action="store_true", 
        default=False, 
        help="Run benchmark tests that measure performance"
    )


def pytest_configure(config):
    """Configure pytest benchmark markers."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )


def pytest_collection_modifyitems(config, items):
    """Skip benchmark tests unless explicitly requested."""
    if not config.getoption("--run-benchmark"):
        skip_benchmarks = pytest.mark.skip(reason="Need --run-benchmark option to run")
        for item in items:
            if "benchmark" in item.keywords:
                item.add_marker(skip_benchmarks)