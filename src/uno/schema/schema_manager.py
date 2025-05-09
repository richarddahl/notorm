# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema management component for Domain entities and data models.

This module provides functionality for creating and managing schemas for domain entities,
SQLAlchemy models, and data transfer objects (DTOs) used in the Uno framework.
"""

from typing import Dict, Type, Optional, Any, Set, TypeVar, cast, get_origin, get_args, List
import inspect
from collections.abc import Mapping

from pydantic import BaseModel, create_model, Field
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.declarative import DeclarativeMeta

from uno.schema.errors import (
    SchemaErrorCode,
    SchemaNotFoundError,
    SchemaInvalidError,
    SchemaFieldMissingError,
    SchemaFieldTypeMismatchError,
    SchemaConversionError
)
from uno.dto import UnoDTO, DTOConfig, PaginatedListDTO
from uno.core.errors.base import UnoError


# Type variables for improved type safety
ModelT = TypeVar('ModelT', bound=BaseModel)
T = TypeVar('T')


class UnoSchemaManager:
    """
    Manager for creating and managing schemas for domain entities and data models.
    
    This class handles:
    - Creating Pydantic schemas from various source types
    - Configuring field inclusion/exclusion
    - Generating list schemas for paginated responses
    - Managing schema registrations for API documentation
    """

    def __init__(self, schema_configs: Optional[Dict[str, DTOConfig]] = None):
        """
        Initialize the schema manager.

        Args:
            schema_configs: Optional initial schema configurations
        """
        self.schema_configs: Dict[str, DTOConfig] = schema_configs or {}
        self.schemas: Dict[str, Type[UnoDTO]] = {}

    def add_schema_config(self, name: str, config: DTOConfig) -> None:
        """
        Add a schema configuration.

        Args:
            name: The name of the schema configuration
            config: The schema configuration to add
        """
        self.schema_configs[name] = config

    def create_schema(
        self, schema_name: str, model: Type[BaseModel]
    ) -> Type[UnoDTO]:
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
        schema = schema_config.create_dto(
            dto_name=schema_name,
            model=model,
        )

        self.schemas[schema_name] = schema
        return schema

    def create_all_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[UnoDTO]]:
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

    def get_schema(self, schema_name: str) -> Optional[Type[UnoDTO]]:
        """
        Get a schema by name.

        Args:
            schema_name: The name of the schema to get

        Returns:
            The schema if found, None otherwise
        """
        return self.schemas.get(schema_name)
        
    def get_list_schema(self, model: Type[Any]) -> Type[UnoDTO]:
        """
        Get or create a schema for lists of the given model.
        
        This method returns a schema suitable for representing lists of items,
        typically used for API list endpoints. It handles both Pydantic models
        and SQLAlchemy models like UnoModel.
        
        Args:
            model: The model to create a list schema for (can be BaseModel or UnoModel)
            
        Returns:
            A schema class for lists of the given model
            
        Raises:
            UnoError: If there are issues with the schema creation
        """
        # Use a standard naming convention for list schemas
        schema_name = f"{model.__name__}_list"
        
        # Check if the schema already exists
        if schema_name in self.schemas:
            return self.schemas[schema_name]
            
        # If not, check if we have a config for this list type
        if schema_name in self.schema_configs:
            return self.create_schema(schema_name, model)
            
        # Determine if this is a SQLAlchemy model
        is_sqlalchemy_model = isinstance(model, type) and hasattr(model, '__tablename__')
        
        # Create the base item schema
        if is_sqlalchemy_model:
            # Create a Pydantic model from SQLAlchemy model
            base_schema = self._create_schema_from_sqlalchemy_model(model)
        else:
            # For Pydantic models, get or create a detail schema
            base_schema = self._get_or_create_detail_schema(model)
        
        # Create the list schema using the PaginatedListDTO generic
        list_schema_name = f"{model.__name__}ListDTO"
        # Create a specialized list schema as a subclass of PaginatedListDTO
        # Use a different approach to create the list schema to avoid mypy issues
        from typing import cast
        
        # Create a list schema directly without using PaginatedListDTO[T]
        # mypy has issues with create_model and variable types, so we use type: ignore
        item_type = Any  # Default type for mypy
        if isinstance(base_schema, type):
            item_type = base_schema
            
        list_schema = create_model(  # type: ignore
            list_schema_name,
            __base__=UnoDTO,
            items=(List[item_type], ...),  # type: ignore
            total=(int, ...),
            page=(int, 1),
            page_size=(int, 25),
            pages=(int, 1)
        )
        
        # Cast to ensure the type system recognizes it correctly
        typed_list_schema = cast(Type[UnoDTO], list_schema)
        
        # Store the created schema
        self.schemas[schema_name] = typed_list_schema
        return typed_list_schema
    
    def _create_schema_from_sqlalchemy_model(self, model: Type[Any]) -> Type[UnoDTO]:
        """
        Create a Pydantic schema from a SQLAlchemy model.
        
        Args:
            model: The SQLAlchemy model to create a schema from
            
        Returns:
            A Pydantic schema for the model
        """
        # Get the mapper for this model class
        mapper = sa_inspect(model)
        
        # Get column info
        fields = {}
        for column in mapper.columns:
            # Convert SQLAlchemy types to Python types
            python_type = self._get_python_type_for_column(column)
            
            # Add the field with an appropriate default value
            fields[column.name] = (
                python_type, 
                None if column.nullable else ...
            )
        
        # Create a new Pydantic model based on the SQLAlchemy model
        # mypy has issues with create_model, so we use type: ignore
        schema = create_model(  # type: ignore
            f"{model.__name__}DTO",
            __base__=UnoDTO,
            **fields
        )
        
        return cast(Type[UnoDTO], schema)
    
    def _get_python_type_for_column(self, column: Any) -> Type[Any]:
        """
        Get the Python type for a SQLAlchemy column.
        
        Args:
            column: The SQLAlchemy column
            
        Returns:
            The Python type for the column
        """
        # Default to string if we can't determine the type
        python_type: Type[Any] = str
        
        try:
            if hasattr(column, "type") and hasattr(column.type, "python_type"):
                column_python_type = column.type.python_type
                if column_python_type == int:
                    python_type = int
                elif column_python_type == bool:
                    python_type = bool
                elif column_python_type == float:
                    python_type = float
                elif column_python_type == dict:
                    python_type = Dict[str, Any]
                elif column_python_type == list:
                    python_type = List[Any]
        except (AttributeError, TypeError):
            # Fall back to string if we can't determine the type
            python_type = str
            
        return python_type
    
    def _get_or_create_detail_schema(self, model: Type[BaseModel]) -> Type[UnoDTO]:
        """
        Get or create a detail schema for a Pydantic model.
        
        Args:
            model: The Pydantic model to create a schema for
            
        Returns:
            A schema for the model
        """
        # Try different schema names
        base_schema_name = f"{model.__name__}_detail"
        base_schema = self.get_schema(base_schema_name)
        
        if base_schema is None:
            # If no detail schema exists, try to create it
            if base_schema_name in self.schema_configs:
                base_schema = self.create_schema(base_schema_name, model)
            else:
                # Try to use the default schema
                default_schema_name = "default"
                if default_schema_name in self.schema_configs:
                    base_schema = self.create_schema(default_schema_name, model)
                else:
                    # Create a simple detail schema config with all fields
                    detail_config = DTOConfig()
                    self.add_schema_config(base_schema_name, detail_config)
                    base_schema = self.create_schema(base_schema_name, model)
        
        return base_schema


# Global schema manager instance (deprecated, using DTOManager internally)
_schema_manager: Optional[UnoSchemaManager] = None


def get_schema_manager() -> UnoSchemaManager:
    """
    DEPRECATED: This function is maintained for backward compatibility.
    Please use get_dto_manager() from uno.dto instead.
    
    Get the global schema manager instance.
    
    This function returns the global schema manager instance, creating it
    if it doesn't exist yet.
    
    Returns:
        The global schema manager instance
    """
    from uno.dto import get_dto_manager
    
    global _schema_manager
    
    if _schema_manager is None:
        _schema_manager = UnoSchemaManager()
        
    return _schema_manager