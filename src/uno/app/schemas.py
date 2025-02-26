# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Any, Type
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    create_model,
    model_validator,
    field_validator,
)
from pydantic.fields import Field
from pydantic_core import PydanticUndefined

from sqlalchemy import Column, Table
from sqlalchemy.orm import DeclarativeBase

from fastapi import FastAPI

from uno.app.routers import (
    SchemaRouter,
    InsertRouter,
    ListRouter,
    SelectRouter,
    UpdateRouter,
    DeleteRouter,
    ImportRouter,
)


from uno.errors import (
    SchemaConfigError,
    SchemaFieldListError,
)
from uno.utilities import convert_snake_to_title
from uno.config import settings  # type: ignore


_Unset: Any = PydanticUndefined


class ListSchemaBase(BaseModel):
    pass


class DisplaySchemaBase(BaseModel):
    pass


class InsertSchemaBase(BaseModel):
    pass


class UpdateSchemaBase(BaseModel):
    pass


class DeleteSchemaBase(BaseModel):
    pass


class ImportSchemaBase(BaseModel):
    pass


class RelatedSchema(BaseModel):
    primary_key: str
    string_representation: str

    model_config = ConfigDict(extra="ignore")


class SchemaDef(BaseModel):
    schema_type: str
    schema_base: BaseModel
    router: SchemaRouter
    return_format: str = "native"
    exclude_fields: list[str] | None = []
    include_fields: list[str] | None = []
    use_related_schemas: bool = False

    model_config = ConfigDict(extra="ignore")

    def create_schema(self, kls: DeclarativeBase, app: FastAPI) -> None:
        if self.exclude_fields and self.include_fields:
            raise SchemaConfigError(
                "You can't have both include_fields and exclude_fields in the same model (mask) configuration.",
                "INCLUDE_EXCLUDE_FIELDS_CONFLICT",
            )

        schema_name = f"{kls.__name__}{self.schema_type.capitalize()}"
        fields = self.suss_fields(kls)
        # fields.update(self.suss_related_fields(kls))

        schema = create_model(
            schema_name,
            __doc__=self.format_doc(kls),
            __base__=self.schema_base,
            __validators__=None,
            __cls_kwargs__=None,
            __slots__=None,
            **fields,
        )
        router = self.router(kls=kls, reponse_model=schema)
        endpoint = router.endpoint_factory(
            body=schema, response_model=router.response_model
        )
        router.add_to_app(app)

        setattr(kls, f"{self.schema_type}_schema", schema)

    def suss_related_fields(self, kls: DeclarativeBase) -> dict[str, Any]:
        fields = {}
        for rel in kls.relationships():  # type: ignore
            name = rel.key
            if self.include_fields and name not in self.include_fields:
                continue
            if self.exclude_fields and name in self.exclude_fields:
                continue
            if not rel.info.get("edge"):
                raise SchemaFieldListError(
                    f"Relationship {name} in class: {kls} is missing it's info['edge'].",
                    "MISSING_EDGE_INFO",
                )
            field = self.create_field_from_relationship(rel, kls, name)
            if field is None:
                continue

            if name not in fields:
                fields[name] = field

        return fields

    def create_field_from_relationship(
        self,
        rel: Any,
        kls: DeclarativeBase,
        name: str,
    ) -> tuple[Any, Any]:
        default = _Unset
        default_factory = _Unset
        title = _Unset
        description = _Unset or rel.doc  # or rel.back_populates
        title = name.title()
        nullable = True

        if nullable:
            default = None
        else:
            default = ...

        if rel.uselist:
            column_type = list[RelatedSchema]
        else:
            column_type = RelatedSchema

        field = Field(
            default=default,
            default_factory=default_factory,
            title=title,
            description=description,
        )

        if nullable:
            return (column_type | None, field)
        return (column_type, field)

    def suss_fields(self, kls: DeclarativeBase) -> dict[str, Any]:
        fields = {}
        for col in kls.table.columns:  # type: ignore
            if self.include_fields and col.name not in self.include_fields:
                continue
            if self.exclude_fields and col.name in self.exclude_fields:
                continue
            field = self.create_field_from_column(col, kls)
            if field is None:
                continue
            if col.name not in fields:
                fields[col.name] = field
        return fields

    def create_field_from_column(
        self,
        column: Column,
        kls: DeclarativeBase,
    ) -> tuple[Any, Any]:
        default = _Unset
        default_factory = _Unset
        title = _Unset
        description = _Unset or column.doc or column.name
        title = column.name.title()
        nullable = column.nullable

        if column.server_default:
            default = None
        elif column.default:
            if callable(column.default):
                default_factory = column.default
            else:
                default = column.default
        elif nullable:
            default = None
        else:
            default = ...

        try:
            column_type = column.type.python_type
        except NotImplementedError:
            column_type = str

        field = Field(
            default=default,
            default_factory=default_factory,
            title=title,
            description=description,
        )

        if nullable:
            return (column_type | None, field)
        return (column_type, field)


