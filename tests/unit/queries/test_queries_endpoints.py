"""
Tests for the Queries module API endpoints.

This module contains comprehensive tests for the Queries module API endpoints
to ensure proper functionality and compliance with domain-driven design principles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import json

from uno.core.result import Success, Failure
from uno.enums import Include, Match
from uno.queries.entities import QueryPath, QueryValue, Query
from uno.queries.domain_services import (
    QueryPathService, QueryValueService, QueryService
)
from uno.queries.domain_endpoints import (
    register_query_endpoints
)

# Test data
TEST_QUERY_PATH_ID = "test_query_path"
TEST_QUERY_VALUE_ID = "test_query_value"
TEST_QUERY_ID = "test_query"
TEST_SOURCE_META_TYPE_ID = "source_meta_type"
TEST_TARGET_META_TYPE_ID = "target_meta_type"
TEST_CYPHER_PATH = "MATCH (s:SourceType)-[r:RELATES_TO]->(t:TargetType)"
TEST_DATA_TYPE = "string"
TEST_QUERY_NAME = "Test Query"


class TestQueriesEndpoints:
    """Tests for the Queries module endpoints."""

    @pytest.fixture
    def mock_query_path_service(self):
        """Create a mock query path service."""
        return AsyncMock(spec=QueryPathService)

    @pytest.fixture
    def mock_query_value_service(self):
        """Create a mock query value service."""
        return AsyncMock(spec=QueryValueService)

    @pytest.fixture
    def mock_query_service(self):
        """Create a mock query service."""
        return AsyncMock(spec=QueryService)

    @pytest.fixture
    def app(self, mock_query_path_service, mock_query_value_service, mock_query_service):
        """Create a FastAPI test application with query routers."""
        app = FastAPI()
        
        # Patch dependency injection to use mock services
        with patch("uno.queries.domain_endpoints.get_service") as mock_get_service:
            # Configure the mock to return appropriate service based on type
            def get_service_side_effect(service_type):
                if service_type == QueryPathService:
                    return mock_query_path_service
                elif service_type == QueryValueService:
                    return mock_query_value_service
                elif service_type == QueryService:
                    return mock_query_service
                return None
                
            mock_get_service.side_effect = get_service_side_effect
            
            # Register routers with the app
            register_query_endpoints(app)
            
            yield app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    # QueryPath endpoint tests
    
    def test_create_query_path_success(self, client, mock_query_path_service):
        """Test creating a query path successfully."""
        # Arrange
        new_query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        mock_query_path_service.create.return_value = Success(new_query_path)
        
        # Act
        response = client.post(
            "/api/query-paths/",
            json={
                "id": TEST_QUERY_PATH_ID,
                "source_meta_type_id": TEST_SOURCE_META_TYPE_ID,
                "target_meta_type_id": TEST_TARGET_META_TYPE_ID,
                "cypher_path": TEST_CYPHER_PATH,
                "data_type": TEST_DATA_TYPE
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_PATH_ID
        assert response.json()["source_meta_type_id"] == TEST_SOURCE_META_TYPE_ID
        assert response.json()["target_meta_type_id"] == TEST_TARGET_META_TYPE_ID
        assert response.json()["cypher_path"] == TEST_CYPHER_PATH
        assert response.json()["data_type"] == TEST_DATA_TYPE
        mock_query_path_service.create.assert_called_once()

    def test_create_query_path_validation_error(self, client, mock_query_path_service):
        """Test creating a query path with validation error."""
        # Arrange
        error_msg = "Source meta type ID cannot be empty"
        mock_query_path_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/query-paths/",
            json={
                "id": TEST_QUERY_PATH_ID,
                "source_meta_type_id": "",  # Empty source meta type ID
                "target_meta_type_id": TEST_TARGET_META_TYPE_ID,
                "cypher_path": TEST_CYPHER_PATH,
                "data_type": TEST_DATA_TYPE
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_query_path_service.create.assert_called_once()

    def test_get_query_path_by_id_success(self, client, mock_query_path_service):
        """Test getting a query path by ID successfully."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        mock_query_path_service.get_by_id.return_value = Success(query_path)
        
        # Act
        response = client.get(f"/api/query-paths/{TEST_QUERY_PATH_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_PATH_ID
        assert response.json()["source_meta_type_id"] == TEST_SOURCE_META_TYPE_ID
        assert response.json()["target_meta_type_id"] == TEST_TARGET_META_TYPE_ID
        assert response.json()["cypher_path"] == TEST_CYPHER_PATH
        assert response.json()["data_type"] == TEST_DATA_TYPE
        mock_query_path_service.get_by_id.assert_called_once_with(TEST_QUERY_PATH_ID)

    def test_get_query_path_by_id_not_found(self, client, mock_query_path_service):
        """Test getting a query path by ID when not found."""
        # Arrange
        mock_query_path_service.get_by_id.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/query-paths/{TEST_QUERY_PATH_ID}")
        
        # Assert
        assert response.status_code == 404
        mock_query_path_service.get_by_id.assert_called_once_with(TEST_QUERY_PATH_ID)

    def test_update_query_path_success(self, client, mock_query_path_service):
        """Test updating a query path successfully."""
        # Arrange
        updated_query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id="updated_target",
            cypher_path="Updated path",
            data_type=TEST_DATA_TYPE
        )
        mock_query_path_service.update.return_value = Success(updated_query_path)
        
        # Act
        response = client.put(
            f"/api/query-paths/{TEST_QUERY_PATH_ID}",
            json={
                "source_meta_type_id": TEST_SOURCE_META_TYPE_ID,
                "target_meta_type_id": "updated_target",
                "cypher_path": "Updated path",
                "data_type": TEST_DATA_TYPE
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_PATH_ID
        assert response.json()["target_meta_type_id"] == "updated_target"
        assert response.json()["cypher_path"] == "Updated path"
        mock_query_path_service.update.assert_called_once()

    def test_delete_query_path_success(self, client, mock_query_path_service):
        """Test deleting a query path successfully."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        mock_query_path_service.delete.return_value = Success(query_path)
        
        # Act
        response = client.delete(f"/api/query-paths/{TEST_QUERY_PATH_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_PATH_ID
        mock_query_path_service.delete.assert_called_once_with(TEST_QUERY_PATH_ID)

    def test_generate_query_paths_success(self, client, mock_query_path_service):
        """Test generating query paths for a model successfully."""
        # Arrange
        model_name = "TestModel"
        query_paths = [
            QueryPath(
                id="path1",
                source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
                target_meta_type_id=TEST_TARGET_META_TYPE_ID,
                cypher_path=TEST_CYPHER_PATH,
                data_type=TEST_DATA_TYPE
            ),
            QueryPath(
                id="path2",
                source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
                target_meta_type_id="another_target",
                cypher_path="Another path",
                data_type=TEST_DATA_TYPE
            )
        ]
        mock_query_path_service.generate_for_model.return_value = Success(query_paths)
        
        # Act
        response = client.post(
            "/api/query-paths/generate",
            json={
                "model_name": model_name
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_query_path_service.generate_for_model.assert_called_once_with(model_name)

    # QueryValue endpoint tests
    
    def test_create_query_value_success(self, client, mock_query_value_service):
        """Test creating a query value successfully."""
        # Arrange
        new_query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        new_query_value.add_value("test_value")
        mock_query_value_service.create.return_value = Success(new_query_value)
        
        # Act
        response = client.post(
            "/api/query-values/",
            json={
                "id": TEST_QUERY_VALUE_ID,
                "query_path_id": TEST_QUERY_PATH_ID,
                "values": ["test_value"]
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_VALUE_ID
        assert response.json()["query_path_id"] == TEST_QUERY_PATH_ID
        mock_query_value_service.create.assert_called_once()

    def test_create_query_value_validation_error(self, client, mock_query_value_service):
        """Test creating a query value with validation error."""
        # Arrange
        error_msg = "Query value must have either values or queries"
        mock_query_value_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/query-values/",
            json={
                "id": TEST_QUERY_VALUE_ID,
                "query_path_id": TEST_QUERY_PATH_ID,
                "values": []  # Empty values list
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_query_value_service.create.assert_called_once()

    # Query endpoint tests
    
    def test_create_query_with_values_success(self, client, mock_query_service):
        """Test creating a query with values successfully."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_query_service.create_with_values.return_value = Success(query)
        
        # Act
        response = client.post(
            "/api/queries/",
            json={
                "id": TEST_QUERY_ID,
                "name": TEST_QUERY_NAME,
                "query_meta_type_id": TEST_SOURCE_META_TYPE_ID,
                "query_values": [
                    {
                        "id": TEST_QUERY_VALUE_ID,
                        "query_path_id": TEST_QUERY_PATH_ID,
                        "values": ["test_value"]
                    }
                ]
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_ID
        assert response.json()["name"] == TEST_QUERY_NAME
        assert response.json()["query_meta_type_id"] == TEST_SOURCE_META_TYPE_ID
        mock_query_service.create_with_values.assert_called_once()

    def test_get_queries_list_with_values_success(self, client, mock_query_service):
        """Test listing queries with values successfully."""
        # Arrange
        queries = [
            Query(
                id="query1",
                name="Query 1",
                query_meta_type_id=TEST_SOURCE_META_TYPE_ID
            ),
            Query(
                id="query2",
                name="Query 2",
                query_meta_type_id=TEST_SOURCE_META_TYPE_ID
            )
        ]
        mock_query_service.list_with_values.return_value = Success(queries)
        
        # Act
        response = client.get("/api/queries/")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == "query1"
        assert response.json()[1]["id"] == "query2"
        mock_query_service.list_with_values.assert_called_once()

    def test_get_query_with_values_by_id_success(self, client, mock_query_service):
        """Test getting a query with values by ID successfully."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_query_service.get_with_values.return_value = Success(query)
        
        # Act
        response = client.get(f"/api/queries/{TEST_QUERY_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_ID
        assert response.json()["name"] == TEST_QUERY_NAME
        assert response.json()["query_meta_type_id"] == TEST_SOURCE_META_TYPE_ID
        mock_query_service.get_with_values.assert_called_once_with(TEST_QUERY_ID)

    def test_get_query_with_values_by_id_not_found(self, client, mock_query_service):
        """Test getting a query with values by ID when not found."""
        # Arrange
        query_id = "nonexistent"
        error_msg = f"Query {query_id} not found"
        mock_query_service.get_with_values.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.get(f"/api/queries/{query_id}")
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_query_service.get_with_values.assert_called_once_with(query_id)

    def test_update_query_with_values_success(self, client, mock_query_service):
        """Test updating a query with values successfully."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name="Updated Name",
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_query_service.update_with_values.return_value = Success(query)
        
        # Act
        response = client.put(
            f"/api/queries/{TEST_QUERY_ID}",
            json={
                "name": "Updated Name",
                "query_meta_type_id": TEST_SOURCE_META_TYPE_ID,
                "query_values": [
                    {
                        "id": TEST_QUERY_VALUE_ID,
                        "query_path_id": TEST_QUERY_PATH_ID,
                        "values": ["test_value"]
                    }
                ]
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_ID
        assert response.json()["name"] == "Updated Name"
        mock_query_service.update_with_values.assert_called_once()

    def test_delete_query_with_values_success(self, client, mock_query_service):
        """Test deleting a query with values successfully."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_query_service.delete_with_values.return_value = Success(query)
        
        # Act
        response = client.delete(f"/api/queries/{TEST_QUERY_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_QUERY_ID
        mock_query_service.delete_with_values.assert_called_once_with(TEST_QUERY_ID)

    def test_execute_query_success(self, client, mock_query_service):
        """Test executing a query successfully."""
        # Arrange
        query_id = TEST_QUERY_ID
        limit = 10
        offset = 0
        record_ids = ["record1", "record2", "record3"]
        mock_query_service.execute_query.return_value = Success(record_ids)
        
        # Act
        response = client.post(
            f"/api/queries/{query_id}/execute",
            json={
                "limit": limit,
                "offset": offset
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert "record1" in response.json()
        assert "record2" in response.json()
        assert "record3" in response.json()
        mock_query_service.execute_query.assert_called_once_with(query_id, limit, offset)

    def test_count_query_matches_success(self, client, mock_query_service):
        """Test counting query matches successfully."""
        # Arrange
        query_id = TEST_QUERY_ID
        count = 42
        mock_query_service.count_query_matches.return_value = Success(count)
        
        # Act
        response = client.post(f"/api/queries/{query_id}/count")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == count
        mock_query_service.count_query_matches.assert_called_once_with(query_id)

    def test_check_record_matches_query_success(self, client, mock_query_service):
        """Test checking if a record matches a query successfully."""
        # Arrange
        query_id = TEST_QUERY_ID
        record_id = "record1"
        matches = True
        mock_query_service.check_record_matches_query.return_value = Success(matches)
        
        # Act
        response = client.post(
            f"/api/queries/{query_id}/check-record",
            json={
                "record_id": record_id
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == matches
        mock_query_service.check_record_matches_query.assert_called_once_with(query_id, record_id)

    def test_invalidate_cache_success(self, client, mock_query_service):
        """Test invalidating query cache successfully."""
        # Arrange
        mock_query_service.invalidate_cache.return_value = Success(True)
        
        # Act
        response = client.post("/api/queries/cache/invalidate")
        
        # Assert
        assert response.status_code == 200
        assert response.json() is True
        mock_query_service.invalidate_cache.assert_called_once()

    def test_execute_query_with_filters_success(self, client, mock_query_service):
        """Test executing a query with filters successfully."""
        # Arrange
        meta_type_id = TEST_SOURCE_META_TYPE_ID
        filters = {"status": "active"}
        limit = 10
        offset = 0
        record_ids = ["record1", "record2", "record3"]
        mock_query_service.execute_query_with_filters.return_value = Success(record_ids)
        
        # Act
        response = client.post(
            "/api/queries/execute-with-filters",
            json={
                "meta_type_id": meta_type_id,
                "filters": filters,
                "limit": limit,
                "offset": offset
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert "record1" in response.json()
        assert "record2" in response.json()
        assert "record3" in response.json()
        mock_query_service.execute_query_with_filters.assert_called_once_with(
            meta_type_id, filters, limit, offset
        )