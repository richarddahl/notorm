# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar, Optional

from pydantic import BaseModel, model_validator
from sqlalchemy import Table
from sqlalchemy.engine.base import Connection

from uno.db.sql.sql_emitter import SQLEmitter
from uno.errors import UnoRegistryError


class SQLConfig(BaseModel):
    """SQLConfig is a base class for managing SQL configuration and emitting SQL statements.

    These are NOT a ClassVar of UnoModels for the following reasons:
        - Association Tables may require SQL configuration
        - They are only emitted when the database is migrated, not needed during normal operation

    Attributes:
        registry (ClassVar[dict[str, type["SQLConfig"]]]): A registry that keeps track of all subclasses of SQLConfig.
        model (ClassVar[Optional[type[BaseModel]]]): The model associated with the SQL configuration.
            models are only provided for DeclarativeBases
        table (ClassVar[Optional[Any]]): The table object associated with the SQL configuration.
            tables are provided for Association Tables
        table_name (ClassVar[str]): The name of the table associated with the SQL configuration.
        sql_emitters (ClassVar[dict[str, SQLEmitter]]): A dictionary of SQL emitters used to generate SQL statements.

    Methods:
        __init_subclass__(cls, **kwargs):
            Automatically registers subclasses of SQLConfig in the registry.
            Raises:
                UnoRegistryError: If a subclass with the same name already exists in the registry.

        emit_sql(cls, connection: Connection) -> None:
            Emits SQL statements for the associated table using the registered SQL emitters.
            Args:
                connection (Connection): The database connection to use for emitting SQL.
    """

    registry: ClassVar[dict[str, type["SQLConfig"]]] = {}
    model: ClassVar[Optional[type[BaseModel]]] = None
    table: ClassVar[Optional[Table]] = None
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
                f"SQLConfig class: {cls.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )
        if cls.model and cls.table:
            raise UnoRegistryError(
                f"SQLConfig class: {cls.__name__} cannot have both a model and a table.",
                "INVALID_SQLCONFIG",
            )
        if cls.model is None and cls.table is None:
            raise UnoRegistryError(
                f"SQLConfig class: {cls.__name__} must have either a model or a table.",
                "INVALID_SQLCONFIG",
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
