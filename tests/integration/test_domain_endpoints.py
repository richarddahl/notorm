"""
Integration tests for domain endpoints.

This module contains tests that validate the entire flow from API endpoints
through services and repositories to ensure domain-driven endpoints are
working correctly.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
import json
from typing import Dict, Any, List, Optional

from uno.core.di import get_container, clear_container
from uno.dependencies.testing import configure_test_container
from uno.domain.api_integration import create_domain_router

# Import domain entities and services
from uno.attributes.domain_endpoints import create_attributes_router
from uno.meta.domain_endpoints import create_meta_router
from uno.values.domain_endpoints import create_values_router


@pytest.fixture
def test_client():
    """Create a test client for FastAPI with domain routers."""
    # Set up the test container with mocks
    configure_test_container()
    
    # Create the FastAPI application
    app = FastAPI()
    
    # Add domain routers
    app.include_router(create_attributes_router())
    app.include_router(create_meta_router())
    app.include_router(create_values_router())
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up
    clear_container()


class TestMetaEndpoints:
    """Tests for the meta endpoints."""
    
    def test_create_meta_type(self, test_client):
        """Test creating a meta type."""
        # Arrange
        meta_type_data = {
            "name": "Test Meta Type",
            "description": "Test Description"
        }
        
        # Act
        response = test_client.post("/meta-types", json=meta_type_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == meta_type_data["name"]
        assert data["description"] == meta_type_data["description"]
        assert "id" in data
    
    def test_get_meta_type(self, test_client):
        """Test retrieving a meta type."""
        # Arrange - Create a meta type first
        meta_type_data = {
            "name": "Test Meta Type",
            "description": "Test Description"
        }
        create_response = test_client.post("/meta-types", json=meta_type_data)
        created_data = create_response.json()
        meta_id = created_data["id"]
        
        # Act
        response = test_client.get(f"/meta-types/{meta_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meta_id
        assert data["name"] == meta_type_data["name"]
        assert data["description"] == meta_type_data["description"]
    
    def test_list_meta_types(self, test_client):
        """Test listing meta types."""
        # Arrange - Create a few meta types
        for i in range(3):
            meta_type_data = {
                "name": f"Test Meta Type {i}",
                "description": f"Test Description {i}"
            }
            test_client.post("/meta-types", json=meta_type_data)
        
        # Act
        response = test_client.get("/meta-types")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least the ones we created
        
    def test_update_meta_type(self, test_client):
        """Test updating a meta type."""
        # Arrange - Create a meta type first
        meta_type_data = {
            "name": "Test Meta Type",
            "description": "Test Description"
        }
        create_response = test_client.post("/meta-types", json=meta_type_data)
        created_data = create_response.json()
        meta_id = created_data["id"]
        
        # Act - Update it
        update_data = {
            "description": "Updated Description"
        }
        response = test_client.patch(f"/meta-types/{meta_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meta_id
        assert data["name"] == meta_type_data["name"]
        assert data["description"] == update_data["description"]
    
    def test_delete_meta_type(self, test_client):
        """Test deleting a meta type."""
        # Arrange - Create a meta type first
        meta_type_data = {
            "name": "Test Meta Type for Deletion",
            "description": "To be deleted"
        }
        create_response = test_client.post("/meta-types", json=meta_type_data)
        created_data = create_response.json()
        meta_id = created_data["id"]
        
        # Act
        response = test_client.delete(f"/meta-types/{meta_id}")
        
        # Assert
        assert response.status_code == 200
        
        # Verify it's gone
        get_response = test_client.get(f"/meta-types/{meta_id}")
        assert get_response.status_code == 404


class TestAttributesEndpoints:
    """Tests for the attributes endpoints."""
    
    def test_create_attribute(self, test_client):
        """Test creating an attribute."""
        # Arrange
        attribute_data = {
            "name": "Test Attribute",
            "description": "Test Description",
            "attribute_type": "string"
        }
        
        # Act
        response = test_client.post("/attributes", json=attribute_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == attribute_data["name"]
        assert "id" in data


class TestValuesEndpoints:
    """Tests for the values endpoints."""
    
    def test_create_value(self, test_client):
        """Test creating a value."""
        # First create an attribute
        attribute_data = {
            "name": "Test Attribute",
            "description": "Test Description",
            "attribute_type": "string"
        }
        attr_response = test_client.post("/attributes", json=attribute_data)
        attr_data = attr_response.json()
        
        # Then create a value for that attribute
        value_data = {
            "attribute_id": attr_data["id"],
            "value": "Test Value",
            "display_order": 1
        }
        
        # Act
        response = test_client.post("/values", json=value_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["value"] == value_data["value"]
        assert data["attribute_id"] == value_data["attribute_id"]
        assert "id" in data