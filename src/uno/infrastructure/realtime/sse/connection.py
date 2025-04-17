"""SSE connection implementation.

This module provides the SSEConnection class for managing individual SSE connections.
"""

import asyncio
import logging
from typing import (
    Optional, Dict, Any, List, Set, Callable, Awaitable, AsyncIterator, 
    Protocol, Union, TypeVar, Generic
)

from uno.realtime.sse.event import Event, EventPriority, create_keep_alive_event
from uno.realtime.sse.errors import SSEError, SSEErrorCode, ConnectionError, StreamError


# Type for response sender objects
ResponseSender = TypeVar('ResponseSender')


class AsyncResponseWriter(Protocol):
    """Protocol for async response writers.
    
    This abstracts away the framework-specific details of sending SSE responses.
    """
    
    async def write(self, data: str) -> None:
        """Write data to the response."""
        ...
    
    async def flush(self) -> None:
        """Flush the response buffer."""
        ...


class SSEConnection(Generic[ResponseSender]):
    """Represents a Server-Sent Events connection to a client.
    
    This class manages a single SSE connection, handling authentication,
    event broadcasting, and connection lifecycle.
    
    Attributes:
        client_id: Unique identifier for this connection.
        client_info: Additional information about the client.
        subscriptions: Set of subscription IDs for this connection.
        user_id: ID of the authenticated user, if any.
        response: The response object for sending events.
        writer: The async writer for sending SSE data.
        is_connected: Whether the connection is active.
    """
    
    def __init__(self, 
                response: ResponseSender,
                writer: AsyncResponseWriter,
                client_id: Optional[str] = None,
                client_info: Optional[Dict[str, Any]] = None):
        """Initialize a new SSE connection.
        
        Args:
            response: The framework-specific response object.
            writer: The async writer for sending SSE data.
            client_id: Optional client identifier, generated if not provided.
            client_info: Optional dictionary with additional client information.
        """
        from uuid import uuid4
        
        self.client_id = client_id or str(uuid4())
        self.client_info = client_info or {}
        self.subscriptions: Set[str] = set()
        self.user_id: Optional[str] = None
        
        self._response = response
        self._writer = writer
        self._is_connected = False
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._closing = asyncio.Event()
        self._send_task: Optional[asyncio.Task] = None
        self._keep_alive_task: Optional[asyncio.Task] = None
        self._keep_alive_interval: float = 30.0  # seconds
        
        self._logger = logging.getLogger(__name__)
    
    @property
    def is_connected(self) -> bool:
        """Get the connection status.
        
        Returns:
            True if the connection is active, False otherwise.
        """
        return self._is_connected
    
    @property
    def is_authenticated(self) -> bool:
        """Get the authentication status.
        
        Returns:
            True if the user is authenticated, False otherwise.
        """
        return self.user_id is not None
    
    def get_response(self) -> ResponseSender:
        """Get the underlying response object.
        
        Returns:
            The framework-specific response object.
        """
        return self._response
    
    async def start(self, keep_alive: bool = True) -> None:
        """Start the SSE connection.
        
        This sends the SSE headers and starts the event loop.
        
        Args:
            keep_alive: Whether to send keep-alive events.
            
        Raises:
            ConnectionError: If the connection is already started.
        """
        if self._is_connected:
            raise ConnectionError(
                SSEErrorCode.CONNECTION_FAILED, 
                "Connection already started"
            )
        
        # Set headers (assumes web framework will handle this)
        # Note: Headers must be set before any data is sent
        
        # Start the event send loop
        self._is_connected = True
        self._send_task = asyncio.create_task(self._send_loop())
        
        # Start keep-alive if requested
        if keep_alive:
            self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
    
    async def stop(self) -> None:
        """Stop the SSE connection gracefully."""
        if not self._is_connected:
            return
        
        # Signal the send loop to stop
        self._closing.set()
        
        # Cancel tasks
        if self._send_task:
            self._send_task.cancel()
        
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
        
        self._is_connected = False
    
    def close(self) -> None:
        """Close the connection immediately (non-async version).
        
        This is a convenience method for synchronous contexts.
        """
        self._is_connected = False
        self._closing.set()
        
        # Note: This doesn't cancel the tasks, they will exit
        # on their next loop iteration
    
    async def send_event(self, event: Event) -> bool:
        """Send an event to this connection.
        
        Args:
            event: The event to send.
            
        Returns:
            True if the event was queued, False if the connection is closed.
        """
        if not self._is_connected:
            return False
        
        await self._event_queue.put(event)
        return True
    
    async def send_data(self, 
                       resource: str, 
                       data: Any, 
                       priority: EventPriority = EventPriority.NORMAL) -> bool:
        """Send data to this connection.
        
        Args:
            resource: The resource identifier (e.g., "users", "posts").
            data: The data to send.
            priority: The priority of the event.
            
        Returns:
            True if the data was queued, False if the connection is closed.
        """
        from uno.realtime.sse.event import create_data_event
        event = create_data_event(resource, data, priority)
        return await self.send_event(event)
    
    async def send_notification(self, 
                              title: str, 
                              message: str, 
                              level: str = "info",
                              actions: Optional[List[Dict[str, Any]]] = None,
                              priority: EventPriority = EventPriority.HIGH) -> bool:
        """Send a notification to this connection.
        
        Args:
            title: The notification title.
            message: The notification message.
            level: The notification level (info, warning, error, etc.).
            actions: Optional list of actions the user can take.
            priority: The priority of the notification.
            
        Returns:
            True if the notification was queued, False if the connection is closed.
        """
        from uno.realtime.sse.event import create_notification_event
        event = create_notification_event(title, message, level, actions, priority)
        return await self.send_event(event)
    
    def add_subscription(self, subscription_id: str) -> None:
        """Add a subscription to this connection.
        
        Args:
            subscription_id: The subscription identifier.
        """
        self.subscriptions.add(subscription_id)
    
    def remove_subscription(self, subscription_id: str) -> None:
        """Remove a subscription from this connection.
        
        Args:
            subscription_id: The subscription identifier.
        """
        self.subscriptions.discard(subscription_id)
    
    def has_subscription(self, subscription_id: str) -> bool:
        """Check if this connection has a specific subscription.
        
        Args:
            subscription_id: The subscription identifier.
            
        Returns:
            True if the connection has the subscription, False otherwise.
        """
        return subscription_id in self.subscriptions
    
    async def _send_loop(self) -> None:
        """Main loop for sending events to the client."""
        try:
            while self._is_connected and not self._closing.is_set():
                # Get the next event with a timeout
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # No event available, check if we should close
                    continue
                
                # Send the event
                try:
                    event_text = event.to_sse_format()
                    await self._writer.write(event_text)
                    await self._writer.flush()
                    self._event_queue.task_done()
                except Exception as e:
                    self._logger.error(f"Error sending SSE event: {e}")
                    # If we can't send, mark the connection as closed
                    self._is_connected = False
                    break
        except asyncio.CancelledError:
            # Task cancelled, exit gracefully
            pass
        except Exception as e:
            self._logger.error(f"Unexpected error in SSE send loop: {e}")
        finally:
            self._is_connected = False
    
    async def _keep_alive_loop(self) -> None:
        """Send keep-alive comments periodically."""
        try:
            while self._is_connected and not self._closing.is_set():
                await asyncio.sleep(self._keep_alive_interval)
                if self._is_connected and not self._closing.is_set():
                    # Send a keep-alive comment
                    event = create_keep_alive_event()
                    await self.send_event(event)
        except asyncio.CancelledError:
            # Task cancelled, exit gracefully
            pass
        except Exception as e:
            self._logger.error(f"Unexpected error in SSE keep-alive loop: {e}")


# Framework-specific adapters

class FastAPISSEWriter(AsyncResponseWriter):
    """SSE writer implementation for FastAPI/Starlette."""
    
    def __init__(self, response):
        """Initialize with a FastAPI/Starlette response object."""
        self.response = response
    
    async def write(self, data: str) -> None:
        """Write data to the response."""
        await self.response.write(data.encode("utf-8"))
    
    async def flush(self) -> None:
        """Flush the response buffer."""
        # FastAPI responses are auto-flushed
        pass