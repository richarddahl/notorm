"""
Unit tests for the domain event store implementations.
"""

import pytest
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import Table, MetaData

from uno.domain.core import DomainEvent, Entity, AggregateRoot
from uno.domain.event_store import EventStore, PostgresEventStore, EventSourcedRepository


class TestEvent(DomainEvent):
    """Test event for event store tests."""
    aggregate_id: str
    aggregate_type: str = "TestAggregate"
    data: Dict[str, Any] = {}


class TestAggregate(AggregateRoot):
    """Test aggregate for event sourcing tests."""
    name: str
    counter: int = 0
    
    def apply_test_increment(self, event: TestEvent) -> None:
        """Apply a test increment event."""
        self.counter += 1
        
    def apply_test_rename(self, event: TestEvent) -> None:
        """Apply a test rename event."""
        self.name = event.data.get("name", self.name)
        
    def apply_test_reset(self, event: TestEvent) -> None:
        """Apply a test reset event."""
        self.counter = 0
        

@pytest.fixture
def test_event():
    """Create a test event for tests."""
    return TestEvent(
        event_id="event-123",
        event_type="test_increment",
        aggregate_id="aggregate-123",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        data={"value": 1}
    )


@pytest.fixture
def mock_session():
    """Create a mock session for PostgreSQL tests."""
    session = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    session_context.__aexit__.return_value = None
    return session_context


@pytest.fixture
def mock_session_factory(mock_session):
    """Create a mock session factory."""
    with patch('uno.domain.event_store.async_session', return_value=mock_session):
        yield


