"""
Domain entities for the SQL module.

This module defines the core domain entities for the SQL module,
providing a rich domain model for SQL statement generation and execution.
"""

from datetime import datetime, UTC
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union

from uno.domain.core import Entity, AggregateRoot, ValueObject


@dataclass(frozen=True)
class SQLStatementId(ValueObject):
    """Identifier for a SQL statement."""

    value: str


@dataclass(frozen=True)
class SQLEmitterId(ValueObject):
    """Identifier for a SQL emitter."""

    value: str


@dataclass(frozen=True)
class SQLConfigId(ValueObject):
    """Identifier for a SQL configuration."""

    value: str


class SQLStatementType(str, Enum):
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


class SQLTransactionIsolationLevel(str, Enum):
    """Transaction isolation levels."""

    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"
    AUTOCOMMIT = "AUTOCOMMIT"


class SQLFunctionVolatility(str, Enum):
    """Function volatility types."""

    VOLATILE = "VOLATILE"
    STABLE = "STABLE"
    IMMUTABLE = "IMMUTABLE"


class SQLFunctionLanguage(str, Enum):
    """SQL function language types."""

    PLPGSQL = "plpgsql"
    SQL = "sql"
    PYTHON = "plpython3u"
    PLTCL = "pltcl"


@dataclass
class SQLStatement(Entity):
    """A SQL statement with metadata.

    This class represents a SQL statement along with metadata about
    the statement including its name, type, and dependencies.
    """

    id: SQLStatementId
    name: str
    type: SQLStatementType
    sql: str
    depends_on: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def has_dependency(self, statement_name: str) -> bool:
        """
        Check if this statement has a dependency on another statement.

        Args:
            statement_name: Name of the statement to check dependency against

        Returns:
            True if this statement depends on the given statement, False otherwise.
        """
        return statement_name in self.depends_on

    def add_dependency(self, statement_name: str) -> None:
        """
        Add a dependency on another statement.

        Args:
            statement_name: Name of the statement to add as a dependency
        """
        if statement_name not in self.depends_on:
            self.depends_on.append(statement_name)

    def remove_dependency(self, statement_name: str) -> bool:
        """
        Remove a dependency on another statement.

        Args:
            statement_name: Name of the statement to remove as a dependency

        Returns:
            True if the dependency was removed, False if it didn't exist
        """
        if statement_name in self.depends_on:
            self.depends_on.remove(statement_name)
            return True
        return False


@dataclass
class SQLExecution(Entity):
    """Record of a SQL statement execution.

    This class represents a record of a SQL statement execution,
    including metadata about the execution like duration and result.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement_id: SQLStatementId
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SQLEmitter(Entity):
    """A SQL emitter that generates SQL statements.

    This class represents a SQL emitter that generates SQL statements
    for database operations based on configuration.
    """

    id: SQLEmitterId
    name: str
    description: Optional[str] = None
    statement_types: List[SQLStatementType] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def generates_statement_type(self, statement_type: SQLStatementType) -> bool:
        """
        Check if this emitter generates statements of the given type.

        Args:
            statement_type: Type of statement to check

        Returns:
            True if this emitter generates statements of the given type, False otherwise.
        """
        return statement_type in self.statement_types

    def add_statement_type(self, statement_type: SQLStatementType) -> None:
        """
        Add a statement type to the types generated by this emitter.

        Args:
            statement_type: Type of statement to add
        """
        if statement_type not in self.statement_types:
            self.statement_types.append(statement_type)
            self.updated_at = datetime.now(UTC)

    def update_configuration(self, config: Dict[str, Any]) -> None:
        """
        Update the configuration for this emitter.

        Args:
            config: New configuration values to merge
        """
        self.configuration.update(config)
        self.updated_at = datetime.now(UTC)


@dataclass
class SQLFunction(Entity):
    """A SQL function definition.

    This class represents a SQL function definition with all its attributes.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    body: str
    args: str = ""
    schema: str = "public"
    return_type: str = "TRIGGER"
    language: SQLFunctionLanguage = SQLFunctionLanguage.PLPGSQL
    volatility: SQLFunctionVolatility = SQLFunctionVolatility.VOLATILE
    security_definer: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_sql(self) -> str:
        """
        Generate SQL statement for this function.

        Returns:
            SQL statement string for creating/replacing this function
        """
        security = "SECURITY DEFINER" if self.security_definer else ""

        return f"""
            CREATE OR REPLACE FUNCTION {self.schema}.{self.name}({self.args})
            RETURNS {self.return_type}
            LANGUAGE {self.language.value}
            {self.volatility.value}
            {security}
            AS $fnct$
            {self.body}
            $fnct$;
        """

    def update_body(self, body: str) -> None:
        """
        Update the function body.

        Args:
            body: New function body
        """
        self.body = body
        self.updated_at = datetime.now(UTC)

    def update_args(self, args: str) -> None:
        """
        Update the function arguments.

        Args:
            args: New function arguments
        """
        self.args = args
        self.updated_at = datetime.now(UTC)


