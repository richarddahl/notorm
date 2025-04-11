"""
Event store implementation for domain events.

This module provides the event store implementation for persisting and retrieving
domain events, supporting event-driven architectures and event sourcing.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Type, Generic, TypeVar, cast, Union
from datetime import datetime
from uuid import UUID

from sqlalchemy import Table, Column, String, TIMESTAMP, TEXT, MetaData, insert, select, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.events import DomainEvent, EventStore
from uno.domain.model import Entity, AggregateRoot


E = TypeVar('E', bound=DomainEvent)


class EventStore(Generic[E]):
    """
    Abstract base class for event stores.
    
    Event stores persist domain events for event sourcing, auditing,
    and integration with external systems.
    """
    
    async def save_event(self, event: E) -> None:
        """
        Save a domain event to the store.
        
        Args:
            event: The domain event to save
        """
        raise NotImplementedError
    
    async def get_events_by_aggregate_id(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[E]:
        """
        Get all events for a specific aggregate ID.
        
        Args:
            aggregate_id: The ID of the aggregate to get events for
            event_types: Optional list of event types to filter by
            
        Returns:
            List of events for the aggregate
        """
        raise NotImplementedError
    
    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[E]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: The type of events to retrieve
            since: Optional timestamp to retrieve events since
            
        Returns:
            List of events matching the criteria
        """
        raise NotImplementedError


