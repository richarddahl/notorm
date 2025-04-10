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

        # Create a schema
        with patch.object(config, "create_schema") as mock_create:
            mock_schema = MagicMock()
            mock_create.return_value = mock_schema

            schema = manager.create_schema("test", TestModel)

            # Verify the schema was created and stored
            mock_create.assert_called_once_with(schema_name="test", model=TestModel)
            assert schema == mock_schema
            assert "test" in manager.schemas
            assert manager.schemas["test"] == mock_schema

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
        assert hasattr(include_schema, "id")
        assert hasattr(include_schema, "name")
        assert not hasattr(include_schema, "email")
        assert not hasattr(include_schema, "age")

        # Check exclude_schema has all except excluded fields
        assert hasattr(exclude_schema, "id")
        assert hasattr(exclude_schema, "name")
        assert not hasattr(exclude_schema, "email")
        assert not hasattr(exclude_schema, "age")

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
        config1 = UnoSchemaConfig()
        config2 = UnoSchemaConfig()
        manager.add_schema_config("config1", config1)
        manager.add_schema_config("config2", config2)

        # Mock the create_schema method
        with patch.object(manager, "create_schema") as mock_create:
            mock_schema1 = MagicMock()
            mock_schema2 = MagicMock()
            mock_create.side_effect = [mock_schema1, mock_schema2]

            # Create all schemas
            schemas = manager.create_all_schemas(TestModel)

            # Verify create_schema was called for each config
            assert mock_create.call_count == 2
            mock_create.assert_any_call("config1", TestModel)
            mock_create.assert_any_call("config2", TestModel)

            # Verify schemas dictionary was populated
            assert len(schemas) == 2
            assert schemas["config1"] == mock_schema1
            assert schemas["config2"] == mock_schema2

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

        assert hasattr(view_schema, "id")
        assert hasattr(view_schema, "name")
        assert hasattr(view_schema, "age")
        assert not hasattr(view_schema, "email")

        assert hasattr(edit_schema, "id")
        assert hasattr(edit_schema, "name")
        assert hasattr(edit_schema, "email")
        assert hasattr(edit_schema, "age")

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
