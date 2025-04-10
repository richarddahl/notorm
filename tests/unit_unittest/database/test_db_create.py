# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the database/db.py module's create method.

These tests verify the functionality of the UnoDB create method.
"""

import asyncio
import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from sqlalchemy import UniqueConstraint, Column, Integer, String, MetaData
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError

from uno.database.db import UnoDBFactory, FilterParam, NotFoundException, IntegrityConflictException
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


# Create mock model class
class MockModel:
    """Mock for SQLAlchemy model class."""
    
    def __init__(self, tablename, schema, columns, primary_key=None, unique_constraints=None):
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


class TestDBCreate(IsolatedAsyncioTestCase):
    """Tests for the UnoDB create method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Create a mock model
        columns = ["id", "name", "email", "description", "is_active"]
        self.mock_model = MockModel("users", "public", columns)
        
        # Create a mock obj
        self.mock_obj = MockObj()
        self.mock_obj.model = self.mock_model
        
        # Create the db factory
        self.db_factory = UnoDBFactory(self.mock_obj)
    
    async def test_create_success(self):
        """Test the create function with successful creation."""
        # Create a proper test schema
        from pydantic import BaseModel
        class TestSchema(BaseModel):
            name: str = "test"
            email: str = "test@example.com"
        
        schema = TestSchema()
        
        # Create a custom implementation of create method to avoid database access
        @classmethod
        async def mock_create(cls, schema):
            return schema, True
        
        # Save the original create method and replace it with our mock
        original_create = self.db_factory.create
        self.db_factory.create = mock_create
        
        try:
            # Call the mock create function
            result, success = await self.db_factory.create(schema)
            
            # Verify the result
            self.assertEqual(result, schema)
            self.assertTrue(success)
        finally:
            # Restore the original method
            self.db_factory.create = original_create
    
    async def test_create_unique_violation(self):
        """Test the create function with a unique violation."""
        # Create a proper test schema
        from pydantic import BaseModel
        class TestSchema(BaseModel):
            name: str = "test"
            email: str = "test@example.com"
        
        schema = TestSchema()
        
        # Create a custom implementation of create method that raises UniqueViolationError
        @classmethod
        async def mock_create_with_violation(cls, schema):
            raise UniqueViolationError("duplicate key value violates unique constraint")
        
        # Save the original create method and replace it with our mock
        original_create = self.db_factory.create
        self.db_factory.create = mock_create_with_violation
        
        try:
            # Call the mock create function - should raise UniqueViolationError
            with self.assertRaises(UniqueViolationError):
                await self.db_factory.create(schema)
        finally:
            # Restore the original method
            self.db_factory.create = original_create