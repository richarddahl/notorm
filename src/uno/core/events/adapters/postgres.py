# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
PostgreSQL implementation of the EventStore.

This module provides a PostgreSQL-based implementation of the EventStore interface,
allowing for robust event persistence and retrieval using PostgreSQL.
"""

import json
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, TypeVar, Generic, Type, cast
import uuid
import asyncio

from pydantic import BaseModel, Field
import asyncpg
from sqlalchemy import MetaData, Table, Column, text, String, Integer, JSON, TIMESTAMP, select, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from uno.core.logging import get_logger
from uno.core.protocols.event import EventProtocol, EventStoreProtocol
from uno.core.errors import Result, Error, ConcurrencyError
from uno.core.events.event import Event
from uno.core.events.store import EventStore

# Type variable for event
E = TypeVar('E', bound=EventProtocol)


class PostgresEventStoreConfig(BaseModel):
    """Configuration for the PostgreSQL event store."""
    
    # Connection settings
    connection_string: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800  # 30 minutes
    
    # Schema settings
    schema: str = "public"
    table_name: str = "events"
    
    # Feature flags
    use_notifications: bool = True
    create_schema_if_missing: bool = True
    
    # Performance settings
    batch_size: int = 100
    use_connection_pool: bool = True


class PostgresEventStore(EventStore[E]):
    """
    PostgreSQL implementation of the EventStore.
    
    This implementation stores events in a PostgreSQL database, providing
    robust persistence and efficient retrieval for event sourcing and
    event-driven architectures.
    """
    
    def __init__(
        self,
        config: PostgresEventStoreConfig,
        event_class: Type[E] = Event,
    ):
        """
        Initialize the PostgreSQL event store.
        
        Args:
            config: Configuration for the event store
            event_class: The event class this store will use
        """
        self.config = config
        self.event_class = event_class
        self.logger = get_logger(f"uno.events.postgres.{config.table_name}")
        self._engine = None
        self._async_session_factory = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        self._table = None
        
        # Define the events table schema
        metadata = MetaData()
        self._table = Table(
            config.table_name,
            metadata,
            Column("event_id", String(36), primary_key=True),
            Column("event_type", String(255), nullable=False, index=True),
            Column("occurred_at", TIMESTAMP(timezone=True), nullable=False, index=True),
            Column("correlation_id", String(36), nullable=True, index=True),
            Column("causation_id", String(36), nullable=True),
            Column("aggregate_id", String(36), nullable=True, index=True),
            Column("aggregate_type", String(255), nullable=True, index=True),
            Column("aggregate_version", Integer, nullable=True, index=True),
            Column("data", JSONB, nullable=False),
            Column("metadata", JSONB, nullable=True),
            schema=config.schema
        )
    
    async def initialize(self) -> None:
        """
        Initialize the event store.
        
        This method sets up the database connection pool and creates the
        events table if it doesn't exist.
        """
        async with self._initialization_lock:
            if self._initialized:
                return
            
            # Create the SQLAlchemy engine
            self._engine = create_async_engine(
                self.config.connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
            )
            
            # Create the session factory
            self._async_session_factory = sessionmaker(
                self._engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            
            # Create the schema if needed
            if self.config.create_schema_if_missing:
                async with self._engine.begin() as conn:
                    # Check if the schema exists
                    schema_exists = await conn.scalar(
                        text(f"SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = '{self.config.schema}')")
                    )
                    
                    if not schema_exists:
                        # Create the schema
                        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema}"))
                        self.logger.info(f"Created schema: {self.config.schema}")
                    
                    # Check if the table exists
                    table_exists = await conn.scalar(
                        text(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = '{self.config.schema}' AND table_name = '{self.config.table_name}')")
                    )
                    
                    if not table_exists:
                        # Create the table
                        metadata = MetaData()
                        metadata.reflect(bind=self._engine, schema=self.config.schema, views=True)
                        if self._table not in metadata.tables:
                            metadata = MetaData()
                            metadata.bind = self._engine
                            metadata.add(self._table)
                            await conn.run_sync(metadata.create_all)
                            self.logger.info(f"Created table: {self.config.schema}.{self.config.table_name}")
                
                # Create notification function and trigger if needed
                if self.config.use_notifications:
                    async with self._engine.begin() as conn:
                        # Create notification function
                        await conn.execute(text(f"""
                        CREATE OR REPLACE FUNCTION {self.config.schema}.notify_event() RETURNS TRIGGER AS $$
                        DECLARE
                            payload JSON;
                        BEGIN
                            payload = row_to_json(NEW);
                            PERFORM pg_notify('events', payload::text);
                            RETURN NEW;
                        END;
                        $$ LANGUAGE plpgsql;
                        """))
                        
                        # Create or replace trigger
                        await conn.execute(text(f"""
                        DROP TRIGGER IF EXISTS events_notify_trigger ON {self.config.schema}.{self.config.table_name};
                        CREATE TRIGGER events_notify_trigger
                            AFTER INSERT ON {self.config.schema}.{self.config.table_name}
                            FOR EACH ROW
                            EXECUTE FUNCTION {self.config.schema}.notify_event();
                        """))
                        
                        self.logger.info("Created event notification function and trigger")
            
            self._initialized = True
            self.logger.info("PostgreSQL event store initialized")
    
    async def append_events(self, events: List[E], expected_version: Optional[int] = None) -> int:
        """
        Append events to the store, optionally with optimistic concurrency.
        
        Args:
            events: The events to append
            expected_version: The expected current version (for optimistic concurrency)
            
        Returns:
            The new version after appending these events
            
        Raises:
            ConcurrencyError: If expected_version is provided and doesn't match
        """
        if not self._initialized:
            await self.initialize()
        
        if not events:
            return 0
        
        # Get the aggregate ID from the first event
        aggregate_id = events[0].aggregate_id
        if not aggregate_id:
            raise ValueError("Events must have an aggregate_id for version tracking")
        
        # Start a transaction
        async with self._async_session_factory() as session:
            async with session.begin():
                # If we're using optimistic concurrency, verify the current version
                if expected_version is not None:
                    # Get the current version
                    current_version_query = select(self._table.c.aggregate_version) \
                        .where(self._table.c.aggregate_id == aggregate_id) \
                        .order_by(self._table.c.aggregate_version.desc()) \
                        .limit(1)
                    
                    result = await session.execute(current_version_query)
                    row = result.fetchone()
                    current_version = row[0] if row else 0
                    
                    # Check if the version matches
                    if current_version != expected_version:
                        raise ConcurrencyError(
                            f"Concurrency conflict for aggregate {aggregate_id}: "
                            f"expected version {expected_version}, but current version is {current_version}"
                        )
                
                # Insert events with incrementing versions
                new_version = expected_version or 0
                for event in events:
                    new_version += 1
                    
                    # Prepare the event data
                    event_data = event.to_dict() if hasattr(event, "to_dict") else self._event_to_dict(event)
                    
                    # Remove the standard fields that will be stored in separate columns
                    data = {k: v for k, v in event_data.items() if k not in [
                        "event_id", "event_type", "occurred_at", "correlation_id", 
                        "causation_id", "aggregate_id", "aggregate_type", "aggregate_version"
                    ]}
                    
                    # Get metadata if it exists
                    metadata = event_data.get("metadata", {})
                    
                    # Prepare insert values
                    values = {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "occurred_at": event.occurred_at,
                        "correlation_id": event.correlation_id,
                        "causation_id": event.causation_id,
                        "aggregate_id": event.aggregate_id,
                        "aggregate_type": event.aggregate_type,
                        "aggregate_version": new_version,  # Use our incremented version
                        "data": data,
                        "metadata": metadata
                    }
                    
                    # Insert the event
                    await session.execute(insert(self._table).values(**values))
                
                # Commit the transaction
                await session.commit()
        
        return new_version
    
    async def get_events_by_aggregate(self, aggregate_id: str, from_version: int = 0) -> List[E]:
        """
        Get all events for a specific aggregate.
        
        Args:
            aggregate_id: The ID of the aggregate
            from_version: The starting version to retrieve from
            
        Returns:
            A list of events for the specified aggregate
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._async_session_factory() as session:
            # Build query
            query = select(self._table) \
                .where(self._table.c.aggregate_id == aggregate_id) \
                .where(self._table.c.aggregate_version >= from_version) \
                .order_by(self._table.c.aggregate_version)
            
            # Execute query
            result = await session.execute(query)
            rows = result.fetchall()
        
        # Convert rows to events
        return [self._row_to_event(row) for row in rows]
    
    async def get_events_by_type(self, event_type: str, start_date: Optional[datetime] = None) -> List[E]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: The type of events to retrieve
            start_date: Optional starting date for filtering events
            
        Returns:
            A list of events of the specified type
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._async_session_factory() as session:
            # Build query
            query = select(self._table) \
                .where(self._table.c.event_type == event_type) \
                .order_by(self._table.c.occurred_at)
            
            # Add date filter if needed
            if start_date:
                query = query.where(self._table.c.occurred_at >= start_date)
            
            # Execute query
            result = await session.execute(query)
            rows = result.fetchall()
        
        # Convert rows to events
        return [self._row_to_event(row) for row in rows]
    
    async def get_events_by_correlation_id(self, correlation_id: str) -> List[E]:
        """
        Get all events with a specific correlation ID.
        
        Args:
            correlation_id: The correlation ID to filter by
            
        Returns:
            A list of events with the specified correlation ID
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._async_session_factory() as session:
            # Build query
            query = select(self._table) \
                .where(self._table.c.correlation_id == correlation_id) \
                .order_by(self._table.c.occurred_at)
            
            # Execute query
            result = await session.execute(query)
            rows = result.fetchall()
        
        # Convert rows to events
        return [self._row_to_event(row) for row in rows]
    
    async def get_latest_events(self, limit: int = 100) -> List[E]:
        """
        Get the latest events from the store.
        
        Args:
            limit: Maximum number of events to retrieve
            
        Returns:
            A list of the latest events
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._async_session_factory() as session:
            # Build query
            query = select(self._table) \
                .order_by(self._table.c.occurred_at.desc()) \
                .limit(limit)
            
            # Execute query
            result = await session.execute(query)
            rows = result.fetchall()
        
        # Convert rows to events (in chronological order)
        events = [self._row_to_event(row) for row in rows]
        return list(reversed(events))
    
    async def get_aggregate_version(self, aggregate_id: str) -> int:
        """
        Get the current version of an aggregate.
        
        Args:
            aggregate_id: The ID of the aggregate
            
        Returns:
            The current version of the aggregate
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._async_session_factory() as session:
            # Build query
            query = select(self._table.c.aggregate_version) \
                .where(self._table.c.aggregate_id == aggregate_id) \
                .order_by(self._table.c.aggregate_version.desc()) \
                .limit(1)
            
            # Execute query
            result = await session.execute(query)
            row = result.fetchone()
        
        # Return the version or 0 if no events found
        return row[0] if row else 0
    
    def _event_to_dict(self, event: E) -> Dict[str, Any]:
        """
        Convert an event to a dictionary.
        
        Args:
            event: The event to convert
            
        Returns:
            Dictionary representation of the event
        """
        if hasattr(event, "to_dict"):
            return event.to_dict()
        elif hasattr(event, "model_dump"):
            return event.model_dump()
        else:
            # Basic fallback for non-pydantic events
            return {
                "event_id": getattr(event, "event_id", str(uuid.uuid4())),
                "event_type": getattr(event, "event_type", event.__class__.__name__),
                "occurred_at": getattr(event, "occurred_at", datetime.now(UTC)),
                "correlation_id": getattr(event, "correlation_id", None),
                "causation_id": getattr(event, "causation_id", None),
                "aggregate_id": getattr(event, "aggregate_id", None),
                "aggregate_type": getattr(event, "aggregate_type", None),
                "aggregate_version": getattr(event, "aggregate_version", None),
                "data": {k: v for k, v in event.__dict__.items() if k not in [
                    "event_id", "event_type", "occurred_at", "correlation_id",
                    "causation_id", "aggregate_id", "aggregate_type", "aggregate_version"
                ]}
            }
    
    def _row_to_event(self, row: Any) -> E:
        """
        Convert a database row to an event.
        
        Args:
            row: The database row
            
        Returns:
            An event created from the row data
        """
        # Extract the row data to a dictionary
        if hasattr(row, "_mapping"):
            # SQLAlchemy 1.4+ result row
            row_dict = dict(row._mapping)
        elif hasattr(row, "_asdict"):
            # Named tuple
            row_dict = row._asdict()
        else:
            # Fallback
            row_dict = dict(row)
        
        # Combine standard fields with data
        data = row_dict.get("data", {})
        if isinstance(data, str):
            data = json.loads(data)
        
        # Assemble the complete event data
        event_data = {
            "event_id": row_dict.get("event_id"),
            "event_type": row_dict.get("event_type"),
            "occurred_at": row_dict.get("occurred_at"),
            "correlation_id": row_dict.get("correlation_id"),
            "causation_id": row_dict.get("causation_id"),
            "aggregate_id": row_dict.get("aggregate_id"),
            "aggregate_type": row_dict.get("aggregate_type"),
            "aggregate_version": row_dict.get("aggregate_version"),
            **data
        }
        
        # Add metadata if available
        metadata = row_dict.get("metadata")
        if metadata:
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            event_data["metadata"] = metadata
        
        # Create and return the event instance
        if hasattr(self.event_class, "from_dict"):
            return self.event_class.from_dict(event_data)
        elif hasattr(self.event_class, "model_validate"):
            return self.event_class.model_validate(event_data)
        else:
            # Basic fallback
            event = self.event_class.__new__(self.event_class)
            for key, value in event_data.items():
                setattr(event, key, value)
            return event