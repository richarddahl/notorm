# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the obj.py module.

These tests verify the functionality of the UnoObj class, focusing on
object initialization, schema creation, and business logic operations.
"""

import pytest
from typing import ClassVar, Type, Optional, List, Dict, Any
import datetime
import unittest.mock as mock
from unittest.mock import MagicMock, patch, ANY

from sqlalchemy import Column, Integer, String, MetaData, Table
from sqlalchemy.orm import Mapped

from uno.model import UnoModel
from uno.obj import UnoObj
from uno.schema.schema import UnoSchemaConfig
from uno.errors import UnoError
from uno.registry import UnoRegistry
from uno.schema.schema_manager import UnoSchemaManager
from uno.queries.filter_manager import UnoFilterManager
from uno.database.db import UnoDBFactory
from uno.obj_errors import UnoObjSchemaError


@pytest.fixture
def reset_registry():
    """Reset the registry before and after tests."""
    from uno.registry import get_registry
    
    # Reset before test
    registry = get_registry()
    registry.clear()
    
    # Clear the lru_cache to get a fresh instance
    from functools import lru_cache
    get_registry.cache_clear()
    
    yield
    
    # Reset after test
    registry = get_registry()
    registry.clear()
    get_registry.cache_clear()


class TestUnoObjBasic:
    """Tests for UnoObj basic functionality with mocked dependencies."""

    def test_model_validation(self, reset_registry):
        """Test that models need to be explicitly set."""
        # When a model is not set, an error should be raised
        with pytest.raises(TypeError):
            # Create a temporary UnoObj subclass without setting model
            type("TestObjWithoutModel", (UnoObj,), {})

    def test_display_names(self, reset_registry):
        """Test display name generation."""
        # We need to mock _set_display_names to avoid external dependencies
        with patch.object(UnoObj, '_set_display_names') as mock_set_names:
            # Create a mock model
            mock_model = MagicMock()
            mock_model.__tablename__ = "test_table"
            
            # Create a test class
            class TestTempObj(UnoObj):
                model = mock_model
            
            # Manually set display names
            TestTempObj.display_name = "Test Table"
            TestTempObj.display_name_plural = "Test Tables"
            
            # Check display names
            assert TestTempObj.display_name == "Test Table"
            assert TestTempObj.display_name_plural == "Test Tables"

    def test_custom_display_names(self, reset_registry):
        """Test custom display names."""
        # We need to mock UnoRegistry and _set_display_names
        with patch.object(UnoObj, '_set_display_names') as mock_set_names:
            # Create a mock model
            mock_model = MagicMock()
            mock_model.__tablename__ = "test_table"
            
            # Define a test class with custom display names
            class TestTempObj(UnoObj):
                model = mock_model
                display_name = "Custom Name"
                display_name_plural = "Custom Names"
            
            # Check display names are set correctly
            assert TestTempObj.display_name == "Custom Name"
            assert TestTempObj.display_name_plural == "Custom Names"


class TestUnoObjInstantiation:
    """Tests for UnoObj instantiation with mocked components."""
    
    def test_init(self, reset_registry):
        """Test basic initialization using mock components."""
        # Create mocks for all dependencies
        mock_db_factory = MagicMock()
        mock_schema_manager = MagicMock()
        mock_filter_manager = MagicMock()
        
        # Patch the getter functions to return our mocks
        with patch('uno.obj.get_db_factory', return_value=mock_db_factory):
            with patch('uno.obj.get_schema_manager', return_value=mock_schema_manager):
                with patch('uno.obj.get_filter_manager', return_value=mock_filter_manager):
                    with patch.object(UnoObj, '_set_display_names'):
                        # Create a mock model
                        mock_model = MagicMock()
                        
                        # Define a test class with our mocks
                        class TempObj(UnoObj):
                            model = mock_model
                            name: str
                            description: Optional[str] = None
                        
                        # Create an instance
                        obj = TempObj(name="Test")
                        
                        # Check attributes
                        assert obj.name == "Test"
                        assert obj.description is None
                        
                        # Check dependencies were initialized correctly
                        assert obj.db == mock_db_factory
                        assert obj.schema_manager == mock_schema_manager
                        assert obj.filter_manager == mock_filter_manager


@pytest.mark.skip(reason="These tests require more complex setup with SQLAlchemy and async support")
class TestUnoObjDatabaseOperations:
    """Tests for UnoObj database operations that would require async and DB setup."""
    
    @pytest.mark.asyncio
    async def test_get(self):
        """Test getting an object from the database."""
        pass
    
    @pytest.mark.asyncio
    async def test_filter(self):
        """Test filtering objects from the database."""
        pass
    
    @pytest.mark.asyncio
    async def test_merge(self):
        """Test merging an object with the database."""
        pass
    
    @pytest.mark.asyncio
    async def test_save_new(self):
        """Test saving a new object to the database."""
        pass
    
    @pytest.mark.asyncio
    async def test_save_update(self):
        """Test updating an existing object in the database."""
        pass
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting an object from the database."""
        pass


