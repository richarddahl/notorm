"""
Uno Testing Framework.

This module provides a comprehensive testing framework for Uno applications,
including utilities for property-based testing, integration testing with
containerized dependencies, mock data generation, snapshot testing, and
performance regression testing.
"""

# Property-based testing
from uno.testing.property_based.framework import (
    PropertyTest,
    ModelPropertyTest,
    SQLPropertyTest,
    UnoStrategy,
    ModelStrategy,
    SQLStrategy,
    register_custom_strategy,
    forall,
    assume,
    note,
    event,
    stateful_test,
)
from uno.testing.property_based import (
    given_model,
    given_sql,
)

# Integration testing
from uno.testing.integration import (
    IntegrationTestHarness,
    TestEnvironment,
    DatabaseTestService,
    ApiTestService,
    db_session,
    test_database,
    test_app,
    test_client,
)

# Mock data generation
from uno.testing.mock_data.generators import (
    MockDataGenerator,
    RandomGenerator,
    RealisticGenerator,
    SchemaBasedGenerator,
    ModelDataGenerator,
)

# Snapshot testing
from uno.testing.snapshot import (
    snapshot_test,
    compare_snapshot,
    update_snapshot,
    SnapshotManager,
)

# Performance testing
from uno.testing.performance import (
    PerformanceTest,
    benchmark,
    PerformanceMetrics,
    performance_test,
)

__version__ = "0.2.0"

__all__ = [
    # Property-based testing
    "PropertyTest",
    "ModelPropertyTest",
    "SQLPropertyTest",
    "UnoStrategy",
    "ModelStrategy",
    "SQLStrategy",
    "register_custom_strategy",
    "forall",
    "assume",
    "note",
    "event",
    "stateful_test",
    "given_model",
    "given_sql",
    # Integration testing
    "IntegrationTestHarness",
    "TestEnvironment",
    "DatabaseTestService",
    "ApiTestService",
    "db_session",
    "test_database",
    "test_app",
    "test_client",
    # Mock data generation
    "MockDataGenerator",
    "RandomGenerator",
    "RealisticGenerator",
    "SchemaBasedGenerator",
    "ModelDataGenerator",
    # Snapshot testing
    "snapshot_test",
    "compare_snapshot",
    "update_snapshot",
    "SnapshotManager",
    # Performance testing
    "PerformanceTest",
    "benchmark",
    "PerformanceMetrics",
    "performance_test",
]
