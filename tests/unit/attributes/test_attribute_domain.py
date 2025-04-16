"""
Tests for the Attributes module domain components.

This module contains comprehensive tests for the Attributes module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from uno.core.result import Success, Failure
from uno.attributes.entities import AttributeType, Attribute, MetaTypeRef, QueryRef
from uno.attributes.domain_repositories import AttributeTypeRepository, AttributeRepository
from uno.attributes.domain_services import AttributeTypeService, AttributeService

# Test Data
TEST_ATTRIBUTE_TYPE_ID = "test_type"
TEST_ATTRIBUTE_ID = "test_attribute"


class TestAttributeTypeEntity:
    """Tests for the AttributeType domain entity."""

    def test_create_attribute_type(self):
        """Test creating an attribute type entity."""
        # Arrange
        attr_type_id = TEST_ATTRIBUTE_TYPE_ID
        name = "Test Type"
        text = "A test attribute type"

        # Act
        attr_type = AttributeType(id=attr_type_id, name=name, text=text)

        # Assert
        assert attr_type.id == attr_type_id
        assert attr_type.name == name
        assert attr_type.text == text
        assert hasattr(attr_type, "children")
        assert isinstance(attr_type.children, list)
        assert len(attr_type.children) == 0
        assert hasattr(attr_type, "describes")
        assert isinstance(attr_type.describes, list)
        assert len(attr_type.describes) == 0
        assert hasattr(attr_type, "value_types")
        assert isinstance(attr_type.value_types, list)
        assert len(attr_type.value_types) == 0

    def test_validate_attribute_type_valid(self):
        """Test validation with valid attribute type."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="Valid Name", text="Valid description")

        # Act & Assert
        attr_type.validate()  # Should not raise an exception

    def test_validate_attribute_type_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="", text="Valid description")

        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            attr_type.validate()

    def test_validate_attribute_type_invalid_empty_text(self):
        """Test validation with empty text."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="Valid Name", text="")

        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            attr_type.validate()

    def test_validate_attribute_type_comment_required_without_initial_comment(self):
        """Test validation when comment is required but initial comment is missing."""
        # Arrange
        attr_type = AttributeType(
            id="valid_id", 
            name="Valid Name", 
            text="Valid description",
            comment_required=True,
            initial_comment=None
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Initial comment is required when comment is required"):
            attr_type.validate()

    def test_add_value_type(self):
        """Test adding a value type to an attribute type."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="Valid Name", text="Valid description")
        meta_type_id = "meta_type_1"
        meta_type_name = "Meta Type 1"

        # Act
        attr_type.add_value_type(meta_type_id, meta_type_name)

        # Assert
        assert len(attr_type.value_types) == 1
        assert attr_type.value_types[0].id == meta_type_id
        assert attr_type.value_types[0].name == meta_type_name

        # Adding the same value type again should not duplicate
        attr_type.add_value_type(meta_type_id, meta_type_name)
        assert len(attr_type.value_types) == 1

    def test_add_describable_type(self):
        """Test adding a describable type to an attribute type."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="Valid Name", text="Valid description")
        meta_type_id = "meta_type_1"
        meta_type_name = "Meta Type 1"

        # Act
        attr_type.add_describable_type(meta_type_id, meta_type_name)

        # Assert
        assert len(attr_type.describes) == 1
        assert attr_type.describes[0].id == meta_type_id
        assert attr_type.describes[0].name == meta_type_name

        # Adding the same describable type again should not duplicate
        attr_type.add_describable_type(meta_type_id, meta_type_name)
        assert len(attr_type.describes) == 1

    def test_can_describe(self):
        """Test can_describe method."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="Valid Name", text="Valid description")
        meta_type_id = "meta_type_1"
        attr_type.add_describable_type(meta_type_id, "Meta Type 1")

        # Act & Assert
        assert attr_type.can_describe(meta_type_id) is True
        assert attr_type.can_describe("unknown_type") is False

    def test_can_have_value_type(self):
        """Test can_have_value_type method."""
        # Arrange
        attr_type = AttributeType(id="valid_id", name="Valid Name", text="Valid description")
        meta_type_id = "meta_type_1"
        attr_type.add_value_type(meta_type_id, "Meta Type 1")

        # Act & Assert
        assert attr_type.can_have_value_type(meta_type_id) is True
        assert attr_type.can_have_value_type("unknown_type") is False


