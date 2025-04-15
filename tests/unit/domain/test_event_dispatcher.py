"""
Unit tests for the domain event dispatcher.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch, call

from uno.domain.core import DomainEvent
from uno.domain.event_store import EventStore
from uno.domain.event_dispatcher import (
    EventDispatcher,
    PostgresEventListener,
    EventHandler,
    domain_event_handler,
    EventSubscriber,
)


class TestEvent(DomainEvent):
    """Test event for event dispatcher tests."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    aggregate_id: str
    data: Dict[str, Any] = {}


@pytest.fixture
def test_event():
    """Create a test event for tests."""
    return TestEvent(
        event_id="event-123",
        event_type="test_event",
        aggregate_id="aggregate-123",
        data={"value": 1},
    )


@pytest.fixture
def mock_event_store():
    """Create a mock event store."""
    store = AsyncMock(spec=EventStore)
    return store


@pytest.fixture
def dispatcher(mock_event_store):
    """Create an event dispatcher with a mock event store."""
    return EventDispatcher(event_store=mock_event_store)


class TestEventDispatcher:
    """Test the event dispatcher implementation."""

    def test_init(self, mock_event_store):
        """Test dispatcher initialization."""
        dispatcher = EventDispatcher(event_store=mock_event_store)
        assert dispatcher.event_store == mock_event_store
        assert dispatcher._handlers == {}
        assert dispatcher._wildcard_handlers == []

    def test_subscribe(self, dispatcher):
        """Test subscribing handlers to event types."""
        # Create mock handlers
        handler1 = AsyncMock()
        handler1.__name__ = "handler1"
        handler2 = AsyncMock()
        handler2.__name__ = "handler2"
        wildcard_handler = AsyncMock()
        wildcard_handler.__name__ = "wildcard_handler"

        # Subscribe handlers
        dispatcher.subscribe("test_event", handler1)
        dispatcher.subscribe("test_event", handler2)
        dispatcher.subscribe("other_event", handler1)
        dispatcher.subscribe("*", wildcard_handler)

        # Check handler registration
        assert len(dispatcher._handlers) == 2
        assert len(dispatcher._handlers["test_event"]) == 2
        assert len(dispatcher._handlers["other_event"]) == 1
        assert len(dispatcher._wildcard_handlers) == 1

        assert handler1 in dispatcher._handlers["test_event"]
        assert handler2 in dispatcher._handlers["test_event"]
        assert handler1 in dispatcher._handlers["other_event"]
        assert wildcard_handler in dispatcher._wildcard_handlers

    def test_unsubscribe(self, dispatcher):
        """Test unsubscribing handlers from event types."""
        # Create mock handlers
        handler1 = AsyncMock()
        handler1.__name__ = "handler1"
        handler2 = AsyncMock()
        handler2.__name__ = "handler2"
        wildcard_handler = AsyncMock()
        wildcard_handler.__name__ = "wildcard_handler"

        # Subscribe handlers
        dispatcher.subscribe("test_event", handler1)
        dispatcher.subscribe("test_event", handler2)
        dispatcher.subscribe("*", wildcard_handler)

        # Unsubscribe handlers
        dispatcher.unsubscribe("test_event", handler1)
        dispatcher.unsubscribe("*", wildcard_handler)

        # Check handler registration
        assert len(dispatcher._handlers["test_event"]) == 1
        assert handler1 not in dispatcher._handlers["test_event"]
        assert handler2 in dispatcher._handlers["test_event"]
        assert len(dispatcher._wildcard_handlers) == 0

    @pytest.mark.asyncio
    async def test_publish(self, dispatcher, test_event, mock_event_store):
        """Test publishing events to handlers."""
        # Create mock handlers
        handler1 = AsyncMock()
        handler1.__name__ = "handler1"
        handler2 = AsyncMock()
        handler2.__name__ = "handler2"
        wildcard_handler = AsyncMock()
        wildcard_handler.__name__ = "wildcard_handler"

        # Subscribe handlers
        dispatcher.subscribe("test_event", handler1)
        dispatcher.subscribe("test_event", handler2)
        dispatcher.subscribe("*", wildcard_handler)

        # Publish event
        await dispatcher.publish(test_event)

        # Check that event was saved to store
        mock_event_store.save_event.assert_called_once_with(test_event)

        # Check that handlers were called
        handler1.assert_called_once_with(test_event)
        handler2.assert_called_once_with(test_event)
        wildcard_handler.assert_called_once_with(test_event)

    @pytest.mark.asyncio
    async def test_publish_no_store(self, test_event):
        """Test publishing events without an event store."""
        # Create dispatcher without event store
        dispatcher = EventDispatcher()

        # Create mock handler
        handler = AsyncMock()
        handler.__name__ = "handler"

        # Subscribe handler
        dispatcher.subscribe("test_event", handler)

        # Publish event
        await dispatcher.publish(test_event)

        # Check that handler was called
        handler.assert_called_once_with(test_event)

    @pytest.mark.asyncio
    async def test_publish_handler_error(self, dispatcher, test_event):
        """Test publishing events with a handler that raises an error."""
        # Create mock handlers
        handler1 = AsyncMock()
        handler1.__name__ = "handler1"
        handler1.side_effect = Exception("Handler error")
        handler2 = AsyncMock()
        handler2.__name__ = "handler2"

        # Subscribe handlers
        dispatcher.subscribe("test_event", handler1)
        dispatcher.subscribe("test_event", handler2)

        # Publish event (should not raise an exception)
        with patch("logging.Logger.error") as mock_error:
            await dispatcher.publish(test_event)
            mock_error.assert_called_once()

        # Both handlers should be called
        handler1.assert_called_once_with(test_event)
        handler2.assert_called_once_with(test_event)


