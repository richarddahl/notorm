"""
Core migration system implementation.

This module provides the Migrator class, which is responsible for applying and
reverting migrations, tracking migration status, and managing dependencies.
"""

import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union, Tuple
import asyncio

from uno.core.migrations.migration import Migration, MigrationStatus


class MigrationDirection(Enum):
    """Direction of migration operation."""

    UP = auto()
    DOWN = auto()


@dataclass
class MigrationConfig:
    """Configuration for the migration system."""

    schema_name: str = "public"
    """Name of the database schema where migrations are applied."""

    migration_table: str = "uno_migrations"
    """Name of the table used to track applied migrations."""

    require_transactional: bool = True
    """Whether migrations must be run in a transaction."""

    allow_missing_down: bool = False
    """Whether to allow migrations without down/revert functionality."""

    batch_size: int = 10
    """Number of migrations to apply in a single batch."""

    migration_paths: list[str] = field(default_factory=list)
    """Paths where migration files are located."""

    migration_modules: list[str] = field(default_factory=list)
    """Python modules where migrations are defined."""

    before_migration_hook: Optional[Any] = None
    """Hook function called before applying a migration."""

    after_migration_hook: Optional[Any] = None
    """Hook function called after applying a migration."""

    verbose: bool = False
    """Whether to output verbose logging."""


@dataclass
class MigrationContext:
    """Context for executing migrations."""

    connection: Any
    """Database connection object."""

    config: MigrationConfig
    """Migration configuration."""

    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("uno.migrations")
    )
    """Logger instance."""

    async def execute_sql(self, sql: str, params: Any = None) -> Any:
        """
        Execute an SQL statement.

        Args:
            sql: SQL statement to execute
            params: Optional parameters for the SQL statement (list, tuple, or dict)

        Returns:
            Result of the SQL execution
        """
        if hasattr(self.connection, "execute"):
            # Handle SQLAlchemy-like connections
            if params is None:
                return await self.connection.execute(sql)
            else:
                return await self.connection.execute(sql, params)
        elif hasattr(self.connection, "cursor"):
            # Handle database-api connections
            cursor = await self.connection.cursor()
            if params is None:
                await cursor.execute(sql)
            else:
                await cursor.execute(sql, params)
            return cursor
        else:
            raise TypeError("Unsupported connection type")

    async def execute_transaction(self, func, *args, **kwargs) -> Any:
        """
        Execute a function within a transaction.

        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function
        """
        if hasattr(self.connection, "begin"):
            # Handle SQLAlchemy-like connections
            async with self.connection.begin():
                return await func(*args, **kwargs)
        elif hasattr(self.connection, "transaction"):
            # Handle asyncpg-like connections
            async with self.connection.transaction():
                return await func(*args, **kwargs)
        else:
            # Handle raw connections (best effort)
            try:
                await self.execute_sql("BEGIN")
                result = await func(*args, **kwargs)
                await self.execute_sql("COMMIT")
                return result
            except Exception as e:
                await self.execute_sql("ROLLBACK")
                raise e


# Global registry of migrations
migration_registry: dict[str, Migration] = {}


def get_revision_id() -> str:
    """
    Generate a unique revision ID for migrations.

    Returns:
        A unique string identifier for a migration
    """
    import uuid
    import time

    # Format: timestamp_random
    timestamp = int(time.time())
    random_part = str(uuid.uuid4())[:8]

    return f"{timestamp}_{random_part}"


def register_migration(migration: Migration) -> None:
    """
    Register a migration with the global registry.

    Args:
        migration: Migration to register
    """
    migration_registry[migration.id] = migration


def get_migrations() -> dict[str, Migration]:
    """
    Get all registered migrations.

    Returns:
        Dictionary of migration ID to Migration object
    """
    return migration_registry.copy()


def get_applied_migrations() -> list[Migration]:
    """
    Get all applied migrations.

    Returns:
        List of applied Migration objects
    """
    return [
        m for m in migration_registry.values() if m.status == MigrationStatus.APPLIED
    ]


def get_pending_migrations() -> list[Migration]:
    """
    Get all pending migrations.

    Returns:
        List of pending Migration objects
    """
    return [
        m for m in migration_registry.values() if m.status == MigrationStatus.PENDING
    ]


