"""
Configuration for integration tests.

This module provides fixtures and configuration for integration tests
that require actual infrastructure components.
"""

import os
import pytest
import asyncio
from typing import Any, Dict, Generator

from uno.database.session import async_session
from uno.dependencies.container import configure_container
from uno.dependencies.provider import ServiceProvider


def pytest_addoption(parser):
    """Add options to control integration tests."""
    parser.addoption(
        "--run-integration", 
        action="store_true", 
        default=False, 
        help="Run integration tests requiring external services"
    )
    parser.addoption(
        "--run-pgvector", 
        action="store_true", 
        default=False, 
        help="Run tests that require pgvector extension"
    )


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as requiring external services"
    )
    config.addinivalue_line(
        "markers", "pgvector: mark test as requiring pgvector extension"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests based on markers unless explicitly requested."""
    # Mark integration tests to skip by default
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    # Mark pgvector tests to skip by default
    if not config.getoption("--run-pgvector"):
        skip_pgvector = pytest.mark.skip(reason="Need --run-pgvector option to run")
        for item in items:
            if "pgvector" in item.keywords:
                item.add_marker(skip_pgvector)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the entire test session."""
    # This allows session-scoped async fixtures
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def check_pgvector():
    """Check if pgvector extension is available and skip if not."""
    try:
        async with async_session() as session:
            result = await session.execute(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
            )
            if result.scalar() == 0:
                pytest.skip("pgvector extension not installed in the database")
    except Exception as e:
        pytest.skip(f"Error checking for pgvector extension: {e}")


@pytest.fixture(scope="session")
def service_provider():
    """Create a service provider for testing."""
    # Configure the container
    configure_container()
    provider = ServiceProvider.get_instance()
    return provider