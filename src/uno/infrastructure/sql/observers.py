# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL observers for monitoring and logging SQL operations."""

import logging
from typing import List, Protocol

from uno.sql.statement import SQLStatement


class SQLObserver(Protocol):
    """Observer for SQL emitter events.

    Protocol defining the interface for SQL emitter event observers.
    """

    def on_sql_generated(self, source: str, statements: list[SQLStatement]) -> None:
        """Called when SQL statements are generated.

        Args:
            source: Source of the SQL statements (typically emitter class name)
            statements: Generated SQL statements
        """
        ...

    def on_sql_executed(
        self, source: str, statements: list[SQLStatement], duration: float
    ) -> None:
        """Called when SQL statements are executed.

        Args:
            source: Source of the SQL statements
            statements: Executed SQL statements
            duration: Execution duration in seconds
        """
        ...

    def on_sql_error(
        self, source: str, statements: list[SQLStatement], error: Exception
    ) -> None:
        """Called when SQL execution fails.

        Args:
            source: Source of the SQL statements
            statements: SQL statements that failed
            error: Exception that occurred
        """
        ...


class BaseObserver:
    """Base class for SQL observers.

    This concrete base class implements the SQLObserver protocol with empty methods.
    Subclasses should override these methods to provide actual implementations.
    """

    def on_sql_generated(self, source: str, statements: list[SQLStatement]) -> None:
        """Called when SQL statements are generated (base implementation does nothing).

        Args:
            source: Source of the SQL statements
            statements: Generated SQL statements
        """
        pass

    def on_sql_executed(
        self, source: str, statements: list[SQLStatement], duration: float
    ) -> None:
        """Called when SQL statements are executed (base implementation does nothing).

        Args:
            source: Source of the SQL statements
            statements: Executed SQL statements
            duration: Execution duration in seconds
        """
        pass

    def on_sql_error(
        self, source: str, statements: list[SQLStatement], error: Exception
    ) -> None:
        """Called when SQL execution fails (base implementation does nothing).

        Args:
            source: Source of the SQL statements
            statements: SQL statements that failed
            error: Exception that occurred
        """
        pass


class LoggingSQLObserver(BaseObserver):
    """Observer that logs SQL operations.

    Implements the SQLObserver protocol to log SQL operations.

    Attributes:
        logger: Logger to use for logging
    """

    def __init__(self, logger: logging.Logger = None):
        """Initialize the observer with a logger.

        Args:
            logger: Logger to use for logging (defaults to module logger)
        """
        self.logger = logger or logging.getLogger(__name__)

    def on_sql_generated(self, source: str, statements: list[SQLStatement]) -> None:
        """Log SQL statement generation.

        Args:
            source: Source of the SQL statements
            statements: Generated SQL statements
        """
        self.logger.debug(f"Generated {len(statements)} SQL statements from {source}")
        for stmt in statements:
            self.logger.debug(f"  - {stmt.name} ({stmt.type.value})")

    def on_sql_executed(
        self, source: str, statements: list[SQLStatement], duration: float
    ) -> None:
        """Log SQL statement execution.

        Args:
            source: Source of the SQL statements
            statements: Executed SQL statements
            duration: Execution duration in seconds
        """
        self.logger.info(
            f"Executed {len(statements)} SQL statements from {source} in {duration:.2f}s"
        )

    def on_sql_error(
        self, source: str, statements: list[SQLStatement], error: Exception
    ) -> None:
        """Log SQL execution errors.

        Args:
            source: Source of the SQL statements
            statements: SQL statements that failed
            error: Exception that occurred
        """
        self.logger.error(f"SQL error in {source}: {error}")
        self.logger.error(f"Failed statements: {[stmt.name for stmt in statements]}")
