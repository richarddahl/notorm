#!/usr/bin/env python
"""
Event Store Migration Script

This script helps migrate events from the InMemoryEventStore to the PostgreSQL
implementation of the EventStore. It's useful when you've been working with the
in-memory store for development and want to move to a persistent store for
production.

Usage:
    python eventstore_migration.py --source <source_type> --target <target_type> [options]

Example:
    python eventstore_migration.py --source memory --target postgres --connection "postgresql+asyncpg://username:password@localhost:5432/mydatabase"
"""

import argparse
import asyncio
import logging
import json
import sys
from typing import Dict, List, Any, Optional, Type
from datetime import datetime, UTC

from pydantic import BaseModel, Field

# Add project root to path
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from uno.core.events import (
    Event,
    EventStore,
    InMemoryEventStore,
    PostgresEventStore,
    PostgresEventStoreConfig,
)
from uno.core.logging import configure_logging, get_logger


class MigrationConfig(BaseModel):
    """Configuration for event store migration."""

    source_type: str
    target_type: str
    connection_string: str | None = None
    schema: str = "public"
    table_name: str = "domain_events"
    batch_size: int = 100
    event_class: Type[Event] = Event
    create_schema: bool = True
    use_notifications: bool = True


async def migrate_events(config: MigrationConfig) -> int:
    """
    Migrate events from one store to another.

    Args:
        config: Migration configuration

    Returns:
        Number of events migrated
    """
    logger = get_logger("event_migration")
    logger.info(
        f"Starting event migration from {config.source_type} to {config.target_type}"
    )

    # Create source store
    source_store = create_event_store(
        store_type=config.source_type, config=config, logger=logger
    )

    # Create target store
    target_store = create_event_store(
        store_type=config.target_type, config=config, logger=logger
    )

    if not source_store or not target_store:
        logger.error("Failed to create event stores")
        return 0

    # Initialize stores if needed
    if hasattr(source_store, "initialize"):
        await source_store.initialize()

    if hasattr(target_store, "initialize"):
        await target_store.initialize()

    # Function to get all events from source
    async def get_all_source_events() -> list[Event]:
        """Get all events from the source store."""
        if isinstance(source_store, InMemoryEventStore):
            return source_store._events
        elif isinstance(source_store, PostgresEventStore):
            # Get events by aggregate to maintain ordering
            all_events = []

            # Get unique aggregate IDs
            unique_aggregates = set()

            # This is simplified - for a real database with many aggregates,
            # you'd need a more sophisticated approach to get all aggregate IDs
            latest_events = await source_store.get_latest_events(1000)
            for event in latest_events:
                if event.aggregate_id:
                    unique_aggregates.add(event.aggregate_id)

            # Get all events for each aggregate
            for aggregate_id in unique_aggregates:
                events = await source_store.get_events_by_aggregate(aggregate_id)
                all_events.extend(events)

            return all_events
        else:
            # Generic approach - this might not be efficient for all stores
            logger.warning(
                "Using generic approach to get all events - this might be slow"
            )
            # This is just a placeholder - you'd need to implement specific logic
            # for your event store
            return []

    # Get all events from source
    logger.info("Retrieving events from source store")
    events = await get_all_source_events()
    logger.info(f"Found {len(events)} events to migrate")

    if not events:
        logger.info("No events to migrate")
        return 0

    # Group events by aggregate
    events_by_aggregate: Dict[str, list[Event]] = {}
    for event in events:
        if event.aggregate_id:
            if event.aggregate_id not in events_by_aggregate:
                events_by_aggregate[event.aggregate_id] = []
            events_by_aggregate[event.aggregate_id].append(event)

    # Sort events by version within each aggregate
    for aggregate_id, aggregate_events in events_by_aggregate.items():
        aggregate_events.sort(key=lambda e: getattr(e, "aggregate_version", 0) or 0)

    # Migrate events aggregate by aggregate
    total_migrated = 0

    for aggregate_id, aggregate_events in events_by_aggregate.items():
        logger.info(
            f"Migrating {len(aggregate_events)} events for aggregate {aggregate_id}"
        )

        # Migrate in batches
        for i in range(0, len(aggregate_events), config.batch_size):
            batch = aggregate_events[i : i + config.batch_size]
            try:
                await target_store.append_events(batch)
                total_migrated += len(batch)
                logger.info(
                    f"Migrated batch of {len(batch)} events for aggregate {aggregate_id}"
                )
            except Exception as e:
                logger.error(
                    f"Error migrating events for aggregate {aggregate_id}: {str(e)}"
                )
                raise

    logger.info(f"Migration completed. Migrated {total_migrated} events")
    return total_migrated


def create_event_store(
    store_type: str, config: MigrationConfig, logger: logging.Logger
) -> Optional[EventStore]:
    """
    Create an event store based on the type.

    Args:
        store_type: Type of store to create (memory, postgres)
        config: Migration configuration
        logger: Logger to use

    Returns:
        The created event store or None if the type is not supported
    """
    if store_type == "memory":
        logger.info("Creating InMemoryEventStore")
        return InMemoryEventStore()
    elif store_type == "postgres":
        if not config.connection_string:
            logger.error("PostgreSQL connection string is required")
            return None

        logger.info(
            f"Creating PostgresEventStore with schema {config.schema}, table {config.table_name}"
        )
        postgres_config = PostgresEventStoreConfig(
            connection_string=config.connection_string,
            schema=config.schema,
            table_name=config.table_name,
            create_schema_if_missing=config.create_schema,
            use_notifications=config.use_notifications,
            batch_size=config.batch_size,
        )
        return PostgresEventStore(
            config=postgres_config, event_class=config.event_class
        )
    else:
        logger.error(f"Unsupported event store type: {store_type}")
        return None


async def main():
    """Run the event store migration."""
    # Configure logging
    configure_logging()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Migrate events between event stores")
    parser.add_argument(
        "--source", required=True, help="Source event store type (memory, postgres)"
    )
    parser.add_argument(
        "--target", required=True, help="Target event store type (memory, postgres)"
    )
    parser.add_argument("--connection", help="PostgreSQL connection string")
    parser.add_argument("--schema", default="public", help="PostgreSQL schema")
    parser.add_argument(
        "--table", default="domain_events", help="PostgreSQL table name"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for migrations"
    )
    parser.add_argument(
        "--no-create-schema", action="store_true", help="Don't create schema if missing"
    )
    parser.add_argument(
        "--no-notifications",
        action="store_true",
        help="Don't use PostgreSQL notifications",
    )

    args = parser.parse_args()

    # Create configuration
    config = MigrationConfig(
        source_type=args.source,
        target_type=args.target,
        connection_string=args.connection,
        schema=args.schema,
        table_name=args.table,
        batch_size=args.batch_size,
        create_schema=not args.no_create_schema,
        use_notifications=not args.no_notifications,
    )

    # Perform migration
    try:
        migrated = await migrate_events(config)
        if migrated > 0:
            print(f"Successfully migrated {migrated} events")
            return 0
        else:
            print("No events migrated")
            return 1
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())
