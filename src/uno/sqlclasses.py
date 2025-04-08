# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import Optional, ClassVar

from psycopg import sql
from pydantic import BaseModel, ConfigDict
from sqlalchemy.sql import text
from sqlalchemy.engine.base import Connection
from sqlalchemy import Table

from uno.errors import UnoError
from uno.config import settings


class SQLEmitter(BaseModel):
    exclude_fields: ClassVar[list[str]] = ["table"]
    table: Optional[Table] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def emit_sql(self, connection: Connection) -> None:
        for statement_name, sql_statement in self.model_dump(
            exclude=self.exclude_fields
        ).items():
            connection.execute(text(sql_statement))

    def createsqltrigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:

        trigger_scope = (
            f"{settings.DB_SCHEMA}."
            if db_function
            else f"{settings.DB_SCHEMA}.{self.table.name}_"
        )
        trigger_prefix = self.table.name
        return textwrap.dedent(
            sql.SQL(
                """
            CREATE OR REPLACE TRIGGER {trigger_prefix}_{function_name}_trigger
                {timing} {operation}
                ON {schema_name}.{table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
            )
            .format(
                table_name=sql.SQL(self.table.name),
                trigger_prefix=sql.SQL(trigger_prefix),
                function_name=sql.SQL(function_name),
                timing=sql.SQL(timing),
                operation=sql.SQL(operation),
                for_each=sql.SQL(for_each),
                trigger_scope=sql.SQL(trigger_scope),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

    def createsqlfunction(
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
            else f"{self.table.name}_{function_name}"
        )
        ADMIN_ROLE = sql.SQL(f"{settings.DB_NAME}_admin")
        fnct_string = textwrap.dedent(
            sql.SQL(
                """
            SET ROLE {admin_role};
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            {volatile}
            {security_definer}
            AS $fnct$ 
            {function_string}
            $fnct$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                full_function_name=sql.SQL(full_function_name),
                function_args=sql.SQL(function_args),
                return_type=sql.SQL(return_type),
                volatile=sql.SQL(volatile),
                security_definer=sql.SQL(security_definer),
                function_string=sql.SQL(function_string),
            )
            .as_string()
        )

        if not include_trigger:
            return textwrap.dedent(fnct_string)
        trggr_string = self.createsqltrigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return textwrap.dedent(
            sql.SQL(
                "{fnct_string}\n{trggr_string}".format(
                    fnct_string=fnct_string, trggr_string=trggr_string
                )
            ).as_string()
        )


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
            raise UnoError(
                f"SQLConfig class: {cls.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )

    # End of __init_subclass__

    @classmethod
    def emit_sql(cls, connection: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(table=cls.table).emit_sql(connection)
