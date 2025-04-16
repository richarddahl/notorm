"""
Domain repositories for the SQL module.

This module defines repository interfaces and implementations for the SQL module,
providing data access patterns for SQL statement management.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator, TypeVar, Generic, Union

from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine

from uno.core.result import Result, Success, Failure
from uno.domain.repository import AsyncDomainRepository, DomainRepository

from uno.sql.entities import (
    SQLStatementId,
    SQLEmitterId,
    SQLConfigId,
    SQLStatementType,
    SQLTransactionIsolationLevel,
    SQLStatement,
    SQLExecution,
    SQLEmitter,
    SQLFunction,
    SQLTrigger,
    DatabaseConnectionInfo,
    SQLConfiguration
)


# Repository Protocols
@runtime_checkable
class SQLStatementRepositoryProtocol(Protocol):
    """Protocol for SQL statement repository."""
    
    async def save(self, statement: SQLStatement) -> Result[SQLStatement]:
        """
        Save a SQL statement.
        
        Args:
            statement: The statement to save.
            
        Returns:
            Result containing the saved statement.
        """
        ...
    
    async def get_by_id(self, statement_id: SQLStatementId) -> Result[SQLStatement]:
        """
        Get a SQL statement by ID.
        
        Args:
            statement_id: The statement ID.
            
        Returns:
            Result containing the statement or an error if not found.
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[SQLStatement]:
        """
        Get a SQL statement by name.
        
        Args:
            name: The statement name.
            
        Returns:
            Result containing the statement or an error if not found.
        """
        ...
    
    async def get_by_type(self, statement_type: SQLStatementType) -> Result[List[SQLStatement]]:
        """
        Get SQL statements by type.
        
        Args:
            statement_type: The statement type.
            
        Returns:
            Result containing a list of statements of the specified type.
        """
        ...
    
    async def get_all(self) -> Result[List[SQLStatement]]:
        """
        Get all SQL statements.
        
        Returns:
            Result containing a list of all statements.
        """
        ...
    
    async def delete(self, statement_id: SQLStatementId) -> Result[bool]:
        """
        Delete a SQL statement.
        
        Args:
            statement_id: The statement ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def execute(self, statement: SQLStatement, connection: Connection) -> Result[SQLExecution]:
        """
        Execute a SQL statement.
        
        Args:
            statement: The statement to execute.
            connection: The database connection.
            
        Returns:
            Result containing the execution record.
        """
        ...


@runtime_checkable
class SQLEmitterRepositoryProtocol(Protocol):
    """Protocol for SQL emitter repository."""
    
    async def save(self, emitter: SQLEmitter) -> Result[SQLEmitter]:
        """
        Save a SQL emitter.
        
        Args:
            emitter: The emitter to save.
            
        Returns:
            Result containing the saved emitter.
        """
        ...
    
    async def get_by_id(self, emitter_id: SQLEmitterId) -> Result[SQLEmitter]:
        """
        Get a SQL emitter by ID.
        
        Args:
            emitter_id: The emitter ID.
            
        Returns:
            Result containing the emitter or an error if not found.
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[SQLEmitter]:
        """
        Get a SQL emitter by name.
        
        Args:
            name: The emitter name.
            
        Returns:
            Result containing the emitter or an error if not found.
        """
        ...
    
    async def get_by_statement_type(self, statement_type: SQLStatementType) -> Result[List[SQLEmitter]]:
        """
        Get SQL emitters by statement type they can generate.
        
        Args:
            statement_type: The statement type.
            
        Returns:
            Result containing a list of emitters that can generate the specified statement type.
        """
        ...
    
    async def get_all(self) -> Result[List[SQLEmitter]]:
        """
        Get all SQL emitters.
        
        Returns:
            Result containing a list of all emitters.
        """
        ...
    
    async def delete(self, emitter_id: SQLEmitterId) -> Result[bool]:
        """
        Delete a SQL emitter.
        
        Args:
            emitter_id: The emitter ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...


@runtime_checkable
class SQLConfigurationRepositoryProtocol(Protocol):
    """Protocol for SQL configuration repository."""
    
    async def save(self, configuration: SQLConfiguration) -> Result[SQLConfiguration]:
        """
        Save a SQL configuration.
        
        Args:
            configuration: The configuration to save.
            
        Returns:
            Result containing the saved configuration.
        """
        ...
    
    async def get_by_id(self, config_id: SQLConfigId) -> Result[SQLConfiguration]:
        """
        Get a SQL configuration by ID.
        
        Args:
            config_id: The configuration ID.
            
        Returns:
            Result containing the configuration or an error if not found.
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[SQLConfiguration]:
        """
        Get a SQL configuration by name.
        
        Args:
            name: The configuration name.
            
        Returns:
            Result containing the configuration or an error if not found.
        """
        ...
    
    async def get_all(self) -> Result[List[SQLConfiguration]]:
        """
        Get all SQL configurations.
        
        Returns:
            Result containing a list of all configurations.
        """
        ...
    
    async def delete(self, config_id: SQLConfigId) -> Result[bool]:
        """
        Delete a SQL configuration.
        
        Args:
            config_id: The configuration ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...


@runtime_checkable
class SQLFunctionRepositoryProtocol(Protocol):
    """Protocol for SQL function repository."""
    
    async def save(self, function: SQLFunction) -> Result[SQLFunction]:
        """
        Save a SQL function.
        
        Args:
            function: The function to save.
            
        Returns:
            Result containing the saved function.
        """
        ...
    
    async def get_by_id(self, function_id: str) -> Result[SQLFunction]:
        """
        Get a SQL function by ID.
        
        Args:
            function_id: The function ID.
            
        Returns:
            Result containing the function or an error if not found.
        """
        ...
    
    async def get_by_name(self, schema: str, name: str) -> Result[SQLFunction]:
        """
        Get a SQL function by schema and name.
        
        Args:
            schema: The function schema.
            name: The function name.
            
        Returns:
            Result containing the function or an error if not found.
        """
        ...
    
    async def get_by_schema(self, schema: str) -> Result[List[SQLFunction]]:
        """
        Get SQL functions by schema.
        
        Args:
            schema: The schema name.
            
        Returns:
            Result containing a list of functions in the specified schema.
        """
        ...
    
    async def get_all(self) -> Result[List[SQLFunction]]:
        """
        Get all SQL functions.
        
        Returns:
            Result containing a list of all functions.
        """
        ...
    
    async def delete(self, function_id: str) -> Result[bool]:
        """
        Delete a SQL function.
        
        Args:
            function_id: The function ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def deploy(self, function: SQLFunction, connection: Connection) -> Result[bool]:
        """
        Deploy a SQL function to the database.
        
        Args:
            function: The function to deploy.
            connection: The database connection.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...


@runtime_checkable
class SQLTriggerRepositoryProtocol(Protocol):
    """Protocol for SQL trigger repository."""
    
    async def save(self, trigger: SQLTrigger) -> Result[SQLTrigger]:
        """
        Save a SQL trigger.
        
        Args:
            trigger: The trigger to save.
            
        Returns:
            Result containing the saved trigger.
        """
        ...
    
    async def get_by_id(self, trigger_id: str) -> Result[SQLTrigger]:
        """
        Get a SQL trigger by ID.
        
        Args:
            trigger_id: The trigger ID.
            
        Returns:
            Result containing the trigger or an error if not found.
        """
        ...
    
    async def get_by_name(self, schema: str, name: str) -> Result[SQLTrigger]:
        """
        Get a SQL trigger by schema and name.
        
        Args:
            schema: The trigger schema.
            name: The trigger name.
            
        Returns:
            Result containing the trigger or an error if not found.
        """
        ...
    
    async def get_by_table(self, schema: str, table: str) -> Result[List[SQLTrigger]]:
        """
        Get SQL triggers by table.
        
        Args:
            schema: The schema name.
            table: The table name.
            
        Returns:
            Result containing a list of triggers for the specified table.
        """
        ...
    
    async def get_all(self) -> Result[List[SQLTrigger]]:
        """
        Get all SQL triggers.
        
        Returns:
            Result containing a list of all triggers.
        """
        ...
    
    async def delete(self, trigger_id: str) -> Result[bool]:
        """
        Delete a SQL trigger.
        
        Args:
            trigger_id: The trigger ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def deploy(self, trigger: SQLTrigger, connection: Connection) -> Result[bool]:
        """
        Deploy a SQL trigger to the database.
        
        Args:
            trigger: The trigger to deploy.
            connection: The database connection.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...


@runtime_checkable
class SQLConnectionManagerProtocol(Protocol):
    """Protocol for SQL connection manager."""
    
    async def get_connection(
        self, 
        connection_info: DatabaseConnectionInfo,
        isolation_level: SQLTransactionIsolationLevel = SQLTransactionIsolationLevel.READ_COMMITTED
    ) -> Result[Connection]:
        """
        Get a database connection.
        
        Args:
            connection_info: The connection information.
            isolation_level: The transaction isolation level.
            
        Returns:
            Result containing a database connection.
        """
        ...
    
    async def close_connection(self, connection: Connection) -> Result[bool]:
        """
        Close a database connection.
        
        Args:
            connection: The connection to close.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def get_engine(self, connection_info: DatabaseConnectionInfo) -> Result[Engine]:
        """
        Get a database engine.
        
        Args:
            connection_info: The connection information.
            
        Returns:
            Result containing a database engine.
        """
        ...


