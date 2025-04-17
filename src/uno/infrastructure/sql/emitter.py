# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Base class and protocols for SQL emitters."""

import time
import logging
from typing import Dict, List, Optional, Protocol, ClassVar, Type
from pydantic import BaseModel, model_validator

from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine.sync import SyncEngineFactory, sync_connection
from uno.settings import uno_settings
from uno.sql.errors import (
    SQLErrorCode,
    SQLEmitterError,
    SQLExecutionError,
    SQLStatementError,
    SQLSyntaxError
)

from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.observers import SQLObserver, BaseObserver

# No additional imports needed


class SQLGenerator(Protocol):
    """Protocol for objects that can generate SQL statements."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements.

        Returns:
            List of SQL statements with metadata
        """
        ...


class SQLExecutor(Protocol):
    """Protocol for objects that can execute SQL statements."""

    def execute_sql(
        self, connection: Connection, statements: List[SQLStatement]
    ) -> None:
        """Execute SQL statements on a connection.

        Args:
            connection: Database connection
            statements: List of SQL statements to execute
        """
        ...


class SQLEmitter(BaseModel):
    """Base class for SQL emitters that generate and execute SQL statements.

    SQL emitters generate SQL statements for various database operations like
    creating tables, functions, triggers, etc. Each property in the model
    can represent a separate SQL statement to be executed.

    Attributes:
        exclude_fields: Fields excluded when dumping the model
        table: Table for which SQL is being generated
        connection_config: Database configuration
        config: Configuration settings
        logger: Logger for this emitter
        engine_factory: Engine factory for creating connections
        observers: Observers for SQL operations
    """

    # Fields excluded when serializing the model
    exclude_fields: ClassVar[List[str]] = [
        "table",
        "config",
        "logger",
        "connection_config",
        "observers",
        "engine_factory",
    ]

    # The table for which SQL is being generated
    table: Optional[Table] = None

    # Database configuration
    connection_config: Optional[ConnectionConfig] = None

    # Configuration settings
    config: BaseModel = uno_settings

    # Logger for this emitter
    logger: logging.Logger = logging.getLogger(__name__)

    # Engine factory for creating connections
    engine_factory: Optional[SyncEngineFactory] = None

    # Observers for SQL operations - using BaseObserver which is a concrete class
    observers: List[BaseObserver] = []

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="before")
    def initialize_connection_config(cls, values: Dict) -> Dict:
        """Initialize connection_config if not provided.

        Args:
            values: Dictionary of field values

        Returns:
            Updated dictionary of field values
        """
        if "connection_config" not in values or values["connection_config"] is None:
            config = values.get("config", uno_settings)
            values["connection_config"] = ConnectionConfig(
                db_name=config.DB_NAME,
                db_user_pw=config.DB_USER_PW,
                db_driver=config.DB_SYNC_DRIVER,
            )
        return values

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements based on emitter configuration.

        This method converts properties of the model to SQL statements with
        appropriate metadata.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Convert properties to SQL statements with metadata
        for property_name, value in self.model_dump(
            exclude=self.exclude_fields
        ).items():
            if value is None or (
                isinstance(value, (str, list, dict)) and not value
            ):  # Skip empty/None properties
                continue

            # Determine statement type from property name
            statement_type = None
            for type_enum in SQLStatementType:
                if type_enum.value in property_name.lower():
                    statement_type = type_enum
                    break

            # Default to function if type can't be determined
            if statement_type is None:
                statement_type = SQLStatementType.FUNCTION

            statements.append(
                SQLStatement(name=property_name, type=statement_type, sql=value)
            )

        return statements

    def execute_sql(
        self, connection: Connection, statements: List[SQLStatement]
    ) -> None:
        """Execute the generated SQL statements.

        Args:
            connection: Database connection
            statements: List of SQL statements to execute
        """
        # First set the role to admin to ensure we have proper permissions
        # IMPORTANT: Always use the config's DB_NAME for role setting, not the connection's database
        db_name = None
        if self.config:
            db_name = self.config.DB_NAME
            
        if db_name:
            # We need to handle the special case where we're dropping a database
            # In that case, we're connected to 'postgres' database but want to affect the target database
            if self.__class__.__name__ == 'DropDatabaseAndRoles':
                # No need to set role when connected as postgres user to postgres db
                self.logger.debug("Connected as postgres, no need to set role for dropping database")
            else:
                # For regular operations, set to the admin role for the target database
                admin_role = f"{db_name}_admin"
                connection.execute(text(f"SET ROLE {admin_role};"))
                self.logger.debug(f"Set role to {admin_role}")
            
        # Execute the statements
        for statement in statements:
            self.logger.debug(f"Executing SQL statement: {statement.name}")
            connection.execute(text(statement.sql))

    def emit_sql(
        self, connection: Connection, dry_run: bool = False
    ) -> Optional[List[SQLStatement]]:
        """Generate and optionally execute SQL statements.

        Args:
            connection: Database connection
            dry_run: If True, return statements without executing

        Returns:
            List of SQL statements if dry_run is True, None otherwise

        Raises:
            UnoError: If SQL execution fails
        """
        statements = []
        if 1 == 1:  # try:
            # Generate SQL statements
            print(self)
            statements = self.generate_sql()

            # Notify observers
            for observer in self.observers:
                observer.on_sql_generated(self.__class__.__name__, statements)

            if dry_run:
                return statements

            # Execute statements
            start_time = time.monotonic()
            self.execute_sql(connection, statements)
            duration = time.monotonic() - start_time

            # Notify observers
            for observer in self.observers:
                observer.on_sql_executed(self.__class__.__name__, statements, duration)

            return None
        # except Exception as e:
        #    # Notify observers of error
        #    for observer in self.observers:
        #        observer.on_sql_error(self.__class__.__name__, statements, e)

        #    # Re-raise the exception
        #    raise UnoError(f"Failed to execute SQL: {e}", "SQL_EXECUTION_ERROR")

    def emit_with_connection(
        self,
        dry_run: bool = False,
        factory: Optional[SyncEngineFactory] = None,
        config: Optional[ConnectionConfig] = None,
        isolation_level: str = "AUTOCOMMIT",
    ) -> Optional[List[SQLStatement]]:
        """Execute SQL with a new connection from the factory.

        Args:
            dry_run: If True, return statements without executing
            factory: Optional engine factory for creating connections
            config: Optional connection configuration
            isolation_level: Transaction isolation level

        Returns:
            List of SQL statements if dry_run is True, None otherwise

        Raises:
            ValueError: If no connection configuration is provided
            UnoError: If SQL execution fails
        """
        # Use provided factory or instance factory or create a new one
        engine_factory = (
            factory or self.engine_factory or SyncEngineFactory(logger=self.logger)
        )

        # Use provided config or instance config
        conn_config = config or self.connection_config
        if not conn_config:
            raise ValueError("No connection configuration provided")

        with sync_connection(
            factory=engine_factory,
            config=conn_config,
            isolation_level=isolation_level,
        ) as conn:
            return self.emit_sql(conn, dry_run)

    @classmethod
    def register_observer(cls, observer: SQLObserver) -> None:
        """Register a new observer for all emitter instances.

        We accept any object that implements the SQLObserver protocol, but
        store it as a BaseObserver for compatibility with Pydantic.

        Args:
            observer: Observer to register
        """
        if not hasattr(cls, "observers"):
            cls.observers = []

        # We only accept objects that implement the SQLObserver protocol
        # but we store them as BaseObserver instances for Pydantic compatibility
        if isinstance(observer, BaseObserver) and observer not in cls.observers:
            cls.observers.append(observer)

    def get_function_builder(self) -> "SQLFunctionBuilder":
        """Get a pre-configured SQL function builder with database name set.
        
        Returns:
            SQLFunctionBuilder: A function builder with database name set
        """
        from uno.sql.builders.function import SQLFunctionBuilder
        builder = SQLFunctionBuilder()
        
        if self.connection_config:
            builder.with_db_name(self.connection_config.db_name)
        elif self.config:
            builder.with_db_name(self.config.DB_NAME)
            
        return builder
        
    def format_sql_template(self, template: str, **kwargs) -> str:
        """Format an SQL template with variables.

        Args:
            template: SQL template string with placeholders
            **kwargs: Values to substitute into the template

        Returns:
            Formatted SQL string

        Raises:
            ValueError: If template formatting fails
        """
        try:
            # Add default values from DB config
            format_args = {}

            # If we have a connection_config, use its attributes
            if self.connection_config:
                format_args.update(
                    {
                        "schema_name": self.connection_config.db_schema,
                        "db_name": self.connection_config.db_name,
                        "admin_role": self.connection_config.admin_role,
                        "writer_role": self.connection_config.writer_role,
                        "reader_role": self.connection_config.reader_role,
                    }
                )
            # Otherwise fall back to config
            elif self.config:
                format_args.update(
                    {
                        "schema_name": self.config.DB_SCHEMA,
                        "db_name": self.config.DB_NAME,
                        "admin_role": f"{self.config.DB_NAME}_admin",
                        "writer_role": f"{self.config.DB_NAME}_writer",
                        "reader_role": f"{self.config.DB_NAME}_reader",
                    }
                )

            # Override defaults with provided kwargs
            format_args.update(kwargs)

            # Format the template
            return template.format(**format_args)
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error formatting SQL template: {e}")
            raise ValueError(f"Error formatting SQL template: {e}")


# Type verification function for static type checking
def _verify_protocol_compliance() -> None:
    """Verify that SQLEmitter complies with the SQLGenerator and SQLExecutor protocols.

    This function is never called at runtime but helps with static type checking
    to ensure that SQLEmitter implements all required methods from the protocols.
    """
    emitter: SQLEmitter = SQLEmitter()
    generator: SQLGenerator = emitter  # Will raise type error if incompatible
    executor: SQLExecutor = emitter  # Will raise type error if incompatible
