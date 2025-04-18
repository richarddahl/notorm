# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL generation and execution for database operations.

This package provides tools for generating and executing SQL statements
for database operations including creating tables, functions, triggers,
and other database objects.
"""

# Use the domain-based SQL implementation instead
# See domain repositories and services below

# Error types
from uno.sql.errors import (
    SQLErrorCode,
    SQLStatementError,
    SQLExecutionError,
    SQLSyntaxError,
    SQLEmitterError,
    SQLEmitterInvalidConfigError,
    SQLRegistryClassNotFoundError,
    SQLRegistryClassAlreadyExistsError,
    SQLConfigError,
    SQLConfigInvalidError,
    register_sql_errors,
)


# Register SQL errors
register_sql_errors()

__all__ = [
    # Modern domain-based components only
    # Error types
    "SQLErrorCode",
    "SQLStatementError",
    "SQLExecutionError",
    "SQLSyntaxError",
    "SQLEmitterError",
    "SQLEmitterInvalidConfigError",
    "SQLRegistryClassNotFoundError",
    "SQLRegistryClassAlreadyExistsError",
    "SQLConfigError",
    "SQLConfigInvalidError",
    # Domain entities
    "SQLStatementId",
    "SQLEmitterId",
    "SQLConfigId",
    "SQLTransactionIsolationLevel",
    "SQLFunctionVolatility",
    "SQLFunctionLanguage",
    "SQLFunction",
    "SQLTrigger",
    "DatabaseConnectionInfo",
    "SQLConfiguration",
    # Domain repositories
    "SQLStatementRepositoryProtocol",
    "SQLEmitterRepositoryProtocol",
    "SQLConfigurationRepositoryProtocol",
    "SQLFunctionRepositoryProtocol",
    "SQLTriggerRepositoryProtocol",
    "SQLConnectionManagerProtocol",
    "InMemorySQLStatementRepository",
    "InMemorySQLEmitterRepository",
    "InMemorySQLConfigurationRepository",
    "InMemorySQLFunctionRepository",
    "InMemorySQLTriggerRepository",
    # Domain services
    "SQLStatementServiceProtocol",
    "SQLEmitterServiceProtocol",
    "SQLConfigurationServiceProtocol",
    "SQLFunctionServiceProtocol",
    "SQLTriggerServiceProtocol",
    "SQLConnectionServiceProtocol",
    "SQLStatementService",
    "SQLEmitterService",
    "SQLConfigurationService",
    "SQLFunctionService",
    "SQLTriggerService",
    "SQLConnectionService",
    # Domain provider
    "configure_sql_dependencies",
    "get_sql_statement_service",
    "get_sql_emitter_service",
    "get_sql_configuration_service",
    "get_sql_function_service",
    "get_sql_trigger_service",
    "get_sql_connection_service",
    "create_sql_statement",
    "execute_sql_statement",
    "create_sql_function",
    "create_sql_trigger",
    "create_database_connection",
    "execute_sql",
    "get_sql_dependencies",
]
