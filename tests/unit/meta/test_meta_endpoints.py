"""
Tests for the Meta module domain endpoints.

This module contains comprehensive tests for the Meta module domain endpoints
to ensure proper API functionality and integration with domain services.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from uno.meta.entities import MetaType, MetaRecord
from uno.meta.domain_services import MetaTypeService, MetaRecordService
from uno.meta.domain_endpoints import create_meta_router
from uno.core.result import Success, Failure


class TestMetaEndpoints:
    """Tests for the Meta module domain endpoints."""

    @pytest.fixture
    def mock_meta_type_service(self):
        """Create a mock MetaTypeService."""
        service = AsyncMock(spec=MetaTypeService)
        return service

    @pytest.fixture
    def mock_meta_record_service(self):
        """Create a mock MetaRecordService."""
        service = AsyncMock(spec=MetaRecordService)
        return service

    @pytest.fixture
    def test_client(self, mock_meta_type_service, mock_meta_record_service):
        """Create a test client with the meta router."""
        app = FastAPI()
        
        # Patch the get_service function to return our mocks
        with patch("uno.dependencies.scoped_container.get_service") as mock_get_service:
            def get_service_side_effect(service_type):
                if service_type == MetaTypeService:
                    return mock_meta_type_service
                elif service_type == MetaRecordService:
                    return mock_meta_record_service
                return None
                
            mock_get_service.side_effect = get_service_side_effect
            
            # Create and add the router
            router = create_meta_router()
            app.include_router(router)
            
            # Create and return the test client
            return TestClient(app)

    def test_create_meta_type(self, test_client, mock_meta_type_service):
        """Test creating a meta type via the API."""
        # Arrange
        meta_type_data = {
            "id": "test_type",
            "name": "Test Type",
            "description": "A test meta type"
        }
        
        meta_type = MetaType(**meta_type_data)
        mock_meta_type_service.create.return_value = Success(meta_type)
        
        # Act
        response = test_client.post("/meta-types", json=meta_type_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == meta_type_data["id"]
        assert data["name"] == meta_type_data["name"]
        assert data["description"] == meta_type_data["description"]
        
        # Verify service was called correctly
        mock_meta_type_service.create.assert_called_once_with(**meta_type_data)

    def test_create_meta_type_validation_error(self, test_client, mock_meta_type_service):
        """Test creating a meta type with validation error."""
        # Arrange
        meta_type_data = {
            "id": "invalid id!",
            "name": "Test Type"
        }
        
        error_message = "ID must contain only alphanumeric characters and underscores"
        mock_meta_type_service.create.return_value = Failure(error_message)
        
        # Act
        response = test_client.post("/meta-types", json=meta_type_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert error_message in data["detail"]
        
        # Verify service was called
        mock_meta_type_service.create.assert_called_once()

    def test_get_meta_type(self, test_client, mock_meta_type_service):
        """Test getting a meta type by ID."""
        # Arrange
        meta_type_id = "test_type"
        meta_type = MetaType(id=meta_type_id, name="Test Type")
        mock_meta_type_service.get_by_id.return_value = Success(meta_type)
        
        # Act
        response = test_client.get(f"/meta-types/{meta_type_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meta_type_id
        assert data["name"] == "Test Type"
        
        # Verify service was called correctly
        mock_meta_type_service.get_by_id.assert_called_once_with(meta_type_id)

    def test_get_meta_type_not_found(self, test_client, mock_meta_type_service):
        """Test getting a non-existent meta type."""
        # Arrange
        meta_type_id = "nonexistent"
        error_message = f"MetaType with ID '{meta_type_id}' not found"
        mock_meta_type_service.get_by_id.return_value = Failure(error_message)
        
        # Act
        response = test_client.get(f"/meta-types/{meta_type_id}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert error_message in data["detail"]
        
        # Verify service was called correctly
        mock_meta_type_service.get_by_id.assert_called_once_with(meta_type_id)

    def test_list_meta_types(self, test_client, mock_meta_type_service):
        """Test listing meta types."""
        # Arrange
        meta_types = [
            MetaType(id="type1", name="Type 1"),
            MetaType(id="type2", name="Type 2")
        ]
        mock_meta_type_service.list.return_value = Success(meta_types)
        
        # Act
        response = test_client.get("/meta-types")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "type1"
        assert data[1]["id"] == "type2"
        
        # Verify service was called correctly
        mock_meta_type_service.list.assert_called_once()

    def test_update_meta_type(self, test_client, mock_meta_type_service):
        """Test updating a meta type."""
        # Arrange
        meta_type_id = "test_type"
        update_data = {
            "description": "Updated description"
        }
        
        updated_meta_type = MetaType(
            id=meta_type_id, 
            name="Test Type", 
            description=update_data["description"]
        )
        mock_meta_type_service.update_by_id.return_value = Success(updated_meta_type)
        
        # Act
        response = test_client.patch(f"/meta-types/{meta_type_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meta_type_id
        assert data["description"] == update_data["description"]
        
        # Verify service was called correctly
        mock_meta_type_service.update_by_id.assert_called_once_with(meta_type_id, **update_data)

    def test_delete_meta_type(self, test_client, mock_meta_type_service):
        """Test deleting a meta type."""
        # Arrange
        meta_type_id = "test_type"
        mock_meta_type_service.delete_by_id.return_value = Success(True)
        
        # Act
        response = test_client.delete(f"/meta-types/{meta_type_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify service was called correctly
        mock_meta_type_service.delete_by_id.assert_called_once_with(meta_type_id)

    def test_create_meta_record(self, test_client, mock_meta_record_service):
        """Test creating a meta record via the API."""
        # Arrange
        meta_record_data = {
            "id": "test_record",
            "meta_type_id": "test_type"
        }
        
        meta_record = MetaRecord(**meta_record_data)
        mock_meta_record_service.create.return_value = Success(meta_record)
        
        # Act
        response = test_client.post("/meta-records", json=meta_record_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == meta_record_data["id"]
        assert data["meta_type_id"] == meta_record_data["meta_type_id"]
        
        # Verify service was called correctly
        mock_meta_record_service.create.assert_called_once_with(**meta_record_data)

    def test_get_meta_record(self, test_client, mock_meta_record_service):
        """Test getting a meta record by ID."""
        # Arrange
        meta_record_id = "test_record"
        meta_record = MetaRecord(id=meta_record_id, meta_type_id="test_type")
        mock_meta_record_service.get_by_id.return_value = Success(meta_record)
        
        # Act
        response = test_client.get(f"/meta-records/{meta_record_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meta_record_id
        assert data["meta_type_id"] == "test_type"
        
        # Verify service was called correctly
        mock_meta_record_service.get_by_id.assert_called_once_with(meta_record_id)

    def test_get_records_for_type(self, test_client, mock_meta_record_service):
        """Test getting records for a specific meta type."""
        # Arrange
        meta_type_id = "test_type"
        records = [
            MetaRecord(id="record1", meta_type_id=meta_type_id),
            MetaRecord(id="record2", meta_type_id=meta_type_id)
        ]
        mock_meta_record_service.get_records_for_type.return_value = Success(records)
        
        # Act
        response = test_client.get(f"/meta-records/type/{meta_type_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(record["meta_type_id"] == meta_type_id for record in data)
        
        # Verify service was called correctly
        mock_meta_record_service.get_records_for_type.assert_called_once_with(meta_type_id)