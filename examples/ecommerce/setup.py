#!/usr/bin/env python3
"""
Setup script for the e-commerce domain example.

This script initializes the database and needed infrastructure for
the e-commerce domain example.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ecommerce-setup")

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import needed modules
from uno.domain.event_store import PostgresEventStore


async def initialize_event_store():
    """Initialize the event store schema."""
    logger.info("Initializing event store schema...")
    try:
        PostgresEventStore.initialize_schema(logger=logger)
        logger.info("Event store schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing event store: {e}")
        return False
    return True


async def setup_database():
    """Check database connection and set up necessary structures."""
    # Import here to avoid circular import
    from uno.database.session import async_session
    
    logger.info("Testing database connection...")
    try:
        async with async_session() as session:
            result = await session.execute("SELECT version()")
            version = result.fetchone()[0]
            logger.info(f"Connected to database: {version}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def main():
    """Main setup function."""
    logger.info("Starting e-commerce domain example setup")
    
    # Check database connection
    if not await setup_database():
        logger.error("Setup failed: Database connection error")
        return False
    
    # Initialize event store
    if not await initialize_event_store():
        logger.error("Setup failed: Event store initialization error")
        return False
    
    logger.info("Setup completed successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)