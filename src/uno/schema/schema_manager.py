# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema management component for UnoObj models.

This module provides functionality for creating and managing schemas for UnoObj models.
"""

from typing import Dict, Type, Optional, Any, Set

from pydantic import BaseModel

from uno.errors import UnoError
from uno.schema.schema import UnoSchema, UnoSchemaConfig


class UnoSchemaManager:
    """
    Manager for UnoObj schemas.

    This class handles the creation and management of schemas for UnoObj models.
    """

    def __init__(self, schema_configs: Optional[Dict[str, UnoSchemaConfig]] = None):
        """
        Initialize the schema manager.

        Args:
            schema_configs: Optional initial schema configurations
        """
        self.schema_configs = schema_configs or {}
        self.schemas: Dict[str, Type[UnoSchema]] = {}

    def add_schema_config(self, name: str, config: UnoSchemaConfig) -> None:
        """
        Add a schema configuration.

        Args:
            name: The name of the schema configuration
            config: The schema configuration to add
        """
        self.schema_configs[name] = config

    def create_schema(
        self, schema_name: str, model: Type[BaseModel]
    ) -> Type[UnoSchema]:
        """
        Create a schema for a model.

        Args:
            schema_name: The name of the schema to create
            model: The model to create a schema for

        Returns:
            The created schema class

        Raises:
            UnoError: If the schema configuration is not found or if there are issues
                     with the schema creation
        """
        if schema_name not in self.schema_configs:
            raise UnoError(
                f"Schema configuration {schema_name} not found.",
                "SCHEMA_CONFIG_NOT_FOUND",
            )

        schema_config = self.schema_configs[schema_name]
        schema = schema_config.create_schema(
            schema_name=schema_name,
            model=model,
        )

        self.schemas[schema_name] = schema
        return schema

    def create_all_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[UnoSchema]]:
        """
        Create all schemas for a model.

        Args:
            model: The model to create schemas for

        Returns:
            A dictionary of schema names to schema classes
        """
        for schema_name in self.schema_configs:
            self.create_schema(schema_name, model)
        return self.schemas

    def get_schema(self, schema_name: str) -> Optional[Type[UnoSchema]]:
        """
        Get a schema by name.

        Args:
            schema_name: The name of the schema to get

        Returns:
            The schema if found, None otherwise
        """
        return self.schemas.get(schema_name)