# Repository implementations
class InMemorySQLStatementRepository(DomainRepository, SQLStatementRepositoryProtocol):
    """In-memory implementation of SQL statement repository."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statements: Dict[str, SQLStatement] = {}
    
    async def save(self, statement: SQLStatement) -> Result[SQLStatement]:
        """Save a SQL statement."""
        self.statements[statement.id.value] = statement
        return Success(statement)
    
    async def get_by_id(self, statement_id: SQLStatementId) -> Result[SQLStatement]:
        """Get a SQL statement by ID."""
        statement = self.statements.get(statement_id.value)
        if statement is None:
            return Failure(f"SQL statement not found: {statement_id.value}")
        return Success(statement)
    
    async def get_by_name(self, name: str) -> Result[SQLStatement]:
        """Get a SQL statement by name."""
        for statement in self.statements.values():
            if statement.name == name:
                return Success(statement)
        return Failure(f"SQL statement not found: {name}")
    
    async def get_by_type(self, statement_type: SQLStatementType) -> Result[List[SQLStatement]]:
        """Get SQL statements by type."""
        statements = [s for s in self.statements.values() if s.type == statement_type]
        return Success(statements)
    
    async def get_all(self) -> Result[List[SQLStatement]]:
        """Get all SQL statements."""
        return Success(list(self.statements.values()))
    
    async def delete(self, statement_id: SQLStatementId) -> Result[bool]:
        """Delete a SQL statement."""
        if statement_id.value in self.statements:
            del self.statements[statement_id.value]
            return Success(True)
        return Success(False)
    
    async def execute(self, statement: SQLStatement, connection: Connection) -> Result[SQLExecution]:
        """Execute a SQL statement."""
        import time
        
        execution = SQLExecution(
            statement_id=statement.id,
            duration_ms=0.0,
            success=True
        )
        
        try:
            start_time = time.monotonic()
            connection.execute(text(statement.sql))
            duration = time.monotonic() - start_time
            
            execution.duration_ms = duration * 1000
            execution.success = True
            
            return Success(execution)
        except Exception as e:
            execution.success = False
            execution.error_message = str(e)
            
            return Failure(f"SQL execution failed: {str(e)}", execution)


class InMemorySQLEmitterRepository(DomainRepository, SQLEmitterRepositoryProtocol):
    """In-memory implementation of SQL emitter repository."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emitters: Dict[str, SQLEmitter] = {}
    
    async def save(self, emitter: SQLEmitter) -> Result[SQLEmitter]:
        """Save a SQL emitter."""
        self.emitters[emitter.id.value] = emitter
        return Success(emitter)
    
    async def get_by_id(self, emitter_id: SQLEmitterId) -> Result[SQLEmitter]:
        """Get a SQL emitter by ID."""
        emitter = self.emitters.get(emitter_id.value)
        if emitter is None:
            return Failure(f"SQL emitter not found: {emitter_id.value}")
        return Success(emitter)
    
    async def get_by_name(self, name: str) -> Result[SQLEmitter]:
        """Get a SQL emitter by name."""
        for emitter in self.emitters.values():
            if emitter.name == name:
                return Success(emitter)
        return Failure(f"SQL emitter not found: {name}")
    
    async def get_by_statement_type(self, statement_type: SQLStatementType) -> Result[List[SQLEmitter]]:
        """Get SQL emitters by statement type."""
        emitters = [e for e in self.emitters.values() if statement_type in e.statement_types]
        return Success(emitters)
    
    async def get_all(self) -> Result[List[SQLEmitter]]:
        """Get all SQL emitters."""
        return Success(list(self.emitters.values()))
    
    async def delete(self, emitter_id: SQLEmitterId) -> Result[bool]:
        """Delete a SQL emitter."""
        if emitter_id.value in self.emitters:
            del self.emitters[emitter_id.value]
            return Success(True)
        return Success(False)


