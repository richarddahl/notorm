"""
Tests for the Values module domain components.

This module contains comprehensive tests for the Values module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, date, time, UTC
import decimal
from decimal import Decimal

from uno.core.result import Success, Failure
from uno.values.entities import (
    BaseValue, Attachment, BooleanValue, DateTimeValue, 
    DateValue, DecimalValue, IntegerValue, TextValue, TimeValue
)
from uno.values.domain_repositories import (
    ValueRepository, UnoDBValueRepository,
    AttachmentRepository, BooleanValueRepository, DateTimeValueRepository,
    DateValueRepository, DecimalValueRepository, IntegerValueRepository,
    TextValueRepository, TimeValueRepository
)
from uno.values.domain_services import (
    ValueService, AttachmentService, BooleanValueService, DateTimeValueService,
    DateValueService, DecimalValueService, IntegerValueService,
    TextValueService, TimeValueService
)

# Test Data
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


class TestBaseValueEntity:
    """Tests for the BaseValue domain entity."""

    def test_create_base_value(self):
        """Test creating a base value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        group_id = TEST_GROUP_ID
        tenant_id = TEST_TENANT_ID
        
        # Act
        value = BaseValue(
            id=value_id,
            name=name,
            group_id=group_id,
            tenant_id=tenant_id
        )
        
        # Assert
        assert value.id == value_id
        assert value.name == name
        assert value.group_id == group_id
        assert value.tenant_id == tenant_id

    def test_validate_base_value_valid(self):
        """Test validation with a valid base value."""
        # Arrange
        value = BaseValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME
        )
        
        # Act & Assert
        value.validate()  # Should not raise an exception

    def test_validate_base_value_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        value = BaseValue(
            id=TEST_VALUE_ID,
            name=""  # Empty name
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            value.validate()


class TestAttachmentEntity:
    """Tests for the Attachment domain entity."""

    def test_create_attachment(self):
        """Test creating an attachment entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        file_path = TEST_FILE_PATH
        
        # Act
        attachment = Attachment(
            id=value_id,
            name=name,
            file_path=file_path
        )
        
        # Assert
        assert attachment.id == value_id
        assert attachment.name == name
        assert attachment.file_path == file_path
        assert attachment.__uno_model__ == "AttachmentModel"

    def test_validate_attachment_valid(self):
        """Test validation with a valid attachment."""
        # Arrange
        attachment = Attachment(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            file_path=TEST_FILE_PATH
        )
        
        # Act & Assert
        attachment.validate()  # Should not raise an exception

    def test_validate_attachment_invalid_empty_file_path(self):
        """Test validation with empty file path."""
        # Arrange
        attachment = Attachment(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            file_path=""  # Empty file path
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="File path cannot be empty"):
            attachment.validate()


class TestBooleanValueEntity:
    """Tests for the BooleanValue domain entity."""

    def test_create_boolean_value(self):
        """Test creating a boolean value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_BOOLEAN_VALUE
        
        # Act
        boolean_value = BooleanValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert boolean_value.id == value_id
        assert boolean_value.name == name
        assert boolean_value.value == value
        assert boolean_value.__uno_model__ == "BooleanValueModel"

    def test_validate_boolean_value_valid(self):
        """Test validation with a valid boolean value."""
        # Arrange
        boolean_value = BooleanValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_BOOLEAN_VALUE
        )
        
        # Act & Assert
        boolean_value.validate()  # Should not raise an exception

    def test_validate_boolean_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        boolean_value = BooleanValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value="not a boolean"  # Not a boolean
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be a boolean"):
            boolean_value.validate()


class TestDateTimeValueEntity:
    """Tests for the DateTimeValue domain entity."""

    def test_create_datetime_value(self):
        """Test creating a datetime value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_DATETIME_VALUE
        
        # Act
        datetime_value = DateTimeValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert datetime_value.id == value_id
        assert datetime_value.name == name
        assert datetime_value.value == value
        assert datetime_value.__uno_model__ == "DateTimeValueModel"

    def test_validate_datetime_value_valid(self):
        """Test validation with a valid datetime value."""
        # Arrange
        datetime_value = DateTimeValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_DATETIME_VALUE
        )
        
        # Act & Assert
        datetime_value.validate()  # Should not raise an exception

    def test_validate_datetime_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        datetime_value = DateTimeValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value="not a datetime"  # Not a datetime
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be a datetime"):
            datetime_value.validate()


class TestDateValueEntity:
    """Tests for the DateValue domain entity."""

    def test_create_date_value(self):
        """Test creating a date value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_DATE_VALUE
        
        # Act
        date_value = DateValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert date_value.id == value_id
        assert date_value.name == name
        assert date_value.value == value
        assert date_value.__uno_model__ == "DateValueModel"

    def test_validate_date_value_valid(self):
        """Test validation with a valid date value."""
        # Arrange
        date_value = DateValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_DATE_VALUE
        )
        
        # Act & Assert
        date_value.validate()  # Should not raise an exception

    def test_validate_date_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        date_value = DateValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value="not a date"  # Not a date
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be a date"):
            date_value.validate()


