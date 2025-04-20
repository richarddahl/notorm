"""
Base classes and utilities for defining migrations.

This module provides the core classes for defining migrations, including
SQL-based and Python-based migrations.
"""

import os
import re
import uuid
import time
import datetime
from enum import Enum, auto
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union, Callable, Tuple


class MigrationStatus(Enum):
    """Status of a migration."""

    PENDING = auto()
    APPLIED = auto()
    FAILED = auto()
    REVERTED = auto()


@dataclass
class MigrationBase:
    """Base class for migration metadata."""

    id: str
    """Unique identifier for the migration."""

    name: str
    """Human-readable name of the migration."""

    description: str = ""
    """Detailed description of what the migration does."""

    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    """When the migration was created."""

    dependencies: list[str] = field(default_factory=list)
    """List of migration IDs that this migration depends on."""

    tags: list[str] = field(default_factory=list)
    """Tags for categorizing migrations."""

    status: MigrationStatus = MigrationStatus.PENDING
    """Current status of the migration."""

    applied_at: Optional[datetime.datetime] = None
    """When the migration was applied, if it has been."""

    version: str | None = None
    """Optional version identifier for the migration."""

    checksum: str | None = None
    """Checksum of the migration content, used to detect changes."""

    def __post_init__(self):
        """Validate the migration ID format."""
        # Generate version from ID if not provided
        if not self.version and "_" in self.id:
            self.version = self.id.split("_")[0]

        # Validate ID format
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.id):
            raise ValueError(f"Invalid migration ID format: {self.id}")


class Migration(ABC):
    """
    Abstract base class for migrations.

    A migration represents a single change to the database schema.
    Migrations can be applied (to update the schema) or reverted (to undo changes).
    """

    def __init__(self, base: MigrationBase):
        """
        Initialize a migration.

        Args:
            base: Base migration metadata
        """
        self.base = base

    @property
    def id(self) -> str:
        """Get the migration ID."""
        return self.base.id

    @property
    def name(self) -> str:
        """Get the migration name."""
        return self.base.name

    @property
    def description(self) -> str:
        """Get the migration description."""
        return self.base.description

    @property
    def dependencies(self) -> list[str]:
        """Get the migration dependencies."""
        return self.base.dependencies

    @property
    def status(self) -> MigrationStatus:
        """Get the migration status."""
        return self.base.status

    @status.setter
    def status(self, value: MigrationStatus) -> None:
        """Set the migration status."""
        self.base.status = value

    @property
    def applied_at(self) -> Optional[datetime.datetime]:
        """Get when the migration was applied."""
        return self.base.applied_at

    @applied_at.setter
    def applied_at(self, value: Optional[datetime.datetime]) -> None:
        """Set when the migration was applied."""
        self.base.applied_at = value

    @property
    def version(self) -> Optional[str]:
        """Get the migration version."""
        return self.base.version

    @property
    def tags(self) -> list[str]:
        """Get the migration tags."""
        return self.base.tags

    @abstractmethod
    async def apply(self, context: Any) -> None:
        """
        Apply the migration.

        Args:
            context: Migration context with database connection and other dependencies
        """
        pass

    @abstractmethod
    async def revert(self, context: Any) -> None:
        """
        Revert the migration.

        Args:
            context: Migration context with database connection and other dependencies
        """
        pass

    @abstractmethod
    def get_checksum(self) -> str:
        """
        Calculate a checksum for the migration content.

        Returns:
            Checksum string
        """
        pass