class InMemorySQLConfigurationRepository(DomainRepository, SQLConfigurationRepositoryProtocol):
    """In-memory implementation of SQL configuration repository."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configurations: Dict[str, SQLConfiguration] = {}
    
    async def save(self, configuration: SQLConfiguration) -> Result[SQLConfiguration]:
        """Save a SQL configuration."""
        self.configurations[configuration.id.value] = configuration
        return Success(configuration)
    
    async def get_by_id(self, config_id: SQLConfigId) -> Result[SQLConfiguration]:
        """Get a SQL configuration by ID."""
        configuration = self.configurations.get(config_id.value)
        if configuration is None:
            return Failure(f"SQL configuration not found: {config_id.value}")
        return Success(configuration)
    
    async def get_by_name(self, name: str) -> Result[SQLConfiguration]:
        """Get a SQL configuration by name."""
        for configuration in self.configurations.values():
            if configuration.name == name:
                return Success(configuration)
        return Failure(f"SQL configuration not found: {name}")
    
    async def get_all(self) -> Result[List[SQLConfiguration]]:
        """Get all SQL configurations."""
        return Success(list(self.configurations.values()))
    
    async def delete(self, config_id: SQLConfigId) -> Result[bool]:
        """Delete a SQL configuration."""
        if config_id.value in self.configurations:
            del self.configurations[config_id.value]
            return Success(True)
        return Success(False)


class InMemorySQLFunctionRepository(DomainRepository, SQLFunctionRepositoryProtocol):
    """In-memory implementation of SQL function repository."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.functions: Dict[str, SQLFunction] = {}
    
    async def save(self, function: SQLFunction) -> Result[SQLFunction]:
        """Save a SQL function."""
        self.functions[function.id] = function
        return Success(function)
    
    async def get_by_id(self, function_id: str) -> Result[SQLFunction]:
        """Get a SQL function by ID."""
        function = self.functions.get(function_id)
        if function is None:
            return Failure(f"SQL function not found: {function_id}")
        return Success(function)
    
    async def get_by_name(self, schema: str, name: str) -> Result[SQLFunction]:
        """Get a SQL function by schema and name."""
        for function in self.functions.values():
            if function.schema == schema and function.name == name:
                return Success(function)
        return Failure(f"SQL function not found: {schema}.{name}")
    
    async def get_by_schema(self, schema: str) -> Result[List[SQLFunction]]:
        """Get SQL functions by schema."""
        functions = [f for f in self.functions.values() if f.schema == schema]
        return Success(functions)
    
    async def get_all(self) -> Result[List[SQLFunction]]:
        """Get all SQL functions."""
        return Success(list(self.functions.values()))
    
    async def delete(self, function_id: str) -> Result[bool]:
        """Delete a SQL function."""
        if function_id in self.functions:
            del self.functions[function_id]
            return Success(True)
        return Success(False)
    
    async def deploy(self, function: SQLFunction, connection: Connection) -> Result[bool]:
        """Deploy a SQL function to the database."""
        try:
            sql = function.to_sql()
            connection.execute(text(sql))
            return Success(True)
        except Exception as e:
            return Failure(f"Failed to deploy SQL function: {str(e)}")


