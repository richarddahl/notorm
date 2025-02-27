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


from uno.errors import SchemaConfigError
from uno.db.obj import UnoObj
from uno.db.rel_obj import UnoRelObj, RelType
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


class SchemaDef(BaseModel):
    schema_type: str
    schema_base: BaseModel
    router: SchemaRouter
    return_format: str = "native"
    exclude_fields: list[str] | None = []
    include_fields: list[str] | None = []
    include_related_fields: bool = False

    model_config = ConfigDict(extra="ignore")

    def create_schema(self, kls: BaseModel, app: FastAPI) -> None:
        if self.exclude_fields and self.include_fields:
            raise SchemaConfigError(
                "You can't have both include_fields and exclude_fields in the same model (mask) configuration.",
                "INCLUDE_EXCLUDE_FIELDS_CONFLICT",
            )

        schema_name = f"{kls.__name__}{self.schema_type.capitalize()}"

        fields = self.suss_fields(kls)
        if self.include_related_fields:
            fields.update(self.suss_related_fields(kls))

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

    def suss_related_fields(self, kls: UnoObj) -> dict[str, Any]:
        fields = {}
        for name, rel_obj in kls.related_objects.items():  # type: ignore
            if self.include_fields and name not in self.include_fields:
                continue
            if self.exclude_fields and name in self.exclude_fields:
                continue
            field = self.create_field_from_related_objects(rel_obj, name)
            if field is None:
                continue

            if name not in fields:
                fields[name] = field

        return fields

    def create_field_from_related_objects(
        self,
        rel_obj: UnoRelObj,
        name: str,
    ) -> tuple[Any, Any]:
        default = _Unset
        default_factory = _Unset
        title = _Unset
        description = _Unset or rel_obj.doc  # or rel.back_populates
        title = name.title()
        nullable = True

        if nullable:
            default = None
        else:
            default = ...

        if rel_obj.rel_type in [RelType.MANY_TO_ONE, RelType.MANY_TO_MANY]:
            column_type = list[UnoObj]
        else:
            column_type = UnoObj

        field = Field(
            default=default,
            default_factory=default_factory,
            title=title,
            description=description,
        )

        if nullable:
            return (column_type | None, field)
        return (column_type, field)

    def suss_fields(self, kls: UnoObj) -> dict[str, Any]:
        fields = {}
        for col in kls.table.columns:  # type: ignore
            if self.include_fields and col.name not in self.include_fields:
                continue
            if self.exclude_fields and col.name in self.exclude_fields:
                continue
            field = self.create_field_from_column(col)
            if field is None:
                continue
            if col.name not in fields:
                fields[col.name] = field
        return fields

    def create_field_from_column(
        self,
        column: Column,
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


class InsertSchemaDef(SchemaDef):
    schema_type: str = "insert"
    schema_base: BaseModel = InsertSchemaBase
    router: SchemaRouter = InsertRouter

    def format_doc(self, kls: UnoObj) -> str:
        return f"Create a {kls.display_name}"

    def set_schema(self, kls: UnoObj, schema: Type[BaseModel]) -> None:
        kls.insert_schema = schema


class ListSchemaDef(SchemaDef):
    schema_type: str = "list"
    schema_base: BaseModel = ListSchemaBase
    router: SchemaRouter = ListRouter
    include_related_fields: bool = True

    def format_doc(self, kls: UnoObj) -> str:
        return f"List {kls.display_name}"

    def set_schema(self, kls: UnoObj, schema: Type[BaseModel]) -> None:
        kls.list_schema = schema


class DisplaySchemaDef(SchemaDef):
    schema_type: str = "display"
    schema_base: BaseModel = DisplaySchemaBase
    router: SchemaRouter = SelectRouter
    include_related_fields: bool = True

    def format_doc(self, kls: UnoObj) -> str:
        return f"Select a {kls.display_name}"

    def set_schema(self, kls: UnoObj, schema: Type[BaseModel]) -> None:
        kls.display_schema = schema


class UpdateSchemaDef(SchemaDef):
    schema_type: str = "update"
    schema_base: BaseModel = UpdateSchemaBase
    router: SchemaRouter = UpdateRouter

    def format_doc(self, kls: UnoObj) -> str:
        return f"Update a {kls.display_name}"

    def set_schema(self, kls: UnoObj, schema: Type[BaseModel]) -> None:
        kls.update_schema = schema


class DeleteSchemaDef(SchemaDef):
    schema_type: str = "delete"
    schema_base: BaseModel = DeleteSchemaBase
    router: SchemaRouter = DeleteRouter
    include_fields: list[str] = ["id"]

    def format_doc(self, kls: UnoObj) -> str:
        return f"Delete a {kls.display_name}"

    def set_schema(self, kls: UnoObj, schema: Type[BaseModel]) -> None:
        kls.delete_schema = schema


class ImportSchemaDef(SchemaDef):
    schema_type: str = "import"
    schema_base: BaseModel = ImportSchemaBase
    router: SchemaRouter = ImportRouter

    def format_doc(self, kls: UnoObj) -> str:
        return f"Schema to Import a {kls.display_name}"

    def set_schema(self, kls: UnoObj, schema: Type[BaseModel]) -> None:
        kls.import_schema = schema
