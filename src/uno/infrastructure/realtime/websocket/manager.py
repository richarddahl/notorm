"""WebSocket manager implementation.

This module provides a manager for WebSocket connections that integrates with
various web frameworks.
"""

import logging
import asyncio
import uuid
from typing import Dict, Set, Any, Optional, List, Callable, Awaitable, Union, Protocol, Type, TypeVar

from uno.realtime.websocket.connection import WebSocketConnection, WebSocketSender, ConnectionState
from uno.realtime.websocket.message import Message, MessageType
from uno.realtime.websocket.protocol import WebSocketProtocol, DefaultProtocol
from uno.realtime.websocket.errors import WebSocketError


logger = logging.getLogger("uno.websocket")


T = TypeVar('T')


class WebSocketManager:
    """Manager for WebSocket connections.
    
    This class manages WebSocket connections and provides methods for sending
    messages to clients.
    """
    
    def __init__(self, 
                protocol: Optional[WebSocketProtocol] = None,
                require_authentication: bool = True,
                auth_handler: Optional[Callable[[Dict[str, Any], WebSocketConnection], Awaitable[Optional[str]]]] = None,
                auto_ping: bool = True,
                ping_interval: float = 30.0,
                ping_timeout: float = 10.0,
                max_message_size: int = 1024 * 1024,  # 1 MB
                close_timeout: float = 5.0):
        """Initialize the WebSocket manager.
        
        Args:
            protocol: Optional protocol implementation. If not provided, DefaultProtocol is used.
            require_authentication: Whether to require authentication for connections.
            auth_handler: Optional function to authenticate clients.
            auto_ping: Whether to automatically send ping messages.
            ping_interval: Interval between ping messages in seconds.
            ping_timeout: Timeout for ping responses in seconds.
            max_message_size: Maximum message size in bytes.
            close_timeout: Timeout for graceful connection close in seconds.
        """
        self.protocol = protocol or DefaultProtocol(require_authentication, auth_handler)
        self.require_authentication = require_authentication
        self.auth_handler = auth_handler
        self.auto_ping = auto_ping
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_message_size = max_message_size
        self.close_timeout = close_timeout
        
        # Connection storage
        self.connections: Dict[str, WebSocketConnection] = {}
        self.connections_by_user: Dict[str, Set[WebSocketConnection]] = {}
        self.subscriptions: Dict[str, Set[WebSocketConnection]] = {}
        
        # Connection hooks
        self.on_connect_handlers: List[Callable[[WebSocketConnection], Awaitable[None]]] = []
        self.on_disconnect_handlers: List[Callable[[WebSocketConnection, int, str], Awaitable[None]]] = []
        self.on_message_handlers: List[Callable[[Message, WebSocketConnection], Awaitable[None]]] = []
        self.on_error_handlers: List[Callable[[WebSocketConnection, WebSocketError], Awaitable[None]]] = []
        
        # Task mapping to keep track of connection tasks
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        
        # Shutdown flag
        self.shutting_down = False
    
    async def handle_connection(self, 
                              socket: WebSocketSender,
                              client_id: Optional[str] = None,
                              client_info: Optional[Dict[str, Any]] = None,
                              handler: Optional[Callable[[WebSocketConnection], Awaitable[None]]] = None) -> None:
        """Handle a new WebSocket connection.
        
        This method should be called when a new WebSocket connection is established.
        
        Args:
            socket: The WebSocket socket.
            client_id: Optional client ID. If not provided, a UUID will be generated.
            client_info: Optional dictionary with client information.
            handler: Optional custom message handler.
        """
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Create connection object
        connection = WebSocketConnection(
            socket=socket,
            client_id=client_id,
            client_info=client_info or {},
            auto_ping=self.auto_ping,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            max_message_size=self.max_message_size,
            close_timeout=self.close_timeout
        )
        
        # Register connection
        self.connections[client_id] = connection
        
        # Register connection handlers
        connection.add_connect_handler(self._on_connect)
        connection.add_disconnect_handler(self._on_disconnect)
        connection.add_error_handler(self._on_error)
        
        try:
            # Initialize connection
            await connection.initialize()
            
            # Notify protocol
            await self.protocol.handle_connection_established(connection)
            
            # Mark as connected
            await connection.handle_connected()
            
            # Handle messages using custom handler or default loop
            if handler:
                await handler(connection)
            else:
                # Run message loop
                while connection.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                    try:
                        # Wait for message (integration specific)
                        # This is just a placeholder, actual message reception will be handled by the framework
                        await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        # Connection task cancelled
                        break
                    except Exception as e:
                        # Handle error
                        logger.error(f"Error in message loop: {e}")
                        break
            
        except Exception as e:
            # Handle connection error
            logger.error(f"Connection error: {e}")
            try:
                await connection.close(1011, f"Internal error: {e}")
            except Exception:
                # Ignore errors when closing connection
                pass
            
        finally:
            # Clean up connection if still registered
            await self._cleanup_connection(connection)
    
    def get_connection(self, client_id: str) -> Optional[WebSocketConnection]:
        """Get a connection by client ID.
        
        Args:
            client_id: The client ID.
            
        Returns:
            The connection or None if not found.
        """
        return self.connections.get(client_id)
    
    def get_connections_by_user(self, user_id: str) -> List[WebSocketConnection]:
        """Get all connections for a user.
        
        Args:
            user_id: The user ID.
            
        Returns:
            A list of connections for the user.
        """
        return list(self.connections_by_user.get(user_id, set()))
    
    def get_connections_by_subscription(self, subscription: str) -> List[WebSocketConnection]:
        """Get all connections with a subscription.
        
        Args:
            subscription: The subscription key.
            
        Returns:
            A list of connections with the subscription.
        """
        return list(self.subscriptions.get(subscription, set()))
    
    async def broadcast(self, 
                       message: Message,
                       filter_func: Optional[Callable[[WebSocketConnection], bool]] = None) -> None:
        """Broadcast a message to all connections.
        
        Args:
            message: The message to broadcast.
            filter_func: Optional function to filter connections.
        """
        tasks = []
        for connection in self.connections.values():
            if filter_func and not filter_func(connection):
                continue
            
            if connection.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                tasks.append(connection.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_users(self, 
                               message: Message,
                               user_ids: List[str]) -> None:
        """Broadcast a message to specific users.
        
        Args:
            message: The message to broadcast.
            user_ids: The user IDs to send to.
        """
        tasks = []
        for user_id in user_ids:
            for connection in self.connections_by_user.get(user_id, set()):
                if connection.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                    tasks.append(connection.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_subscription(self, 
                                      message: Message,
                                      subscription: str) -> None:
        """Broadcast a message to connections with a subscription.
        
        Args:
            message: The message to broadcast.
            subscription: The subscription key.
        """
        tasks = []
        for connection in self.subscriptions.get(subscription, set()):
            if connection.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                tasks.append(connection.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_client(self, 
                           client_id: str,
                           message: Message) -> bool:
        """Send a message to a specific client.
        
        Args:
            client_id: The client ID.
            message: The message to send.
            
        Returns:
            True if the message was sent, False otherwise.
        """
        connection = self.connections.get(client_id)
        if not connection or connection.state not in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
            return False
        
        try:
            await connection.send_message(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            return False
    
    async def close_connection(self, 
                             client_id: str,
                             code: int = 1000,
                             reason: str = "") -> bool:
        """Close a connection.
        
        Args:
            client_id: The client ID.
            code: The close code.
            reason: The close reason.
            
        Returns:
            True if the connection was closed, False otherwise.
        """
        connection = self.connections.get(client_id)
        if not connection:
            return False
        
        try:
            await connection.close(code, reason)
            return True
        except Exception as e:
            logger.error(f"Error closing connection {client_id}: {e}")
            return False
    
    async def close_all_connections(self, 
                                  code: int = 1000,
                                  reason: str = "") -> None:
        """Close all connections.
        
        Args:
            code: The close code.
            reason: The close reason.
        """
        # Mark as shutting down
        self.shutting_down = True
        
        # Close all connections
        tasks = []
        for connection in list(self.connections.values()):
            tasks.append(connection.close(code, reason))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cancel all connection tasks
        for task in self.connection_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.connection_tasks:
            await asyncio.gather(*self.connection_tasks.values(), return_exceptions=True)
        
        # Clear connection storage
        self.connections.clear()
        self.connections_by_user.clear()
        self.subscriptions.clear()
        self.connection_tasks.clear()
    
    def add_on_connect_handler(self, handler: Callable[[WebSocketConnection], Awaitable[None]]) -> None:
        """Add a connection handler.
        
        Args:
            handler: The handler function.
        """
        self.on_connect_handlers.append(handler)
    
    def remove_on_connect_handler(self, handler: Callable[[WebSocketConnection], Awaitable[None]]) -> None:
        """Remove a connection handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_connect_handlers:
            self.on_connect_handlers.remove(handler)
    
    def add_on_disconnect_handler(self, handler: Callable[[WebSocketConnection, int, str], Awaitable[None]]) -> None:
        """Add a disconnection handler.
        
        Args:
            handler: The handler function.
        """
        self.on_disconnect_handlers.append(handler)
    
    def remove_on_disconnect_handler(self, handler: Callable[[WebSocketConnection, int, str], Awaitable[None]]) -> None:
        """Remove a disconnection handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_disconnect_handlers:
            self.on_disconnect_handlers.remove(handler)
    
    def add_on_message_handler(self, handler: Callable[[Message, WebSocketConnection], Awaitable[None]]) -> None:
        """Add a message handler.
        
        Args:
            handler: The handler function.
        """
        self.on_message_handlers.append(handler)
    
    def remove_on_message_handler(self, handler: Callable[[Message, WebSocketConnection], Awaitable[None]]) -> None:
        """Remove a message handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_message_handlers:
            self.on_message_handlers.remove(handler)
    
    def add_on_error_handler(self, handler: Callable[[WebSocketConnection, WebSocketError], Awaitable[None]]) -> None:
        """Add an error handler.
        
        Args:
            handler: The handler function.
        """
        self.on_error_handlers.append(handler)
    
    def remove_on_error_handler(self, handler: Callable[[WebSocketConnection, WebSocketError], Awaitable[None]]) -> None:
        """Remove an error handler.
        
        Args:
            handler: The handler function.
        """
        if handler in self.on_error_handlers:
            self.on_error_handlers.remove(handler)
    
    async def _on_connect(self, connection: WebSocketConnection) -> None:
        """Handle a connection being established.
        
        Args:
            connection: The WebSocket connection.
        """
        # Notify connection handlers
        for handler in self.on_connect_handlers:
            try:
                await handler(connection)
            except Exception as e:
                logger.error(f"Error in connection handler: {e}")
    
    async def _on_disconnect(self, 
                           connection: WebSocketConnection,
                           code: int,
                           reason: str) -> None:
        """Handle a connection being closed.
        
        Args:
            connection: The WebSocket connection.
            code: The close code.
            reason: The close reason.
        """
        # Notify protocol
        try:
            await self.protocol.handle_connection_closed(connection, code, reason)
        except Exception as e:
            logger.error(f"Error in protocol connection closed handler: {e}")
        
        # Notify disconnection handlers
        for handler in self.on_disconnect_handlers:
            try:
                await handler(connection, code, reason)
            except Exception as e:
                logger.error(f"Error in disconnection handler: {e}")
        
        # Clean up connection
        await self._cleanup_connection(connection)
    
    async def _on_error(self, 
                      connection: WebSocketConnection,
                      error: WebSocketError) -> None:
        """Handle a connection error.
        
        Args:
            connection: The WebSocket connection.
            error: The error that occurred.
        """
        # Notify protocol
        try:
            await self.protocol.handle_error(connection, error)
        except Exception as e:
            logger.error(f"Error in protocol error handler: {e}")
        
        # Notify error handlers
        for handler in self.on_error_handlers:
            try:
                await handler(connection, error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
    
    async def _on_message(self, 
                        message: Message,
                        connection: WebSocketConnection) -> None:
        """Handle a message.
        
        Args:
            message: The message.
            connection: The WebSocket connection.
        """
        # Notify protocol
        try:
            await self.protocol.handle_message(message, connection)
        except Exception as e:
            logger.error(f"Error in protocol message handler: {e}")
        
        # Notify message handlers
        for handler in self.on_message_handlers:
            try:
                await handler(message, connection)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
    
    async def _cleanup_connection(self, connection: WebSocketConnection) -> None:
        """Clean up a connection.
        
        Args:
            connection: The WebSocket connection.
        """
        # Remove from connections
        self.connections.pop(connection.client_id, None)
        
        # Remove from connections by user
        if connection.user_id:
            user_connections = self.connections_by_user.get(connection.user_id)
            if user_connections and connection in user_connections:
                user_connections.remove(connection)
                if not user_connections:
                    self.connections_by_user.pop(connection.user_id, None)
        
        # Remove from subscriptions
        for subscription in list(connection.subscriptions):
            sub_connections = self.subscriptions.get(subscription)
            if sub_connections and connection in sub_connections:
                sub_connections.remove(connection)
                if not sub_connections:
                    self.subscriptions.pop(subscription, None)
        
        # Remove connection task
        self.connection_tasks.pop(connection.client_id, None)
    
    def _register_subscription(self, connection: WebSocketConnection, subscription: str) -> None:
        """Register a subscription.
        
        Args:
            connection: The WebSocket connection.
            subscription: The subscription key.
        """
        if subscription not in self.subscriptions:
            self.subscriptions[subscription] = set()
        
        self.subscriptions[subscription].add(connection)
    
    def _unregister_subscription(self, connection: WebSocketConnection, subscription: str) -> None:
        """Unregister a subscription.
        
        Args:
            connection: The WebSocket connection.
            subscription: The subscription key.
        """
        if subscription in self.subscriptions:
            sub_connections = self.subscriptions[subscription]
            if connection in sub_connections:
                sub_connections.remove(connection)
                if not sub_connections:
                    self.subscriptions.pop(subscription, None)
    
    def _register_user(self, connection: WebSocketConnection, user_id: str) -> None:
        """Register a user connection.
        
        Args:
            connection: The WebSocket connection.
            user_id: The user ID.
        """
        if user_id not in self.connections_by_user:
            self.connections_by_user[user_id] = set()
        
        self.connections_by_user[user_id].add(connection)