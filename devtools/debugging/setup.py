"""
Setup utilities for debugging Uno applications.

This module provides utilities for setting up debugging in Uno applications.
"""

import logging
import sys
import os
from typing import Dict, List, Optional, Set, Union, Any
from pathlib import Path

from fastapi import FastAPI

from uno.devtools.debugging.middleware import debug_fastapi, DebugMiddleware
from uno.devtools.debugging.sql_debug import SQLQueryDebugger, get_query_tracker
from uno.devtools.debugging.error_enhancer import setup_error_hooks


def setup_debugger(
    app: Optional[FastAPI] = None,
    log_level: int = logging.DEBUG,
    log_file: Optional[Union[str, Path]] = None,
    enable_console: bool = True,
    enable_sql_tracking: bool = True,
    enable_error_hooks: bool = True,
    debug_headers: bool = True,
) -> dict[str, Any]:
    """Set up debugging for a Uno application.

    Args:
        app: Optional FastAPI application to add debug middleware to
        log_level: Logging level for the debug logger
        log_file: Optional file path to log debug information to
        enable_console: Whether to log debug information to the console
        enable_sql_tracking: Whether to enable SQL query tracking
        enable_error_hooks: Whether to install error hooks
        debug_headers: Whether to add debug headers to responses

    Returns:
        Dictionary with initialized debug components
    """
    # Set up logging
    debug_logger = _setup_logging(log_level, log_file, enable_console)

    debug_components = {
        "logger": debug_logger,
    }

    # Set up SQL query tracking
    if enable_sql_tracking:
        sql_debugger = SQLQueryDebugger()
        sql_debugger.patch_db_manager()
        debug_components["sql_tracker"] = get_query_tracker()

    # Set up error hooks
    if enable_error_hooks:
        error_handler = setup_error_hooks()
        debug_components["error_handler"] = error_handler

    # Set up FastAPI debug middleware
    if app is not None:
        debug_fastapi(
            app,
            enable_request_logging=True,
            enable_sql_tracking=enable_sql_tracking,
            enable_dependency_tracking=True,
            enable_error_enhancement=True,
            debug_headers=debug_headers,
        )
        debug_components["app"] = app

    return debug_components


def _setup_logging(
    log_level: int,
    log_file: Optional[Union[str, Path]],
    enable_console: bool,
) -> logging.Logger:
    """Set up logging for debugging.

    Args:
        log_level: Logging level for the debug logger
        log_file: Optional file path to log debug information to
        enable_console: Whether to log debug information to the console

    Returns:
        The configured logger
    """
    # Create logger
    logger = logging.getLogger("uno.debug")
    logger.setLevel(log_level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Format for debug logs
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
