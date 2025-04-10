# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the schema manager module.

These tests verify the functionality of the UnoSchemaManager class, ensuring
it correctly manages schema configurations and creates schemas for models.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Optional

from pydantic import BaseModel, Field

from uno.schema.schema_manager import UnoSchemaManager
from uno.schema.schema import UnoSchema, UnoSchemaConfig
from uno.errors import UnoError


class TestModel(BaseModel):
    """Test model for schema tests."""

    __test__ = False  # Prevent pytest from treating this as a test case
    id: str = Field(default="")
    name: str = Field(default="")
    email: str = Field(default="")
    age: int = Field(default=0)


class TestPartialSchema(UnoSchema):
    """Test schema base class with only some fields."""

    __test__ = False  # Prevent pytest from treating this as a test case

    id: str
    name: str


class TestUnoSchemaManager:
    """Tests for the UnoSchemaManager class."""

    def test_initialization(self):
        """Test initialization of the schema manager."""
        # Create a schema manager without configs
        manager = UnoSchemaManager()
        assert manager.schema_configs == {}
        assert manager.schemas == {}

        # Create a schema manager with configs
        config = UnoSchemaConfig()
        manager = UnoSchemaManager(schema_configs={"test": config})
        assert "test" in manager.schema_configs
        assert manager.schemas == {}

    def test_add_schema_config(self):
        """Test adding a schema configuration."""
        manager = UnoSchemaManager()
        config = UnoSchemaConfig()

        # Add a schema config
        manager.add_schema_config("test", config)

        # Verify it was added
        assert "test" in manager.schema_configs
        assert manager.schema_configs["test"] == config

        # Add another config and verify both exist
        another_config = UnoSchemaConfig(schema_base=TestPartialSchema)
        manager.add_schema_config("another_test", another_config)
        assert "test" in manager.schema_configs
        assert "another_test" in manager.schema_configs
        assert manager.schema_configs["another_test"] == another_config

    def test_create_schema(self):
        """Test creating a schema for a model."""
        manager = UnoSchemaManager()
        config = UnoSchemaConfig()
        manager.add_schema_config("test", config)

        # Create a schema directly without mocking
        schema = manager.create_schema("test", TestModel)

        # Verify the schema was created and stored
        assert schema is not None
        assert "test" in manager.schemas
        assert manager.schemas["test"] == schema
        assert "id" in schema.model_fields
        assert "name" in schema.model_fields
        assert "email" in schema.model_fields
        assert "age" in schema.model_fields

    def test_create_schema_with_real_schema(self):
        """Test creating a real schema (not mocked)."""
        manager = UnoSchemaManager()

        # Add configs with include fields and exclude fields
        include_config = UnoSchemaConfig(include_fields={"id", "name"})
        exclude_config = UnoSchemaConfig(exclude_fields={"email", "age"})
        manager.add_schema_config("include_only", include_config)
        manager.add_schema_config("exclude_some", exclude_config)

        # Create schemas
        include_schema = manager.create_schema("include_only", TestModel)
        exclude_schema = manager.create_schema("exclude_some", TestModel)

        # Check include_schema has only specified fields
        assert "id" in include_schema.model_fields
        assert "name" in include_schema.model_fields
        assert "email" not in include_schema.model_fields
        assert "age" not in include_schema.model_fields

        # Check exclude_schema has all except excluded fields
        assert "id" in exclude_schema.model_fields
        assert "name" in exclude_schema.model_fields
        assert "email" not in exclude_schema.model_fields
        assert "age" not in exclude_schema.model_fields

        # Verify schema names follow expected format
        assert include_schema.__name__ == "TestModelInclude"
        assert exclude_schema.__name__ == "TestModelExclude"

    def test_create_schema_not_found(self):
        """Test creating a schema with a non-existent config."""
        manager = UnoSchemaManager()

        # Try to create a schema with a non-existent config
        with pytest.raises(UnoError) as exc_info:
            manager.create_schema("not_found", TestModel)

        # Verify the error
        assert "Schema configuration not_found not found" in str(exc_info.value)
        assert exc_info.value.error_code == "SCHEMA_CONFIG_NOT_FOUND"

    def test_create_all_schemas(self):
        """Test creating all schemas for a model."""
        manager = UnoSchemaManager()
        
        # Add different configs
        config1 = UnoSchemaConfig(include_fields={"id", "name"})
        config2 = UnoSchemaConfig(exclude_fields={"email"})
        manager.add_schema_config("config1", config1)
        manager.add_schema_config("config2", config2)
        
        # Create all schemas directly
        schemas = manager.create_all_schemas(TestModel)
        
        # Verify results
        assert len(schemas) == 2
        assert "config1" in schemas
        assert "config2" in schemas
        assert "id" in schemas["config1"].model_fields
        assert "name" in schemas["config1"].model_fields
        assert "email" not in schemas["config1"].model_fields
        assert "age" not in schemas["config1"].model_fields
        
        assert "id" in schemas["config2"].model_fields
        assert "name" in schemas["config2"].model_fields
        assert "email" not in schemas["config2"].model_fields
        assert "age" in schemas["config2"].model_fields

    def test_create_all_schemas_real(self):
        """Test creating all schemas without mocking."""
        manager = UnoSchemaManager()

        # Add different types of configs
        view_config = UnoSchemaConfig(exclude_fields={"email"})
        edit_config = UnoSchemaConfig()
        manager.add_schema_config("view", view_config)
        manager.add_schema_config("edit", edit_config)

        # Create all schemas
        schemas = manager.create_all_schemas(TestModel)

        # Verify schemas were created correctly
        assert len(schemas) == 2
        assert "view" in schemas
        assert "edit" in schemas

        # Check field differences
        view_schema = schemas["view"]
        edit_schema = schemas["edit"]

        assert "id" in view_schema.model_fields
        assert "name" in view_schema.model_fields
        assert "age" in view_schema.model_fields
        assert "email" not in view_schema.model_fields

        assert "id" in edit_schema.model_fields
        assert "name" in edit_schema.model_fields
        assert "email" in edit_schema.model_fields
        assert "age" in edit_schema.model_fields

    def test_get_schema(self):
        """Test getting a schema by name."""
        manager = UnoSchemaManager()
        mock_schema = MagicMock()
        manager.schemas["test"] = mock_schema

        # Get an existing schema
        schema = manager.get_schema("test")
        assert schema == mock_schema

        # Get a non-existent schema
        schema = manager.get_schema("not_found")
        assert schema is None

    def test_get_schema_after_create(self):
        """Test getting a schema after creating it."""
        manager = UnoSchemaManager()
        config = UnoSchemaConfig()
        manager.add_schema_config("test", config)

        # Create a schema
        created_schema = manager.create_schema("test", TestModel)

        # Get the schema
        retrieved_schema = manager.get_schema("test")

        # Verify the schemas are the same
        assert retrieved_schema == created_schema
