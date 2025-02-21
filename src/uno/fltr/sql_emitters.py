# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from psycopg.sql import SQL, Identifier, Literal

from sqlalchemy import text
from sqlalchemy.engine import Engine


from uno.db.sql.sql_emitter import (
    SQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
    LOGIN_ROLE,
    BASE_ROLE,
    LIT_BASE_ROLE,
    LIT_READER_ROLE,
    LIT_WRITER_ROLE,
    LIT_ADMIN_ROLE,
    LIT_LOGIN_ROLE,
)
from uno.config import settings


@dataclass
class PathEdgeChcek(SQLEmitter):
    """ """

    def emit_sql(self, conn: Connection) -> None:
        function_string = """
            BEGIN
                SELECT 
                IF pare
                    RAISE EXCEPTION 'Path cannot start and end at the same node';
                END IF;
                RETURN NEW;
            END;
            """

        conn.execute(
            text(
                self.create_sql_function(
                    "validate_path",
                    function_string,
                    return_type="BOOLEAN",
                    include_trigger=False,
                    db_function=False,
                )
            )
        )
