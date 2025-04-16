"""
Domain provider for the SQL module.

This module provides dependency injection configuration for the SQL module.
"""

from typing import Optional, Any, Dict, Type, List, cast

import inject
from sqlalchemy import Connection

from uno.dependencies.container import UnoContainer
from uno.core.result import Result

from uno.sql.entities import (
    SQLStatementId,
    SQLEmitterId,
    SQLConfigId,
    SQLStatementType,
    SQLStatement,
    SQLExecution,
    SQLEmitter,
    SQLFunction,
    SQLTrigger,
    DatabaseConnectionInfo,
    SQLConfiguration
)
from uno.sql.domain_repositories import (
    SQLStatementRepositoryProtocol,
    SQLEmitterRepositoryProtocol,
    SQLConfigurationRepositoryProtocol,
    SQLFunctionRepositoryProtocol,
    SQLTriggerRepositoryProtocol,
    SQLConnectionManagerProtocol,
    InMemorySQLStatementRepository,
    InMemorySQLEmitterRepository,
    InMemorySQLConfigurationRepository,
    InMemorySQLFunctionRepository,
    InMemorySQLTriggerRepository
)
from uno.sql.domain_services import (
    SQLStatementServiceProtocol,
    SQLEmitterServiceProtocol, 
    SQLConfigurationServiceProtocol,
    SQLFunctionServiceProtocol,
    SQLTriggerServiceProtocol,
    SQLConnectionServiceProtocol,
    SQLStatementService,
    SQLEmitterService,
    SQLConfigurationService,
    SQLFunctionService,
    SQLTriggerService,
    SQLConnectionService
)


def configure_sql_dependencies(container: UnoContainer) -> None:
    """
    Configure SQL dependencies in the container.
    
    Args:
        container: The dependency injection container.
    """
    # Register repositories
    container.bind(
        SQLStatementRepositoryProtocol,
        InMemorySQLStatementRepository
    )
    
    container.bind(
        SQLEmitterRepositoryProtocol,
        InMemorySQLEmitterRepository
    )
    
    container.bind(
        SQLConfigurationRepositoryProtocol,
        InMemorySQLConfigurationRepository
    )
    
    container.bind(
        SQLFunctionRepositoryProtocol,
        InMemorySQLFunctionRepository
    )
    
    container.bind(
        SQLTriggerRepositoryProtocol,
        InMemorySQLTriggerRepository
    )
    
    # Register services
    container.bind(
        SQLConnectionServiceProtocol,
        SQLConnectionService
    )
    
    container.bind(
        SQLStatementServiceProtocol,
        SQLStatementService
    )
    
    container.bind(
        SQLEmitterServiceProtocol,
        SQLEmitterService
    )
    
    container.bind(
        SQLConfigurationServiceProtocol,
        SQLConfigurationService
    )
    
    container.bind(
        SQLFunctionServiceProtocol,
        SQLFunctionService
    )
    
    container.bind(
        SQLTriggerServiceProtocol,
        SQLTriggerService
    )


# Helper functions for accessing domain services
async def get_sql_statement_service() -> SQLStatementServiceProtocol:
    """
    Get the SQL statement service.
    
    Returns:
        The SQL statement service.
    """
    return inject.instance(SQLStatementServiceProtocol)


async def get_sql_emitter_service() -> SQLEmitterServiceProtocol:
    """
    Get the SQL emitter service.
    
    Returns:
        The SQL emitter service.
    """
    return inject.instance(SQLEmitterServiceProtocol)


async def get_sql_configuration_service() -> SQLConfigurationServiceProtocol:
    """
    Get the SQL configuration service.
    
    Returns:
        The SQL configuration service.
    """
    return inject.instance(SQLConfigurationServiceProtocol)


async def get_sql_function_service() -> SQLFunctionServiceProtocol:
    """
    Get the SQL function service.
    
    Returns:
        The SQL function service.
    """
    return inject.instance(SQLFunctionServiceProtocol)


async def get_sql_trigger_service() -> SQLTriggerServiceProtocol:
    """
    Get the SQL trigger service.
    
    Returns:
        The SQL trigger service.
    """
    return inject.instance(SQLTriggerServiceProtocol)


async def get_sql_connection_service() -> SQLConnectionServiceProtocol:
    """
    Get the SQL connection service.
    
    Returns:
        The SQL connection service.
    """
    return inject.instance(SQLConnectionServiceProtocol)


# Convenience functions for common SQL operations
async def create_sql_statement(
    name: str,
    statement_type: SQLStatementType,
    sql: str,
    depends_on: Optional[List[str]] = None
) -> Result[SQLStatement]:
    """
    Create a new SQL statement.
    
    Args:
        name: Statement name.
        statement_type: Statement type.
        sql: SQL code.
        depends_on: Optional list of statement names this one depends on.
        
    Returns:
        Result containing the created statement.
    """
    service = await get_sql_statement_service()
    return await service.create_statement(name, statement_type, sql, depends_on)


