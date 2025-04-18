# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
DTO management for Domain entities and data models.

This module provides functionality for creating and managing DTOs for domain entities,
SQLAlchemy models, and data transfer objects (DTOs) used in the Uno framework.
"""

from typing import (
    Dict,
    Type,
    Optional,
    Any,
    Set,
    TypeVar,
    cast,
    List,
)
import inspect
from collections.abc import Mapping

from pydantic import BaseModel, create_model, Field
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.declarative import DeclarativeMeta

from uno.core.base.error import BaseError
from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO


# Type variables for improved type safety
ModelT = TypeVar("ModelT", bound=BaseModel)
T = TypeVar("T")


class DTOManager:
    """
    Manager for creating and managing DTOs for domain entities and data models.

    This class handles:
    - Creating Pydantic DTOs from various source types
    - Configuring field inclusion/exclusion
    - Generating list DTOs for paginated responses
    - Managing DTO registrations for API documentation
    """

    def __init__(self, dto_configs: Optional[Dict[str, DTOConfig]] = None):
        """
        Initialize the DTO manager.

        Args:
            dto_configs: Optional initial DTO configurations
        """
        self.dto_configs: Dict[str, DTOConfig] = dto_configs or {}
        self.dtos: Dict[str, Type[BaseDTO]] = {}

    def add_dto_config(self, name: str, config: DTOConfig) -> None:
        """
        Add a DTO configuration.

        Args:
            name: The name of the DTO configuration
            config: The DTO configuration to add
        """
        self.dto_configs[name] = config

    def create_dto(self, dto_name: str, model: Type[BaseModel]) -> Type[BaseDTO]:
        """
        Create a DTO for a model.

        Args:
            dto_name: The name of the DTO to create
            model: The model to create a DTO for

        Returns:
            The created DTO class

        Raises:
            BaseError: If the DTO configuration is not found or if there are issues
                    with the DTO creation
        """
        if dto_name not in self.dto_configs:
            raise BaseError(
                f"DTO configuration {dto_name} not found.",
                "DTO_CONFIG_NOT_FOUND",
            )

        dto_config = self.dto_configs[dto_name]
        dto = dto_config.create_dto(
            dto_name=dto_name,
            model=model,
        )

        self.dtos[dto_name] = dto
        return dto

    def create_all_dtos(self, model: Type[BaseModel]) -> Dict[str, Type[BaseDTO]]:
        """
        Create all DTOs for a model.

        Args:
            model: The model to create DTOs for

        Returns:
            A dictionary of DTO names to DTO classes
        """
        for dto_name in self.dto_configs:
            self.create_dto(dto_name, model)
        return self.dtos

    def get_dto(self, dto_name: str) -> Optional[Type[BaseDTO]]:
        """
        Get a DTO by name.

        Args:
            dto_name: The name of the DTO to get

        Returns:
            The DTO if found, None otherwise
        """
        return self.dtos.get(dto_name)

    def get_list_dto(self, model: Type[T]) -> Type[PaginatedListDTO[T]]:
        """
        Get or create a DTO for lists of the given model.

        This method returns a DTO suitable for representing lists of items,
        typically used for API list endpoints. It handles both Pydantic models
        and SQLAlchemy models like BaseModel.

        Args:
            model: The model to create a list DTO for (can be a Pydantic model or SQLAlchemy model)

        Returns:
            A DTO class for lists of the given model

        Raises:
            BaseError: If there are issues with the DTO creation
        """
        # Use a standard naming convention for list DTOs
        dto_name = f"{model.__name__}_list"

        # Check if the DTO already exists
        if dto_name in self.dtos:
            return self.dtos[dto_name]

        # If not, check if we have a config for this list type
        if dto_name in self.dto_configs:
            return self.create_dto(dto_name, model)

        # Determine if this is a SQLAlchemy model
        is_sqlalchemy_model = isinstance(model, type) and hasattr(
            model, "__tablename__"
        )

        # Create the base item DTO
        if is_sqlalchemy_model:
            # Create a Pydantic model from SQLAlchemy model
            base_dto = self._create_dto_from_sqlalchemy_model(model)
        else:
            # For Pydantic models, get or create a detail DTO
            base_dto = self._get_or_create_detail_dto(model)

        # Create the list DTO using the PaginatedListDTO generic
        list_dto_name = f"{model.__name__}ListDTO"
        
        # Create a specialized list DTO as a subclass of PaginatedListDTO
        item_type = base_dto
        
        # Create a proper generic PaginatedListDTO class
        list_dto = create_model(
            list_dto_name,
            __base__=PaginatedListDTO[item_type],
        )
        
        # Cast to ensure the type system recognizes it correctly
        typed_list_dto = cast(Type[PaginatedListDTO[T]], list_dto)

        # Store the created DTO
        self.dtos[dto_name] = typed_list_dto
        return typed_list_dto

    def _create_dto_from_sqlalchemy_model(self, model: Type[Any]) -> Type[BaseDTO]:
        """
        Create a Pydantic DTO from a SQLAlchemy model.

        Args:
            model: The SQLAlchemy model to create a DTO from

        Returns:
            A Pydantic DTO for the model
        """
        # Get the mapper for this model class
        mapper = sa_inspect(model)

        # Get column info
        fields = {}
        for column in mapper.columns:
            # Convert SQLAlchemy types to Python types
            python_type = self._get_python_type_for_column(column)

            # Add the field with an appropriate default value
            fields[column.name] = (python_type, None if column.nullable else ...)

        # Create a new Pydantic model based on the SQLAlchemy model
        dto = create_model(
            f"{model.__name__}DTO", __base__=BaseDTO, **fields
        )

        return cast(Type[BaseDTO], dto)

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

    def _get_or_create_detail_dto(self, model: Type[BaseModel]) -> Type[BaseDTO]:
        """
        Get or create a detail DTO for a Pydantic model.

        Args:
            model: The Pydantic model to create a DTO for

        Returns:
            A DTO for the model
        """
        # Try different DTO names
        base_dto_name = f"{model.__name__}_detail"
        base_dto = self.get_dto(base_dto_name)

        if base_dto is None:
            # If no detail DTO exists, try to create it
            if base_dto_name in self.dto_configs:
                base_dto = self.create_dto(base_dto_name, model)
            else:
                # Try to use the default DTO
                default_dto_name = "default"
                if default_dto_name in self.dto_configs:
                    base_dto = self.create_dto(default_dto_name, model)
                else:
                    # Create a simple detail DTO config with all fields
                    detail_config = DTOConfig()
                    self.add_dto_config(base_dto_name, detail_config)
                    base_dto = self.create_dto(base_dto_name, model)

        return base_dto


# Global DTO manager instance
_dto_manager: Optional[DTOManager] = None


def get_dto_manager() -> DTOManager:
    """
    Get the global DTO manager instance.

    This function returns the global DTO manager instance, creating it
    if it doesn't exist yet.

    Returns:
        The global DTO manager instance
    """
    global _dto_manager

    if _dto_manager is None:
        _dto_manager = DTOManager()

    return _dto_manager