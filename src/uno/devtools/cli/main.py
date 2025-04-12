"""
Main CLI entry point for Uno developer tools.

This module provides the main CLI entry point for Uno developer tools.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    import argparse


if TYPER_AVAILABLE:
    app = typer.Typer(
        name="uno-dev",
        help="Developer tools for Uno",
        add_completion=True,
    )
    
    def cli():
        """Run the CLI application."""
        app()
else:
    # Simple CLI without typer
    def cli():
        """Run the CLI application."""
        parser = argparse.ArgumentParser(description="Developer tools for Uno")
        
        subparsers = parser.add_subparsers(dest="command")
        
        # Set up subparsers for each command
        from uno.devtools.cli.codegen import setup_parser as setup_codegen_parser
        setup_codegen_parser(subparsers)
        
        from uno.devtools.cli.debug import setup_parser as setup_debug_parser
        setup_debug_parser(subparsers)
        
        from uno.devtools.cli.profile import setup_parser as setup_profile_parser
        setup_profile_parser(subparsers)
        
        # Parse arguments and dispatch
        args = parser.parse_args()
        
        if args.command is None:
            parser.print_help()
            return
        
        # Call the appropriate handler
        if args.command == "generate":
            from uno.devtools.cli.codegen import handle_command as handle_codegen
            handle_codegen(args)
        elif args.command == "debug":
            from uno.devtools.cli.debug import handle_command as handle_debug
            handle_debug(args)
        elif args.command == "profile":
            from uno.devtools.cli.profile import handle_command as handle_profile
            handle_profile(args)
        else:
            print(f"Unknown command: {args.command}")


def setup_logging(verbosity: int = 0):
    """Set up logging with the specified verbosity.
    
    Args:
        verbosity: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
    """
    log_level = logging.WARNING
    if verbosity == 1:
        log_level = logging.INFO
    elif verbosity >= 2:
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


if __name__ == "__main__":
    cli()