"""
Tests for the Schema domain entities.

This module contains tests for the domain entities in the schema module.
"""

import pytest
from typing import Dict, Any, Optional, List, Set
from pydantic import BaseModel, Field

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.schema.entities import (
    # Value Objects
    SchemaId,
    FieldDefinition,
    SchemaType,
    PaginationParams,
    PaginationMetadata,
    MetadataFields,
    
    # Entities and Aggregates
    SchemaDefinition,
    SchemaConfiguration,
    PaginatedResult,
    
    # API Models
    SchemaCreationRequest,
    SchemaUpdateRequest,
    SchemaValidationRequest,
    ApiSchemaCreationRequest
)


# Test fixtures
@pytest.fixture
def schema_id() -> SchemaId:
    """Create a test schema ID."""
    return SchemaId("test-schema")


@pytest.fixture
def field_definition() -> FieldDefinition:
    """Create a test field definition."""
    return FieldDefinition(
        name="test_field",
        annotation=str,
        description="A test field",
        required=True,
        default=None
    )


class TestPydanticModel(BaseModel):
    """Test Pydantic model for schema tests."""
    id: str = Field(description="The ID")
    name: str = Field(description="The name")
    age: Optional[int] = Field(default=None, description="The age")


class TestValueObjects:
    """Tests for value objects in the schema module."""
    
    def test_schema_id(self):
        """Test SchemaId creation and validation."""
        # Test valid ID
        schema_id = SchemaId("test-schema")
        assert schema_id.value == "test-schema"
        assert str(schema_id) == "test-schema"
        
        # Test invalid (empty) ID
        with pytest.raises(ValueError, match="SchemaId cannot be empty"):
            SchemaId("")
    
    def test_field_definition(self):
        """Test FieldDefinition creation and methods."""
        # Test creation
        field_def = FieldDefinition(
            name="test_field",
            annotation=str,
            description="A test field",
            required=True,
            default="default value"
        )
        
        # Test properties
        assert field_def.name == "test_field"
        assert field_def.annotation == str
        assert field_def.description == "A test field"
        assert field_def.required is True
        assert field_def.default == "default value"
        
        # Test to_dict method
        field_dict = field_def.to_dict()
        assert field_dict["name"] == "test_field"
        assert field_dict["annotation"] == str
        assert field_dict["description"] == "A test field"
        assert field_dict["required"] is True
        assert field_dict["default"] == "default value"
    
    def test_field_definition_from_pydantic_field(self):
        """Test creating a FieldDefinition from a Pydantic field."""
        # Get a field from the test model
        field_info = TestPydanticModel.model_fields["name"]
        
        # Create field definition
        field_def = FieldDefinition.from_pydantic_field("name", field_info)
        
        # Test properties
        assert field_def.name == "name"
        assert field_def.annotation == str
        assert field_def.description == "The name"
        assert field_def.required is True
        assert field_def.default is None
        
        # Test with optional field
        optional_field_info = TestPydanticModel.model_fields["age"]
        optional_field_def = FieldDefinition.from_pydantic_field("age", optional_field_info)
        
        assert optional_field_def.name == "age"
        assert optional_field_def.required is False
        assert optional_field_def.default is None
    
    def test_schema_type_enum(self):
        """Test SchemaType enum values."""
        assert SchemaType.ENTITY.name == "ENTITY"
        assert SchemaType.DTO.name == "DTO"
        assert SchemaType.DETAIL.name == "DETAIL"
        assert SchemaType.LIST.name == "LIST"
        assert SchemaType.CREATE.name == "CREATE"
        assert SchemaType.UPDATE.name == "UPDATE"
        assert SchemaType.CUSTOM.name == "CUSTOM"
    
    def test_pagination_params(self):
        """Test PaginationParams creation and validation."""
        # Test default values
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 25
        
        # Test custom values
        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50
        
        # Test to_dict method
        params_dict = params.to_dict()
        assert params_dict["page"] == 2
        assert params_dict["page_size"] == 50
        
        # Test validation
        with pytest.raises(ValueError, match="Page must be a positive integer"):
            PaginationParams(page=0)
        
        with pytest.raises(ValueError, match="Page size must be a positive integer"):
            PaginationParams(page_size=0)
    
    def test_pagination_metadata(self):
        """Test PaginationMetadata creation and computed properties."""
        # Test with exactly full pages
        metadata = PaginationMetadata(total=50, page=2, page_size=10)
        assert metadata.total == 50
        assert metadata.page == 2
        assert metadata.page_size == 10
        assert metadata.pages == 5
        assert metadata.has_next is True
        assert metadata.has_previous is True
        
        # Test with partial last page
        metadata = PaginationMetadata(total=55, page=2, page_size=10)
        assert metadata.pages == 6
        
        # Test first page
        metadata = PaginationMetadata(total=50, page=1, page_size=10)
        assert metadata.has_next is True
        assert metadata.has_previous is False
        
        # Test last page
        metadata = PaginationMetadata(total=50, page=5, page_size=10)
        assert metadata.has_next is False
        assert metadata.has_previous is True
        
        # Test to_dict method
        metadata_dict = metadata.to_dict()
        assert metadata_dict["total"] == 50
        assert metadata_dict["page"] == 5
        assert metadata_dict["page_size"] == 10
        assert metadata_dict["pages"] == 5
        assert metadata_dict["has_next"] is False
        assert metadata_dict["has_previous"] is True
    
    def test_metadata_fields(self):
        """Test MetadataFields creation and methods."""
        # Test with minimal values
        metadata = MetadataFields()
        assert metadata.created_at is None
        assert metadata.updated_at is None
        assert metadata.version is None
        assert metadata.additional_metadata == {}
        
        # Test with all values
        metadata = MetadataFields(
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-02T00:00:00Z",
            version=1,
            additional_metadata={"key": "value"}
        )
        assert metadata.created_at == "2023-01-01T00:00:00Z"
        assert metadata.updated_at == "2023-01-02T00:00:00Z"
        assert metadata.version == 1
        assert metadata.additional_metadata == {"key": "value"}
        
        # Test to_dict method
        metadata_dict = metadata.to_dict()
        assert metadata_dict["created_at"] == "2023-01-01T00:00:00Z"
        assert metadata_dict["updated_at"] == "2023-01-02T00:00:00Z"
        assert metadata_dict["version"] == 1
        assert metadata_dict["metadata"] == {"key": "value"}
        
        # Test to_dict with no additional metadata
        metadata = MetadataFields(created_at="2023-01-01T00:00:00Z")
        metadata_dict = metadata.to_dict()
        assert "metadata" not in metadata_dict


