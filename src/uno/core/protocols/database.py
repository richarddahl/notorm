"""
Database provider protocols.

This module defines Protocol classes for database access, including
connection and session management, health checks, and transaction support.
"""

from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    ContextManager,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)
from contextlib import asynccontextmanager, contextmanager

# Import as optional to avoid direct dependency
try:
    import asyncpg
    import psycopg
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session
except ImportError:
    pass

T = TypeVar("T")
QueryResultT = TypeVar("QueryResultT")


class DatabaseConnectionProtocol(Protocol):
    """
    Protocol for database connections.

    This protocol defines the interface for low-level database connections,
    providing methods for executing queries, transactions, and prepared statements.
    """

    async def fetch(self, query: str, *args, **kwargs) -> list[Any]:
        """
        Execute a query and return all results.

        Args:
            query: The SQL query to execute
            *args: Positional arguments for query parameters
            **kwargs: Keyword arguments for query options

        Returns:
            A list of query results
        """
        ...

    async def fetchrow(self, query: str, *args, **kwargs) -> Optional[Any]:
        """
        Execute a query and return the first row.

        Args:
            query: The SQL query to execute
            *args: Positional arguments for query parameters
            **kwargs: Keyword arguments for query options

        Returns:
            The first row of the result, or None if no results
        """
        ...

    async def fetchval(self, query: str, *args, **kwargs) -> Any:
        """
        Execute a query and return a single value.

        Args:
            query: The SQL query to execute
            *args: Positional arguments for query parameters
            **kwargs: Keyword arguments for query options

        Returns:
            The first value of the first row, or None if no results
        """
        ...

    async def execute(self, query: str, *args, **kwargs) -> str:
        """
        Execute a query and return the status.

        Args:
            query: The SQL query to execute
            *args: Positional arguments for query parameters
            **kwargs: Keyword arguments for query options

        Returns:
            The command status as a string (e.g., "INSERT 0 1")
        """
        ...

    async def executemany(self, query: str, args: list[Any], **kwargs) -> None:
        """
        Execute a query multiple times with different parameters.

        Args:
            query: The SQL query to execute
            args: List of parameter sets for the query
            **kwargs: Keyword arguments for query options
        """
        ...

    async def prepare(self, query: str) -> Any:
        """
        Prepare a statement for execution.

        Args:
            query: The SQL query to prepare

        Returns:
            A prepared statement object
        """
        ...

    async def transaction(self) -> AsyncContextManager[Any]:
        """
        Start a transaction.

        Returns:
            A context manager for the transaction
        """
        ...

    async def close(self) -> None:
        """Close the connection."""
        ...


class DatabaseSessionProtocol(Protocol):
    """
    Protocol for database sessions.

    This protocol defines the interface for ORM-level database sessions,
    providing methods for querying, transactions, and entity management.
    """

    async def execute(self, statement: Any, *args, **kwargs) -> Any:
        """
        Execute a statement.

        Args:
            statement: The statement to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the execution
        """
        ...

    async def scalar(self, statement: Any, *args, **kwargs) -> Any:
        """
        Execute a statement and return a scalar result.

        Args:
            statement: The statement to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The scalar result
        """
        ...

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...

    async def close(self) -> None:
        """Close the session."""
        ...

    async def begin(self) -> None:
        """Begin a transaction."""
        ...

    async def begin_nested(self) -> Any:
        """Begin a nested transaction."""
        ...

    async def flush(self, objects: Optional[list[Any]] = None) -> None:
        """
        Flush pending changes to the database.

        Args:
            objects: Optional list of objects to flush
        """
        ...

    async def refresh(self, object: Any, **kwargs) -> None:
        """
        Refresh an object from the database.

        Args:
            object: The object to refresh
            **kwargs: Keyword arguments
        """
        ...

    def query(self, *entities: Any) -> Any:
        """
        Create a new query.

        Args:
            *entities: The entities to query

        Returns:
            A new query object
        """
        ...


class DatabaseProviderProtocol(Protocol):
    """
    Protocol for database providers.

    This protocol defines the interface for database providers that manage
    connections and sessions for database access, supporting both synchronous
    and asynchronous operations.
    """

    @asynccontextmanager
    async def async_session(self) -> AsyncContextManager[AsyncSession]:
        """
        Get an async session for ORM operations.

        This method provides a context manager for using an async session.

        Yields:
            AsyncSession: SQLAlchemy async session
        """
        ...

    @contextmanager
    def sync_session(self) -> ContextManager[Session]:
        """
        Get a sync session for ORM operations.

        This method provides a context manager for using a sync session.

        Yields:
            Session: SQLAlchemy sync session
        """
        ...

    @asynccontextmanager
    async def async_connection(self) -> AsyncContextManager[Any]:
        """
        Get a raw async connection from the pool.

        This method provides a context manager for using a raw asyncpg connection.
        Useful for operations that require features specific to asyncpg.

        Yields:
            asyncpg.Connection: Raw asyncpg connection
        """
        ...

    @contextmanager
    def sync_connection(self) -> ContextManager[Any]:
        """
        Get a raw sync connection.

        This method provides a context manager for using a raw psycopg connection.
        Useful for DDL operations and other tasks that require synchronous access.

        Yields:
            psycopg.Connection: Raw psycopg connection
        """
        ...

    async def health_check(self) -> bool:
        """
        Check the health of database connections.

        This method verifies that the database is accessible and functioning
        correctly by performing a simple query.

        Returns:
            bool: True if the database is healthy, False otherwise
        """
        ...

    async def close(self) -> None:
        """
        Close all database connections and pools.

        This method should be called when shutting down the application
        to release all database resources.
        """
        ...


