# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Base DTO definitions for the Uno framework.

This module provides the base Data Transfer Object classes that are used
throughout the framework for transferring data between layers, including
validation, serialization, and API documentation.
"""

from typing import TypeVar, Generic


from pydantic import BaseModel, Field

from uno.core.base.error import BaseError

# Type variable for DTO classes
DTOT = TypeVar("DTOT", bound="BaseDTO")
T = TypeVar("T", bound=BaseModel)


class BaseDTO(BaseModel):
    """
    Base class for all data transfer objects (DTOs) in the Uno framework.

    This class extends Pydantic's BaseModel with additional functionality
    specific to the Uno framework for data transfer between layers.
    """

    @classmethod
    def create_field_dict(cls, field_name: str) -> dict[str, object]:
        """
        Create a field dictionary for a given field name.

        Args:
            field_name: The name of the field to create a dictionary for

        Returns:
            A dictionary with field metadata
        """
        if field_name not in cls.model_fields:
            raise BaseError(
                f"Field {field_name} not found in DTO {cls.__name__}", "FIELD_NOT_FOUND"
            )

        field = cls.model_fields[field_name]
        return {
            "name": field_name,
            "annotation": field.annotation,
            "description": field.description or "",
            "required": field.is_required(),
            "default": field.get_default() if not field.is_required() else None,
        }

    @classmethod
    def get_field_annotations(cls) -> dict[str, object]:
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

    dto_base: type[BaseDTO] = BaseDTO
    exclude_fields: set[str] = Field(default_factory=set)
    include_fields: set[str] = Field(default_factory=set)

    def create_dto(self, dto_name: str, model: type[BaseModel]) -> type[BaseDTO]:
        """
        Create a DTO for a model based on this configuration.

        Args:
            dto_name: The name of the DTO to create
            model: The model to create a DTO for

        Returns:
            The created DTO class

        Raises:
            BaseError: If there are issues with the DTO creation
        """
        from pydantic import create_model, model_validator
        
        # Validate config
        if self.exclude_fields and self.include_fields:
            raise BaseError(
                "The DTO configuration cannot have both exclude_fields or include_fields.",
                "BOTH_EXCLUDE_INCLUDE_FIELDS",
            )

        dto_title = f"{model.__name__}{dto_name.split('_')[0].title()}"

        # Convert to set for faster comparison and comparison
        all_model_fields = set(model.model_fields.keys())

        # Validate include fields
        if self.include_fields:
            invalid_fields = self.include_fields.difference(all_model_fields)
            if invalid_fields:
                raise BaseError(
                    f"Include fields not found in model {model.__name__}: {', '.join(invalid_fields)} for DTO: {dto_name}",
                    "INCLUDE_FIELD_NOT_IN_MODEL",
                )

        # Validate exclude fields
        if self.exclude_fields:
            invalid_fields = self.exclude_fields.difference(all_model_fields)
            if invalid_fields:
                raise BaseError(
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
            raise BaseError(
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
        from typing import cast
        dto_cls = create_model(
            dto_title,
            __base__=self.dto_base,
            **fields,
        )

        # Cast to ensure the type system recognizes the return value correctly
        return cast(Type[BaseDTO], dto_cls)


class PaginatedListDTO(BaseDTO, Generic[T]):
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


class WithMetadataDTO(BaseDTO):
    """
    DTO for items with metadata.

    This DTO is used as a base class for objects that include metadata
    such as created_at, updated_at, and version information.
    """

    created_at: str | None = Field(None, description="The creation timestamp")
    updated_at: str | None = Field(None, description="The last update timestamp")
    version: int | None = Field(None, description="The object version number")
    metadata: dict[str, object] | None = Field(None, description="Additional metadata")