@dataclass
class SQLTrigger(Entity):
    """A SQL trigger definition.

    This class represents a SQL trigger definition with all its attributes.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    table: str
    function_name: str
    schema: str = "public"
    events: List[str] = field(default_factory=list)
    when: Optional[str] = None
    for_each: str = "ROW"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_sql(self) -> str:
        """
        Generate SQL statement for this trigger.

        Returns:
            SQL statement string for creating/replacing this trigger
        """
        events_sql = " OR ".join(self.events)
        when_clause = f"WHEN ({self.when})" if self.when else ""

        return f"""
            CREATE OR REPLACE TRIGGER {self.name}
            {self.for_each} {events_sql} ON {self.schema}.{self.table}
            {when_clause}
            EXECUTE FUNCTION {self.schema}.{self.function_name}();
        """

    def update_events(self, events: List[str]) -> None:
        """
        Update the trigger events.

        Args:
            events: New trigger events
        """
        self.events = events
        self.updated_at = datetime.now(UTC)

    def update_when_condition(self, when: Optional[str]) -> None:
        """
        Update the trigger when condition.

        Args:
            when: New when condition
        """
        self.when = when
        self.updated_at = datetime.now(UTC)


@dataclass
class DatabaseConnectionInfo(Entity):
    """Information about a database connection."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    db_name: str
    db_user: str
    db_host: str
    db_port: int = 5432
    db_schema: str = "public"
    admin_role: Optional[str] = None
    writer_role: Optional[str] = None
    reader_role: Optional[str] = None

    def __post_init__(self):
        """Set default roles if not provided."""
        if not self.admin_role:
            self.admin_role = f"{self.db_name}_admin"

        if not self.writer_role:
            self.writer_role = f"{self.db_name}_writer"

        if not self.reader_role:
            self.reader_role = f"{self.db_name}_reader"


@dataclass
class SQLConfiguration(AggregateRoot):
    """Aggregate root for SQL configuration.

    This class represents the configuration for SQL operations,
    including emitters and database connection info.
    """

    id: SQLConfigId
    name: str
    description: Optional[str] = None
    connection_info: Optional[DatabaseConnectionInfo] = None
    emitters: List[SQLEmitter] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_emitter(self, emitter: SQLEmitter) -> None:
        """
        Add an emitter to this configuration.

        Args:
            emitter: Emitter to add
        """
        if not any(e.id.value == emitter.id.value for e in self.emitters):
            self.emitters.append(emitter)
            self.updated_at = datetime.now(UTC)

    def remove_emitter(self, emitter_id: SQLEmitterId) -> bool:
        """
        Remove an emitter from this configuration.

        Args:
            emitter_id: ID of the emitter to remove

        Returns:
            True if the emitter was removed, False if it wasn't found
        """
        for i, emitter in enumerate(self.emitters):
            if emitter.id.value == emitter_id.value:
                self.emitters.pop(i)
                self.updated_at = datetime.now(UTC)
                return True
        return False

    def get_emitter(self, emitter_id: SQLEmitterId) -> Optional[SQLEmitter]:
        """
        Get an emitter by ID.

        Args:
            emitter_id: ID of the emitter to get

        Returns:
            The emitter if found, None otherwise
        """
        for emitter in self.emitters:
            if emitter.id.value == emitter_id.value:
                return emitter
        return None

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the metadata for this configuration.

        Args:
            metadata: New metadata values to merge
        """
        self.metadata.update(metadata)
        self.updated_at = datetime.now(UTC)

    def set_connection_info(self, connection_info: DatabaseConnectionInfo) -> None:
        """
        Set the database connection information.

        Args:
            connection_info: New connection information
        """
        self.connection_info = connection_info
        self.updated_at = datetime.now(UTC)
