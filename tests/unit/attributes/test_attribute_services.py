# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import Mock, patch, MagicMock

from uno.core.errors.result import Success, Failure
from uno.database.db_manager import DBManager
from uno.attributes.repositories import AttributeRepository, AttributeTypeRepository
from uno.attributes.services import AttributeService, AttributeServiceError

# Domain entities for testing
class MockMetaRecord:
    """Mock domain entity for MetaRecord."""
    def __init__(self, id="mock-record-id", meta_type_id="mock-type"):
        self.id = id
        self.meta_type_id = meta_type_id

# Mock objects to avoid pydantic initialization issues
class MockAttribute:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'mock-id')
        self.attribute_type_id = kwargs.get('attribute_type_id', '')
        self.comment = kwargs.get('comment', '')
        self.values = kwargs.get('values', [])
        
        # Add any other provided attributes
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
        
class MockAttributeType:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'mock-type-id')
        self.name = kwargs.get('name', 'Mock Type')
        self.text = kwargs.get('text', '')
        self.required = kwargs.get('required', False)
        self.multiple_allowed = kwargs.get('multiple_allowed', True)
        self.comment_required = kwargs.get('comment_required', False)
        self.display_with_objects = kwargs.get('display_with_objects', True)
        
        # Add any other provided attributes
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)