class TestAttributeEntity:
    """Tests for the Attribute domain entity."""

    def test_create_attribute(self):
        """Test creating an attribute entity."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        attribute_type_id = TEST_ATTRIBUTE_TYPE_ID
        comment = "Test comment"

        # Act
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=attribute_type_id,
            comment=comment
        )

        # Assert
        assert attribute.id == attribute_id
        assert attribute.attribute_type_id == attribute_type_id
        assert attribute.comment == comment
        assert attribute.attribute_type is None
        assert hasattr(attribute, "value_ids")
        assert isinstance(attribute.value_ids, list)
        assert len(attribute.value_ids) == 0
        assert hasattr(attribute, "meta_record_ids")
        assert isinstance(attribute.meta_record_ids, list)
        assert len(attribute.meta_record_ids) == 0

    def test_validate_attribute_valid(self):
        """Test validation with valid attribute."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="valid_type")

        # Act & Assert
        attribute.validate()  # Should not raise an exception

    def test_validate_attribute_invalid_empty_type_id(self):
        """Test validation with empty attribute type ID."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="")

        # Act & Assert
        with pytest.raises(ValueError, match="Attribute type ID cannot be empty"):
            attribute.validate()

    def test_validate_attribute_comment_required(self):
        """Test validation when comment is required but missing."""
        # Arrange
        attribute_type = AttributeType(
            id="type_id", 
            name="Type Name", 
            text="Type Text",
            comment_required=True
        )
        attribute = Attribute(
            id="valid_id", 
            attribute_type_id="type_id",
            attribute_type=attribute_type,
            comment=None
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Comment is required for this attribute type"):
            attribute.validate()

    def test_add_value(self):
        """Test adding a value to an attribute."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="valid_type")
        value_id = "value1"

        # Act
        attribute.add_value(value_id)

        # Assert
        assert value_id in attribute.value_ids
        assert len(attribute.value_ids) == 1

        # Add the same value again - should not duplicate
        attribute.add_value(value_id)
        assert len(attribute.value_ids) == 1

    def test_add_value_multiple_not_allowed(self):
        """Test adding multiple values when not allowed."""
        # Arrange
        attribute_type = AttributeType(
            id="type_id", 
            name="Type Name", 
            text="Type Text",
            multiple_allowed=False
        )
        attribute = Attribute(
            id="valid_id", 
            attribute_type_id="type_id",
            attribute_type=attribute_type
        )
        
        # Add first value
        attribute.add_value("value1")
        
        # Act - add second value
        attribute.add_value("value2")
        
        # Assert - should replace the first value, not add to it
        assert len(attribute.value_ids) == 1
        assert "value1" not in attribute.value_ids
        assert "value2" in attribute.value_ids

    def test_add_meta_record(self):
        """Test adding a meta record to an attribute."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="valid_type")
        meta_record_id = "record1"

        # Act
        attribute.add_meta_record(meta_record_id)

        # Assert
        assert meta_record_id in attribute.meta_record_ids
        assert len(attribute.meta_record_ids) == 1

        # Add the same meta record again - should not duplicate
        attribute.add_meta_record(meta_record_id)
        assert len(attribute.meta_record_ids) == 1

    def test_has_values_with_values(self):
        """Test has_values property when values exist."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="valid_type")
        attribute.add_value("value1")

        # Act & Assert
        assert attribute.has_values is True

    def test_has_values_with_meta_records(self):
        """Test has_values property when meta records exist."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="valid_type")
        attribute.add_meta_record("record1")

        # Act & Assert
        assert attribute.has_values is True

    def test_has_values_without_values(self):
        """Test has_values property when no values or meta records exist."""
        # Arrange
        attribute = Attribute(id="valid_id", attribute_type_id="valid_type")

        # Act & Assert
        assert attribute.has_values is False


class TestAttributeTypeRepository:
    """Tests for the AttributeTypeRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create an AttributeTypeRepository instance."""
        return AttributeTypeRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting an attribute type by ID successfully."""
        # Arrange
        attribute_type_id = TEST_ATTRIBUTE_TYPE_ID
        mock_session.get.return_value = AttributeType(
            id=attribute_type_id, 
            name="Test Type", 
            text="Test Description"
        )

        # Act
        result = await repository.get_by_id(attribute_type_id, mock_session)

        # Assert
        assert result.is_success
        attr_type = result.value
        assert attr_type.id == attribute_type_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """Test getting an attribute type by ID when not found."""
        # Arrange
        attribute_type_id = "nonexistent"
        mock_session.get.return_value = None

        # Act
        result = await repository.get_by_id(attribute_type_id, mock_session)

        # Assert
        assert result.is_success
        assert result.value is None
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name(self, repository, mock_session):
        """Test finding attribute type by name."""
        # Arrange
        name = "Test Type"
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            AttributeType(id="type1", name=name, text="Description 1"),
            AttributeType(id="type2", name=name, text="Description 2")
        ]

        # Create a patched version of the list method
        original_list = repository.list
        
        async def mock_list(*args, **kwargs):
            return mock_session.execute.return_value.scalars.return_value.all.return_value
            
        repository.list = mock_list
        
        try:
            # Act
            result = await repository.find_by_name(name)
            
            # Assert
            assert len(result) == 2
            assert all(at.name == name for at in result)
        finally:
            # Restore original method
            repository.list = original_list

    @pytest.mark.asyncio
    async def test_find_by_parent(self, repository, mock_session):
        """Test finding attribute types by parent ID."""
        # Arrange
        parent_id = "parent_type"
        children = [
            AttributeType(id="child1", name="Child 1", text="Description 1", parent_id=parent_id),
            AttributeType(id="child2", name="Child 2", text="Description 2", parent_id=parent_id)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = children

        # Create a patched version of the list method
        original_list = repository.list
        
        async def mock_list(*args, **kwargs):
            return mock_session.execute.return_value.scalars.return_value.all.return_value
            
        repository.list = mock_list
        
        try:
            # Act
            result = await repository.find_by_parent(parent_id)
            
            # Assert
            assert len(result) == 2
            assert all(at.parent_id == parent_id for at in result)
        finally:
            # Restore original method
            repository.list = original_list


class TestAttributeRepository:
    """Tests for the AttributeRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create an AttributeRepository instance."""
        return AttributeRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting an attribute by ID successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        mock_session.get.return_value = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )

        # Act
        result = await repository.get_by_id(attribute_id, mock_session)

        # Assert
        assert result.is_success
        attribute = result.value
        assert attribute.id == attribute_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_attribute_type(self, repository, mock_session):
        """Test finding attributes by attribute type."""
        # Arrange
        attribute_type_id = TEST_ATTRIBUTE_TYPE_ID
        attributes = [
            Attribute(id="attr1", attribute_type_id=attribute_type_id),
            Attribute(id="attr2", attribute_type_id=attribute_type_id)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = attributes

        # Create a patched version of the list method
        original_list = repository.list
        
        async def mock_list(*args, **kwargs):
            return mock_session.execute.return_value.scalars.return_value.all.return_value
            
        repository.list = mock_list
        
        try:
            # Act
            result = await repository.find_by_attribute_type(attribute_type_id)
            
            # Assert
            assert len(result) == 2
            assert all(attr.attribute_type_id == attribute_type_id for attr in result)
        finally:
            # Restore original method
            repository.list = original_list
            
    @pytest.mark.asyncio
    async def test_find_by_meta_record(self, repository):
        """Test finding attributes by meta record."""
        # This is currently a placeholder in the implementation
        # So we'll just verify it returns an empty list
        result = await repository.find_by_meta_record("record1")
        assert isinstance(result, list)
        assert len(result) == 0


class TestAttributeTypeService:
    """Tests for the AttributeTypeService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=AttributeTypeRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create an AttributeTypeService instance."""
        return AttributeTypeService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_attribute_type_success(self, service, mock_repository):
        """Test creating an attribute type successfully."""
        # Arrange
        attr_type = AttributeType(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Test Type", 
            text="Test description"
        )
        mock_repository.save.return_value = Success(attr_type)

        # Act
        result = await service.create(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Test Type", 
            text="Test description"
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_ATTRIBUTE_TYPE_ID
        assert result.value.name == "Test Type"
        assert result.value.text == "Test description"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_attribute_type_validation_error(self, service):
        """Test creating an attribute type with validation error."""
        # Act - Missing required text field
        result = await service.create(
            id=TEST_ATTRIBUTE_TYPE_ID, 
            name="Test Type", 
            text=""
        )

        # Assert
        assert result.is_failure
        assert "Text cannot be empty" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_name_success(self, service, mock_repository):
        """Test finding attribute types by name successfully."""
        # Arrange
        name = "Test Type"
        attr_types = [
            AttributeType(id="type1", name=name, text="Description 1"),
            AttributeType(id="type2", name=name, text="Description 2")
        ]
        mock_repository.find_by_name.return_value = attr_types

        # Act
        result = await service.find_by_name(name)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(at.name == name for at in result.value)
        mock_repository.find_by_name.assert_called_once_with(name, None)

    @pytest.mark.asyncio
    async def test_get_hierarchy_success(self, service, mock_repository):
        """Test getting an attribute type hierarchy successfully."""
        # Arrange
        root_id = "root_type"
        root = AttributeType(id=root_id, name="Root Type", text="Root Description")
        root.children = [
            AttributeType(id="child1", name="Child 1", text="Child Description 1", parent_id=root_id),
            AttributeType(id="child2", name="Child 2", text="Child Description 2", parent_id=root_id)
        ]
        
        mock_repository.get_with_relationships.return_value = root
        
        # Mock the recursive call to get_hierarchy for children
        service.get_hierarchy = AsyncMock(side_effect=[
            Success([root.children[0]]),  # First child result
            Success([root.children[1]])   # Second child result
        ])

        # Act
        result = await service.get_hierarchy(root_id)

        # Assert
        assert result.is_success
        assert len(result.value) == 3  # Root + 2 children
        assert result.value[0].id == root_id
        mock_repository.get_with_relationships.assert_called_once_with(root_id)

    @pytest.mark.asyncio
    async def test_get_hierarchy_not_found(self, service, mock_repository):
        """Test getting a hierarchy when root not found."""
        # Arrange
        root_id = "nonexistent"
        mock_repository.get_with_relationships.return_value = None

        # Act
        result = await service.get_hierarchy(root_id)

        # Assert
        assert result.is_failure
        assert f"Attribute type {root_id} not found" in str(result.error)

    @pytest.mark.asyncio
    async def test_add_value_type_success(self, service, mock_repository):
        """Test adding a value type successfully."""
        # Arrange
        attr_type_id = TEST_ATTRIBUTE_TYPE_ID
        meta_type_id = "meta_type_1"
        
        attr_type = AttributeType(id=attr_type_id, name="Test Type", text="Test Description")
        mock_repository.get.return_value = attr_type
        mock_repository.save.return_value = Success(attr_type)

        # Act
        result = await service.add_value_type(attr_type_id, meta_type_id)

        # Assert
        assert result.is_success
        assert meta_type_id in [vt.id for vt in result.value.value_types]
        mock_repository.get.assert_called_once_with(attr_type_id)
        mock_repository.save.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_add_value_type_not_found(self, service, mock_repository):
        """Test adding a value type to nonexistent attribute type."""
        # Arrange
        attr_type_id = "nonexistent"
        meta_type_id = "meta_type_1"
        
        mock_repository.get.return_value = None

        # Act
        result = await service.add_value_type(attr_type_id, meta_type_id)

        # Assert
        assert result.is_failure
        assert f"Attribute type {attr_type_id} not found" in str(result.error)


class TestAttributeService:
    """Tests for the AttributeService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=AttributeRepository)

    @pytest.fixture
    def mock_type_service(self):
        """Create a mock attribute type service."""
        return AsyncMock(spec=AttributeTypeService)

    @pytest.fixture
    def service(self, mock_repository, mock_type_service):
        """Create an AttributeService instance."""
        service = AttributeService(repository=mock_repository)
        service.attribute_type_service = mock_type_service
        return service

    @pytest.mark.asyncio
    async def test_create_attribute_success(self, service, mock_repository):
        """Test creating an attribute successfully."""
        # Arrange
        attribute = Attribute(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        mock_repository.save.return_value = Success(attribute)

        # Act
        result = await service.create(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_ATTRIBUTE_ID
        assert result.value.attribute_type_id == TEST_ATTRIBUTE_TYPE_ID
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_attribute_validation_error(self, service):
        """Test creating an attribute with validation error."""
        # Act - Missing required attribute_type_id
        result = await service.create(
            id=TEST_ATTRIBUTE_ID, 
            attribute_type_id=""
        )

        # Assert
        assert result.is_failure
        assert "Attribute type ID cannot be empty" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_attribute_type_success(self, service, mock_repository):
        """Test finding attributes by type successfully."""
        # Arrange
        attribute_type_id = TEST_ATTRIBUTE_TYPE_ID
        attributes = [
            Attribute(id="attr1", attribute_type_id=attribute_type_id),
            Attribute(id="attr2", attribute_type_id=attribute_type_id)
        ]
        mock_repository.find_by_attribute_type.return_value = attributes

        # Act
        result = await service.find_by_attribute_type(attribute_type_id)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(attr.attribute_type_id == attribute_type_id for attr in result.value)
        mock_repository.find_by_attribute_type.assert_called_once_with(attribute_type_id)

    @pytest.mark.asyncio
    async def test_get_with_related_data_success(self, service, mock_repository, mock_type_service):
        """Test getting an attribute with related data successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        
        # Set up mocks
        mock_repository.get_with_relationships.return_value = attribute
        
        # Set up the mock attribute type repository to be retrieved
        mock_type_repository = AsyncMock(spec=AttributeTypeRepository)
        mock_type_service.repository = mock_type_repository

        # Act
        result = await service.get_with_related_data(attribute_id)

        # Assert
        assert result.is_success
        assert result.value.id == attribute_id
        mock_repository.get_with_relationships.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_related_data_not_found(self, service, mock_repository):
        """Test getting an attribute with related data when not found."""
        # Arrange
        attribute_id = "nonexistent"
        mock_repository.get_with_relationships.return_value = None

        # Act
        result = await service.get_with_related_data(attribute_id)

        # Assert
        assert result.is_failure
        assert f"Attribute {attribute_id} not found" in str(result.error)

    @pytest.mark.asyncio
    async def test_add_value_success(self, service, mock_repository, mock_type_service):
        """Test adding a value to an attribute successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        value_id = "value1"
        
        # Create attribute with type info
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        
        # Create attribute type
        attr_type = AttributeType(
            id=TEST_ATTRIBUTE_TYPE_ID,
            name="Test Type",
            text="Test Description"
        )
        
        # Set up mocks
        mock_repository.get.return_value = attribute
        mock_repository.save.return_value = Success(attribute)
        mock_type_service.get_by_id.return_value = Success(attr_type)

        # Act
        result = await service.add_value(attribute_id, value_id)

        # Assert
        assert result.is_success
        assert value_id in result.value.value_ids
        mock_repository.get.assert_called_once_with(attribute_id)
        mock_repository.save.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_add_value_attribute_not_found(self, service, mock_repository):
        """Test adding a value to a nonexistent attribute."""
        # Arrange
        attribute_id = "nonexistent"
        value_id = "value1"
        
        mock_repository.get.return_value = None

        # Act
        result = await service.add_value(attribute_id, value_id)

        # Assert
        assert result.is_failure
        assert f"Attribute {attribute_id} not found" in str(result.error)
        
    @pytest.mark.asyncio
    async def test_add_meta_record_success(self, service, mock_repository):
        """Test adding a meta record to an attribute successfully."""
        # Arrange
        attribute_id = TEST_ATTRIBUTE_ID
        meta_record_id = "record1"
        
        attribute = Attribute(
            id=attribute_id, 
            attribute_type_id=TEST_ATTRIBUTE_TYPE_ID
        )
        
        mock_repository.get.return_value = attribute
        mock_repository.save.return_value = Success(attribute)

        # Act
        result = await service.add_meta_record(attribute_id, meta_record_id)

        # Assert
        assert result.is_success
        assert meta_record_id in result.value.meta_record_ids
        mock_repository.get.assert_called_once_with(attribute_id)
        mock_repository.save.assert_called_once()