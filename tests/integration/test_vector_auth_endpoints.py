"""
Integration tests for vector search and authorization domain endpoints.

This module contains tests that validate the entire flow from API endpoints
through services and repositories to ensure domain-driven endpoints are
working correctly for the vector search and authorization modules.
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
from uno.vector_search.domain_endpoints import create_vector_search_router
from uno.authorization.domain_endpoints import create_authorization_router


@pytest.fixture
def test_client():
    """Create a test client for FastAPI with domain routers."""
    # Set up the test container with mocks
    configure_test_container()
    
    # Create the FastAPI application
    app = FastAPI()
    
    # Add domain routers
    app.include_router(create_vector_search_router())
    app.include_router(create_authorization_router())
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up
    clear_container()


class TestVectorSearchEndpoints:
    """Tests for the vector search endpoints."""
    
    def test_create_vector_index(self, test_client):
        """Test creating a vector index."""
        # Arrange
        index_data = {
            "name": "test_index",
            "dimension": 384,
            "description": "Test vector index",
            "metric": "cosine"
        }
        
        # Act
        response = test_client.post("/vector-indexes", json=index_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == index_data["name"]
        assert data["dimension"] == index_data["dimension"]
        assert "id" in data
    
    def test_add_vector(self, test_client):
        """Test adding a vector to an index."""
        # Arrange - Create an index first
        index_data = {
            "name": "test_index_for_vectors",
            "dimension": 3,
            "description": "Test vector index for adding vectors",
            "metric": "cosine"
        }
        create_response = test_client.post("/vector-indexes", json=index_data)
        created_data = create_response.json()
        index_id = created_data["id"]
        
        # Act - Add a vector
        vector_data = {
            "index_id": index_id,
            "vector": [0.1, 0.2, 0.3],
            "metadata": {"text": "Test text", "source": "test"}
        }
        response = test_client.post("/vectors", json=vector_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["index_id"] == index_id
        assert "id" in data
    
    def test_vector_search(self, test_client):
        """Test searching vectors."""
        # Arrange - Create an index and add vectors
        index_data = {
            "name": "test_index_for_search",
            "dimension": 3,
            "description": "Test vector index for searching",
            "metric": "cosine"
        }
        create_index_response = test_client.post("/vector-indexes", json=index_data)
        index_data = create_index_response.json()
        index_id = index_data["id"]
        
        # Add vectors
        for i in range(3):
            vector_data = {
                "index_id": index_id,
                "vector": [0.1 * i, 0.2 * i, 0.3 * i],
                "metadata": {"text": f"Test text {i}", "source": "test"}
            }
            test_client.post("/vectors", json=vector_data)
        
        # Act - Search
        search_data = {
            "index_id": index_id,
            "query_vector": [0.1, 0.2, 0.3],
            "top_k": 2
        }
        response = test_client.post("/search", json=search_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) <= 2  # At most 2 results (top_k)


class TestAuthorizationEndpoints:
    """Tests for the authorization endpoints."""
    
    def test_create_role(self, test_client):
        """Test creating a role."""
        # Arrange
        role_data = {
            "name": "test_role",
            "description": "Test role for API testing"
        }
        
        # Act
        response = test_client.post("/roles", json=role_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == role_data["name"]
        assert data["description"] == role_data["description"]
        assert "id" in data
    
    def test_create_permission(self, test_client):
        """Test creating a permission."""
        # Arrange
        permission_data = {
            "name": "test_permission",
            "resource": "test_resource",
            "action": "read",
            "description": "Test permission for reading test resource"
        }
        
        # Act
        response = test_client.post("/permissions", json=permission_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == permission_data["name"]
        assert data["resource"] == permission_data["resource"]
        assert data["action"] == permission_data["action"]
        assert "id" in data
    
    def test_assign_permission_to_role(self, test_client):
        """Test assigning a permission to a role."""
        # Arrange - Create a role and permission first
        role_data = {
            "name": "test_role_with_permission",
            "description": "Test role for permission assignment"
        }
        role_response = test_client.post("/roles", json=role_data)
        role_data = role_response.json()
        role_id = role_data["id"]
        
        permission_data = {
            "name": "test_permission_for_role",
            "resource": "test_resource",
            "action": "read",
            "description": "Test permission to assign to role"
        }
        permission_response = test_client.post("/permissions", json=permission_data)
        permission_data = permission_response.json()
        permission_id = permission_data["id"]
        
        # Act - Assign permission to role
        assignment_data = {
            "role_id": role_id,
            "permission_id": permission_id
        }
        response = test_client.post("/role-permissions", json=assignment_data)
        
        # Assert
        assert response.status_code == 201
        
        # Verify the role has the permission
        role_permissions_response = test_client.get(f"/roles/{role_id}/permissions")
        assert role_permissions_response.status_code == 200
        data = role_permissions_response.json()
        assert len(data) >= 1
        assert any(p["id"] == permission_id for p in data)