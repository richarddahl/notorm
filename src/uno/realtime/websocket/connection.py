"""WebSocket connection management.

This module provides classes for managing WebSocket connections.
"""

import uuid
import asyncio
import logging
import time
from enum import Enum, auto
from typing import Dict, Any, Optional, Set, List, Callable, Awaitable, Union, Protocol, cast

from uno.realtime.websocket.message import Message, MessageType
from uno.realtime.websocket.errors import (
    WebSocketError,
    ConnectionError,
    WebSocketErrorCode
)


logger = logging.getLogger("uno.websocket")


class ConnectionState(Enum):
    """State of a WebSocket connection."""
    
    INITIALIZING = auto()     # Connection is being initialized
    CONNECTING = auto()       # Connection is being established
    CONNECTED = auto()        # Connection is established
    AUTHENTICATING = auto()   # Client is being authenticated
    AUTHENTICATED = auto()    # Client is authenticated
    DISCONNECTING = auto()    # Connection is being closed gracefully
    DISCONNECTED = auto()     # Connection is closed
    ERROR = auto()            # Connection is in error state


class WebSocketSender(Protocol):
    """Protocol for sending WebSocket messages."""
    
    async def send_text(self, data: str) -> None:
        """Send a text message.
        
        Args:
            data: The text data to send.
        """
        ...
    
    async def send_bytes(self, data: bytes) -> None:
        """Send a binary message.
        
        Args:
            data: The binary data to send.
        """
        ...
    
    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection.
        
        Args:
            code: The close code.
            reason: The close reason.
        """
        ...


MessageHandler = Callable[[Message, "WebSocketConnection"], Awaitable[None]]
ConnectionHandler = Callable[["WebSocketConnection"], Awaitable[None]]
DisconnectionHandler = Callable[["WebSocketConnection", int, str], Awaitable[None]]
ErrorHandler = Callable[["WebSocketConnection", WebSocketError], Awaitable[None]]


class WebSocketConnection:
    """Represents a WebSocket connection to a client.
    
    This class manages the lifecycle of a WebSocket connection and provides
    methods for sending and receiving messages.
    """
    
    def __init__(self, 
                socket: WebSocketSender,
                client_id: Optional[str] = None,
                client_info: Optional[Dict[str, Any]] = None,
                auto_ping: bool = True,
                ping_interval: float = 30.0,
                ping_timeout: float = 10.0,
                max_message_size: int = 1024 * 1024,  # 1 MB
                close_timeout: float = 5.0):
        """Initialize a WebSocket connection.
        
        Args:
            socket: The WebSocket socket.
            client_id: Optional client ID. If not provided, a UUID will be generated.
            client_info: Optional dictionary with client information.
            auto_ping: Whether to automatically send ping messages.
            ping_interval: Interval between ping messages in seconds.
            ping_timeout: Timeout for ping responses in seconds.
            max_message_size: Maximum message size in bytes.
            close_timeout: Timeout for graceful connection close in seconds.
        """
        self.socket = socket
        self.client_id = client_id or str(uuid.uuid4())
        self.client_info = client_info or {}
        self.state = ConnectionState.INITIALIZING
        self.user_id: Optional[str] = None
        self.authenticated = False
        self.subscriptions: Set[str] = set()
        self.auto_ping = auto_ping
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_message_size = max_message_size
        self.close_timeout = close_timeout
        
        # Connection stats
        self.connected_at: Optional[float] = None
        self.last_message_at: Optional[float] = None
        self.message_count = 0
        self.error_count = 0
        
        # Pending pings
        self.pending_pings: Dict[str, float] = {}
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[MessageHandler]] = {
            message_type: [] for message_type in MessageType
        }
        
        # Lifecycle handlers
        self.on_connect_handlers: List[ConnectionHandler] = []
        self.on_disconnect_handlers: List[DisconnectionHandler] = []
        self.on_error_handlers: List[ErrorHandler] = []
        
        # Tasks
        self.ping_task: Optional[asyncio.Task] = None
        self.main_task: Optional[asyncio.Task] = None
    
    def __str__(self) -> str:
        """Return a string representation of the connection."""
        return f"WebSocketConnection(client_id={self.client_id}, state={self.state.name})"
    
    async def initialize(self) -> None:
        """Initialize the connection.
        
        This method should be called after creating the connection object.
        """
        self.state = ConnectionState.CONNECTING
        
        # Start ping task if auto_ping is enabled
        if self.auto_ping:
            self.ping_task = asyncio.create_task(self._ping_loop())
            self.ping_task.add_done_callback(self._on_ping_task_done)
    
    async def handle_connected(self) -> None:
        """Handle connection established event.
        
        This method should be called when the WebSocket connection is established.
        """
        self.state = ConnectionState.CONNECTED
        self.connected_at = time.time()
        
        # Notify connection handlers
        await self._notify_connect_handlers()
    
    async def handle_message(self, data: Union[str, bytes]) -> None:
        """Handle a received message.
        
        Args:
            data: The message data.
        """
        # Update stats
        self.last_message_at = time.time()
        self.message_count += 1
        
        try:
            # Parse the message
            if isinstance(data, bytes):
                data_str = data.decode("utf-8")
            else:
                data_str = data
            
            message = Message.from_json(data_str)
            
            # Handle system messages
            if message.type == MessageType.PING:
                await self.send_message(create_pong_message(message.id))
                return
            
            elif message.type == MessageType.PONG:
                if message.correlation_id in self.pending_pings:
                    del self.pending_pings[message.correlation_id]
                return
            
            # Process message handlers
            await self._process_message_handlers(message)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error handling message: {e}")
            
            # Create and send error message
            error_message = Message(
                type=MessageType.ERROR,
                payload={
                    "error": {
                        "code": "MESSAGE_PROCESSING_ERROR",
                        "message": str(e)
                    }
                }
            )
            await self.send_message(error_message)
    
    async def handle_disconnected(self, code: int, reason: str) -> None:
        """Handle connection closed event.
        
        Args:
            code: The close code.
            reason: The close reason.
        """
        self.state = ConnectionState.DISCONNECTED
        
        # Cancel tasks
        if self.ping_task:
            self.ping_task.cancel()
        
        if self.main_task:
            self.main_task.cancel()
        
        # Notify disconnection handlers
        await self._notify_disconnect_handlers(code, reason)
    
    async def handle_error(self, error: WebSocketError) -> None:
        """Handle connection error.
        
        Args:
            error: The error that occurred.
        """
        self.state = ConnectionState.ERROR
        self.error_count += 1
        
        # Notify error handlers
        await self._notify_error_handlers(error)
    
    async def send_message(self, message: Message) -> None:
        """Send a message to the client.
        
        Args:
            message: The message to send.
        """
        if self.state not in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
            raise ConnectionError(
                WebSocketErrorCode.CONNECTION_CLOSED_UNEXPECTEDLY,
                f"Cannot send message in state {self.state.name}"
            )
        
        try:
            # Convert the message to JSON
            json_data = message.to_json()
            
            # Send the message
            await self.socket.send_text(json_data)
            
        except Exception as e:
            raise ConnectionError(
                WebSocketErrorCode.CONNECTION_CLOSED_UNEXPECTEDLY,
                f"Failed to send message: {e}"
            )
    
    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the connection.
        
        Args:
            code: The close code.
            reason: The close reason.
        """
        if self.state in (ConnectionState.DISCONNECTED, ConnectionState.DISCONNECTING):
            return
        
        self.state = ConnectionState.DISCONNECTING
        
        try:
            # Try to send a disconnect message before closing
            try:
                disconnect_message = Message(
                    type=MessageType.DISCONNECT,
                    payload={"code": code, "reason": reason}
                )
                await self.send_message(disconnect_message)
                
                # Give the client a chance to process the disconnect message
                await asyncio.sleep(0.1)
                
            except Exception:
                # Ignore errors when sending the disconnect message
                pass
            
            # Close the WebSocket connection
            await self.socket.close(code, reason)
            
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
            
        finally:
            # Ensure the connection is marked as disconnected
            await self.handle_disconnected(code, reason)
    
    def add_message_handler(self, message_type: MessageType, handler: MessageHandler) -> None:
        """Add a message handler.
        
        Args:
            message_type: The message type to handle.
            handler: The handler function.
        """
        self.message_handlers[message_type].append(handler)
    
    def remove_message_handler(self, message_type: MessageType, handler: MessageHandler) -> None:
        """Remove a message handler.
        
        Args:
            message_type: The message type.
            handler: The handler function.
        """
        if handler in self.message_handlers[message_type]:
            self.message_handlers[message_type].remove(handler)
    
    def add_connect_handler(self, handler: ConnectionHandler) -> None:
        """Add a connection handler.
        
        Args:
            handler: The handler function.
        """
        self.on_connect_handlers.append(handler)
    
    def remove_connect_handler(self, handler: ConnectionHandler) -> None:
        """Remove a connection handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_connect_handlers:
            self.on_connect_handlers.remove(handler)
    
    def add_disconnect_handler(self, handler: DisconnectionHandler) -> None:
        """Add a disconnection handler.
        
        Args:
            handler: The handler function.
        """
        self.on_disconnect_handlers.append(handler)
    
    def remove_disconnect_handler(self, handler: DisconnectionHandler) -> None:
        """Remove a disconnection handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_disconnect_handlers:
            self.on_disconnect_handlers.remove(handler)
    
    def add_error_handler(self, handler: ErrorHandler) -> None:
        """Add an error handler.
        
        Args:
            handler: The handler function.
        """
        self.on_error_handlers.append(handler)
    
    def remove_error_handler(self, handler: ErrorHandler) -> None:
        """Remove an error handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_error_handlers:
            self.on_error_handlers.remove(handler)
    
    async def authenticate(self, user_id: str) -> None:
        """Mark the connection as authenticated.
        
        Args:
            user_id: The user ID.
        """
        self.state = ConnectionState.AUTHENTICATED
        self.user_id = user_id
        self.authenticated = True
    
    async def add_subscription(self, subscription: str) -> None:
        """Add a subscription.
        
        Args:
            subscription: The subscription key.
        """
        self.subscriptions.add(subscription)
    
    async def remove_subscription(self, subscription: str) -> None:
        """Remove a subscription.
        
        Args:
            subscription: The subscription key.
        """
        if subscription in self.subscriptions:
            self.subscriptions.remove(subscription)
    
    def has_subscription(self, subscription: str) -> bool:
        """Check if the connection has a subscription.
        
        Args:
            subscription: The subscription key.
            
        Returns:
            True if the connection has the subscription, False otherwise.
        """
        return subscription in self.subscriptions
    
    async def _ping_loop(self) -> None:
        """Background task for sending ping messages."""
        while True:
            if self.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                # Check for timed out pings
                now = time.time()
                timed_out_pings = [
                    ping_id for ping_id, sent_at in self.pending_pings.items()
                    if now - sent_at > self.ping_timeout
                ]
                
                if timed_out_pings:
                    for ping_id in timed_out_pings:
                        del self.pending_pings[ping_id]
                    
                    # Connection is not responding to pings
                    logger.warning(f"Connection {self.client_id} not responding to pings")
                    
                    # Close the connection
                    error = ConnectionError(
                        WebSocketErrorCode.CONNECTION_TIMED_OUT,
                        "Connection timed out (no ping response)"
                    )
                    await self.handle_error(error)
                    await self.close(1001, "Connection timeout")
                    return
                
                # Send a new ping
                try:
                    ping_message = Message(type=MessageType.PING)
                    await self.send_message(ping_message)
                    self.pending_pings[ping_message.id] = now
                    
                except Exception as e:
                    logger.error(f"Error sending ping: {e}")
            
            # Sleep until next ping
            await asyncio.sleep(self.ping_interval)
    
    def _on_ping_task_done(self, task: asyncio.Task) -> None:
        """Callback for when the ping task is done."""
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping task failed: {e}")
    
    async def _notify_connect_handlers(self) -> None:
        """Notify all connection handlers."""
        for handler in self.on_connect_handlers:
            try:
                await handler(self)
            except Exception as e:
                logger.error(f"Error in connection handler: {e}")
    
    async def _notify_disconnect_handlers(self, code: int, reason: str) -> None:
        """Notify all disconnection handlers.
        
        Args:
            code: The close code.
            reason: The close reason.
        """
        for handler in self.on_disconnect_handlers:
            try:
                await handler(self, code, reason)
            except Exception as e:
                logger.error(f"Error in disconnection handler: {e}")
    
    async def _notify_error_handlers(self, error: WebSocketError) -> None:
        """Notify all error handlers.
        
        Args:
            error: The error that occurred.
        """
        for handler in self.on_error_handlers:
            try:
                await handler(self, error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
    
    async def _process_message_handlers(self, message: Message) -> None:
        """Process all handlers for a message.
        
        Args:
            message: The message to process.
        """
        # Get handlers for this message type
        handlers = self.message_handlers.get(message.type, [])
        
        # Process handlers
        for handler in handlers:
            try:
                await handler(message, self)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
                
                # Send error response if the message has an ID
                try:
                    error_response = message.create_error_response(
                        "HANDLER_ERROR",
                        str(e)
                    )
                    await self.send_message(error_response)
                except Exception:
                    # Ignore errors when sending the error response
                    pass


def create_pong_message(ping_id: str) -> Message:
    """Create a PONG message in response to a PING.
    
    Args:
        ping_id: The ID of the PING message.
        
    Returns:
        A PONG Message instance.
    """
    return Message(
        type=MessageType.PONG,
        correlation_id=ping_id
    )