@pytest.fixture
def mock_asyncpg_connection():
    """Create a mock asyncpg connection."""
    conn = AsyncMock()
    conn.add_listener = AsyncMock()
    conn.execute = AsyncMock()
    return conn


@pytest.fixture
def mock_asyncpg_pool(mock_asyncpg_connection):
    """Create a mock asyncpg connection pool."""
    pool = AsyncMock()

    # Mock the context manager
    pool_context = AsyncMock()
    pool_context.__aenter__.return_value = mock_asyncpg_connection
    pool_context.__aexit__.return_value = None
    pool.acquire.return_value = pool_context

    # Mock the create_pool function
    with patch("asyncpg.create_pool", return_value=pool):
        yield pool


class TestPostgresEventListener:
    """Test the PostgreSQL event listener implementation."""

    @pytest.fixture
    def listener(self, dispatcher):
        """Create a PostgreSQL event listener."""
        return PostgresEventListener(dispatcher, TestEvent)

    def test_init(self, dispatcher):
        """Test listener initialization."""
        listener = PostgresEventListener(dispatcher, TestEvent)
        assert listener.dispatcher == dispatcher
        assert listener.event_type == TestEvent
        assert listener.channel == "domain_events"
        assert listener._running is False
        assert listener._task is None

    @pytest.mark.asyncio
    async def test_start_stop(self, listener):
        """Test starting and stopping the listener."""
        # Mock the _listen_for_events method
        with patch.object(listener, "_listen_for_events", AsyncMock()) as mock_listen:
            # Start the listener
            await listener.start()

            # Check that the listener is running
            assert listener._running is True
            assert listener._task is not None

            # Check that the _listen_for_events method was called
            assert mock_listen.call_count > 0

            # Stop the listener
            await listener.stop()

            # Check that the listener is stopped
            assert listener._running is False
            assert listener._task is None

    @pytest.mark.asyncio
    async def test_listen_for_events(
        self, listener, mock_asyncpg_pool, mock_asyncpg_connection
    ):
        """Test the _listen_for_events method."""
        # Set up a mock for _on_notification
        with patch.object(
            listener, "_on_notification", AsyncMock()
        ) as mock_on_notification:
            # Create a task for _listen_for_events
            task = asyncio.create_task(listener._listen_for_events())

            # Wait a bit for the task to run
            await asyncio.sleep(0.1)

            # Check that the connection was set up correctly
            mock_asyncpg_connection.add_listener.assert_called_once_with(
                "domain_events", listener._on_notification
            )
            mock_asyncpg_connection.execute.assert_called_once_with(
                "LISTEN domain_events"
            )

            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_on_notification(self, listener, dispatcher):
        """Test the _on_notification method."""
        # Create a mock connection
        conn = MagicMock()

        # Create a notification payload
        payload = '{"event_id": "event-123", "event_type": "test_event", "aggregate_id": "aggregate-123", "timestamp": "2023-01-01T12:00:00"}'

        # Mock the json.loads function
        with patch(
            "json.loads",
            return_value={
                "event_id": "event-123",
                "event_type": "test_event",
                "aggregate_id": "aggregate-123",
                "timestamp": "2023-01-01T12:00:00",
            },
        ):
            # Call _on_notification
            await listener._on_notification(conn, 1234, "domain_events", payload)

            # Check that the dispatcher was called to publish an event
            assert dispatcher.publish.call_count == 1

            # Get the event that was published
            event = dispatcher.publish.call_args.args[0]
            assert isinstance(event, TestEvent)
            assert event.event_id == "event-123"
            assert event.event_type == "test_event"
            assert event.aggregate_id == "aggregate-123"


class TestDomainEventHandler:
    """Test the domain event handler decorator."""

    def test_decorator(self):
        """Test the domain_event_handler decorator."""

        # Create a function
        async def handler(event):
            pass

        # Apply the decorator
        decorated = domain_event_handler("test_event")(handler)

        # Check that the function was properly decorated
        assert hasattr(decorated, "__is_event_handler__")
        assert decorated.__is_event_handler__ is True
        assert hasattr(decorated, "__event_type__")
        assert decorated.__event_type__ == "test_event"

        # The function itself should be unchanged
        assert decorated == handler


class TestEventSubscriber:
    """Test the event subscriber base class."""

    class TestSubscriber(EventSubscriber):
        """Test subscriber class."""

        __test__ = False  # Prevent pytest from collecting this class as a test

        def __init__(self, dispatcher):
            super().__init__(dispatcher)
            self.handled_events = []

        @domain_event_handler("test_event")
        async def handle_test_event(self, event):
            """Handle test events."""
            self.handled_events.append(event)

        @domain_event_handler("*")
        async def handle_all_events(self, event):
            """Handle all events."""
            self.handled_events.append(f"all: {event.event_type}")

    def test_init(self, dispatcher):
        """Test subscriber initialization."""
        subscriber = self.TestSubscriber(dispatcher)

        # Check that the dispatcher and handlers were set up
        assert subscriber.dispatcher == dispatcher

        # Check that handlers were registered with the dispatcher
        assert len(dispatcher._handlers.get("test_event", [])) == 1
        assert len(dispatcher._wildcard_handlers) == 1

    @pytest.mark.asyncio
    async def test_event_handling(self, dispatcher, test_event):
        """Test event handling by subscribers."""
        # Create a subscriber
        subscriber = self.TestSubscriber(dispatcher)

        # Publish an event
        await dispatcher.publish(test_event)

        # Check that the event was handled
        assert len(subscriber.handled_events) == 2
        assert test_event in subscriber.handled_events
        assert f"all: {test_event.event_type}" in subscriber.handled_events
