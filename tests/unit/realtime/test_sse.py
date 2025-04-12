"""Tests for the SSE module."""

import asyncio
import pytest
import json
from typing import Dict, Any, List, Optional, Set, Callable

from uno.realtime.sse.event import Event, EventPriority, create_data_event, create_notification_event
from uno.realtime.sse.errors import SSEError, SSEErrorCode
from uno.realtime.sse.connection import SSEConnection, AsyncResponseWriter
from uno.realtime.sse.manager import SSEManager


class MockResponseWriter(AsyncResponseWriter):
    """Mock implementation of AsyncResponseWriter for testing."""
    
    def __init__(self):
        self.written_data: List[str] = []
    
    async def write(self, data: str) -> None:
        """Record written data."""
        self.written_data.append(data)
    
    async def flush(self) -> None:
        """No-op for testing."""
        pass


class MockResponse:
    """Mock response object for testing."""
    pass


class TestSSEEvent:
    """Tests for the SSE Event class."""
    
    def test_event_creation(self):
        """Test creating an Event."""
        event = Event(data={"test": "data"})
        assert event.data == {"test": "data"}
        assert event.event == "message"  # Default type
        assert event.priority == EventPriority.NORMAL
        assert event.id is not None
    
    def test_event_sse_format(self):
        """Test converting an Event to SSE format."""
        event = Event(
            data={"test": "data"},
            id="test-id",
            event="test-event"
        )
        
        # Get the SSE format string
        sse_format = event.to_sse_format()
        
        # Verify essential parts
        assert ": timestamp=" in sse_format
        assert "id: test-id" in sse_format
        assert "event: test-event" in sse_format
        assert 'data: {"test": "data"}' in sse_format
        
        # Should end with empty line
        assert sse_format.endswith("\n")
    
    def test_create_data_event(self):
        """Test creating a data event."""
        event = create_data_event("users", {"id": 1, "name": "Test"})
        
        assert event.event == "data"
        assert event.data == {
            "resource": "users",
            "data": {"id": 1, "name": "Test"}
        }
    
    def test_create_notification_event(self):
        """Test creating a notification event."""
        event = create_notification_event(
            "Success", 
            "Operation completed", 
            "info",
            [{"label": "View", "action": "view"}]
        )
        
        assert event.event == "notification"
        assert event.data["title"] == "Success"
        assert event.data["message"] == "Operation completed"
        assert event.data["level"] == "info"
        assert event.data["actions"] == [{"label": "View", "action": "view"}]
        assert event.priority == EventPriority.HIGH  # Default for notifications


@pytest.mark.asyncio
class TestSSEConnection:
    """Tests for the SSE Connection class."""
    
    async def test_connection_lifecycle(self):
        """Test the connection lifecycle."""
        # Create mock objects
        writer = MockResponseWriter()
        response = MockResponse()
        
        # Create connection
        connection = SSEConnection(response, writer, client_id="test-client")
        
        # Check initial state
        assert connection.client_id == "test-client"
        assert not connection.is_connected
        assert not connection.is_authenticated
        
        # Start connection
        await connection.start(keep_alive=False)
        assert connection.is_connected
        
        # Send an event
        event = Event(data="Test message")
        success = await connection.send_event(event)
        assert success
        
        # Wait for the event to be processed
        await asyncio.sleep(0.1)
        
        # Check that the event was written
        assert len(writer.written_data) > 0
        
        # Stop the connection
        await connection.stop()
        assert not connection.is_connected
    
    async def test_subscription_management(self):
        """Test subscription management."""
        # Create connection
        writer = MockResponseWriter()
        response = MockResponse()
        connection = SSEConnection(response, writer, client_id="test-client")
        
        # Add subscriptions
        connection.add_subscription("users:updates")
        connection.add_subscription("global:notifications")
        
        # Check subscriptions
        assert connection.has_subscription("users:updates")
        assert connection.has_subscription("global:notifications")
        assert not connection.has_subscription("other:subscription")
        
        # Remove subscription
        connection.remove_subscription("users:updates")
        assert not connection.has_subscription("users:updates")
        assert connection.has_subscription("global:notifications")


@pytest.mark.asyncio
class TestSSEManager:
    """Tests for the SSE Manager class."""
    
    async def test_manager_connection_tracking(self):
        """Test manager tracking connections."""
        manager = SSEManager()
        
        # Create mock objects
        writer1 = MockResponseWriter()
        resp1 = MockResponse()
        writer2 = MockResponseWriter()
        resp2 = MockResponse()
        
        # Create connections
        conn1 = await manager.create_connection(resp1, writer1, client_id="client1")
        conn2 = await manager.create_connection(resp2, writer2, client_id="client2")
        
        # Check connection count
        assert manager.connection_count == 2
        
        # Get connections
        assert manager.get_connection("client1") == conn1
        assert manager.get_connection("client2") == conn2
        
        # Close a connection
        await manager.close_connection("client1")
        
        # Check tracking is updated
        assert manager.connection_count == 1
        assert manager.get_connection("client1") is None
        assert manager.get_connection("client2") is not None
    
    async def test_manager_broadcasting(self):
        """Test broadcasting events to connections."""
        manager = SSEManager()
        
        # Create connections
        writers = [MockResponseWriter() for _ in range(3)]
        connections = []
        
        for i, writer in enumerate(writers):
            conn = await manager.create_connection(
                MockResponse(), writer, client_id=f"client{i}"
            )
            connections.append(conn)
        
        # Add subscriptions
        await manager.add_subscription("client0", "topic:A")
        await manager.add_subscription("client1", "topic:A")
        await manager.add_subscription("client2", "topic:B")
        
        # Broadcast to all connections
        event = Event(data="Broadcast to all")
        count = await manager.broadcast_event(event)
        assert count == 3
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Broadcast to specific subscription
        event = Event(data="Broadcast to topic A")
        count = await manager.broadcast_to_subscriptions(event, ["topic:A"])
        assert count == 2  # Should reach 2 clients
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Clean up
        for conn in connections:
            await conn.stop()
    
    async def test_manager_authentication(self):
        """Test manager with authentication."""
        # Create authentication handler
        async def auth_handler(auth_data: Dict[str, Any]) -> Optional[str]:
            token = auth_data.get("token")
            if token == "valid-token":
                return "user123"
            return None
        
        # Create manager with authentication required
        manager = SSEManager(require_authentication=True, auth_handler=auth_handler)
        
        # Test valid authentication
        conn = await manager.create_connection(
            MockResponse(),
            MockResponseWriter(),
            client_id="client1",
            auth_data={"token": "valid-token"}
        )
        
        assert conn.is_authenticated
        assert conn.user_id == "user123"
        
        # Test invalid authentication
        with pytest.raises(SSEError) as exc_info:
            await manager.create_connection(
                MockResponse(),
                MockResponseWriter(),
                client_id="client2",
                auth_data={"token": "invalid-token"}
            )
        
        assert exc_info.value.code == SSEErrorCode.AUTHENTICATION_FAILED
        
        # Test missing auth data
        with pytest.raises(SSEError) as exc_info:
            await manager.create_connection(
                MockResponse(),
                MockResponseWriter(),
                client_id="client3"
            )
        
        assert exc_info.value.code == SSEErrorCode.AUTHENTICATION_REQUIRED