from __future__ import annotations

from typing import Any, Type, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    create_model,
    model_validator,
)
from pydantic.fields import Field
from pydantic_core import PydanticUndefined

from fastapi import FastAPI

from sqlalchemy import Column, Table

from uno.db.enums import SchemaOperationType, SchemaDataType
from uno.routers import Router

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


class ListSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SelectSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeleteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Schema(BaseModel):
    name: ClassVar[str]
    doc: ClassVar[str] = ""
    base: ClassVar[type[BaseModel]] = SelectSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.NATIVE
    exclude_fields: ClassVar[list[str] | None] = []
    include_fields: ClassVar[list[str] | None] = []
    router_def: ClassVar[Router | None] = None

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def create_schema(self, table: Table, app: FastAPI) -> Type[BaseModel]:
        schema = create_model(
            self.name,
            __doc__=self.doc,
            __base__=self.base,
            __validators__=None,
            __cls_kwargs__=None,
            __slots__=None,
            **self.suss_fields(table),
        )
        self.router_def.add_to_app(schema, table, app)
        return schema

    @classmethod
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

    @classmethod
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
    async def is_insert(self) -> bool:
        for key in self.model_dump().keys():
            if not hasattr(self, key):
                return False
        return True

    async def save(self) -> bool:
        if await self.is_insert():
            await self.db.insert(self.model_dump(exclude=await self.insert_excludes()))
            return True
        return True

    def format_unique_constraints(self) -> str:
        # return "NOT IMPLEMENTED YET"
        return ", ".join(
            [
                f"{unique_constraint}: {getattr(self, unique_constraint, "Not Set")}"
                for unique_constraint in self.db.unique_constraints()
            ]
        )

    def update_excludes(self) -> list[str]:
        return [
            field_def
            for field_def in self.model_fields
            if not hasattr(field_def, "server_onupdate")
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} - {self.format_unique_constraints()}"

"""
