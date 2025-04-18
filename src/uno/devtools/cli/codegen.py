"""
Code generation CLI commands for Uno.

This module provides CLI commands for generating Uno code.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

try:
    import typer
    from typing_extensions import Annotated

    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    import argparse

from uno.devtools.codegen.model import generate_model
from uno.devtools.codegen.repository import generate_repository
from uno.devtools.codegen.api import generate_api
from uno.devtools.codegen.crud import generate_crud
from uno.devtools.cli.main import setup_logging


logger = logging.getLogger("uno.cli.codegen")


if TYPER_AVAILABLE:
    codegen_app = typer.Typer(
        name="generate",
        help="Generate Uno code",
        add_completion=True,
    )

    @codegen_app.command("model")
    def generate_model_command(
        name: Annotated[str, typer.Argument(help="Model class name")],
        fields_file: Annotated[
            Optional[Path], typer.Option(help="JSON file with field definitions")
        ] = None,
        fields_json: Annotated[
            Optional[str], typer.Option(help="JSON string with field definitions")
        ] = None,
        table_name: Annotated[Optional[str], typer.Option(help="Table name")] = None,
        output_file: Annotated[
            Optional[Path], typer.Option(help="Output file path")
        ] = None,
        include_schema: Annotated[
            bool, typer.Option(help="Include schema class")
        ] = True,
        schema_name: Annotated[
            Optional[str], typer.Option(help="Schema class name")
        ] = None,
        timestamps: Annotated[
            bool, typer.Option(help="Include timestamp fields")
        ] = True,
        soft_delete: Annotated[
            bool, typer.Option(help="Include soft delete field")
        ] = False,
        verbose: Annotated[
            int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")
        ] = 0,
    ):
        """Generate a BaseModel class."""
        setup_logging(verbose)

        # Load fields
        fields = {}
        if fields_file:
            try:
                with open(fields_file, "r") as f:
                    fields = json.load(f)
            except Exception as e:
                logger.error(f"Error loading fields file: {str(e)}")
                sys.exit(1)
        elif fields_json:
            try:
                fields = json.loads(fields_json)
            except Exception as e:
                logger.error(f"Error parsing fields JSON: {str(e)}")
                sys.exit(1)

        # Generate model
        code = generate_model(
            name=name,
            fields=fields,
            table_name=table_name,
            include_schema=include_schema,
            schema_name=schema_name,
            timestamps=timestamps,
            soft_delete=soft_delete,
            output_file=output_file,
        )

        # Print code if no output file
        if not output_file:
            print(code)

    @codegen_app.command("repository")
    def generate_repository_command(
        name: Annotated[str, typer.Argument(help="Repository class name")],
        model_name: Annotated[str, typer.Argument(help="Model class name")],
        output_file: Annotated[
            Optional[Path], typer.Option(help="Output file path")
        ] = None,
        id_type: Annotated[str, typer.Option(help="ID field type")] = "str",
        include_crud: Annotated[bool, typer.Option(help="Include CRUD methods")] = True,
        include_query_methods: Annotated[
            bool, typer.Option(help="Include query methods")
        ] = True,
        include_bulk_methods: Annotated[
            bool, typer.Option(help="Include bulk methods")
        ] = True,
        filters_file: Annotated[
            Optional[Path], typer.Option(help="JSON file with filter definitions")
        ] = None,
        verbose: Annotated[
            int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")
        ] = 0,
    ):
        """Generate a repository class."""
        setup_logging(verbose)

        # Load filters
        filters = None
        if filters_file:
            try:
                with open(filters_file, "r") as f:
                    filters = json.load(f)
            except Exception as e:
                logger.error(f"Error loading filters file: {str(e)}")
                sys.exit(1)

        # Generate repository
        code = generate_repository(
            name=name,
            model_name=model_name,
            id_type=id_type,
            include_crud=include_crud,
            include_query_methods=include_query_methods,
            include_bulk_methods=include_bulk_methods,
            filters=filters,
            output_file=output_file,
        )

        # Print code if no output file
        if not output_file:
            print(code)

    @codegen_app.command("api")
    def generate_api_command(
        name: Annotated[str, typer.Argument(help="Router name")],
        model_name: Annotated[str, typer.Argument(help="Model class name")],
        schema_name: Annotated[
            Optional[str], typer.Option(help="Schema class name")
        ] = None,
        repository_name: Annotated[
            Optional[str], typer.Option(help="Repository class name")
        ] = None,
        output_file: Annotated[
            Optional[Path], typer.Option(help="Output file path")
        ] = None,
        id_type: Annotated[str, typer.Option(help="ID field type")] = "str",
        prefix: Annotated[Optional[str], typer.Option(help="API path prefix")] = None,
        tag: Annotated[Optional[str], typer.Option(help="API tag")] = None,
        include_crud: Annotated[
            bool, typer.Option(help="Include CRUD endpoints")
        ] = True,
        include_pagination: Annotated[
            bool, typer.Option(help="Include pagination")
        ] = True,
        include_filtering: Annotated[
            bool, typer.Option(help="Include filtering")
        ] = True,
        include_validation: Annotated[
            bool, typer.Option(help="Include validation")
        ] = True,
        config_file: Annotated[
            Optional[Path], typer.Option(help="JSON file with endpoint configuration")
        ] = None,
        verbose: Annotated[
            int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")
        ] = 0,
    ):
        """Generate API endpoints."""
        setup_logging(verbose)

        # Load endpoint config
        endpoint_config = None
        if config_file:
            try:
                with open(config_file, "r") as f:
                    endpoint_config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config file: {str(e)}")
                sys.exit(1)

        # Generate API
        code = generate_api(
            name=name,
            model_name=model_name,
            schema_name=schema_name,
            repository_name=repository_name,
            id_type=id_type,
            prefix=prefix,
            tag=tag,
            include_crud=include_crud,
            include_pagination=include_pagination,
            include_filtering=include_filtering,
            include_validation=include_validation,
            endpoint_config=endpoint_config,
            output_file=output_file,
        )

        # Print code if no output file
        if not output_file:
            print(code)

    @codegen_app.command("crud")
    def generate_crud_command(
        name: Annotated[str, typer.Argument(help="Base name")],
        output_dir: Annotated[Path, typer.Option(help="Output directory")] = None,
        id_type: Annotated[str, typer.Option(help="ID field type")] = "str",
        fields_file: Annotated[
            Optional[Path], typer.Option(help="JSON file with field definitions")
        ] = None,
        verbose: Annotated[
            int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")
        ] = 0,
    ):
        """Generate a complete CRUD setup (model, repository, API)."""
        setup_logging(verbose)

        # Load fields
        fields = {}
        if fields_file:
            try:
                with open(fields_file, "r") as f:
                    fields = json.load(f)
            except Exception as e:
                logger.error(f"Error loading fields file: {str(e)}")
                sys.exit(1)

        # Generate CRUD
        try:
            generate_crud(
                name=name,
                fields=fields,
                id_type=id_type,
                output_dir=output_dir,
            )
            logger.info(f"Generated CRUD for {name} in {output_dir}")
        except Exception as e:
            logger.error(f"Error generating CRUD: {str(e)}")
            sys.exit(1)

else:
    # Simple CLI without typer
    def setup_parser(subparsers):
        """Set up command parsers.

        Args:
            subparsers: Subparsers object from argparse
        """
        # Add generate parser
        generate_parser = subparsers.add_parser("generate", help="Generate Uno code")
        generate_subparsers = generate_parser.add_subparsers(dest="subcommand")

        # Model command
        model_parser = generate_subparsers.add_parser(
            "model", help="Generate a BaseModel class"
        )
        model_parser.add_argument("name", help="Model class name")
        model_parser.add_argument(
            "--fields-file", type=str, help="JSON file with field definitions"
        )
        model_parser.add_argument(
            "--fields-json", type=str, help="JSON string with field definitions"
        )
        model_parser.add_argument("--table-name", type=str, help="Table name")
        model_parser.add_argument("--output-file", type=str, help="Output file path")
        model_parser.add_argument(
            "--include-schema", action="store_true", help="Include schema class"
        )
        model_parser.add_argument("--schema-name", type=str, help="Schema class name")
        model_parser.add_argument(
            "--timestamps", action="store_true", help="Include timestamp fields"
        )
        model_parser.add_argument(
            "--soft-delete", action="store_true", help="Include soft delete field"
        )
        model_parser.add_argument(
            "-v", "--verbose", action="count", default=0, help="Verbosity level"
        )

        # Repository command
        repo_parser = generate_subparsers.add_parser(
            "repository", help="Generate a repository class"
        )
        repo_parser.add_argument("name", help="Repository class name")
        repo_parser.add_argument("model_name", help="Model class name")
        repo_parser.add_argument("--output-file", type=str, help="Output file path")
        repo_parser.add_argument(
            "--id-type", type=str, default="str", help="ID field type"
        )
        repo_parser.add_argument(
            "--include-crud", action="store_true", help="Include CRUD methods"
        )
        repo_parser.add_argument(
            "--include-query-methods", action="store_true", help="Include query methods"
        )
        repo_parser.add_argument(
            "--include-bulk-methods", action="store_true", help="Include bulk methods"
        )
        repo_parser.add_argument(
            "--filters-file", type=str, help="JSON file with filter definitions"
        )
        repo_parser.add_argument(
            "-v", "--verbose", action="count", default=0, help="Verbosity level"
        )

        # API command
        api_parser = generate_subparsers.add_parser(
            "api", help="Generate API endpoints"
        )
        api_parser.add_argument("name", help="Router name")
        api_parser.add_argument("model_name", help="Model class name")
        api_parser.add_argument("--schema-name", type=str, help="Schema class name")
        api_parser.add_argument(
            "--repository-name", type=str, help="Repository class name"
        )
        api_parser.add_argument("--output-file", type=str, help="Output file path")
        api_parser.add_argument(
            "--id-type", type=str, default="str", help="ID field type"
        )
        api_parser.add_argument("--prefix", type=str, help="API path prefix")
        api_parser.add_argument("--tag", type=str, help="API tag")
        api_parser.add_argument(
            "--include-crud", action="store_true", help="Include CRUD endpoints"
        )
        api_parser.add_argument(
            "--include-pagination", action="store_true", help="Include pagination"
        )
        api_parser.add_argument(
            "--include-filtering", action="store_true", help="Include filtering"
        )
        api_parser.add_argument(
            "--include-validation", action="store_true", help="Include validation"
        )
        api_parser.add_argument(
            "--config-file", type=str, help="JSON file with endpoint configuration"
        )
        api_parser.add_argument(
            "-v", "--verbose", action="count", default=0, help="Verbosity level"
        )

        # CRUD command
        crud_parser = generate_subparsers.add_parser(
            "crud", help="Generate a complete CRUD setup"
        )
        crud_parser.add_argument("name", help="Base name")
        crud_parser.add_argument("--output-dir", type=str, help="Output directory")
        crud_parser.add_argument(
            "--id-type", type=str, default="str", help="ID field type"
        )
        crud_parser.add_argument(
            "--fields-file", type=str, help="JSON file with field definitions"
        )
        crud_parser.add_argument(
            "-v", "--verbose", action="count", default=0, help="Verbosity level"
        )

    def handle_command(args):
        """Handle codegen commands.

        Args:
            args: Command arguments
        """
        setup_logging(getattr(args, "verbose", 0))

        if args.subcommand == "model":
            _handle_model_command(args)
        elif args.subcommand == "repository":
            _handle_repository_command(args)
        elif args.subcommand == "api":
            _handle_api_command(args)
        elif args.subcommand == "crud":
            _handle_crud_command(args)
        else:
            print(f"Unknown subcommand: {args.subcommand}")

    def _handle_model_command(args):
        """Handle model command.

        Args:
            args: Command arguments
        """
        # Load fields
        fields = {}
        if getattr(args, "fields_file", None):
            try:
                with open(args.fields_file, "r") as f:
                    fields = json.load(f)
            except Exception as e:
                logger.error(f"Error loading fields file: {str(e)}")
                sys.exit(1)
        elif getattr(args, "fields_json", None):
            try:
                fields = json.loads(args.fields_json)
            except Exception as e:
                logger.error(f"Error parsing fields JSON: {str(e)}")
                sys.exit(1)

        # Generate model
        code = generate_model(
            name=args.name,
            fields=fields,
            table_name=getattr(args, "table_name", None),
            include_schema=getattr(args, "include_schema", True),
            schema_name=getattr(args, "schema_name", None),
            timestamps=getattr(args, "timestamps", True),
            soft_delete=getattr(args, "soft_delete", False),
            output_file=getattr(args, "output_file", None),
        )

        # Print code if no output file
        if not getattr(args, "output_file", None):
            print(code)

    def _handle_repository_command(args):
        """Handle repository command.

        Args:
            args: Command arguments
        """
        # Load filters
        filters = None
        if getattr(args, "filters_file", None):
            try:
                with open(args.filters_file, "r") as f:
                    filters = json.load(f)
            except Exception as e:
                logger.error(f"Error loading filters file: {str(e)}")
                sys.exit(1)

        # Generate repository
        code = generate_repository(
            name=args.name,
            model_name=args.model_name,
            id_type=getattr(args, "id_type", "str"),
            include_crud=getattr(args, "include_crud", True),
            include_query_methods=getattr(args, "include_query_methods", True),
            include_bulk_methods=getattr(args, "include_bulk_methods", True),
            filters=filters,
            output_file=getattr(args, "output_file", None),
        )

        # Print code if no output file
        if not getattr(args, "output_file", None):
            print(code)

    def _handle_api_command(args):
        """Handle API command.

        Args:
            args: Command arguments
        """
        # Load endpoint config
        endpoint_config = None
        if getattr(args, "config_file", None):
            try:
                with open(args.config_file, "r") as f:
                    endpoint_config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config file: {str(e)}")
                sys.exit(1)

        # Generate API
        code = generate_api(
            name=args.name,
            model_name=args.model_name,
            schema_name=getattr(args, "schema_name", None),
            repository_name=getattr(args, "repository_name", None),
            id_type=getattr(args, "id_type", "str"),
            prefix=getattr(args, "prefix", None),
            tag=getattr(args, "tag", None),
            include_crud=getattr(args, "include_crud", True),
            include_pagination=getattr(args, "include_pagination", True),
            include_filtering=getattr(args, "include_filtering", True),
            include_validation=getattr(args, "include_validation", True),
            endpoint_config=endpoint_config,
            output_file=getattr(args, "output_file", None),
        )

        # Print code if no output file
        if not getattr(args, "output_file", None):
            print(code)

    def _handle_crud_command(args):
        """Handle CRUD command.

        Args:
            args: Command arguments
        """
        # Load fields
        fields = {}
        if getattr(args, "fields_file", None):
            try:
                with open(args.fields_file, "r") as f:
                    fields = json.load(f)
            except Exception as e:
                logger.error(f"Error loading fields file: {str(e)}")
                sys.exit(1)

        # Generate CRUD
        try:
            generate_crud(
                name=args.name,
                fields=fields,
                id_type=getattr(args, "id_type", "str"),
                output_dir=getattr(args, "output_dir", None),
            )
            logger.info(
                f"Generated CRUD for {args.name} in {getattr(args, 'output_dir', 'current directory')}"
            )
        except Exception as e:
            logger.error(f"Error generating CRUD: {str(e)}")
            sys.exit(1)
