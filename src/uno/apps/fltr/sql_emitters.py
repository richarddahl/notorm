# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from pydantic import computed_field
from dataclasses import dataclass

from uno.record.sql.sql_emitter import (
    SQLStatement,
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


class PathEdgeCheck(SQLStatement):
    """ """

    @computed_field
    def validate_path(self) -> str:
        function_string = """
            BEGIN
                SELECT 
                IF pare
                    RAISE EXCEPTION 'Path cannot start and end at the same graph_node';
                END IF;
                RETURN NEW;
            END;
            """

        return self.create_sql_function(
            "validate_path",
            function_string,
            return_type="BOOLEAN",
            include_trigger=False,
            db_function=False,
        )
