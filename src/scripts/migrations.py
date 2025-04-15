#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
"""
Uno database migration script that provides a CLI for managing migrations.

This script supports two migration systems:
1. Alembic: Traditional schema-migration tool (legacy support)
2. Uno Core Migrations: New lightweight, flexible migration system

Alembic Commands:
    alembic:init: Initialize the Alembic migration environment
    alembic:generate <message>: Generate a new Alembic migration
    alembic:upgrade [revision]: Upgrade the database to the latest or specified revision
    alembic:downgrade [revision]: Downgrade the database to the specified revision
    alembic:history: Show Alembic migration history
    alembic:current: Show current Alembic migration version
    alembic:revision: Show available Alembic revisions

Uno Migration Commands:
    create <name> [--type=sql|python]: Create a new migration file
    migrate [--target=ID] [--steps=N]: Apply pending migrations
    rollback [--target=ID] [--steps=N] [--all]: Revert applied migrations
    status: Show migration status
    info [migration_id]: Show detailed information about migrations
    check [--repair]: Check migrations for consistency issues
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path

from uno.settings import uno_settings
from uno.database.config import ConnectionConfig
from alembic.config import Config
from alembic import command

# Initialize a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_alembic_config() -> Config:
    """Get the Alembic configuration.

    Returns:
        Config: Alembic configuration object
    """
    # Get the migration script directory
    migrations_dir = Path(__file__).parent.parent / "uno" / "migrations"

    # Debug output to help troubleshoot path issues
    print(f"Migrations directory: {migrations_dir}")
    if not migrations_dir.exists():
        print(f"ERROR: Migrations directory does not exist: {migrations_dir}")
        # Try to find the correct path by checking parent directories
        parent_dir = Path(__file__).parent
        for _ in range(5):  # Search up to 5 levels up
            print(f"Looking in: {parent_dir}")
            possible_path = list(parent_dir.glob("**/migrations"))
            if possible_path:
                print(f"Found possible migrations directories: {possible_path}")
                if len(possible_path) > 0:
                    migrations_dir = possible_path[0]
                    print(f"Using found migrations directory: {migrations_dir}")
                    break
            parent_dir = parent_dir.parent

        # Create migrations dir if it doesn't exist
        if not migrations_dir.exists():
            print(f"Creating migrations directory: {migrations_dir}")
            migrations_dir.mkdir(parents=True, exist_ok=True)
            (migrations_dir / "versions").mkdir(exist_ok=True)

    # Create Alembic config
    alembic_ini = migrations_dir / "alembic.ini"
    print(f"Alembic config path: {alembic_ini}")

    # Create config and ensure proper connection details
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(migrations_dir))

    # Override SQLAlchemy URL if needed
    from uno.settings import uno_settings
    from uno.database.config import ConnectionConfig

    # Use login role (not admin) since login role has connect permission
    conn_config = ConnectionConfig(
        db_role=f"{uno_settings.DB_NAME}_login",  # Login role
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_SYNC_DRIVER,
        db_schema=uno_settings.DB_SCHEMA,
    )

    # Don't set the URL in the config file since it can have escaping issues
    # Instead, we'll use it directly in the environment.py file
    # Just return the config as is

    return config


def init_migrations() -> None:
    """Initialize migration environment after database creation."""
    logger.info("Initializing migration environment")

    try:
        # Get migration directory and verify it exists
        migrations_dir = Path(__file__).parent.parent / "uno" / "migrations"
        if not migrations_dir.exists():
            logger.error(f"Migration directory not found: {migrations_dir}")
            # Try to find it in a different location
            project_root = Path(__file__).parent.parent.parent
            migrations_dir = project_root / "src" / "uno" / "migrations"
            logger.info(f"Trying alternate path: {migrations_dir}")

            if not migrations_dir.exists():
                logger.error(
                    f"Alternative migration directory also not found: {migrations_dir}"
                )
                # Create the directory as a last resort
                logger.info("Creating migrations directory structure")
                migrations_dir.mkdir(parents=True, exist_ok=True)
                (migrations_dir / "versions").mkdir(exist_ok=True)

                # Create basic alembic config files
                create_initial_migration_files(migrations_dir)

        # Get Alembic config
        config = get_alembic_config()

        # Stamp with 'base' to initialize without running migrations
        command.stamp(config, "base")
        logger.info("Migration environment initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize migration environment: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def create_initial_migration_files(migrations_dir: Path) -> None:
    """Create initial migration files if they don't exist.

    Args:
        migrations_dir: Path to the migrations directory
    """
    # Create alembic.ini
    with open(migrations_dir / "alembic.ini", "w") as f:
        f.write(
            """# Generic single-database configuration for Uno

