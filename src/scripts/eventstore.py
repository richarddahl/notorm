#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Command for managing the event store schema."""

import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from uno.domain.event_store import PostgresEventStore
from uno.domain.event_store_manager import EventStoreManager
from uno.settings import uno_settings


# Set up logger
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("eventstore")

# Create Typer app
app = typer.Typer(
    help="Manage the event store for domain events",
    add_completion=False,
)

# Create console for output
console = Console()


@app.command("create")
def create_schema(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """Create the event store schema in the database."""
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Initialize the event store schema
        logger.info("Creating event store schema...")
        PostgresEventStore.initialize_schema(logger=logger)
        logger.info("Event store schema created successfully")
    
    except Exception as e:
        logger.error(f"Error creating event store schema: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()