"""
    @classmethod
    def create_view(cls) -> None:
        cls.sql_emitters.append(ViewSQL()._emit_sql())
"""


class InsertSchemaDef(SchemaDef):
    schema_type: str = "insert"
    schema_base: BaseModel = InsertSchemaBase
    router: SchemaRouter = InsertRouter

    def format_doc(self, kls: DeclarativeBase) -> str:
        return f"Create a {kls.display_name}"

    def set_schema(self, kls: DeclarativeBase, schema: Type[BaseModel]) -> None:
        kls.insert_schema = schema


class ListSchemaDef(SchemaDef):
    schema_type: str = "list"
    schema_base: BaseModel = ListSchemaBase
    router: SchemaRouter = ListRouter
    use_related_schemas: bool = True

    def format_doc(self, kls: DeclarativeBase) -> str:
        return f"List {kls.display_name}"

    def set_schema(self, kls: DeclarativeBase, schema: Type[BaseModel]) -> None:
        kls.list_schema = schema


class DisplaySchemaDef(SchemaDef):
    schema_type: str = "display"
    schema_base: BaseModel = DisplaySchemaBase
    router: SchemaRouter = SelectRouter
    use_related_schemas: bool = True

    def format_doc(self, kls: DeclarativeBase) -> str:
        return f"Select a {kls.display_name}"

    def set_schema(self, kls: DeclarativeBase, schema: Type[BaseModel]) -> None:
        kls.display_schema = schema


class UpdateSchemaDef(SchemaDef):
    schema_type: str = "update"
    schema_base: BaseModel = UpdateSchemaBase
    router: SchemaRouter = UpdateRouter

    def format_doc(self, kls: DeclarativeBase) -> str:
        return f"Update a {kls.display_name}"

    def set_schema(self, kls: DeclarativeBase, schema: Type[BaseModel]) -> None:
        kls.update_schema = schema


class DeleteSchemaDef(SchemaDef):
    schema_type: str = "delete"
    schema_base: BaseModel = DeleteSchemaBase
    router: SchemaRouter = DeleteRouter
    include_fields: list[str] = ["id"]

    def format_doc(self, kls: DeclarativeBase) -> str:
        return f"Delete a {kls.display_name}"

    def set_schema(self, kls: DeclarativeBase, schema: Type[BaseModel]) -> None:
        kls.delete_schema = schema


class ImportSchemaDef(SchemaDef):
    schema_type: str = "import"
    schema_base: BaseModel = ImportSchemaBase
    router: SchemaRouter = ImportRouter

    def format_doc(self, kls: DeclarativeBase) -> str:
        return f"Schema to Import a {kls.display_name}"

    def set_schema(self, kls: DeclarativeBase, schema: Type[BaseModel]) -> None:
        kls.import_schema = schema
