# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Any

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, computed_field

from psycopg.sql import SQL, Literal

from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import DeclarativeBase

from uno.config import settings

# SQL Literal and Identifier objects are used to create SQL strings
# that are passed to the database for execution.

# SQL Literals
# These are Necessary for searchiing pg_roles
LIT_ADMIN_ROLE = Literal(f"{settings.DB_NAME}_admin")
LIT_WRITER_ROLE = Literal(f"{settings.DB_NAME}_writer")
LIT_READER_ROLE = Literal(f"{settings.DB_NAME}_reader")
LIT_LOGIN_ROLE = Literal(f"{settings.DB_NAME}_login")
LIT_BASE_ROLE = Literal(f"{settings.DB_NAME}_base_role")

# SQL
ADMIN_ROLE = SQL(f"{settings.DB_NAME}_admin")
WRITER_ROLE = SQL(f"{settings.DB_NAME}_writer")
READER_ROLE = SQL(f"{settings.DB_NAME}_reader")
LOGIN_ROLE = SQL(f"{settings.DB_NAME}_login")
BASE_ROLE = SQL(f"{settings.DB_NAME}_base_role")
DB_NAME = SQL(settings.DB_NAME)
DB_SCHEMA = SQL(settings.DB_SCHEMA)


class SQLEmitter(ABC, BaseModel):

    @computed_field
    def table_name(self) -> str:
        return None

    @abstractmethod
    def _emit_sql(self, conn: Connection) -> None:
        raise NotImplementedError

    def create_sql_trigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:

        trigger_scope = (
            f"{settings.DB_SCHEMA}." if db_function else f"{self.table_name}_"
        )
        trigger_prefix = self.table_name.split(".")[1]
        return (
            SQL(
                """
            CREATE OR REPLACE TRIGGER {trigger_prefix}_{function_name}_trigger
                {timing} {operation}
                ON {table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
            )
            .format(
                table_name=SQL(self.table_name),
                trigger_prefix=SQL(trigger_prefix),
                function_name=SQL(function_name),
                timing=SQL(timing),
                operation=SQL(operation),
                for_each=SQL(for_each),
                trigger_scope=SQL(trigger_scope),
                db_schema=DB_SCHEMA,
            )
            .as_string()
        )

    def create_sql_function(
        self,
        function_name: str,
        function_string: str,
        function_args: str = "",
        db_function: bool = True,
        return_type: str = "TRIGGER",
        volatile: str = "VOLATILE",
        include_trigger: bool = False,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        security_definer: str = "",
    ) -> str:

        if function_args and include_trigger is True:
            raise ValueError(
                "Function arguments cannot be used when creating a trigger function."
            )
        full_function_name = (
            f"{settings.DB_SCHEMA}.{function_name}"
            if db_function
            else f"{self.table_name}_{function_name}"
        )
        ADMIN_ROLE = SQL(f"{settings.DB_NAME}_admin")
        fnct_string = (
            SQL(
                """
            SET ROLE {admin_role};
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            {volatile}
            {security_definer}
            AS $$
            {function_string}
            $$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                full_function_name=SQL(full_function_name),
                function_args=SQL(function_args),
                return_type=SQL(return_type),
                volatile=SQL(volatile),
                security_definer=SQL(security_definer),
                function_string=SQL(function_string),
            )
            .as_string()
        )

        if not include_trigger:
            return fnct_string
        trggr_string = self.create_sql_trigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return SQL(
            "{fnct_string}\n{trggr_string}".format(
                fnct_string=fnct_string, trggr_string=trggr_string
            )
        ).as_string()


class TableSQLEmitter(SQLEmitter):
    obj_class: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def table_name(self) -> str:
        return self.obj_class.table.fullname
