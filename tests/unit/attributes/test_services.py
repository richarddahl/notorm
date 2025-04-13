# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import Mock, patch, MagicMock

from uno.core.errors.result import Ok, Err
from uno.database.db_manager import DBManager
from uno.attributes.repositories import AttributeRepository, AttributeTypeRepository
from uno.attributes.services import AttributeService, AttributeServiceError
from uno.attributes.objs import Attribute, AttributeType
from uno.meta.objs import MetaRecord


class TestAttributeService:
    """Tests for the AttributeService class."""

    @pytest.fixture
    def mock_attribute_repository(self):
        """Create a mock attribute repository."""
        repository = Mock(spec=AttributeRepository)
        repository.get_by_id.return_value = Ok(None)
        repository.create.return_value = Ok(Attribute(attribute_type_id="test-type"))
        repository.update.return_value = Ok(Attribute(attribute_type_id="test-type"))
        return repository

    @pytest.fixture
    def mock_attribute_type_repository(self):
        """Create a mock attribute type repository."""
        repository = Mock(spec=AttributeTypeRepository)
        
        # Create a mock attribute type
        attribute_type = AttributeType(
            id="test-type",
            name="Test Type",
            text="Test attribute type",
            required=False,
            multiple_allowed=True,
            comment_required=False,
            display_with_objects=True
        )
        
        repository.get_by_id.return_value = Ok(attribute_type)
        return repository

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock DB manager."""
        db_manager = Mock(spec=DBManager)
        
        # Mock session context manager
        session_context = MagicMock()
        session_context.__aenter__.return_value = MagicMock()
        session_context.__aexit__.return_value = None
        
        db_manager.get_enhanced_session.return_value = session_context
        return db_manager

    @pytest.fixture
    def service(self, mock_attribute_repository, mock_attribute_type_repository, mock_db_manager):
        """Create an attribute service instance with mocked dependencies."""
        return AttributeService(
            attribute_repository=mock_attribute_repository,
            attribute_type_repository=mock_attribute_type_repository,
            db_manager=mock_db_manager
        )

    async def test_create_attribute(self, service, mock_attribute_repository):
        """Test creating an attribute."""
        # Setup
        attribute = Attribute(attribute_type_id="test-type")
        values = [Mock(spec=MetaRecord)]
        
        # Execute
        result = await service.create_attribute(attribute, values)
        
        # Assert
        assert result.is_ok()
        mock_attribute_repository.create.assert_called_once()

    async def test_create_attribute_validation_failure(self, service, mock_attribute_type_repository):
        """Test creating an attribute with validation failure."""
        # Setup
        # Change the attribute type to require a comment
        attribute_type = mock_attribute_type_repository.get_by_id.return_value.unwrap()
        attribute_type.comment_required = True
        
        attribute = Attribute(attribute_type_id="test-type")  # No comment provided
        
        # Execute
        result = await service.create_attribute(attribute)
        
        # Assert
        assert result.is_err()
        assert "requires a comment" in str(result.unwrap_err())

    async def test_add_values(self, service, mock_attribute_repository):
        """Test adding values to an attribute."""
        # Setup
        # Mock existing attribute
        existing_attribute = Attribute(
            id="test-attr",
            attribute_type_id="test-type",
            values=[]
        )
        mock_attribute_repository.get_by_id.return_value = Ok(existing_attribute)
        
        new_values = [Mock(spec=MetaRecord)]
        
        # Execute
        result = await service.add_values("test-attr", new_values)
        
        # Assert
        assert result.is_ok()
        mock_attribute_repository.update.assert_called_once()

    async def test_add_values_multiple_not_allowed(self, service, mock_attribute_repository, mock_attribute_type_repository):
        """Test adding values when multiple values are not allowed."""
        # Setup
        # Change the attribute type to disallow multiple values
        attribute_type = mock_attribute_type_repository.get_by_id.return_value.unwrap()
        attribute_type.multiple_allowed = False
        
        # Mock existing attribute with a value
        existing_attribute = Attribute(
            id="test-attr",
            attribute_type_id="test-type",
            values=[Mock(spec=MetaRecord)]
        )
        mock_attribute_repository.get_by_id.return_value = Ok(existing_attribute)
        
        new_values = [Mock(spec=MetaRecord)]
        
        # Execute
        result = await service.add_values("test-attr", new_values)
        
        # Assert
        assert result.is_err()
        assert "does not allow multiple values" in str(result.unwrap_err())

    async def test_remove_values(self, service, mock_attribute_repository):
        """Test removing values from an attribute."""
        # Setup
        # Create mock values
        value1 = Mock(spec=MetaRecord)
        value1.id = "value1"
        value2 = Mock(spec=MetaRecord)
        value2.id = "value2"
        
        # Mock existing attribute with values
        existing_attribute = Attribute(
            id="test-attr",
            attribute_type_id="test-type",
            values=[value1, value2]
        )
        mock_attribute_repository.get_by_id.return_value = Ok(existing_attribute)
        
        # Execute
        result = await service.remove_values("test-attr", ["value1"])
        
        # Assert
        assert result.is_ok()
        mock_attribute_repository.update.assert_called_once()
        
        # Verify that the correct value was removed
        updated_attribute = mock_attribute_repository.update.call_args[0][0]
        assert len(updated_attribute.values) == 1
        assert updated_attribute.values[0].id == "value2"

    async def test_validate_attribute(self, service, mock_attribute_type_repository):
        """Test validating an attribute."""
        # Setup
        attribute = Attribute(
            attribute_type_id="test-type",
            comment="Test comment"
        )
        values = [Mock(spec=MetaRecord)]
        
        # Execute
        result = await service.validate_attribute(attribute, values)
        
        # Assert
        assert result.is_ok()
        assert result.unwrap() is True

    async def test_validate_attribute_required_value(self, service, mock_attribute_type_repository):
        """Test validating an attribute that requires a value."""
        # Setup
        # Change the attribute type to require a value
        attribute_type = mock_attribute_type_repository.get_by_id.return_value.unwrap()
        attribute_type.required = True
        
        attribute = Attribute(attribute_type_id="test-type")
        
        # Execute
        result = await service.validate_attribute(attribute, [])
        
        # Assert
        assert result.is_err()
        assert "requires at least one value" in str(result.unwrap_err())

    async def test_get_attributes_for_record(self, service, mock_attribute_repository):
        """Test getting attributes for a record."""
        # Setup
        expected_attributes = [
            Attribute(id="attr1", attribute_type_id="test-type"),
            Attribute(id="attr2", attribute_type_id="test-type")
        ]
        mock_attribute_repository.get_by_meta_record.return_value = Ok(expected_attributes)
        
        # Execute
        result = await service.get_attributes_for_record("record123")
        
        # Assert
        assert result.is_ok()
        assert result.unwrap() == expected_attributes
        mock_attribute_repository.get_by_meta_record.assert_called_once_with("record123", None)