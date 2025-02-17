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

from uno.routers import (
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

from uno.config import settings  # type: ignore


_Unset: Any = PydanticUndefined

'''
from uno.utilities import (  # type: ignore
    boolean_to_string,
    date_to_string,
    datetime_to_string,
    decimal_to_string,
    timedelta_to_string,
    obj_to_string,
    boolean_to_okui,
    date_to_okui,
    datetime_to_okui,
    decimal_to_okui,
    timedelta_to_okui,
    obj_to_okui,
)



@dataclass
class ViewSQL(SQLEmitter):
    def emit_sql(self, schema_name: str, field_list: list[str]) -> str:
        return textwrap.dedent(
            f"""
            SET ROLE {settings.DB_USER}_admin;
            CREATE OR REPLACE VIEW {self.schema_name}.{self.table_name}_{schema_name} AS 
            SELECT {field_list}
            FROM {self.schema_name}.{self.table_name};
            """
        )

class UnoStringSchema(UnoSchema):
    """
    A subclass of UnoSchema that represents a string-based mask model.

    UnoStringSchemas are generally used to display the data in a localized string format, via babel.
    """

    pass


class UnoHTMLSchema(UnoSchema):
    """
    This class represents an Uno element mask model.

    It inherits from the UnoSchema class and provides additional functionality specific to element masks.
    """

    pass
    """
    @model_validator(mode="after")
    @classmethod
    def convert_fields_to_strings(cls, data: Any) -> Any:
        str_data = {}
        for k, v in data.items():
            if isinstance(v, list):
                for val in v:

                str_data.update({k: [str(i) for i in v]})
            str_data.update({k: str(v)})
    """

'''


class ListSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SelectSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeleteSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FKSchema(BaseModel):
    primary_key: str
    string_representation: str

    model_config = ConfigDict(extra="forbid")


class SchemaDef(BaseModel):
    schema_type: str
    schema_base: BaseModel
    router: SchemaRouter
    data_type: str = "native"
    exclude_fields: list[str] | None = []
    include_fields: list[str] | None = []
    schema_direction: str = "inbound"

    model_config = ConfigDict(extra="forbid")

    def init_schema(self, klass: DeclarativeBase, app: FastAPI) -> Type[BaseModel]:
        if self.exclude_fields and self.include_fields:
            raise SchemaConfigError(
                "You can't have both include_fields and exclude_fields in the same model (mask) configuration.",
                "INCLUDE_EXCLUDE_FIELDS_CONFLICT",
            )

        schema_name = f"{klass.__name__}{self.schema_type.capitalize()}"

        schema = create_model(
            schema_name,
            __doc__=self.format_doc(klass),
            __base__=self.schema_base,
            __validators__=None,
            __cls_kwargs__=None,
            __slots__=None,
            **self.suss_fields(klass),
        )
        self.router(klass=klass).add_to_app(schema, app)
        self.set_schema(klass, schema)

    def create_field(
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
        json_schema_extra = {}

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

        if column.foreign_keys and self.schema_direction == "outbound":
            json_schema_extra.update({"display": False})
            if column.info.get("edge"):
                if not isinstance(column.info["edge"], dict):
                    return None
                title = column.info["edge"].get("name")
                accessor = column.info["edge"].get("relationship")

                if not title or not accessor:
                    raise SchemaFieldListError(
                        f"Edge field {column.name} is missing a required attribute.",
                        "MISSING_EDGE_FIELD_ATTRIBUTE",
                    )
                column_type = FKSchema

        field = Field(
            default=default,
            default_factory=default_factory,
            title=title,
            description=description,
            json_schema_extra=json_schema_extra,
        )

        if nullable:
            return (column_type | None, field)
        return (column_type, field)

    def suss_fields(self, klass: DeclarativeBase) -> dict[str, Any]:
        fields = {}
        for col in klass.__table__.columns:  # type: ignore
            if self.include_fields and col.name not in self.include_fields:
                continue
            if self.exclude_fields and col.name in self.exclude_fields:
                continue
            field = self.create_field(col, klass)
            if field is None:
                continue
            if col.name not in fields:
                fields[col.name] = field
        return fields


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


class CreateSchemaDef(SchemaDef):
    schema_type: str = "create"
    schema_base: BaseModel = CreateSchemaBase
    router: SchemaRouter = PostRouter

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Create a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.create_schema = schema


class ListSchemaDef(SchemaDef):
    schema_type: str = "list"
    schema_base: BaseModel = ListSchemaBase
    router: SchemaRouter = ListRouter
    # data_type: str = "html"
    schema_direction: str = "outbound"

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"List {klass.display_name_plural}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.list_schema = schema


class SelectSchemaDef(SchemaDef):
    schema_type: str = "select"
    schema_base: BaseModel = SelectSchemaBase
    router: SchemaRouter = SelectRouter
    schema_direction: str = "outbound"

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Select a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.select_schema = schema


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