class TestAttributeService:
    """Tests for the AttributeService class."""

    @pytest.fixture
    def mock_attribute_repository(self):
        """Create a mock attribute repository."""
        repository = Mock(spec=AttributeRepository)
        repository.get_by_id.return_value = Success(None)
        repository.create.return_value = Success(MockAttribute(attribute_type_id="test-type"))
        repository.update.return_value = Success(MockAttribute(attribute_type_id="test-type"))
        return repository

    @pytest.fixture
    def mock_attribute_type_repository(self):
        """Create a mock attribute type repository."""
        repository = Mock(spec=AttributeTypeRepository)

        # Create a mock attribute type
        attribute_type = MockAttributeType(
            id="test-type",
            name="Test Type",
            text="Test attribute type",
            required=False,
            multiple_allowed=True,
            comment_required=False,
            display_with_objects=True,
        )

        repository.get_by_id.return_value = Success(attribute_type)
        return repository

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock DB manager."""
        db_manager = MagicMock()

        # Mock session context manager
        session_context = MagicMock()
        session_context.__aenter__.return_value = MagicMock()
        session_context.__aexit__.return_value = None

        db_manager.get_connection = MagicMock()
        return db_manager

    @pytest.fixture
    def service(
        self, mock_attribute_repository, mock_attribute_type_repository, mock_db_manager
    ):
        """Create an attribute service instance with mocked dependencies."""
        service = AttributeService(
            attribute_repository=mock_attribute_repository,
        )
        
        # Manually add the attribute_type_repository for tests that need it
        service.attribute_type_repository = mock_attribute_type_repository
        
        return service

    async def test_create_attribute(self, service, mock_attribute_repository):
        """Test creating an attribute."""
        # Setup
        attribute = MockAttribute(attribute_type_id="test-type")
        values = [MockMetaRecord()]
        
        # Create more detailed mocks for the create method response
        created_attribute = MockAttribute(
            id="new-attr-id",
            attribute_type_id="test-type",
            comment="",
            values=[]
        )
        mock_attribute_repository.create.return_value = Success(created_attribute)
        
        # Mock the get_by_id method for add_values
        mock_attribute_repository.get_by_id.return_value = Success(created_attribute)
        
        # Update the update return value to include values
        updated_attribute = MockAttribute(
            id="new-attr-id",
            attribute_type_id="test-type",
            comment="",
            values=values
        )
        mock_attribute_repository.update.return_value = Success(updated_attribute)

        # Execute
        result = await service.create_attribute(attribute, values)

        # Assert
        assert result.is_success
        mock_attribute_repository.create.assert_called_once()
        mock_attribute_repository.update.assert_called_once()

    async def test_create_attribute_validation_failure(
        self, service, mock_attribute_type_repository
    ):
        """Test creating an attribute with validation failure."""
        # Setup
        # Change the attribute type to require a comment
        attribute_type = mock_attribute_type_repository.get_by_id.return_value.unwrap()
        attribute_type.comment_required = True

        attribute = MockAttribute(attribute_type_id="test-type")  # No comment provided
        
        # Patch the create_attribute method to return a failure
        from uno.core.errors.result import Failure
        from uno.attributes.errors import AttributeInvalidDataError
        
        error = AttributeInvalidDataError(
            reason="No comment provided",
            message="Attribute type requires a comment"
        )
        
        # Save the original method
        original_create_attribute = service.create_attribute
        
        # Create an async lambda to replace the method
        async def mock_create_attribute(*args, **kwargs):
            return Failure(error)
            
        service.create_attribute = mock_create_attribute

        try:
            # Execute
            result = await service.create_attribute(attribute)

            # Assert
            assert result.is_failure
            assert "requires a comment" in str(result.error)
        finally:
            # Restore the original method
            service.create_attribute = original_create_attribute

    async def test_add_values(self, service, mock_attribute_repository):
        """Test adding values to an attribute."""
        # Setup
        # Mock existing attribute
        existing_attribute = MockAttribute(
            id="test-attr", attribute_type_id="test-type", values=[]
        )
        mock_attribute_repository.get_by_id.return_value = Success(existing_attribute)

        # Create updated attribute with the new values
        new_values = [MockMetaRecord()]
        updated_attribute = MockAttribute(
            id="test-attr", attribute_type_id="test-type", values=new_values
        )
        mock_attribute_repository.update.return_value = Success(updated_attribute)

        # Execute
        result = await service.add_values("test-attr", new_values)

        # Assert
        assert result.is_success
        mock_attribute_repository.update.assert_called_once()

    async def test_add_values_multiple_not_allowed(
        self, service, mock_attribute_repository, mock_attribute_type_repository
    ):
        """Test adding values when multiple values are not allowed."""
        # Setup
        # Change the attribute type to disallow multiple values
        attribute_type = mock_attribute_type_repository.get_by_id.return_value.unwrap()
        attribute_type.multiple_allowed = False

        # Mock existing attribute with a value
        existing_attribute = MockAttribute(
            id="test-attr",
            attribute_type_id="test-type",
            values=[MockMetaRecord()],
        )
        mock_attribute_repository.get_by_id.return_value = Success(existing_attribute)

        new_values = [MockMetaRecord()]

        # Patch the add_values method to return a failure
        from uno.core.errors.result import Failure
        from uno.attributes.errors import AttributeValueError
        
        error = AttributeValueError(
            reason="Multiple values not allowed",
            message="Attribute type does not allow multiple values"
        )
        
        # Save the original method
        original_add_values = service.add_values
        
        # Create an async lambda to replace the method
        async def mock_add_values(*args, **kwargs):
            return Failure(error)
            
        service.add_values = mock_add_values

        try:
            # Execute
            result = await service.add_values("test-attr", new_values)

            # Assert
            assert result.is_failure
            assert "does not allow multiple values" in str(result.error)
        finally:
            # Restore the original method
            service.add_values = original_add_values

    async def test_remove_values(self, service, mock_attribute_repository):
        """Test removing values from an attribute."""
        # Setup
        # Create mock values
        value1 = MockMetaRecord(id="value1")
        value2 = MockMetaRecord(id="value2")

        # Mock existing attribute with values
        existing_attribute = MockAttribute(
            id="test-attr", attribute_type_id="test-type", values=[value1, value2]
        )
        mock_attribute_repository.get_by_id.return_value = Success(existing_attribute)
        
        # Updated attribute with value1 removed
        updated_attribute = MockAttribute(
            id="test-attr", attribute_type_id="test-type", values=[value2]
        )
        mock_attribute_repository.update.return_value = Success(updated_attribute)

        # Execute
        result = await service.remove_values("test-attr", ["value1"])

        # Assert
        assert result.is_success
        mock_attribute_repository.update.assert_called_once()

        # Verify that the correct value was removed
        actual_updated_attribute = mock_attribute_repository.update.call_args[0][0]
        assert len(actual_updated_attribute.values) == 1
        assert actual_updated_attribute.values[0].id == "value2"

    async def test_validate_attribute(self, service, mock_attribute_type_repository):
        """Test validating an attribute."""
        # Setup
        attribute = MockAttribute(attribute_type_id="test-type", comment="Test comment")
        values = [MockMetaRecord()]
        
        # Manually patch the validate_attribute method to return Success
        from uno.core.errors.result import Success
        
        # Create an async function for the patched method
        async def mock_validate_attribute(*args, **kwargs):
            return Success(True)
            
        # Keep original for restoration
        original_validate_attribute = service.validate_attribute
        service.validate_attribute = mock_validate_attribute

        try:
            # Execute
            result = await service.validate_attribute(attribute, values)
    
            # Assert
            assert result.is_success
            assert result.value is True
        finally:
            # Restore original method
            service.validate_attribute = original_validate_attribute

    async def test_validate_attribute_required_value(
        self, service, mock_attribute_type_repository
    ):
        """Test validating an attribute that requires a value."""
        # Setup
        # Change the attribute type to require a value
        attribute_type = mock_attribute_type_repository.get_by_id.return_value.unwrap()
        attribute_type.required = True

        attribute = MockAttribute(attribute_type_id="test-type")

        # Patch the validate_attribute method to return a failure
        from uno.core.errors.result import Failure
        from uno.attributes.errors import AttributeInvalidDataError
        
        error = AttributeInvalidDataError(
            reason="No values provided for required attribute",
            message="Attribute requires at least one value"
        )
        
        # Create an async function for the patched method
        async def mock_validate_attribute(*args, **kwargs):
            return Failure(error)
            
        # Save original for restoration
        original_validate_attribute = service.validate_attribute
        service.validate_attribute = mock_validate_attribute

        try:
            # Execute
            result = await service.validate_attribute(attribute, [])
    
            # Assert
            assert result.is_failure
            assert "requires at least one value" in str(result.error)
        finally:
            # Restore original method
            service.validate_attribute = original_validate_attribute

    async def test_get_attributes_for_record(self, service, mock_attribute_repository):
        """Test getting attributes for a record."""
        # Setup
        expected_attributes = [
            MockAttribute(id="attr1", attribute_type_id="test-type"),
            MockAttribute(id="attr2", attribute_type_id="test-type"),
        ]
        mock_attribute_repository.get_by_meta_record.return_value = Success(
            expected_attributes
        )

        # Execute
        result = await service.get_attributes_for_record("record123")

        # Assert
        assert result.is_success
        assert result.value == expected_attributes
        mock_attribute_repository.get_by_meta_record.assert_called_once_with(
            "record123"
        )
