"""
Command-line interface for managing migrations.

This module provides a command-line tool for managing database migrations,
including creating, applying, and reverting migrations.
"""

import os
import sys
import time
import logging
import argparse
import asyncio
import datetime
from typing import Optional, List, Dict, Any

from uno.core.migrations.migrator import (
    migrate, MigrationConfig, MigrationDirection, migration_registry
)
from uno.core.migrations.migration import create_migration, SqlMigration, MigrationBase
from uno.core.migrations.providers import (
    register_provider, DirectoryMigrationProvider, ModuleMigrationProvider, discover_migrations
)
from uno.core.migrations.tracker import (
    set_migration_tracker, DatabaseMigrationTracker, FileMigrationTracker
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uno.migrations.cli")


def setup_common_args(parser: argparse.ArgumentParser) -> None:
    """
    Add common arguments to the parser.
    
    Args:
        parser: ArgumentParser to add arguments to
    """
    parser.add_argument(
        "--database-url",
        help="Database connection URL"
    )
    
    parser.add_argument(
        "--schema",
        default="public",
        help="Database schema name (default: public)"
    )
    
    parser.add_argument(
        "--table",
        default="uno_migrations",
        help="Migration tracking table name (default: uno_migrations)"
    )
    
    parser.add_argument(
        "--directory",
        "-d",
        action="append",
        dest="directories",
        default=[],
        help="Directory containing migration files (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--module",
        "-m",
        action="append",
        dest="modules",
        default=[],
        help="Python module containing migrations (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    
    Returns:
        ArgumentParser object
    """
    parser = argparse.ArgumentParser(
        description="Manage database migrations"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Apply pending migrations")
    setup_common_args(migrate_parser)
    migrate_parser.add_argument(
        "--target",
        help="Target migration ID to migrate to"
    )
    migrate_parser.add_argument(
        "--steps",
        type=int,
        default=0,
        help="Number of migrations to apply (0 for all)"
    )
    migrate_parser.add_argument(
        "--fake",
        action="store_true",
        help="Mark migrations as applied without running them"
    )
    
    # rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Revert applied migrations")
    setup_common_args(rollback_parser)
    rollback_parser.add_argument(
        "--target",
        help="Target migration ID to rollback to"
    )
    rollback_parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of migrations to revert (default: 1)"
    )
    rollback_parser.add_argument(
        "--all",
        action="store_true",
        help="Revert all applied migrations"
    )
    rollback_parser.add_argument(
        "--fake",
        action="store_true",
        help="Mark migrations as reverted without running them"
    )
    
    # create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument(
        "name",
        help="Name of the migration"
    )
    create_parser.add_argument(
        "--type",
        choices=["sql", "python"],
        default="sql",
        help="Type of migration to create (default: sql)"
    )
    create_parser.add_argument(
        "--directory",
        "-d",
        required=True,
        help="Directory to create the migration in"
    )
    create_parser.add_argument(
        "--template",
        "-t",
        help="Template file to use for the migration"
    )
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    setup_common_args(status_parser)
    
    # info command
    info_parser = subparsers.add_parser("info", help="Show detailed information about migrations")
    setup_common_args(info_parser)
    info_parser.add_argument(
        "migration_id",
        nargs="?",
        help="Optional migration ID to show information for"
    )
    
    return parser


async def get_database_connection(database_url: str) -> Any:
    """
    Get a database connection based on the URL.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Database connection object
    """
    # This is a simplified example that supports PostgreSQL via asyncpg
    # In a real implementation, you would handle more database types and connection options
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        import asyncpg
        return await asyncpg.connect(database_url)
    else:
        raise ValueError(f"Unsupported database URL: {database_url}")


async def create_migration_file(args: argparse.Namespace) -> None:
    """
    Create a new migration file.
    
    Args:
        args: Command-line arguments
    """
    # Create the directory if it doesn't exist
    os.makedirs(args.directory, exist_ok=True)
    
    # Generate timestamp
    timestamp = int(time.time())
    
    # Create migration name
    name = args.name.replace(" ", "_").lower()
    
    if args.type == "sql":
        # Create SQL migration file
        filename = f"{timestamp}_{name}.sql"
        filepath = os.path.join(args.directory, filename)
        
        # Generate SQL content
        if args.template and os.path.exists(args.template):
            with open(args.template, 'r') as f:
                content = f.read()
        else:
            content = """-- Migration: {name}
-- Created at: {created_at}

-- Write your UP SQL here

-- DOWN

-- Write your DOWN SQL here
""".format(
    name=args.name,
    created_at=datetime.datetime.now().isoformat()
)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        logger.info(f"Created SQL migration: {filepath}")
    
    elif args.type == "python":
        # Create Python migration file
        filename = f"{timestamp}_{name}.py"
        filepath = os.path.join(args.directory, filename)
        
        # Generate Python content
        if args.template and os.path.exists(args.template):
            with open(args.template, 'r') as f:
                content = f.read()
        else:
            content = """# Migration: {name}
# Created at: {created_at}

from typing import Any
from uno.core.migrations.migration import Migration, MigrationBase, create_migration


# Function-based migration
async def up(context: Any) -> None:
    """Apply the migration."""
    # Write your UP migration code here
    # Example:
    # await context.execute_sql('''
    #     CREATE TABLE example (
    #         id SERIAL PRIMARY KEY,
    #         name VARCHAR(255) NOT NULL
    #     )
    # ''')
    pass


async def down(context: Any) -> None:
    """Revert the migration."""
    # Write your DOWN migration code here
    # Example:
    # await context.execute_sql('DROP TABLE example')
    pass


# Alternatively, you can define a class-based migration:
# class {class_name}(Migration):
#     def __init__(self):
#         base = create_migration(
#             name="{name}",
#             description="Migration created on {created_at}"
#         )
#         super().__init__(base)
#     
#     async def apply(self, context: Any) -> None:
#         # Write your UP migration code here
#         pass
#     
#     async def revert(self, context: Any) -> None:
#         # Write your DOWN migration code here
#         pass
#     
#     def get_checksum(self) -> str:
#         # Return a checksum of the migration content
#         import hashlib
#         return hashlib.md5(b"{name}").hexdigest()
""".format(
    name=args.name,
    class_name=''.join(word.title() for word in args.name.split()),
    created_at=datetime.datetime.now().isoformat()
)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        logger.info(f"Created Python migration: {filepath}")


async def show_migration_status(args: argparse.Namespace) -> None:
    """
    Show the status of migrations.
    
    Args:
        args: Command-line arguments
    """
    # Connect to the database
    connection = await get_database_connection(args.database_url)
    
    try:
        # Create migration config
        config = MigrationConfig(
            schema_name=args.schema,
            migration_table=args.table,
            migration_paths=args.directories,
            migration_modules=args.modules,
            verbose=args.verbose
        )
        
        # Set up migration tracker
        tracker = DatabaseMigrationTracker(
            connection=connection,
            schema_name=args.schema,
            table_name=args.table
        )
        
        await tracker.initialize()
        set_migration_tracker(tracker)
        
        # Register migration providers
        if args.directories:
            register_provider("directory", DirectoryMigrationProvider(args.directories))
        
        if args.modules:
            register_provider("module", ModuleMigrationProvider(args.modules))
        
        # Discover migrations
        migrations = await discover_migrations()
        for migration in migrations:
            migration_registry[migration.id] = migration
        
        # Get applied migrations
        applied_migrations = await tracker.get_applied_migrations()
        
        # Print status
        print(f"Database schema: {args.schema}")
        print(f"Migration table: {args.table}")
        print(f"Discovered {len(migrations)} migrations, {len(applied_migrations)} applied")
        print()
        
        if not migrations:
            print("No migrations found")
            return
        
        # Print migration list
        print("Migrations:")
        print("-" * 80)
        print(f"{'ID':<40} {'Status':<10} {'Name':<30}")
        print("-" * 80)
        
        for migration in sorted(migrations, key=lambda m: m.id):
            status = "Applied" if migration.id in applied_migrations else "Pending"
            print(f"{migration.id:<40} {status:<10} {migration.name:<30}")
    
    finally:
        # Close the database connection
        await connection.close()


async def show_migration_info(args: argparse.Namespace) -> None:
    """
    Show detailed information about migrations.
    
    Args:
        args: Command-line arguments
    """
    # Connect to the database
    connection = await get_database_connection(args.database_url)
    
    try:
        # Create migration config
        config = MigrationConfig(
            schema_name=args.schema,
            migration_table=args.table,
            migration_paths=args.directories,
            migration_modules=args.modules,
            verbose=args.verbose
        )
        
        # Set up migration tracker
        tracker = DatabaseMigrationTracker(
            connection=connection,
            schema_name=args.schema,
            table_name=args.table
        )
        
        await tracker.initialize()
        set_migration_tracker(tracker)
        
        # Register migration providers
        if args.directories:
            register_provider("directory", DirectoryMigrationProvider(args.directories))
        
        if args.modules:
            register_provider("module", ModuleMigrationProvider(args.modules))
        
        # Discover migrations
        migrations = await discover_migrations()
        for migration in migrations:
            migration_registry[migration.id] = migration
        
        # Get applied migrations
        applied_migrations = await tracker.get_applied_migrations()
        
        # Get migration history
        history = await tracker.get_migration_history()
        
        # Create a mapping of migration ID to history record
        history_map = {record["id"]: record for record in history}
        
        if args.migration_id:
            # Show info for a specific migration
            for migration in migrations:
                if migration.id == args.migration_id:
                    print(f"Migration: {migration.id}")
                    print(f"Name: {migration.name}")
                    print(f"Description: {migration.description}")
                    print(f"Type: {migration.__class__.__name__}")
                    print(f"Status: {'Applied' if migration.id in applied_migrations else 'Pending'}")
                    
                    if migration.id in history_map:
                        record = history_map[migration.id]
                        print(f"Applied at: {record['applied_at']}")
                        print(f"Checksum: {record['checksum']}")
                    
                    if hasattr(migration, 'dependencies') and migration.dependencies:
                        print(f"Dependencies: {', '.join(migration.dependencies)}")
                    
                    if hasattr(migration, 'tags') and migration.tags:
                        print(f"Tags: {', '.join(migration.tags)}")
                    
                    # For SQL migrations, show content
                    if isinstance(migration, SqlMigration):
                        print("\nUP SQL:")
                        print("-" * 80)
                        print(migration.up_sql)
                        
                        if migration.down_sql:
                            print("\nDOWN SQL:")
                            print("-" * 80)
                            print(migration.down_sql)
                    
                    break
            else:
                print(f"Migration not found: {args.migration_id}")
        else:
            # Show summary info for all migrations
            print(f"Database schema: {args.schema}")
            print(f"Migration table: {args.table}")
            print(f"Discovered {len(migrations)} migrations, {len(applied_migrations)} applied")
            print()
            
            if not migrations:
                print("No migrations found")
                return
            
            # Print migration list with more details
            print("Migrations:")
            print("-" * 100)
            print(f"{'ID':<30} {'Status':<10} {'Applied At':<25} {'Name':<30}")
            print("-" * 100)
            
            for migration in sorted(migrations, key=lambda m: m.id):
                status = "Applied" if migration.id in applied_migrations else "Pending"
                applied_at = history_map.get(migration.id, {}).get("applied_at", "")
                print(f"{migration.id:<30} {status:<10} {applied_at:<25} {migration.name:<30}")
    
    finally:
        # Close the database connection
        await connection.close()


async def run_migrations(args: argparse.Namespace) -> None:
    """
    Run database migrations.
    
    Args:
        args: Command-line arguments
    """
    # Connect to the database
    connection = await get_database_connection(args.database_url)
    
    try:
        # Create migration config
        config = MigrationConfig(
            schema_name=args.schema,
            migration_table=args.table,
            migration_paths=args.directories,
            migration_modules=args.modules,
            verbose=args.verbose
        )
        
        # Register migration providers
        if args.directories:
            register_provider("directory", DirectoryMigrationProvider(args.directories))
        
        if args.modules:
            register_provider("module", ModuleMigrationProvider(args.modules))
        
        # Discover migrations
        migrations = await discover_migrations()
        for migration in migrations:
            migration_registry[migration.id] = migration
        
        # Run migrations
        if args.command == "migrate":
            # Apply migrations
            direction = MigrationDirection.UP
            count, applied = await migrate(
                connection=connection,
                config=config,
                direction=direction,
                target=args.target,
                steps=args.steps
            )
            
            if count > 0:
                logger.info(f"Applied {count} migrations")
                for migration in applied:
                    logger.info(f"  - {migration.id}: {migration.name}")
            else:
                logger.info("No migrations to apply")
        
        elif args.command == "rollback":
            # Revert migrations
            direction = MigrationDirection.DOWN
            steps = 0 if args.all else args.steps
            
            count, reverted = await migrate(
                connection=connection,
                config=config,
                direction=direction,
                target=args.target,
                steps=steps
            )
            
            if count > 0:
                logger.info(f"Reverted {count} migrations")
                for migration in reverted:
                    logger.info(f"  - {migration.id}: {migration.name}")
            else:
                logger.info("No migrations to revert")
    
    finally:
        # Close the database connection
        await connection.close()


async def _main(args: Optional[List[str]] = None) -> int:
    """
    Main function for the CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    try:
        if parsed_args.command == "create":
            await create_migration_file(parsed_args)
        elif parsed_args.command == "status":
            await show_migration_status(parsed_args)
        elif parsed_args.command == "info":
            await show_migration_info(parsed_args)
        elif parsed_args.command in ("migrate", "rollback"):
            await run_migrations(parsed_args)
        else:
            parser.print_help()
            return 1
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Entry point for the CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    return asyncio.run(_main(args))