# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the schema module.

These tests verify the functionality of the UnoSchema and UnoSchemaConfig classes,
ensuring they correctly validate and create schema configurations.
"""

import pytest
from typing import Set, Optional

from pydantic import BaseModel, Field, ValidationError

from uno.schema.schema import UnoSchema, UnoSchemaConfig
from uno.core.errors.base import UnoError


class TestModel(BaseModel):
    """Test model for schema tests."""

    __test__ = False  # Prevent pytest from treating this as a test case
    id: str = Field(default="")
    name: str = Field(default="")
    email: str = Field(default="")
    age: int = Field(default=0)


class CustomSchema(UnoSchema):
    """Custom schema for testing."""

    custom_field: str = Field(default="")


class TestUnoSchema:
    """Tests for the UnoSchema class."""

    def test_basic_schema(self):
        """Test basic schema definition."""
        # Create a schema instance
        schema = UnoSchema()
        assert isinstance(schema, BaseModel)

        # Verify schema fields
        assert schema.model_fields == {}

    def test_schema_inheritance(self):
        """Test schema inheritance."""
        # Create a schema instance from a derived class
        schema = CustomSchema()
        assert isinstance(schema, UnoSchema)
        assert isinstance(schema, BaseModel)

        # Verify schema fields
        assert "custom_field" in schema.model_fields
        assert schema.custom_field == ""


class TestUnoSchemaConfig:
    """Tests for the UnoSchemaConfig class."""

    def test_default_config(self):
        """Test default schema configuration."""
        config = UnoSchemaConfig()

        # Verify default values
        assert config.schema_base == UnoSchema
        assert config.exclude_fields == set()
        assert config.include_fields == set()

    def test_custom_config(self):
        """Test custom schema configuration."""
        config = UnoSchemaConfig(
            schema_base=CustomSchema, exclude_fields={"email", "age"}
        )

        # Verify custom values
        assert config.schema_base == CustomSchema
        assert config.exclude_fields == {"email", "age"}
        assert config.include_fields == set()

    def test_validate_both_exclude_include(self):
        """Test validation fails when both exclude and include fields are specified."""
        # Try to create a config with both exclude and include fields
        with pytest.raises(UnoError) as exc_info:
            UnoSchemaConfig(exclude_fields={"name"}, include_fields={"id"})

        # Verify the error
        assert "cannot have both exclude_fields or include_fields" in str(
            exc_info.value
        )
        assert exc_info.value.error_code == "BOTH_EXCLUDE_INCLUDE_FIELDS"

    def test_create_schema_with_include_fields(self):
        """Test creating a schema with include fields."""
        config = UnoSchemaConfig(include_fields={"id", "name"})

        # Create a schema
        schema_class = config.create_schema("view", TestModel)

        # Verify schema fields
        assert "id" in schema_class.model_fields
        assert "name" in schema_class.model_fields
        assert "email" not in schema_class.model_fields
        assert "age" not in schema_class.model_fields

        # Verify schema name
        assert schema_class.__name__ == "TestModelView"

    def test_create_schema_with_exclude_fields(self):
        """Test creating a schema with exclude fields."""
        config = UnoSchemaConfig(exclude_fields={"email", "age"})

        # Create a schema
        schema_class = config.create_schema("edit", TestModel)

        # Verify schema fields
        assert "id" in schema_class.model_fields
        assert "name" in schema_class.model_fields
        assert "email" not in schema_class.model_fields
        assert "age" not in schema_class.model_fields

        # Verify schema name
        assert schema_class.__name__ == "TestModelEdit"

    def test_create_schema_with_custom_base(self):
        """Test creating a schema with a custom base class."""
        config = UnoSchemaConfig(
            schema_base=CustomSchema, include_fields={"id", "name"}
        )

        # Create a schema
        schema_class = config.create_schema("view", TestModel)

        # Verify schema inherits from custom base
        assert issubclass(schema_class, CustomSchema)

        # Verify schema has base class fields plus included fields
        schema = schema_class()
        assert hasattr(schema, "custom_field")
        assert hasattr(schema, "id")
        assert hasattr(schema, "name")
        assert not hasattr(schema, "email")
        assert not hasattr(schema, "age")

    def test_create_schema_invalid_include_fields(self):
        """Test creating a schema with invalid include fields."""
        config = UnoSchemaConfig(include_fields={"id", "invalid_field"})

        # Try to create a schema with invalid include fields
        with pytest.raises(UnoError) as exc_info:
            config.create_schema("view", TestModel)

        # Verify the error
        assert "Include fields not found in model" in str(exc_info.value)
        assert "invalid_field" in str(exc_info.value)
        assert exc_info.value.error_code == "INCLUDE_FIELD_NOT_IN_MODEL"

    def test_create_schema_invalid_exclude_fields(self):
        """Test creating a schema with invalid exclude fields."""
        config = UnoSchemaConfig(exclude_fields={"invalid_field"})

        # Try to create a schema with invalid exclude fields
        with pytest.raises(UnoError) as exc_info:
            config.create_schema("view", TestModel)

        # Verify the error
        assert "Exclude fields not found in model" in str(exc_info.value)
        assert "invalid_field" in str(exc_info.value)
        assert exc_info.value.error_code == "EXCLUDE_FIELD_NOT_IN_MODEL"

    def test_create_schema_no_fields(self):
        """Test creating a schema with no fields after filtering."""
        # Create a config that would exclude all fields
        config = UnoSchemaConfig(exclude_fields={"id", "name", "email", "age"})

        # Try to create a schema with no fields
        with pytest.raises(UnoError) as exc_info:
            config.create_schema("view", TestModel)

        # Verify the error
        assert "No fields specified for schema" in str(exc_info.value)
        assert exc_info.value.error_code == "NO_FIELDS_SPECIFIED"

    def test_schema_fields_with_exclude_attribute(self):
        """Test handling of fields with exclude=True attribute."""

        class ModelWithExcludedField(BaseModel):
            """Model with a field that has exclude=True."""

            id: str = Field(default="")
            name: str = Field(default="")
            internal: str = Field(default="", exclude=True)

        config = UnoSchemaConfig()

        # Create a schema
        schema_class = config.create_schema("view", ModelWithExcludedField)

        # Verify excluded field is not in schema
        assert "id" in schema_class.model_fields
        assert "name" in schema_class.model_fields
        assert "internal" not in schema_class.model_fields