class SqlMigration(Migration):
    """
    SQL-based migration.

    This class represents a migration defined as SQL scripts for applying
    and reverting changes.
    """

    def __init__(self, base: MigrationBase, up_sql: str, down_sql: str | None = None):
        """
        Initialize an SQL migration.

        Args:
            base: Base migration metadata
            up_sql: SQL script for applying the migration
            down_sql: SQL script for reverting the migration (optional)
        """
        super().__init__(base)
        self.up_sql = up_sql
        self.down_sql = down_sql

    async def apply(self, context: Any) -> None:
        """
        Apply the migration by executing the up SQL script.

        Args:
            context: Migration context with database connection
        """
        if not self.up_sql:
            raise ValueError(f"Migration {self.id} has no up SQL script")

        # Execute the SQL script
        await context.execute_sql(self.up_sql)

        # Update migration status
        self.status = MigrationStatus.APPLIED
        self.applied_at = datetime.datetime.now()

    async def revert(self, context: Any) -> None:
        """
        Revert the migration by executing the down SQL script.

        Args:
            context: Migration context with database connection
        """
        if not self.down_sql:
            raise ValueError(f"Migration {self.id} has no down SQL script")

        # Execute the SQL script
        await context.execute_sql(self.down_sql)

        # Update migration status
        self.status = MigrationStatus.REVERTED
        self.applied_at = None

    def get_checksum(self) -> str:
        """
        Calculate a checksum for the migration content.

        Returns:
            MD5 hexdigest of the combined up and down SQL scripts
        """
        import hashlib

        content = (self.up_sql or "") + (self.down_sql or "")
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class PythonMigration(Migration):
    """
    Python-based migration.

    This class represents a migration defined as Python functions for applying
    and reverting changes.
    """

    def __init__(
        self,
        base: MigrationBase,
        up_func: Callable[[Any], Any],
        down_func: Optional[Callable[[Any], Any]] = None,
        source_code: str | None = None,
    ):
        """
        Initialize a Python migration.

        Args:
            base: Base migration metadata
            up_func: Function for applying the migration
            down_func: Function for reverting the migration (optional)
            source_code: Source code of the migration functions (for checksum)
        """
        super().__init__(base)
        self.up_func = up_func
        self.down_func = down_func
        self.source_code = source_code

    async def apply(self, context: Any) -> None:
        """
        Apply the migration by calling the up function.

        Args:
            context: Migration context with database connection and other dependencies
        """
        if not self.up_func:
            raise ValueError(f"Migration {self.id} has no up function")

        # Call the function (handle both sync and async functions)
        result = self.up_func(context)
        if hasattr(result, "__await__"):
            await result

        # Update migration status
        self.status = MigrationStatus.APPLIED
        self.applied_at = datetime.datetime.now()

    async def revert(self, context: Any) -> None:
        """
        Revert the migration by calling the down function.

        Args:
            context: Migration context with database connection and other dependencies
        """
        if not self.down_func:
            raise ValueError(f"Migration {self.id} has no down function")

        # Call the function (handle both sync and async functions)
        result = self.down_func(context)
        if hasattr(result, "__await__"):
            await result

        # Update migration status
        self.status = MigrationStatus.REVERTED
        self.applied_at = None

    def get_checksum(self) -> str:
        """
        Calculate a checksum for the migration content.

        Returns:
            MD5 hexdigest of the source code or function objects
        """
        import hashlib
        import inspect

        if self.source_code:
            content = self.source_code
        else:
            # Fall back to inspecting function objects
            up_source = inspect.getsource(self.up_func) if self.up_func else ""
            down_source = inspect.getsource(self.down_func) if self.down_func else ""
            content = up_source + down_source

        return hashlib.md5(content.encode("utf-8")).hexdigest()


def create_migration(
    name: str,
    description: str = "",
    dependencies: list[str] = None,
    tags: list[str] = None,
    version: str | None = None,
    id: str | None = None,
) -> MigrationBase:
    """
    Create a new migration base.

    Args:
        name: Human-readable name of the migration
        description: Detailed description of what the migration does
        dependencies: List of migration IDs that this migration depends on
        tags: Tags for categorizing migrations
        version: Optional version identifier for the migration
        id: Optional custom ID for the migration

    Returns:
        MigrationBase object
    """
    # Generate a timestamp-based ID if not provided
    if not id:
        timestamp = int(time.time())

        # Format name for ID (lowercase, replace spaces with underscores)
        formatted_name = name.lower().replace(" ", "_")

        # Special characters not allowed in ID
        for char in r'!@#$%^&*()+={}[]:;"\',.<>?/\\|':
            formatted_name = formatted_name.replace(char, "_")

        # Generate ID
        if version:
            id = f"{version}_{timestamp}_{formatted_name}"
        else:
            id = f"{timestamp}_{formatted_name}"

    return MigrationBase(
        id=id,
        name=name,
        description=description,
        dependencies=dependencies or [],
        tags=tags or [],
        version=version,
    )
