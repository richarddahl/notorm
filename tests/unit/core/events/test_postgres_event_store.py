"""
Unit tests for the PostgreSQL event store.
"""

import asyncio
import pytest
import json
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch, call

from uno.core.events import Event, PostgresEventStore, PostgresEventStoreConfig
from uno.core.errors import ConcurrencyError


# Test events
class TestEvent(Event):
    """Test event class."""
    data: str


class UserCreated(Event):
    """User created event."""
    user_id: str
    email: str
    username: str


class UserEmailChanged(Event):
    """User email changed event."""
    user_id: str
    old_email: str
    new_email: str


@pytest.fixture
def postgres_config():
    """Create a PostgreSQL event store configuration."""
    return PostgresEventStoreConfig(
        connection_string="postgresql+asyncpg://user:password@localhost:5432/testdb",
        schema="test",
        table_name="test_events",
        create_schema_if_missing=True
    )


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine."""
    engine = AsyncMock()
    
    # Mock begin method to return a connection context manager
    connection = AsyncMock()
    engine.begin.return_value.__aenter__.return_value = connection
    
    # Mock execute method to return results
    connection.execute = AsyncMock()
    connection.execute.return_value = None
    
    # Mock scalar method
    connection.scalar = AsyncMock()
    connection.scalar.side_effect = [True, True]  # schema exists, table exists
    
    # Mock run_sync method
    connection.run_sync = AsyncMock()
    
    return engine


@pytest.fixture
def mock_session_factory():
    """Create a mock SQLAlchemy session factory."""
    session = AsyncMock()
    
    # Mock session context manager
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    session_context.__aexit__.return_value = None
    
    factory = MagicMock()
    factory.return_value = session_context
    
    # Mock execute method to return results
    result = AsyncMock()
    session.execute.return_value = result
    
    # Mock fetchone and fetchall methods
    result.fetchone.return_value = (1,)  # Current version
    result.fetchall.return_value = []  # No events by default
    
    return factory


@pytest.fixture
async def postgres_event_store(postgres_config, mock_engine, mock_session_factory):
    """Create a PostgreSQL event store with mocks."""
    # Create the event store
    store = PostgresEventStore(postgres_config)
    
    # Replace engine and session factory with mocks
    with patch('sqlalchemy.ext.asyncio.create_async_engine', return_value=mock_engine):
        with patch('sqlalchemy.orm.sessionmaker', return_value=mock_session_factory):
            # Initialize the store
            await store.initialize()
            store._engine = mock_engine
            store._async_session_factory = mock_session_factory
            
            yield store


class TestPostgresEventStore:
    """Tests for the PostgresEventStore class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, postgres_event_store):
        """Test initializing the event store."""
        assert postgres_event_store._initialized is True
    
    @pytest.mark.asyncio
    async def test_append_events(self, postgres_event_store, mock_session_factory):
        """Test appending events to the store."""
        # Create test events
        events = [
            TestEvent(
                event_id="1",
                event_type="test_event",
                data="test data 1",
                aggregate_id="123",
                aggregate_type="Test"
            ),
            TestEvent(
                event_id="2",
                event_type="test_event",
                data="test data 2",
                aggregate_id="123",
                aggregate_type="Test"
            )
        ]
        
        # Append events
        version = await postgres_event_store.append_events(events)
        
        # Assert session was used
        assert mock_session_factory.called
        
        # Assert version was incremented
        assert version == 2
    
    @pytest.mark.asyncio
    async def test_append_events_with_concurrency(self, postgres_event_store, mock_session_factory):
        """Test appending events with optimistic concurrency."""
        # Set up the mock to return version 2
        session = mock_session_factory.return_value.__aenter__.return_value
        result = session.execute.return_value
        result.fetchone.return_value = (2,)  # Current version is 2
        
        # Create test event
        event = TestEvent(
            event_id="1",
            event_type="test_event",
            data="test data",
            aggregate_id="123",
            aggregate_type="Test"
        )
        
        # Try to append with expected version 1 (should fail)
        with pytest.raises(ConcurrencyError):
            await postgres_event_store.append_events([event], expected_version=1)
    
    @pytest.mark.asyncio
    async def test_get_events_by_aggregate(self, postgres_event_store, mock_session_factory):
        """Test getting events by aggregate ID."""
        # Set up mock to return events
        session = mock_session_factory.return_value.__aenter__.return_value
        
        # Create mock events as rows
        row1 = {
            "event_id": "1",
            "event_type": "test_event",
            "occurred_at": datetime.now(UTC),
            "correlation_id": None,
            "causation_id": None,
            "aggregate_id": "123",
            "aggregate_type": "Test",
            "aggregate_version": 1,
            "data": {"data": "test data 1"}
        }
        
        row2 = {
            "event_id": "2",
            "event_type": "test_event",
            "occurred_at": datetime.now(UTC),
            "correlation_id": None,
            "causation_id": None,
            "aggregate_id": "123",
            "aggregate_type": "Test",
            "aggregate_version": 2,
            "data": {"data": "test data 2"}
        }
        
        # Mock rows with _mapping attribute
        mock_row1 = MagicMock()
        mock_row1._mapping = row1
        
        mock_row2 = MagicMock()
        mock_row2._mapping = row2
        
        result = session.execute.return_value
        result.fetchall.return_value = [mock_row1, mock_row2]
        
        # Get events by aggregate
        events = await postgres_event_store.get_events_by_aggregate("123")
        
        # Assert we got the right number of events
        assert len(events) == 2
        
        # Assert event data was parsed correctly
        assert events[0].event_id == "1"
        assert events[0].data == "test data 1"
        assert events[1].event_id == "2"
        assert events[1].data == "test data 2"
    
    @pytest.mark.asyncio
    async def test_get_events_by_type(self, postgres_event_store, mock_session_factory):
        """Test getting events by type."""
        # Set up mock to return events
        session = mock_session_factory.return_value.__aenter__.return_value
        
        # Create mock events as rows
        row1 = {
            "event_id": "1",
            "event_type": "user_created",
            "occurred_at": datetime.now(UTC),
            "correlation_id": None,
            "causation_id": None,
            "aggregate_id": "123",
            "aggregate_type": "User",
            "aggregate_version": 1,
            "data": {"user_id": "123", "email": "user@example.com", "username": "testuser"}
        }
        
        # Mock rows with _mapping attribute
        mock_row1 = MagicMock()
        mock_row1._mapping = row1
        
        result = session.execute.return_value
        result.fetchall.return_value = [mock_row1]
        
        # Get events by type
        events = await postgres_event_store.get_events_by_type("user_created")
        
        # Assert we got the right number of events
        assert len(events) == 1
        
        # Assert event data was parsed correctly
        assert events[0].event_id == "1"
        assert events[0].event_type == "user_created"
    
    @pytest.mark.asyncio
    async def test_get_aggregate_version(self, postgres_event_store, mock_session_factory):
        """Test getting the aggregate version."""
        # Set up mock to return version
        session = mock_session_factory.return_value.__aenter__.return_value
        result = session.execute.return_value
        result.fetchone.return_value = (5,)  # Current version is 5
        
        # Get version
        version = await postgres_event_store.get_aggregate_version("123")
        
        # Assert version is correct
        assert version == 5
    
    @pytest.mark.asyncio
    async def test_event_to_dict_and_row_to_event(self, postgres_event_store):
        """Test converting between events and dictionaries/rows."""
        # Create an event
        event = UserCreated(
            event_id="1",
            user_id="123",
            email="user@example.com",
            username="testuser",
            aggregate_id="123",
            aggregate_type="User",
            aggregate_version=1
        )
        
        # Convert to dict
        event_dict = postgres_event_store._event_to_dict(event)
        
        # Check dict has the right fields
        assert event_dict["event_id"] == "1"
        assert event_dict["user_id"] == "123"
        assert event_dict["email"] == "user@example.com"
        assert event_dict["username"] == "testuser"
        assert event_dict["aggregate_id"] == "123"
        assert event_dict["aggregate_type"] == "User"
        assert event_dict["aggregate_version"] == 1
        
        # Create a mock row
        row = MagicMock()
        row._mapping = {
            "event_id": "1",
            "event_type": "user_created",
            "occurred_at": datetime.now(UTC),
            "correlation_id": None,
            "causation_id": None,
            "aggregate_id": "123",
            "aggregate_type": "User",
            "aggregate_version": 1,
            "data": {
                "user_id": "123", 
                "email": "user@example.com", 
                "username": "testuser"
            }
        }
        
        # Convert row to event
        recreated_event = postgres_event_store._row_to_event(row)
        
        # Check event has the right fields
        assert recreated_event.event_id == "1"
        assert recreated_event.event_type == "user_created"
        assert recreated_event.aggregate_id == "123"
        assert recreated_event.aggregate_type == "User"
        assert recreated_event.aggregate_version == 1
        assert recreated_event.user_id == "123"
        assert recreated_event.email == "user@example.com"
        assert recreated_event.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_real_event_sourcing_flow(self, postgres_event_store, mock_session_factory):
        """Test a realistic event sourcing flow."""
        # 1. Create a user
        create_event = UserCreated(
            event_id="1",
            user_id="123",
            email="user@example.com",
            username="testuser",
            aggregate_id="123",
            aggregate_type="User"
        )
        
        # Set up mock to report version 0 initially
        session = mock_session_factory.return_value.__aenter__.return_value
        result = session.execute.return_value
        result.fetchone.return_value = None  # No current version
        
        # Store the event
        version = await postgres_event_store.append_events([create_event])
        assert version == 1
        
        # 2. Update the user's email
        # Now mock reports version 1
        result.fetchone.return_value = (1,)
        
        update_event = UserEmailChanged(
            event_id="2",
            user_id="123",
            old_email="user@example.com",
            new_email="new@example.com",
            aggregate_id="123",
            aggregate_type="User"
        )
        
        # Store with optimistic concurrency
        version = await postgres_event_store.append_events([update_event], expected_version=1)
        assert version == 2
        
        # 3. Load all events for the user
        # Mock returning both events
        mock_row1 = MagicMock()
        mock_row1._mapping = {
            "event_id": "1",
            "event_type": "user_created",
            "occurred_at": datetime.now(UTC),
            "aggregate_id": "123",
            "aggregate_type": "User",
            "aggregate_version": 1,
            "data": {"user_id": "123", "email": "user@example.com", "username": "testuser"}
        }
        
        mock_row2 = MagicMock()
        mock_row2._mapping = {
            "event_id": "2",
            "event_type": "user_email_changed",
            "occurred_at": datetime.now(UTC),
            "aggregate_id": "123",
            "aggregate_type": "User",
            "aggregate_version": 2,
            "data": {"user_id": "123", "old_email": "user@example.com", "new_email": "new@example.com"}
        }
        
        result.fetchall.return_value = [mock_row1, mock_row2]
        
        # Get events
        events = await postgres_event_store.get_events_by_aggregate("123")
        
        # Verify events
        assert len(events) == 2
        assert events[0].event_type == "user_created"
        assert events[1].event_type == "user_email_changed"
        
        # 4. Reconstruct user state from events
        user_id = None
        username = None
        email = None
        
        for event in events:
            if isinstance(event, UserCreated):
                user_id = event.user_id
                username = event.username
                email = event.email
            elif isinstance(event, UserEmailChanged):
                email = event.new_email
        
        # Verify user state
        assert user_id == "123"
        assert username == "testuser"
        assert email == "new@example.com"