class TestPostgresEventStore:
    """Test the PostgreSQL event store implementation."""
    
    def test_init(self):
        """Test event store initialization."""
        store = PostgresEventStore(TestEvent)
        assert store.event_type == TestEvent
        assert store.table_name == 'domain_events'
        assert store.schema == 'public'
        assert isinstance(store.events_table, Table)
        
        # Custom parameters
        store = PostgresEventStore(
            TestEvent,
            table_name='custom_events',
            schema='test_schema'
        )
        assert store.table_name == 'custom_events'
        assert store.schema == 'test_schema'
    
    @pytest.mark.asyncio
    async def test_save_event(self, test_event, mock_session_factory, mock_session):
        """Test saving an event."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Create event store
        store = PostgresEventStore(TestEvent)
        
        # Save event
        await store.save_event(test_event)
        
        # Check that the session was used correctly
        session.execute.assert_called_once()
        session.commit.assert_called_once()
        
        # Verify the insert statement
        call_args = session.execute.call_args
        assert call_args is not None
        
        # Insert statement contains correct values
        insert_stmt = call_args.args[0]
        assert "INSERT INTO" in str(insert_stmt).upper()
        assert "domain_events" in str(insert_stmt).lower()
    
    @pytest.mark.asyncio
    async def test_save_event_with_metadata(self, test_event, mock_session_factory, mock_session):
        """Test saving an event with metadata."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Create event store
        store = PostgresEventStore(TestEvent)
        
        # Save event with metadata
        await store.save_event(
            test_event,
            aggregate_id="custom-aggregate-id",
            metadata={"user_id": "user-123", "ip": "127.0.0.1"}
        )
        
        # Check that the session was used correctly
        session.execute.assert_called_once()
        session.commit.assert_called_once()
        
        # Verify the insert statement
        call_args = session.execute.call_args
        assert call_args is not None
        
        # Insert statement contains correct values
        insert_stmt = call_args.args[0]
        assert "INSERT INTO" in str(insert_stmt).upper()
        assert "domain_events" in str(insert_stmt).lower()
    
    @pytest.mark.asyncio
    async def test_get_events_by_aggregate_id(self, mock_session_factory, mock_session):
        """Test getting events by aggregate ID."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Mock query result
        result = AsyncMock()
        result.fetchall.return_value = [
            MagicMock(
                event_id="event-1",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                data=json.dumps({"value": 1})
            ),
            MagicMock(
                event_id="event-2",
                event_type="test_rename",
                aggregate_id="aggregate-123",
                timestamp=datetime(2023, 1, 1, 12, 1, 0),
                data=json.dumps({"name": "New Name"})
            )
        ]
        session.execute.return_value = result
        
        # Create event store
        store = PostgresEventStore(TestEvent)
        
        # Get events
        events = await store.get_events_by_aggregate_id("aggregate-123")
        
        # Check that the session was used correctly
        session.execute.assert_called_once()
        
        # Verify the query
        call_args = session.execute.call_args
        assert call_args is not None
        
        # Query contains correct values
        select_stmt = call_args.args[0]
        assert "SELECT" in str(select_stmt).upper()
        assert "domain_events" in str(select_stmt).lower()
        assert "aggregate_id" in str(select_stmt).lower()
        
        # Check results
        assert len(events) == 2
        assert all(isinstance(e, TestEvent) for e in events)
        assert events[0].event_id == "event-1"
        assert events[0].event_type == "test_increment"
        assert events[1].event_id == "event-2"
        assert events[1].event_type == "test_rename"
    
    @pytest.mark.asyncio
    async def test_get_events_by_aggregate_id_with_event_types(self, mock_session_factory, mock_session):
        """Test getting events by aggregate ID and event types."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Mock query result
        result = AsyncMock()
        result.fetchall.return_value = [
            MagicMock(
                event_id="event-1",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                data=json.dumps({"value": 1})
            )
        ]
        session.execute.return_value = result
        
        # Create event store
        store = PostgresEventStore(TestEvent)
        
        # Get events with specific types
        events = await store.get_events_by_aggregate_id(
            "aggregate-123",
            event_types=["test_increment"]
        )
        
        # Check that the session was used correctly
        session.execute.assert_called_once()
        
        # Verify the query
        call_args = session.execute.call_args
        assert call_args is not None
        
        # Query contains correct values
        select_stmt = call_args.args[0]
        assert "SELECT" in str(select_stmt).upper()
        assert "domain_events" in str(select_stmt).lower()
        assert "aggregate_id" in str(select_stmt).lower()
        assert "event_type" in str(select_stmt).lower()
        
        # Check results
        assert len(events) == 1
        assert events[0].event_id == "event-1"
        assert events[0].event_type == "test_increment"
    
    @pytest.mark.asyncio
    async def test_get_events_by_type(self, mock_session_factory, mock_session):
        """Test getting events by type."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Mock query result
        result = AsyncMock()
        result.fetchall.return_value = [
            MagicMock(
                event_id="event-1",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                data=json.dumps({"value": 1})
            ),
            MagicMock(
                event_id="event-2",
                event_type="test_increment",
                aggregate_id="aggregate-456",
                timestamp=datetime(2023, 1, 1, 12, 1, 0),
                data=json.dumps({"value": 2})
            )
        ]
        session.execute.return_value = result
        
        # Create event store
        store = PostgresEventStore(TestEvent)
        
        # Get events
        events = await store.get_events_by_type("test_increment")
        
        # Check that the session was used correctly
        session.execute.assert_called_once()
        
        # Verify the query
        call_args = session.execute.call_args
        assert call_args is not None
        
        # Query contains correct values
        select_stmt = call_args.args[0]
        assert "SELECT" in str(select_stmt).upper()
        assert "domain_events" in str(select_stmt).lower()
        assert "event_type" in str(select_stmt).lower()
        
        # Check results
        assert len(events) == 2
        assert all(isinstance(e, TestEvent) for e in events)
        assert all(e.event_type == "test_increment" for e in events)
        assert events[0].aggregate_id == "aggregate-123"
        assert events[1].aggregate_id == "aggregate-456"
    
    @pytest.mark.asyncio
    async def test_get_events_by_type_with_since(self, mock_session_factory, mock_session):
        """Test getting events by type with a timestamp filter."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Mock query result
        result = AsyncMock()
        result.fetchall.return_value = [
            MagicMock(
                event_id="event-2",
                event_type="test_increment",
                aggregate_id="aggregate-456",
                timestamp=datetime(2023, 1, 1, 12, 1, 0),
                data=json.dumps({"value": 2})
            )
        ]
        session.execute.return_value = result
        
        # Create event store
        store = PostgresEventStore(TestEvent)
        
        # Get events since a specific time
        since = datetime(2023, 1, 1, 12, 0, 30)
        events = await store.get_events_by_type("test_increment", since=since)
        
        # Check that the session was used correctly
        session.execute.assert_called_once()
        
        # Verify the query
        call_args = session.execute.call_args
        assert call_args is not None
        
        # Query contains correct values
        select_stmt = call_args.args[0]
        assert "SELECT" in str(select_stmt).upper()
        assert "domain_events" in str(select_stmt).lower()
        assert "event_type" in str(select_stmt).lower()
        assert "timestamp" in str(select_stmt).lower()
        
        # Check results
        assert len(events) == 1
        assert events[0].event_id == "event-2"
        assert events[0].timestamp > since


