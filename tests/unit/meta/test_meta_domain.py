"""
Tests for the Meta module domain components.

This module contains comprehensive tests for the Meta module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from uno.core.result import Success, Failure
from uno.meta.entities import MetaType, MetaRecord
from uno.meta.domain_repositories import MetaTypeRepository, MetaRecordRepository
from uno.meta.domain_services import MetaTypeService, MetaRecordService

# Test Data
TEST_META_TYPE_ID = "test_type"
TEST_META_RECORD_ID = "test_record"


class TestMetaTypeEntity:
    """Tests for the MetaType domain entity."""

    def test_create_meta_type(self):
        """Test creating a meta type entity."""
        # Arrange
        meta_type_id = TEST_META_TYPE_ID
        name = "Test Type"
        description = "A test meta type"

        # Act
        meta_type = MetaType(id=meta_type_id, name=name, description=description)

        # Assert
        assert meta_type.id == meta_type_id
        assert meta_type.name == name
        assert meta_type.description == description
        assert hasattr(meta_type, "meta_records")
        assert isinstance(meta_type.meta_records, list)
        assert len(meta_type.meta_records) == 0

    def test_display_name_with_name(self):
        """Test display_name property when name is provided."""
        # Arrange
        meta_type = MetaType(id="user_profile", name="User Profile")

        # Act
        display_name = meta_type.display_name

        # Assert
        assert display_name == "User Profile"

    def test_display_name_without_name(self):
        """Test display_name property when name is not provided."""
        # Arrange
        meta_type = MetaType(id="user_profile")

        # Act
        display_name = meta_type.display_name

        # Assert
        assert display_name == "User Profile"

    def test_validate_meta_type_valid(self):
        """Test validation with valid meta type."""
        # Arrange
        meta_type = MetaType(id="valid_id")

        # Act & Assert
        meta_type.validate()  # Should not raise an exception

    def test_validate_meta_type_invalid_empty_id(self):
        """Test validation with empty ID."""
        # Arrange
        meta_type = MetaType(id="")

        # Act & Assert
        with pytest.raises(ValueError, match="ID cannot be empty"):
            meta_type.validate()

    def test_validate_meta_type_invalid_id_format(self):
        """Test validation with invalid ID format."""
        # Arrange
        meta_type = MetaType(id="Invalid ID!")

        # Act & Assert
        with pytest.raises(ValueError, match="ID must contain only alphanumeric characters and underscores"):
            meta_type.validate()


class TestMetaRecordEntity:
    """Tests for the MetaRecord domain entity."""

    def test_create_meta_record(self):
        """Test creating a meta record entity."""
        # Arrange
        record_id = TEST_META_RECORD_ID
        meta_type_id = TEST_META_TYPE_ID

        # Act
        meta_record = MetaRecord(id=record_id, meta_type_id=meta_type_id)

        # Assert
        assert meta_record.id == record_id
        assert meta_record.meta_type_id == meta_type_id
        assert meta_record.meta_type is None
        assert hasattr(meta_record, "attributes")
        assert isinstance(meta_record.attributes, list)
        assert len(meta_record.attributes) == 0

    def test_validate_meta_record_valid(self):
        """Test validation with valid meta record."""
        # Arrange
        meta_record = MetaRecord(id="valid_id", meta_type_id="valid_type")

        # Act & Assert
        meta_record.validate()  # Should not raise an exception

    def test_validate_meta_record_invalid_empty_id(self):
        """Test validation with empty ID."""
        # Arrange
        meta_record = MetaRecord(id="", meta_type_id="valid_type")

        # Act & Assert
        with pytest.raises(ValueError, match="ID cannot be empty"):
            meta_record.validate()

    def test_validate_meta_record_invalid_empty_type_id(self):
        """Test validation with empty meta type ID."""
        # Arrange
        meta_record = MetaRecord(id="valid_id", meta_type_id="")

        # Act & Assert
        with pytest.raises(ValueError, match="Meta type ID cannot be empty"):
            meta_record.validate()

    def test_add_attribute(self):
        """Test adding an attribute to a meta record."""
        # Arrange
        meta_record = MetaRecord(id="valid_id", meta_type_id="valid_type")
        attribute_id = "attr1"

        # Act
        meta_record.add_attribute(attribute_id)

        # Assert
        assert attribute_id in meta_record.attributes
        assert len(meta_record.attributes) == 1

        # Add the same attribute again - should not duplicate
        meta_record.add_attribute(attribute_id)
        assert len(meta_record.attributes) == 1

    def test_type_name_with_meta_type(self):
        """Test type_name property when meta_type is available."""
        # Arrange
        meta_type = MetaType(id="user_profile", name="User Profile")
        meta_record = MetaRecord(id="user1", meta_type_id="user_profile", meta_type=meta_type)

        # Act
        type_name = meta_record.type_name

        # Assert
        assert type_name == "User Profile"

    def test_type_name_without_meta_type(self):
        """Test type_name property when meta_type is not available."""
        # Arrange
        meta_record = MetaRecord(id="user1", meta_type_id="user_profile")

        # Act
        type_name = meta_record.type_name

        # Assert
        assert type_name == "user_profile"


class TestMetaTypeRepository:
    """Tests for the MetaTypeRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a MetaTypeRepository instance."""
        return MetaTypeRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a meta type by ID successfully."""
        # Arrange
        meta_type_id = TEST_META_TYPE_ID
        mock_session.get.return_value = MetaType(id=meta_type_id, name="Test Type")

        # Act
        result = await repository.get_by_id(meta_type_id, mock_session)

        # Assert
        assert result.is_success
        meta_type = result.value
        assert meta_type.id == meta_type_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """Test getting a meta type by ID when not found."""
        # Arrange
        meta_type_id = "nonexistent"
        mock_session.get.return_value = None

        # Act
        result = await repository.get_by_id(meta_type_id, mock_session)

        # Assert
        assert result.is_success
        assert result.value is None
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name_success(self, repository, mock_session):
        """Test finding meta types by name successfully."""
        # Arrange
        name = "Test Type"
        meta_types = [
            MetaType(id="type1", name=name),
            MetaType(id="type2", name=name)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = meta_types

        # Act
        result = await repository.find_by_name(name, mock_session)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(mt.name == name for mt in result.value)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name_not_found(self, repository, mock_session):
        """Test finding meta types by name when none match."""
        # Arrange
        name = "Nonexistent"
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        # Act
        result = await repository.find_by_name(name, mock_session)

        # Assert
        assert result.is_success
        assert len(result.value) == 0
        mock_session.execute.assert_called_once()


class TestMetaRecordRepository:
    """Tests for the MetaRecordRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a MetaRecordRepository instance."""
        return MetaRecordRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a meta record by ID successfully."""
        # Arrange
        record_id = TEST_META_RECORD_ID
        mock_session.get.return_value = MetaRecord(id=record_id, meta_type_id=TEST_META_TYPE_ID)

        # Act
        result = await repository.get_by_id(record_id, mock_session)

        # Assert
        assert result.is_success
        meta_record = result.value
        assert meta_record.id == record_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_records_for_type_success(self, repository, mock_session):
        """Test getting records for a specific meta type successfully."""
        # Arrange
        meta_type_id = TEST_META_TYPE_ID
        records = [
            MetaRecord(id="record1", meta_type_id=meta_type_id),
            MetaRecord(id="record2", meta_type_id=meta_type_id)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = records

        # Act
        result = await repository.get_records_for_type(meta_type_id, mock_session)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(mr.meta_type_id == meta_type_id for mr in result.value)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_records_for_type_not_found(self, repository, mock_session):
        """Test getting records for a meta type when none exist."""
        # Arrange
        meta_type_id = "nonexistent"
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        # Act
        result = await repository.get_records_for_type(meta_type_id, mock_session)

        # Assert
        assert result.is_success
        assert len(result.value) == 0
        mock_session.execute.assert_called_once()


class TestMetaTypeService:
    """Tests for the MetaTypeService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=MetaTypeRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create a MetaTypeService instance."""
        return MetaTypeService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_meta_type_success(self, service, mock_repository):
        """Test creating a meta type successfully."""
        # Arrange
        meta_type = MetaType(id=TEST_META_TYPE_ID, name="Test Type")
        mock_repository.save.return_value = Success(meta_type)

        # Act
        result = await service.create(id=TEST_META_TYPE_ID, name="Test Type")

        # Assert
        assert result.is_success
        assert result.value.id == TEST_META_TYPE_ID
        assert result.value.name == "Test Type"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_meta_type_validation_error(self, service):
        """Test creating a meta type with validation error."""
        # Act
        result = await service.create(id="Invalid ID!", name="Test Type")

        # Assert
        assert result.is_failure
        assert "ID must contain only alphanumeric characters and underscores" in str(result.error)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_repository):
        """Test getting a meta type by ID successfully."""
        # Arrange
        meta_type = MetaType(id=TEST_META_TYPE_ID, name="Test Type")
        mock_repository.get_by_id.return_value = Success(meta_type)

        # Act
        result = await service.get_by_id(TEST_META_TYPE_ID)

        # Assert
        assert result.is_success
        assert result.value.id == TEST_META_TYPE_ID
        mock_repository.get_by_id.assert_called_once_with(TEST_META_TYPE_ID, None)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service, mock_repository):
        """Test getting a meta type by ID when not found."""
        # Arrange
        mock_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.get_by_id("nonexistent")

        # Assert
        assert result.is_failure
        assert "MetaType with ID 'nonexistent' not found" in str(result.error)
        mock_repository.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name_success(self, service, mock_repository):
        """Test finding meta types by name successfully."""
        # Arrange
        name = "Test Type"
        meta_types = [
            MetaType(id="type1", name=name),
            MetaType(id="type2", name=name)
        ]
        mock_repository.find_by_name.return_value = Success(meta_types)

        # Act
        result = await service.find_by_name(name)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(mt.name == name for mt in result.value)
        mock_repository.find_by_name.assert_called_once_with(name, None)


class TestMetaRecordService:
    """Tests for the MetaRecordService."""

    @pytest.fixture
    def mock_record_repository(self):
        """Create a mock record repository."""
        return AsyncMock(spec=MetaRecordRepository)

    @pytest.fixture
    def mock_type_repository(self):
        """Create a mock type repository."""
        return AsyncMock(spec=MetaTypeRepository)

    @pytest.fixture
    def service(self, mock_record_repository, mock_type_repository):
        """Create a MetaRecordService instance."""
        return MetaRecordService(
            repository=mock_record_repository,
            meta_type_repository=mock_type_repository
        )

    @pytest.mark.asyncio
    async def test_create_meta_record_success(self, service, mock_record_repository, mock_type_repository):
        """Test creating a meta record successfully."""
        # Arrange
        meta_type = MetaType(id=TEST_META_TYPE_ID, name="Test Type")
        mock_type_repository.get_by_id.return_value = Success(meta_type)
        
        meta_record = MetaRecord(id=TEST_META_RECORD_ID, meta_type_id=TEST_META_TYPE_ID)
        mock_record_repository.save.return_value = Success(meta_record)

        # Act
        result = await service.create(id=TEST_META_RECORD_ID, meta_type_id=TEST_META_TYPE_ID)

        # Assert
        assert result.is_success
        assert result.value.id == TEST_META_RECORD_ID
        assert result.value.meta_type_id == TEST_META_TYPE_ID
        mock_type_repository.get_by_id.assert_called_once_with(TEST_META_TYPE_ID, None)
        mock_record_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_meta_record_invalid_type(self, service, mock_type_repository):
        """Test creating a meta record with invalid meta type."""
        # Arrange
        mock_type_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.create(id=TEST_META_RECORD_ID, meta_type_id="nonexistent")

        # Assert
        assert result.is_failure
        assert "MetaType with ID 'nonexistent' not found" in str(result.error)
        mock_type_repository.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_records_for_type_success(self, service, mock_record_repository, mock_type_repository):
        """Test getting records for a meta type successfully."""
        # Arrange
        meta_type = MetaType(id=TEST_META_TYPE_ID, name="Test Type")
        mock_type_repository.get_by_id.return_value = Success(meta_type)
        
        records = [
            MetaRecord(id="record1", meta_type_id=TEST_META_TYPE_ID),
            MetaRecord(id="record2", meta_type_id=TEST_META_TYPE_ID)
        ]
        mock_record_repository.get_records_for_type.return_value = Success(records)

        # Act
        result = await service.get_records_for_type(TEST_META_TYPE_ID)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(mr.meta_type_id == TEST_META_TYPE_ID for mr in result.value)
        mock_type_repository.get_by_id.assert_called_once_with(TEST_META_TYPE_ID, None)
        mock_record_repository.get_records_for_type.assert_called_once_with(TEST_META_TYPE_ID, None)

    @pytest.mark.asyncio
    async def test_get_records_for_type_invalid_type(self, service, mock_type_repository):
        """Test getting records for an invalid meta type."""
        # Arrange
        mock_type_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.get_records_for_type("nonexistent")

        # Assert
        assert result.is_failure
        assert "MetaType with ID 'nonexistent' not found" in str(result.error)
        mock_type_repository.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_attribute_success(self, service, mock_record_repository):
        """Test adding an attribute to a meta record successfully."""
        # Arrange
        meta_record = MetaRecord(id=TEST_META_RECORD_ID, meta_type_id=TEST_META_TYPE_ID)
        mock_record_repository.get_by_id.return_value = Success(meta_record)
        mock_record_repository.save.return_value = Success(meta_record)
        
        attribute_id = "attr1"

        # Act
        result = await service.add_attribute(TEST_META_RECORD_ID, attribute_id)

        # Assert
        assert result.is_success
        assert attribute_id in result.value.attributes
        mock_record_repository.get_by_id.assert_called_once_with(TEST_META_RECORD_ID, None)
        mock_record_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_attribute_record_not_found(self, service, mock_record_repository):
        """Test adding an attribute to a nonexistent meta record."""
        # Arrange
        mock_record_repository.get_by_id.return_value = Success(None)
        
        # Act
        result = await service.add_attribute("nonexistent", "attr1")

        # Assert
        assert result.is_failure
        assert "MetaRecord with ID 'nonexistent' not found" in str(result.error)
        mock_record_repository.get_by_id.assert_called_once()