class TestDecimalValueEntity:
    """Tests for the DecimalValue domain entity."""

    def test_create_decimal_value(self):
        """Test creating a decimal value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_DECIMAL_VALUE
        
        # Act
        decimal_value = DecimalValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert decimal_value.id == value_id
        assert decimal_value.name == name
        assert decimal_value.value == value
        assert decimal_value.__uno_model__ == "DecimalValueModel"

    def test_validate_decimal_value_valid(self):
        """Test validation with a valid decimal value."""
        # Arrange
        decimal_value = DecimalValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_DECIMAL_VALUE
        )
        
        # Act & Assert
        decimal_value.validate()  # Should not raise an exception

    def test_validate_decimal_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        decimal_value = DecimalValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value="not a decimal"  # Not a decimal
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be a decimal"):
            decimal_value.validate()


class TestIntegerValueEntity:
    """Tests for the IntegerValue domain entity."""

    def test_create_integer_value(self):
        """Test creating an integer value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_INTEGER_VALUE
        
        # Act
        integer_value = IntegerValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert integer_value.id == value_id
        assert integer_value.name == name
        assert integer_value.value == value
        assert integer_value.__uno_model__ == "IntegerValueModel"

    def test_validate_integer_value_valid(self):
        """Test validation with a valid integer value."""
        # Arrange
        integer_value = IntegerValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_INTEGER_VALUE
        )
        
        # Act & Assert
        integer_value.validate()  # Should not raise an exception

    def test_validate_integer_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        integer_value = IntegerValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value="not an integer"  # Not an integer
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be an integer"):
            integer_value.validate()


