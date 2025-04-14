# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Pytest configuration for integration tests.

This module provides configuration and fixtures for integration testing
with Uno applications, used by the `uno.testing.integration` package.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import Dict, Any, List, Optional

from uno.testing.integration.harness import IntegrationTestHarness
from uno.testing.integration.services import TestEnvironment


def pytest_addoption(parser):
    """Add command-line options for integration testing."""
    group = parser.getgroup("uno-integration")
    group.addoption(
        "--database-url",
        action="store",
        dest="database_url",
        default=None,
        help="Database URL for integration tests"
    )
    group.addoption(
        "--use-docker",
        action="store_true",
        dest="use_docker",
        default=False,
        help="Use Docker for integration tests"
    )
    group.addoption(
        "--docker-compose-file",
        action="store",
        dest="docker_compose_file",
        default=None,
        help="Docker Compose file for integration tests"
    )
    group.addoption(
        "--skip-cleanup",
        action="store_true",
        dest="skip_cleanup",
        default=False,
        help="Skip cleaning up resources after tests"
    )


# Basic fixtures for integration testing

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def integration_test_config(request):
    """Get configuration for integration tests from command-line options."""
    return {
        "database_url": request.config.getoption("database_url"),
        "use_docker": request.config.getoption("use_docker"),
        "docker_compose_file": request.config.getoption("docker_compose_file"),
        "skip_cleanup": request.config.getoption("skip_cleanup"),
    }


@pytest.fixture(scope="session")
def integration_harness(integration_test_config):
    """Create an integration test harness based on configuration."""
    if integration_test_config["use_docker"]:
        # Configure with Docker services
        if integration_test_config["docker_compose_file"]:
            # Use Docker Compose file
            harness = IntegrationTestHarness(
                docker_compose_file=integration_test_config["docker_compose_file"]
            )
        else:
            # Use individual services
            harness = IntegrationTestHarness(
                services=[
                    IntegrationTestHarness.get_postgres_config(),
                    # Add other services as needed
                ]
            )
            
        # Start services and yield harness
        with harness.start_services():
            yield harness
            
    else:
        # Use existing services (no Docker)
        harness = IntegrationTestHarness()
        yield harness


# Test data fixtures

@pytest.fixture
def default_test_data() -> Dict[str, List[Dict[str, Any]]]:
    """Get default test data for common test cases."""
    return {
        "users": [
            {"username": "testuser1", "email": "user1@example.com", "bio": "Test user 1"},
            {"username": "testuser2", "email": "user2@example.com", "bio": "Test user 2"}
        ],
        "roles": [
            {"name": "admin", "description": "Administrator role"},
            {"name": "user", "description": "Standard user role"}
        ],
        "permissions": [
            {"name": "read", "description": "Read permission"},
            {"name": "write", "description": "Write permission"},
            {"name": "delete", "description": "Delete permission"}
        ]
    }


@pytest.fixture
def create_test_data_file(integration_harness, default_test_data):
    """Create a test data file with the provided data."""
    def _create_data_file(data=None):
        # Use default data if none provided
        test_data = data or default_test_data
        
        # Create a temporary data file
        return integration_harness.with_test_data(test_data)
    
    return _create_data_file


# Environment fixtures

@pytest_asyncio.fixture
async def test_environment(integration_harness):
    """Create a test environment with database and API clients."""
    async with integration_harness.create_test_environment() as env:
        yield env


@pytest_asyncio.fixture
async def test_environment_with_data(test_environment, default_test_data):
    """Create a test environment with pre-loaded test data."""
    # Load the default test data into the database
    for table_name, rows in default_test_data.items():
        # Only load data for tables that exist
        try:
            for row in rows:
                await test_environment.db.insert_test_data(table_name, row)
        except Exception:
            pass  # Skip tables that don't exist
            
    yield test_environment


# Custom fixtures for specific test scenarios

@pytest_asyncio.fixture
async def isolated_test_environment(integration_harness):
    """
    Create an isolated test environment for each test.
    
    This creates a fresh schema with its own tables for each test,
    ensuring complete isolation between tests.
    """
    # Create a unique schema for this test
    import uuid
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    
    # Create a test environment
    async with integration_harness.create_test_environment() as env:
        # Create the schema
        await env.db.execute_sql(f"CREATE SCHEMA {schema_name}")
        
        # Set search path to the new schema
        await env.db.execute_sql(f"SET search_path TO {schema_name}")
        
        yield env
        
        # Drop the schema on cleanup
        if not integration_test_config.get("skip_cleanup"):
            await env.db.execute_sql(f"DROP SCHEMA {schema_name} CASCADE")