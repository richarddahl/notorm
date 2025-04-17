"""
Unit tests for the event store integration.
"""

import pytest
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from uno.domain.events import DomainEvent, EventBus, EventStore
from uno.domain.models import AggregateRoot
from uno.domain.event_store import EventSourcedRepository
from uno.domain.event_store_integration import (
    EventStoreIntegration,
    get_event_store_integration,
    get_event_sourced_repository,
)
from uno.core.result import Result


class TestEvent(DomainEvent):
    """Test event for integration tests."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    aggregate_id: str
    aggregate_type: str = "TestAggregate"
    data: Dict[str, Any] = {}


class TestAggregate(AggregateRoot):
    """Test aggregate for integration tests."""

    __test__ = False  # Prevent pytest from collecting this class as a test
    name: str = "Default Name"
    counter: int = 0

    def apply_test_increment(self, event: TestEvent) -> None:
        """Apply a test increment event."""
        self.counter += 1


@pytest.fixture
def test_event():
    """Create a test event."""
    return TestEvent(
        event_id=str(uuid.uuid4()),
        event_type="test_increment",
        aggregate_id="aggregate-123",
        timestamp=datetime.now(UTC),
        data={"value": 1},
    )


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = AsyncMock(spec=EventBus)
    return bus


@pytest.fixture
def mock_event_store():
    """Create a mock event store."""
    store = AsyncMock(spec=EventStore)
    return store


@pytest.fixture
def integration(mock_event_bus, mock_event_store):
    """Create an event store integration instance."""
    with patch("uno.domain.event_store_integration.EventStoreManager") as mock_manager:
        integration = EventStoreIntegration(
            event_bus=mock_event_bus, event_store=mock_event_store
        )
        return integration


class TestEventStoreIntegration:
    """Test the event store integration."""

    def test_init(self, integration, mock_event_bus, mock_event_store):
        """Test initialization."""
        assert integration.event_bus is mock_event_bus
        assert integration.event_store is mock_event_store
        assert integration.logger is not None
        assert integration.publisher is not None

    @pytest.mark.asyncio
    async def test_initialize(self, integration):
        """Test initialization of the event store."""
        # Mock the schema creation
        with patch.object(
            integration.store_manager, "create_event_store_schema"
        ) as mock_create:
            await integration.initialize()
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_error(self, integration):
        """Test error handling during initialization."""
        # Mock schema creation to raise an error
        with patch.object(
            integration.store_manager, "create_event_store_schema"
        ) as mock_create:
            mock_create.side_effect = Exception("Test error")

            # Should raise the exception
            with pytest.raises(Exception, match="Test error"):
                await integration.initialize()

    @pytest.mark.asyncio
    async def test_publish_event(self, integration, test_event):
        """Test publishing an event."""
        result = await integration.publish_event(test_event)

        # Should have published the event
        integration.publisher.publish.assert_called_once_with(test_event)

        # Should return success
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_publish_event_error(self, integration, test_event):
        """Test error handling when publishing an event."""
        # Mock publisher to raise an error
        integration.publisher.publish.side_effect = Exception("Test error")

        # Call the method
        result = await integration.publish_event(test_event)

        # Should return failure
        assert result.is_failure()
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_publish_events(self, integration, test_event):
        """Test publishing multiple events."""
        events = [test_event, test_event]
        result = await integration.publish_events(events)

        # Should have published the events
        integration.publisher.publish_many.assert_called_once_with(events)

        # Should return success
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_publish_events_error(self, integration, test_event):
        """Test error handling when publishing multiple events."""
        # Mock publisher to raise an error
        integration.publisher.publish_many.side_effect = Exception("Test error")

        # Call the method
        events = [test_event, test_event]
        result = await integration.publish_events(events)

        # Should return failure
        assert result.is_failure()
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, integration, test_event, mock_event_store):
        """Test getting events by type."""
        # Mock event store response
        mock_event_store.get_events_by_type.return_value = [test_event]

        # Call the method
        events = await integration.get_events_by_type("test_increment")

        # Should have called the event store
        mock_event_store.get_events_by_type.assert_called_once_with(
            "test_increment", None
        )

        # Should return the events
        assert len(events) == 1
        assert events[0] is test_event

    @pytest.mark.asyncio
    async def test_get_events_by_type_error(self, integration, mock_event_store):
        """Test error handling when getting events by type."""
        # Mock event store to raise an error
        mock_event_store.get_events_by_type.side_effect = Exception("Test error")

        # Call the method
        events = await integration.get_events_by_type("test_increment")

        # Should return empty list
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_get_events_by_aggregate(
        self, integration, test_event, mock_event_store
    ):
        """Test getting events by aggregate."""
        # Mock event store response
        mock_event_store.get_events_by_aggregate_id.return_value = [test_event]

        # Call the method
        events = await integration.get_events_by_aggregate("aggregate-123")

        # Should have called the event store
        mock_event_store.get_events_by_aggregate_id.assert_called_once_with(
            "aggregate-123", None
        )

        # Should return the events
        assert len(events) == 1
        assert events[0] is test_event

    @pytest.mark.asyncio
    async def test_get_events_by_aggregate_error(self, integration, mock_event_store):
        """Test error handling when getting events by aggregate."""
        # Mock event store to raise an error
        mock_event_store.get_events_by_aggregate_id.side_effect = Exception(
            "Test error"
        )

        # Call the method
        events = await integration.get_events_by_aggregate("aggregate-123")

        # Should return empty list
        assert len(events) == 0

    def test_get_repository(self, integration):
        """Test getting a repository."""
        repository = integration.get_repository(TestAggregate)

        # Should return a repository of the correct type
        assert isinstance(repository, EventSourcedRepository)
        assert repository.aggregate_type is TestAggregate
        assert repository.event_store is integration.event_store

    def test_create_event_store(self, integration):
        """Test creating an event store."""
        with patch(
            "uno.domain.event_store_integration.PostgresEventStore"
        ) as mock_store:
            store = EventStoreIntegration.create_event_store(
                TestEvent, schema="test_schema"
            )
            mock_store.assert_called_once_with(TestEvent, schema="test_schema")


class TestHelperFunctions:
    """Test the helper functions."""

    def test_get_event_store_integration(self):
        """Test getting the default integration."""
        integration = get_event_store_integration()
        assert isinstance(integration, EventStoreIntegration)

    @patch("uno.core.di.inject_dependency")
    def test_get_event_sourced_repository(self, mock_inject):
        """Test getting an event-sourced repository."""
        # Mock the integration
        mock_integration = AsyncMock(spec=EventStoreIntegration)
        mock_repository = AsyncMock(spec=EventSourcedRepository)
        mock_integration.get_repository.return_value = mock_repository

        # Call the function
        repository = get_event_sourced_repository(
            TestAggregate, integration=mock_integration
        )

        # Should have called get_repository
        mock_integration.get_repository.assert_called_once_with(TestAggregate)

        # Should return the repository
        assert repository is mock_repository
