"""
Debugging CLI commands for Uno.

This module provides CLI commands for debugging Uno applications.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable

try:
    import typer
    from typing_extensions import Annotated
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    import argparse

from uno.devtools.debugging.setup import setup_debugger
from uno.devtools.debugging.tracer import trace_function, trace_class, trace_module
from uno.devtools.debugging.sql_debug import SQLQueryDebugger, get_query_tracker
from uno.devtools.debugging.repository_debug import RepositoryDebugger
from uno.devtools.debugging.error_enhancer import enhance_error_info
from uno.core.config import get_settings
from uno.devtools.cli.main import setup_logging


logger = logging.getLogger("uno.cli.debug")


if TYPER_AVAILABLE:
    debug_app = typer.Typer(
        name="debug",
        help="Debugging utilities for Uno",
        add_completion=True,
    )
    
    @debug_app.command("setup")
    def setup_debug_command(
        app_path: Annotated[str, typer.Argument(help="Path to the FastAPI application module (e.g., 'myapp.main:app')")],
        log_level: Annotated[str, typer.Option(help="Log level: DEBUG, INFO, WARNING, ERROR")] = "DEBUG",
        log_file: Annotated[Optional[Path], typer.Option(help="Log file path")] = None,
        enable_sql: Annotated[bool, typer.Option(help="Enable SQL query tracking")] = True,
        enable_errors: Annotated[bool, typer.Option(help="Enable enhanced error reporting")] = True,
        enable_headers: Annotated[bool, typer.Option(help="Enable debug headers in responses")] = True,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Configure debugging for a Uno application."""
        setup_logging(verbose)
        
        # Parse log level
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        level = log_level_map.get(log_level.upper(), logging.DEBUG)
        
        # Import app dynamically
        try:
            module_path, app_var = app_path.split(":")
            module = __import__(module_path, fromlist=[app_var])
            app = getattr(module, app_var)
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error importing application: {str(e)}")
            sys.exit(1)
        
        # Set up debugger
        debug_components = setup_debugger(
            app=app,
            log_level=level,
            log_file=log_file,
            enable_console=True,
            enable_sql_tracking=enable_sql,
            enable_error_hooks=enable_errors,
            debug_headers=enable_headers,
        )
        
        logger.info(f"Debug setup complete for {app_path}")
        for component, value in debug_components.items():
            logger.info(f"- {component}: {type(value).__name__}")
    
    @debug_app.command("trace")
    def trace_command(
        target: Annotated[str, typer.Argument(help="Module, class, or function to trace (e.g., 'myapp.models:MyClass')")],
        log_args: Annotated[bool, typer.Option(help="Log function arguments")] = True,
        log_return: Annotated[bool, typer.Option(help="Log return values")] = True,
        log_time: Annotated[bool, typer.Option(help="Log execution time")] = True,
        log_exceptions: Annotated[bool, typer.Option(help="Log exceptions")] = True,
        max_arg_length: Annotated[int, typer.Option(help="Maximum length for logged arguments")] = 500,
        log_file: Annotated[Optional[Path], typer.Option(help="Log file path")] = None,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Set up tracing for a module, class, or function."""
        setup_logging(verbose)
        
        # Configure logging
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
            ))
            trace_logger = logging.getLogger("uno.debug.trace")
            trace_logger.addHandler(handler)
            trace_logger.setLevel(logging.DEBUG)
        
        # Parse target
        try:
            if ":" in target:
                module_path, obj_name = target.split(":")
                module = __import__(module_path, fromlist=[obj_name])
                obj = getattr(module, obj_name)
                
                if callable(obj) and not isinstance(obj, type):
                    # Function
                    logger.info(f"Setting up tracing for function {target}")
                    traced_obj = trace_function(
                        obj,
                        log_args=log_args,
                        log_return=log_return,
                        log_time=log_time,
                        log_exceptions=log_exceptions,
                        max_arg_length=max_arg_length,
                    )
                    setattr(module, obj_name, traced_obj)
                elif isinstance(obj, type):
                    # Class
                    logger.info(f"Setting up tracing for class {target}")
                    traced_class = trace_class(
                        obj,
                        log_args=log_args,
                        log_return=log_return,
                        log_time=log_time,
                        log_exceptions=log_exceptions,
                        max_arg_length=max_arg_length,
                    )
                    setattr(module, obj_name, traced_class)
                else:
                    logger.error(f"Cannot trace object of type {type(obj).__name__}")
                    sys.exit(1)
            else:
                # Module
                logger.info(f"Setting up tracing for module {target}")
                module = __import__(target, fromlist=["__name__"])
                trace_module(
                    module,
                    log_args=log_args,
                    log_return=log_return,
                    log_time=log_time,
                    log_exceptions=log_exceptions,
                    max_arg_length=max_arg_length,
                )
            
            logger.info(f"Tracing configured for {target}")
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error setting up tracing: {str(e)}")
            sys.exit(1)
    
    @debug_app.command("sql")
    def sql_debug_command(
        output: Annotated[str, typer.Option(help="Output format: console, file, or json")] = "console",
        log_file: Annotated[Optional[Path], typer.Option(help="Log file path (if output=file)")] = None,
        threshold: Annotated[float, typer.Option(help="Slow query threshold in seconds")] = 0.1,
        max_queries: Annotated[int, typer.Option(help="Maximum number of queries to track")] = 100,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Configure SQL query debugging and monitoring."""
        setup_logging(verbose)
        
        # Set up SQL debugger
        try:
            sql_debugger = SQLQueryDebugger(
                slow_query_threshold=threshold,
                max_tracked_queries=max_queries,
            )
            sql_debugger.patch_db_manager()
            
            logger.info(f"SQL debugging enabled (threshold: {threshold}s, max queries: {max_queries})")
            
            # Configure output
            if output == "file" and log_file:
                handler = logging.FileHandler(log_file)
                handler.setFormatter(logging.Formatter(
                    "[%(asctime)s] SQL: %(message)s"
                ))
                sql_logger = logging.getLogger("uno.debug.sql")
                sql_logger.addHandler(handler)
                sql_logger.setLevel(logging.DEBUG)
                logger.info(f"SQL query logs will be written to {log_file}")
            elif output == "json":
                logger.info("JSON query tracking enabled")
                # JSON tracking is handled by the query tracker directly
            
            logger.info("SQL debugging setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up SQL debugging: {str(e)}")
            sys.exit(1)
    
    @debug_app.command("error-hooks")
    def error_hooks_command(
        log_file: Annotated[Optional[Path], typer.Option(help="Log file path")] = None,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Configure enhanced error reporting."""
        setup_logging(verbose)
        
        try:
            # Set up error hooks
            error_handler = enhance_error_info()
            
            # Configure output
            if log_file:
                handler = logging.FileHandler(log_file)
                handler.setFormatter(logging.Formatter(
                    "[%(asctime)s] ERROR: %(message)s"
                ))
                error_logger = logging.getLogger("uno.debug.error")
                error_logger.addHandler(handler)
                error_logger.setLevel(logging.DEBUG)
                logger.info(f"Error logs will be written to {log_file}")
            
            logger.info("Enhanced error reporting enabled")
            
        except Exception as e:
            logger.error(f"Error setting up error hooks: {str(e)}")
            sys.exit(1)
else:
    # Simple CLI without typer
    def setup_parser(subparsers):
        """Set up command parsers.
        
        Args:
            subparsers: Subparsers object from argparse
        """
        # Add debug parser
        debug_parser = subparsers.add_parser("debug", help="Debugging utilities for Uno")
        debug_subparsers = debug_parser.add_subparsers(dest="subcommand")
        
        # Setup command
        setup_parser = debug_subparsers.add_parser("setup", help="Configure debugging for a Uno application")
        setup_parser.add_argument("app_path", help="Path to the FastAPI application module (e.g., 'myapp.main:app')")
        setup_parser.add_argument("--log-level", default="DEBUG", help="Log level: DEBUG, INFO, WARNING, ERROR")
        setup_parser.add_argument("--log-file", help="Log file path")
        setup_parser.add_argument("--enable-sql", action="store_true", help="Enable SQL query tracking")
        setup_parser.add_argument("--enable-errors", action="store_true", help="Enable enhanced error reporting")
        setup_parser.add_argument("--enable-headers", action="store_true", help="Enable debug headers in responses")
        setup_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
        
        # Trace command
        trace_parser = debug_subparsers.add_parser("trace", help="Set up tracing for a module, class, or function")
        trace_parser.add_argument("target", help="Module, class, or function to trace (e.g., 'myapp.models:MyClass')")
        trace_parser.add_argument("--log-args", action="store_true", help="Log function arguments")
        trace_parser.add_argument("--log-return", action="store_true", help="Log return values")
        trace_parser.add_argument("--log-time", action="store_true", help="Log execution time")
        trace_parser.add_argument("--log-exceptions", action="store_true", help="Log exceptions")
        trace_parser.add_argument("--max-arg-length", type=int, default=500, help="Maximum length for logged arguments")
        trace_parser.add_argument("--log-file", help="Log file path")
        trace_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
        
        # SQL command
        sql_parser = debug_subparsers.add_parser("sql", help="Configure SQL query debugging and monitoring")
        sql_parser.add_argument("--output", default="console", choices=["console", "file", "json"], help="Output format")
        sql_parser.add_argument("--log-file", help="Log file path (if output=file)")
        sql_parser.add_argument("--threshold", type=float, default=0.1, help="Slow query threshold in seconds")
        sql_parser.add_argument("--max-queries", type=int, default=100, help="Maximum number of queries to track")
        sql_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
        
        # Error hooks command
        error_parser = debug_subparsers.add_parser("error-hooks", help="Configure enhanced error reporting")
        error_parser.add_argument("--log-file", help="Log file path")
        error_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
    
    def handle_command(args):
        """Handle debug commands.
        
        Args:
            args: Command arguments
        """
        setup_logging(getattr(args, "verbose", 0))
        
        if args.subcommand == "setup":
            _handle_setup_command(args)
        elif args.subcommand == "trace":
            _handle_trace_command(args)
        elif args.subcommand == "sql":
            _handle_sql_command(args)
        elif args.subcommand == "error-hooks":
            _handle_error_hooks_command(args)
        else:
            print(f"Unknown debug subcommand: {args.subcommand}")
    
    def _handle_setup_command(args):
        """Handle setup command.
        
        Args:
            args: Command arguments
        """
        # Parse log level
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        level = log_level_map.get(args.log_level.upper(), logging.DEBUG)
        
        # Import app dynamically
        try:
            module_path, app_var = args.app_path.split(":")
            module = __import__(module_path, fromlist=[app_var])
            app = getattr(module, app_var)
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error importing application: {str(e)}")
            sys.exit(1)
        
        # Set up debugger
        debug_components = setup_debugger(
            app=app,
            log_level=level,
            log_file=args.log_file,
            enable_console=True,
            enable_sql_tracking=args.enable_sql,
            enable_error_hooks=args.enable_errors,
            debug_headers=args.enable_headers,
        )
        
        logger.info(f"Debug setup complete for {args.app_path}")
        for component, value in debug_components.items():
            logger.info(f"- {component}: {type(value).__name__}")
    
    def _handle_trace_command(args):
        """Handle trace command.
        
        Args:
            args: Command arguments
        """
        # Configure logging
        if args.log_file:
            handler = logging.FileHandler(args.log_file)
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
            ))
            trace_logger = logging.getLogger("uno.debug.trace")
            trace_logger.addHandler(handler)
            trace_logger.setLevel(logging.DEBUG)
        
        # Parse target
        try:
            if ":" in args.target:
                module_path, obj_name = args.target.split(":")
                module = __import__(module_path, fromlist=[obj_name])
                obj = getattr(module, obj_name)
                
                if callable(obj) and not isinstance(obj, type):
                    # Function
                    logger.info(f"Setting up tracing for function {args.target}")
                    traced_obj = trace_function(
                        obj,
                        log_args=args.log_args,
                        log_return=args.log_return,
                        log_time=args.log_time,
                        log_exceptions=args.log_exceptions,
                        max_arg_length=args.max_arg_length,
                    )
                    setattr(module, obj_name, traced_obj)
                elif isinstance(obj, type):
                    # Class
                    logger.info(f"Setting up tracing for class {args.target}")
                    traced_class = trace_class(
                        obj,
                        log_args=args.log_args,
                        log_return=args.log_return,
                        log_time=args.log_time,
                        log_exceptions=args.log_exceptions,
                        max_arg_length=args.max_arg_length,
                    )
                    setattr(module, obj_name, traced_class)
                else:
                    logger.error(f"Cannot trace object of type {type(obj).__name__}")
                    sys.exit(1)
            else:
                # Module
                logger.info(f"Setting up tracing for module {args.target}")
                module = __import__(args.target, fromlist=["__name__"])
                trace_module(
                    module,
                    log_args=args.log_args,
                    log_return=args.log_return,
                    log_time=args.log_time,
                    log_exceptions=args.log_exceptions,
                    max_arg_length=args.max_arg_length,
                )
            
            logger.info(f"Tracing configured for {args.target}")
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error setting up tracing: {str(e)}")
            sys.exit(1)
    
    def _handle_sql_command(args):
        """Handle SQL debug command.
        
        Args:
            args: Command arguments
        """
        # Set up SQL debugger
        try:
            sql_debugger = SQLQueryDebugger(
                slow_query_threshold=args.threshold,
                max_tracked_queries=args.max_queries,
            )
            sql_debugger.patch_db_manager()
            
            logger.info(f"SQL debugging enabled (threshold: {args.threshold}s, max queries: {args.max_queries})")
            
            # Configure output
            if args.output == "file" and args.log_file:
                handler = logging.FileHandler(args.log_file)
                handler.setFormatter(logging.Formatter(
                    "[%(asctime)s] SQL: %(message)s"
                ))
                sql_logger = logging.getLogger("uno.debug.sql")
                sql_logger.addHandler(handler)
                sql_logger.setLevel(logging.DEBUG)
                logger.info(f"SQL query logs will be written to {args.log_file}")
            elif args.output == "json":
                logger.info("JSON query tracking enabled")
                # JSON tracking is handled by the query tracker directly
            
            logger.info("SQL debugging setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up SQL debugging: {str(e)}")
            sys.exit(1)
    
    def _handle_error_hooks_command(args):
        """Handle error hooks command.
        
        Args:
            args: Command arguments
        """
        try:
            # Set up error hooks
            error_handler = enhance_error_info()
            
            # Configure output
            if args.log_file:
                handler = logging.FileHandler(args.log_file)
                handler.setFormatter(logging.Formatter(
                    "[%(asctime)s] ERROR: %(message)s"
                ))
                error_logger = logging.getLogger("uno.debug.error")
                error_logger.addHandler(handler)
                error_logger.setLevel(logging.DEBUG)
                logger.info(f"Error logs will be written to {args.log_file}")
            
            logger.info("Enhanced error reporting enabled")
            
        except Exception as e:
            logger.error(f"Error setting up error hooks: {str(e)}")
            sys.exit(1)