class InMemorySQLTriggerRepository(DomainRepository, SQLTriggerRepositoryProtocol):
    """In-memory implementation of SQL trigger repository."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.triggers: Dict[str, SQLTrigger] = {}
    
    async def save(self, trigger: SQLTrigger) -> Result[SQLTrigger]:
        """Save a SQL trigger."""
        self.triggers[trigger.id] = trigger
        return Success(trigger)
    
    async def get_by_id(self, trigger_id: str) -> Result[SQLTrigger]:
        """Get a SQL trigger by ID."""
        trigger = self.triggers.get(trigger_id)
        if trigger is None:
            return Failure(f"SQL trigger not found: {trigger_id}")
        return Success(trigger)
    
    async def get_by_name(self, schema: str, name: str) -> Result[SQLTrigger]:
        """Get a SQL trigger by schema and name."""
        for trigger in self.triggers.values():
            if trigger.schema == schema and trigger.name == name:
                return Success(trigger)
        return Failure(f"SQL trigger not found: {schema}.{name}")
    
    async def get_by_table(self, schema: str, table: str) -> Result[List[SQLTrigger]]:
        """Get SQL triggers by table."""
        triggers = [t for t in self.triggers.values() if t.schema == schema and t.table == table]
        return Success(triggers)
    
    async def get_all(self) -> Result[List[SQLTrigger]]:
        """Get all SQL triggers."""
        return Success(list(self.triggers.values()))
    
    async def delete(self, trigger_id: str) -> Result[bool]:
        """Delete a SQL trigger."""
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            return Success(True)
        return Success(False)
    
    async def deploy(self, trigger: SQLTrigger, connection: Connection) -> Result[bool]:
        """Deploy a SQL trigger to the database."""
        try:
            sql = trigger.to_sql()
            connection.execute(text(sql))
            return Success(True)
        except Exception as e:
            return Failure(f"Failed to deploy SQL trigger: {str(e)}")