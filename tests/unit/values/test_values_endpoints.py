"""
Tests for the Values module API endpoints.

This module contains comprehensive tests for the Values module API endpoints
to ensure proper functionality and compliance with domain-driven design principles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, date, time, UTC
import decimal
from decimal import Decimal
import urllib.parse

from uno.core.result import Success, Failure
from uno.values.entities import (
    BaseValue, Attachment, BooleanValue, DateTimeValue, 
    DateValue, DecimalValue, IntegerValue, TextValue, TimeValue
)
from uno.values.domain_services import (
    ValueService, AttachmentService, BooleanValueService, DateTimeValueService,
    DateValueService, DecimalValueService, IntegerValueService,
    TextValueService, TimeValueService
)
from uno.values.domain_endpoints import (
    register_values_endpoints
)

# Test data
TEST_VALUE_ID = "test_value"
TEST_VALUE_NAME = "Test Value"
TEST_GROUP_ID = "test_group"
TEST_TENANT_ID = "test_tenant"
TEST_TEXT_VALUE = "Test text value"
TEST_INTEGER_VALUE = 42
TEST_BOOLEAN_VALUE = True
TEST_DECIMAL_VALUE = Decimal("42.5")
TEST_DATE_VALUE = date(2023, 1, 1)
TEST_DATETIME_VALUE = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
TEST_TIME_VALUE = time(12, 0, 0)
TEST_FILE_PATH = "/path/to/file.txt"


class TestValuesEndpoints:
    """Tests for the Values module endpoints."""

    @pytest.fixture
    def mock_attachment_service(self):
        """Create a mock attachment service."""
        return AsyncMock(spec=AttachmentService)

    @pytest.fixture
    def mock_boolean_service(self):
        """Create a mock boolean service."""
        return AsyncMock(spec=BooleanValueService)

    @pytest.fixture
    def mock_datetime_service(self):
        """Create a mock datetime service."""
        return AsyncMock(spec=DateTimeValueService)

    @pytest.fixture
    def mock_date_service(self):
        """Create a mock date service."""
        return AsyncMock(spec=DateValueService)

    @pytest.fixture
    def mock_decimal_service(self):
        """Create a mock decimal service."""
        return AsyncMock(spec=DecimalValueService)

    @pytest.fixture
    def mock_integer_service(self):
        """Create a mock integer service."""
        return AsyncMock(spec=IntegerValueService)

    @pytest.fixture
    def mock_text_service(self):
        """Create a mock text service."""
        return AsyncMock(spec=TextValueService)

    @pytest.fixture
    def mock_time_service(self):
        """Create a mock time service."""
        return AsyncMock(spec=TimeValueService)

    @pytest.fixture
    def app(self, mock_attachment_service, mock_boolean_service, mock_datetime_service,
            mock_date_service, mock_decimal_service, mock_integer_service,
            mock_text_service, mock_time_service):
        """Create a FastAPI test application with values routers."""
        app = FastAPI()
        
        # Patch dependency injection to use mock services
        with patch("uno.values.domain_endpoints.get_service") as mock_get_service:
            # Configure the mock to return appropriate service based on type
            def get_service_side_effect(service_type):
                if service_type == AttachmentService:
                    return mock_attachment_service
                elif service_type == BooleanValueService:
                    return mock_boolean_service
                elif service_type == DateTimeValueService:
                    return mock_datetime_service
                elif service_type == DateValueService:
                    return mock_date_service
                elif service_type == DecimalValueService:
                    return mock_decimal_service
                elif service_type == IntegerValueService:
                    return mock_integer_service
                elif service_type == TextValueService:
                    return mock_text_service
                elif service_type == TimeValueService:
                    return mock_time_service
                return None
                
            mock_get_service.side_effect = get_service_side_effect
            
            # Register routers with the app
            register_values_endpoints(app)
            
            yield app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    # TextValue endpoint tests
    
    def test_create_text_value_success(self, client, mock_text_service):
        """Test creating a text value successfully."""
        # Arrange
        new_text_value = TextValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )
        mock_text_service.create.return_value = Success(new_text_value)
        
        # Act
        response = client.post(
            "/api/values/texts",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": TEST_TEXT_VALUE
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        assert response.json()["value"] == TEST_TEXT_VALUE
        mock_text_service.create.assert_called_once()

    def test_create_text_value_validation_error(self, client, mock_text_service):
        """Test creating a text value with validation error."""
        # Arrange
        error_msg = "Value must be a string"
        mock_text_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/values/texts",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": 42  # Not a string
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_text_service.create.assert_called_once()

    def test_get_text_value_by_id_success(self, client, mock_text_service):
        """Test getting a text value by ID successfully."""
        # Arrange
        text_value = TextValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )
        mock_text_service.get_by_id.return_value = Success(text_value)
        
        # Act
        response = client.get(f"/api/values/texts/{TEST_VALUE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        assert response.json()["value"] == TEST_TEXT_VALUE
        mock_text_service.get_by_id.assert_called_once_with(TEST_VALUE_ID)

    def test_get_text_value_by_id_not_found(self, client, mock_text_service):
        """Test getting a text value by ID when not found."""
        # Arrange
        mock_text_service.get_by_id.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/values/texts/{TEST_VALUE_ID}")
        
        # Assert
        assert response.status_code == 404
        mock_text_service.get_by_id.assert_called_once_with(TEST_VALUE_ID)

    def test_update_text_value_success(self, client, mock_text_service):
        """Test updating a text value successfully."""
        # Arrange
        updated_text_value = TextValue(
            id=TEST_VALUE_ID,
            name="Updated Value",
            value="Updated text value"
        )
        mock_text_service.update.return_value = Success(updated_text_value)
        
        # Act
        response = client.patch(
            f"/api/values/texts/{TEST_VALUE_ID}",
            json={
                "name": "Updated Value",
                "value": "Updated text value"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == "Updated Value"
        assert response.json()["value"] == "Updated text value"
        mock_text_service.update.assert_called_once()

    def test_delete_text_value_success(self, client, mock_text_service):
        """Test deleting a text value successfully."""
        # Arrange
        text_value = TextValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )
        mock_text_service.delete.return_value = Success(text_value)
        
        # Act
        response = client.delete(f"/api/values/texts/{TEST_VALUE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        mock_text_service.delete.assert_called_once_with(TEST_VALUE_ID)

    def test_list_text_values_success(self, client, mock_text_service):
        """Test listing text values successfully."""
        # Arrange
        text_values = [
            TextValue(id="value1", name="Value 1", value="Text 1"),
            TextValue(id="value2", name="Value 2", value="Text 2")
        ]
        mock_text_service.list.return_value = Success(text_values)
        
        # Act
        response = client.get("/api/values/texts")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == "value1"
        assert response.json()[1]["id"] == "value2"
        mock_text_service.list.assert_called_once()

    def test_search_text_values_success(self, client, mock_text_service):
        """Test searching text values successfully."""
        # Arrange
        search_term = "test"
        text_values = [
            TextValue(id="value1", name="Test Value 1", value="Test text 1"),
            TextValue(id="value2", name="Test Value 2", value="Test text 2")
        ]
        mock_text_service.search.return_value = Success(text_values)
        
        # Act
        response = client.get(f"/api/values/texts/search?term={search_term}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_text_service.search.assert_called_once_with(search_term, None)

    # IntegerValue endpoint tests
    
    def test_create_integer_value_success(self, client, mock_integer_service):
        """Test creating an integer value successfully."""
        # Arrange
        new_integer_value = IntegerValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_INTEGER_VALUE
        )
        mock_integer_service.create.return_value = Success(new_integer_value)
        
        # Act
        response = client.post(
            "/api/values/integers",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": TEST_INTEGER_VALUE
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        assert response.json()["value"] == TEST_INTEGER_VALUE
        mock_integer_service.create.assert_called_once()

    def test_create_integer_value_validation_error(self, client, mock_integer_service):
        """Test creating an integer value with validation error."""
        # Arrange
        error_msg = "Value must be an integer"
        mock_integer_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/values/integers",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": "not an integer"  # Not an integer
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_integer_service.create.assert_called_once()

    # BooleanValue endpoint tests
    
    def test_create_boolean_value_success(self, client, mock_boolean_service):
        """Test creating a boolean value successfully."""
        # Arrange
        new_boolean_value = BooleanValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_BOOLEAN_VALUE
        )
        mock_boolean_service.create.return_value = Success(new_boolean_value)
        
        # Act
        response = client.post(
            "/api/values/booleans",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": TEST_BOOLEAN_VALUE
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        assert response.json()["value"] == TEST_BOOLEAN_VALUE
        mock_boolean_service.create.assert_called_once()

    # DateTimeValue endpoint tests
    
    def test_create_datetime_value_success(self, client, mock_datetime_service):
        """Test creating a datetime value successfully."""
        # Arrange
        new_datetime_value = DateTimeValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_DATETIME_VALUE
        )
        mock_datetime_service.create.return_value = Success(new_datetime_value)
        
        # Act
        response = client.post(
            "/api/values/datetimes",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": TEST_DATETIME_VALUE.isoformat()
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        # The datetime is returned as an ISO string
        mock_datetime_service.create.assert_called_once()

    # DateValue endpoint tests
    
    def test_create_date_value_success(self, client, mock_date_service):
        """Test creating a date value successfully."""
        # Arrange
        new_date_value = DateValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_DATE_VALUE
        )
        mock_date_service.create.return_value = Success(new_date_value)
        
        # Act
        response = client.post(
            "/api/values/dates",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": TEST_DATE_VALUE.isoformat()
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        # The date is returned as an ISO string
        mock_date_service.create.assert_called_once()

    # TimeValue endpoint tests
    
    def test_create_time_value_success(self, client, mock_time_service):
        """Test creating a time value successfully."""
        # Arrange
        new_time_value = TimeValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TIME_VALUE
        )
        mock_time_service.create.return_value = Success(new_time_value)
        
        # Act
        response = client.post(
            "/api/values/times",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": TEST_TIME_VALUE.isoformat()
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        # The time is returned as an ISO string
        mock_time_service.create.assert_called_once()

    # DecimalValue endpoint tests
    
    def test_create_decimal_value_success(self, client, mock_decimal_service):
        """Test creating a decimal value successfully."""
        # Arrange
        new_decimal_value = DecimalValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_DECIMAL_VALUE
        )
        mock_decimal_service.create.return_value = Success(new_decimal_value)
        
        # Act
        response = client.post(
            "/api/values/decimals",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "value": float(TEST_DECIMAL_VALUE)
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        # The decimal is converted to a float for JSON
        assert float(response.json()["value"]) == float(TEST_DECIMAL_VALUE)
        mock_decimal_service.create.assert_called_once()

    # Attachment endpoint tests
    
    def test_create_attachment_success(self, client, mock_attachment_service):
        """Test creating an attachment successfully."""
        # Arrange
        new_attachment = Attachment(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            file_path=TEST_FILE_PATH
        )
        mock_attachment_service.create.return_value = Success(new_attachment)
        
        # Act
        response = client.post(
            "/api/values/attachments",
            json={
                "id": TEST_VALUE_ID,
                "name": TEST_VALUE_NAME,
                "file_path": TEST_FILE_PATH
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_VALUE_ID
        assert response.json()["name"] == TEST_VALUE_NAME
        assert response.json()["file_path"] == TEST_FILE_PATH
        mock_attachment_service.create.assert_called_once()

    def test_get_attachments_by_file_path_success(self, client, mock_attachment_service):
        """Test getting attachments by file path successfully."""
        # Arrange
        file_path = TEST_FILE_PATH
        encoded_path = urllib.parse.quote(file_path, safe='')
        
        attachments = [
            Attachment(id="attach1", name="Attachment 1", file_path=file_path),
            Attachment(id="attach2", name="Attachment 2", file_path=file_path)
        ]
        mock_attachment_service.find_by_file_path.return_value = Success(attachments)
        
        # Act
        response = client.get(f"/api/values/attachments/by-path/{encoded_path}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["file_path"] == file_path
        assert response.json()[1]["file_path"] == file_path
        mock_attachment_service.find_by_file_path.assert_called_once()