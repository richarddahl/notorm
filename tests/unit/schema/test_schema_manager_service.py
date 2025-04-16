"""
Tests for the SchemaManagerService.

This module contains tests for the SchemaManagerService, which
is responsible for managing domain entity schemas via dependency injection.
"""

import pytest
from typing import Dict, Type, Optional, Any
from unittest.mock import MagicMock, patch

from pydantic import BaseModel, Field

from uno.schema.schema import UnoSchema, UnoSchemaConfig
from uno.schema.services import SchemaManagerService
from uno.dependencies.interfaces import SchemaManagerProtocol


class TestModel(BaseModel):
    """Test model for schema creation."""

    __test__ = False  # Prevent pytest from collecting this class as a test
    id: str = Field(default="")
    name: str
    display_name: str = Field(default="")
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: int = Field(default=1)
    private_fields: Dict[str, Any] = Field(default_factory=dict)
    password: Optional[str] = None
    secret_key: Optional[str] = None


class TestSchemaManagerService:
    """Tests for SchemaManagerService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = MagicMock()
        self.service = SchemaManagerService(logger=self.logger)

    def test_initialization(self):
        """Test service initialization."""
        assert isinstance(self.service, SchemaManagerService)
        # We can't test Protocol instance checks directly without @runtime_checkable
        # But we can check that the service has all required methods from the Protocol
        for method_name in [
            "add_schema_config",
            "create_schema",
            "create_all_schemas",
            "get_schema",
            "register_standard_configs",
            "create_standard_schemas",
        ]:
            assert hasattr(self.service, method_name)

        assert self.service.schema_configs == {}
        assert self.service.schemas == {}
        assert self.service.logger == self.logger

    def test_add_schema_config(self):
        """Test adding a schema configuration."""
        config = UnoSchemaConfig()
        self.service.add_schema_config("test", config)

        assert "test" in self.service.schema_configs
        assert self.service.schema_configs["test"] == config
        self.logger.debug.assert_called_once()

    def test_create_schema(self):
        """Test creating a schema."""
        # Add a schema config
        config = UnoSchemaConfig()
        self.service.add_schema_config("test", config)

        # Create a schema
        schema = self.service.create_schema("test", TestModel)

        assert "test" in self.service.schemas
        assert self.service.schemas["test"] == schema
        assert issubclass(schema, UnoSchema)
        self.logger.debug.assert_called()

    def test_create_schema_error(self):
        """Test creating a schema with invalid config name."""
        with pytest.raises(ValueError):
            self.service.create_schema("nonexistent", TestModel)

        self.logger.error.assert_called_once()

    def test_create_all_schemas(self):
        """Test creating all schemas."""
        # Add schema configs
        self.service.add_schema_config("test1", UnoSchemaConfig())
        self.service.add_schema_config("test2", UnoSchemaConfig())

        # Create all schemas
        schemas = self.service.create_all_schemas(TestModel)

        assert len(schemas) == 2
        assert "test1" in schemas
        assert "test2" in schemas
        assert issubclass(schemas["test1"], UnoSchema)
        assert issubclass(schemas["test2"], UnoSchema)
        assert (
            self.logger.debug.call_count >= 3
        )  # Initial call + at least 2 create calls

    def test_get_schema(self):
        """Test getting a schema."""
        # Add a schema config and create a schema
        self.service.add_schema_config("test", UnoSchemaConfig())
        schema = self.service.create_schema("test", TestModel)

        # Get the schema
        retrieved_schema = self.service.get_schema("test")

        assert retrieved_schema == schema

        # Test getting a nonexistent schema
        assert self.service.get_schema("nonexistent") is None

    def test_register_standard_configs(self):
        """Test registering standard configs."""
        self.service.register_standard_configs()

        # Check that standard configs are registered
        standard_configs = ["data", "api", "edit", "view", "list"]
        for config_name in standard_configs:
            assert config_name in self.service.schema_configs
            assert isinstance(self.service.schema_configs[config_name], UnoSchemaConfig)

        # Debug is called multiple times, once for the main method and once for each config
        assert self.logger.debug.call_count >= 1

    def test_create_standard_schemas(self):
        """Test creating standard schemas."""
        schemas = self.service.create_standard_schemas(TestModel)

        # Check that standard schemas are created
        standard_schemas = ["data", "api", "edit", "view", "list"]
        for schema_name in standard_schemas:
            assert schema_name in schemas
            assert issubclass(schemas[schema_name], UnoSchema)

        assert (
            self.logger.debug.call_count >= 2
        )  # register configs + create all schemas
