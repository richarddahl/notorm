# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Migration providers for loading migrations from different sources.

This module provides classes for loading migrations from different sources,
such as files and directories.
"""

import os
import re
import glob
import inspect
import importlib.util
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Any, Union, Callable, Type

from uno.core.migrations.migration import (
    Migration,
    SqlMigration,
    PythonMigration,
    MigrationBase,
    create_migration,
)


class MigrationProvider(ABC):
    """
    Abstract base class for migration providers.

    A migration provider is responsible for loading migrations from a specific
    source, such as files or Python modules.
    """

    @abstractmethod
    async def load_migrations(self) -> list[Migration]:
        """
        Load migrations from the provider's source.

        Returns:
            List of Migration objects
        """
        pass


class FileMigrationProvider(MigrationProvider):
    """
    Provider for loading migrations from individual files.

    This provider loads migrations from SQL or Python files.
    """

    def __init__(self, file_paths: list[str]):
        """
        Initialize the file migration provider.

        Args:
            file_paths: List of file paths to load migrations from
        """
        self.file_paths = file_paths

    async def load_migrations(self) -> list[Migration]:
        """
        Load migrations from the specified files.

        Returns:
            List of Migration objects
        """
        migrations = []

        for file_path in self.file_paths:
            if not os.path.exists(file_path):
                continue

            # Determine migration type based on file extension
            if file_path.endswith(".sql"):
                migration = await self._load_sql_migration(file_path)
            elif file_path.endswith(".py"):
                migration = await self._load_python_migration(file_path)
            else:
                # Skip unsupported file types
                continue

            if migration:
                migrations.append(migration)

        return migrations

    async def _load_sql_migration(self, file_path: str) -> Optional[SqlMigration]:
        """
        Load an SQL migration from a file.

        Args:
            file_path: Path to the SQL file

        Returns:
            SqlMigration object or None if loading fails
        """
        # Extract migration ID and name from filename
        filename = os.path.basename(file_path)
        match = re.match(r"(\d+)(?:_([^\.]+))?\.sql", filename)

        if not match:
            # Try another format: V1__Create_initial_schema.sql
            match = re.match(r"V(\d+)__([^\.]+)\.sql", filename)

        if not match:
            # Cannot determine migration ID and name
            return None

        timestamp = match.group(1)
        name_part = (
            match.group(2).replace("_", " ").title() if match.group(2) else "Migration"
        )

        # Create migration ID
        migration_id = f"{timestamp}_{name_part.lower().replace(' ', '_')}"

        # Read SQL content
        with open(file_path, "r") as f:
            content = f.read()

        # Split into up and down sections if marked
        up_sql = content
        down_sql = None

        if "-- DOWN" in content:
            parts = content.split("-- DOWN", 1)
            up_sql = parts[0].strip()
            down_sql = parts[1].strip()
        elif "-- === DOWN MIGRATION ===" in content:
            parts = content.split("-- === DOWN MIGRATION ===", 1)
            up_sql = parts[0].strip()
            down_sql = parts[1].strip()

        # Create migration base
        base = create_migration(
            name=name_part,
            description=f"SQL migration from file: {filename}",
            id=migration_id,
        )

        # Create SQL migration
        return SqlMigration(base, up_sql, down_sql)

    async def _load_python_migration(self, file_path: str) -> Optional[Migration]:
        """
        Load a Python migration from a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Migration object or None if loading fails
        """
        # Extract migration ID and name from filename
        filename = os.path.basename(file_path)
        match = re.match(r"(\d+)(?:_([^\.]+))?\.py", filename)

        if not match:
            # Cannot determine migration ID and name
            return None

        timestamp = match.group(1)
        name_part = (
            match.group(2).replace("_", " ").title() if match.group(2) else "Migration"
        )

        # Create migration ID
        migration_id = f"{timestamp}_{formatted_name}"

        # Format name for ID
        formatted_name = name_part.lower().replace(" ", "_")

        # Remove special characters
        for char in r'!@#$%^&*()+={}[]:;"\',.<>?/\\|':
            formatted_name = formatted_name.replace(char, "_")

        migration_id = f"{timestamp}_{formatted_name}"

        # Load the Python module
        module_name = os.path.splitext(filename)[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check for migration class
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Migration)
                and obj is not Migration
                and obj is not SqlMigration
                and obj is not PythonMigration
            ):
                # Found a migration class
                return obj()

        # Check for up/down functions
        up_func = getattr(module, "up", None) or getattr(module, "upgrade", None)
        down_func = getattr(module, "down", None) or getattr(module, "downgrade", None)

        if up_func:
            # Create migration base
            base = create_migration(
                name=name_part,
                description=f"Python migration from file: {filename}",
                id=migration_id,
            )

            # Get source code for checksum
            source_code = inspect.getsource(module)

            # Create Python migration
            return PythonMigration(base, up_func, down_func, source_code)

        return None


class DirectoryMigrationProvider(MigrationProvider):
    """
    Provider for loading migrations from directories.

    This provider loads migrations from SQL and Python files in specified directories.
    """

    def __init__(
        self, directories: list[str], sql_glob: str = "*.sql", python_glob: str = "*.py"
    ):
        """
        Initialize the directory migration provider.

        Args:
            directories: List of directory paths to load migrations from
            sql_glob: Glob pattern for SQL files (default: "*.sql")
            python_glob: Glob pattern for Python files (default: "*.py")
        """
        self.directories = directories
        self.sql_glob = sql_glob
        self.python_glob = python_glob

    async def load_migrations(self) -> list[Migration]:
        """
        Load migrations from the specified directories.

        Returns:
            List of Migration objects
        """
        migrations = []

        for directory in self.directories:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                continue

            # Load SQL migrations
            sql_files = glob.glob(os.path.join(directory, self.sql_glob))
            sql_provider = FileMigrationProvider(sql_files)
            sql_migrations = await sql_provider.load_migrations()
            migrations.extend(sql_migrations)

            # Load Python migrations
            python_files = glob.glob(os.path.join(directory, self.python_glob))
            python_provider = FileMigrationProvider(python_files)
            python_migrations = await python_provider.load_migrations()
            migrations.extend(python_migrations)

        return migrations


class ModuleMigrationProvider(MigrationProvider):
    """
    Provider for loading migrations from Python modules.

    This provider loads migrations from Python modules by importing them and
    looking for Migration subclasses or migration functions.
    """

    def __init__(self, module_names: list[str]):
        """
        Initialize the module migration provider.

        Args:
            module_names: List of module names to load migrations from
        """
        self.module_names = module_names

    async def load_migrations(self) -> list[Migration]:
        """
        Load migrations from the specified modules.

        Returns:
            List of Migration objects
        """
        migrations = []

        for module_name in self.module_names:
            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Look for migration classes
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, Migration)
                        and obj is not Migration
                        and obj is not SqlMigration
                        and obj is not PythonMigration
                        and obj.__module__
                        == module_name  # Only include classes defined in this module
                    ):
                        # Found a migration class
                        migrations.append(obj())

                # Look for migration functions
                for name, obj in inspect.getmembers(module):
                    if (
                        name.startswith("migration_")
                        and inspect.isfunction(obj)
                        and obj.__module__
                        == module_name  # Only include functions defined in this module
                    ):
                        # Get migration info
                        migration_id = name[10:]  # Remove 'migration_' prefix
                        name_part = migration_id.replace("_", " ").title()

                        # Create migration base
                        base = create_migration(
                            name=name_part,
                            description=f"Python migration from module: {module_name}.{name}",
                            id=migration_id,
                        )

                        # Get up and down functions
                        up_func = obj
                        down_func = getattr(module, f"revert_{migration_id}", None)

                        # Get source code for checksum
                        source_code = inspect.getsource(obj)
                        if down_func:
                            source_code += inspect.getsource(down_func)

                        # Create Python migration
                        migrations.append(
                            PythonMigration(base, up_func, down_func, source_code)
                        )

            except ImportError:
                # Skip modules that can't be imported
                continue

        return migrations


class MigrationServiceProvider:
    """
    Provider for migration-related services in dependency injection system.

    This provider integrates the migration system with the dependency injection system.
    """

    def __init__(
        self, migration_dirs: list[str] = None, migration_modules: list[str] = None
    ):
        """
        Initialize the migration service provider.

        Args:
            migration_dirs: List of directories containing migrations
            migration_modules: List of modules containing migrations
        """
        self.migration_dirs = migration_dirs or []
        self.migration_modules = migration_modules or []

    async def get_migration_providers(self) -> list[MigrationProvider]:
        """
        Get migration providers based on configuration.

        Returns:
            List of migration providers
        """
        providers = []

        # Add directory provider if directories are specified
        if self.migration_dirs:
            providers.append(DirectoryMigrationProvider(self.migration_dirs))

        # Add module provider if modules are specified
        if self.migration_modules:
            providers.append(ModuleMigrationProvider(self.migration_modules))

        return providers

    async def get_migrations(self) -> list[Migration]:
        """
        Get all migrations from all providers.

        Returns:
            List of migrations
        """
        migrations = []

        # Get providers
        providers = await self.get_migration_providers()

        # Load migrations from all providers
        for provider in providers:
            provider_migrations = await provider.load_migrations()
            migrations.extend(provider_migrations)

        return migrations

    async def register_providers(self) -> None:
        """Register migration providers with the global registry."""
        from uno.core.migrations.providers import register_provider

        providers = await self.get_migration_providers()

        # Register directory provider
        if self.migration_dirs:
            register_provider(
                "directory", DirectoryMigrationProvider(self.migration_dirs)
            )

        # Register module provider
        if self.migration_modules:
            register_provider("module", ModuleMigrationProvider(self.migration_modules))


# Registry of migration providers
_providers: dict[str, MigrationProvider] = {}


def register_provider(name: str, provider: MigrationProvider) -> None:
    """
    Register a migration provider.

    Args:
        name: Name of the provider
        provider: Provider instance
    """
    _providers[name] = provider


def get_providers() -> dict[str, MigrationProvider]:
    """
    Get all registered migration providers.

    Returns:
        Dictionary of provider name to provider instance
    """
    return _providers.copy()


async def discover_migrations() -> list[Migration]:
    """
    Discover migrations from all registered providers.

    Returns:
        List of discovered Migration objects
    """
    migrations = []

    for provider in _providers.values():
        provider_migrations = await provider.load_migrations()
        migrations.extend(provider_migrations)

    return migrations