[alembic]
# path to migration scripts
script_location = %(here)s

# template used to generate migration files
file_template = %%(year)d%%(month).2d%%(day).2d%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# timezone to use when rendering the date within the migration file
# and when checking if migration is applied
timezone = UTC

# max length of characters to apply to the
# "slug" field
truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
revision_environment = false

# version location specification
version_locations = %(here)s/versions

# version path separator
version_path_separator = os

# output encoding used when revision files are written
output_encoding = utf-8

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        )

    # Create script.py.mako
    with open(migrations_dir / "script.py.mako", "w") as f:
        f.write(
            '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Optional
from alembic import op
import sqlalchemy as sa
import uno.database.engine  # noqa: F401
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema to this revision."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade database schema from this revision."""
    ${downgrades if downgrades else "pass"}'''
        )

    # Create env.py
    with open(migrations_dir / "env.py", "w") as f:
        f.write(
            '''"""Alembic environment script for Uno database migrations."""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import Uno configuration and model base
from uno.settings import uno_settings
from uno.model import UnoModel
from uno.database.config import ConnectionConfig
from uno.database.engine import sync_connection, SyncEngineFactory
import uno.attributes.models  # noqa: F401
import uno.authorization.models  # noqa: F401
import uno.meta.models  # noqa: F401
import uno.messaging.models  # noqa: F401
import uno.queries.models  # noqa: F401
import uno.reports.models  # noqa: F401
import uno.values.models  # noqa: F401
import uno.workflows.models  # noqa: F401

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add model's MetaData object for 'autogenerate' support
target_metadata = UnoModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Build connection URL from Uno settings
    conn_config = ConnectionConfig(
        db_role=f"{uno_settings.DB_NAME}_admin",
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_SYNC_DRIVER,
        db_schema=uno_settings.DB_SCHEMA,
    )
    
    # Create the connection URL
    url = conn_config.get_uri()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=uno_settings.DB_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Build connection configuration
    conn_config = ConnectionConfig(
        db_role=f"{uno_settings.DB_NAME}_admin",
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_SYNC_DRIVER,
        db_schema=uno_settings.DB_SCHEMA,
    )
    
    # Create engine factory
    engine_factory = SyncEngineFactory()
    
    # Create engine
    engine = engine_factory.create_engine(conn_config)
    
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=uno_settings.DB_SCHEMA,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()'''
        )


def generate_migration(message: str) -> None:
    """Generate a new migration script.

    Args:
        message: Migration message/description
    """
    logger.info(f"Generating migration: {message}")

    # Get Alembic config
    config = get_alembic_config()

    try:
        # Generate migration with autogenerate
        command.revision(config, message=message, autogenerate=True)
        logger.info("Migration generated successfully")
    except Exception as e:
        logger.error(f"Failed to generate migration: {e}")
        sys.exit(1)


def upgrade_database(revision: str = "head") -> None:
    """Upgrade database to the specified revision.

    Args:
        revision: Target revision (default: 'head' for latest)
    """
    logger.info(f"Upgrading database to revision: {revision}")

    # Get Alembic config
    config = get_alembic_config()

    try:
        # Upgrade to specified revision
        command.upgrade(config, revision)
        logger.info("Database upgraded successfully")
    except Exception as e:
        logger.error(f"Failed to upgrade database: {e}")
        sys.exit(1)


def downgrade_database(revision: str) -> None:
    """Downgrade database to the specified revision.

    Args:
        revision: Target revision
    """
    if not revision:
        logger.error("Downgrade requires a revision identifier")
        sys.exit(1)

    logger.info(f"Downgrading database to revision: {revision}")

    # Get Alembic config
    config = get_alembic_config()

    try:
        # Downgrade to specified revision
        command.downgrade(config, revision)
        logger.info("Database downgraded successfully")
    except Exception as e:
        logger.error(f"Failed to downgrade database: {e}")
        sys.exit(1)


def show_history() -> None:
    """Show migration history."""
    logger.info("Showing migration history")

    # Get Alembic config
    config = get_alembic_config()

    try:
        # Show history
        command.history(config)
    except Exception as e:
        logger.error(f"Failed to show migration history: {e}")
        sys.exit(1)


def show_current() -> None:
    """Show current migration version."""
    logger.info("Showing current migration version")

    # Get Alembic config
    config = get_alembic_config()

    try:
        # Show current version
        command.current(config, verbose=True)
    except Exception as e:
        logger.error(f"Failed to show current version: {e}")
        sys.exit(1)


def show_revisions() -> None:
    """Show available revisions."""
    # Get Alembic config
    config = get_alembic_config()
    migrations_dir = Path(config.get_main_option("script_location"))
    versions_dir = migrations_dir / "versions"

    # Get all revision files
    revision_files = sorted(list(versions_dir.glob("*.py")))

    if not revision_files:
        print("No revisions found")
        return

    print("Available revisions:")
    for file in revision_files:
        # Extract revision info
        with open(file, "r") as f:
            content = f.read()
            revision_line = [
                line for line in content.split("\n") if line.startswith("revision = ")
            ][0]
            revision_id = revision_line.split("=")[1].strip().strip("'\"")

            # Get the revision message (first docstring line)
            docstring_start = content.find('"""')
            if docstring_start >= 0:
                docstring_end = content.find('"""', docstring_start + 3)
                if docstring_end >= 0:
                    message = (
                        content[docstring_start + 3 : docstring_end]
                        .split("\n")[0]
                        .strip()
                    )
                    print(f"  {revision_id}: {message}")
            else:
                print(f"  {revision_id}: {file.stem}")


def get_database_url() -> str:
    """
    Get the database URL from settings.

    Returns:
        Database URL string
    """
    # Use connection config to build URL
    conn_config = ConnectionConfig(
        db_role=f"{uno_settings.DB_NAME}_login",  # Login role
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_SYNC_DRIVER,
        db_schema=uno_settings.DB_SCHEMA,
    )

    return conn_config.get_uri()


def get_default_migration_dirs() -> list:
    """
    Get the default migration directories.

    Returns:
        List of migration directory paths
    """
    # Default directories for migrations
    migrations_dir = os.path.join(os.getcwd(), "migrations")

    # Create directory if it doesn't exist
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir, exist_ok=True)

    return [migrations_dir]


# Import Uno Core Migration system
try:
    from uno.core.migrations.cli import main as core_migrations_main
except ImportError:
    logger.warning(
        "Uno Core Migration system not available. "
        "Only Alembic migrations will be available."
    )
    core_migrations_main = None


def run_core_migrations(args_list: list) -> int:
    """
    Run Uno Core Migration system commands.

    Args:
        args_list: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if core_migrations_main is None:
        logger.error("Uno Core Migration system is not available.")
        return 1

    try:
        return core_migrations_main(args_list)
    except Exception as e:
        logger.error(f"Error running core migrations: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Uno database migration tool")
    subparsers = parser.add_subparsers(dest="command", help="Migration command")

    # =====================================================
    # Alembic Migration Commands
    # =====================================================

    # Alembic Init command
    init_parser = subparsers.add_parser(
        "alembic:init", help="Initialize Alembic migration environment"
    )

    # Alembic Generate command
    generate_parser = subparsers.add_parser(
        "alembic:generate", help="Generate a new Alembic migration"
    )
    generate_parser.add_argument("message", help="Migration message/description")

    # Alembic Upgrade command
    upgrade_parser = subparsers.add_parser(
        "alembic:upgrade", help="Upgrade database using Alembic"
    )
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Target revision (default: 'head' for latest)",
    )

    # Alembic Downgrade command
    downgrade_parser = subparsers.add_parser(
        "alembic:downgrade", help="Downgrade database using Alembic"
    )
    downgrade_parser.add_argument("revision", help="Target revision")

    # Alembic History command
    history_parser = subparsers.add_parser(
        "alembic:history", help="Show Alembic migration history"
    )

    # Alembic Current command
    current_parser = subparsers.add_parser(
        "alembic:current", help="Show current Alembic migration version"
    )

    # Alembic Revisions command
    revisions_parser = subparsers.add_parser(
        "alembic:revisions", help="Show available Alembic revisions"
    )

    # =====================================================
    # Uno Core Migration Commands
    # =====================================================

    if core_migrations_main is not None:
        # Create command
        create_parser = subparsers.add_parser(
            "create", help="Create a new migration file"
        )
        create_parser.add_argument("name", help="Name of the migration")
        create_parser.add_argument(
            "--type",
            choices=["sql", "python"],
            default="sql",
            help="Type of migration to create (default: sql)",
        )
        create_parser.add_argument(
            "--directory", "-d", help="Directory to create the migration in"
        )
        create_parser.add_argument(
            "--template", "-t", help="Template file to use for the migration"
        )
        create_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

        # Migrate command
        migrate_parser = subparsers.add_parser(
            "migrate", help="Apply pending migrations"
        )
        migrate_parser.add_argument("--database-url", help="Database connection URL")
        migrate_parser.add_argument(
            "--schema",
            default=uno_settings.DB_SCHEMA,
            help=f"Database schema name (default: {uno_settings.DB_SCHEMA})",
        )
        migrate_parser.add_argument(
            "--table",
            default="uno_migrations",
            help="Migration tracking table name (default: uno_migrations)",
        )
        migrate_parser.add_argument(
            "--directory",
            "-d",
            action="append",
            dest="directories",
            default=[],
            help="Directory containing migration files",
        )
        migrate_parser.add_argument(
            "--module",
            "-m",
            action="append",
            dest="modules",
            default=[],
            help="Python module containing migrations",
        )
        migrate_parser.add_argument(
            "--target", help="Target migration ID to migrate to"
        )
        migrate_parser.add_argument(
            "--steps",
            type=int,
            default=0,
            help="Number of migrations to apply (0 for all)",
        )
        migrate_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

        # Rollback command
        rollback_parser = subparsers.add_parser(
            "rollback", help="Revert applied migrations"
        )
        rollback_parser.add_argument("--database-url", help="Database connection URL")
        rollback_parser.add_argument(
            "--schema",
            default=uno_settings.DB_SCHEMA,
            help=f"Database schema name (default: {uno_settings.DB_SCHEMA})",
        )
        rollback_parser.add_argument(
            "--table",
            default="uno_migrations",
            help="Migration tracking table name (default: uno_migrations)",
        )
        rollback_parser.add_argument(
            "--directory",
            "-d",
            action="append",
            dest="directories",
            default=[],
            help="Directory containing migration files",
        )
        rollback_parser.add_argument(
            "--module",
            "-m",
            action="append",
            dest="modules",
            default=[],
            help="Python module containing migrations",
        )
        rollback_parser.add_argument(
            "--target", help="Target migration ID to rollback to"
        )
        rollback_parser.add_argument(
            "--steps",
            type=int,
            default=1,
            help="Number of migrations to revert (default: 1)",
        )
        rollback_parser.add_argument(
            "--all", action="store_true", help="Revert all applied migrations"
        )
        rollback_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

        # Status command
        status_parser = subparsers.add_parser("status", help="Show migration status")
        status_parser.add_argument("--database-url", help="Database connection URL")
        status_parser.add_argument(
            "--schema",
            default=uno_settings.DB_SCHEMA,
            help=f"Database schema name (default: {uno_settings.DB_SCHEMA})",
        )
        status_parser.add_argument(
            "--table",
            default="uno_migrations",
            help="Migration tracking table name (default: uno_migrations)",
        )
        status_parser.add_argument(
            "--directory",
            "-d",
            action="append",
            dest="directories",
            default=[],
            help="Directory containing migration files",
        )
        status_parser.add_argument(
            "--module",
            "-m",
            action="append",
            dest="modules",
            default=[],
            help="Python module containing migrations",
        )
        status_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

        # Info command
        info_parser = subparsers.add_parser(
            "info", help="Show detailed information about migrations"
        )
        info_parser.add_argument(
            "migration_id",
            nargs="?",
            help="Optional migration ID to show information for",
        )
        info_parser.add_argument("--database-url", help="Database connection URL")
        info_parser.add_argument(
            "--schema",
            default=uno_settings.DB_SCHEMA,
            help=f"Database schema name (default: {uno_settings.DB_SCHEMA})",
        )
        info_parser.add_argument(
            "--table",
            default="uno_migrations",
            help="Migration tracking table name (default: uno_migrations)",
        )
        info_parser.add_argument(
            "--directory",
            "-d",
            action="append",
            dest="directories",
            default=[],
            help="Directory containing migration files",
        )
        info_parser.add_argument(
            "--module",
            "-m",
            action="append",
            dest="modules",
            default=[],
            help="Python module containing migrations",
        )
        info_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

        # Check command
        check_parser = subparsers.add_parser(
            "check", help="Check migrations for consistency issues"
        )
        check_parser.add_argument("--database-url", help="Database connection URL")
        check_parser.add_argument(
            "--schema",
            default=uno_settings.DB_SCHEMA,
            help=f"Database schema name (default: {uno_settings.DB_SCHEMA})",
        )
        check_parser.add_argument(
            "--table",
            default="uno_migrations",
            help="Migration tracking table name (default: uno_migrations)",
        )
        check_parser.add_argument(
            "--directory",
            "-d",
            action="append",
            dest="directories",
            default=[],
            help="Directory containing migration files",
        )
        check_parser.add_argument(
            "--module",
            "-m",
            action="append",
            dest="modules",
            default=[],
            help="Python module containing migrations",
        )
        check_parser.add_argument(
            "--repair",
            action="store_true",
            help="Attempt to repair issues automatically",
        )
        check_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "alembic:init":
        init_migrations()
    elif args.command == "alembic:generate":
        generate_migration(args.message)
    elif args.command == "alembic:upgrade":
        upgrade_database(args.revision)
    elif args.command == "alembic:downgrade":
        downgrade_database(args.revision)
    elif args.command == "alembic:history":
        show_history()
    elif args.command == "alembic:current":
        show_current()
    elif args.command == "alembic:revisions":
        show_revisions()
    elif core_migrations_main is not None and args.command in [
        "create",
        "migrate",
        "rollback",
        "status",
        "info",
        "check",
    ]:
        # Handle core migration commands

        # Initialize additional parameters if needed
        if args.command in ["migrate", "rollback", "status", "info", "check"]:
            # Set database URL if not provided
            if not getattr(args, "database_url", None):
                args.database_url = get_database_url()

            # Add default directories if none provided
            if not args.directories:
                args.directories = get_default_migration_dirs()

        # Convert namespace to args list
        args_dict = vars(args)
        args_list = [args.command]

        # Add all other arguments
        for key, value in args_dict.items():
            if key != "command" and value is not None:
                if isinstance(value, bool) and value:
                    args_list.append(f"--{key}")
                elif isinstance(value, list):
                    for item in value:
                        args_list.append(f"--{key}")
                        args_list.append(str(item))
                elif not isinstance(value, bool) or value:
                    args_list.append(f"--{key}")
                    args_list.append(str(value))

        # Run core migrations and exit with its return code
        sys.exit(run_core_migrations(args_list))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
