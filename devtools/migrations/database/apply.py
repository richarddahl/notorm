"""Migration application utilities.

This module provides utilities for applying database migrations
with transaction safety and dry-run capabilities.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
import os
import logging
import importlib.util
import inspect
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.engine import Engine, Connection

logger = logging.getLogger(__name__)


class MigrationExecutor:
    """Executes migration scripts with transaction safety."""

    def __init__(self, engine: Engine, schema: str = "public", dry_run: bool = False):
        """Initialize the migration executor.

        Args:
            engine: SQLAlchemy engine for the database
            schema: Database schema name
            dry_run: Whether to run in dry run mode (no changes applied)
        """
        self.engine = engine
        self.schema = schema
        self.dry_run = dry_run
        self.conn = None
        self.transaction = None

    def __enter__(self):
        """Enter context manager, starting a transaction."""
        self.conn = self.engine.connect()
        self.transaction = self.conn.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, committing or rolling back the transaction."""
        if exc_type is not None or self.dry_run:
            logger.info("Rolling back migration due to error or dry run mode")
            self.transaction.rollback()
        else:
            logger.info("Committing migration")
            self.transaction.commit()

        self.conn.close()
        self.conn = None
        self.transaction = None

    def execute_sql(self, sql: str) -> None:
        """Execute SQL statements.

        Args:
            sql: SQL statements to execute
        """
        if self.dry_run:
            logger.info(f"Would execute SQL (dry run): {sql[:500]}...")
            return

        logger.debug(f"Executing SQL: {sql[:500]}...")

        # Split the SQL script into individual statements
        statements = []
        current_statement = []

        for line in sql.split("\n"):
            # Skip comments and empty lines
            if line.strip().startswith("--") or not line.strip():
                continue

            current_statement.append(line)

            # If the line ends with a semicolon, it's the end of a statement
            if line.strip().endswith(";"):
                statements.append("\n".join(current_statement))
                current_statement = []

        # Execute each statement
        for statement in statements:
            if statement.strip():
                self.conn.execute(sa.text(statement))

    def execute_python(
        self, script_path: Union[str, Path], context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Execute a Python migration script.

        Args:
            script_path: Path to the Python migration script
            context: Additional context to pass to the script
        """
        script_path = Path(script_path)

        if not script_path.exists():
            raise FileNotFoundError(f"Migration script not found: {script_path}")

        # Import the script as a module
        spec = importlib.util.spec_from_file_location(
            f"migration_{script_path.stem}", script_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check if the module has upgrade/downgrade functions
        if not hasattr(module, "upgrade"):
            raise ValueError(f"Migration script has no upgrade function: {script_path}")

        # Create a mock alembic op object that logs operations
        if self.dry_run:

            class MockOp:
                def __getattr__(self, name):
                    def method(*args, **kwargs):
                        logger.info(f"Would call op.{name}({args}, {kwargs}) (dry run)")

                    return method

            module.op = MockOp()
        else:
            # When not in dry run mode, run the normal upgrade function
            # This assumes that the script has imports like:
            # from alembic import op
            # This is a simplified implementation
            pass

        # Set up context
        context = context or {}
        context["connection"] = self.conn
        context["schema"] = self.schema

        # Execute the upgrade function
        if self.dry_run:
            logger.info(f"Would execute upgrade from {script_path} (dry run)")
            # In dry run mode, we still call the function but with the mock op
            module.upgrade()
        else:
            logger.info(f"Executing upgrade from {script_path}")
            module.upgrade()

    def apply_migration(
        self, script_path: Union[str, Path], context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Apply a migration script.

        Args:
            script_path: Path to the migration script
            context: Additional context to pass to the script
        """
        script_path = Path(script_path)

        if not script_path.exists():
            raise FileNotFoundError(f"Migration script not found: {script_path}")

        # Determine script type by extension
        if script_path.suffix == ".py":
            self.execute_python(script_path, context)
        elif script_path.suffix == ".sql":
            with open(script_path, "r") as f:
                sql = f.read()
            self.execute_sql(sql)
        else:
            raise ValueError(f"Unsupported migration script type: {script_path.suffix}")


def apply_migration(
    script_path: Union[str, Path],
    engine: Engine,
    schema: str = "public",
    dry_run: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Apply a migration script with transaction safety.

    Args:
        script_path: Path to the migration script
        engine: SQLAlchemy engine for the database
        schema: Database schema name
        dry_run: Whether to run in dry run mode (no changes applied)
        context: Additional context to pass to the script

    Returns:
        True if the migration was applied successfully, False otherwise
    """
    script_path = Path(script_path)

    if not script_path.exists():
        logger.error(f"Migration script not found: {script_path}")
        return False

    try:
        with MigrationExecutor(engine, schema, dry_run) as executor:
            executor.apply_migration(script_path, context)
        return True
    except Exception as e:
        logger.error(f"Error applying migration {script_path}: {e}")
        return False


def apply_migrations(
    scripts: list[Union[str, Path]],
    engine: Engine,
    schema: str = "public",
    dry_run: bool = False,
    context: Optional[Dict[str, Any]] = None,
    stop_on_error: bool = True,
) -> Dict[str, bool]:
    """Apply multiple migration scripts with transaction safety.

    Args:
        scripts: List of paths to migration scripts
        engine: SQLAlchemy engine for the database
        schema: Database schema name
        dry_run: Whether to run in dry run mode (no changes applied)
        context: Additional context to pass to the scripts
        stop_on_error: Whether to stop on the first error

    Returns:
        Dictionary mapping script paths to success/failure status
    """
    results = {}

    for script_path in scripts:
        script_path = Path(script_path)

        if not script_path.exists():
            logger.error(f"Migration script not found: {script_path}")
            results[str(script_path)] = False

            if stop_on_error:
                break

            continue

        try:
            with MigrationExecutor(engine, schema, dry_run) as executor:
                executor.apply_migration(script_path, context)
            results[str(script_path)] = True
        except Exception as e:
            logger.error(f"Error applying migration {script_path}: {e}")
            results[str(script_path)] = False

            if stop_on_error:
                break

    return results


def apply_migrations_directory(
    directory: Union[str, Path],
    engine: Engine,
    schema: str = "public",
    dry_run: bool = False,
    context: Optional[Dict[str, Any]] = None,
    stop_on_error: bool = True,
    file_pattern: str = "*.py",
    sort_key: Optional[Callable[[Path], Any]] = None,
) -> Dict[str, bool]:
    """Apply all migration scripts in a directory.

    Args:
        directory: Path to the directory containing migration scripts
        engine: SQLAlchemy engine for the database
        schema: Database schema name
        dry_run: Whether to run in dry run mode (no changes applied)
        context: Additional context to pass to the scripts
        stop_on_error: Whether to stop on the first error
        file_pattern: Pattern to match migration script files
        sort_key: Function to sort the migration scripts (default: alphabetical)

    Returns:
        Dictionary mapping script paths to success/failure status
    """
    directory = Path(directory)

    if not directory.exists() or not directory.is_dir():
        logger.error(f"Migration directory not found: {directory}")
        return {}

    # Find migration scripts in the directory
    scripts = list(directory.glob(file_pattern))

    # Sort scripts if sort_key is provided
    if sort_key:
        scripts.sort(key=sort_key)
    else:
        scripts.sort()

    return apply_migrations(scripts, engine, schema, dry_run, context, stop_on_error)