class TestEntitiesAndAggregates:
    """Tests for entities and aggregates in the schema module."""
    
    def test_schema_definition(self, schema_id: SchemaId, field_definition: FieldDefinition):
        """Test SchemaDefinition creation and methods."""
        # Create schema definition
        schema_def = SchemaDefinition(
            id=schema_id,
            name="Test Schema",
            type=SchemaType.ENTITY,
            description="A test schema"
        )
        
        # Test properties
        assert schema_def.id == schema_id
        assert schema_def.name == "Test Schema"
        assert schema_def.type == SchemaType.ENTITY
        assert schema_def.description == "A test schema"
        assert schema_def.fields == {}
        assert schema_def.base_class is None
        
        # Test add_field
        result = schema_def.add_field(field_definition)
        assert result.is_success() is True
        assert "test_field" in schema_def.fields
        assert schema_def.fields["test_field"] == field_definition
        
        # Test add_field with duplicate field
        result = schema_def.add_field(field_definition)
        assert result.is_success() is False
        assert result.error.code == "SCHEMA_FIELD_ALREADY_EXISTS"
        
        # Test get_field
        result = schema_def.get_field("test_field")
        assert result.is_success() is True
        assert result.value == field_definition
        
        # Test get_field with non-existent field
        result = schema_def.get_field("non_existent")
        assert result.is_success() is False
        assert result.error.code == "SCHEMA_FIELD_NOT_FOUND"
        
        # Test update_field
        updated_field = FieldDefinition(
            name="test_field",
            annotation=int,
            description="Updated field",
            required=False,
            default=0
        )
        result = schema_def.update_field(updated_field)
        assert result.is_success() is True
        assert schema_def.fields["test_field"] == updated_field
        
        # Test update_field with non-existent field
        non_existent_field = FieldDefinition(
            name="non_existent",
            annotation=str,
            description="Non-existent field"
        )
        result = schema_def.update_field(non_existent_field)
        assert result.is_success() is False
        assert result.error.code == "SCHEMA_FIELD_NOT_FOUND"
        
        # Test remove_field
        result = schema_def.remove_field("test_field")
        assert result.is_success() is True
        assert "test_field" not in schema_def.fields
        
        # Test remove_field with non-existent field
        result = schema_def.remove_field("non_existent")
        assert result.is_success() is False
        assert result.error.code == "SCHEMA_FIELD_NOT_FOUND"
        
        # Test to_dict method
        schema_def.add_field(field_definition)  # Add back the field
        schema_dict = schema_def.to_dict()
        assert schema_dict["id"] == "test-schema"
        assert schema_dict["name"] == "Test Schema"
        assert schema_dict["type"] == "ENTITY"
        assert schema_dict["description"] == "A test schema"
        assert "test_field" in schema_dict["fields"]
    
    def test_schema_definition_from_pydantic_model(self):
        """Test creating a SchemaDefinition from a Pydantic model."""
        # Create schema definition
        schema_def = SchemaDefinition.from_pydantic_model(TestPydanticModel, SchemaType.DTO)
        
        # Test properties
        assert schema_def.id.value == "TestPydanticModelSchema"
        assert schema_def.name == "TestPydanticModel"
        assert schema_def.type == SchemaType.DTO
        assert schema_def.base_class == TestPydanticModel
        
        # Test fields
        assert "id" in schema_def.fields
        assert "name" in schema_def.fields
        assert "age" in schema_def.fields
        
        # Check field details
        id_field = schema_def.fields["id"]
        assert id_field.name == "id"
        assert id_field.annotation == str
        assert id_field.description == "The ID"
        assert id_field.required is True
        
        age_field = schema_def.fields["age"]
        assert age_field.name == "age"
        assert age_field.annotation == Optional[int]
        assert age_field.description == "The age"
        assert age_field.required is False
    
    def test_schema_configuration(self):
        """Test SchemaConfiguration creation and validation."""
        # Test default values
        config = SchemaConfiguration()
        assert config.schema_base == BaseModel
        assert config.exclude_fields == set()
        assert config.include_fields == set()
        
        # Test custom values
        config = SchemaConfiguration(
            schema_base=TestPydanticModel,
            exclude_fields={"age"}
        )
        assert config.schema_base == TestPydanticModel
        assert config.exclude_fields == {"age"}
        assert config.include_fields == set()
        
        # Test validation success
        result = config.validate()
        assert result.is_success() is True
        
        # Test validation failure
        config = SchemaConfiguration(
            exclude_fields={"id"},
            include_fields={"name"}
        )
        result = config.validate()
        assert result.is_success() is False
        assert result.error.code == "INVALID_SCHEMA_CONFIG"
        assert "Cannot specify both include_fields and exclude_fields" in result.error.message
        
        # Test to_dict method
        config = SchemaConfiguration(
            schema_base=TestPydanticModel,
            exclude_fields={"id", "age"}
        )
        config_dict = config.to_dict()
        assert config_dict["schema_base"] == "TestPydanticModel"
        assert sorted(config_dict["exclude_fields"]) == ["age", "id"]
        assert config_dict["include_fields"] == []
    
    def test_paginated_result(self):
        """Test PaginatedResult creation and methods."""
        # Create test items
        items = [
            TestPydanticModel(id="1", name="Test 1"),
            TestPydanticModel(id="2", name="Test 2"),
            TestPydanticModel(id="3", name="Test 3")
        ]
        
        # Create metadata
        metadata = PaginationMetadata(total=10, page=1, page_size=3)
        
        # Create paginated result
        paginated = PaginatedResult(items=items, metadata=metadata)
        
        # Test properties
        assert paginated.items == items
        assert paginated.metadata == metadata
        
        # Test to_dict method
        result_dict = paginated.to_dict()
        assert "items" in result_dict
        assert len(result_dict["items"]) == 3
        assert result_dict["total"] == 10
        assert result_dict["page"] == 1
        assert result_dict["page_size"] == 3
        assert result_dict["pages"] == 4
        assert result_dict["has_next"] is True
        assert result_dict["has_previous"] is False