class TestEventSourcedRepository:
    """Test the event-sourced repository implementation."""
    
    @pytest.fixture
    def mock_event_store(self):
        """Create a mock event store."""
        store = AsyncMock(spec=EventStore)
        return store
    
    @pytest.fixture
    def repository(self, mock_event_store):
        """Create an event-sourced repository."""
        return EventSourcedRepository(TestAggregate, mock_event_store)
    
    @pytest.mark.asyncio
    async def test_save(self, repository, mock_event_store, test_event):
        """Test saving an aggregate."""
        # Create aggregate with events
        aggregate = TestAggregate(id="aggregate-123", name="Test Aggregate")
        aggregate.add_event(test_event)
        
        # Additional event
        event2 = TestEvent(
            event_id="event-456",
            event_type="test_rename",
            aggregate_id="aggregate-123",
            data={"name": "New Name"}
        )
        aggregate.add_event(event2)
        
        # Save aggregate
        await repository.save(aggregate)
        
        # Check that events were saved
        assert mock_event_store.save_event.call_count == 2
        
        # Events should be cleared from aggregate
        assert len(aggregate.clear_events()) == 0
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, repository, mock_event_store):
        """Test getting an aggregate by ID."""
        # Mock event store response
        mock_event_store.get_events_by_aggregate_id.return_value = [
            TestEvent(
                event_id="event-1",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                aggregate_type="TestAggregate",
                data={}
            ),
            TestEvent(
                event_id="event-2",
                event_type="test_rename",
                aggregate_id="aggregate-123",
                aggregate_type="TestAggregate",
                data={"name": "New Name"}
            ),
            TestEvent(
                event_id="event-3",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                aggregate_type="TestAggregate",
                data={}
            )
        ]
        
        # Get aggregate
        aggregate = await repository.get_by_id("aggregate-123")
        
        # Check that event store was called correctly
        mock_event_store.get_events_by_aggregate_id.assert_called_once_with("aggregate-123")
        
        # Check reconstituted aggregate
        assert aggregate is not None
        assert aggregate.id == "aggregate-123"
        assert aggregate.name == "New Name"
        assert aggregate.counter == 2  # Incremented twice
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_event_store):
        """Test getting a non-existent aggregate."""
        # Mock empty event store response
        mock_event_store.get_events_by_aggregate_id.return_value = []
        
        # Get aggregate
        aggregate = await repository.get_by_id("nonexistent-id")
        
        # Check that event store was called correctly
        mock_event_store.get_events_by_aggregate_id.assert_called_once_with("nonexistent-id")
        
        # Should return None if no events found
        assert aggregate is None
    
    @pytest.mark.asyncio
    async def test_apply_events(self, repository):
        """Test applying events to an aggregate."""
        # Create an aggregate
        aggregate = TestAggregate(id="aggregate-123", name="Test Aggregate")
        
        # Create events
        events = [
            TestEvent(
                event_id="event-1",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                data={}
            ),
            TestEvent(
                event_id="event-2",
                event_type="test_rename",
                aggregate_id="aggregate-123",
                data={"name": "New Name"}
            ),
            TestEvent(
                event_id="event-3",
                event_type="test_reset",
                aggregate_id="aggregate-123",
                data={}
            ),
            TestEvent(
                event_id="event-4",
                event_type="test_increment",
                aggregate_id="aggregate-123",
                data={}
            )
        ]
        
        # Apply events
        for event in events:
            repository._apply_event(aggregate, event)
        
        # Check aggregate state
        assert aggregate.name == "New Name"
        assert aggregate.counter == 1  # Incremented, then reset, then incremented again
    
    @pytest.mark.asyncio
    async def test_unknown_event_type(self, repository):
        """Test handling unknown event types."""
        # Create an aggregate
        aggregate = TestAggregate(id="aggregate-123", name="Test Aggregate")
        
        # Create event with unknown type
        event = TestEvent(
            event_id="event-1",
            event_type="unknown_event",
            aggregate_id="aggregate-123",
            data={}
        )
        
        # Apply event - should log warning but not error
        with patch('logging.Logger.warning') as mock_warning:
            repository._apply_event(aggregate, event)
            mock_warning.assert_called_once()
        
        # Aggregate state should be unchanged
        assert aggregate.name == "Test Aggregate"
        assert aggregate.counter == 0