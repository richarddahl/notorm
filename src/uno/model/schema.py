# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Union

from pydantic import BaseModel, model_validator, create_model

from uno.errors import UnoError
from uno.config import settings


class SchemaConfigError(UnoError):
    pass


class SchemaFieldListError(UnoError):
    pass


class UnoSchema(BaseModel):
    """Base class for all model schemas"""

    pass


class UnoSchemaConfig(BaseModel):
    """Base class for all model schema configs"""

    schema_base: BaseModel = UnoSchema
    exclude_fields: list[str] | None = []
    include_fields: list[str] | None = []

    @model_validator(mode="after")
    def validate_exclude_include_fields(self) -> "Self":
        if self.exclude_fields and self.include_fields:
            raise SchemaConfigError(
                f"The schema configuration: {self.__name__} cannot have both exclude_fields or include_fields.",
                "BOTH_EXCLUDE_INCLUDE_FIELDS",
            )
        return self

    def create_schema(self, schema_name: str, model: BaseModel) -> UnoSchema:

        # First validate all field references
        all_model_fields = set(model.model_fields.keys())

        schema_title = f"{model.__name__}{schema_name.split('_')[0].title()}"

        # Validate include fields
        if self.include_fields:
            invalid_fields = set(self.include_fields) - all_model_fields
            if invalid_fields:
                raise SchemaFieldListError(
                    f"Fields not found in model {model.__name__}: {', '.join(invalid_fields)} for schema: {schema_name}",
                    "INCLUDE_FIELD_NOT_IN_MODEL",
                )

        # Validate exclude fields
        if self.exclude_fields:
            invalid_fields = set(self.exclude_fields) - all_model_fields
            if invalid_fields:
                raise SchemaFieldListError(
                    f"Fields not found in model {model.__name__}: {', '.join(invalid_fields)} for schema: {schema_name}",
                    "EXCLUDE_FIELD_NOT_IN_MODEL",
                )

        # Determine which fields to include in the schema
        if self.include_fields:
            field_names = set(self.include_fields)
        elif self.exclude_fields:
            field_names = all_model_fields - set(self.exclude_fields)
        else:
            field_names = all_model_fields

        # Create the field dictionary for the schema
        fields = {
            field_name: (
                model.model_fields[field_name].annotation,
                model.model_fields[field_name],
            )
            for field_name in field_names
        }
        # fields = {}
        # for field_name in field_names:
        #    field_annotation = model.model_fields[field_name].annotation
        #    if (
        #        hasattr(field_annotation, "__origin__")
        #        and field_annotation.__origin__ is Union
        #    ):
        #        args = field_annotation.__args__
        #        for arg in args:
        #            if issubclass(arg, BaseModel):
        #                rel_model_class_name = arg.__name__
        #                rel_model_class = arg.registry[rel_model_class_name]
        #                fields[field_name] = (
        #                    model.model_fields[field_name].annotation,
        #                    getattr(
        #                        rel_model_class,
        #                        "summary_schema",
        #                    ),
        #                )
        #    fields[field_name] = (
        #        model.model_fields[field_name].annotation,
        #        model.model_fields[field_name],
        #    )
        return create_model(
            schema_title,
            __base__=self.schema_base,
            **fields,
        )
