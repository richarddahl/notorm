# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from dataclasses import dataclass

from uno.db.sql_emitters import SQLEmitter
from uno.config import settings


@dataclass
class PathEdgeChcekSQL(SQLEmitter):
    """ """

    def emit_sql(self) -> str:
        function_string = """
            BEGIN
                SELECT 
                IF pare
                    RAISE EXCEPTION 'Path cannot start and end at the same node';
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
