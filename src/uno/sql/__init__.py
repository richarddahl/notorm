# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL generation and execution for database operations.

This package provides tools for generating and executing SQL statements
for database operations including creating tables, functions, triggers,
and other database objects.
"""

# Re-export primary classes for backward compatibility
from uno.sql.registry import SQLConfigRegistry
from uno.sql.config import SQLConfig
from uno.sql.emitter import SQLEmitter, SQLGenerator, SQLExecutor
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.observers import SQLObserver, LoggingSQLObserver

# Re-export builders
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder

# Re-export common emitters
from uno.sql.emitters import (
    AlterGrants,
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
)

__all__ = [
    "SQLConfigRegistry",
    "SQLConfig",
    "SQLEmitter",
    "SQLGenerator",
    "SQLExecutor",
    "SQLStatement",
    "SQLStatementType",
    "SQLObserver",
    "LoggingSQLObserver",
    "SQLFunctionBuilder",
    "SQLTriggerBuilder",
    "AlterGrants",
    "RecordUserAuditFunction",
    "InsertMetaRecordTrigger",
]
