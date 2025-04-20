"""CLI commands for database and codebase migrations.

This module provides CLI commands for working with migrations,
including diffing schemas, generating migrations, and applying migrations.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
from sqlalchemy import create_engine

from uno.devtools.migrations.database.diff import (
    diff_model_to_db,
    diff_db_to_db,
    SchemaDiff,
)
from uno.devtools.migrations.database.generate import (
    generate_migration_script,
    generate_migration_plan,
)
from uno.devtools.migrations.database.apply import (
    apply_migration,
    apply_migrations,
    apply_migrations_directory,
)
from uno.devtools.migrations.database.rollback import (
    rollback_migration,
    rollback_to_revision,
)
from uno.devtools.migrations.codebase.analyzer import analyze_python_files
from uno.devtools.migrations.codebase.transformer import apply_transformations
from uno.devtools.migrations.codebase.verifier import verify_transformations
from uno.devtools.migrations.utilities.backup import backup_before_migration
from uno.devtools.migrations.utilities.restoration import undo_migration

# Set up logger
logger = logging.getLogger(__name__)

# Create Typer app
migrations_app = typer.Typer(
    name="migrations",
    help="Tools for database migrations and codebase transformations",
    add_completion=False,
)

# Console for rich output
console = Console()

# Fallback to basic CLI if typer is not available
in_fallback_mode = False

try:
    from typing import Annotated
except ImportError:
    # For Python < 3.9
    from typing_extensions import Annotated


# Database migrations commands
@migrations_app.command("diff-schema")
def diff_schema_command(
    connection_string: Annotated[
        str, typer.Option("--connection", "-c", help="Database connection string")
    ],
    models_module: Annotated[
        str,
        typer.Option(
            "--models", "-m", help="Python module path containing SQLAlchemy models"
        ),
    ],
    schema: Annotated[
        str | None, typer.Option("--schema", "-s", help="Database schema to compare")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format (text or markdown)")
    ] = "text",
    output_file: Annotated[
        str | None, typer.Option("--output", "-o", help="Output file path")
    ] = None,
) -> None:
    """Compare SQLAlchemy models to database schema and show differences."""
    try:
        # Create engine
        engine = create_engine(connection_string)

        # Import models module
        module_path = models_module.split(".")
        module_name = module_path[-1]
        package_path = ".".join(module_path[:-1]) if len(module_path) > 1 else None

        try:
            if package_path:
                module = __import__(package_path, fromlist=[module_name])
                models_module = getattr(module, module_name)
            else:
                models_module = __import__(module_name)
        except ImportError:
            console.print(
                f"[bold red]Error:[/bold red] Could not import module {models_module}"
            )
            return

        # Get models from module
        models = []
        for name in dir(models_module):
            obj = getattr(models_module, name)
            if hasattr(obj, "__tablename__"):
                models.append(obj)

        if not models:
            console.print(
                f"[bold yellow]Warning:[/bold yellow] No models found in {models_module}"
            )
            return

        # Run the diff
        console.print(
            f"[bold]Comparing {len(models)} models to database schema...[/bold]"
        )
        diff = diff_model_to_db(models, engine, schema=schema)

        # Generate the report
        if diff.has_changes:
            if output_format == "markdown":
                report = generate_migration_plan(diff, format="markdown")
            else:
                report = diff.summary()

            # Print or save the report
            if output_file:
                with open(output_file, "w") as f:
                    f.write(report)
                console.print(
                    f"[bold green]Schema diff saved to {output_file}[/bold green]"
                )
            else:
                if output_format == "markdown":
                    syntax = Syntax(
                        report, "markdown", theme="monokai", line_numbers=False
                    )
                    console.print(syntax)
                else:
                    console.print(report)
        else:
            console.print("[bold green]No schema differences detected.[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


@migrations_app.command("generate-migration")
def generate_migration_command(
    connection_string: Annotated[
        str, typer.Option("--connection", "-c", help="Database connection string")
    ],
    models_module: Annotated[
        str,
        typer.Option(
            "--models", "-m", help="Python module path containing SQLAlchemy models"
        ),
    ],
    output_dir: Annotated[
        str, typer.Option("--output-dir", "-o", help="Directory for migration scripts")
    ],
    message: Annotated[
        str,
        typer.Option("--message", "-g", help="Migration message (short description)"),
    ],
    schema: Annotated[
        str | None, typer.Option("--schema", "-s", help="Database schema")
    ] = None,
    format: Annotated[
        str, typer.Option("--format", "-f", help="Migration format (python or sql)")
    ] = "python",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Show what would be generated without creating files"
        ),
    ] = False,
) -> None:
    """Generate a database migration script based on model/schema differences."""
    try:
        # Create engine
        engine = create_engine(connection_string)

        # Import models module
        module_path = models_module.split(".")
        module_name = module_path[-1]
        package_path = ".".join(module_path[:-1]) if len(module_path) > 1 else None

        try:
            if package_path:
                module = __import__(package_path, fromlist=[module_name])
                models_module = getattr(module, module_name)
            else:
                models_module = __import__(module_name)
        except ImportError:
            console.print(
                f"[bold red]Error:[/bold red] Could not import module {models_module}"
            )
            return

        # Get models from module
        models = []
        for name in dir(models_module):
            obj = getattr(models_module, name)
            if hasattr(obj, "__tablename__"):
                models.append(obj)

        if not models:
            console.print(
                f"[bold yellow]Warning:[/bold yellow] No models found in {models_module}"
            )
            return

        # Run the diff
        console.print(
            f"[bold]Comparing {len(models)} models to database schema...[/bold]"
        )
        diff = diff_model_to_db(models, engine, schema=schema)

        if not diff.has_changes:
            console.print(
                "[bold yellow]No schema differences detected. No migration needed.[/bold yellow]"
            )
            return

        # Generate migration plan first
        plan = generate_migration_plan(diff, format="text")
        console.print("[bold]Migration plan:[/bold]")
        console.print(plan)

        if not dry_run:
            # Generate the migration script
            output_dir = Path(output_dir)
            os.makedirs(output_dir, exist_ok=True)

            script_path = generate_migration_script(
                diff, output_dir, message, format=format, schema=schema
            )

            console.print(
                f"[bold green]Migration script generated: {script_path}[/bold green]"
            )

            # Show a preview of the script
            with open(script_path, "r") as f:
                content = f.read()

            syntax = Syntax(
                content,
                "python" if format == "python" else "sql",
                theme="monokai",
                line_numbers=True,
            )
            console.print(Panel(syntax, title=f"Migration Script: {script_path.name}"))

        else:
            console.print("[bold]Dry run, no files were created.[/bold]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


@migrations_app.command("apply-migration")
def apply_migration_command(
    script_path: Annotated[str, typer.Argument(help="Path to the migration script")],
    connection_string: Annotated[
        str, typer.Option("--connection", "-c", help="Database connection string")
    ],
    schema: Annotated[
        str | None, typer.Option("--schema", "-s", help="Database schema")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Run without applying changes")
    ] = False,
    backup: Annotated[
        bool, typer.Option("--backup", help="Create database backup before applying")
    ] = True,
    backup_dir: Annotated[
        str | None, typer.Option("--backup-dir", help="Directory for backups")
    ] = None,
) -> None:
    """Apply a database migration script."""
    try:
        script_path = Path(script_path)

        if not script_path.exists():
            console.print(
                f"[bold red]Error:[/bold red] Migration script not found: {script_path}"
            )
            return

        # Create engine
        engine = create_engine(connection_string)

        # Create backup if requested
        if backup and not dry_run:
            from uno.devtools.migrations.utilities.backup import backup_database

            backup_dir = backup_dir or "./backups"
            os.makedirs(backup_dir, exist_ok=True)

            db_name = connection_string.split("/")[-1]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = Path(backup_dir) / f"{db_name}_backup_{timestamp}"

            console.print(f"[bold]Creating database backup...[/bold]")
            backup_path = backup_database(connection_string, backup_file, compress=True)
            console.print(f"[bold green]Backup created: {backup_path}[/bold green]")

        # Apply the migration
        console.print(
            f"[bold]{'Would apply' if dry_run else 'Applying'} migration: {script_path}[/bold]"
        )

        result = apply_migration(script_path, engine, schema=schema, dry_run=dry_run)

        if result:
            console.print(
                f"[bold green]Migration {'would be' if dry_run else 'was'} successfully applied[/bold green]"
            )
        else:
            console.print(
                f"[bold red]Migration {'would fail' if dry_run else 'failed'}![/bold red]"
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


@migrations_app.command("rollback-migration")
def rollback_migration_command(
    script_path: Annotated[
        str, typer.Argument(help="Path to the migration script to roll back")
    ],
    connection_string: Annotated[
        str, typer.Option("--connection", "-c", help="Database connection string")
    ],
    schema: Annotated[
        str | None, typer.Option("--schema", "-s", help="Database schema")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Run without applying changes")
    ] = False,
    backup: Annotated[
        bool,
        typer.Option("--backup", help="Create database backup before rolling back"),
    ] = True,
    backup_dir: Annotated[
        str | None, typer.Option("--backup-dir", help="Directory for backups")
    ] = None,
) -> None:
    """Roll back a database migration."""
    try:
        script_path = Path(script_path)

        if not script_path.exists():
            console.print(
                f"[bold red]Error:[/bold red] Migration script not found: {script_path}"
            )
            return

        # Create engine
        engine = create_engine(connection_string)

        # Create backup if requested
        if backup and not dry_run:
            from uno.devtools.migrations.utilities.backup import backup_database

            backup_dir = backup_dir or "./backups"
            os.makedirs(backup_dir, exist_ok=True)

            db_name = connection_string.split("/")[-1]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = Path(backup_dir) / f"{db_name}_backup_{timestamp}"

            console.print(f"[bold]Creating database backup...[/bold]")
            backup_path = backup_database(connection_string, backup_file, compress=True)
            console.print(f"[bold green]Backup created: {backup_path}[/bold green]")

        # Roll back the migration
        console.print(
            f"[bold]{'Would roll back' if dry_run else 'Rolling back'} migration: {script_path}[/bold]"
        )

        result = rollback_migration(script_path, engine, schema=schema, dry_run=dry_run)

        if result:
            console.print(
                f"[bold green]Migration {'would be' if dry_run else 'was'} successfully rolled back[/bold green]"
            )
        else:
            console.print(
                f"[bold red]Rollback {'would fail' if dry_run else 'failed'}![/bold red]"
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


# Codebase migration commands
@migrations_app.command("analyze-code")
def analyze_code_command(
    directory: Annotated[
        str, typer.Argument(help="Directory containing Python code to analyze")
    ],
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (text, markdown, or json)"),
    ] = "text",
    output_file: Annotated[
        str | None, typer.Option("--output", "-o", help="Output file path")
    ] = None,
    patterns: Annotated[
        list[str] | None,
        typer.Option("--pattern", "-p", help="Patterns to check for"),
    ] = None,
) -> None:
    """Analyze Python code for migration needs."""
    try:
        directory_path = Path(directory)

        if not directory_path.exists() or not directory_path.is_dir():
            console.print(
                f"[bold red]Error:[/bold red] Directory not found: {directory}"
            )
            return

        # Run the analysis
        console.print(f"[bold]Analyzing Python code in {directory}...[/bold]")
        results = analyze_python_files(directory, patterns, output_format)

        # Output the results
        if output_file:
            with open(output_file, "w") as f:
                f.write(results)
            console.print(
                f"[bold green]Analysis results saved to {output_file}[/bold green]"
            )
        else:
            if output_format == "markdown":
                syntax = Syntax(
                    results, "markdown", theme="monokai", line_numbers=False
                )
                console.print(syntax)
            elif output_format == "json":
                syntax = Syntax(results, "json", theme="monokai", line_numbers=False)
                console.print(syntax)
            else:
                console.print(results)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


@migrations_app.command("transform-code")
def transform_code_command(
    directory: Annotated[
        str, typer.Argument(help="Directory containing Python code to transform")
    ],
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format (text, diff, or json)")
    ] = "text",
    output_file: Annotated[
        str | None, typer.Option("--output", "-o", help="Output file path")
    ] = None,
    transformations: Annotated[
        list[str] | None,
        typer.Option("--transform", "-t", help="Transformations to apply"),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show changes without modifying files")
    ] = True,
    backup: Annotated[
        bool, typer.Option("--backup", help="Create backups before transforming")
    ] = True,
    backup_dir: Annotated[
        str | None, typer.Option("--backup-dir", help="Directory for backups")
    ] = None,
) -> None:
    """Transform Python code to migrate patterns and APIs."""
    try:
        directory_path = Path(directory)

        if not directory_path.exists() or not directory_path.is_dir():
            console.print(
                f"[bold red]Error:[/bold red] Directory not found: {directory}"
            )
            return

        # Create backups if requested
        if backup and not dry_run:
            backup_dir = backup_dir or "./backups"
            os.makedirs(backup_dir, exist_ok=True)

            console.print(f"[bold]Creating code backups...[/bold]")
            backups = backup_before_migration(
                [directory_path], backup_dir, compress=True
            )

            for path, backup_path in backups.items():
                console.print(f"[bold green]Backup created: {backup_path}[/bold green]")

        # Apply transformations
        console.print(
            f"[bold]{'Analyzing' if dry_run else 'Transforming'} Python code in {directory}...[/bold]"
        )
        results = apply_transformations(
            directory, transformations, dry_run, output_format
        )

        # Output the results
        if output_file:
            with open(output_file, "w") as f:
                f.write(results)
            console.print(
                f"[bold green]Transformation results saved to {output_file}[/bold green]"
            )
        else:
            if output_format == "diff" and not isinstance(results, str):
                # Handle case when the actual results were returned
                console.print("[bold yellow]No changes to display[/bold yellow]")
            else:
                console.print(results)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


@migrations_app.command("restore-backup")
def restore_backup_command(
    backup_dir: Annotated[str, typer.Argument(help="Directory containing backups")],
    force: Annotated[
        bool, typer.Option("--force", help="Force overwriting existing files")
    ] = False,
    target_dir: Annotated[
        str | None,
        typer.Option("--target", "-t", help="Target directory for restoration"),
    ] = None,
) -> None:
    """Restore files from backups."""
    try:
        backup_dir_path = Path(backup_dir)

        if not backup_dir_path.exists() or not backup_dir_path.is_dir():
            console.print(
                f"[bold red]Error:[/bold red] Backup directory not found: {backup_dir}"
            )
            return

        # Restore from backups
        console.print(f"[bold]Restoring from backups in {backup_dir}...[/bold]")

        try:
            results = undo_migration(backup_dir_path, force=force)

            console.print(f"[bold green]Restoration complete[/bold green]")
            console.print(f"Files processed: {results['restore_count']}")
            console.print(f"Files successfully restored: {results['successful']}")

            if results["failed"] > 0:
                console.print(
                    f"[bold yellow]Files failed to restore: {results['failed']}[/bold yellow]"
                )

        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            return

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            import traceback

            console.print(traceback.format_exc())


# Fallback functions to use without typer
def _fallback_print_help():
    """Print help for the migrations CLI without typer."""
    print("Database and Codebase Migration Tools")
    print("\nCommands:")
    print("  diff-schema        - Compare SQLAlchemy models to database schema")
    print("  generate-migration - Generate a database migration script")
    print("  apply-migration    - Apply a database migration script")
    print("  rollback-migration - Roll back a database migration")
    print("  analyze-code       - Analyze Python code for migration needs")
    print("  transform-code     - Transform Python code to migrate patterns and APIs")
    print("  restore-backup     - Restore files from backups")
    print("\nUse --help with any command for more information")


def _fallback_parse_args(args):
    """Parse command-line arguments without typer."""
    if len(args) == 0 or args[0] in ["--help", "-h"]:
        _fallback_print_help()
        return None, {}

    command = args[0]

    # Define a mapping of argument names to their types
    arg_types = {
        "connection_string": str,
        "models_module": str,
        "schema": str,
        "output_format": str,
        "output_file": str,
        "message": str,
        "format": str,
        "dry_run": bool,
        "backup": bool,
        "backup_dir": str,
        "directory": str,
        "patterns": list,
        "transformations": list,
        "force": bool,
        "target_dir": str,
    }

    # Parse arguments
    parsed_args = {}
    i = 1
    positional_count = 0

    while i < len(args):
        arg = args[i]

        if arg.startswith("--"):
            # Named argument
            arg_name = arg[2:].replace("-", "_")

            if arg_name in arg_types:
                if arg_types[arg_name] == bool:
                    parsed_args[arg_name] = True
                    i += 1
                else:
                    if i + 1 < len(args) and not args[i + 1].startswith("--"):
                        parsed_args[arg_name] = args[i + 1]
                        i += 2
                    else:
                        parsed_args[arg_name] = None
                        i += 1
            else:
                i += 1
        elif arg.startswith("-"):
            # Short option
            # Map short options to long ones
            short_to_long = {
                "-c": "connection_string",
                "-m": "models_module",
                "-s": "schema",
                "-f": "output_format",
                "-o": "output_file",
                "-g": "message",
                "-p": "patterns",
                "-t": "transformations",
            }

            arg_name = short_to_long.get(arg)

            if arg_name:
                if arg_types[arg_name] == bool:
                    parsed_args[arg_name] = True
                    i += 1
                else:
                    if i + 1 < len(args) and not args[i + 1].startswith("-"):
                        parsed_args[arg_name] = args[i + 1]
                        i += 2
                    else:
                        parsed_args[arg_name] = None
                        i += 1
            else:
                i += 1
        else:
            # Positional argument
            if command == "diff-schema":
                if positional_count == 0:
                    parsed_args["connection_string"] = arg
                elif positional_count == 1:
                    parsed_args["models_module"] = arg
                positional_count += 1
            elif command in ["apply-migration", "rollback-migration"]:
                if positional_count == 0:
                    parsed_args["script_path"] = arg
                positional_count += 1
            elif command in ["analyze-code", "transform-code", "restore-backup"]:
                if positional_count == 0:
                    if command == "restore-backup":
                        parsed_args["backup_dir"] = arg
                    else:
                        parsed_args["directory"] = arg
                positional_count += 1

            i += 1

    return command, parsed_args


def _fallback_run_command(command, args):
    """Run a command with parsed arguments without typer."""
    if command == "diff-schema":
        diff_schema_command(**args)
    elif command == "generate-migration":
        generate_migration_command(**args)
    elif command == "apply-migration":
        apply_migration_command(**args)
    elif command == "rollback-migration":
        rollback_migration_command(**args)
    elif command == "analyze-code":
        analyze_code_command(**args)
    elif command == "transform-code":
        transform_code_command(**args)
    elif command == "restore-backup":
        restore_backup_command(**args)
    else:
        print(f"Unknown command: {command}")
        _fallback_print_help()


def migrations_cli():
    """Entry point for the migrations CLI."""
    global in_fallback_mode

    try:
        migrations_app()
    except SystemExit:
        # This is normal when typer exits
        pass
    except Exception as e:
        if not in_fallback_mode:
            # Fall back to basic CLI
            in_fallback_mode = True
            print(f"Warning: Using fallback CLI mode due to error: {e}")
            args = sys.argv[1:]
            command, parsed_args = _fallback_parse_args(args)

            if command:
                _fallback_run_command(command, parsed_args)


# Functions for argparse-based CLI
def setup_parser(subparsers):
    """Set up the argument parser for the migrations command.

    Args:
        subparsers: Subparsers object from the main parser
    """
    migrations_parser = subparsers.add_parser(
        "migrations", help="Tools for database migrations and codebase transformations"
    )

    migrations_subparsers = migrations_parser.add_subparsers(dest="subcommand")

    # diff-schema command
    diff_parser = migrations_subparsers.add_parser(
        "diff-schema",
        help="Compare SQLAlchemy models to database schema and show differences",
    )
    diff_parser.add_argument(
        "-c",
        "--connection",
        dest="connection_string",
        required=True,
        help="Database connection string",
    )
    diff_parser.add_argument(
        "-m",
        "--models",
        dest="models_module",
        required=True,
        help="Python module path containing SQLAlchemy models",
    )
    diff_parser.add_argument(
        "-s", "--schema", dest="schema", help="Database schema to compare"
    )
    diff_parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        default="text",
        choices=["text", "markdown"],
        help="Output format (text or markdown)",
    )
    diff_parser.add_argument(
        "-o", "--output", dest="output_file", help="Output file path"
    )

    # generate-migration command
    generate_parser = migrations_subparsers.add_parser(
        "generate-migration",
        help="Generate a database migration script based on model/schema differences",
    )
    generate_parser.add_argument(
        "-c",
        "--connection",
        dest="connection_string",
        required=True,
        help="Database connection string",
    )
    generate_parser.add_argument(
        "-m",
        "--models",
        dest="models_module",
        required=True,
        help="Python module path containing SQLAlchemy models",
    )
    generate_parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        required=True,
        help="Directory for migration scripts",
    )
    generate_parser.add_argument(
        "-g",
        "--message",
        dest="message",
        required=True,
        help="Migration message (short description)",
    )
    generate_parser.add_argument(
        "-s", "--schema", dest="schema", help="Database schema"
    )
    generate_parser.add_argument(
        "-f",
        "--format",
        dest="format",
        default="python",
        choices=["python", "sql"],
        help="Migration format (python or sql)",
    )
    generate_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show what would be generated without creating files",
    )

    # apply-migration command
    apply_parser = migrations_subparsers.add_parser(
        "apply-migration", help="Apply a database migration script"
    )
    apply_parser.add_argument("script_path", help="Path to the migration script")
    apply_parser.add_argument(
        "-c",
        "--connection",
        dest="connection_string",
        required=True,
        help="Database connection string",
    )
    apply_parser.add_argument("-s", "--schema", dest="schema", help="Database schema")
    apply_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Run without applying changes",
    )
    apply_parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Skip database backup before applying",
    )
    apply_parser.add_argument(
        "--backup-dir", dest="backup_dir", help="Directory for backups"
    )

    # rollback-migration command
    rollback_parser = migrations_subparsers.add_parser(
        "rollback-migration", help="Roll back a database migration"
    )
    rollback_parser.add_argument(
        "script_path", help="Path to the migration script to roll back"
    )
    rollback_parser.add_argument(
        "-c",
        "--connection",
        dest="connection_string",
        required=True,
        help="Database connection string",
    )
    rollback_parser.add_argument(
        "-s", "--schema", dest="schema", help="Database schema"
    )
    rollback_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Run without applying changes",
    )
    rollback_parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Skip database backup before rolling back",
    )
    rollback_parser.add_argument(
        "--backup-dir", dest="backup_dir", help="Directory for backups"
    )

    # analyze-code command
    analyze_parser = migrations_subparsers.add_parser(
        "analyze-code", help="Analyze Python code for migration needs"
    )
    analyze_parser.add_argument(
        "directory", help="Directory containing Python code to analyze"
    )
    analyze_parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        default="text",
        choices=["text", "markdown", "json"],
        help="Output format (text, markdown, or json)",
    )
    analyze_parser.add_argument(
        "-o", "--output", dest="output_file", help="Output file path"
    )
    analyze_parser.add_argument(
        "-p",
        "--pattern",
        dest="patterns",
        action="append",
        help="Patterns to check for (can be specified multiple times)",
    )

    # transform-code command
    transform_parser = migrations_subparsers.add_parser(
        "transform-code", help="Transform Python code to migrate patterns and APIs"
    )
    transform_parser.add_argument(
        "directory", help="Directory containing Python code to transform"
    )
    transform_parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        default="text",
        choices=["text", "diff", "json"],
        help="Output format (text, diff, or json)",
    )
    transform_parser.add_argument(
        "-o", "--output", dest="output_file", help="Output file path"
    )
    transform_parser.add_argument(
        "-t",
        "--transform",
        dest="transformations",
        action="append",
        help="Transformations to apply (can be specified multiple times)",
    )
    transform_parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        default=True,
        help="Apply changes to files (default is dry run)",
    )
    transform_parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        default=True,
        help="Skip backups before transforming",
    )
    transform_parser.add_argument(
        "--backup-dir", dest="backup_dir", help="Directory for backups"
    )

    # restore-backup command
    restore_parser = migrations_subparsers.add_parser(
        "restore-backup", help="Restore files from backups"
    )
    restore_parser.add_argument("backup_dir", help="Directory containing backups")
    restore_parser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="Force overwriting existing files",
    )
    restore_parser.add_argument(
        "-t", "--target", dest="target_dir", help="Target directory for restoration"
    )

    return migrations_parser


def handle_command(args):
    """Handle the migrations command.

    Args:
        args: Parsed command-line arguments
    """
    if not hasattr(args, "subcommand") or args.subcommand is None:
        print("Please specify a subcommand")
        return

    # Map subcommands to handler functions
    handlers = {
        "diff-schema": diff_schema_command,
        "generate-migration": generate_migration_command,
        "apply-migration": apply_migration_command,
        "rollback-migration": rollback_migration_command,
        "analyze-code": analyze_code_command,
        "transform-code": transform_code_command,
        "restore-backup": restore_backup_command,
    }

    if args.subcommand in handlers:
        # Convert args namespace to dict, omitting subcommand
        kwargs = {
            k: v for k, v in vars(args).items() if k != "subcommand" and k != "command"
        }

        # Call the appropriate handler
        handlers[args.subcommand](**kwargs)
    else:
        print(f"Unknown subcommand: {args.subcommand}")


if __name__ == "__main__":
    migrations_cli()
