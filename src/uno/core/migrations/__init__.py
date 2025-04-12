"""
Schema migration system for the Uno framework.

This module provides tools for defining, applying, and managing database schema
migrations. It supports both SQL and Python-based migrations, version tracking,
and dependency management between migrations.
"""

from uno.core.migrations.migrator import (
    Migrator, MigrationConfig, MigrationContext, MigrationDirection,
    migration_registry, migrate, register_migration, get_migrations,
    get_applied_migrations, get_pending_migrations
)
from uno.core.migrations.migration import (
    Migration, SqlMigration, PythonMigration, MigrationBase,
    MigrationStatus, create_migration
)
from uno.core.migrations.tracker import (
    MigrationTracker, DatabaseMigrationTracker, get_migration_tracker
)
from uno.core.migrations.providers import (
    MigrationProvider, FileMigrationProvider, DirectoryMigrationProvider,
    register_provider, get_providers, discover_migrations
)
from uno.core.migrations.cli import main as migration_cli

__all__ = [
    # Migrator
    "Migrator", "MigrationConfig", "MigrationContext", "MigrationDirection",
    "migration_registry", "migrate", "register_migration", "get_migrations",
    "get_applied_migrations", "get_pending_migrations",
    
    # Migration
    "Migration", "SqlMigration", "PythonMigration", "MigrationBase",
    "MigrationStatus", "create_migration",
    
    # Tracker
    "MigrationTracker", "DatabaseMigrationTracker", "get_migration_tracker",
    
    # Providers
    "MigrationProvider", "FileMigrationProvider", "DirectoryMigrationProvider",
    "register_provider", "get_providers", "discover_migrations",
    
    # CLI
    "migration_cli"
]