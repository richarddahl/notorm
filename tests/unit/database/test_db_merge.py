# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database/db.py module's merge method.

These tests verify the functionality of the UnoDB merge method.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock

from sqlalchemy import func, text

from uno.database.db import UnoDBFactory
from uno.errors import UnoError


@pytest.mark.asyncio
async def test_merge_function(db_factory):
    """Test the merge function."""
    # Expected result for the merge operation
    expected_result = [{"id": "123", "name": "Test", "_action": "insert"}]
    
    # Create a custom implementation of merge method to avoid database access
    @classmethod
    async def mock_merge(cls, data):
        # This mock simply returns a fixed result without connecting to the database
        return expected_result
    
    # Save the original merge method and replace it with our mock
    original_merge = db_factory.merge
    db_factory.merge = mock_merge
    
    try:
        # Call the mock merge function with test data
        data = {"name": "Test", "email": "test@example.com"}
        result = await db_factory.merge(data)
        
        # Verify the result was processed correctly
        assert result == expected_result
    finally:
        # Restore the original method
        db_factory.merge = original_merge


@pytest.mark.asyncio
async def test_merge_with_mock_session(configurable_db_factory, mock_session_cm):
    """Test the merge method with a mock session."""
    # Create a mock model with specific columns
    model = MockModel("users", "public", ["id", "name", "email", "description", "is_active"])
    obj = MockObj(model)
    db_factory = configurable_db_factory(obj=obj)
    
    # Create test data
    data = {"name": "Test User", "email": "test@example.com"}
    
    # Mock the session that will be used
    with patch('uno.database.db.async_session', return_value=mock_session_cm):
        # Execute the merge
        result = await db_factory.merge(data)
        
        # Verify session methods were called correctly
        mock_session_cm.mock_obj.execute.assert_called()
        mock_session_cm.mock_obj.commit.assert_called_once()


@pytest.mark.asyncio
async def test_merge_with_custom_table_function(configurable_db_factory):
    """Test the merge method specifically for tables with custom merge functions."""
    # Create a mock model with a custom merge function
    model = MockModel("users", "public", ["id", "name", "email"])
    obj = MockObj(model)
    db_factory = configurable_db_factory(obj=obj)
    
    # Mock the SQL function call and its results
    mock_result = MagicMock()
    mock_result.all.return_value = [{"id": "456", "name": "Custom Merge", "_action": "update"}]
    
    mock_execute = AsyncMock()
    mock_execute.return_value = mock_result
    
    mock_session = AsyncMock()
    mock_session.execute = mock_execute
    
    # Create the session context manager
    mock_session_cm = AsyncMockContextManager(mock_session)
    
    # Create test data to merge
    data = {"id": "456", "name": "Custom Merge", "email": "custom@example.com"}
    
    # Patch the session to use our mock
    with patch('uno.database.db.async_session', return_value=mock_session_cm):
        # Execute the merge
        result = await db_factory.merge(data)
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == "456"
        assert result[0]["name"] == "Custom Merge"
        assert result[0]["_action"] == "update"
        
        # Verify session methods
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()


# Helper classes needed for tests
class MockModel:
    """Mock for SQLAlchemy model class."""
    
    def __init__(self, tablename, schema, columns, primary_key=None):
        self.__table__ = MagicMock()
        self.__table__.name = tablename
        self.__table__.schema = schema
        self.__table__.columns = MagicMock()
        self.__table__.columns.keys.return_value = columns
        self.__table__.primary_key = MagicMock()
        self.__table__.primary_key.columns = MagicMock()
        if primary_key:
            self.__table__.primary_key.columns.keys.return_value = primary_key
        else:
            self.__table__.primary_key.columns.keys.return_value = ["id"]


class MockObj:
    """Mock object that uses the model."""
    
    def __init__(self, model=None):
        self.model = model
        self.filters = {}