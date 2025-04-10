from typing import (
    Dict,
    Type,
    List,
    Optional,
    Callable,
    Protocol,
    ClassVar,
    Union,
    TypeVar,
    Generic,
    cast,
)
from contextlib import contextmanager
import time
import logging
from enum import Enum

from pydantic import BaseModel, model_validator
from sqlalchemy import Table
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine.sync import SyncEngineFactory, sync_connection
from uno.database.engine.base import EngineFactory
from uno.settings import uno_settings
from uno.errors import UnoError


class SQLStatementType(Enum):
    """Types of SQL statements that can be emitted."""

    FUNCTION = "function"
    TRIGGER = "trigger"
    INDEX = "index"
    CONSTRAINT = "constraint"
    GRANT = "grant"
    VIEW = "view"
    PROCEDURE = "procedure"
    TABLE = "table"
    ROLE = "role"
    SCHEMA = "schema"
    EXTENSION = "extension"
    DATABASE = "database"
    INSERT = "insert"


class SQLStatement(BaseModel):
    """A SQL statement with metadata."""

    name: str
    type: SQLStatementType
    sql: str
    depends_on: List[str] = []


class SQLGenerator(Protocol):
    """Protocol for objects that can generate SQL statements."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements with metadata."""
        ...


class SQLExecutor(Protocol):
    """Protocol for objects that can execute SQL statements."""

    def execute_sql(
        self, connection: Connection, statements: List[SQLStatement]
    ) -> None:
        """Execute SQL statements on a connection."""
        ...


class SQLObserver(Protocol):
    """Observer for SQL operations."""

    def on_sql_generated(self, source: str, statements: List[SQLStatement]) -> None:
        """Called when SQL statements are generated."""
        ...

    def on_sql_executed(
        self, source: str, statements: List[SQLStatement], duration: float
    ) -> None:
        """Called when SQL statements are executed."""
        ...

    def on_sql_error(
        self, source: str, statements: List[SQLStatement], error: Exception
    ) -> None:
        """Called when SQL execution fails."""
        ...


class LoggingSQLObserver:
    """Observer that logs SQL operations."""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def on_sql_generated(self, source: str, statements: List[SQLStatement]) -> None:
        self.logger.debug(f"Generated {len(statements)} SQL statements from {source}")

    def on_sql_executed(
        self, source: str, statements: List[SQLStatement], duration: float
    ) -> None:
        self.logger.info(
            f"Executed {len(statements)} SQL statements from {source} in {duration:.2f}s"
        )

    def on_sql_error(
        self, source: str, statements: List[SQLStatement], error: Exception
    ) -> None:
        self.logger.error(f"SQL error in {source}: {error}")


