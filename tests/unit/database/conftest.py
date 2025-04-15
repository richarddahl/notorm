"""
Fixtures for database tests.

This module provides fixtures for testing database-related functionality.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection, AsyncSession
from uno.database.db import UnoDBFactory
from uno.database.config import ConnectionConfig


# Mock async context manager
class AsyncMockContextManager:
    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Create a mock model class
class MockModel:
    """Mock for SQLAlchemy model class."""
    
    def __init__(self, tablename="mock_table", schema="public", columns=None, primary_key=None):
        self.__table__ = MagicMock()
        self.__table__.name = tablename
        self.__table__.schema = schema
        self.__table__.columns = MagicMock()
        self.__table__.columns.keys.return_value = columns or ["id", "name", "email"]
        self.__table__.primary_key = MagicMock()
        self.__table__.primary_key.columns = MagicMock()
        if primary_key:
            self.__table__.primary_key.columns.keys.return_value = primary_key
        else:
            self.__table__.primary_key.columns.keys.return_value = ["id"]
        self.__table__.c = MagicMock()


# Create a mock obj class
class MockObj:
    """Mock object that uses the model."""
    
    def __init__(self, model=None):
        self.model = model
        self.filters = {}


@pytest.fixture
def mock_model():
    """Fixture that provides a mock SQLAlchemy model."""
    return MockModel()


@pytest.fixture
def mock_model_with_columns():
    """Fixture that provides a mock SQLAlchemy model with specific columns."""
    def _create_mock_model(tablename="mock_table", schema="public", columns=None, primary_key=None):
        """Create a mock model with the specified parameters."""
        return MockModel(tablename, schema, columns, primary_key)
    
    return _create_mock_model


@pytest.fixture
def mock_obj(mock_model):
    """Fixture that provides a mock UnoObj."""
    obj = MockObj(mock_model)
    return obj


@pytest.fixture
def mock_obj_factory():
    """Fixture that provides a factory for creating mock UnoObj instances."""
    def _create_mock_obj(model=None):
        """Create a mock UnoObj with the specified model."""
        return MockObj(model)
    
    return _create_mock_obj


@pytest.fixture
def db_factory(mock_obj):
    """Fixture that provides a UnoDBFactory with a mock UnoObj."""
    return UnoDBFactory(mock_obj)


@pytest.fixture
def configurable_db_factory():
    """Fixture that provides a factory for creating UnoDBFactory instances with custom UnoObj."""
    def _create_db_factory(obj=None, model=None):
        """Create a UnoDBFactory with the specified UnoObj or model."""
        if obj is None:
            if model is None:
                model = MockModel()
            obj = MockObj(model)
        return UnoDBFactory(obj)
    
    return _create_db_factory


@pytest.fixture
def mock_session():
    """Fixture that provides a mock SQLAlchemy session."""
    session = AsyncMock()
    # Configure method mocks with appropriate return values
    session.execute.return_value = AsyncMock()
    session.execute.return_value.scalar.return_value = None
    session.execute.return_value.scalars.return_value.all.return_value = []
    session.add.return_value = None
    session.flush.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def mock_session_cm(mock_session):
    """Fixture that provides a mock SQLAlchemy session as a context manager."""
    return AsyncMockContextManager(mock_session)


@pytest.fixture
def mock_connection_config():
    """Fixture that provides a mock ConnectionConfig."""
    return ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        db_port=5432,
        db_user_pw="test_password",
        db_driver="postgresql+psycopg2",
        db_schema="public"
    )


@pytest.fixture
def mock_connection():
    """Fixture that provides a mock database connection."""
    connection = MagicMock()
    cursor = MagicMock()
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    connection.cursor.return_value = cursor_cm
    connection_cm = MagicMock()
    connection_cm.__enter__.return_value = connection
    return connection_cm


@pytest.fixture
def mock_async_connection():
    """Fixture that provides a mock async database connection."""
    connection = AsyncMock()
    cursor = AsyncMock()
    connection.cursor.return_value = AsyncMockContextManager(cursor)
    # Add SQLAlchemy AsyncConnection attributes
    connection.execution_options = AsyncMock(return_value=None)
    connection.close = AsyncMock()
    connection.begin = AsyncMock()
    connection.commit = AsyncMock()
    connection.rollback = AsyncMock()
    connection.engine = MagicMock()
    return AsyncMockContextManager(connection)


@pytest.fixture
def mock_async_utils():
    """Mock the async_utils module components for testing."""
    with patch("uno.core.async_utils.TaskGroup") as mock_task_group, \
         patch("uno.core.async_utils.AsyncLock") as mock_async_lock, \
         patch("uno.core.async_utils.Limiter") as mock_limiter, \
         patch("uno.core.async_utils.AsyncContextGroup") as mock_context_group, \
         patch("uno.core.async_utils.AsyncExitStack") as mock_exit_stack, \
         patch("uno.core.async_utils.timeout") as mock_timeout:
        
        # Configure the mocks
        mock_task_group.return_value = AsyncMock()
        mock_async_lock.return_value = AsyncMock()
        mock_limiter.return_value = AsyncMock()
        mock_context_group.return_value = AsyncMock()
        mock_exit_stack.return_value = AsyncMock()
        
        yield {
            "TaskGroup": mock_task_group,
            "AsyncLock": mock_async_lock,
            "Limiter": mock_limiter,
            "AsyncContextGroup": mock_context_group,
            "AsyncExitStack": mock_exit_stack,
            "timeout": mock_timeout,
        }

@pytest.fixture
def mock_engine_factory():
    """Mock the AsyncEngineFactory for testing."""
    mock_factory = MagicMock()
    mock_factory.create_engine.return_value = AsyncMock(spec=AsyncEngine)
    mock_factory.get_connection_lock.return_value = AsyncMock()
    mock_factory.connection_limiter = AsyncMock()
    mock_factory.execute_callbacks = AsyncMock()
    
    return mock_factory

@pytest.fixture
def mock_sqlalchemy_async_connection():
    """Mock a SQLAlchemy AsyncConnection for testing."""
    mock_conn = AsyncMock(spec=AsyncConnection)
    mock_conn.execution_options = AsyncMock(return_value=None)
    mock_conn.close = AsyncMock()
    mock_conn.begin = AsyncMock()
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()
    mock_conn.__aenter__.return_value = mock_conn
    
    return mock_conn

@pytest.fixture
def mock_async_engine():
    """Mock an AsyncEngine for testing."""
    mock_engine = AsyncMock(spec=AsyncEngine)
    mock_engine.connect = AsyncMock()
    mock_engine.dispose = AsyncMock()
    
    return mock_engine