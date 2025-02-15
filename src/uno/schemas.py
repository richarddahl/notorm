from __future__ import annotations

from typing import Any, Type

from pydantic import (
    BaseModel,
    ConfigDict,
    create_model,
    model_validator,
    computed_field,
)
from pydantic.fields import Field
from pydantic_core import PydanticUndefined

from sqlalchemy import Column, Table
from sqlalchemy.orm import DeclarativeBase

from fastapi import FastAPI

from uno.db.enums import SchemaDataType
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


class SchemaDef(BaseModel):
    schema_type: str
    schema_base: BaseModel
    router: SchemaRouter
    data_type: SchemaDataType = SchemaDataType.NATIVE
    exclude_fields: list[str] | None = []
    include_fields: list[str] | None = []

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
            **self.suss_fields(klass.__table__),
        )
        self.router(klass=klass).add_to_app(schema, app)
        self.set_schema(klass, schema)

    def create_field(
        self,
        column: Column,
        data_type: SchemaDataType = SchemaDataType.NATIVE,
    ) -> tuple[Any, Any]:
        default = _Unset
        default_factory = _Unset
        title = _Unset
        description = _Unset or column.help_text or column.name
        title = column.name.title()
        if data_type is SchemaDataType.NATIVE:
            try:
                field_type = column.type.python_type
            except NotImplementedError:
                field_type = str
        elif data_type is SchemaDataType.STRING:
            field_type = str
        elif data_type is SchemaDataType.HTML:
            field_type = dict
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

        field = Field(
            default=default,
            default_factory=default_factory,
            title=title,
            description=description,
        )
        if nullable:
            return (field_type | None, field)
        return (field_type, field)

    def suss_fields(self, table: Table) -> dict[str, Any]:
        if self.include_fields and self.exclude_fields:
            raise SchemaFieldListError(
                "You can't have both include_fields and exclude_fields in the same model (mask) configuration.",
                "INCLUDE_EXCLUDE_FIELDS_CONFLICT",
            )
        fields = {}
        for col in table.columns:  # type: ignore
            column_name = col.name
            if self.include_fields and column_name not in self.include_fields:
                continue
            if self.exclude_fields and column_name in self.exclude_fields:
                continue
            field = self.create_field(col, data_type=self.data_type)
            if column_name not in fields:
                fields[column_name] = field
        # for name, config in cls.non_db_field_configs.items():
        #    if name not in fields:
        #        fields[name] = (
        #            config.field_type,
        #            Field(default=config.default, alias=config.alias),
        #        )
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
    data_type: SchemaDataType = SchemaDataType.NATIVE

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to Create a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.create_schema = schema


class ListSchemaDef(SchemaDef):
    schema_type: str = "list"
    schema_base: BaseModel = ListSchemaBase
    router: SchemaRouter = ListRouter
    data_type: SchemaDataType = SchemaDataType.HTML

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to List {klass.display_name_plural}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.list_schema = schema


class SelectSchemaDef(SchemaDef):
    schema_type: str = "select"
    schema_base: BaseModel = SelectSchemaBase
    router: SchemaRouter = SelectRouter
    data_type: SchemaDataType = SchemaDataType.NATIVE

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to Select a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.select_schema = schema


class UpdateSchemaDef(SchemaDef):
    schema_type: str = "update"
    schema_base: BaseModel = UpdateSchemaBase
    router: SchemaRouter = PatchRouter
    data_type: SchemaDataType = SchemaDataType.NATIVE

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to Update a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.update_schema = schema


class DeleteSchemaDef(SchemaDef):
    schema_type: str = "delete"
    schema_base: BaseModel = DeleteSchemaBase
    router: SchemaRouter = DeleteRouter
    data_type: SchemaDataType = SchemaDataType.NATIVE
    include_fields: list[str] = ["id"]

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to Delete a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.delete_schema = schema


class ImportSchemaDef(SchemaDef):
    schema_type: str = "import"
    schema_base: BaseModel = ImportSchemaBase
    router: SchemaRouter = PutRouter
    data_type: SchemaDataType = SchemaDataType.NATIVE

    def format_doc(self, klass: DeclarativeBase) -> str:
        return f"Schema to Import a {klass.display_name}"

    def set_schema(self, klass: DeclarativeBase, schema: Type[BaseModel]) -> None:
        klass.import_schema = schema
