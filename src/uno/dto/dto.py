# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
DTO definitions for the Uno framework's Domain-Driven Design approach.

This module provides base classes and utilities for creating and managing Data Transfer Objects (DTOs)
that define the structure for transferring data between layers, including validation,
serialization, and API documentation.
"""

from typing import Set, Dict, Any, Type, TypeVar, Generic, get_args, get_origin, cast, List, Optional

from pydantic import BaseModel, model_validator, create_model, Field

from uno.schema.errors import (
    SchemaInvalidError,
    SchemaValidationError,
    SchemaConversionError
)
from uno.core.errors.base import UnoError

# Type variable for DTO classes
DTOT = TypeVar("DTOT", bound="UnoDTO")


class UnoDTO(BaseModel):
    """
    Base class for all data transfer objects (DTOs) in the Uno framework.
    
    This class extends Pydantic's BaseModel with additional functionality
    specific to the Uno framework for data transfer between layers.
    """
    
    @classmethod
    def create_field_dict(cls, field_name: str) -> Dict[str, Any]:
        """
        Create a field dictionary for a given field name.
        
        Args:
            field_name: The name of the field to create a dictionary for
            
        Returns:
            A dictionary with field metadata
        """
        if field_name not in cls.model_fields:
            raise UnoError(
                f"Field {field_name} not found in DTO {cls.__name__}",
                "FIELD_NOT_FOUND"
            )
            
        field = cls.model_fields[field_name]
        return {
            "name": field_name,
            "annotation": field.annotation,
            "description": field.description or "",
            "required": field.is_required(),
            "default": field.get_default() if not field.is_required() else None
        }
        
    @classmethod
    def get_field_annotations(cls) -> Dict[str, Any]:
        """
        Get a dictionary of field names to their annotations.
        
        Returns:
            A dictionary mapping field names to their type annotations
        """
        return {name: field.annotation for name, field in cls.model_fields.items()}


class DTOConfig(BaseModel):
    """
    Configuration for DTO creation.
    
    This class defines how DTOs are created, including which fields to
    include or exclude and the base class to use.
    """
    
    dto_base: Type[UnoDTO] = UnoDTO
    exclude_fields: Set[str] = Field(default_factory=set)
    include_fields: Set[str] = Field(default_factory=set)
    
    @model_validator(mode="after")
    def validate_exclude_include_fields(self) -> "DTOConfig":
        """
        Validate that the configuration doesn't have both exclude_fields and include_fields.
        
        Returns:
            The validated configuration
            
        Raises:
            UnoError: If both exclude_fields and include_fields are specified
        """
        if self.exclude_fields and self.include_fields:
            raise UnoError(
                "The DTO configuration cannot have both exclude_fields or include_fields.",
                "BOTH_EXCLUDE_INCLUDE_FIELDS",
            )
        return self
    
    def create_dto(self, dto_name: str, model: Type[BaseModel]) -> Type[UnoDTO]:
        """
        Create a DTO for a model based on this configuration.
        
        Args:
            dto_name: The name of the DTO to create
            model: The model to create a DTO for
            
        Returns:
            The created DTO class
            
        Raises:
            UnoError: If there are issues with the DTO creation
        """
        
        dto_title = f"{model.__name__}{dto_name.split('_')[0].title()}"
        
        # Convert to set for faster comparison and comparison
        all_model_fields = set(model.model_fields.keys())
        
        # Validate include fields
        if self.include_fields:
            invalid_fields = self.include_fields.difference(all_model_fields)
            if invalid_fields:
                raise UnoError(
                    f"Include fields not found in model {model.__name__}: {', '.join(invalid_fields)} for DTO: {dto_name}",
                    "INCLUDE_FIELD_NOT_IN_MODEL",
                )
        
        # Validate exclude fields
        if self.exclude_fields:
            invalid_fields = self.exclude_fields.difference(all_model_fields)
            if invalid_fields:
                raise UnoError(
                    f"Exclude fields not found in model {model.__name__}: {', '.join(invalid_fields)} for DTO: {dto_name}",
                    "EXCLUDE_FIELD_NOT_IN_MODEL",
                )
        
        # Determine which fields to include in the DTO
        if self.include_fields:
            field_names = all_model_fields.intersection(self.include_fields)
        elif self.exclude_fields:
            field_names = all_model_fields.difference(self.exclude_fields)
        else:
            field_names = all_model_fields
        
        # If no fields are specified, use all fields
        if not field_names:
            raise UnoError(
                f"No fields specified for DTO {dto_name}.",
                "NO_FIELDS_SPECIFIED",
            )
        
        # Create the field dictionary for the DTO
        fields = {
            field_name: (
                model.model_fields[field_name].annotation,
                model.model_fields[field_name],
            )
            for field_name in field_names
            if model.model_fields[field_name].exclude is not True
        }
        
        # Create and return the DTO class
        # mypy has issues with create_model, so we use type: ignore
        dto_cls = create_model(  # type: ignore
            dto_title,
            __base__=self.dto_base,
            **fields,
        )
        
        # Cast to ensure the type system recognizes the return value correctly
        return cast(Type[UnoDTO], dto_cls)


# Generic list DTO for pagination
T = TypeVar("T", bound=BaseModel)

class PaginatedListDTO(UnoDTO, Generic[T]):
    """
    DTO for paginated lists of items.
    
    This generic DTO is used to represent paginated lists of items,
    with metadata about the pagination.
    
    Type Parameters:
        T: The type of items in the list
    """
    
    items: list[T] = Field(..., description="The list of items")
    total: int = Field(..., description="The total number of items")
    page: int = Field(1, description="The current page number")
    page_size: int = Field(25, description="The number of items per page")
    pages: int = Field(1, description="The total number of pages")


class WithMetadataDTO(UnoDTO):
    """
    DTO for items with metadata.
    
    This DTO is used as a base class for objects that include metadata
    such as created_at, updated_at, and version information.
    """
    
    created_at: Optional[str] = Field(None, description="The creation timestamp")
    updated_at: Optional[str] = Field(None, description="The last update timestamp")
    version: Optional[int] = Field(None, description="The object version number")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")