class TestTextValueEntity:
    """Tests for the TextValue domain entity."""

    def test_create_text_value(self):
        """Test creating a text value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_TEXT_VALUE
        
        # Act
        text_value = TextValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert text_value.id == value_id
        assert text_value.name == name
        assert text_value.value == value
        assert text_value.__uno_model__ == "TextValueModel"

    def test_validate_text_value_valid(self):
        """Test validation with a valid text value."""
        # Arrange
        text_value = TextValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )
        
        # Act & Assert
        text_value.validate()  # Should not raise an exception

    def test_validate_text_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        text_value = TextValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=42  # Not a string
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be a string"):
            text_value.validate()


class TestTimeValueEntity:
    """Tests for the TimeValue domain entity."""

    def test_create_time_value(self):
        """Test creating a time value entity."""
        # Arrange
        value_id = TEST_VALUE_ID
        name = TEST_VALUE_NAME
        value = TEST_TIME_VALUE
        
        # Act
        time_value = TimeValue(
            id=value_id,
            name=name,
            value=value
        )
        
        # Assert
        assert time_value.id == value_id
        assert time_value.name == name
        assert time_value.value == value
        assert time_value.__uno_model__ == "TimeValueModel"

    def test_validate_time_value_valid(self):
        """Test validation with a valid time value."""
        # Arrange
        time_value = TimeValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TIME_VALUE
        )
        
        # Act & Assert
        time_value.validate()  # Should not raise an exception

    def test_validate_time_value_invalid_type(self):
        """Test validation with an invalid type."""
        # Arrange
        time_value = TimeValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value="not a time"  # Not a time
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Value must be a time"):
            time_value.validate()


# Repository Tests

class TestTextValueRepository:
    """Tests for the TextValueRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a TextValueRepository instance."""
        return TextValueRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a text value by ID successfully."""
        # Arrange
        value_id = TEST_VALUE_ID
        mock_session.get.return_value = TextValue(
            id=value_id,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )

        # Act
        result = await repository.get_by_id(value_id, mock_session)

        # Assert
        assert result.is_success
        text_value = result.value
        assert text_value.id == value_id
        assert text_value.name == TEST_VALUE_NAME
        assert text_value.value == TEST_TEXT_VALUE
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """Test getting a text value by ID when not found."""
        # Arrange
        value_id = "nonexistent"
        mock_session.get.return_value = None

        # Act
        result = await repository.get_by_id(value_id, mock_session)

        # Assert
        assert result.is_success
        assert result.value is None
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name(self, repository, mock_session):
        """Test finding text values by name."""
        # Arrange
        name = TEST_VALUE_NAME
        text_values = [
            TextValue(id="value1", name=name, value="Value 1"),
            TextValue(id="value2", name=name, value="Value 2")
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = text_values

        # Act
        result = await repository.find_by_name(name, mock_session)

        # Assert
        assert len(result) == 2
        assert all(value.name == name for value in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_value(self, repository, mock_session):
        """Test finding text values by value."""
        # Arrange
        value = TEST_TEXT_VALUE
        text_values = [
            TextValue(id="value1", name="Value 1", value=value),
            TextValue(id="value2", name="Value 2", value=value)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = text_values

        # Act
        result = await repository.find_by_value(value, mock_session)

        # Assert
        assert len(result) == 2
        assert all(val.value == value for val in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(self, repository, mock_session):
        """Test searching for text values."""
        # Arrange
        search_text = "test"
        text_values = [
            TextValue(id="value1", name="Test Value 1", value="Test text 1"),
            TextValue(id="value2", name="Test Value 2", value="Test text 2")
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = text_values

        # Act
        result = await repository.search(search_text, mock_session)

        # Assert
        assert len(result) == 2
        mock_session.execute.assert_called_once()


class TestAttachmentRepository:
    """Tests for the AttachmentRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create an AttachmentRepository instance."""
        return AttachmentRepository()

    @pytest.mark.asyncio
    async def test_find_by_file_path(self, repository, mock_session):
        """Test finding attachments by file path."""
        # Arrange
        file_path = TEST_FILE_PATH
        attachments = [
            Attachment(id="attachment1", name="Attachment 1", file_path=file_path),
            Attachment(id="attachment2", name="Attachment 2", file_path=file_path)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = attachments

        # Act
        result = await repository.find_by_file_path(file_path, mock_session)

        # Assert
        assert len(result) == 2
        assert all(attachment.file_path == file_path for attachment in result)
        mock_session.execute.assert_called_once()


# Service Tests

class TestTextValueService:
    """Tests for the TextValueService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=TextValueRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TextValueService instance."""
        return TextValueService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_text_value_success(self, service, mock_repository):
        """Test creating a text value successfully."""
        # Arrange
        text_value = TextValue(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )
        mock_repository.save.return_value = Success(text_value)

        # Act
        result = await service.create(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=TEST_TEXT_VALUE
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_VALUE_ID
        assert result.value.name == TEST_VALUE_NAME
        assert result.value.value == TEST_TEXT_VALUE
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_text_value_validation_error(self, service):
        """Test creating a text value with validation error."""
        # Act - Value with wrong type
        result = await service.create(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            value=42  # Not a string
        )

        # Assert
        assert result.is_failure
        assert "Value must be a string" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_name_success(self, service, mock_repository):
        """Test finding text values by name successfully."""
        # Arrange
        name = TEST_VALUE_NAME
        text_values = [
            TextValue(id="value1", name=name, value="Value 1"),
            TextValue(id="value2", name=name, value="Value 2")
        ]
        mock_repository.find_by_name.return_value = text_values

        # Act
        result = await service.find_by_name(name)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(value.name == name for value in result.value)
        mock_repository.find_by_name.assert_called_once_with(name, None)

    @pytest.mark.asyncio
    async def test_find_by_value_success(self, service, mock_repository):
        """Test finding text values by value successfully."""
        # Arrange
        value = TEST_TEXT_VALUE
        text_values = [
            TextValue(id="value1", name="Value 1", value=value),
            TextValue(id="value2", name="Value 2", value=value)
        ]
        mock_repository.find_by_value.return_value = text_values

        # Act
        result = await service.find_by_value(value)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(val.value == value for val in result.value)
        mock_repository.find_by_value.assert_called_once_with(value, None)

    @pytest.mark.asyncio
    async def test_search_success(self, service, mock_repository):
        """Test searching for text values successfully."""
        # Arrange
        search_text = "test"
        text_values = [
            TextValue(id="value1", name="Test Value 1", value="Test text 1"),
            TextValue(id="value2", name="Test Value 2", value="Test text 2")
        ]
        mock_repository.search.return_value = text_values

        # Act
        result = await service.search(search_text)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        mock_repository.search.assert_called_once_with(search_text, None)


class TestAttachmentService:
    """Tests for the AttachmentService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=AttachmentRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create an AttachmentService instance."""
        return AttachmentService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_attachment_success(self, service, mock_repository):
        """Test creating an attachment successfully."""
        # Arrange
        attachment = Attachment(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            file_path=TEST_FILE_PATH
        )
        mock_repository.save.return_value = Success(attachment)

        # Act
        result = await service.create(
            id=TEST_VALUE_ID,
            name=TEST_VALUE_NAME,
            file_path=TEST_FILE_PATH
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_VALUE_ID
        assert result.value.name == TEST_VALUE_NAME
        assert result.value.file_path == TEST_FILE_PATH
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_file_path_success(self, service, mock_repository):
        """Test finding attachments by file path successfully."""
        # Arrange
        file_path = TEST_FILE_PATH
        attachments = [
            Attachment(id="attachment1", name="Attachment 1", file_path=file_path),
            Attachment(id="attachment2", name="Attachment 2", file_path=file_path)
        ]
        mock_repository.find_by_file_path.return_value = attachments

        # Act
        result = await service.find_by_file_path(file_path)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(attachment.file_path == file_path for attachment in result.value)
        mock_repository.find_by_file_path.assert_called_once_with(file_path, None)