async def execute_sql_statement(
    statement: SQLStatement,
    connection: Connection
) -> Result[SQLExecution]:
    """
    Execute a SQL statement.
    
    Args:
        statement: Statement to execute.
        connection: Database connection.
        
    Returns:
        Result containing execution details.
    """
    service = await get_sql_statement_service()
    return await service.execute_statement(statement, connection)


async def create_sql_function(
    schema: str,
    name: str,
    body: str,
    args: str = "",
    return_type: str = "TRIGGER",
    language: str = "plpgsql",
    volatility: str = "VOLATILE",
    security_definer: bool = False
) -> Result[SQLFunction]:
    """
    Create a new SQL function.
    
    Args:
        schema: Schema name.
        name: Function name.
        body: Function body.
        args: Function arguments.
        return_type: Return type.
        language: Function language.
        volatility: Function volatility.
        security_definer: Whether this is a security definer function.
        
    Returns:
        Result containing the created function.
    """
    service = await get_sql_function_service()
    return await service.create_function(
        schema, name, body, args, return_type, language, volatility, security_definer
    )


async def create_sql_trigger(
    schema: str,
    name: str,
    table: str,
    function_name: str,
    events: List[str],
    when: Optional[str] = None,
    for_each: str = "ROW"
) -> Result[SQLTrigger]:
    """
    Create a new SQL trigger.
    
    Args:
        schema: Schema name.
        name: Trigger name.
        table: Table name.
        function_name: Function name.
        events: Trigger events.
        when: Optional when condition.
        for_each: FOR EACH ROW or FOR EACH STATEMENT.
        
    Returns:
        Result containing the created trigger.
    """
    service = await get_sql_trigger_service()
    return await service.create_trigger(
        schema, name, table, function_name, events, when, for_each
    )


async def create_database_connection(
    db_name: str,
    db_user: str,
    db_host: str,
    db_port: int = 5432,
    db_schema: str = "public"
) -> Result[DatabaseConnectionInfo]:
    """
    Create database connection information.
    
    Args:
        db_name: Database name.
        db_user: Database user.
        db_host: Database host.
        db_port: Database port.
        db_schema: Schema name.
        
    Returns:
        Result containing the connection information.
    """
    service = await get_sql_connection_service()
    return await service.create_connection(
        db_name, db_user, db_host, db_port, db_schema
    )


async def execute_sql(
    connection_info: DatabaseConnectionInfo,
    sql: str,
    params: Optional[Dict[str, Any]] = None
) -> Result[Any]:
    """
    Execute SQL on a database.
    
    Args:
        connection_info: Connection information.
        sql: SQL to execute.
        params: Optional SQL parameters.
        
    Returns:
        Result containing execution result.
    """
    service = await get_sql_connection_service()
    return await service.execute_sql(connection_info, sql, params)


# Register with FastAPI dependency system
def get_sql_dependencies():
    """
    Get dependencies for use with FastAPI.
    
    This function can be called from FastAPI app startup to register
    the SQL module's dependencies with the application.
    """
    from fastapi import Depends
    from uno.dependencies.fastapi_integration import (
        inject_dependency,
        register_dependency
    )
    
    # Register domain services for injection in FastAPI routes
    register_dependency(SQLStatementServiceProtocol, lambda: inject.instance(SQLStatementServiceProtocol))
    register_dependency(SQLEmitterServiceProtocol, lambda: inject.instance(SQLEmitterServiceProtocol))
    register_dependency(SQLConfigurationServiceProtocol, lambda: inject.instance(SQLConfigurationServiceProtocol))
    register_dependency(SQLFunctionServiceProtocol, lambda: inject.instance(SQLFunctionServiceProtocol))
    register_dependency(SQLTriggerServiceProtocol, lambda: inject.instance(SQLTriggerServiceProtocol))
    register_dependency(SQLConnectionServiceProtocol, lambda: inject.instance(SQLConnectionServiceProtocol))
    
    # Return dependency accessors for FastAPI
    return {
        "get_sql_statement_service": Depends(inject_dependency(SQLStatementServiceProtocol)),
        "get_sql_emitter_service": Depends(inject_dependency(SQLEmitterServiceProtocol)),
        "get_sql_configuration_service": Depends(inject_dependency(SQLConfigurationServiceProtocol)),
        "get_sql_function_service": Depends(inject_dependency(SQLFunctionServiceProtocol)),
        "get_sql_trigger_service": Depends(inject_dependency(SQLTriggerServiceProtocol)),
        "get_sql_connection_service": Depends(inject_dependency(SQLConnectionServiceProtocol)),
    }