class TestAPIModels:
    """Tests for API models in the schema module."""
    
    def test_schema_creation_request(self):
        """Test SchemaCreationRequest model."""
        # Create valid request
        request = SchemaCreationRequest(
            name="TestSchema",
            type="ENTITY",
            description="Test schema",
            fields={
                "id": {"annotation": "str", "description": "ID field"},
                "name": {"annotation": "str", "description": "Name field"}
            }
        )
        
        # Test properties
        assert request.name == "TestSchema"
        assert request.type == "ENTITY"
        assert request.description == "Test schema"
        assert "id" in request.fields
        assert "name" in request.fields
        assert request.exclude_fields == []
        assert request.include_fields == []
        
        # Test validation - can't have both include and exclude fields
        with pytest.raises(ValueError, match="Cannot specify both include_fields and exclude_fields"):
            SchemaCreationRequest(
                name="TestSchema",
                type="ENTITY",
                fields={},
                include_fields=["id"],
                exclude_fields=["name"]
            )
    
    def test_schema_update_request(self):
        """Test SchemaUpdateRequest model."""
        # Create request
        request = SchemaUpdateRequest(
            description="Updated description",
            fields_to_add={
                "new_field": {"annotation": "str", "description": "New field"}
            },
            fields_to_update={
                "existing_field": {"description": "Updated description"}
            },
            fields_to_remove=["old_field"]
        )
        
        # Test properties
        assert request.description == "Updated description"
        assert "new_field" in request.fields_to_add
        assert "existing_field" in request.fields_to_update
        assert "old_field" in request.fields_to_remove
    
    def test_schema_validation_request(self):
        """Test SchemaValidationRequest model."""
        # Create request
        request = SchemaValidationRequest(
            data={"id": "1", "name": "Test"},
            schema_id="test-schema"
        )
        
        # Test properties
        assert request.data == {"id": "1", "name": "Test"}
        assert request.schema_id == "test-schema"
    
    def test_api_schema_creation_request(self):
        """Test ApiSchemaCreationRequest model."""
        # Create request
        request = ApiSchemaCreationRequest(
            entity_name="TestEntity",
            fields={
                "id": {"annotation": "str", "description": "ID field"},
                "name": {"annotation": "str", "description": "Name field"}
            }
        )
        
        # Test properties
        assert request.entity_name == "TestEntity"
        assert "id" in request.fields
        assert "name" in request.fields
        assert request.create_list_schema is True
        assert request.create_detail_schema is True
        assert request.create_create_schema is True
        assert request.create_update_schema is True
        
        # Test with custom boolean values
        request = ApiSchemaCreationRequest(
            entity_name="TestEntity",
            fields={},
            create_list_schema=False,
            create_detail_schema=True,
            create_create_schema=False,
            create_update_schema=True
        )
        
        assert request.create_list_schema is False
        assert request.create_detail_schema is True
        assert request.create_create_schema is False
        assert request.create_update_schema is True