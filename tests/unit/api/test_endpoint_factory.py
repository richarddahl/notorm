# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the API endpoint factory module.

These tests verify the functionality of the UnoEndpointFactory class, ensuring
it correctly creates FastAPI endpoints for domain models.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch, call
from typing import List, Dict, Any, Optional, ClassVar, Set

from fastapi import FastAPI, APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from uno.api.endpoint_factory import (
    UnoEndpointFactory,
    EndpointCreationError
)
from uno.api.endpoint import (
    UnoEndpoint,
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


# Create a custom endpoint for testing
class CustomEndpoint(UnoEndpoint):
    """Custom endpoint for testing."""
    

class TestUnoEndpointFactory:
    """Tests for the UnoEndpointFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = UnoEndpointFactory()
        self.app = MagicMock(spec=FastAPI)
        self.router = MagicMock(spec=APIRouter)
        
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
    
    @patch("uno.api.endpoint_factory.CreateEndpoint")
    def test_create_single_endpoint(self, mock_endpoint_class):
        """Test creating a single endpoint."""
        # Mock the endpoint class
        mock_instance = MagicMock()
        mock_endpoint_class.return_value = mock_instance
        
        # Create only one endpoint type
        endpoints = self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["Create"]
        )
        
        # Verify endpoint creation
        mock_endpoint_class.assert_called_once()
        assert "Create" in endpoints
        assert endpoints["Create"] == mock_instance
    
    @patch("uno.api.endpoint_factory.ViewEndpoint")
    @patch("uno.api.endpoint_factory.ListEndpoint")
    def test_create_multiple_endpoints(self, mock_list_class, mock_view_class):
        """Test creating multiple endpoints."""
        # Mock the endpoint classes
        mock_view_instance = MagicMock()
        mock_list_instance = MagicMock()
        mock_view_class.return_value = mock_view_instance
        mock_list_class.return_value = mock_list_instance
        
        # Create multiple endpoint types
        endpoints = self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["View", "List"]
        )
        
        # Verify endpoint creation
        mock_view_class.assert_called_once()
        mock_list_class.assert_called_once()
        assert "View" in endpoints
        assert "List" in endpoints
        assert endpoints["View"] == mock_view_instance
        assert endpoints["List"] == mock_list_instance
    
    def test_create_endpoints_with_defaults(self):
        """Test creating endpoints with default values."""
        # Mock all endpoint classes
        with patch.multiple(
            "uno.api.endpoint_factory",
            CreateEndpoint=MagicMock(return_value=MagicMock()),
            ViewEndpoint=MagicMock(return_value=MagicMock()),
            ListEndpoint=MagicMock(return_value=MagicMock()),
            UpdateEndpoint=MagicMock(return_value=MagicMock()),
            DeleteEndpoint=MagicMock(return_value=MagicMock())
        ):
            # Create endpoints with default values
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls
            )
            
            # Verify all default endpoints were created
            assert set(endpoints.keys()) == {
                "Create", "View", "List", "Update", "Delete"
            }
    
    def test_create_endpoints_empty_list(self):
        """Test creating endpoints with an empty list."""
        with patch("uno.api.endpoint_factory.logger") as mock_logger:
            # Create endpoints with empty list
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls,
                endpoints=[]
            )
            
            # Verify no endpoints were created
            assert len(endpoints) == 0
            # Verify warning was logged
            mock_logger.info.assert_called_with(
                f"No endpoints specified for {self.model_cls.__name__}, skipping"
            )
    
    @patch("uno.api.endpoint_factory.CreateEndpoint")
    @patch("uno.api.endpoint_factory.logger")
    def test_create_endpoints_invalid_type(self, mock_logger, mock_create_endpoint):
        """Test creating an invalid endpoint type."""
        # Mock the valid endpoint class
        mock_create_instance = MagicMock()
        mock_create_endpoint.return_value = mock_create_instance
        
        # Create endpoints with an invalid type
        endpoints = self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["Create", "InvalidType"]
        )
        
        # Verify only valid endpoint was created
        assert len(endpoints) == 1
        assert "Create" in endpoints
        assert endpoints["Create"] == mock_create_instance
        
        # Verify warning was logged
        mock_logger.warning.assert_called_with(
            "Unknown endpoint type 'InvalidType', skipping"
        )
    
    @patch("uno.api.endpoint_factory.CreateEndpoint")
    @patch("uno.api.endpoint_factory.logger")
    def test_create_endpoints_with_error(self, mock_logger, mock_create_endpoint):
        """Test creating an endpoint that raises an error."""
        # Mock the endpoint class to raise an error
        mock_create_endpoint.side_effect = ValueError("Test error")
        
        # Create endpoint that will fail
        endpoints = self.factory.create_endpoints(
            app=self.app,
            model_obj=self.model_cls,
            endpoints=["Create"]
        )
        
        # Verify no endpoints were created
        assert len(endpoints) == 0
        
        # Verify error was logged
        mock_logger.error.assert_called_with(
            f"Error creating Create endpoint for {self.model_cls.__name__}: Test error"
        )
        mock_logger.warning.assert_called_with(
            f"Created 0/1 endpoints for {self.model_cls.__name__}. Failed endpoints: Create"
        )
    
    def test_create_endpoints_with_router(self):
        """Test creating endpoints with a router."""
        # Mock the endpoint class
        with patch("uno.api.endpoint_factory.CreateEndpoint") as mock_endpoint_class:
            mock_instance = MagicMock()
            mock_endpoint_class.return_value = mock_instance
            
            # Create endpoint with router
            endpoints = self.factory.create_endpoints(
                app=None,
                router=self.router,
                model_obj=self.model_cls,
                endpoints=["Create"]
            )
            
            # Verify endpoint was created with router
            mock_endpoint_class.assert_called_once()
            args, kwargs = mock_endpoint_class.call_args
            assert kwargs["router"] == self.router
            assert "app" not in kwargs or kwargs["app"] is None
            assert "Create" in endpoints
    
    def test_create_endpoints_with_path_prefix(self):
        """Test creating endpoints with a path prefix."""
        # Mock the endpoint class
        with patch("uno.api.endpoint_factory.CreateEndpoint") as mock_endpoint_class:
            mock_instance = MagicMock()
            mock_endpoint_class.return_value = mock_instance
            
            # Create endpoint with path prefix
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls,
                endpoints=["Create"],
                path_prefix="/api/v2"
            )
            
            # Verify endpoint was created with path prefix
            mock_endpoint_class.assert_called_once()
            args, kwargs = mock_endpoint_class.call_args
            assert kwargs["path_prefix"] == "/api/v2"
            assert "Create" in endpoints
    
    def test_create_endpoints_with_status_codes(self):
        """Test creating endpoints with custom status codes."""
        # Mock the endpoint class
        with patch("uno.api.endpoint_factory.CreateEndpoint") as mock_endpoint_class:
            mock_instance = MagicMock()
            mock_endpoint_class.return_value = mock_instance
            
            # Create endpoint with custom status code
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls,
                endpoints=["Create"],
                status_codes={"Create": 201}
            )
            
            # Verify endpoint was created with status code
            mock_endpoint_class.assert_called_once()
            args, kwargs = mock_endpoint_class.call_args
            assert kwargs["status_code"] == 201
            assert "Create" in endpoints
    
    def test_create_endpoints_parameter_filtering(self):
        """Test parameter filtering for endpoint creation."""
        # Create a custom endpoint class that doesn't accept all parameters
        class TestEndpoint(UnoEndpoint):
            def __init__(self, model, app):
                pass
                
        # Register the custom endpoint
        self.factory.ENDPOINT_TYPES["Test"] = TestEndpoint
        
        # Mock the inspect module to return a limited signature
        with patch("uno.api.endpoint_factory.inspect.signature") as mock_signature:
            # Create a mock signature that only accepts model and app
            mock_signature.return_value = MagicMock()
            mock_signature.return_value.parameters = {"self": None, "model": None, "app": None}
            
            # Mock the endpoint class
            with patch.object(TestEndpoint, "__init__", return_value=None) as mock_init:
                # Create endpoint with extra parameters that should be filtered out
                self.factory.create_endpoints(
                    app=self.app,
                    model_obj=self.model_cls,
                    endpoints=["Test"],
                    path_prefix="/api/v2",  # Should be filtered out
                    status_codes={"Test": 201}  # Should be filtered out
                )
                
                # Verify only valid parameters were passed
                mock_init.assert_called_once_with(model=self.model_cls, app=self.app)
    
    def test_get_endpoint_class(self):
        """Test getting an endpoint class."""
        # Get existing endpoint class
        endpoint_class = self.factory.get_endpoint_class("Create")
        assert endpoint_class == CreateEndpoint
        
        # Get nonexistent endpoint class
        endpoint_class = self.factory.get_endpoint_class("Nonexistent")
        assert endpoint_class is None
    
    def test_register_endpoint_type(self):
        """Test registering a custom endpoint type."""
        # Register a custom endpoint type
        self.factory.register_endpoint_type("Custom", CustomEndpoint)
        
        # Verify registration
        assert "Custom" in self.factory.ENDPOINT_TYPES
        assert self.factory.ENDPOINT_TYPES["Custom"] == CustomEndpoint
        
        # Try to register again (should raise ValueError)
        with pytest.raises(ValueError):
            self.factory.register_endpoint_type("Custom", CustomEndpoint)
    
    def test_get_available_endpoints(self):
        """Test getting available endpoint types."""
        # Get available endpoints
        available = self.factory.get_available_endpoints()
        
        # Verify expected endpoints
        assert isinstance(available, set)
        assert "Create" in available
        assert "View" in available
        assert "List" in available
        assert "Update" in available
        assert "Delete" in available
        assert "Import" in available
        
        # Register a custom endpoint
        self.factory.register_endpoint_type("Custom", CustomEndpoint)
        
        # Verify updated available endpoints
        available = self.factory.get_available_endpoints()
        assert "Custom" in available
    
    def test_create_endpoints_invalid_inputs(self):
        """Test creating endpoints with invalid inputs."""
        # Test missing app and router
        with pytest.raises(ValueError, match="Either app or router must be provided"):
            self.factory.create_endpoints(
                app=None,
                router=None,
                model_obj=self.model_cls
            )
        
        # Test missing model
        with pytest.raises(ValueError, match="Model object must be provided"):
            self.factory.create_endpoints(
                app=self.app,
                model_obj=None
            )