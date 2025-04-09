# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import logging
from unittest.mock import MagicMock

from typing import (
    Optional,
    ClassVar,
    Dict,
    Type,
    Any,
    Callable,
    List,
)
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_settings import BaseSettings
from sqlalchemy import Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from sqlalchemy.engine.base import Connection

from uno.db.config import ConnectionConfig
from uno.utilities import import_from_path
from uno.settings import uno_settings
from uno.errors import UnoError


def load_sql_modules() -> None:
    """
    Dynamically load models and SQL configurations for all packages
    listed in uno_settings.LOAD_PACKAGES when APP_PATH is defined.
    """
    if uno_settings.APP_PATH:
        for pkg in uno_settings.LOAD_PACKAGES:
            try:
                file_path = f"{uno_settings.APP_PATH}/{pkg.replace('.', '/')}/models.py"
                import_from_path(pkg, file_path)
            except Exception as e:
                logging.error(f"Failed to load models for package `{pkg}`: {e}")
            try:
                file_path = (
                    f"{uno_settings.APP_PATH}/{pkg.replace('.', '/')}/sqlconfigs.py"
                )
                import_from_path(pkg, file_path)
            except Exception as e:
                logging.error(f"Failed to load sqlconfigs for package `{pkg}`: {e}")


class SQLEmitter(BaseModel):
    """
    Base class for SQL emitters that generate and execute SQL statements.

    SQL emitters generate SQL statements for various database operations like
    creating tables, functions, triggers, etc. Each property in the model
    can represent a separate SQL statement to be executed.

    Attributes:
        exclude_fields: Fields to exclude when dumping model for SQL emission
        table: Table for which SQL is being generated
        connection_config: Database configuration
        config: Configuration uno_settings
        logger: Logger for recording operations
    """

    # Fields excluded when dumping the model (for SQL emission)
    exclude_fields: ClassVar[list[str]] = [
        "table",
        "config",
        "logger",
        "connection_config",
    ]

    # The table for which SQL is being generated, if applicable
    table: Optional[Table] = None

    # Database configuration
    connection_config: Optional[ConnectionConfig] = None

    # Configuration uno_settings
    config: BaseSettings = uno_settings  # Default to uno_settings

    # Logger injected via dependency injection
    logger: logging.Logger = logging.getLogger(__name__)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    def initialize_connection_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pydantic model validator to initialize connection_config if not provided.

        Args:
            values: Dictionary of field values

        Returns:
            Updated dictionary of field values
        """
        if "connection_config" not in values or values["connection_config"] is None:
            config = values.get("config")
            if config is None:
                raise UnoError(
                    "No connection_config or config provided. ",
                    "NO_CONNECTION_CONFIG_OR_CONFIG",
                )
            values["connection_config"] = ConnectionConfig(
                db_name=config.DB_NAME,
                db_user_pw=config.DB_USER_PW,
                db_driver=config.DB_SYNC_DRIVER,
            )
        return values

    def emit_sql(
        self,
        connection: Connection,
        dry_run: bool = False,
        executor: Optional[Callable[[str], Any]] = None,
    ) -> Optional[List[str]]:
        """
        Execute SQL statements using the provided connection.

        Args:
            connection: SQLAlchemy connection object
            dry_run: If True, return statements without executing
            executor: Optional custom executor function

        Returns:
            List of SQL statements if dry_run is True, None otherwise

        Raises:
            UnoError: If SQL execution fails
        """
        statements = []
        try:
            # Get all properties from the model (excluding the specified fields)
            for statement_name, sql_statement in self.model_dump(
                exclude=self.exclude_fields
            ).items():
                if sql_statement:  # Only process non-empty statements
                    self.logger.info(f"Processing SQL statement: {statement_name}")
                    statements.append(sql_statement)

            if dry_run:
                return statements

            # Execute the statements
            for sql in statements:
                if executor:
                    executor(sql)
                else:
                    connection.execute(text(sql))

            return None
        except SQLAlchemyError as e:
            self.logger.error(f"Error executing SQL: {e}")
            raise UnoError(f"Failed to execute SQL: {e}", "SQL_EXECUTION_ERROR")

    def format_sql_template(self, template: str, **kwargs) -> str:
        """
        Format an SQL template with the provided keyword arguments.

        Args:
            template: SQL template with {placeholder} syntax
            **kwargs: Values to substitute into the template

        Returns:
            Formatted SQL string

        Raises:
            KeyError: If a required placeholder is missing
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

    def create_sql_trigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:
        """
        Create a SQL trigger statement.

        Args:
            function_name: Name of the function to trigger
            timing: Timing of the trigger (BEFORE/AFTER/INSTEAD OF)
            operation: Operation type(s). Can be a single operation (e.g., "UPDATE")
                       or combined operations separated by "OR" (e.g., "INSERT OR UPDATE").
            for_each: Trigger for each ROW or STATEMENT
            db_function: Whether the function is a database function

        Returns:
            SQL trigger statement

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        valid_timings = ["BEFORE", "AFTER", "INSTEAD OF"]
        # Base allowed operations
        base_operations = {"INSERT", "UPDATE", "DELETE", "TRUNCATE"}
        valid_for_each = ["ROW", "STATEMENT"]

        if timing not in valid_timings:
            raise ValueError(
                f"Invalid timing: {timing}. Must be one of {valid_timings}"
            )

        # Allow composite operations such as "INSERT OR UPDATE"
        operations = [op.strip() for op in operation.split("OR")]
        if not all(op in base_operations for op in operations):
            raise ValueError(
                f"Invalid operation(s) in '{operation}'. Each must be one of {base_operations}"
            )

        if for_each not in valid_for_each:
            raise ValueError(
                f"Invalid for_each: {for_each}. Must be one of {valid_for_each}"
            )

        schema = (
            self.connection_config.db_schema
            if self.connection_config
            else self.config.DB_SCHEMA
        )
        trigger_scope = f"{schema}." if db_function else f"{schema}.{self.table.name}_"
        trigger_prefix = self.table.name

        return f"""
            CREATE OR REPLACE TRIGGER {trigger_prefix}_{function_name}_trigger
                {timing} {operation}
                ON {schema}.{self.table.name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
        """

    def create_sql_function(
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
        """
        Create a SQL function statement.

        Args:
            function_name: Name of the function
            function_string: Function body
            function_args: Function arguments
            db_function: Whether the function is a database function
            return_type: Return type of the function
            volatile: Volatility of the function
            include_trigger: Whether to include a trigger
            timing: Timing for the trigger (BEFORE/AFTER)
            operation: Operation type (INSERT/UPDATE/DELETE)
            for_each: Trigger for each ROW or STATEMENT
            security_definer: Security definer clause

        Returns:
            SQL function statement

        Raises:
            ValueError: If function arguments are used with a trigger or other invalid parameters
        """
        if function_args and include_trigger:
            raise ValueError(
                "Function arguments cannot be used when creating a trigger function."
            )

        # Use connection_config if available, otherwise fall back to config
        schema = (
            self.connection_config.db_schema
            if self.connection_config
            else self.config.DB_SCHEMA
        )

        full_function_name = (
            f"{schema}.{function_name}"
            if db_function
            else f"{schema}.{self.table.name}_{function_name}"
        )

        fnct_string = f"""
            SET ROLE {self.config.DB_NAME}_admin;
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            {volatile}
            {security_definer}
            AS $fnct$
            {function_string}
            $fnct$;
        """

        if not include_trigger:
            return fnct_string

        trggr_string = self.create_sql_trigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return f"{fnct_string}\n{trggr_string}"


class SQLConfig(BaseModel):
    """
    Configuration for SQL generation and execution.

    This class manages SQL emitters for specific tables or database operations.
    It maintains a registry of all SQLConfig subclasses for dynamic registration
    and discovery.

    Attributes:
        registry: Registry of all SQLConfig subclasses
        sql_emitters: Dictionary of SQL emitter classes for this config
        table: Table for which SQL is being generated
        connection_config: ConnectionConfig
    """

    registry: ClassVar[Dict[str, Type["SQLConfig"]]] = {}
    sql_emitters: ClassVar[List[Type[SQLEmitter]]] = []
    table: ClassVar[Optional[Table]] = None
    connection_config: Optional[ConnectionConfig] = None

    @model_validator(mode="before")
    def initialize_connection_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pydantic model validator to initialize connection_config if not provided.

        Args:
            values: Dictionary of field values

        Returns:
            Updated dictionary of field values
        """
        if "connection_config" not in values or values["connection_config"] is None:
            config = values.get("config")
            if config is None:
                raise UnoError(
                    "No connection_config or config provided. ",
                    "NO_CONNECTION_CONFIG_OR_CONFIG",
                )
            values["connection_config"] = ConnectionConfig(
                db_name=config.DB_NAME,
                db_user_pw=config.DB_USER_PW,
                db_driver=config.DB_SYNC_DRIVER,
            )
        return values

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize and register the SQLConfig subclass.

        Raises:
            UnoError: If a subclass with the same name already exists in the registry.
        """
        super().__init_subclass__(**kwargs)
        if cls is SQLConfig:
            return
        if cls.__name__ not in cls.registry:
            cls.registry[cls.__name__] = cls
        else:
            raise UnoError(
                f"SQLConfig class: {cls.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )

    def emit_sql(self, connection: Connection) -> None:
        """
        Emit SQL for all registered SQL emitters.

        Args:
            connection: SQLAlchemy connection object

        Raises:
            UnoError: If SQL emission fails
        """
        try:
            for emitter_class in self.sql_emitters:
                logging.info(f"Emitting SQL for table: {self.table}")
                # Instantiate emitter using dependency injection for table and config
                emitter_instance = emitter_class(
                    table=self.table,
                    connection_config=self.connection_config,
                )
                emitter_instance.emit_sql(connection)
        except SQLAlchemyError as e:
            logging.error(f"Error emitting SQL: {e}")
            raise UnoError(f"Failed to emit SQL: {e}", "SQL_EMISSION_ERROR")

    @classmethod
    def get_emitter(cls, emitter_class: Type[SQLEmitter]) -> SQLEmitter:
        """
        Create an instance of the specified SQL emitter.

        Args:
            emitter_class: SQLEmitter class to instantiate

        Returns:
            Instantiated SQL emitter

        Raises:
            ValueError: If emitter_class is not a subclass of SQLEmitter
        """
        if not issubclass(emitter_class, SQLEmitter):
            raise ValueError(f"{emitter_class.__name__} is not a SQLEmitter subclass")

        return emitter_class(
            table=cls.table,
            config=cls.config,
            connection_config=get_connection_config(cls.config),
        )


class SQLEmitterTester:
    """
    Utility class for testing SQL emitters without executing SQL.

    Allows retrieving SQL statements that would be generated by emitters
    for inspection and verification during testing.
    """

    def __init__(self, config_cls: Type[SQLConfig]) -> None:
        """
        Initialize the tester with a SQLConfig class.

        Args:
            config_cls: SQLConfig class to test
        """
        self.config_cls = config_cls

    def get_all_emitter_sql(self) -> Dict[str, List[str]]:
        """
        Get SQL statements from all emitters in the config.

        Returns:
            Dictionary mapping emitter names to lists of SQL statements
        """
        result = {}
        for emitter_cls in self.config_cls.sql_emitters:
            emitter_name = emitter_cls.__name__
            result[emitter_name] = self.get_emitter_sql(emitter_cls)
        return result

    def get_emitter_sql(self, emitter_cls: Type[SQLEmitter]) -> List[str]:
        """
        Get SQL statements from a specific emitter.

        Args:
            emitter_cls: SQLEmitter class to test

        Returns:
            List of SQL statements that would be generated
        """
        emitter = emitter_cls(
            table=self.config_cls.table,
            config=self.config_cls.config,
            connection_config=get_connection_config(self.config_cls.config),
        )
        # Create a mock connection
        connection = MagicMock()
        # Get SQL statements in dry run mode
        return emitter.emit_sql(connection, dry_run=True) or []


# Load models and SQL configurations dynamically
load_sql_modules()
