# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Test fixtures for integration testing with Uno applications.

This module provides pytest fixtures for integration testing that handle
common setup and teardown operations for databases, API clients, and other
components used in integration tests.
"""

import asyncio
import os
import uuid
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Generator, Optional, Type, Union

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.db_manager import DBManager
from uno.database.engine import AsyncEngine, create_async_engine
from uno.database.session import get_session


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_env_vars():
    """
    Context manager for setting temporary environment variables.
    
    Example:
        ```python
        def test_with_custom_env(temp_env_vars):
            with temp_env_vars({"UNO_DATABASE_URL": "postgresql://test:test@localhost/test"}):
                # Environment variables are set
                assert os.environ["UNO_DATABASE_URL"] == "postgresql://test:test@localhost/test"
            # Environment variables are restored
        ```
    """
    original_values = {}
    
    @contextmanager
    def set_env(**kwargs):
        # Save original values and set new ones
        for key, value in kwargs.items():
            if key in os.environ:
                original_values[key] = os.environ[key]
            os.environ[key] = value
        
        try:
            yield
        finally:
            # Restore original values
            for key in kwargs:
                if key in original_values:
                    os.environ[key] = original_values[key]
                else:
                    del os.environ[key]
    
    return set_env


@pytest.fixture(scope="session")
def test_database_url(request):
    """Get the database URL for testing."""
    # First try to get from pytest config
    db_url = request.config.getoption("--database-url", default=None)
    
    # Next try environment
    if not db_url:
        db_url = os.environ.get("UNO_TEST_DATABASE_URL", "postgresql+asyncpg://uno_test:uno_test@localhost:5432/uno_test_db")
    
    return db_url


@pytest.fixture(scope="function")
def test_database(test_database_url):
    """
    Create a temporary test database for each test.
    
    This fixture creates a new schema in the test database for each test,
    ensuring test isolation and preventing test interference.
    
    Returns:
        A dictionary with database connection information
    """
    # Generate a unique schema name for this test
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    
    # Create a dedicated URL with the schema
    test_url = f"{test_database_url}?options=-c%20search_path%3D{schema_name}"
    
    # Create a synchronous connection to setup the schema
    import psycopg
    
    # Extract connection parameters from the URL
    from urllib.parse import urlparse
    parsed = urlparse(test_database_url)
    dbname = parsed.path.lstrip('/')
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    
    with psycopg.connect(f"dbname={dbname} user={user} password={password} host={host} port={port}") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            # Create the schema
            cur.execute(f"CREATE SCHEMA {schema_name}")
            
            # Apply any required base migrations or setup
            # Here we could apply base schema migrations required for tests
            pass
    
    # Return the connection info
    db_info = {
        "url": test_url,
        "schema": schema_name,
        "base_url": test_database_url,
    }
    
    yield db_info
    
    # Cleanup: Drop the schema
    with psycopg.connect(f"dbname={dbname} user={user} password={password} host={host} port={port}") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"DROP SCHEMA {schema_name} CASCADE")


@pytest_asyncio.fixture
async def db_session(test_database):
    """
    Fixture that provides a database session for tests.
    
    This fixture creates an AsyncSession that is committed at the end of the test,
    and connected to the per-test schema created by the test_database fixture.
    
    Returns:
        An AsyncSession for database operations
    """
    # Create an engine with the test URL
    engine = create_async_engine(test_database["url"])
    
    # Create a session
    async with get_session(engine) as session:
        # Set up the schema with any required objects
        # Here we would execute SQL setup code needed for specific tests
        
        yield session


@pytest.fixture
def test_app() -> FastAPI:
    """
    Create a FastAPI application for testing.
    
    Returns:
        A FastAPI application configured for testing
    """
    from fastapi import FastAPI
    
    app = FastAPI(title="Test App", debug=True)
    
    # Add any middleware, routes, or dependencies required for testing
    
    return app


@pytest.fixture
def test_client(test_app) -> TestClient:
    """
    Create a test client for the FastAPI application.
    
    Returns:
        A TestClient for making HTTP requests to the test app
    """
    return TestClient(test_app)


@pytest.fixture
def api_auth_headers() -> Dict[str, str]:
    """
    Generate authentication headers for API testing.
    
    This fixture creates authentication headers that can be used
    in requests to authenticated API endpoints.
    
    Returns:
        A dictionary of authentication headers
    """
    # Generate a test JWT or other auth token
    auth_token = "test_token"
    
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }