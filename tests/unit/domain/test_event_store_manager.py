"""
Unit tests for the domain event store manager.
"""

import pytest
import json
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch, Mock, ANY

from sqlalchemy import Table, MetaData

from uno.domain.event_store_manager import EventStoreManager
from uno.domain.events import DomainEvent


class TestEvent(DomainEvent):
    """Test event for event store tests."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    def with_metadata(self, **kwargs):
        """Add metadata to the event and return a new instance."""
        # Create a copy with the updated fields
        data = self.model_dump()
        data.update(kwargs)
        return self.__class__(**data)


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
    # We need to patch the actual function imported in event_store_manager.py
    with patch("uno.domain.event_store_manager.async_session", return_value=mock_session):
        yield


@pytest.fixture
def test_manager():
    """Create an event store manager for testing."""
    with patch("uno.domain.event_store_manager.uno_settings") as mock_settings:
        mock_settings.DB_SCHEMA = "test_schema"
        mock_settings.DB_NAME = "test_db"
        manager = EventStoreManager(logger=None)
        return manager


class TestEventStoreManager:
    """Test the event store manager implementation."""

    def test_init(self, test_manager):
        """Test manager initialization."""
        assert test_manager.logger is not None
        assert test_manager.config is not None

    def test_generate_event_store_sql(self, test_manager):
        """Test SQL generation."""
        # Should generate SQL statements for the schema
        with patch("uno.sql.emitters.event_store.SQLEmitter.generate_sql") as mock_generate:
            mock_generate.return_value = []
            statements = test_manager._generate_event_store_sql()
            assert isinstance(statements, list)
            
            # Should have created the emitters
            assert mock_generate.call_count > 0

    @patch("uno.domain.event_store_manager.psycopg")
    def test_create_event_store_schema(self, mock_psycopg, test_manager):
        """Test schema creation."""
        # Mock the SQL generation
        with patch.object(test_manager, "_generate_event_store_sql") as mock_generate:
            mock_generate.return_value = [
                MagicMock(name="stmt1", sql="CREATE TABLE test"),
                MagicMock(name="stmt2", sql="CREATE FUNCTION test"),
            ]
            
            # Mock the connection
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_psycopg.connect.return_value = mock_conn
            
            # Call the method
            test_manager.create_event_store_schema()
            
            # Should have connected to the database
            mock_psycopg.connect.assert_called_once()
            
            # Should have executed the SQL statements
            assert mock_cursor.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_event_counts(self, test_manager, mock_session_factory, mock_session):
        """Test getting event counts."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        session.execute.return_value.fetchall.return_value = [
            ("test_increment", 10),
            ("test_rename", 5),
        ]
        
        # Call the method
        counts = await test_manager.get_event_counts()
        
        # Check results
        assert counts["test_increment"] == 10
        assert counts["test_rename"] == 5
        
        # Should have executed a query
        session.execute.assert_called_once()
        assert "SELECT event_type, COUNT(*)" in session.execute.call_args.args[0]

    @pytest.mark.asyncio
    async def test_get_aggregate_counts(self, test_manager, mock_session_factory, mock_session):
        """Test getting aggregate counts."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        session.execute.return_value.fetchall.return_value = [
            ("TestAggregate", 3),
            ("OtherAggregate", 2),
        ]
        
        # Call the method
        counts = await test_manager.get_aggregate_counts()
        
        # Check results
        assert counts["TestAggregate"] == 3
        assert counts["OtherAggregate"] == 2
        
        # Should have executed a query
        session.execute.assert_called_once()
        assert "SELECT aggregate_type, COUNT(DISTINCT aggregate_id)" in session.execute.call_args.args[0]

    @pytest.mark.asyncio
    async def test_create_snapshot(self, test_manager, mock_session_factory, mock_session):
        """Test creating a snapshot."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        
        # Aggregate data
        aggregate_id = "test-123"
        aggregate_type = "TestAggregate"
        version = 5
        state = {"name": "Test", "counter": 5}
        
        # Call the method
        await test_manager.create_snapshot(aggregate_id, aggregate_type, version, state)
        
        # Should have executed a query
        session.execute.assert_called_once()
        assert "INSERT INTO" in session.execute.call_args.args[0]
        assert "ON CONFLICT" in session.execute.call_args.args[0]
        
        # Should have committed the transaction
        session.commit.assert_called_once()
        
        # Check the parameters
        params = session.execute.call_args.args[1]
        assert params["aggregate_id"] == aggregate_id
        assert params["aggregate_type"] == aggregate_type
        assert params["version"] == version
        assert "state" in params

    @pytest.mark.asyncio
    async def test_get_snapshot(self, test_manager, mock_session_factory, mock_session):
        """Test getting a snapshot."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        state_json = '{"name": "Test", "counter": 5}'
        session.execute.return_value.fetchone.return_value = (5, state_json)
        
        # Aggregate data
        aggregate_id = "test-123"
        aggregate_type = "TestAggregate"
        
        # Call the method
        result = await test_manager.get_snapshot(aggregate_id, aggregate_type)
        
        # Should have executed a query
        session.execute.assert_called_once()
        assert "SELECT version, state" in session.execute.call_args.args[0]
        
        # Check the parameters
        params = session.execute.call_args.args[1]
        assert params["aggregate_id"] == aggregate_id
        assert params["aggregate_type"] == aggregate_type
        
        # Check the result
        assert result is not None
        version, state = result
        assert version == 5
        assert state["name"] == "Test"
        assert state["counter"] == 5

    @pytest.mark.asyncio
    async def test_get_snapshot_not_found(self, test_manager, mock_session_factory, mock_session):
        """Test getting a non-existent snapshot."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        session.execute.return_value.fetchone.return_value = None
        
        # Aggregate data
        aggregate_id = "nonexistent"
        aggregate_type = "TestAggregate"
        
        # Call the method
        result = await test_manager.get_snapshot(aggregate_id, aggregate_type)
        
        # Should have executed a query
        session.execute.assert_called_once()
        
        # Should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, test_manager, mock_session_factory, mock_session):
        """Test cleaning up old events."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        session.execute.return_value.fetchall.return_value = [("event-1",), ("event-2",)]
        
        # Call the method
        count = await test_manager.cleanup_old_events(days_to_keep=30)
        
        # Should have executed a query
        session.execute.assert_called_once()
        assert "DELETE FROM" in session.execute.call_args.args[0]
        assert "WHERE created_at < NOW() - INTERVAL" in session.execute.call_args.args[0]
        
        # Should have committed the transaction
        session.commit.assert_called_once()
        
        # Should return the count of deleted events
        assert count == 2

    @pytest.mark.asyncio
    async def test_cleanup_old_events_with_event_types(self, test_manager, mock_session_factory, mock_session):
        """Test cleaning up old events with event type filter."""
        # Configure mock session
        session = mock_session.__aenter__.return_value
        session.execute.return_value.fetchall.return_value = [("event-1",)]
        
        # Call the method with event types
        count = await test_manager.cleanup_old_events(days_to_keep=30, event_types=["test_event"])
        
        # Should have executed a query
        session.execute.assert_called_once()
        assert "DELETE FROM" in session.execute.call_args.args[0]
        assert "AND event_type IN" in session.execute.call_args.args[0]
        
        # Should have committed the transaction
        session.commit.assert_called_once()
        
        # Should return the count of deleted events
        assert count == 1