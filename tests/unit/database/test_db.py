# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database/db.py module.

These tests verify the functionality of the UnoDBFactory and the UnoDB class it generates,
focusing on database operations like create, update, get, and filter.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock, call
from psycopg import sql
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy import UniqueConstraint, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError

from uno.database.db import (
    UnoDBFactory,
    FilterParam,
    NotFoundException,
    IntegrityConflictException
)
from uno.errors import UnoError
from uno.model import UnoModel


# Mock async context manager
class AsyncMockContextManager:
    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Create test models
class MockTable:
    """Mock for SQLAlchemy Table class."""
    
    def __init__(self, name, schema, columns, primary_key=None, constraints=None):
        self.name = name
        self.schema = schema
        self.columns = MagicMock()
        self.columns.keys.return_value = columns
        self.primary_key = MagicMock()
        self.primary_key.columns = MagicMock()
        if primary_key:
            self.primary_key.columns.keys.return_value = primary_key
        else:
            self.primary_key.columns.keys.return_value = ["id"]
        
        # Create columns with unique attributes
        self._columns = []
        for col_name in columns:
            mock_col = MagicMock(name=col_name)
            mock_col.unique = col_name == "email"  # For testing unique constraints
            mock_col.name = col_name
            self._columns.append(mock_col)
            
        # Add columns property as a list
        self.__setattr__("columns", self._columns)
        
        # Create table constraints
        self._constraints = constraints or []


# Create mock model class
class MockModel:
    """Mock for SQLAlchemy model class."""
    
    def __init__(self, tablename, schema, columns, primary_key=None, unique_constraints=None):
        self.__table__ = MockTable(
            tablename, 
            schema, 
            columns, 
            primary_key=primary_key, 
            constraints=unique_constraints
        )
        
        # Set up table_args if unique_constraints are specified
        if unique_constraints:
            self.__table_args__ = unique_constraints
        
        # Add attributes for each column
        for col in columns:
            setattr(self, col, MagicMock())


# Create mock obj class
class MockObj:
    """Mock object that uses the model."""
    
    model = None  # Set in the test functions
    filters = {}

    def __init__(self):
        pass


@pytest.fixture
def mock_model():
    """Return a mock model for testing."""
    columns = ["id", "name", "email", "description", "is_active"]
    model = MockModel("users", "public", columns)
    return model


@pytest.fixture
def mock_obj(mock_model):
    """Return a mock obj for testing."""
    obj = MockObj()
    obj.model = mock_model
    return obj


@pytest.fixture
def db_factory(mock_obj):
    """Return a UnoDBFactory instance with mock obj."""
    return UnoDBFactory(mock_obj)