class SQLEmitter(BaseModel, SQLExecutor):
    """Base class for SQL emitters that generate and execute SQL statements."""

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
    config: BaseSettings = uno_settings

    # Logger for this emitter
    logger: logging.Logger = logging.getLogger(__name__)

    # Engine factory for creating connections
    engine_factory: Optional[SyncEngineFactory] = None

    # Observers for SQL operations
    observers: List[SQLObserver] = []

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="before")
    def initialize_connection_config(cls, values: Dict) -> Dict:
        """Initialize connection_config if not provided."""
        if "connection_config" not in values or values["connection_config"] is None:
            config = values.get("config", uno_settings)
            values["connection_config"] = ConnectionConfig(
                db_name=config.DB_NAME,
                db_user_pw=config.DB_USER_PW,
                db_driver=config.DB_SYNC_DRIVER,
            )
        return values

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements based on emitter configuration."""
        statements = []

        # Convert properties to SQL statements with metadata
        for property_name, value in self.model_dump(
            exclude=self.exclude_fields
        ).items():
            if value is None or (isinstance(value, (str, list, dict)) and not value):  # Skip empty/None properties
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
        """Execute the generated SQL statements synchronously."""
        for statement in statements:
            self.logger.debug(f"Executing SQL statement: {statement.name}")
            connection.execute(text(statement.sql))

    def emit_sql(
        self, connection: Connection, dry_run: bool = False
    ) -> Optional[List[SQLStatement]]:
        """Generate and optionally execute SQL statements."""
        statements = []
        try:
            # Generate SQL statements
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
        except Exception as e:
            # Notify observers of error
            for observer in self.observers:
                observer.on_sql_error(self.__class__.__name__, statements, e)

            # Re-raise the exception
            raise UnoError(f"Failed to execute SQL: {e}", "SQL_EXECUTION_ERROR")

    def emit_with_connection(
        self,
        dry_run: bool = False,
        factory: Optional[SyncEngineFactory] = None,
        config: Optional[ConnectionConfig] = None,
        isolation_level: str = "AUTOCOMMIT",
    ) -> Optional[List[SQLStatement]]:
        """Execute SQL with a new connection from the factory."""
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
        """Register a new observer for all emitter instances."""
        if not hasattr(cls, "observers"):
            cls.observers = []

        if observer not in cls.observers:
            cls.observers.append(observer)

    def format_sql_template(self, template: str, **kwargs) -> str:
        """Format an SQL template with variables."""
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


class SQLConfigRegistry:
    """Registry of all SQLConfig classes."""

    _registry: Dict[str, Type["SQLConfig"]] = {}

    @classmethod
    def register(cls, config_class: Type["SQLConfig"]) -> None:
        """Register a SQLConfig class in the registry."""
        if config_class.__name__ in cls._registry:
            raise UnoError(
                f"SQLConfig class: {config_class.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )
        cls._registry[config_class.__name__] = config_class

    @classmethod
    def get(cls, name: str) -> Optional[Type["SQLConfig"]]:
        """Get a SQLConfig class by name."""
        return cls._registry.get(name)

    @classmethod
    def all(cls) -> Dict[str, Type["SQLConfig"]]:
        """Get all registered SQLConfig classes."""
        return dict(cls._registry)

    @classmethod
    def emit_all(
        cls,
        connection: Optional[Connection] = None,
        engine_factory: Optional[SyncEngineFactory] = None,
        config: Optional[ConnectionConfig] = None,
        exclude: List[str] = None,
    ) -> None:
        """
        Emit SQL for all registered SQLConfig classes.

        Args:
            connection: Optional existing connection to use
            engine_factory: Optional engine factory to create new connections
            config: Optional connection configuration
            exclude: List of config class names to exclude
        """
        exclude = exclude or []

        # Use provided connection or create a new one
        should_create_connection = connection is None

        if should_create_connection:
            if engine_factory is None:
                engine_factory = SyncEngineFactory()

            with sync_connection(
                factory=engine_factory,
                config=config,
            ) as conn:
                for name, config_cls in cls._registry.items():
                    if name in exclude:
                        continue
                    config_instance = config_cls(
                        connection_config=config, engine_factory=engine_factory
                    )
                    config_instance.emit_sql(conn)
        else:
            # Use the provided connection
            for name, config_cls in cls._registry.items():
                if name in exclude:
                    continue
                config_instance = config_cls(
                    connection_config=config, engine_factory=engine_factory
                )
                config_instance.emit_sql(connection)


class SQLConfig(BaseModel):
    """Configuration for SQL generation and execution for a table."""

    # Default emitters to use for this config
    default_emitters: ClassVar[List[Type[SQLEmitter]]] = []

    # The table for which SQL is being generated
    table: ClassVar[Optional[Table]] = None

    # Connection configuration
    connection_config: Optional[ConnectionConfig] = None

    # Engine factory for creating connections
    engine_factory: Optional[SyncEngineFactory] = None

    # Emitter instances
    emitters: List[SQLEmitter] = []

    model_config = {"arbitrary_types_allowed": True}

    def __init_subclass__(cls, **kwargs) -> None:
        """Register the SQLConfig subclass in the registry."""
        super().__init_subclass__(**kwargs)
        if cls is not SQLConfig:  # Don't register the base class
            SQLConfigRegistry.register(cls)

    def __init__(self, **kwargs):
        """Initialize the SQLConfig with default emitters if none provided."""
        super().__init__(**kwargs)

        # If no emitters were provided, create them from default_emitters
        if not self.emitters and self.__class__.default_emitters:
            self.emitters = [
                emitter_cls(
                    table=self.__class__.table,
                    connection_config=self.connection_config,
                    engine_factory=self.engine_factory,
                )
                for emitter_cls in self.__class__.default_emitters
            ]

    def emit_sql(self, connection: Optional[Connection] = None) -> None:
        """
        Emit SQL for all registered emitters.

        Args:
            connection: Optional existing connection to use. If not provided,
                       a new connection will be created using the engine factory.
        """
        should_create_connection = connection is None

        try:
            if should_create_connection:
                if self.engine_factory is None:
                    self.engine_factory = SyncEngineFactory()

                with sync_connection(
                    factory=self.engine_factory, config=self.connection_config
                ) as conn:
                    self._emit_sql_internal(conn)
            else:
                self._emit_sql_internal(connection)
        except SQLAlchemyError as e:
            logging.error(f"Error emitting SQL: {e}")
            raise UnoError(f"Failed to emit SQL: {e}", "SQL_EMISSION_ERROR")

    def _emit_sql_internal(self, connection: Connection) -> None:
        """Internal method to emit SQL statements."""
        for emitter in self.emitters:
            logging.info(f"Emitting SQL for {emitter.__class__.__name__}")
            emitter.emit_sql(connection)


class SQLFunctionBuilder:
    """Builder for SQL functions."""

    def __init__(self):
        self.schema = None
        self.name = None
        self.args = ""
        self.return_type = "TRIGGER"
        self.body = None
        self.language = "plpgsql"
        self.volatility = "VOLATILE"
        self.security_definer = False

    def with_schema(self, schema: str) -> "SQLFunctionBuilder":
        self.schema = schema
        return self

    def with_name(self, name: str) -> "SQLFunctionBuilder":
        self.name = name
        return self

    def with_args(self, args: str) -> "SQLFunctionBuilder":
        self.args = args
        return self

    def with_return_type(self, return_type: str) -> "SQLFunctionBuilder":
        self.return_type = return_type
        return self

    def with_body(self, body: str) -> "SQLFunctionBuilder":
        self.body = body
        return self

    def with_language(self, language: str) -> "SQLFunctionBuilder":
        self.language = language
        return self

    def with_volatility(self, volatility: str) -> "SQLFunctionBuilder":
        self.volatility = volatility
        return self

    def as_security_definer(self) -> "SQLFunctionBuilder":
        self.security_definer = True
        return self

    def build(self) -> str:
        """Build the SQL function statement."""
        if not self.schema or not self.name or not self.body:
            raise ValueError("Schema, name, and body are required for a function")

        security = "SECURITY DEFINER" if self.security_definer else ""

        return f"""
            CREATE OR REPLACE FUNCTION {self.schema}.{self.name}({self.args})
            RETURNS {self.return_type}
            LANGUAGE {self.language}
            {self.volatility}
            {security}
            AS $fnct$
            {self.body}
            $fnct$;
        """


class SQLTriggerBuilder:
    """Builder for SQL triggers."""

    def __init__(self):
        self.schema = None
        self.table_name = None
        self.trigger_name = None
        self.function_name = None
        self.timing = "BEFORE"
        self.operation = "UPDATE"
        self.for_each = "ROW"

    def with_schema(self, schema: str) -> "SQLTriggerBuilder":
        self.schema = schema
        return self

    def with_table(self, table_name: str) -> "SQLTriggerBuilder":
        self.table_name = table_name
        return self

    def with_name(self, trigger_name: str) -> "SQLTriggerBuilder":
        self.trigger_name = trigger_name
        return self

    def with_function(self, function_name: str) -> "SQLTriggerBuilder":
        self.function_name = function_name
        return self

    def with_timing(self, timing: str) -> "SQLTriggerBuilder":
        valid_timings = ["BEFORE", "AFTER", "INSTEAD OF"]
        if timing not in valid_timings:
            raise ValueError(
                f"Invalid timing: {timing}. Must be one of {valid_timings}"
            )
        self.timing = timing
        return self

    def with_operation(self, operation: str) -> "SQLTriggerBuilder":
        base_operations = {"INSERT", "UPDATE", "DELETE", "TRUNCATE"}
        operations = [op.strip() for op in operation.split("OR")]
        if not all(op in base_operations for op in operations):
            raise ValueError(f"Invalid operation(s): {operation}")
        self.operation = operation
        return self

    def with_for_each(self, for_each: str) -> "SQLTriggerBuilder":
        valid_for_each = ["ROW", "STATEMENT"]
        if for_each not in valid_for_each:
            raise ValueError(
                f"Invalid for_each: {for_each}. Must be one of {valid_for_each}"
            )
        self.for_each = for_each
        return self

    def build(self) -> str:
        """Build the SQL trigger statement."""
        if (
            not self.schema
            or not self.table_name
            or not self.trigger_name
            or not self.function_name
        ):
            raise ValueError(
                "Schema, table name, trigger name, and function name are required"
            )

        return f"""
            CREATE OR REPLACE TRIGGER {self.trigger_name}
                {self.timing} {self.operation}
                ON {self.schema}.{self.table_name}
                FOR EACH {self.for_each}
                EXECUTE FUNCTION {self.schema}.{self.function_name}();
        """


# Example of using the new structure
class UserRecordUserAuditEmitter(SQLEmitter):
    """Emits SQL for tracking user record changes."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for user audit function and trigger."""
        statements = []

        # Create function using builder
        schema = self.connection_config.db_schema
        table_name = self.table.name

        # Build the function
        function_body = """
        DECLARE
            -- Function implementation
        BEGIN
            -- Record changes
            NEW.modified_by = (SELECT current_setting('app.current_user', TRUE));
            RETURN NEW;
        END;
        """

        function_sql = (
            SQLFunction()
            .with_schema(schema)
            .with_name(f"{table_name}_audit_user")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_audit_user_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql,
            )
        )

        # Build the trigger
        trigger_sql = (
            SQLTrigger()
            .with_schema(schema)
            .with_table(table_name)
            .with_name(f"{table_name}_audit_user_trigger")
            .with_function(f"{table_name}_audit_user")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE")
            .build()
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_audit_user_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
                depends_on=[f"{table_name}_audit_user_function"],
            )
        )

        return statements


# Example usage in new SQLConfig structure
class UserSQLConfig(SQLConfig):
    """SQL configuration for the user table."""

    table = ...  # UserModel.__table__
    default_emitters = [
        UserRecordUserAuditEmitter,
        # Other emitters...
    ]


# Usage example
def setup_db():
    # Register global observer
    SQLEmitter.register_observer(LoggingSQLObserver())

    # Create connection
    connection_config = ConnectionConfig(...)

    with get_db_connection(connection_config) as conn:
        # Emit SQL for all registered configs
        SQLConfigRegistry.emit_all(conn)