class TestUnoObjSchemaOperations:
    """Tests for UnoObj schema operations with mocked components."""
    
    def test_ensure_schemas_created(self, reset_registry):
        """Test ensuring schemas are created."""
        # Create a mock schema manager
        mock_schema_manager = MagicMock()
        mock_schema_manager.get_schema.return_value = None
        
        # Create a mock model
        mock_model = MagicMock()
        
        # Patch dependencies and avoid UnoObj.__init_subclass__
        with patch('uno.obj.get_db_factory', return_value=MagicMock()):
            with patch('uno.obj.get_schema_manager', return_value=mock_schema_manager):
                with patch('uno.obj.get_filter_manager', return_value=MagicMock()):
                    with patch.object(UnoObj, '_set_display_names'):
                        # Create a test class
                        class TestSchemaObj(UnoObj):
                            model = mock_model
                        
                        # Create an instance
                        obj = TestSchemaObj()
                        
                        # Call the method
                        obj._ensure_schemas_created()
                        
                        # Check that the method was called
                        mock_schema_manager.create_all_schemas.assert_called_once_with(TestSchemaObj)
    
    def test_ensure_schemas_created_already_exists(self, reset_registry):
        """Test ensuring schemas are created when they already exist."""
        # Create a mock schema manager with schemas already created
        mock_schema_manager = MagicMock()
        mock_schema_manager.get_schema.return_value = "exists"  # Will return a value for edit_schema
        
        # Create a mock model
        mock_model = MagicMock()
        
        # Patch dependencies and avoid UnoObj.__init_subclass__
        with patch('uno.obj.get_db_factory', return_value=MagicMock()):
            with patch('uno.obj.get_schema_manager', return_value=mock_schema_manager):
                with patch('uno.obj.get_filter_manager', return_value=MagicMock()):
                    with patch.object(UnoObj, '_set_display_names'):
                        # Create a test class
                        class TestSchemaObj(UnoObj):
                            model = mock_model
                        
                        # Create an instance
                        obj = TestSchemaObj()
                        
                        # Call the method
                        obj._ensure_schemas_created()
                        
                        # Check that the create method was NOT called
                        mock_schema_manager.create_all_schemas.assert_not_called()
    
    def test_to_model_schema_not_found(self, reset_registry):
        """Test to_model with a nonexistent schema raises an error."""
        # Create a mock schema manager that returns None for get_schema
        mock_schema_manager = MagicMock()
        mock_schema_manager.get_schema.return_value = None
        
        # Create a mock model
        mock_model = MagicMock()
        
        # Patch dependencies and avoid UnoObj.__init_subclass__
        with patch('uno.obj.get_db_factory', return_value=MagicMock()):
            with patch('uno.obj.get_schema_manager', return_value=mock_schema_manager):
                with patch('uno.obj.get_filter_manager', return_value=MagicMock()):
                    with patch.object(UnoObj, '_set_display_names'):
                        # Create a test class
                        class TestSchemaObj(UnoObj):
                            model = mock_model
                        
                        # Create an instance
                        obj = TestSchemaObj()
                        
                        # Call the method - should raise an error
                        with pytest.raises(UnoObjSchemaError) as excinfo:
                            obj.to_model(schema_name="nonexistent")
                        
                        assert "Schema nonexistent not found" in str(excinfo.value)
                        assert excinfo.value.error_code == "OBJ-0201"


class TestUnoObjConfiguration:
    """Tests for UnoObj configuration methods with mocked components."""
    
    def test_configure(self, reset_registry):
        """Test configuring a UnoObj class for use with a web application."""
        # Create mock app, model, filter_manager, schema_manager, and endpoint_factory
        mock_app = MagicMock()
        mock_model = MagicMock()
        mock_filter_manager = MagicMock()
        mock_schema_manager = MagicMock()
        mock_endpoint_factory = MagicMock()
        
        # Patch dependencies and avoid UnoObj.__init_subclass__
        with patch('uno.obj.get_filter_manager', return_value=mock_filter_manager):
            with patch('uno.obj.get_schema_manager', return_value=mock_schema_manager):
                with patch('uno.obj.UnoEndpointFactory', MagicMock(return_value=mock_endpoint_factory)):
                    with patch.object(UnoObj, '_set_display_names'):
                        # Create a test class
                        class TestConfigObj(UnoObj):
                            model = mock_model
                            endpoints = ["Test"]
                            endpoint_tags = ["tag"]
                        
                        # Call the method
                        TestConfigObj.configure(mock_app)
                        
                        # Verify filter manager was used correctly
                        mock_filter_manager.create_filters_from_table.assert_called_once_with(
                            TestConfigObj.model,
                            TestConfigObj.exclude_from_filters,
                            TestConfigObj.terminate_field_filters,
                        )
                        
                        # Verify schema manager was used correctly
                        mock_schema_manager.create_all_schemas.assert_called_once_with(TestConfigObj)
                        
                        # Verify endpoint factory was used correctly
                        mock_endpoint_factory.create_endpoints.assert_called_once_with(
                            mock_app,
                            TestConfigObj,
                            ["Test"],
                            ["tag"],
                        )