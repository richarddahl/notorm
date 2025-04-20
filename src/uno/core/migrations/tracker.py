"""
Migration tracking system.

This module provides classes for tracking the status of migrations, including
which migrations have been applied and when.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Any

from uno.core.migrations.migration import Migration, MigrationStatus


class MigrationTracker(ABC):
    """
    Abstract base class for migration trackers.

    A migration tracker is responsible for keeping track of which migrations
    have been applied and when.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the migration tracker."""
        pass

    @abstractmethod
    async def get_applied_migrations(self) -> Set[str]:
        """
        Get the set of applied migration IDs.

        Returns:
            Set of applied migration IDs
        """
        pass

    @abstractmethod
    async def record_migration(self, migration: Migration) -> None:
        """
        Record a migration as applied.

        Args:
            migration: Applied migration
        """
        pass

    @abstractmethod
    async def remove_migration(self, migration_id: str) -> None:
        """
        Remove a migration from the applied set.

        Args:
            migration_id: ID of the migration to remove
        """
        pass

    @abstractmethod
    async def get_migration_history(self) -> list[dict[str, Any]]:
        """
        Get the history of applied migrations.

        Returns:
            List of migration records with metadata
        """
        pass


class DatabaseMigrationTracker(MigrationTracker):
    """
    Database-backed migration tracker.

    This tracker stores migration status in a database table.
    """

    def __init__(
        self,
        connection: Any,
        schema_name: str = "public",
        table_name: str = "uno_migrations",
    ):
        """
        Initialize the database migration tracker.

        Args:
            connection: Database connection
            schema_name: Name of the database schema (default: "public")
            table_name: Name of the migrations table (default: "uno_migrations")
        """
        self.connection = connection
        self.schema_name = schema_name
        self.table_name = table_name
        self.logger = logging.getLogger("uno.migrations.tracker")

    async def initialize(self) -> None:
        """Initialize the migration tracker by creating the migrations table if it doesn't exist."""
        schema_prefix = f"{self.schema_name}." if self.schema_name != "public" else ""
        full_table_name = f"{schema_prefix}{self.table_name}"

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {full_table_name} (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE NOT NULL,
            version VARCHAR(255),
            checksum VARCHAR(255),
            description TEXT,
            tags TEXT[],
            metadata JSONB
        )
        """

        # Execute the SQL
        await self._execute_sql(create_table_sql)
        self.logger.debug(f"Initialized migration tracker with table {full_table_name}")

    async def get_applied_migrations(self) -> Set[str]:
        """
        Get the set of applied migration IDs from the database.

        Returns:
            Set of applied migration IDs
        """
        schema_prefix = f"{self.schema_name}." if self.schema_name != "public" else ""
        full_table_name = f"{schema_prefix}{self.table_name}"

        query = f"SELECT id FROM {full_table_name}"
        result = await self._execute_sql(query)

        if hasattr(result, "fetchall"):
            # Handle database-api cursors
            rows = await result.fetchall()
            return {row[0] for row in rows}
        else:
            # Handle SQLAlchemy-like results
            return {row[0] for row in result}

    async def record_migration(self, migration: Migration) -> None:
        """
        Record a migration as applied in the database.

        Args:
            migration: Applied migration
        """
        schema_prefix = f"{self.schema_name}." if self.schema_name != "public" else ""
        full_table_name = f"{schema_prefix}{self.table_name}"

        # Prepare JSON data
        import json

        # Safe handling of tags and metadata
        if migration.tags:
            tags = (
                "{"
                + ",".join(f'"{tag.replace("\"", "")}"' for tag in migration.tags)
                + "}"
            )
        else:
            tags = "{}"

        metadata = json.dumps({})

        # Determine connection type and use appropriate parameter binding
        if hasattr(self.connection, "execute"):
            # SQLAlchemy-like connection
            query = f"""
            INSERT INTO {full_table_name} (
                id, name, applied_at, version, checksum, description, tags, metadata
            ) VALUES (
                :id, :name, :applied_at, :version, :checksum, :description, :tags, :metadata
            )
            """

            params = {
                "id": migration.id,
                "name": migration.name,
                "applied_at": migration.applied_at.isoformat(),
                "version": migration.version,
                "checksum": migration.get_checksum(),
                "description": migration.description,
                "tags": tags,
                "metadata": metadata,
            }

            await self.connection.execute(query, params)
        else:
            # Database-api or asyncpg-like connection
            query = f"""
            INSERT INTO {full_table_name} (
                id, name, applied_at, version, checksum, description, tags, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8
            )
            """

            # Create parameters list
            params = [
                migration.id,
                migration.name,
                migration.applied_at.isoformat(),
                migration.version,
                migration.get_checksum(),
                migration.description,
                tags,
                metadata,
            ]

            # Execute with parameters
            cursor = await self.connection.cursor()
            await cursor.execute(query, params)

        self.logger.info(f"Recorded migration: {migration.id}")

    async def remove_migration(self, migration_id: str) -> None:
        """
        Remove a migration from the applied set in the database.

        Args:
            migration_id: ID of the migration to remove
        """
        schema_prefix = f"{self.schema_name}." if self.schema_name != "public" else ""
        full_table_name = f"{schema_prefix}{self.table_name}"

        # Determine connection type and use appropriate parameter binding
        if hasattr(self.connection, "execute"):
            # SQLAlchemy-like connection
            query = f"DELETE FROM {full_table_name} WHERE id = :id"
            await self.connection.execute(query, {"id": migration_id})
        else:
            # Database-api or asyncpg-like connection
            query = f"DELETE FROM {full_table_name} WHERE id = $1"
            cursor = await self.connection.cursor()
            await cursor.execute(query, [migration_id])

        self.logger.info(f"Removed migration: {migration_id}")

    async def get_migration_history(self) -> list[dict[str, Any]]:
        """
        Get the history of applied migrations from the database.

        Returns:
            List of migration records with metadata
        """
        schema_prefix = f"{self.schema_name}." if self.schema_name != "public" else ""
        full_table_name = f"{schema_prefix}{self.table_name}"

        query = f"""
        SELECT id, name, applied_at, version, checksum, description, tags, metadata
        FROM {full_table_name}
        ORDER BY applied_at
        """

        result = await self._execute_sql(query)

        if hasattr(result, "fetchall"):
            # Handle database-api cursors
            rows = await result.fetchall()
            columns = [column[0] for column in result.description]
            return [dict(zip(columns, row)) for row in rows]
        else:
            # Handle SQLAlchemy-like results
            return [dict(row) for row in result]

    async def _execute_sql(self, sql: str) -> Any:
        """
        Execute an SQL statement.

        Args:
            sql: SQL statement to execute

        Returns:
            Result of the SQL execution
        """
        if hasattr(self.connection, "execute"):
            # Handle SQLAlchemy-like connections
            return await self.connection.execute(sql)
        elif hasattr(self.connection, "cursor"):
            # Handle database-api connections
            cursor = await self.connection.cursor()
            await cursor.execute(sql)
            return cursor
        else:
            raise TypeError("Unsupported connection type")


class FileMigrationTracker(MigrationTracker):
    """
    File-based migration tracker.

    This tracker stores migration status in a JSON file.
    """

    def __init__(self, file_path: str):
        """
        Initialize the file migration tracker.

        Args:
            file_path: Path to the JSON file for storing migration status
        """
        self.file_path = file_path
        self.logger = logging.getLogger("uno.migrations.tracker")

    async def initialize(self) -> None:
        """Initialize the migration tracker by creating the JSON file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

            # Create an empty migration history
            await self._write_history([])
            self.logger.debug(
                f"Initialized migration tracker with file {self.file_path}"
            )

    async def get_applied_migrations(self) -> Set[str]:
        """
        Get the set of applied migration IDs from the file.

        Returns:
            Set of applied migration IDs
        """
        history = await self._read_history()
        return {migration["id"] for migration in history}

    async def record_migration(self, migration: Migration) -> None:
        """
        Record a migration as applied in the file.

        Args:
            migration: Applied migration
        """
        history = await self._read_history()

        # Create migration record
        record = {
            "id": migration.id,
            "name": migration.name,
            "applied_at": migration.applied_at.isoformat(),
            "version": migration.version,
            "checksum": migration.get_checksum(),
            "description": migration.description,
            "tags": migration.tags,
            "metadata": {},
        }

        # Add to history
        history.append(record)

        # Write back to file
        await self._write_history(history)
        self.logger.info(f"Recorded migration: {migration.id}")

    async def remove_migration(self, migration_id: str) -> None:
        """
        Remove a migration from the applied set in the file.

        Args:
            migration_id: ID of the migration to remove
        """
        history = await self._read_history()

        # Filter out the migration
        new_history = [m for m in history if m["id"] != migration_id]

        # Write back to file
        await self._write_history(new_history)
        self.logger.info(f"Removed migration: {migration_id}")

    async def get_migration_history(self) -> list[dict[str, Any]]:
        """
        Get the history of applied migrations from the file.

        Returns:
            List of migration records with metadata
        """
        return await self._read_history()

    async def _read_history(self) -> list[dict[str, Any]]:
        """
        Read migration history from the file.

        Returns:
            List of migration records
        """
        if not os.path.exists(self.file_path):
            return []

        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.logger.warning(
                f"Could not parse migration history file: {self.file_path}"
            )
            return []

    async def _write_history(self, history: list[dict[str, Any]]) -> None:
        """
        Write migration history to the file.

        Args:
            history: List of migration records
        """
        with open(self.file_path, "w") as f:
            json.dump(history, f, indent=2)


# Global tracker instance
_migration_tracker: Optional[MigrationTracker] = None


def get_migration_tracker() -> Optional[MigrationTracker]:
    """
    Get the global migration tracker instance.

    Returns:
        Migration tracker instance or None if not set
    """
    return _migration_tracker


def set_migration_tracker(tracker: MigrationTracker) -> None:
    """
    Set the global migration tracker instance.

    Args:
        tracker: Migration tracker instance
    """
    global _migration_tracker
    _migration_tracker = tracker
