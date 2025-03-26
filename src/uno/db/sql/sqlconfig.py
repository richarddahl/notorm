# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar, Optional

from pydantic import BaseModel, model_validator
from sqlalchemy import Table
from sqlalchemy.engine.base import Connection

from uno.db.sql.sql import SQLEmitter
from uno.errors import UnoRegistryError


class SQLConfig(BaseModel):
    registry: ClassVar[dict[str, type["SQLConfig"]]] = {}
    sql_emitters: ClassVar[dict[str, SQLEmitter]] = {}
    table: ClassVar[Optional[Table]] = None

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
                f"SQLConfig class: {cls.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )

    # End of __init_subclass__

    @classmethod
    def emit_sql(cls, connection: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(table=cls.table).emit_sql(connection)