class PostgresEventStore(EventStore[E]):
    """
    PostgreSQL implementation of the event store.
    
    This implementation uses a PostgreSQL table to store domain events.
    """
    
    EVENT_TABLE_NAME = 'domain_events'
    # Use the schema from settings rather than hardcoding 'public'
    from uno.settings import uno_settings
    EVENT_TABLE_SCHEMA = uno_settings.DB_SCHEMA
    
    def __init__(
        self, 
        event_type: Type[E],
        table_name: str = EVENT_TABLE_NAME,
        schema: str = EVENT_TABLE_SCHEMA,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the PostgreSQL event store.
        
        Args:
            event_type: The type of events this store handles
            table_name: The name of the table to store events in
            schema: The database schema to use
            logger: Optional logger for diagnostic information
        """
        self.event_type = event_type
        self.table_name = table_name
        self.schema = schema
        self.logger = logger or logging.getLogger(__name__)
        
        # Define table structure
        metadata = MetaData()
        self.events_table = Table(
            self.table_name,
            metadata,
            Column('event_id', String(36), primary_key=True),
            Column('event_type', String(100), nullable=False, index=True),
            Column('aggregate_id', String(36), nullable=True, index=True),
            Column('aggregate_type', String(100), nullable=True),
            Column('timestamp', TIMESTAMP, nullable=False, index=True),
            Column('data', JSONB, nullable=False),
            Column('metadata', JSONB, nullable=True),
            Column('created_at', TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
            schema=self.schema
        )
    
    @classmethod
    def initialize_schema(cls, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the event store schema in the database.
        
        This class method creates all the necessary database objects for the event store
        using the EventStoreManager, which leverages Uno's SQL generation capabilities.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        manager = EventStoreManager(logger=logger)
        manager.create_event_store_schema()
    
    async def save_event(self, event: E, aggregate_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save a domain event to the PostgreSQL store.
        
        Args:
            event: The domain event to save
            aggregate_id: Optional ID of the aggregate that generated this event
            metadata: Optional metadata to store with the event
        """
        try:
            # Prepare event data
            event_data = event.model_dump()
            
            # Extract standard fields
            event_id = event_data.pop('event_id', None) or str(event.event_id)
            event_type = event_data.pop('event_type', None) or event.event_type
            timestamp = event_data.pop('timestamp', None) or event.timestamp
            
            # Determine aggregate details
            aggregate_type = None
            if 'aggregate_type' in event_data:
                aggregate_type = event_data.pop('aggregate_type')
            
            # Use provided aggregate ID or extract from event if available
            if aggregate_id is None and 'aggregate_id' in event_data:
                aggregate_id = event_data.pop('aggregate_id')
                
            # Insert event into database
            insert_stmt = insert(self.events_table).values(
                event_id=event_id,
                event_type=event_type,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                timestamp=timestamp,
                data=json.dumps(event_data),
                metadata=json.dumps(metadata) if metadata else None
            )
            
            async with async_session() as session:
                await session.execute(insert_stmt)
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving event: {e}")
            raise
    
    async def get_events_by_aggregate_id(
        self, aggregate_id: str, event_types: Optional[List[str]] = None
    ) -> List[E]:
        """
        Get all events for a specific aggregate ID.
        
        Args:
            aggregate_id: The ID of the aggregate to get events for
            event_types: Optional list of event types to filter by
            
        Returns:
            List of events for the aggregate
        """
        try:
            # Build query
            query = select(self.events_table).where(
                self.events_table.c.aggregate_id == aggregate_id
            ).order_by(self.events_table.c.timestamp)
            
            # Add event type filter if provided
            if event_types:
                query = query.where(self.events_table.c.event_type.in_(event_types))
                
            # Execute query
            async with async_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
                
            # Convert rows to domain events
            events = []
            for row in rows:
                event_data = json.loads(row.data)
                event_data.update({
                    'event_id': row.event_id,
                    'event_type': row.event_type,
                    'timestamp': row.timestamp
                })
                events.append(self.event_type.model_validate(event_data))
                
            return events
                
        except Exception as e:
            self.logger.error(f"Error fetching events by aggregate ID: {e}")
            return []
    
    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[E]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: The type of events to retrieve
            since: Optional timestamp to retrieve events since
            
        Returns:
            List of events matching the criteria
        """
        try:
            # Build query
            query = select(self.events_table).where(
                self.events_table.c.event_type == event_type
            )
            
            # Add timestamp filter if provided
            if since:
                query = query.where(self.events_table.c.timestamp >= since)
                
            # Order by timestamp
            query = query.order_by(self.events_table.c.timestamp)
                
            # Execute query
            async with async_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
                
            # Convert rows to domain events
            events = []
            for row in rows:
                event_data = json.loads(row.data)
                event_data.update({
                    'event_id': row.event_id,
                    'event_type': row.event_type,
                    'timestamp': row.timestamp
                })
                events.append(self.event_type.model_validate(event_data))
                
            return events
                
        except Exception as e:
            self.logger.error(f"Error fetching events by type: {e}")
            return []


class EventSourcedRepository(Generic[E]):
    """
    Repository implementation that uses event sourcing.
    
    This implementation rebuilds aggregates from their event history,
    enabling full auditability and temporal queries.
    """
    
    def __init__(
        self, 
        aggregate_type: Type[AggregateRoot],
        event_store: EventStore,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the event-sourced repository.
        
        Args:
            aggregate_type: The type of aggregate this repository manages
            event_store: The event store to use for event persistence and retrieval
            logger: Optional logger for diagnostic information
        """
        self.aggregate_type = aggregate_type
        self.event_store = event_store
        self.logger = logger or logging.getLogger(__name__)
        self._snapshots: Dict[str, AggregateRoot] = {}  # In-memory cache for snapshots
    
    async def save(self, aggregate: AggregateRoot) -> AggregateRoot:
        """
        Save an aggregate by persisting its uncommitted events.
        
        Args:
            aggregate: The aggregate to save
            
        Returns:
            The saved aggregate
        """
        # Apply changes to ensure invariants are checked
        aggregate.apply_changes()
        
        # Collect all domain events from the aggregate
        events = aggregate.clear_events()
        
        # Save each event to the event store
        for event in events:
            # Set the aggregate information on the event if not already set
            if not event.aggregate_id:
                event = event.with_metadata(
                    aggregate_id=str(aggregate.id),
                    aggregate_type=self.aggregate_type.__name__
                )
            
            await self.event_store.append(event)
        
        # Update the snapshot cache
        self._snapshots[str(aggregate.id)] = aggregate
        
        return aggregate
    
    async def get(self, id: str) -> Optional[AggregateRoot]:
        """
        Get an aggregate by ID.
        
        Args:
            id: The aggregate ID
            
        Returns:
            The aggregate if found, None otherwise
        """
        # Check if we have a snapshot in the cache
        if id in self._snapshots:
            return self._snapshots[id]
        
        # Otherwise, rebuild the aggregate from events
        return await self.get_by_id(id)
    
    async def get_by_id(self, id: str) -> Optional[AggregateRoot]:
        """
        Get an aggregate by rebuilding it from its event history.
        
        Args:
            id: The ID of the aggregate to retrieve
            
        Returns:
            The reconstructed aggregate if found, None otherwise
        """
        # Get all events for this aggregate
        events = await self.event_store.get_events(aggregate_id=id)
        
        if not events:
            return None
            
        # Create a new instance of the aggregate
        aggregate = self.aggregate_type(id=id)
        
        # Apply each event to rebuild the aggregate's state
        for event in events:
            self._apply_event(aggregate, event)
        
        # Cache the reconstructed aggregate
        self._snapshots[id] = aggregate
            
        return aggregate
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: Optional[int] = None
    ) -> List[AggregateRoot]:
        """
        List aggregates matching the given filters.
        
        Note: This is not an efficient operation with an event-sourced repository
        as it requires rebuilding each aggregate from its event history.
        
        Args:
            filters: Optional filters to apply
            limit: Optional maximum number of aggregates to return
            
        Returns:
            List of aggregates matching the filters
        """
        # This implementation is simplified and not efficient
        # In a real application, you would use a separate read model
        
        # Get all aggregate IDs (this would need to be optimized in a real application)
        # For now, we'll use a simple approach by querying the event store
        if 'aggregate_type' not in filters:
            filters = filters or {}
            filters['aggregate_type'] = self.aggregate_type.__name__
        
        # Get unique aggregate IDs from the event store
        # This is a placeholder - in a real system, you'd have a more efficient way
        unique_ids = set()
        events = await self.event_store.get_events(**filters)
        for event in events:
            if event.aggregate_id:
                unique_ids.add(event.aggregate_id)
        
        # Limit the number of IDs if specified
        if limit and len(unique_ids) > limit:
            unique_ids = set(list(unique_ids)[:limit])
        
        # Get each aggregate by ID
        aggregates = []
        for aggregate_id in unique_ids:
            aggregate = await self.get_by_id(aggregate_id)
            if aggregate:
                aggregates.append(aggregate)
        
        return aggregates
    
    async def exists(self, id: str) -> bool:
        """
        Check if an aggregate exists.
        
        Args:
            id: The aggregate ID
            
        Returns:
            True if the aggregate exists, False otherwise
        """
        # Check if we have a snapshot or if there are events for this aggregate
        if id in self._snapshots:
            return True
        
        events = await self.event_store.get_events(
            aggregate_id=id, 
            limit=1
        )
        return len(events) > 0
    
    async def remove(self, aggregate: AggregateRoot) -> None:
        """
        Remove an aggregate.
        
        In an event-sourced repository, removal is typically implemented by adding
        a 'deleted' event rather than actually removing the data.
        
        Args:
            aggregate: The aggregate to remove
        """
        # Create a deletion event
        from uno.domain.events import DomainEvent
        
        event = DomainEvent(
            event_type="aggregate_deleted",
            aggregate_id=str(aggregate.id),
            aggregate_type=self.aggregate_type.__name__
        )
        
        # Add the event to the store
        await self.event_store.append(event)
        
        # Remove from snapshot cache
        if str(aggregate.id) in self._snapshots:
            del self._snapshots[str(aggregate.id)]
    
    def _apply_event(self, aggregate: AggregateRoot, event: DomainEvent) -> None:
        """
        Apply an event to an aggregate to update its state.
        
        This method calls the appropriate event handler method on the aggregate.
        
        Args:
            aggregate: The aggregate to apply the event to
            event: The event to apply
        """
        # Determine the event handler method name
        # Convention: apply_[event_type]
        event_type = event.event_type.lower()
        if "." in event_type:
            # If the event type contains dots, use the last part
            event_type = event_type.split(".")[-1]
            
        handler_name = f"apply_{event_type}"
        
        # Call the event handler if it exists
        if hasattr(aggregate, handler_name) and callable(getattr(aggregate, handler_name)):
            try:
                handler = getattr(aggregate, handler_name)
                handler(event)
            except Exception as e:
                self.logger.error(f"Error applying event {event.event_type} to aggregate {aggregate.id}: {e}")
                raise
        else:
            self.logger.warning(f"No handler found for event type {event.event_type} on aggregate {type(aggregate).__name__}")