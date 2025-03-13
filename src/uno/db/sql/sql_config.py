# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Any, ClassVar, Optional

from sqlalchemy.engine.base import Connection
from pydantic import BaseModel

from uno.db.sql.sql_emitter import SQLEmitter, SQLEmitter
from uno.db.sql.db_sql_emitters import InsertMetaRecordTrigger, RecordStatusFunction
from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaType
from uno.errors import UnoRegistryError


class SQLConfig(BaseModel):
    registry: ClassVar[dict[str, type["SQLConfig"]]] = {}
    model: ClassVar[Optional[type[BaseModel]]] = None
    table: ClassVar[Optional[Any]] = None
    table_name: ClassVar[str] = None
    sql_emitters: ClassVar[dict[str, SQLEmitter]] = {}

    def __init_subclass__(cls, **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        # Don't add the SQLConfig class itself to the registry
        if cls is SQLConfig:
            return
        # Add the subclass to the registry if it is not already there
        if cls.__name__ not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            raise UnoRegistryError(
                f"A SQLConfig class with the name {cls.__name__} already exists in the registry.",
                "SQLEMITTER_CLASS_EXISTS_IN_REGISTRY",
            )

    # End of __init_subclass__

    @classmethod
    def emit_sql(cls, connection: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(
                table_name=cls.table_name,
                model=cls.model,
                table=cls.table,
            ).emit_sql(connection)


class TableSQLConfig(SQLConfig):
    @classmethod
    def emit_sql(cls, connection: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter.emit_sql(connection)
