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
    
    def test_create_single_endpoint(self):
        """Test creating a single endpoint."""
        # Mock the CreateEndpoint class with a MagicMock
        original_endpoint = self.factory.ENDPOINT_TYPES["Create"]
        try:
            # Replace with a MagicMock that returns a mock instance
            mock_instance = MagicMock()
            mock_endpoint_class = MagicMock(return_value=mock_instance)
            self.factory.ENDPOINT_TYPES["Create"] = mock_endpoint_class
            
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
        finally:
            # Restore the original class
            self.factory.ENDPOINT_TYPES["Create"] = original_endpoint
    
    def test_create_multiple_endpoints(self):
        """Test creating multiple endpoints."""
        # Save original endpoint classes
        original_view_endpoint = self.factory.ENDPOINT_TYPES["View"]
        original_list_endpoint = self.factory.ENDPOINT_TYPES["List"]
        
        try:
            # Create mock instances
            mock_view_instance = MagicMock()
            mock_list_instance = MagicMock()
            
            # Create mock classes
            mock_view_class = MagicMock(return_value=mock_view_instance)
            mock_list_class = MagicMock(return_value=mock_list_instance)
            
            # Replace endpoint classes with mocks
            self.factory.ENDPOINT_TYPES["View"] = mock_view_class
            self.factory.ENDPOINT_TYPES["List"] = mock_list_class
            
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
        finally:
            # Restore original classes
            self.factory.ENDPOINT_TYPES["View"] = original_view_endpoint
            self.factory.ENDPOINT_TYPES["List"] = original_list_endpoint
    
    def test_create_endpoints_with_defaults(self):
        """Test creating endpoints with default values."""
        # Save original endpoint classes
        original_endpoints = {}
        default_endpoint_types = ["Create", "View", "List", "Update", "Delete"]
        for endpoint_type in default_endpoint_types:
            original_endpoints[endpoint_type] = self.factory.ENDPOINT_TYPES[endpoint_type]
        
        try:
            # Create mock instances for each endpoint type
            mock_instances = {}
            for endpoint_type in default_endpoint_types:
                mock_instances[endpoint_type] = MagicMock()
                self.factory.ENDPOINT_TYPES[endpoint_type] = MagicMock(
                    return_value=mock_instances[endpoint_type]
                )
            
            # Create endpoints with default values
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls
            )
            
            # Verify all default endpoints were created
            assert set(endpoints.keys()) == set(default_endpoint_types)
            
            # Verify each mock was called correctly
            for endpoint_type in default_endpoint_types:
                assert self.factory.ENDPOINT_TYPES[endpoint_type].call_count > 0
                assert endpoints[endpoint_type] == mock_instances[endpoint_type]
        finally:
            # Restore original classes
            for endpoint_type, original_class in original_endpoints.items():
                self.factory.ENDPOINT_TYPES[endpoint_type] = original_class
    
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
    
    def test_create_endpoints_invalid_type(self):
        """Test creating an invalid endpoint type."""
        # Save original endpoint class
        original_endpoint = self.factory.ENDPOINT_TYPES["Create"]
        
        try:
            # Create a mock logger
            with patch("uno.api.endpoint_factory.logger") as mock_logger:
                # Create mock instance
                mock_create_instance = MagicMock()
                mock_create_endpoint = MagicMock(return_value=mock_create_instance)
                
                # Replace endpoint class with mock
                self.factory.ENDPOINT_TYPES["Create"] = mock_create_endpoint
                
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
        finally:
            # Restore original class
            self.factory.ENDPOINT_TYPES["Create"] = original_endpoint
    
    def test_create_endpoints_with_error(self):
        """Test creating an endpoint that raises an error."""
        # Save original endpoint class
        original_endpoint = self.factory.ENDPOINT_TYPES["Create"]
        
        try:
            # Create a mock logger
            with patch("uno.api.endpoint_factory.logger") as mock_logger:
                # Create mock endpoint class that raises an error
                mock_create_endpoint = MagicMock(side_effect=ValueError("Test error"))
                
                # Replace endpoint class with mock
                self.factory.ENDPOINT_TYPES["Create"] = mock_create_endpoint
                
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
        finally:
            # Restore original class
            self.factory.ENDPOINT_TYPES["Create"] = original_endpoint
    
    def test_create_endpoints_with_router(self):
        """Test creating endpoints with a router."""
        # This test verifies that endpoint creation works with router instead of app
        
        # Save original endpoint class
        original_endpoint = self.factory.ENDPOINT_TYPES["Create"]
        
        try:
            # Create mock instance and class
            mock_instance = MagicMock()
            mock_endpoint_class = MagicMock(return_value=mock_instance)
            
            # Replace endpoint class with mock
            self.factory.ENDPOINT_TYPES["Create"] = mock_endpoint_class
            
            # Create endpoint with router
            endpoints = self.factory.create_endpoints(
                app=None,
                router=self.router,
                model_obj=self.model_cls,
                endpoints=["Create"]
            )
            
            # Verify endpoint was created
            mock_endpoint_class.assert_called_once()
            
            # Verify that endpoint creation was successful
            assert "Create" in endpoints
            assert endpoints["Create"] == mock_instance
            
            # Since we can't directly access kwargs passed to the constructor,
            # we can verify the behavior by examining the endpoint creation function
            with patch.object(self.factory, "_filter_valid_params") as mock_filter:
                # Set up mock to return a simple dictionary
                mock_filter.return_value = {"model": self.model_cls, "app": None, "router": self.router}
                
                # Call create_endpoints again
                self.factory.create_endpoints(
                    app=None,
                    router=self.router,
                    model_obj=self.model_cls,
                    endpoints=["Create"]
                )
                
                # Verify _filter_valid_params was called with expected parameters
                # This should include the router parameter
                call_args = mock_filter.call_args_list[0]
                _, params_dict = call_args[0]
                assert "router" in params_dict
                assert params_dict["router"] == self.router
                assert params_dict["app"] is None
        finally:
            # Restore original class
            self.factory.ENDPOINT_TYPES["Create"] = original_endpoint
    
    def test_create_endpoints_with_path_prefix(self):
        """Test creating endpoints with a path prefix."""
        # Save original endpoint class
        original_endpoint = self.factory.ENDPOINT_TYPES["Create"]
        
        try:
            # Create mock instance and class
            mock_instance = MagicMock()
            mock_endpoint_class = MagicMock(return_value=mock_instance)
            
            # Replace endpoint class with mock
            self.factory.ENDPOINT_TYPES["Create"] = mock_endpoint_class
            
            # Create endpoint with path prefix
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls,
                endpoints=["Create"],
                path_prefix="/api/v2"
            )
            
            # Verify endpoint was created
            mock_endpoint_class.assert_called_once()
            
            # Get all parameters that would be passed after filtering
            endpoint_params = self.factory._filter_valid_params(original_endpoint, {
                "model": self.model_cls,
                "app": self.app,
                "include_in_schema": True,
                "path_prefix": "/api/v2"
            })
            
            # Validate path_prefix is in the parameters
            assert "path_prefix" in endpoint_params
            assert endpoint_params["path_prefix"] == "/api/v2"
            
            # Check that the endpoint was properly added to the result
            assert "Create" in endpoints
            assert endpoints["Create"] == mock_instance
        finally:
            # Restore original class
            self.factory.ENDPOINT_TYPES["Create"] = original_endpoint
    
    def test_create_endpoints_with_status_codes(self):
        """Test creating endpoints with custom status codes."""
        # Save original endpoint class
        original_endpoint = self.factory.ENDPOINT_TYPES["Create"]
        
        try:
            # Create mock instance and class
            mock_instance = MagicMock()
            mock_endpoint_class = MagicMock(return_value=mock_instance)
            
            # Replace endpoint class with mock
            self.factory.ENDPOINT_TYPES["Create"] = mock_endpoint_class
            
            # Create endpoint with custom status code
            endpoints = self.factory.create_endpoints(
                app=self.app,
                model_obj=self.model_cls,
                endpoints=["Create"],
                status_codes={"Create": 201}
            )
            
            # Verify endpoint was created
            mock_endpoint_class.assert_called_once()
            
            # Get all parameters that would be passed after filtering
            endpoint_params = self.factory._filter_valid_params(original_endpoint, {
                "model": self.model_cls,
                "app": self.app,
                "include_in_schema": True,
                "status_code": 201
            })
            
            # Validate status_code is in the parameters
            assert "status_code" in endpoint_params
            assert endpoint_params["status_code"] == 201
            
            # Check that the endpoint was properly added to the result
            assert "Create" in endpoints
            assert endpoints["Create"] == mock_instance
        finally:
            # Restore original class
            self.factory.ENDPOINT_TYPES["Create"] = original_endpoint
    
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
        
        # Generate a unique endpoint type name that's not already registered
        custom_endpoint_name = "Custom"
        counter = 1
        while custom_endpoint_name in self.factory.ENDPOINT_TYPES:
            custom_endpoint_name = f"Custom{counter}"
            counter += 1
        
        # Register a custom endpoint
        self.factory.register_endpoint_type(custom_endpoint_name, CustomEndpoint)
        
        try:
            # Verify updated available endpoints
            available = self.factory.get_available_endpoints()
            assert custom_endpoint_name in available
        finally:
            # Clean up - remove the endpoint type we added
            if custom_endpoint_name in self.factory.ENDPOINT_TYPES:
                del self.factory.ENDPOINT_TYPES[custom_endpoint_name]
    
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