class Migrator:
    """
    Main class for managing database migrations.

    The Migrator is responsible for applying and reverting migrations,
    tracking migration status, and managing dependencies.
    """

    def __init__(self, config: MigrationConfig):
        """
        Initialize the migrator.

        Args:
            config: Migration configuration
        """
        self.config = config
        self.logger = logging.getLogger("uno.migrations")

        if self.config.verbose:
            self.logger.setLevel(logging.DEBUG)

    async def ensure_migration_table(self, context: MigrationContext) -> None:
        """
        Ensure the migration tracking table exists.

        Args:
            context: Migration context with database connection
        """
        # Create the migration table if it doesn't exist
        schema_prefix = (
            f"{self.config.schema_name}." if self.config.schema_name != "public" else ""
        )
        table_name = f"{schema_prefix}{self.config.migration_table}"

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
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

        await context.execute_sql(create_table_sql)

    async def get_applied_migration_ids(self, context: MigrationContext) -> Set[str]:
        """
        Get the IDs of all applied migrations.

        Args:
            context: Migration context with database connection

        Returns:
            Set of applied migration IDs
        """
        schema_prefix = (
            f"{self.config.schema_name}." if self.config.schema_name != "public" else ""
        )
        table_name = f"{schema_prefix}{self.config.migration_table}"

        query = f"SELECT id FROM {table_name}"
        result = await context.execute_sql(query)

        if hasattr(result, "fetchall"):
            # Handle database-api cursors
            rows = await result.fetchall()
            return {row[0] for row in rows}
        else:
            # Handle SQLAlchemy-like results
            return {row[0] for row in result}

    async def record_migration(
        self, context: MigrationContext, migration: Migration, revert: bool = False
    ) -> None:
        """
        Record a migration as applied or reverted.

        Args:
            context: Migration context with database connection
            migration: Migration that was applied or reverted
            revert: Whether the migration was reverted (default: False)
        """
        schema_prefix = (
            f"{self.config.schema_name}." if self.config.schema_name != "public" else ""
        )
        table_name = f"{schema_prefix}{self.config.migration_table}"

        # Get tracker to handle database-specific operations
        from uno.core.migrations.tracker import get_migration_tracker

        tracker = get_migration_tracker()

        if tracker is not None:
            # Use the tracker to record or remove the migration
            if revert:
                await tracker.remove_migration(migration.id)
            else:
                await tracker.record_migration(migration)
            return

        # Fallback implementation if no tracker is set
        if revert:
            # Delete the migration record
            try:
                # Use the context's execute transaction method for safety
                async def delete_migration():
                    query = f"DELETE FROM {table_name} WHERE id = %s"
                    return await context.execute_sql(query, [migration.id])

                await context.execute_transaction(delete_migration)
                self.logger.info(f"Removed migration: {migration.id}")
            except Exception as e:
                self.logger.error(f"Failed to remove migration record: {e}")
                raise
        else:
            # Insert the migration record
            import json

            # Prepare data
            checksum = migration.get_checksum()

            # Safe handling of tags
            if migration.tags:
                tags = (
                    "{"
                    + ",".join(f'"{tag.replace("\"", "")}"' for tag in migration.tags)
                    + "}"
                )
            else:
                tags = "{}"

            metadata = json.dumps({})

            try:
                # Use the context's execute transaction method for safety
                async def insert_migration():
                    # Use proper parameter binding based on database type
                    query = f"""
                    INSERT INTO {table_name} (
                        id, name, applied_at, version, checksum, description, tags, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    # Parameters as a list
                    params = [
                        migration.id,
                        migration.name,
                        migration.applied_at.isoformat(),
                        migration.version,
                        checksum,
                        migration.description,
                        tags,
                        metadata,
                    ]

                    return await context.execute_sql(query, params)

                await context.execute_transaction(insert_migration)
                self.logger.info(f"Recorded migration: {migration.id}")
            except Exception as e:
                self.logger.error(f"Failed to record migration: {e}")
                raise

    def _build_dependency_graph(
        self, migrations: dict[str, Migration]
    ) -> dict[str, Set[str]]:
        """
        Build a dependency graph for migrations.

        Args:
            migrations: Dictionary of migration ID to Migration object

        Returns:
            Dictionary mapping migration ID to set of dependent migration IDs
        """
        graph = {mid: set() for mid in migrations}

        for mid, migration in migrations.items():
            for dep_id in migration.dependencies:
                if dep_id in graph:
                    graph[dep_id].add(mid)

        return graph

    def _calculate_execution_order(
        self, migrations: dict[str, Migration], direction: MigrationDirection
    ) -> list[Migration]:
        """
        Calculate the order in which migrations should be executed.

        Args:
            migrations: Dictionary of migration ID to Migration object
            direction: Direction of migration (UP or DOWN)

        Returns:
            List of Migration objects in execution order
        """
        if not migrations:
            return []

        # Build dependency graph
        if direction == MigrationDirection.UP:
            # For UP direction, we need "depends on" relationships
            depends_on = {mid: set(m.dependencies) for mid, m in migrations.items()}
            graph = depends_on
        else:
            # For DOWN direction, we need "depended by" relationships
            graph = self._build_dependency_graph(migrations)

        # Topological sort
        result = []
        visited = set()
        temp_visited = set()

        def visit(migration_id):
            if migration_id in temp_visited:
                # Detect cycles
                cycle_path = " -> ".join(list(temp_visited) + [migration_id])
                raise ValueError(f"Circular dependency detected: {cycle_path}")

            if migration_id not in visited and migration_id in migrations:
                temp_visited.add(migration_id)

                # Visit dependencies first for UP direction, dependents first for DOWN direction
                for dep_id in graph.get(migration_id, set()):
                    if dep_id in migrations:
                        visit(dep_id)

                temp_visited.remove(migration_id)
                visited.add(migration_id)
                result.append(migrations[migration_id])

        # Visit all migrations
        for migration_id in migrations:
            if migration_id not in visited:
                visit(migration_id)

        # For DOWN direction, we need to reverse the order
        if direction == MigrationDirection.DOWN:
            result.reverse()

        return result

    async def _apply_single_migration(
        self, context: MigrationContext, migration: Migration
    ) -> None:
        """
        Apply a single migration.

        Args:
            context: Migration context with database connection
            migration: Migration to apply
        """
        self.logger.info(f"Applying migration: {migration.id} - {migration.name}")

        # Call the before migration hook if provided
        if self.config.before_migration_hook:
            await self.config.before_migration_hook(context, migration)

        # Apply the migration
        try:
            if self.config.require_transactional:
                await context.execute_transaction(migration.apply, context)
            else:
                await migration.apply(context)

            # Record the migration
            await self.record_migration(context, migration)

            self.logger.info(f"Successfully applied migration: {migration.id}")
        except Exception as e:
            self.logger.error(f"Failed to apply migration {migration.id}: {str(e)}")
            migration.status = MigrationStatus.FAILED
            raise

        # Call the after migration hook if provided
        if self.config.after_migration_hook:
            await self.config.after_migration_hook(context, migration)

    async def _revert_single_migration(
        self, context: MigrationContext, migration: Migration
    ) -> None:
        """
        Revert a single migration.

        Args:
            context: Migration context with database connection
            migration: Migration to revert
        """
        self.logger.info(f"Reverting migration: {migration.id} - {migration.name}")

        # Call the before migration hook if provided
        if self.config.before_migration_hook:
            await self.config.before_migration_hook(context, migration)

        # Revert the migration
        try:
            if self.config.require_transactional:
                await context.execute_transaction(migration.revert, context)
            else:
                await migration.revert(context)

            # Record the migration as reverted
            await self.record_migration(context, migration, revert=True)

            self.logger.info(f"Successfully reverted migration: {migration.id}")
        except Exception as e:
            self.logger.error(f"Failed to revert migration {migration.id}: {str(e)}")
            migration.status = MigrationStatus.FAILED
            raise

        # Call the after migration hook if provided
        if self.config.after_migration_hook:
            await self.config.after_migration_hook(context, migration)

    async def apply_migrations(
        self,
        context: MigrationContext,
        migrations: Optional[list[Migration]] = None,
        target: str | None = None,
    ) -> Tuple[int, list[Migration]]:
        """
        Apply pending migrations.

        Args:
            context: Migration context with database connection
            migrations: Optional list of migrations to apply (default: all pending)
            target: Optional target migration ID to migrate up to

        Returns:
            Tuple of (number of migrations applied, list of applied migrations)
        """
        # Ensure migration table exists
        await self.ensure_migration_table(context)

        # Get applied migration IDs
        applied_ids = await self.get_applied_migration_ids(context)

        # Determine migrations to apply
        if migrations is None:
            # Use all registered migrations
            migrations_dict = {
                mid: m
                for mid, m in migration_registry.items()
                if mid not in applied_ids
            }
        else:
            # Use provided migrations
            migrations_dict = {m.id: m for m in migrations if m.id not in applied_ids}

        # Filter by target if provided
        if target and target in migration_registry:
            # Build dependency graph to include target and its dependencies
            target_deps = set()

            def collect_deps(mid):
                target_deps.add(mid)
                for dep_id in migration_registry[mid].dependencies:
                    if dep_id in migration_registry and dep_id not in target_deps:
                        collect_deps(dep_id)

            collect_deps(target)
            migrations_dict = {
                mid: m for mid, m in migrations_dict.items() if mid in target_deps
            }

        # Calculate execution order
        ordered_migrations = self._calculate_execution_order(
            migrations_dict, MigrationDirection.UP
        )

        if not ordered_migrations:
            self.logger.info("No migrations to apply")
            return 0, []

        self.logger.info(f"Applying {len(ordered_migrations)} migrations")

        # Apply migrations
        applied_migrations = []

        for migration in ordered_migrations:
            await self._apply_single_migration(context, migration)
            applied_migrations.append(migration)

            # Check for batch size limit
            if len(applied_migrations) >= self.config.batch_size:
                self.logger.info(
                    f"Reached batch size limit of {self.config.batch_size} migrations"
                )
                break

        return len(applied_migrations), applied_migrations

    async def revert_migrations(
        self,
        context: MigrationContext,
        migrations: Optional[list[Migration]] = None,
        target: str | None = None,
        steps: int = 1,
    ) -> Tuple[int, list[Migration]]:
        """
        Revert applied migrations.

        Args:
            context: Migration context with database connection
            migrations: Optional list of migrations to revert (default: last applied)
            target: Optional target migration ID to migrate down to
            steps: Number of migrations to revert (default: 1)

        Returns:
            Tuple of (number of migrations reverted, list of reverted migrations)
        """
        # Ensure migration table exists
        await self.ensure_migration_table(context)

        # Get applied migration IDs
        applied_ids = await self.get_applied_migration_ids(context)

        # Determine migrations to revert
        if migrations is None:
            # Use all applied migrations from registry
            migrations_dict = {
                mid: m for mid, m in migration_registry.items() if mid in applied_ids
            }
        else:
            # Use provided migrations
            migrations_dict = {m.id: m for m in migrations if m.id in applied_ids}

        # Filter by target if provided
        if target and target in migration_registry:
            # Keep migrations applied after the target
            target_deps = set()

            def collect_deps(mid):
                target_deps.add(mid)
                for dep_id in self._build_dependency_graph(migration_registry).get(
                    mid, set()
                ):
                    if dep_id in migration_registry and dep_id not in target_deps:
                        collect_deps(dep_id)

            collect_deps(target)
            migrations_dict = {
                mid: m for mid, m in migrations_dict.items() if mid not in target_deps
            }

        # Calculate execution order
        ordered_migrations = self._calculate_execution_order(
            migrations_dict, MigrationDirection.DOWN
        )

        # Limit by steps
        if steps > 0 and steps < len(ordered_migrations):
            ordered_migrations = ordered_migrations[:steps]

        if not ordered_migrations:
            self.logger.info("No migrations to revert")
            return 0, []

        self.logger.info(f"Reverting {len(ordered_migrations)} migrations")

        # Check for migrations without down scripts
        if self.config.allow_missing_down:
            # Filter out migrations without down functionality
            filtered_migrations = []
            for migration in ordered_migrations:
                if (
                    isinstance(migration, migration_registry["SqlMigration"])
                    and migration.down_sql is None
                ) or (
                    isinstance(migration, migration_registry["PythonMigration"])
                    and migration.down_func is None
                ):
                    self.logger.warning(
                        f"Skipping migration {migration.id} that has no down/revert functionality"
                    )
                else:
                    filtered_migrations.append(migration)
            ordered_migrations = filtered_migrations

        # Revert migrations
        reverted_migrations = []

        for migration in ordered_migrations:
            await self._revert_single_migration(context, migration)
            reverted_migrations.append(migration)

        return len(reverted_migrations), reverted_migrations


async def migrate(
    connection: Any,
    config: MigrationConfig,
    direction: MigrationDirection = MigrationDirection.UP,
    target: str | None = None,
    steps: int = 0,
) -> Tuple[int, list[Migration]]:
    """
    Apply or revert migrations.

    Args:
        connection: Database connection
        config: Migration configuration
        direction: Direction of migration (UP or DOWN)
        target: Optional target migration ID
        steps: Number of migrations to apply/revert (0 for all)

    Returns:
        Tuple of (number of migrations applied/reverted, list of migrations)
    """
    # Create migrator and context
    migrator = Migrator(config)
    context = MigrationContext(connection=connection, config=config)

    if direction == MigrationDirection.UP:
        return await migrator.apply_migrations(context, target=target)
    else:
        return await migrator.revert_migrations(context, target=target, steps=steps)
