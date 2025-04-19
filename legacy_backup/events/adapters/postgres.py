"""
PostgreSQL adapter for the event store.

This module provides a PostgreSQL implementation of the event store,
allowing events to be persisted to and retrieved from a PostgreSQL database.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

import structlog
from sqlalchemy import Column, MetaData, Table, Text, create_engine
from sqlalchemy import String, TIMESTAMP, JSON, Integer
from sqlalchemy import insert, select, desc, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from uno.events.core.event import Event
from uno.events.core.store import EventStore

# Type variable for event store
E = TypeVar("E", bound=Event)


class PostgresEventStoreManager:
    """
    Manager for creating and initializing the PostgreSQL event store.
    
    This class handles the DDL operations needed to set up the event store
    schema in PostgreSQL, including creating tables, indices, and functions.
    """
    
    def __init__(
        self,
        schema: str = "public",
        table_name: str = "events",
        connection_string: Optional[str] = None
    ):
        """
        Initialize the PostgreSQL event store manager.
        
        Args:
            schema: Database schema to use
            table_name: Name of the events table
            connection_string: Database connection string (optional)
        """
        self.schema = schema
        self.table_name = table_name
        self.connection_string = connection_string
        self.logger = structlog.get_logger("uno.events.postgres")
        
        # Try to get connection string from settings if not provided
        if self.connection_string is None:
            try:
                from uno.settings import uno_settings
                
                self.connection_string = (
                    f"postgresql://{uno_settings.DB_USER}:{uno_settings.DB_USER_PW}@"
                    f"{uno_settings.DB_HOST}:{uno_settings.DB_PORT}/{uno_settings.DB_NAME}"
                )
            except (ImportError, AttributeError):
                self.logger.warning(
                    "Could not determine database connection string from settings"
                )
    
    def create_event_store_schema(self) -> None:
        """
        Create the event store schema in the database.
        
        This method creates the events table, indices, and related database
        objects needed for the event store.
        """
        if not self.connection_string:
            self.logger.error("Cannot create schema: No connection string available")
            return
        
        engine = create_engine(self.connection_string)
        metadata = MetaData()
        
        # Define events table
        events_table = Table(
            self.table_name,
            metadata,
            Column("id", String(36), primary_key=True),
            Column("type", String(100), nullable=False, index=True),
            Column("timestamp", TIMESTAMP(timezone=True), nullable=False, index=True),
            Column("correlation_id", String(36), nullable=True, index=True),
            Column("causation_id", String(36), nullable=True),
            Column("aggregate_id", String(36), nullable=True, index=True),
            Column("aggregate_type", String(100), nullable=True, index=True),
            Column("aggregate_version", Integer, nullable=True),
            Column("topic", String(100), nullable=True, index=True),
            Column("data", JSONB, nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")),
            schema=self.schema
        )
        
        # Create tables
        metadata.create_all(engine)
        
        self.logger.info(
            "Created event store schema",
            schema=self.schema,
            table=self.table_name
        )
        
        # Create notification function and trigger
        with engine.connect() as conn:
            # Create notification function
            conn.execute(text(f"""
            CREATE OR REPLACE FUNCTION {self.schema}.notify_event() RETURNS TRIGGER AS $$
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
            conn.execute(text(f"""
            DROP TRIGGER IF EXISTS events_notify_trigger ON {self.schema}.{self.table_name};
            CREATE TRIGGER events_notify_trigger
                AFTER INSERT ON {self.schema}.{self.table_name}
                FOR EACH ROW
                EXECUTE FUNCTION {self.schema}.notify_event();
            """))
            
            conn.commit()
        
        self.logger.info(
            "Created event notification function and trigger",
            schema=self.schema,
            table=self.table_name
        )