class TestUnoDBFactory:
    """Tests for the UnoDBFactory function and the class it returns."""
    
    @pytest.mark.asyncio
    async def test_factory_returns_class(self, mock_obj):
        """Test that UnoDBFactory returns a class with the expected attributes."""
        db_cls = UnoDBFactory(mock_obj)
        
        # Check class has the expected properties
        assert db_cls.obj == mock_obj
        assert db_cls.table_name == mock_obj.model.__table__.name
        assert hasattr(db_cls, "table_keys")
        assert hasattr(db_cls, "merge")
        assert hasattr(db_cls, "create")
        assert hasattr(db_cls, "update")
        assert hasattr(db_cls, "get")
        assert hasattr(db_cls, "filter")

    def test_table_keys_finds_primary_key(self, db_factory, mock_model):
        """Test that table_keys returns the primary key columns."""
        # Setup mock with specific primary key
        mock_model.__table__.primary_key.columns.keys.return_value = ["id"]
        
        pk_fields, uq_fields = db_factory.table_keys()
        
        assert pk_fields == ["id"]
        assert isinstance(uq_fields, list)
    
    def test_table_keys_finds_unique_constraints(self, mock_obj):
        """Test that table_keys returns unique constraints."""
        # Create model with a unique constraint
        columns = ["id", "name", "email", "tenant_id"]
        unique_constraints = [UniqueConstraint("name", "tenant_id")]
        model = MockModel("users", "public", columns, unique_constraints=unique_constraints)
        mock_obj.model = model
        
        db_cls = UnoDBFactory(mock_obj)
        
        # Mock the check for unique constraints
        with patch.object(db_cls, "obj", mock_obj):
            pk_fields, uq_fields = db_cls.table_keys()
            
            # Check primary key fields
            assert pk_fields == ["id"]
            
            # We expect one unique constraint on (name, tenant_id)
            assert len(uq_fields) >= 1
            # Email should be detected as a unique column
            assert ["email"] in uq_fields
    
    @pytest.mark.asyncio
    async def test_merge_function(self, db_factory):
        """Test the merge function."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        
        # Use normal MagicMock for set_role since it's not awaited in the code
        set_role_mock = MagicMock()
        mock_session.execute.return_value = set_role_mock
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = [{"id": "123", "name": "Test", "_action": "insert"}]
        mock_session.execute.return_value = mock_result
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            data = {"name": "Test", "email": "test@example.com"}
            
            # Call the merge function
            result = await db_factory.merge(data)
            
            # Verify the session was used correctly
            # Use normal MagicMock for set_role since it's not awaited in the code
            set_role_mock = MagicMock()
            mock_session.execute.side_effect = [set_role_mock, mock_result]
            mock_session.commit.assert_called_once()
            
            # Verify the result was processed correctly
            mock_result.fetchone.assert_called_once()
            assert result == [{"id": "123", "name": "Test", "_action": "insert"}]
    
    @pytest.mark.asyncio
    async def test_create_success(self, db_factory):
        """Test the create function with successful creation."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            schema = MagicMock()
            
            # Call the create function
            result, success = await db_factory.create(schema)
            
            # Use normal MagicMock for set_role since it's not awaited in the code
            set_role_mock = MagicMock()
            mock_session.execute.return_value = set_role_mock
            
            # Verify the session was used correctly
            mock_session.execute.assert_called_once()
            mock_session.add.assert_called_once_with(schema)
            mock_session.commit.assert_called_once()
            
            # Verify the result was processed correctly
            assert result == schema
            assert success is True
    
    @pytest.mark.asyncio
    async def test_create_unique_violation(self, db_factory):
        """Test the create function with a unique violation."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        
        # Use normal MagicMock for set_role since it's not awaited in the code
        set_role_mock = MagicMock()
        mock_session.execute.return_value = set_role_mock
        
        # Make add raise IntegrityError with "duplicate key" message
        mock_session.add.side_effect = IntegrityError(
            "duplicate key value violates unique constraint", 
            None, 
            None
        )
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            schema = MagicMock()
            
            # Call the create function - should raise UniqueViolationError
            with pytest.raises(UniqueViolationError):
                await db_factory.create(schema)
            
            # Verify the session was used
            mock_session.execute.assert_called_once()
            mock_session.add.assert_called_once_with(schema)
            mock_session.commit.assert_not_called()  # Commit should not be called on error
    
    @pytest.mark.asyncio
    async def test_update_success(self, db_factory):
        """Test the update function with successful update."""
        # Mock the get function to return a model
        mock_model_instance = MagicMock()
        
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            with patch.object(db_factory, 'get', AsyncMock(return_value=mock_model_instance)):
                # Call the update function
                result = await db_factory.update(mock_model_instance)
                
                # Verify the session was used correctly
                mock_session.execute.assert_called_once()
                mock_session.add.assert_called_once_with(mock_model_instance)
                mock_session.commit.assert_called_once()
                
                # Verify the result was processed correctly
                assert result == mock_model_instance
    
    @pytest.mark.asyncio
    async def test_get_success(self, db_factory, mock_obj):
        """Test the get function with successful retrieval."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_row = MagicMock()
        mock_row._mapping = {"id": "123", "name": "Test"}
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            # Call the get function
            result = await db_factory.get(id="123")
            
            # Use normal MagicMock for set_role since it's not awaited in the code
            set_role_mock = MagicMock()
            mock_session.execute.side_effect = [set_role_mock, mock_result]
            
            # Verify the result was processed correctly
            assert result == {"id": "123", "name": "Test"}
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, db_factory):
        """Test the get function when the record is not found."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = []
        
        # Use normal MagicMock for set_role since it's not awaited in the code
        set_role_mock = MagicMock()
        mock_session.execute.side_effect = [set_role_mock, mock_result]
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            # Call the get function - should raise NotFoundException
            with pytest.raises(NotFoundException):
                await db_factory.get(id="123")
    
    @pytest.mark.asyncio
    async def test_get_integrity_conflict(self, db_factory):
        """Test the get function when multiple records are found."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_row1 = MagicMock()
        mock_row1._mapping = {"id": "123", "name": "Test1"}
        mock_row2 = MagicMock()
        mock_row2._mapping = {"id": "456", "name": "Test2"}
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        
        # Use normal MagicMock for set_role since it's not awaited in the code
        set_role_mock = MagicMock()
        mock_session.execute.side_effect = [set_role_mock, mock_result]
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            # Call the get function - should raise IntegrityConflictException
            with pytest.raises(IntegrityConflictException):
                await db_factory.get(name="Test")
    
    @pytest.mark.asyncio
    async def test_filter_basic(self, db_factory, mock_obj):
        """Test the filter function with basic filtering."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_mappings = AsyncMock()
        mock_mappings.all.return_value = [
            {"id": "123", "name": "Test1"}, 
            {"id": "456", "name": "Test2"}
        ]
        mock_result.mappings.return_value = mock_mappings
        
        # Use normal MagicMock for set_role since it's not awaited in the code
        set_role_mock = MagicMock()
        mock_session.execute.side_effect = [set_role_mock, mock_result]
        
        # Create mocked filter params
        mock_filter = MagicMock()
        mock_filter.label = "name"
        mock_filter.val = "Test"
        mock_filter.lookup = "contains"
        mock_obj.filters = {"name": MagicMock()}
        mock_obj.filters["name"].cypher_query.return_value = "MATCH (n) WHERE n.name CONTAINS 'Test' RETURN n.id"
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            # Call the filter function
            result = await db_factory.filter([mock_filter])
            
            # Verify the result was processed correctly
            assert result == [
                {"id": "123", "name": "Test1"}, 
                {"id": "456", "name": "Test2"}
            ]
    
    @pytest.mark.asyncio
    async def test_filter_with_paging(self, db_factory, mock_obj):
        """Test the filter function with paging parameters."""
        # Mock the necessary functions and objects
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_mappings = AsyncMock()
        mock_mappings.all.return_value = [{"id": "123", "name": "Test1"}]
        mock_result.mappings.return_value = mock_mappings
        
        # Use normal MagicMock for set_role since it's not awaited in the code
        set_role_mock = MagicMock()
        mock_session.execute.side_effect = [set_role_mock, mock_result]
        
        # Create mocked filter params for paging
        limit_filter = MagicMock()
        limit_filter.label = "limit"
        limit_filter.val = 1
        
        offset_filter = MagicMock()
        offset_filter.label = "offset"
        offset_filter.val = 1
        
        order_by_filter = MagicMock()
        order_by_filter.label = "order_by"
        order_by_filter.val = "name"
        
        # Create async context manager for the session
        mock_async_session = AsyncMockContextManager(mock_session)
        
        # Patch the session and other dependencies
        with patch('uno.database.db.async_session', return_value=mock_async_session):
            # Call the filter function
            result = await db_factory.filter([limit_filter, offset_filter, order_by_filter])
            
            # Verify the result was processed correctly
            assert result == [{"id": "123", "name": "Test1"}]
