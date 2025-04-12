"""
Fixtures for database tests.

This module provides fixtures for testing database-related functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

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
    return AsyncMockContextManager(connection)