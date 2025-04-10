# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the API endpoint factory module.

These tests verify the functionality of the UnoEndpointFactory class, ensuring
it correctly creates FastAPI endpoints for UnoObj models.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any, Optional, ClassVar

from fastapi import FastAPI, status
from pydantic import BaseModel, ConfigDict, Field

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.api.endpoint import (
    CreateEndpoint,
    ViewEndpoint, 
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)
from uno.schema.schema_manager import UnoSchemaManager
from uno.schema.schema import UnoSchema


class MockSchema(BaseModel):
    """Mock schema for testing."""
    id: str = ""
    name: str = ""


class ModelBase(BaseModel):
    """Base model class for testing."""
    display_name: ClassVar[str] = "Mock Model"
    display_name_plural: ClassVar[str] = "Mock Models"
    
    @classmethod
    def get(cls, id: str):
        """Mock get method."""
        return None
    
    @classmethod
    async def filter(cls, filters=None):
        """Mock filter method."""
        return []
    
    @classmethod
    async def save(cls, body, importing=False):
        """Mock save method."""
        return None
    
    @classmethod
    async def delete_(cls, id):
        """Mock delete method."""
        return True
    
    @classmethod
    def create_filter_params(cls):
        """Mock create_filter_params method."""
        return None
    
    @classmethod
    def validate_filter_params(cls, params):
        """Mock validate_filter_params method."""
        return {}


class TestUnoEndpointFactory:
    """Tests for the UnoEndpointFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = UnoEndpointFactory()
        self.app = MagicMock(spec=FastAPI)
        
        # Create a real model class that inherits from BaseModel
        class MockModel(ModelBase):
            """Mock model for testing."""
            __name__: ClassVar[str] = "MockModel"
            model_config = ConfigDict(arbitrary_types_allowed=True)
            schema_manager: ClassVar[UnoSchemaManager] = UnoSchemaManager()
            
            @classmethod
            def get_schema(cls, schema_name):
                """Mock get_schema method."""
                return MockSchema
        
        # Set up the schema manager with test schemas
        self.model_cls = MockModel
        MockModel.schema_manager.schemas = {
            "view_schema": MockSchema,
            "edit_schema": MockSchema
        }
    
    def test_initialization(self):
        """Test initialization of the endpoint factory."""
        factory = UnoEndpointFactory()
        
        # Verify ENDPOINT_TYPES mapping is correct
        assert factory.ENDPOINT_TYPES["Create"] == CreateEndpoint
        assert factory.ENDPOINT_TYPES["View"] == ViewEndpoint
        assert factory.ENDPOINT_TYPES["List"] == ListEndpoint
        assert factory.ENDPOINT_TYPES["Update"] == UpdateEndpoint
        assert factory.ENDPOINT_TYPES["Delete"] == DeleteEndpoint
        assert factory.ENDPOINT_TYPES["Import"] == ImportEndpoint
    
    @patch("uno.api.endpoint_factory.CreateEndpoint.__init__", return_value=None)
    @patch("uno.api.endpoint_factory.CreateEndpoint.__call__", return_value=None)
    def test_create_single_endpoint(self, mock_call, mock_init):
        """Test creating a single endpoint."""
        # Create only one endpoint type
        self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["Create"]
        )
        
        # Verify only CreateEndpoint was instantiated
        mock_init.assert_called_once_with(
            model=self.model_cls,
            app=self.app,
        )
    
    @patch("uno.api.endpoint_factory.ViewEndpoint.__init__", return_value=None)
    @patch("uno.api.endpoint_factory.ListEndpoint.__init__", return_value=None)
    @patch("uno.api.endpoint_factory.ViewEndpoint.__call__", return_value=None)
    @patch("uno.api.endpoint_factory.ListEndpoint.__call__", return_value=None)
    def test_create_multiple_endpoints(self, mock_list_call, mock_view_call, mock_list_init, mock_view_init):
        """Test creating multiple endpoints."""
        # Create multiple endpoint types
        self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["View", "List"]
        )
        
        # Verify both endpoints were instantiated
        mock_view_init.assert_called_once_with(
            model=self.model_cls,
            app=self.app,
        )
        mock_list_init.assert_called_once_with(
            model=self.model_cls,
            app=self.app,
        )
    
    def test_create_endpoints_empty_list(self):
        """Test creating endpoints with an empty list."""
        # Attempt to create endpoints with an empty list
        with patch.object(self.factory, 'ENDPOINT_TYPES') as mock_types:
            # Should return early if endpoints list is empty
            self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls,
                endpoints=[]
            )
            
            # Verify no endpoint classes were instantiated
            assert not mock_types.__getitem__.called
    
    @patch("uno.api.endpoint_factory.CreateEndpoint.__init__", return_value=None)
    @patch("uno.api.endpoint_factory.CreateEndpoint.__call__", return_value=None)
    def test_create_endpoints_invalid_type(self, mock_call, mock_init):
        """Test creating an invalid endpoint type."""
        # Try to create an invalid endpoint type
        self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["Create", "InvalidType"]
        )
        
        # Verify only valid endpoint was created
        mock_init.assert_called_once()
    
    def test_endpoint_class_registry(self):
        """Test that endpoint class registry contains all expected endpoint types."""
        # Verify endpoint mapping has expected classes
        assert set(self.factory.ENDPOINT_TYPES.keys()) == {
            "Create", "View", "List", "Update", "Delete", "Import"
        }
        
        # Verify endpoint classes are mapped correctly
        assert self.factory.ENDPOINT_TYPES["Create"] == CreateEndpoint
        assert self.factory.ENDPOINT_TYPES["View"] == ViewEndpoint
        assert self.factory.ENDPOINT_TYPES["List"] == ListEndpoint
        assert self.factory.ENDPOINT_TYPES["Update"] == UpdateEndpoint
        assert self.factory.ENDPOINT_TYPES["Delete"] == DeleteEndpoint
        assert self.factory.ENDPOINT_TYPES["Import"] == ImportEndpoint