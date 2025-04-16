"""
Tests for the Attributes module API endpoints.

This module contains comprehensive tests for the Attributes module API endpoints
to ensure proper functionality and compliance with domain-driven design principles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from uno.core.result import Success, Failure
from uno.attributes.entities import AttributeType, Attribute
from uno.attributes.domain_services import AttributeTypeService, AttributeService
from uno.attributes.domain_endpoints import (
    attribute_router,
    attribute_type_router,
    register_attribute_routers,
)

# Test data
TEST_ATTRIBUTE_TYPE_ID = "test_type"
TEST_ATTRIBUTE_ID = "test_attribute"


class TestAttributeEndpoints:
    """Tests for the Attribute module endpoints."""

    @pytest.fixture
    def mock_attribute_service(self):
        """Create a mock attribute service."""
        return AsyncMock(spec=AttributeService)

    @pytest.fixture
    def mock_attribute_type_service(self):
        """Create a mock attribute type service."""
        return AsyncMock(spec=AttributeTypeService)

    @pytest.fixture
    def app(self, mock_attribute_service, mock_attribute_type_service):
        """Create a FastAPI test application with attribute routers."""
        app = FastAPI()
        
        # Patch dependency injection to use mock services
        with patch("uno.attributes.domain_endpoints.get_service") as mock_get_service:
            # Configure the mock to return appropriate service based on type
            def get_service_side_effect(service_type):
                if service_type == AttributeService:
                    return mock_attribute_service
                elif service_type == AttributeTypeService:
                    return mock_attribute_type_service
                return None
                
            mock_get_service.side_effect = get_service_side_effect
            
            # Register routers with the app
            register_attribute_routers(app)
            
            yield app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    # AttributeType endpoint tests
    
    def test_create_attribute_type_success(self, client, mock_attribute_type_service):
        """Test creating an attribute type successfully."""
        # Arrange
        new_type = AttributeType(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Test Type", 
            text="Test description"
        )
        mock_attribute_type_service.create.return_value = Success(new_type)
        
        # Act
        response = client.post(
            "/api/attribute-types/",
            json={
                "id": TEST_ATTRIBUTE_TYPE_ID,
                "name": "Test Type",
                "text": "Test description"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_TYPE_ID
        assert response.json()["name"] == "Test Type"
        mock_attribute_type_service.create.assert_called_once()

    def test_create_attribute_type_validation_error(self, client, mock_attribute_type_service):
        """Test creating an attribute type with validation error."""
        # Arrange
        error_msg = "Text cannot be empty"
        mock_attribute_type_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/attribute-types/",
            json={
                "id": TEST_ATTRIBUTE_TYPE_ID,
                "name": "Test Type",
                "text": ""  # Empty text will cause validation error
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_attribute_type_service.create.assert_called_once()

    def test_get_attribute_type_by_id_success(self, client, mock_attribute_type_service):
        """Test getting an attribute type by ID successfully."""
        # Arrange
        attr_type = AttributeType(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Test Type", 
            text="Test description"
        )
        mock_attribute_type_service.get_by_id.return_value = Success(attr_type)
        
        # Act
        response = client.get(f"/api/attribute-types/{TEST_ATTRIBUTE_TYPE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_TYPE_ID
        assert response.json()["name"] == "Test Type"
        mock_attribute_type_service.get_by_id.assert_called_once_with(TEST_ATTRIBUTE_TYPE_ID)

    def test_get_attribute_type_by_id_not_found(self, client, mock_attribute_type_service):
        """Test getting an attribute type by ID when not found."""
        # Arrange
        mock_attribute_type_service.get_by_id.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/attribute-types/{TEST_ATTRIBUTE_TYPE_ID}")
        
        # Assert
        assert response.status_code == 404
        mock_attribute_type_service.get_by_id.assert_called_once_with(TEST_ATTRIBUTE_TYPE_ID)

    def test_update_attribute_type_success(self, client, mock_attribute_type_service):
        """Test updating an attribute type successfully."""
        # Arrange
        updated_type = AttributeType(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Updated Type", 
            text="Updated description"
        )
        mock_attribute_type_service.update.return_value = Success(updated_type)
        
        # Act
        response = client.put(
            f"/api/attribute-types/{TEST_ATTRIBUTE_TYPE_ID}",
            json={
                "name": "Updated Type",
                "text": "Updated description"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_TYPE_ID
        assert response.json()["name"] == "Updated Type"
        assert response.json()["text"] == "Updated description"
        mock_attribute_type_service.update.assert_called_once()

    def test_delete_attribute_type_success(self, client, mock_attribute_type_service):
        """Test deleting an attribute type successfully."""
        # Arrange
        attr_type = AttributeType(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Test Type", 
            text="Test description"
        )
        mock_attribute_type_service.delete.return_value = Success(attr_type)
        
        # Act
        response = client.delete(f"/api/attribute-types/{TEST_ATTRIBUTE_TYPE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_TYPE_ID
        mock_attribute_type_service.delete.assert_called_once_with(TEST_ATTRIBUTE_TYPE_ID)

    def test_get_attribute_types_list_success(self, client, mock_attribute_type_service):
        """Test getting a list of attribute types successfully."""
        # Arrange
        attr_types = [
            AttributeType(id="type1", name="Type 1", text="Description 1"),
            AttributeType(id="type2", name="Type 2", text="Description 2")
        ]
        mock_attribute_type_service.list.return_value = Success(attr_types)
        
        # Act
        response = client.get("/api/attribute-types/")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == "type1"
        assert response.json()[1]["id"] == "type2"
        mock_attribute_type_service.list.assert_called_once()

    def test_get_attribute_type_by_name_success(self, client, mock_attribute_type_service):
        """Test getting attribute types by name successfully."""
        # Arrange
        name = "Test Type"
        attr_types = [
            AttributeType(id="type1", name=name, text="Description 1"),
            AttributeType(id="type2", name=name, text="Description 2")
        ]
        mock_attribute_type_service.find_by_name.return_value = Success(attr_types)
        
        # Act
        response = client.get(f"/api/attribute-types/by-name/{name}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(at["name"] == name for at in response.json())
        mock_attribute_type_service.find_by_name.assert_called_once_with(name, None)

    def test_get_attribute_type_by_name_not_found(self, client, mock_attribute_type_service):
        """Test getting attribute types by name when none found."""
        # Arrange
        name = "Nonexistent"
        mock_attribute_type_service.find_by_name.return_value = Success([])
        
        # Act
        response = client.get(f"/api/attribute-types/by-name/{name}")
        
        # Assert
        assert response.status_code == 404
        assert "Attribute type not found" in response.json()["detail"]
        mock_attribute_type_service.find_by_name.assert_called_once_with(name, None)

    def test_get_attribute_type_hierarchy_success(self, client, mock_attribute_type_service):
        """Test getting an attribute type hierarchy successfully."""
        # Arrange
        root_id = TEST_ATTRIBUTE_TYPE_ID
        hierarchy = [
            AttributeType(id=root_id, name="Root Type", text="Root Description"),
            AttributeType(id="child1", name="Child 1", text="Child Description 1", parent_id=root_id),
            AttributeType(id="child2", name="Child 2", text="Child Description 2", parent_id=root_id)
        ]
        mock_attribute_type_service.get_hierarchy.return_value = Success(hierarchy)
        
        # Act
        response = client.get(f"/api/attribute-types/{root_id}/hierarchy")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert response.json()[0]["id"] == root_id
        mock_attribute_type_service.get_hierarchy.assert_called_once_with(root_id)

    def test_get_attribute_type_hierarchy_not_found(self, client, mock_attribute_type_service):
        """Test getting an attribute type hierarchy when root not found."""
        # Arrange
        root_id = "nonexistent"
        error_msg = f"Attribute type {root_id} not found"
        mock_attribute_type_service.get_hierarchy.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.get(f"/api/attribute-types/{root_id}/hierarchy")
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_attribute_type_service.get_hierarchy.assert_called_once_with(root_id)

    def test_add_value_type_success(self, client, mock_attribute_type_service):
        """Test adding a value type to an attribute type successfully."""
        # Arrange
        attr_type_id = TEST_ATTRIBUTE_TYPE_ID
        meta_type_id = "meta_type_1"
        
        attr_type = AttributeType(id=attr_type_id, name="Test Type", text="Test Description")
        attr_type.add_value_type(meta_type_id, "Meta Type 1")
        
        mock_attribute_type_service.add_value_type.return_value = Success(attr_type)
        
        # Act
        response = client.post(f"/api/attribute-types/{attr_type_id}/value-types/{meta_type_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == attr_type_id
        assert any(vt["id"] == meta_type_id for vt in response.json()["value_types"])
        mock_attribute_type_service.add_value_type.assert_called_once_with(attr_type_id, meta_type_id)

    def test_add_value_type_not_found(self, client, mock_attribute_type_service):
        """Test adding a value type to a nonexistent attribute type."""
        # Arrange
        attr_type_id = "nonexistent"
        meta_type_id = "meta_type_1"
        error_msg = f"Attribute type {attr_type_id} not found"
        
        mock_attribute_type_service.add_value_type.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(f"/api/attribute-types/{attr_type_id}/value-types/{meta_type_id}")
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_attribute_type_service.add_value_type.assert_called_once_with(attr_type_id, meta_type_id)

    def test_add_describable_type_success(self, client, mock_attribute_type_service):
        """Test adding a describable type to an attribute type successfully."""
        # Arrange
        attr_type_id = TEST_ATTRIBUTE_TYPE_ID
        meta_type_id = "meta_type_1"
        
        attr_type = AttributeType(id=attr_type_id, name="Test Type", text="Test Description")
        attr_type.add_describable_type(meta_type_id, "Meta Type 1")
        
        mock_attribute_type_service.add_describable_type.return_value = Success(attr_type)
        
        # Act
        response = client.post(f"/api/attribute-types/{attr_type_id}/describes/{meta_type_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == attr_type_id
        assert any(dt["id"] == meta_type_id for dt in response.json()["describes"])
        mock_attribute_type_service.add_describable_type.assert_called_once_with(attr_type_id, meta_type_id)

    # Attribute endpoint tests
    
    def test_create_attribute_success(self, client, mock_attribute_service):
        """Test creating an attribute successfully."""
        # Arrange
        new_attribute = Attribute(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID,
            comment="Test comment"
        )
        mock_attribute_service.create.return_value = Success(new_attribute)
        
        # Act
        response = client.post(
            "/api/attributes/",
            json={
                "id": TEST_ATTRIBUTE_ID,
                "attribute_type_id": TEST_ATTRIBUTE_TYPE_ID,
                "comment": "Test comment"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_ID
        assert response.json()["attribute_type_id"] == TEST_ATTRIBUTE_TYPE_ID
        assert response.json()["comment"] == "Test comment"
        mock_attribute_service.create.assert_called_once()

    def test_create_attribute_validation_error(self, client, mock_attribute_service):
        """Test creating an attribute with validation error."""
        # Arrange
        error_msg = "Attribute type ID cannot be empty"
        mock_attribute_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/attributes/",
            json={
                "id": TEST_ATTRIBUTE_ID,
                "attribute_type_id": "",  # Empty type ID will cause validation error
                "comment": "Test comment"
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_attribute_service.create.assert_called_once()

    def test_get_attribute_by_id_success(self, client, mock_attribute_service):
        """Test getting an attribute by ID successfully."""
        # Arrange
        attribute = Attribute(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID,
            comment="Test comment"
        )
        mock_attribute_service.get_by_id.return_value = Success(attribute)
        
        # Act
        response = client.get(f"/api/attributes/{TEST_ATTRIBUTE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_ID
        assert response.json()["attribute_type_id"] == TEST_ATTRIBUTE_TYPE_ID
        mock_attribute_service.get_by_id.assert_called_once_with(TEST_ATTRIBUTE_ID)

    def test_get_attribute_by_id_not_found(self, client, mock_attribute_service):
        """Test getting an attribute by ID when not found."""
        # Arrange
        mock_attribute_service.get_by_id.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/attributes/{TEST_ATTRIBUTE_ID}")
        
        # Assert
        assert response.status_code == 404
        mock_attribute_service.get_by_id.assert_called_once_with(TEST_ATTRIBUTE_ID)

    def test_update_attribute_success(self, client, mock_attribute_service):
        """Test updating an attribute successfully."""
        # Arrange
        updated_attribute = Attribute(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID,
            comment="Updated comment"
        )
        mock_attribute_service.update.return_value = Success(updated_attribute)
        
        # Act
        response = client.put(
            f"/api/attributes/{TEST_ATTRIBUTE_ID}",
            json={
                "comment": "Updated comment"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_ID
        assert response.json()["comment"] == "Updated comment"
        mock_attribute_service.update.assert_called_once()

    def test_delete_attribute_success(self, client, mock_attribute_service):
        """Test deleting an attribute successfully."""
        # Arrange
        attribute = Attribute(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        mock_attribute_service.delete.return_value = Success(attribute)
        
        # Act
        response = client.delete(f"/api/attributes/{TEST_ATTRIBUTE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ATTRIBUTE_ID
        mock_attribute_service.delete.assert_called_once_with(TEST_ATTRIBUTE_ID)

    def test_get_attributes_list_success(self, client, mock_attribute_service):
        """Test getting a list of attributes successfully."""
        # Arrange
        attributes = [
            Attribute(id="attr1", attribute_type_id=TEST_ATTRIBUTE_TYPE_ID),
            Attribute(id="attr2", attribute_type_id=TEST_ATTRIBUTE_TYPE_ID)
        ]
        mock_attribute_service.list.return_value = Success(attributes)
        
        # Act
        response = client.get("/api/attributes/")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == "attr1"
        assert response.json()[1]["id"] == "attr2"
        mock_attribute_service.list.assert_called_once()

    def test_get_attributes_by_type_success(self, client, mock_attribute_service):
        """Test getting attributes by type successfully."""
        # Arrange
        attribute_type_id = TEST_ATTRIBUTE_TYPE_ID
        attributes = [
            Attribute(id="attr1", attribute_type_id=attribute_type_id),
            Attribute(id="attr2", attribute_type_id=attribute_type_id)
        ]
        mock_attribute_service.find_by_attribute_type.return_value = Success(attributes)
        
        # Act
        response = client.get(f"/api/attributes/by-type/{attribute_type_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(attr["attribute_type_id"] == attribute_type_id for attr in response.json())
        mock_attribute_service.find_by_attribute_type.assert_called_once_with(attribute_type_id)

    def test_get_attribute_with_related_success(self, client, mock_attribute_service):
        """Test getting an attribute with related data successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID,
            comment="Test comment"
        )
        # Add example relationships
        attribute.value_ids = ["value1", "value2"]
        attribute.meta_record_ids = ["record1"]
        
        mock_attribute_service.get_with_related_data.return_value = Success(attribute)
        
        # Act
        response = client.get(f"/api/attributes/{attribute_id}/with-related")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == attribute_id
        assert "value_ids" in response.json()
        assert len(response.json()["value_ids"]) == 2
        mock_attribute_service.get_with_related_data.assert_called_once_with(attribute_id)

    def test_get_attribute_with_related_not_found(self, client, mock_attribute_service):
        """Test getting an attribute with related data when not found."""
        # Arrange
        attribute_id = "nonexistent"
        error_msg = f"Attribute {attribute_id} not found"
        mock_attribute_service.get_with_related_data.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.get(f"/api/attributes/{attribute_id}/with-related")
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_attribute_service.get_with_related_data.assert_called_once_with(attribute_id)

    def test_add_value_to_attribute_success(self, client, mock_attribute_service):
        """Test adding a value to an attribute successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        value_id = "value1"
        
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        attribute.add_value(value_id)
        
        mock_attribute_service.add_value.return_value = Success(attribute)
        
        # Act
        response = client.post(f"/api/attributes/{attribute_id}/values/{value_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == attribute_id
        assert value_id in response.json()["value_ids"]
        mock_attribute_service.add_value.assert_called_once_with(attribute_id, value_id)

    def test_add_value_to_attribute_not_found(self, client, mock_attribute_service):
        """Test adding a value to a nonexistent attribute."""
        # Arrange
        attribute_id = "nonexistent"
        value_id = "value1"
        error_msg = f"Attribute {attribute_id} not found"
        
        mock_attribute_service.add_value.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(f"/api/attributes/{attribute_id}/values/{value_id}")
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_attribute_service.add_value.assert_called_once_with(attribute_id, value_id)

    def test_add_meta_record_to_attribute_success(self, client, mock_attribute_service):
        """Test adding a meta record to an attribute successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        meta_record_id = "record1"
        
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        attribute.add_meta_record(meta_record_id)
        
        mock_attribute_service.add_meta_record.return_value = Success(attribute)
        
        # Act
        response = client.post(f"/api/attributes/{attribute_id}/meta-records/{meta_record_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == attribute_id
        assert meta_record_id in response.json()["meta_record_ids"]
        mock_attribute_service.add_meta_record.assert_called_once_with(attribute_id, meta_record_id)