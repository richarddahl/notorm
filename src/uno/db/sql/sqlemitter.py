# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import Optional, ClassVar

from psycopg.sql import SQL, Literal
from pydantic import BaseModel, ConfigDict
from sqlalchemy.sql import text
from sqlalchemy.engine.base import Connection
from sqlalchemy import Table

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


class SQLEmitter(BaseModel):
    exclude_fields: ClassVar[list[str]] = ["table"]
    table: Optional[Table] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def emit_sql(self, connection: Connection) -> None:
        for statement_name, sql_statement in self.model_dump(
            exclude=self.exclude_fields
        ).items():
            print(f"Executing {statement_name}...")
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
            SQL(
                """
            CREATE OR REPLACE TRIGGER {trigger_prefix}_{function_name}_trigger
                {timing} {operation}
                ON {schema_name}.{table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
            )
            .format(
                table_name=SQL(self.table.name),
                trigger_prefix=SQL(trigger_prefix),
                function_name=SQL(function_name),
                timing=SQL(timing),
                operation=SQL(operation),
                for_each=SQL(for_each),
                trigger_scope=SQL(trigger_scope),
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
        ADMIN_ROLE = SQL(f"{settings.DB_NAME}_admin")
        fnct_string = textwrap.dedent(
            SQL(
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
            return textwrap.dedent(fnct_string)
        trggr_string = self.createsqltrigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return textwrap.dedent(
            SQL(
                "{fnct_string}\n{trggr_string}".format(
                    fnct_string=fnct_string, trggr_string=trggr_string
                )
            ).as_string()
        )