class TransactionManagerProtocol(Protocol):
    """
    Protocol for transaction management.

    This protocol defines the interface for transaction management services
    that coordinate database operations within a transaction, supporting
    features like savepoints, rollback, and transaction metadata.
    """

    @asynccontextmanager
    async def transaction(self) -> AsyncContextManager[Any]:
        """
        Begin a new transaction.

        This method provides a context manager for a database transaction,
        automatically committing on successful completion or rolling back
        on exception.

        Yields:
            The transaction context
        """
        ...

    @asynccontextmanager
    async def savepoint(self) -> AsyncContextManager[Any]:
        """
        Create a savepoint within the current transaction.

        This method provides a context manager for a savepoint, allowing
        partial rollback within a transaction.

        Yields:
            The savepoint context
        """
        ...

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...

    @property
    def is_active(self) -> bool:
        """Check if a transaction is currently active."""
        ...

    @property
    def isolation_level(self) -> str:
        """Get the current transaction isolation level."""
        ...

    def set_isolation_level(self, level: str) -> None:
        """
        Set the transaction isolation level.

        Args:
            level: The isolation level (e.g., "READ COMMITTED", "SERIALIZABLE")
        """
        ...


class ConnectionPoolProtocol(Protocol):
    """
    Protocol for connection pools.

    This protocol defines the interface for database connection pools that
    manage connections, ensuring efficient resource usage, connection
    health, and proper cleanup.
    """

    async def acquire(self) -> Any:
        """
        Acquire a connection from the pool.

        Returns:
            A database connection
        """
        ...

    async def release(self, connection: Any) -> None:
        """
        Release a connection back to the pool.

        Args:
            connection: The connection to release
        """
        ...

    async def close(self) -> None:
        """Close the pool and all connections."""
        ...

    async def terminate(self) -> None:
        """
        Terminate the pool and all connections.

        This is a more forceful version of close() that doesn't
        wait for connections to be released.
        """
        ...

    @property
    def min_size(self) -> int:
        """Get the minimum number of connections in the pool."""
        ...

    @property
    def max_size(self) -> int:
        """Get the maximum number of connections in the pool."""
        ...

    @property
    def size(self) -> int:
        """Get the current number of connections in the pool."""
        ...

    @property
    def free_size(self) -> int:
        """Get the number of free connections in the pool."""
        ...

    async def check_health(self) -> bool:
        """
        Check the health of the connection pool.

        Returns:
            bool: True if the pool is healthy, False otherwise
        """
        ...


class DatabaseManagerProtocol(Protocol):
    """
    Protocol for database managers.

    This protocol defines the interface for database managers that
    perform administrative tasks like creating schemas, executing DDL,
    and managing database objects.
    """

    def execute_ddl(self, ddl: str) -> None:
        """
        Execute a DDL statement.

        Args:
            ddl: The DDL statement to execute
        """
        ...

    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.

        Args:
            script: The SQL script to execute
        """
        ...

    def create_schema(self, schema_name: str) -> None:
        """
        Create a database schema.

        Args:
            schema_name: The name of the schema to create
        """
        ...

    def drop_schema(self, schema_name: str, cascade: bool = False) -> None:
        """
        Drop a database schema.

        Args:
            schema_name: The name of the schema to drop
            cascade: Whether to cascade the drop operation
        """
        ...

    def create_extension(self, extension_name: str, schema: str | None = None) -> None:
        """
        Create a PostgreSQL extension.

        Args:
            extension_name: The name of the extension to create
            schema: Optional schema to create the extension in
        """
        ...

    def table_exists(self, table_name: str, schema: str | None = None) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: The name of the table to check
            schema: Optional schema name

        Returns:
            bool: True if the table exists, False otherwise
        """
        ...

    def function_exists(self, function_name: str, schema: str | None = None) -> bool:
        """
        Check if a function exists.

        Args:
            function_name: The name of the function to check
            schema: Optional schema name

        Returns:
            bool: True if the function exists, False otherwise
        """
        ...

    def index_exists(self, index_name: str, schema: str | None = None) -> bool:
        """
        Check if an index exists.

        Args:
            index_name: The name of the index to check
            schema: Optional schema name

        Returns:
            bool: True if the index exists, False otherwise
        """
        ...


class QueryExecutorProtocol(Protocol, Generic[QueryResultT]):
    """
    Protocol for query executors.

    This protocol defines the interface for services that execute
    database queries, supporting various query types and results.
    """

    async def execute(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> QueryResultT:
        """
        Execute a query.

        Args:
            query: The SQL query to execute
            params: Optional parameters for the query

        Returns:
            The query result
        """
        ...

    async def execute_many(
        self, query: str, params_list: list[dict[str, Any]]
    ) -> list[QueryResultT]:
        """
        Execute a query multiple times with different parameters.

        Args:
            query: The SQL query to execute
            params_list: List of parameter dictionaries

        Returns:
            A list of query results
        """
        ...

    async def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.

        Args:
            script: The SQL script to execute
        """
        ...


# Alias for backward compatibility with legacy code
UnoDatabaseProviderProtocol = DatabaseProviderProtocol
