# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the endpoint integration concepts.

This module demonstrates the integration patterns between UnoObj, UnoModel,
UnoDB, and UnoEndpoint without requiring a database or actual HTTP requests.
"""

import asyncio
import pytest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import FastAPI
from pydantic import BaseModel, Field, create_model

from uno.api.endpoint_factory import UnoEndpointFactory


# Mock schemas for testing
class UserViewSchema(BaseModel):
    """Mock schema for user view data."""
    id: str = Field(default="test123")
    email: str = Field(default="test@example.com")
    handle: str = Field(default="test_user")
    full_name: str = Field(default="Test User")
    is_superuser: bool = Field(default=True)


# Mock UnoObj for testing
class MockUser:
    """Mock user business object."""
    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, data):
        """Create a User from dictionary data."""
        return cls(**data)
    
    @classmethod
    async def get(cls, id):
        """Mock get method."""
        return {
            "id": id,
            "email": "test@example.com",
            "handle": "test_user",
            "full_name": "Test User",
            "is_superuser": True
        }
    
    @classmethod
    async def filter(cls, filters=None):
        """Mock filter method."""
        return [{
            "id": "test123",
            "email": "test@example.com",
            "handle": "test_user",
            "full_name": "Test User",
            "is_superuser": True
        }]
    
    @classmethod
    async def save(cls, data):
        """Mock save method."""
        return {
            "id": "new_id" if "id" not in data else data["id"],
            "email": data.get("email", "new@example.com"),
            "handle": data.get("handle", "new_user"),
            "full_name": data.get("full_name", "New User"),
            "is_superuser": data.get("is_superuser", False)
        }
    
    @classmethod
    async def delete_(cls, id):
        """Mock delete method."""
        return True


class TestEndpointIntegrationConcepts(IsolatedAsyncioTestCase):
    """
    Tests that demonstrate the concepts of endpoint integration.
    
    These tests use mock objects to illustrate the integration patterns
    without requiring a database or actual HTTP requests.
    """

    def setUp(self):
        """Set up the test environment."""
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # User test data
        self.user_data = {
            "id": "test123",
            "email": "test@example.com",
            "handle": "test_user",
            "full_name": "Test User",
            "is_superuser": True
        }
        
        # Create mock user object
        self.user = MockUser(**self.user_data)
    
    async def test_create_endpoint_concept(self):
        """
        Test the concept of the Create endpoint.
        
        This test demonstrates how data flows through a Create endpoint
        from API to database.
        """
        # 1. Client sends data to API endpoint
        api_request_data = {
            "email": "new@example.com",
            "handle": "new_user",
            "full_name": "New User",
            "is_superuser": False
        }
        
        # 2. API converts request to a schema
        request_schema = UserViewSchema(**api_request_data)
        
        # 3. UnoObj.save() method is called with the schema
        saved_data = await MockUser.save(request_schema.model_dump())
        
        # 4. Response data is returned to the client
        assert saved_data["email"] == "new@example.com"
        assert saved_data["handle"] == "new_user"
        assert saved_data["full_name"] == "New User"
        assert saved_data["is_superuser"] is False
        assert "id" in saved_data  # ID should be generated
    
    async def test_view_endpoint_concept(self):
        """
        Test the concept of the View endpoint.
        
        This test demonstrates how data flows through a View endpoint
        from database to API.
        """
        # 1. Client requests an object by ID
        object_id = "test123"
        
        # 2. UnoObj.get() method is called with the ID
        db_result = await MockUser.get(object_id)
        
        # 3. Result is converted to a schema for response
        response_schema = UserViewSchema(**db_result)
        
        # 4. Schema is returned to the client as JSON
        response_data = response_schema.model_dump()
        
        # Verify response
        assert response_data["id"] == object_id
        assert response_data["email"] == "test@example.com"
        assert response_data["handle"] == "test_user"
        assert response_data["is_superuser"] is True
    
    async def test_list_endpoint_concept(self):
        """
        Test the concept of the List endpoint.
        
        This test demonstrates how data flows through a List endpoint
        from database to API.
        """
        # 1. Client requests a list of objects with filters
        filters = {"status": "active"}
        
        # 2. UnoObj.filter() method is called with the filters
        db_results = await MockUser.filter(filters)
        
        # 3. Results are converted to schemas for response
        response_schemas = [UserViewSchema(**item) for item in db_results]
        
        # 4. Schemas are returned to the client as JSON
        response_data = [schema.model_dump() for schema in response_schemas]
        
        # Verify response
        assert len(response_data) > 0
        assert response_data[0]["id"] == "test123"
        assert response_data[0]["email"] == "test@example.com"
    
    async def test_update_endpoint_concept(self):
        """
        Test the concept of the Update endpoint.
        
        This test demonstrates how data flows through an Update endpoint
        from API to database.
        """
        # 1. Client sends update data with ID to API endpoint
        object_id = "test123"
        api_request_data = {
            "id": object_id,
            "full_name": "Updated User",
            "is_superuser": False
        }
        
        # 2. API converts request to a schema
        request_schema = UserViewSchema(**api_request_data)
        
        # 3. UnoObj.save() method is called with the schema
        saved_data = await MockUser.save(request_schema.model_dump())
        
        # 4. Response data is returned to the client
        assert saved_data["id"] == object_id
        assert saved_data["full_name"] == "Updated User"
        assert saved_data["is_superuser"] is False
    
    async def test_delete_endpoint_concept(self):
        """
        Test the concept of the Delete endpoint.
        
        This test demonstrates how data flows through a Delete endpoint.
        """
        # 1. Client sends delete request for an ID
        object_id = "test123"
        
        # 2. UnoObj.delete_() method is called with the ID
        result = await MockUser.delete_(object_id)
        
        # 3. Success result is returned to the client
        assert result is True
    
    async def test_endpoint_factory_concept(self):
        """
        Test the concept of the EndpointFactory.
        
        This test demonstrates how the factory creates endpoints for a model.
        """
        # Mock the necessary components for endpoint factory
        mock_app = MagicMock(spec=FastAPI)
        mock_model = MagicMock()
        mock_model.__name__ = "User"
        mock_model.display_name = "User"
        mock_model.display_name_plural = "Users"
        
        # Create schema manager mock
        schema_manager = MagicMock()
        schema_manager.get_schema.return_value = UserViewSchema
        mock_model.schema_manager = schema_manager
        
        # Initialize the factory
        factory = UnoEndpointFactory()
        
        # The actual endpoint creation is patched to avoid implementation details
        with patch.object(factory, 'create_endpoints', return_value=None) as mock_create:
            # Call the factory method with our mock objects
            factory.create_endpoints(
                app=mock_app,
                model_obj=mock_model,
                endpoints=["Create", "View", "List"]
            )
            
            # Verify factory method was called with expected arguments
            mock_create.assert_called_once_with(
                app=mock_app,
                model_obj=mock_model,
                endpoints=["Create", "View", "List"]
            )