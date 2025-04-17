"""
Event store manager for managing the event store schema.

This module provides a manager for creating and managing the event store schema
that leverages Uno's SQL generation capabilities for consistent database management.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, UTC

from uno.settings import uno_settings
from uno.sql.statement import SQLStatement
from uno.sql.emitters.event_store import (
    CreateDomainEventsTable,
    CreateEventProcessorsTable,
    CreateEventSnapshotsTable,
    CreateEventProjectionFunction,
)
from uno.database.session import async_session, get_db_session
from uno.database.engine.factory import AsyncEngineFactory
from uno.core.unified_events import UnoDomainEvent


class EventStoreManager:
    """
    Manager for creating and managing the event store schema.

    This class works with the SQLEmitters to generate and execute SQL for
    setting up the event store database objects.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the event store manager.

        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = uno_settings

    def create_event_store_schema(self) -> None:
        """
        Create the event store schema in the database.

        This method generates and executes the SQL for creating the event store
        tables, functions, triggers, and grants needed for the event sourcing system.
        """
        self.logger.info("Creating event store schema...")

        # Collect all SQL statements
        statements = self._generate_event_store_sql()

        # Use a synchronous connection instead of async
        import psycopg
        from uno.database.config import ConnectionConfig

        # Create connection configuration
        conn_config = ConnectionConfig(
            db_role=f"{self.config.DB_NAME}_admin",  # Use admin role
            db_name=self.config.DB_NAME,
            db_host=self.config.DB_HOST,
            db_port=self.config.DB_PORT,
            db_user_pw=self.config.DB_USER_PW,
            db_driver=self.config.DB_SYNC_DRIVER,
            db_schema=self.config.DB_SCHEMA,
        )

        # Create direct connection string
        conn_string = (
            f"host={conn_config.db_host} "
            f"port={conn_config.db_port} "
            f"dbname={conn_config.db_name} "
            f"user={conn_config.db_role} "
            f"password={conn_config.db_user_pw}"
        )

        try:
            # Connect with autocommit for DDL statements
            with psycopg.connect(conn_string, autocommit=True) as conn:
                cursor = conn.cursor()

                # Execute each statement
                for statement in statements:
                    self.logger.debug(f"Executing SQL: {statement.name}")
                    cursor.execute(statement.sql)

            self.logger.info("Event store schema created successfully")

        except Exception as e:
            self.logger.error(f"Error creating event store schema: {e}")
            raise

    def _generate_event_store_sql(self) -> List[SQLStatement]:
        """
        Generate SQL statements for creating the event store schema.

        Returns:
            List of SQL statements to execute
        """
        statements = []

        # Create emitters
        emitters = [
            CreateDomainEventsTable(self.config),
            CreateEventProcessorsTable(self.config),
            CreateEventSnapshotsTable(self.config),
            CreateEventProjectionFunction(self.config),
        ]

        # Generate SQL from each emitter
        for emitter in emitters:
            statements.extend(emitter.generate_sql())

        return statements

    async def get_event_counts(self) -> Dict[str, int]:
        """
        Get count of events by type.

        Returns:
            Dictionary mapping event types to counts
        """
        query = f"""
        SELECT event_type, COUNT(*) as count
        FROM {self.config.DB_SCHEMA}.domain_events
        GROUP BY event_type
        ORDER BY count DESC
        """

        async with async_session() as session:
            result = await session.execute(query)
            rows = result.fetchall()

        return {row[0]: row[1] for row in rows}

    async def get_aggregate_counts(self) -> Dict[str, int]:
        """
        Get count of aggregates by type.

        Returns:
            Dictionary mapping aggregate types to counts
        """
        query = f"""
        SELECT aggregate_type, COUNT(DISTINCT aggregate_id) as count
        FROM {self.config.DB_SCHEMA}.domain_events
        WHERE aggregate_type IS NOT NULL
        GROUP BY aggregate_type
        ORDER BY count DESC
        """

        async with async_session() as session:
            result = await session.execute(query)
            rows = result.fetchall()

        return {row[0]: row[1] for row in rows}

    async def create_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        state: Dict[str, Any],
    ) -> None:
        """
        Create or update a snapshot for an aggregate.

        Args:
            aggregate_id: The aggregate ID
            aggregate_type: The aggregate type
            version: The version of the aggregate
            state: The aggregate state as a JSON-serializable dictionary
        """
        query = f"""
        INSERT INTO {self.config.DB_SCHEMA}.aggregate_snapshots
            (aggregate_id, aggregate_type, version, timestamp, state)
        VALUES
            (:aggregate_id, :aggregate_type, :version, :timestamp, :state)
        ON CONFLICT (aggregate_id, aggregate_type)
        DO UPDATE SET
            version = EXCLUDED.version,
            timestamp = EXCLUDED.timestamp,
            state = EXCLUDED.state,
            created_at = CURRENT_TIMESTAMP
        """

        params = {
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
            "version": version,
            "timestamp": datetime.now(UTC),
            "state": json.dumps(state),
        }

        async with async_session() as session:
            await session.execute(query, params)
            await session.commit()

        self.logger.debug(
            f"Created snapshot for {aggregate_type}/{aggregate_id} at version {version}"
        )

    async def get_snapshot(
        self, aggregate_id: str, aggregate_type: str
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        """
        Get the latest snapshot for an aggregate.

        Args:
            aggregate_id: The aggregate ID
            aggregate_type: The aggregate type

        Returns:
            Tuple of (version, state) if snapshot exists, None otherwise
        """
        query = f"""
        SELECT version, state
        FROM {self.config.DB_SCHEMA}.aggregate_snapshots
        WHERE aggregate_id = :aggregate_id
        AND aggregate_type = :aggregate_type
        """

        params = {"aggregate_id": aggregate_id, "aggregate_type": aggregate_type}

        async with async_session() as session:
            result = await session.execute(query, params)
            row = result.fetchone()

        if row:
            version, state_json = row
            state = json.loads(state_json)
            return (version, state)

        return None

    async def cleanup_old_events(
        self, days_to_keep: int = 90, event_types: Optional[List[str]] = None
    ) -> int:
        """
        Remove old events from the event store.

        Note: This should be used with caution, as it permanently deletes events.
        Only use this for events that are no longer needed for event sourcing
        or audit purposes.

        Args:
            days_to_keep: Number of days of events to keep
            event_types: Optional list of event types to clean up

        Returns:
            Number of events deleted
        """
        base_query = f"""
        DELETE FROM {self.config.DB_SCHEMA}.domain_events
        WHERE created_at < NOW() - INTERVAL '{days_to_keep} days'
        AND aggregate_id IS NULL  -- Only delete events not tied to aggregates
        """

        # Add event type filter if provided
        if event_types:
            placeholders = ", ".join([f"'{t}'" for t in event_types])
            base_query += f" AND event_type IN ({placeholders})"

        base_query += " RETURNING event_id"

        async with async_session() as session:
            result = await session.execute(base_query)
            deleted_ids = result.fetchall()
            deleted_count = len(deleted_ids)
            await session.commit()

        self.logger.info(f"Deleted {deleted_count} old events")
        return deleted_count
