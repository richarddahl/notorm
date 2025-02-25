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
    PostRouter,
    ListRouter,
    SelectRouter,
    PatchRouter,
    DeleteRouter,
    PutRouter,
)


from uno.errors import (
    SchemaConfigError,
    SchemaFieldListError,
)
from uno.utilities import convert_snake_to_title
from uno.config import settings  # type: ignore


_Unset: Any = PydanticUndefined


class ListSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DisplaySchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InsertSchemaBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


class UpdateSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeleteSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RelatedSchema(BaseModel):
    primary_key: str
    string_representation: str

    model_config = ConfigDict(extra="forbid")


class SchemaDef(BaseModel):
    schema_type: str
    schema_base: BaseModel
    router: SchemaRouter
    return_format: str = "native"
    exclude_fields: list[str] | None = []
    include_fields: list[str] | None = []
    use_related_schemas: bool = False

    model_config = ConfigDict(extra="forbid")

    def create_schema(self, klass: DeclarativeBase, app: FastAPI) -> None:
        if self.exclude_fields and self.include_fields:
            raise SchemaConfigError(
                "You can't have both include_fields and exclude_fields in the same model (mask) configuration.",
                "INCLUDE_EXCLUDE_FIELDS_CONFLICT",
            )

        schema_name = f"{klass.__name__}{self.schema_type.capitalize()}"
        fields = self.suss_fields(klass)
        # fields.update(self.suss_related_fields(klass))

        schema = create_model(
            schema_name,
            __doc__=self.format_doc(klass),
            __base__=self.schema_base,
            __validators__=None,
            __cls_kwargs__=None,
            __slots__=None,
            **fields,
        )
        self.router(klass=klass).add_to_app(schema, app)
        # self.set_schema(klass, schema)
        setattr(klass, f"{self.schema_type}_schema", schema)

    def suss_related_fields(self, klass: DeclarativeBase) -> dict[str, Any]:
        fields = {}
        for rel in klass.relationships():  # type: ignore
            name = rel.key
            if self.include_fields and name not in self.include_fields:
                continue
            if self.exclude_fields and name in self.exclude_fields:
                continue
            if not rel.info.get("edge"):
                raise SchemaFieldListError(
                    f"Relationship {name} in class: {klass} is missing it's info['edge'].",
                    "MISSING_EDGE_INFO",
                )
            field = self.create_field_from_relationship(rel, klass, name)
            if field is None:
                continue

            if name not in fields:
                fields[name] = field

        return fields

    def create_field_from_relationship(
        self,
        rel: Any,
        klass: DeclarativeBase,
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

    def suss_fields(self, klass: DeclarativeBase) -> dict[str, Any]:
        fields = {}
        for col in klass.table.columns:  # type: ignore
            if self.include_fields and col.name not in self.include_fields:
                continue
            if self.exclude_fields and col.name in self.exclude_fields:
                continue
            field = self.create_field_from_column(col, klass)
            if field is None:
                continue
            if col.name not in fields:
                fields[col.name] = field
        return fields

    def create_field_from_column(
        self,
        column: Column,
        klass: DeclarativeBase,
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
        cls.sql_emitters.append(ViewSQL().emit_sql())

    @classmethod
    def emit_sql(cls) -> str:
        if cls.schema_operation_type != SchemaOperationType.SELECT:
            return ""
        return "\n".join(
            [f"{sql_emitter().emit_sql()}" for sql_emitter in cls.sql_emitters]
        )

"""


class InsertSchemaDef(SchemaDef):
    schema_type: str = "insert"
    schema_base: BaseModel = InsertSchemaBase
    router: SchemaRouter = PostRouter

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Create a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.insert_schema = schema


class ListSchemaDef(SchemaDef):
    schema_type: str = "list"
    schema_base: BaseModel = ListSchemaBase
    router: SchemaRouter = ListRouter
    use_related_schemas: bool = True

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"List {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.list_schema = schema


class DisplaySchemaDef(SchemaDef):
    schema_type: str = "display"
    schema_base: BaseModel = DisplaySchemaBase
    router: SchemaRouter = SelectRouter
    use_related_schemas: bool = True

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Select a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.display_schema = schema


class UpdateSchemaDef(SchemaDef):
    schema_type: str = "update"
    schema_base: BaseModel = UpdateSchemaBase
    router: SchemaRouter = PatchRouter

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Update a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.update_schema = schema


class DeleteSchemaDef(SchemaDef):
    schema_type: str = "delete"
    schema_base: BaseModel = DeleteSchemaBase
    router: SchemaRouter = DeleteRouter
    include_fields: list[str] = ["id"]

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Delete a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.delete_schema = schema


class ImportSchemaDef(SchemaDef):
    schema_type: str = "import"
    schema_base: BaseModel = ImportSchemaBase
    router: SchemaRouter = PutRouter

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to Import a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.import_schema = schema
