# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Set

from pydantic import BaseModel, model_validator, create_model

from uno.errors import UnoError
from uno.config import settings


class UnoSchema(BaseModel):
    """Model class for all model schemas"""

    pass


class UnoSchemaConfig(BaseModel):
    """Model class for all model schema configs"""

    schema_base: BaseModel = UnoSchema
    exclude_fields: Set[str] = set()
    include_fields: Set[str] = set()

    @model_validator(mode="after")
    def validate_exclude_include_fields(self) -> "Self":
        if self.exclude_fields and self.include_fields:
            raise UnoError(
                f"The schema configuration: {self.__name__} cannot have both exclude_fields or include_fields.",
                "BOTH_EXCLUDE_INCLUDE_FIELDS",
            )
        return self

    def create_schema(self, schema_name: str, model: BaseModel) -> UnoSchema:

        schema_title = f"{model.__name__}{schema_name.split('_')[0].title()}"

        # Convert to set for faster comparison_operator and comparison
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
        }
        return create_model(
            schema_title,
            __base__=self.schema_base,
            **fields,
        )
