# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema definitions for the Uno framework.

This module provides base classes and utilities for creating and managing schemas
that define the structure and validation rules for data models.
"""

from typing import Set, Dict, Any, Type, TypeVar, Generic, get_args, get_origin, cast

from pydantic import BaseModel, model_validator, create_model, Field

from uno.errors import UnoError

# Type variable for schema classes
SchemaT = TypeVar("SchemaT", bound="UnoSchema")


class UnoSchema(BaseModel):
    """
    Base class for all schema models in the Uno framework.
    
    This class extends Pydantic's BaseModel with additional functionality
    specific to the Uno framework.
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
                f"Field {field_name} not found in schema {cls.__name__}",
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


class UnoSchemaConfig(BaseModel):
    """
    Configuration for schema creation.
    
    This class defines how schemas are created, including which fields to
    include or exclude and the base class to use.
    """
    
    schema_base: Type[UnoSchema] = UnoSchema
    exclude_fields: Set[str] = Field(default_factory=set)
    include_fields: Set[str] = Field(default_factory=set)
    
    @model_validator(mode="after")
    def validate_exclude_include_fields(self) -> "UnoSchemaConfig":
        """
        Validate that the configuration doesn't have both exclude_fields and include_fields.
        
        Returns:
            The validated configuration
            
        Raises:
            UnoError: If both exclude_fields and include_fields are specified
        """
        if self.exclude_fields and self.include_fields:
            raise UnoError(
                "The schema configuration cannot have both exclude_fields or include_fields.",
                "BOTH_EXCLUDE_INCLUDE_FIELDS",
            )
        return self
    
    def create_schema(self, schema_name: str, model: Type[BaseModel]) -> Type[UnoSchema]:
        """
        Create a schema for a model based on this configuration.
        
        Args:
            schema_name: The name of the schema to create
            model: The model to create a schema for
            
        Returns:
            The created schema class
            
        Raises:
            UnoError: If there are issues with the schema creation
        """
        
        schema_title = f"{model.__name__}{schema_name.split('_')[0].title()}"
        
        # Convert to set for faster comparison and comparison
        all_model_fields = set(model.model_fields.keys())
        
        # Validate include fields
        if self.include_fields:
            invalid_fields = self.include_fields.difference(all_model_fields)
            if invalid_fields:
                raise UnoError(
                    f"Include fields not found in model {model.__name__}: {', '.join(invalid_fields)} for schema: {schema_name}",
                    "INCLUDE_FIELD_NOT_IN_MODEL",
                )
        
        # Validate exclude fields
        if self.exclude_fields:
            invalid_fields = self.exclude_fields.difference(all_model_fields)
            if invalid_fields:
                raise UnoError(
                    f"Exclude fields not found in model {model.__name__}: {', '.join(invalid_fields)} for schema: {schema_name}",
                    "EXCLUDE_FIELD_NOT_IN_MODEL",
                )
        
        # Determine which fields to include in the schema
        if self.include_fields:
            field_names = all_model_fields.intersection(self.include_fields)
        elif self.exclude_fields:
            field_names = all_model_fields.difference(self.exclude_fields)
        else:
            field_names = all_model_fields
        
        # If no fields are specified, use all fields
        if not field_names:
            raise UnoError(
                f"No fields specified for schema {schema_name}.",
                "NO_FIELDS_SPECIFIED",
            )
        
        # Create the field dictionary for the schema
        fields = {
            field_name: (
                model.model_fields[field_name].annotation,
                model.model_fields[field_name],
            )
            for field_name in field_names
            if model.model_fields[field_name].exclude is not True
        }
        
        # Create and return the schema class
        # mypy has issues with create_model, so we use type: ignore
        schema_cls = create_model(  # type: ignore
            schema_title,
            __base__=self.schema_base,
            **fields,
        )
        
        # Cast to ensure the type system recognizes the return value correctly
        return cast(Type[UnoSchema], schema_cls)


# Generic list schema for pagination
T = TypeVar("T", bound=BaseModel)

class PaginatedList(UnoSchema, Generic[T]):
    """
    Schema for paginated lists of items.
    
    This generic schema is used to represent paginated lists of items,
    with metadata about the pagination.
    
    Type Parameters:
        T: The type of items in the list
    """
    
    items: list[T] = Field(..., description="The list of items")
    total: int = Field(..., description="The total number of items")
    page: int = Field(1, description="The current page number")
    page_size: int = Field(25, description="The number of items per page")
    pages: int = Field(1, description="The total number of pages")