class PostgresEventStore(EventStore[E]):
    """
    PostgreSQL implementation of the event store.
    
    This implementation stores events in a PostgreSQL database table,
    supporting robust persistence and querying capabilities.
    """
    
    def __init__(
        self,
        event_type: Type[E],
        schema: str = "public",
        table_name: str = "events",
        connection_string: Optional[str] = None,
    ):
        """
        Initialize the PostgreSQL event store.
        
        Args:
            event_type: Type of events this store handles
            schema: Database schema to use
            table_name: Name of the events table
            connection_string: Database connection string (optional)
        """
        self.event_type = event_type
        self.schema = schema
        self.table_name = table_name
        self.connection_string = connection_string
        self.logger = structlog.get_logger("uno.events.postgres")
        
        # Try to get connection string from settings if not provided
        if self.connection_string is None:
            try:
                from uno.settings import uno_settings
                
                self.connection_string = (
                    f"postgresql+asyncpg://{uno_settings.DB_USER}:{uno_settings.DB_USER_PW}@"
                    f"{uno_settings.DB_HOST}:{uno_settings.DB_PORT}/{uno_settings.DB_NAME}"
                )
            except (ImportError, AttributeError):
                self.logger.warning(
                    "Could not determine database connection string from settings"
                )
        
        # Create engine and session factory
        if self.connection_string:
            self.engine = create_async_engine(self.connection_string)
            self.async_session = sessionmaker(
                self.engine, expire_on_commit=False, class_=AsyncSession
            )
        else:
            self.engine = None
            self.async_session = None
        
        # Define metadata and table
        metadata = MetaData()
        self.events_table = Table(
            self.table_name,
            metadata,
            Column("id", String(36), primary_key=True),
            Column("type", String(100), nullable=False, index=True),
            Column("timestamp", TIMESTAMP(timezone=True), nullable=False, index=True),
            Column("correlation_id", String(36), nullable=True, index=True),
            Column("causation_id", String(36), nullable=True),
            Column("aggregate_id", String(36), nullable=True, index=True),
            Column("aggregate_type", String(100), nullable=True, index=True),
            Column("aggregate_version", Integer, nullable=True),
            Column("topic", String(100), nullable=True, index=True),
            Column("data", JSONB, nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")),
            schema=self.schema
        )
    
    @classmethod
    def initialize_schema(
        cls,
        schema: str = "public", 
        table_name: str = "events",
        connection_string: Optional[str] = None,
    ) -> None:
        """
        Initialize the event store schema in the database.
        
        Args:
            schema: Database schema to use
            table_name: Name of the events table
            connection_string: Database connection string (optional)
        """
        manager = PostgresEventStoreManager(
            schema=schema,
            table_name=table_name,
            connection_string=connection_string,
        )
        manager.create_event_store_schema()
    
    async def save_event(self, event: E) -> None:
        """
        Save an event to the PostgreSQL store.
        
        Args:
            event: The event to save
        """
        if not self.async_session:
            raise RuntimeError("PostgreSQL event store is not properly initialized")
        
        try:
            # Extract data and metadata from the event
            event_data = event.to_dict()
            
            # Remove standard fields that are stored in separate columns
            data = {k: v for k, v in event_data.items() if k not in [
                "id", "type", "timestamp", "correlation_id", "causation_id",
                "aggregate_id", "aggregate_type", "aggregate_version", "topic"
            ]}
            
            # Insert event into database
            insert_stmt = insert(self.events_table).values(
                id=event.id,
                type=event.type,
                timestamp=event.timestamp,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                aggregate_version=event.aggregate_version,
                topic=event.topic,
                data=data,
            )
            
            async with self.async_session() as session:
                await session.execute(insert_stmt)
                await session.commit()
            
            self.logger.debug(
                "Saved event to database",
                event_id=event.id,
                event_type=event.type,
            )
        
        except Exception as e:
            self.logger.error(
                "Error saving event to database",
                event_id=event.id,
                event_type=event.type,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_events_by_aggregate_id(
        self, 
        aggregate_id: str,
        event_types: Optional[List[str]] = None,
        since: Optional[datetime] = None,
    ) -> List[E]:
        """
        Get all events for a specific aggregate ID.
        
        Args:
            aggregate_id: ID of the aggregate to get events for
            event_types: Optional list of event types to filter by
            since: Optional timestamp to only return events after
            
        Returns:
            List of events for the aggregate
        """
        if not self.async_session:
            raise RuntimeError("PostgreSQL event store is not properly initialized")
        
        try:
            # Build query
            query = (
                select(self.events_table)
                .where(self.events_table.c.aggregate_id == aggregate_id)
                .order_by(self.events_table.c.timestamp)
            )
            
            # Add event types filter if provided
            if event_types:
                query = query.where(self.events_table.c.type.in_(event_types))
            
            # Add timestamp filter if provided
            if since:
                query = query.where(self.events_table.c.timestamp >= since)
            
            # Execute query
            async with self.async_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
            
            # Convert rows to events
            events = []
            for row in rows:
                event_data = self._row_to_event_data(row)
                events.append(self.event_type.from_dict(event_data))
            
            return events
        
        except Exception as e:
            self.logger.error(
                "Error getting events by aggregate ID",
                aggregate_id=aggregate_id,
                error=str(e),
                exc_info=True,
            )
            return []
    
    async def get_events_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[E]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            since: Optional timestamp to only return events after
            limit: Optional maximum number of events to return
            
        Returns:
            List of events of the specified type
        """
        if not self.async_session:
            raise RuntimeError("PostgreSQL event store is not properly initialized")
        
        try:
            # Build query
            query = (
                select(self.events_table)
                .where(self.events_table.c.type == event_type)
                .order_by(self.events_table.c.timestamp)
            )
            
            # Add timestamp filter if provided
            if since:
                query = query.where(self.events_table.c.timestamp >= since)
            
            # Add limit if provided
            if limit:
                query = query.limit(limit)
            
            # Execute query
            async with self.async_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
            
            # Convert rows to events
            events = []
            for row in rows:
                event_data = self._row_to_event_data(row)
                events.append(self.event_type.from_dict(event_data))
            
            return events
        
        except Exception as e:
            self.logger.error(
                "Error getting events by type",
                event_type=event_type,
                error=str(e),
                exc_info=True,
            )
            return []
    
    async def get_events_by_correlation_id(
        self,
        correlation_id: str,
    ) -> List[E]:
        """
        Get all events with a specific correlation ID.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of events with the specified correlation ID
        """
        if not self.async_session:
            raise RuntimeError("PostgreSQL event store is not properly initialized")
        
        try:
            # Build query
            query = (
                select(self.events_table)
                .where(self.events_table.c.correlation_id == correlation_id)
                .order_by(self.events_table.c.timestamp)
            )
            
            # Execute query
            async with self.async_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
            
            # Convert rows to events
            events = []
            for row in rows:
                event_data = self._row_to_event_data(row)
                events.append(self.event_type.from_dict(event_data))
            
            return events
        
        except Exception as e:
            self.logger.error(
                "Error getting events by correlation ID",
                correlation_id=correlation_id,
                error=str(e),
                exc_info=True,
            )
            return []
    
    async def get_all_events(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[E]:
        """
        Get all events in the event store.
        
        Args:
            since: Optional timestamp to only return events after
            limit: Optional maximum number of events to return
            
        Returns:
            List of all events
        """
        if not self.async_session:
            raise RuntimeError("PostgreSQL event store is not properly initialized")
        
        try:
            # Build query
            query = select(self.events_table).order_by(self.events_table.c.timestamp)
            
            # Add timestamp filter if provided
            if since:
                query = query.where(self.events_table.c.timestamp >= since)
            
            # Add limit if provided
            if limit:
                query = query.limit(limit)
            
            # Execute query
            async with self.async_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
            
            # Convert rows to events
            events = []
            for row in rows:
                event_data = self._row_to_event_data(row)
                events.append(self.event_type.from_dict(event_data))
            
            return events
        
        except Exception as e:
            self.logger.error(
                "Error getting all events",
                error=str(e),
                exc_info=True,
            )
            return []
    
    def _row_to_event_data(self, row: Any) -> Dict[str, Any]:
        """
        Convert a database row to event data.
        
        Args:
            row: The database row
            
        Returns:
            Dictionary of event data
        """
        # Get dictionary representation of row
        if hasattr(row, "_mapping"):
            # SQLAlchemy 1.4+ result row
            row_dict = dict(row._mapping)
        elif hasattr(row, "_asdict"):
            # Named tuple
            row_dict = row._asdict()
        else:
            # Fallback
            row_dict = dict(row)
        
        # Extract data field
        data = row_dict.get("data", {})
        if isinstance(data, str):
            data = json.loads(data)
        
        # Combine standard fields with data
        event_data = {
            "id": row_dict.get("id"),
            "type": row_dict.get("type"),
            "timestamp": row_dict.get("timestamp"),
            "correlation_id": row_dict.get("correlation_id"),
            "causation_id": row_dict.get("causation_id"),
            "aggregate_id": row_dict.get("aggregate_id"),
            "aggregate_type": row_dict.get("aggregate_type"),
            "aggregate_version": row_dict.get("aggregate_version"),
            "topic": row_dict.get("topic"),
            **data
        }
        
        return event_data