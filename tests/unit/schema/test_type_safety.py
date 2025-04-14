# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for type safety improvements.

These tests verify that type annotations and validations work correctly
in the improved schema and validation infrastructure.
"""

import pytest
from typing import Dict, List, Optional, Type, Any, Generic, TypeVar

from pydantic import BaseModel, Field

from uno.schema.schema import UnoSchema, UnoSchemaConfig, PaginatedList
from uno.schema.schema_manager import UnoSchemaManager
from uno.errors import UnoError, ValidationError, ValidationContext


# Test models
class TestModel(BaseModel):
    """Test model for schema tests."""

    __test__ = False  # Prevent pytest from treating this as a test case
    id: str = Field(default="")
    name: str = Field(default="")
    email: str = Field(default="")
    age: int = Field(default=0)


class TestNestedModel(BaseModel):
    """Test model with nested fields for schema tests."""

    __test__ = False
    id: str = Field(default="")
    details: TestModel = Field(default_factory=TestModel)
    tags: List[str] = Field(default_factory=list)


class TestPaginatedList(UnoSchema):
    """Test paginated list schema with validation."""

    items: List[TestModel]
    total: int
    page: int = 1
    page_size: int = 25
    pages: int = 1


class TestListSchema(PaginatedList[TestModel]):
    """Test implementation of the generic PaginatedList."""

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"id": "1", "name": "Test", "email": "test@example.com", "age": 30}
                ],
                "total": 1,
                "page": 1,
                "page_size": 25,
                "pages": 1,
            }
        }


class TestUnoSchemaManager:
    """Tests for the improved UnoSchemaManager."""

    def test_generic_list_schema(self):
        """Test creating a generic list schema."""
        # Create a schema manager
        manager = UnoSchemaManager()

        # Get a list schema for TestModel
        list_schema = manager.get_list_schema(TestModel)

        # Verify that it's a PaginatedList
        assert "items" in list_schema.model_fields
        assert "total" in list_schema.model_fields
        assert "page" in list_schema.model_fields
        assert "page_size" in list_schema.model_fields
        assert "pages" in list_schema.model_fields

        # Check field types using get_args to extract inner type from List[T]
        from typing import get_args, get_origin

        items_field = list_schema.model_fields["items"]
        assert get_origin(items_field.annotation) == list

        # Create a sample list schema instance
        # Convert TestModel to dict for compatibility with the schema
        test_model_dict = TestModel(
            id="1", name="Test", email="test@example.com", age=30
        ).model_dump()

        instance = list_schema(
            items=[test_model_dict], total=1, page=1, page_size=25, pages=1
        )

        # Verify the instance is valid
        assert len(instance.items) == 1
        assert instance.items[0].name == "Test"

    def test_field_annotations(self):
        """Test that UnoSchema field annotations are properly retrieved."""
        # Get field annotations from a schema
        annotations = TestListSchema.get_field_annotations()

        # Check that all fields are present
        assert "items" in annotations
        assert "total" in annotations
        assert "page" in annotations
        assert "page_size" in annotations
        assert "pages" in annotations

        # Verify annotation types
        from typing import get_args, get_origin

        assert get_origin(annotations["items"]) == list
        inner_type = get_args(annotations["items"])[0]
        assert inner_type == TestModel

    def test_schema_field_dict(self):
        """Test creating a field dictionary for a field."""
        # Get a field dictionary
        field_dict = TestListSchema.create_field_dict("items")

        # Check the dictionary contents
        assert field_dict["name"] == "items"
        assert "annotation" in field_dict
        assert field_dict["required"] is True

        # Try with a non-existent field
        with pytest.raises(UnoError) as exc_info:
            TestListSchema.create_field_dict("non_existent")

        assert "Field non_existent not found" in str(exc_info.value)
        assert exc_info.value.error_code == "FIELD_NOT_FOUND"


class TestValidationContext:
    """Tests for the ValidationContext class."""

    def test_validation_context_simple(self):
        """Test basic validation context functionality."""
        # Create a context
        context = ValidationContext("TestEntity")

        # Add an error
        context.add_error("name", "Name is required", "REQUIRED_FIELD")

        # Check that it has errors
        assert context.has_errors()

        # Check error details
        assert len(context.errors) == 1
        assert context.errors[0]["field"] == "name"
        assert context.errors[0]["message"] == "Name is required"
        assert context.errors[0]["error_code"] == "REQUIRED_FIELD"

        # Attempting to raise should throw a ValidationError
        with pytest.raises(ValidationError) as exc_info:
            context.raise_if_errors()

        # Check error details in the exception
        assert "Validation failed for TestEntity" in str(exc_info.value)
        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert len(exc_info.value.validation_errors) == 1

    def test_nested_validation_context(self):
        """Test nested validation contexts for hierarchical validation."""
        # Create a parent context
        parent = ValidationContext("Parent")

        # Add a parent-level error
        parent.add_error("id", "ID is invalid", "INVALID_ID", "123")

        # Create a nested context for a child field
        child = parent.nested("child")

        # Add errors to the child context
        child.add_error("name", "Name is too short", "SHORT_NAME", "A")

        # Create a deeper nested context
        grandchild = child.nested("grandchild")
        grandchild.add_error("type", "Type is invalid", "INVALID_TYPE", "unknown")

        # Check that the parent context has all errors
        assert len(parent.errors) == 3

        # Verify field paths are correctly constructed
        assert parent.errors[0]["field"] == "id"
        assert parent.errors[1]["field"] == "child.name"
        assert parent.errors[2]["field"] == "child.grandchild.type"

        # Raising from any context should include all errors
        with pytest.raises(ValidationError) as exc_info:
            child.raise_if_errors()

        assert len(exc_info.value.validation_errors) == 3
