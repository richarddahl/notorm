"""
Domain services for the SQL module.

This module defines service classes for the SQL module,
providing business logic for SQL statement management.
"""

import time
import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable, Union, cast
import uuid

from sqlalchemy import Connection, Engine, text
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import SQLAlchemyError

from uno.core.result import Result, Success, Failure
from uno.domain.service import DomainService
from uno.database.config import ConnectionConfig
from uno.database.engine.sync import SyncEngineFactory, sync_connection

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
from uno.sql.domain_repositories import (
    SQLStatementRepositoryProtocol,
    SQLEmitterRepositoryProtocol,
    SQLConfigurationRepositoryProtocol,
    SQLFunctionRepositoryProtocol,
    SQLTriggerRepositoryProtocol,
    SQLConnectionManagerProtocol
)


# Service protocols
@runtime_checkable
class SQLStatementServiceProtocol(Protocol):
    """Protocol for SQL statement service."""
    
    async def create_statement(
        self,
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
        ...
    
    async def get_statement(self, statement_id: SQLStatementId) -> Result[SQLStatement]:
        """
        Get a SQL statement by ID.
        
        Args:
            statement_id: Statement ID.
            
        Returns:
            Result containing the statement or an error if not found.
        """
        ...
    
    async def get_statement_by_name(self, name: str) -> Result[SQLStatement]:
        """
        Get a SQL statement by name.
        
        Args:
            name: Statement name.
            
        Returns:
            Result containing the statement or an error if not found.
        """
        ...
    
    async def get_statements_by_type(self, statement_type: SQLStatementType) -> Result[List[SQLStatement]]:
        """
        Get statements by type.
        
        Args:
            statement_type: Statement type.
            
        Returns:
            Result containing statements of the given type.
        """
        ...
    
    async def list_statements(self) -> Result[List[SQLStatement]]:
        """
        List all statements.
        
        Returns:
            Result containing all statements.
        """
        ...
    
    async def update_statement(
        self,
        statement_id: SQLStatementId,
        sql: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ) -> Result[SQLStatement]:
        """
        Update a SQL statement.
        
        Args:
            statement_id: Statement ID.
            sql: Optional new SQL code.
            depends_on: Optional new dependencies.
            
        Returns:
            Result containing the updated statement.
        """
        ...
    
    async def delete_statement(self, statement_id: SQLStatementId) -> Result[bool]:
        """
        Delete a SQL statement.
        
        Args:
            statement_id: Statement ID.
            
        Returns:
            Result containing a success flag.
        """
        ...
    
    async def execute_statement(
        self,
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
        ...
    
    async def execute_statement_by_id(
        self,
        statement_id: SQLStatementId,
        connection: Connection
    ) -> Result[SQLExecution]:
        """
        Execute a SQL statement by ID.
        
        Args:
            statement_id: Statement ID.
            connection: Database connection.
            
        Returns:
            Result containing execution details.
        """
        ...


@runtime_checkable
class SQLEmitterServiceProtocol(Protocol):
    """Protocol for SQL emitter service."""
    
    async def register_emitter(
        self,
        name: str,
        statement_types: List[SQLStatementType],
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[SQLEmitter]:
        """
        Register a new SQL emitter.
        
        Args:
            name: Emitter name.
            statement_types: Types of statements this emitter can generate.
            description: Optional description.
            configuration: Optional configuration.
            
        Returns:
            Result containing the registered emitter.
        """
        ...
    
    async def get_emitter(self, emitter_id: SQLEmitterId) -> Result[SQLEmitter]:
        """
        Get an emitter by ID.
        
        Args:
            emitter_id: Emitter ID.
            
        Returns:
            Result containing the emitter or an error if not found.
        """
        ...
    
    async def get_emitter_by_name(self, name: str) -> Result[SQLEmitter]:
        """
        Get an emitter by name.
        
        Args:
            name: Emitter name.
            
        Returns:
            Result containing the emitter or an error if not found.
        """
        ...
    
    async def get_emitters_by_statement_type(self, statement_type: SQLStatementType) -> Result[List[SQLEmitter]]:
        """
        Get emitters by statement type.
        
        Args:
            statement_type: Statement type.
            
        Returns:
            Result containing emitters that can generate the given type.
        """
        ...
    
    async def list_emitters(self) -> Result[List[SQLEmitter]]:
        """
        List all emitters.
        
        Returns:
            Result containing all emitters.
        """
        ...
    
    async def update_emitter(
        self,
        emitter_id: SQLEmitterId,
        statement_types: Optional[List[SQLStatementType]] = None,
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[SQLEmitter]:
        """
        Update an emitter.
        
        Args:
            emitter_id: Emitter ID.
            statement_types: Optional new statement types.
            description: Optional new description.
            configuration: Optional new configuration.
            
        Returns:
            Result containing the updated emitter.
        """
        ...
    
    async def delete_emitter(self, emitter_id: SQLEmitterId) -> Result[bool]:
        """
        Delete an emitter.
        
        Args:
            emitter_id: Emitter ID.
            
        Returns:
            Result containing a success flag.
        """
        ...
    
    async def generate_statements(
        self,
        emitter_id: SQLEmitterId,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[List[SQLStatement]]:
        """
        Generate statements using an emitter.
        
        Args:
            emitter_id: Emitter ID.
            configuration: Optional configuration overrides.
            
        Returns:
            Result containing generated statements.
        """
        ...


@runtime_checkable
class SQLConfigurationServiceProtocol(Protocol):
    """Protocol for SQL configuration service."""
    
    async def create_configuration(
        self,
        name: str,
        description: Optional[str] = None,
        connection_info: Optional[DatabaseConnectionInfo] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[SQLConfiguration]:
        """
        Create a new SQL configuration.
        
        Args:
            name: Configuration name.
            description: Optional description.
            connection_info: Optional database connection info.
            metadata: Optional metadata.
            
        Returns:
            Result containing the created configuration.
        """
        ...
    
    async def get_configuration(self, config_id: SQLConfigId) -> Result[SQLConfiguration]:
        """
        Get a configuration by ID.
        
        Args:
            config_id: Configuration ID.
            
        Returns:
            Result containing the configuration or an error if not found.
        """
        ...
    
    async def get_configuration_by_name(self, name: str) -> Result[SQLConfiguration]:
        """
        Get a configuration by name.
        
        Args:
            name: Configuration name.
            
        Returns:
            Result containing the configuration or an error if not found.
        """
        ...
    
    async def list_configurations(self) -> Result[List[SQLConfiguration]]:
        """
        List all configurations.
        
        Returns:
            Result containing all configurations.
        """
        ...
    
    async def update_configuration(
        self,
        config_id: SQLConfigId,
        name: Optional[str] = None,
        description: Optional[str] = None,
        connection_info: Optional[DatabaseConnectionInfo] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[SQLConfiguration]:
        """
        Update a configuration.
        
        Args:
            config_id: Configuration ID.
            name: Optional new name.
            description: Optional new description.
            connection_info: Optional new connection info.
            metadata: Optional new metadata.
            
        Returns:
            Result containing the updated configuration.
        """
        ...
    
    async def delete_configuration(self, config_id: SQLConfigId) -> Result[bool]:
        """
        Delete a configuration.
        
        Args:
            config_id: Configuration ID.
            
        Returns:
            Result containing a success flag.
        """
        ...
    
    async def add_emitter_to_configuration(
        self,
        config_id: SQLConfigId,
        emitter_id: SQLEmitterId
    ) -> Result[SQLConfiguration]:
        """
        Add an emitter to a configuration.
        
        Args:
            config_id: Configuration ID.
            emitter_id: Emitter ID.
            
        Returns:
            Result containing the updated configuration.
        """
        ...
    
    async def remove_emitter_from_configuration(
        self,
        config_id: SQLConfigId,
        emitter_id: SQLEmitterId
    ) -> Result[SQLConfiguration]:
        """
        Remove an emitter from a configuration.
        
        Args:
            config_id: Configuration ID.
            emitter_id: Emitter ID.
            
        Returns:
            Result containing the updated configuration.
        """
        ...
    
    async def execute_configuration(
        self,
        config_id: SQLConfigId,
        connection: Optional[Connection] = None
    ) -> Result[List[SQLExecution]]:
        """
        Execute all statements in a configuration.
        
        Args:
            config_id: Configuration ID.
            connection: Optional database connection.
            
        Returns:
            Result containing execution details.
        """
        ...


@runtime_checkable
class SQLFunctionServiceProtocol(Protocol):
    """Protocol for SQL function service."""
    
    async def create_function(
        self,
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
        ...
    
    async def get_function(self, function_id: str) -> Result[SQLFunction]:
        """
        Get a function by ID.
        
        Args:
            function_id: Function ID.
            
        Returns:
            Result containing the function or an error if not found.
        """
        ...
    
    async def get_function_by_name(self, schema: str, name: str) -> Result[SQLFunction]:
        """
        Get a function by schema and name.
        
        Args:
            schema: Schema name.
            name: Function name.
            
        Returns:
            Result containing the function or an error if not found.
        """
        ...
    
    async def get_functions_by_schema(self, schema: str) -> Result[List[SQLFunction]]:
        """
        Get functions by schema.
        
        Args:
            schema: Schema name.
            
        Returns:
            Result containing functions in the given schema.
        """
        ...
    
    async def list_functions(self) -> Result[List[SQLFunction]]:
        """
        List all functions.
        
        Returns:
            Result containing all functions.
        """
        ...
    
    async def update_function(
        self,
        function_id: str,
        body: Optional[str] = None,
        args: Optional[str] = None,
        return_type: Optional[str] = None,
        language: Optional[str] = None,
        volatility: Optional[str] = None,
        security_definer: Optional[bool] = None
    ) -> Result[SQLFunction]:
        """
        Update a function.
        
        Args:
            function_id: Function ID.
            body: Optional new body.
            args: Optional new arguments.
            return_type: Optional new return type.
            language: Optional new language.
            volatility: Optional new volatility.
            security_definer: Optional new security definer flag.
            
        Returns:
            Result containing the updated function.
        """
        ...
    
    async def delete_function(self, function_id: str) -> Result[bool]:
        """
        Delete a function.
        
        Args:
            function_id: Function ID.
            
        Returns:
            Result containing a success flag.
        """
        ...
    
    async def deploy_function(
        self,
        function_id: str,
        connection: Connection
    ) -> Result[bool]:
        """
        Deploy a function to the database.
        
        Args:
            function_id: Function ID.
            connection: Database connection.
            
        Returns:
            Result containing a success flag.
        """
        ...


@runtime_checkable
class SQLTriggerServiceProtocol(Protocol):
    """Protocol for SQL trigger service."""
    
    async def create_trigger(
        self,
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
        ...
    
    async def get_trigger(self, trigger_id: str) -> Result[SQLTrigger]:
        """
        Get a trigger by ID.
        
        Args:
            trigger_id: Trigger ID.
            
        Returns:
            Result containing the trigger or an error if not found.
        """
        ...
    
    async def get_trigger_by_name(self, schema: str, name: str) -> Result[SQLTrigger]:
        """
        Get a trigger by schema and name.
        
        Args:
            schema: Schema name.
            name: Trigger name.
            
        Returns:
            Result containing the trigger or an error if not found.
        """
        ...
    
    async def get_triggers_by_table(self, schema: str, table: str) -> Result[List[SQLTrigger]]:
        """
        Get triggers by table.
        
        Args:
            schema: Schema name.
            table: Table name.
            
        Returns:
            Result containing triggers for the given table.
        """
        ...
    
    async def list_triggers(self) -> Result[List[SQLTrigger]]:
        """
        List all triggers.
        
        Returns:
            Result containing all triggers.
        """
        ...
    
    async def update_trigger(
        self,
        trigger_id: str,
        events: Optional[List[str]] = None,
        when: Optional[str] = None,
        for_each: Optional[str] = None
    ) -> Result[SQLTrigger]:
        """
        Update a trigger.
        
        Args:
            trigger_id: Trigger ID.
            events: Optional new events.
            when: Optional new when condition.
            for_each: Optional new for_each setting.
            
        Returns:
            Result containing the updated trigger.
        """
        ...
    
    async def delete_trigger(self, trigger_id: str) -> Result[bool]:
        """
        Delete a trigger.
        
        Args:
            trigger_id: Trigger ID.
            
        Returns:
            Result containing a success flag.
        """
        ...
    
    async def deploy_trigger(
        self,
        trigger_id: str,
        connection: Connection
    ) -> Result[bool]:
        """
        Deploy a trigger to the database.
        
        Args:
            trigger_id: Trigger ID.
            connection: Database connection.
            
        Returns:
            Result containing a success flag.
        """
        ...


@runtime_checkable
class SQLConnectionServiceProtocol(Protocol):
    """Protocol for SQL connection service."""
    
    async def create_connection(
        self,
        db_name: str,
        db_user: str,
        db_host: str,
        db_port: int = 5432,
        db_schema: str = "public",
        admin_role: Optional[str] = None,
        writer_role: Optional[str] = None,
        reader_role: Optional[str] = None
    ) -> Result[DatabaseConnectionInfo]:
        """
        Create connection information.
        
        Args:
            db_name: Database name.
            db_user: Database user.
            db_host: Database host.
            db_port: Database port.
            db_schema: Schema name.
            admin_role: Optional admin role name.
            writer_role: Optional writer role name.
            reader_role: Optional reader role name.
            
        Returns:
            Result containing the connection info.
        """
        ...
    
    async def get_connection(
        self,
        connection_info: DatabaseConnectionInfo,
        isolation_level: SQLTransactionIsolationLevel = SQLTransactionIsolationLevel.READ_COMMITTED
    ) -> Result[Connection]:
        """
        Get a database connection.
        
        Args:
            connection_info: Connection information.
            isolation_level: Transaction isolation level.
            
        Returns:
            Result containing a database connection.
        """
        ...
    
    async def close_connection(self, connection: Connection) -> Result[bool]:
        """
        Close a database connection.
        
        Args:
            connection: Database connection.
            
        Returns:
            Result containing a success flag.
        """
        ...
    
    async def execute_sql(
        self,
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
        ...


# Service implementations
class SQLStatementService(DomainService, SQLStatementServiceProtocol):
    """Service for SQL statement management."""
    
    def __init__(self, repository: SQLStatementRepositoryProtocol):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def create_statement(
        self,
        name: str,
        statement_type: SQLStatementType,
        sql: str,
        depends_on: Optional[List[str]] = None
    ) -> Result[SQLStatement]:
        """Create a new SQL statement."""
        try:
            # Generate a unique ID
            statement_id = SQLStatementId(str(uuid.uuid4()))
            
            # Create the statement
            statement = SQLStatement(
                id=statement_id,
                name=name,
                type=statement_type,
                sql=sql,
                depends_on=depends_on or []
            )
            
            # Save the statement
            return await self.repository.save(statement)
        except Exception as e:
            self.logger.error(f"Error creating SQL statement: {e}")
            return Failure(f"Failed to create SQL statement: {str(e)}")
    
    async def get_statement(self, statement_id: SQLStatementId) -> Result[SQLStatement]:
        """Get a SQL statement by ID."""
        return await self.repository.get_by_id(statement_id)
    
    async def get_statement_by_name(self, name: str) -> Result[SQLStatement]:
        """Get a SQL statement by name."""
        return await self.repository.get_by_name(name)
    
    async def get_statements_by_type(self, statement_type: SQLStatementType) -> Result[List[SQLStatement]]:
        """Get statements by type."""
        return await self.repository.get_by_type(statement_type)
    
    async def list_statements(self) -> Result[List[SQLStatement]]:
        """List all statements."""
        return await self.repository.get_all()
    
    async def update_statement(
        self,
        statement_id: SQLStatementId,
        sql: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ) -> Result[SQLStatement]:
        """Update a SQL statement."""
        # Get the current statement
        result = await self.repository.get_by_id(statement_id)
        if not result.is_success():
            return result
        
        statement = result.value
        
        # Update fields if provided
        if sql is not None:
            statement.sql = sql
        
        if depends_on is not None:
            statement.depends_on = depends_on
        
        # Save the updated statement
        return await self.repository.save(statement)
    
    async def delete_statement(self, statement_id: SQLStatementId) -> Result[bool]:
        """Delete a SQL statement."""
        return await self.repository.delete(statement_id)
    
    async def execute_statement(
        self,
        statement: SQLStatement,
        connection: Connection
    ) -> Result[SQLExecution]:
        """Execute a SQL statement."""
        return await self.repository.execute(statement, connection)
    
    async def execute_statement_by_id(
        self,
        statement_id: SQLStatementId,
        connection: Connection
    ) -> Result[SQLExecution]:
        """Execute a SQL statement by ID."""
        # Get the statement
        result = await self.repository.get_by_id(statement_id)
        if not result.is_success():
            return Failure(f"SQL statement not found: {statement_id.value}")
        
        statement = result.value
        
        # Execute the statement
        return await self.repository.execute(statement, connection)


class SQLEmitterService(DomainService, SQLEmitterServiceProtocol):
    """Service for SQL emitter management."""
    
    def __init__(
        self,
        repository: SQLEmitterRepositoryProtocol,
        statement_service: SQLStatementServiceProtocol
    ):
        self.repository = repository
        self.statement_service = statement_service
        self.logger = logging.getLogger(__name__)
    
    async def register_emitter(
        self,
        name: str,
        statement_types: List[SQLStatementType],
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[SQLEmitter]:
        """Register a new SQL emitter."""
        try:
            # Generate a unique ID
            emitter_id = SQLEmitterId(str(uuid.uuid4()))
            
            # Create the emitter
            emitter = SQLEmitter(
                id=emitter_id,
                name=name,
                description=description or "",
                statement_types=statement_types,
                configuration=configuration or {}
            )
            
            # Save the emitter
            return await self.repository.save(emitter)
        except Exception as e:
            self.logger.error(f"Error registering SQL emitter: {e}")
            return Failure(f"Failed to register SQL emitter: {str(e)}")
    
    async def get_emitter(self, emitter_id: SQLEmitterId) -> Result[SQLEmitter]:
        """Get an emitter by ID."""
        return await self.repository.get_by_id(emitter_id)
    
    async def get_emitter_by_name(self, name: str) -> Result[SQLEmitter]:
        """Get an emitter by name."""
        return await self.repository.get_by_name(name)
    
    async def get_emitters_by_statement_type(self, statement_type: SQLStatementType) -> Result[List[SQLEmitter]]:
        """Get emitters by statement type."""
        return await self.repository.get_by_statement_type(statement_type)
    
    async def list_emitters(self) -> Result[List[SQLEmitter]]:
        """List all emitters."""
        return await self.repository.get_all()
    
    async def update_emitter(
        self,
        emitter_id: SQLEmitterId,
        statement_types: Optional[List[SQLStatementType]] = None,
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[SQLEmitter]:
        """Update an emitter."""
        # Get the current emitter
        result = await self.repository.get_by_id(emitter_id)
        if not result.is_success():
            return result
        
        emitter = result.value
        
        # Update fields if provided
        if statement_types is not None:
            emitter.statement_types = statement_types
        
        if description is not None:
            emitter.description = description
        
        if configuration is not None:
            emitter.update_configuration(configuration)
        
        # Save the updated emitter
        return await self.repository.save(emitter)
    
    async def delete_emitter(self, emitter_id: SQLEmitterId) -> Result[bool]:
        """Delete an emitter."""
        return await self.repository.delete(emitter_id)
    
    async def generate_statements(
        self,
        emitter_id: SQLEmitterId,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[List[SQLStatement]]:
        """Generate statements using an emitter."""
        # This is a placeholder implementation
        # In a real implementation, this would use the emitter to generate SQL statements
        # based on its configuration and the provided overrides
        
        # Get the emitter
        result = await self.repository.get_by_id(emitter_id)
        if not result.is_success():
            return Failure(f"SQL emitter not found: {emitter_id.value}")
        
        emitter = result.value
        
        # Apply configuration overrides
        config = emitter.configuration.copy()
        if configuration:
            config.update(configuration)
        
        # Generate statements based on the emitter's type
        statements = []
        for statement_type in emitter.statement_types:
            # This is where custom logic for different emitter types would go
            
            statement_id = SQLStatementId(str(uuid.uuid4()))
            statements.append(SQLStatement(
                id=statement_id,
                name=f"{emitter.name}_{statement_type.value}",
                type=statement_type,
                sql=f"-- Generated by {emitter.name}\n-- This is a placeholder"
            ))
        
        return Success(statements)


class SQLConfigurationService(DomainService, SQLConfigurationServiceProtocol):
    """Service for SQL configuration management."""
    
    def __init__(
        self,
        repository: SQLConfigurationRepositoryProtocol,
        emitter_repository: SQLEmitterRepositoryProtocol,
        statement_service: SQLStatementServiceProtocol,
        connection_service: "SQLConnectionServiceProtocol"
    ):
        self.repository = repository
        self.emitter_repository = emitter_repository
        self.statement_service = statement_service
        self.connection_service = connection_service
        self.logger = logging.getLogger(__name__)
    
    async def create_configuration(
        self,
        name: str,
        description: Optional[str] = None,
        connection_info: Optional[DatabaseConnectionInfo] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[SQLConfiguration]:
        """Create a new SQL configuration."""
        try:
            # Generate a unique ID
            config_id = SQLConfigId(str(uuid.uuid4()))
            
            # Create the configuration
            configuration = SQLConfiguration(
                id=config_id,
                name=name,
                description=description or "",
                connection_info=connection_info,
                metadata=metadata or {}
            )
            
            # Save the configuration
            return await self.repository.save(configuration)
        except Exception as e:
            self.logger.error(f"Error creating SQL configuration: {e}")
            return Failure(f"Failed to create SQL configuration: {str(e)}")
    
    async def get_configuration(self, config_id: SQLConfigId) -> Result[SQLConfiguration]:
        """Get a configuration by ID."""
        return await self.repository.get_by_id(config_id)
    
    async def get_configuration_by_name(self, name: str) -> Result[SQLConfiguration]:
        """Get a configuration by name."""
        return await self.repository.get_by_name(name)
    
    async def list_configurations(self) -> Result[List[SQLConfiguration]]:
        """List all configurations."""
        return await self.repository.get_all()
    
    async def update_configuration(
        self,
        config_id: SQLConfigId,
        name: Optional[str] = None,
        description: Optional[str] = None,
        connection_info: Optional[DatabaseConnectionInfo] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[SQLConfiguration]:
        """Update a configuration."""
        # Get the current configuration
        result = await self.repository.get_by_id(config_id)
        if not result.is_success():
            return result
        
        configuration = result.value
        
        # Update fields if provided
        if name is not None:
            configuration.name = name
        
        if description is not None:
            configuration.description = description
        
        if connection_info is not None:
            configuration.connection_info = connection_info
        
        if metadata is not None:
            configuration.update_metadata(metadata)
        
        # Save the updated configuration
        return await self.repository.save(configuration)
    
    async def delete_configuration(self, config_id: SQLConfigId) -> Result[bool]:
        """Delete a configuration."""
        return await self.repository.delete(config_id)
    
    async def add_emitter_to_configuration(
        self,
        config_id: SQLConfigId,
        emitter_id: SQLEmitterId
    ) -> Result[SQLConfiguration]:
        """Add an emitter to a configuration."""
        # Get the current configuration
        config_result = await self.repository.get_by_id(config_id)
        if not config_result.is_success():
            return config_result
        
        configuration = config_result.value
        
        # Get the emitter
        emitter_result = await self.emitter_repository.get_by_id(emitter_id)
        if not emitter_result.is_success():
            return Failure(f"SQL emitter not found: {emitter_id.value}")
        
        emitter = emitter_result.value
        
        # Add the emitter to the configuration
        configuration.add_emitter(emitter)
        
        # Save the updated configuration
        return await self.repository.save(configuration)
    
    async def remove_emitter_from_configuration(
        self,
        config_id: SQLConfigId,
        emitter_id: SQLEmitterId
    ) -> Result[SQLConfiguration]:
        """Remove an emitter from a configuration."""
        # Get the current configuration
        result = await self.repository.get_by_id(config_id)
        if not result.is_success():
            return result
        
        configuration = result.value
        
        # Remove the emitter from the configuration
        if not configuration.remove_emitter(emitter_id):
            return Failure(f"Emitter not found in configuration: {emitter_id.value}")
        
        # Save the updated configuration
        return await self.repository.save(configuration)
    
    async def execute_configuration(
        self,
        config_id: SQLConfigId,
        connection: Optional[Connection] = None
    ) -> Result[List[SQLExecution]]:
        """Execute all statements in a configuration."""
        # Get the configuration
        config_result = await self.repository.get_by_id(config_id)
        if not config_result.is_success():
            return Failure(f"SQL configuration not found: {config_id.value}")
        
        configuration = config_result.value
        
        # Check if we need to create a connection
        should_create_connection = connection is None
        own_connection = None
        
        try:
            if should_create_connection:
                if not configuration.connection_info:
                    return Failure("No connection information provided and no connection passed")
                
                # Create a connection
                conn_result = await self.connection_service.get_connection(
                    configuration.connection_info,
                    SQLTransactionIsolationLevel.AUTOCOMMIT
                )
                
                if not conn_result.is_success():
                    return conn_result
                
                own_connection = conn_result.value
                connection = own_connection
            
            # Generate statements from all emitters in the configuration
            all_statements = []
            for emitter in configuration.emitters:
                # Generate statements from this emitter
                statements_result = await self.statement_service.get_statements_by_type(emitter.statement_types[0])
                if statements_result.is_success():
                    all_statements.extend(statements_result.value)
            
            # Execute all statements
            executions = []
            for statement in all_statements:
                execution_result = await self.statement_service.execute_statement(statement, connection)
                if execution_result.is_success():
                    executions.append(execution_result.value)
                else:
                    return Failure(f"Failed to execute statement {statement.name}: {execution_result.error}")
            
            return Success(executions)
        finally:
            # Close our connection if we created it
            if should_create_connection and own_connection:
                await self.connection_service.close_connection(own_connection)


class SQLFunctionService(DomainService, SQLFunctionServiceProtocol):
    """Service for SQL function management."""
    
    def __init__(self, repository: SQLFunctionRepositoryProtocol):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def create_function(
        self,
        schema: str,
        name: str,
        body: str,
        args: str = "",
        return_type: str = "TRIGGER",
        language: str = "plpgsql",
        volatility: str = "VOLATILE",
        security_definer: bool = False
    ) -> Result[SQLFunction]:
        """Create a new SQL function."""
        try:
            # Create the function
            function = SQLFunction(
                schema=schema,
                name=name,
                body=body,
                args=args,
                return_type=return_type,
                language=language,
                volatility=volatility,
                security_definer=security_definer
            )
            
            # Save the function
            return await self.repository.save(function)
        except Exception as e:
            self.logger.error(f"Error creating SQL function: {e}")
            return Failure(f"Failed to create SQL function: {str(e)}")
    
    async def get_function(self, function_id: str) -> Result[SQLFunction]:
        """Get a function by ID."""
        return await self.repository.get_by_id(function_id)
    
    async def get_function_by_name(self, schema: str, name: str) -> Result[SQLFunction]:
        """Get a function by schema and name."""
        return await self.repository.get_by_name(schema, name)
    
    async def get_functions_by_schema(self, schema: str) -> Result[List[SQLFunction]]:
        """Get functions by schema."""
        return await self.repository.get_by_schema(schema)
    
    async def list_functions(self) -> Result[List[SQLFunction]]:
        """List all functions."""
        return await self.repository.get_all()
    
    async def update_function(
        self,
        function_id: str,
        body: Optional[str] = None,
        args: Optional[str] = None,
        return_type: Optional[str] = None,
        language: Optional[str] = None,
        volatility: Optional[str] = None,
        security_definer: Optional[bool] = None
    ) -> Result[SQLFunction]:
        """Update a function."""
        # Get the current function
        result = await self.repository.get_by_id(function_id)
        if not result.is_success():
            return result
        
        function = result.value
        
        # Update fields if provided
        if body is not None:
            function.update_body(body)
        
        if args is not None:
            function.update_args(args)
        
        if return_type is not None:
            function.return_type = return_type
        
        if language is not None:
            function.language = language
        
        if volatility is not None:
            function.volatility = volatility
        
        if security_definer is not None:
            function.security_definer = security_definer
        
        # Save the updated function
        return await self.repository.save(function)
    
    async def delete_function(self, function_id: str) -> Result[bool]:
        """Delete a function."""
        return await self.repository.delete(function_id)
    
    async def deploy_function(
        self,
        function_id: str,
        connection: Connection
    ) -> Result[bool]:
        """Deploy a function to the database."""
        # Get the function
        result = await self.repository.get_by_id(function_id)
        if not result.is_success():
            return Failure(f"SQL function not found: {function_id}")
        
        function = result.value
        
        # Deploy the function
        return await self.repository.deploy(function, connection)


class SQLTriggerService(DomainService, SQLTriggerServiceProtocol):
    """Service for SQL trigger management."""
    
    def __init__(
        self,
        repository: SQLTriggerRepositoryProtocol,
        function_repository: SQLFunctionRepositoryProtocol
    ):
        self.repository = repository
        self.function_repository = function_repository
        self.logger = logging.getLogger(__name__)
    
    async def create_trigger(
        self,
        schema: str,
        name: str,
        table: str,
        function_name: str,
        events: List[str],
        when: Optional[str] = None,
        for_each: str = "ROW"
    ) -> Result[SQLTrigger]:
        """Create a new SQL trigger."""
        try:
            # Verify that the function exists
            function_result = await self.function_repository.get_by_name(schema, function_name)
            if not function_result.is_success():
                return Failure(f"Function not found: {schema}.{function_name}")
            
            # Create the trigger
            trigger = SQLTrigger(
                schema=schema,
                name=name,
                table=table,
                function_name=function_name,
                events=events,
                when=when,
                for_each=for_each
            )
            
            # Save the trigger
            return await self.repository.save(trigger)
        except Exception as e:
            self.logger.error(f"Error creating SQL trigger: {e}")
            return Failure(f"Failed to create SQL trigger: {str(e)}")
    
    async def get_trigger(self, trigger_id: str) -> Result[SQLTrigger]:
        """Get a trigger by ID."""
        return await self.repository.get_by_id(trigger_id)
    
    async def get_trigger_by_name(self, schema: str, name: str) -> Result[SQLTrigger]:
        """Get a trigger by schema and name."""
        return await self.repository.get_by_name(schema, name)
    
    async def get_triggers_by_table(self, schema: str, table: str) -> Result[List[SQLTrigger]]:
        """Get triggers by table."""
        return await self.repository.get_by_table(schema, table)
    
    async def list_triggers(self) -> Result[List[SQLTrigger]]:
        """List all triggers."""
        return await self.repository.get_all()
    
    async def update_trigger(
        self,
        trigger_id: str,
        events: Optional[List[str]] = None,
        when: Optional[str] = None,
        for_each: Optional[str] = None
    ) -> Result[SQLTrigger]:
        """Update a trigger."""
        # Get the current trigger
        result = await self.repository.get_by_id(trigger_id)
        if not result.is_success():
            return result
        
        trigger = result.value
        
        # Update fields if provided
        if events is not None:
            trigger.update_events(events)
        
        if when is not None:
            trigger.update_when_condition(when)
        
        if for_each is not None:
            trigger.for_each = for_each
        
        # Save the updated trigger
        return await self.repository.save(trigger)
    
    async def delete_trigger(self, trigger_id: str) -> Result[bool]:
        """Delete a trigger."""
        return await self.repository.delete(trigger_id)
    
    async def deploy_trigger(
        self,
        trigger_id: str,
        connection: Connection
    ) -> Result[bool]:
        """Deploy a trigger to the database."""
        # Get the trigger
        result = await self.repository.get_by_id(trigger_id)
        if not result.is_success():
            return Failure(f"SQL trigger not found: {trigger_id}")
        
        trigger = result.value
        
        # Deploy the trigger
        return await self.repository.deploy(trigger, connection)


class SQLConnectionService(DomainService, SQLConnectionServiceProtocol):
    """Service for SQL connection management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engines: Dict[str, Engine] = {}
    
    async def create_connection(
        self,
        db_name: str,
        db_user: str,
        db_host: str,
        db_port: int = 5432,
        db_schema: str = "public",
        admin_role: Optional[str] = None,
        writer_role: Optional[str] = None,
        reader_role: Optional[str] = None
    ) -> Result[DatabaseConnectionInfo]:
        """Create connection information."""
        try:
            # Create the connection info
            connection_info = DatabaseConnectionInfo(
                db_name=db_name,
                db_user=db_user,
                db_host=db_host,
                db_port=db_port,
                db_schema=db_schema,
                admin_role=admin_role,
                writer_role=writer_role,
                reader_role=reader_role
            )
            
            return Success(connection_info)
        except Exception as e:
            self.logger.error(f"Error creating connection info: {e}")
            return Failure(f"Failed to create connection info: {str(e)}")
    
    async def get_connection(
        self,
        connection_info: DatabaseConnectionInfo,
        isolation_level: SQLTransactionIsolationLevel = SQLTransactionIsolationLevel.READ_COMMITTED
    ) -> Result[Connection]:
        """Get a database connection."""
        try:
            # Get or create an engine
            engine_result = await self.get_engine(connection_info)
            if not engine_result.is_success():
                return engine_result
            
            engine = engine_result.value
            
            # Create a connection
            conn = engine.connect()
            
            # Set the isolation level
            if isolation_level != SQLTransactionIsolationLevel.AUTOCOMMIT:
                conn.execution_options(isolation_level=isolation_level.value)
            
            return Success(conn)
        except Exception as e:
            self.logger.error(f"Error getting connection: {e}")
            return Failure(f"Failed to get connection: {str(e)}")
    
    async def close_connection(self, connection: Connection) -> Result[bool]:
        """Close a database connection."""
        try:
            connection.close()
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
            return Failure(f"Failed to close connection: {str(e)}")
    
    async def get_engine(self, connection_info: DatabaseConnectionInfo) -> Result[Engine]:
        """Get a database engine."""
        try:
            # Create a key for the engine cache
            key = f"{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
            
            # Return cached engine if available
            if key in self.engines:
                return Success(self.engines[key])
            
            # Create a new engine
            connection_string = (
                f"postgresql://{connection_info.db_user}@{connection_info.db_host}:"
                f"{connection_info.db_port}/{connection_info.db_name}"
            )
            
            engine = create_engine(connection_string)
            
            # Cache the engine
            self.engines[key] = engine
            
            return Success(engine)
        except Exception as e:
            self.logger.error(f"Error getting engine: {e}")
            return Failure(f"Failed to get engine: {str(e)}")
    
    async def execute_sql(
        self,
        connection_info: DatabaseConnectionInfo,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Result[Any]:
        """Execute SQL on a database."""
        # Get a connection
        conn_result = await self.get_connection(
            connection_info,
            SQLTransactionIsolationLevel.AUTOCOMMIT
        )
        
        if not conn_result.is_success():
            return conn_result
        
        conn = conn_result.value
        
        try:
            # Execute the SQL
            result = conn.execute(text(sql), params or {})
            
            # Process the result
            if result.returns_rows:
                # Convert to list of dictionaries
                rows = [dict(row) for row in result]
                return Success(rows)
            else:
                # Return number of affected rows
                return Success(result.rowcount)
        except Exception as e:
            self.logger.error(f"Error executing SQL: {e}")
            return Failure(f"Failed to execute SQL: {str(e)}")
        finally:
            # Close the connection
            await self.close_connection(conn)