"""SSE manager implementation.

This module provides the SSEManager class for managing multiple SSE connections.
"""

import asyncio
import logging
from typing import (
    Dict, Set, List, Any, Optional, Union, TypeVar, Generic, 
    Callable, Coroutine, Awaitable, Type
)
import weakref

from uno.realtime.sse.connection import SSEConnection, AsyncResponseWriter
from uno.realtime.sse.event import Event, EventPriority, create_data_event, create_notification_event


# Type for the framework-specific response
ResponseType = TypeVar('ResponseType')

# Type for authentication result
AuthResult = TypeVar('AuthResult')

# Type for authentication handler
AuthHandler = Callable[[Dict[str, Any]], Awaitable[Optional[AuthResult]]]


class SSEManager(Generic[ResponseType]):
    """Manager for SSE connections.
    
    This class manages multiple SSE connections, providing methods for
    broadcasting events to all connections or targeted subsets.
    
    Attributes:
        require_authentication: Whether authentication is required.
        auth_handler: Optional authentication handler function.
    """
    
    def __init__(self, 
                require_authentication: bool = False,
                auth_handler: Optional[AuthHandler] = None,
                keep_alive: bool = True,
                keep_alive_interval: float = 30.0):
        """Initialize a new SSE manager.
        
        Args:
            require_authentication: Whether clients must authenticate.
            auth_handler: Optional function to handle authentication.
            keep_alive: Whether to send keep-alive comments.
            keep_alive_interval: Interval in seconds for keep-alive comments.
        """
        # Connections (we use WeakValueDictionary to avoid memory leaks)
        self._connections: weakref.WeakValueDictionary[str, SSEConnection] = weakref.WeakValueDictionary()
        # Track user to connection mapping (use sets since a user can have multiple connections)
        self._user_connections: Dict[str, Set[str]] = {}
        # Track subscription to connection mapping
        self._subscription_connections: Dict[str, Set[str]] = {}
        
        # Settings
        self.require_authentication = require_authentication
        self.auth_handler = auth_handler
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        
        self._logger = logging.getLogger(__name__)
    
    def get_connection(self, client_id: str) -> Optional[SSEConnection]:
        """Get a connection by client ID.
        
        Args:
            client_id: The client ID.
            
        Returns:
            The connection if found, None otherwise.
        """
        return self._connections.get(client_id)
    
    def get_connections_by_user(self, user_id: str) -> List[SSEConnection]:
        """Get all connections for a specific user.
        
        Args:
            user_id: The user ID.
            
        Returns:
            A list of connections belonging to the user.
        """
        client_ids = self._user_connections.get(user_id, set())
        return [
            conn for client_id in client_ids 
            if (conn := self._connections.get(client_id)) is not None
        ]
    
    def get_connections_by_subscription(self, subscription_id: str) -> List[SSEConnection]:
        """Get all connections with a specific subscription.
        
        Args:
            subscription_id: The subscription ID.
            
        Returns:
            A list of connections with the subscription.
        """
        client_ids = self._subscription_connections.get(subscription_id, set())
        return [
            conn for client_id in client_ids 
            if (conn := self._connections.get(client_id)) is not None
        ]
    
    @property
    def connection_count(self) -> int:
        """Get the current number of active connections.
        
        Returns:
            The number of active connections.
        """
        return len(self._connections)
    
    async def create_connection(self, 
                              response: ResponseType,
                              writer: AsyncResponseWriter,
                              client_id: Optional[str] = None,
                              client_info: Optional[Dict[str, Any]] = None,
                              auth_data: Optional[Dict[str, Any]] = None) -> SSEConnection:
        """Create a new SSE connection.
        
        Args:
            response: The framework-specific response object.
            writer: The async writer for sending SSE data.
            client_id: Optional client ID, generated if not provided.
            client_info: Optional information about the client.
            auth_data: Optional authentication data.
            
        Returns:
            The newly created SSE connection.
            
        Raises:
            AuthenticationError: If authentication is required but fails.
        """
        # Create the connection
        connection = SSEConnection(response, writer, client_id, client_info)
        
        # Store the connection (do this before authentication to ensure cleanup on error)
        self._connections[connection.client_id] = connection
        
        # Handle authentication if required
        if self.require_authentication:
            from uno.realtime.sse.errors import AuthenticationError, SSEErrorCode
            
            if not auth_data:
                # Clean up and raise error
                await self._remove_connection(connection.client_id)
                raise AuthenticationError(
                    SSEErrorCode.AUTHENTICATION_REQUIRED,
                    "Authentication is required"
                )
            
            if not self.auth_handler:
                # This is a programming error - we require auth but no handler is set
                self._logger.error("Authentication required but no auth_handler set")
                await self._remove_connection(connection.client_id)
                raise AuthenticationError(
                    SSEErrorCode.AUTHENTICATION_FAILED,
                    "Authentication handler not configured"
                )
            
            # Call the auth handler
            try:
                auth_result = await self.auth_handler(auth_data)
                if not auth_result:
                    await self._remove_connection(connection.client_id)
                    raise AuthenticationError(
                        SSEErrorCode.AUTHENTICATION_FAILED,
                        "Authentication failed"
                    )
                
                # Set the user ID on the connection
                user_id = str(auth_result)
                connection.user_id = user_id
                
                # Update user connections map
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(connection.client_id)
                
            except Exception as e:
                await self._remove_connection(connection.client_id)
                if isinstance(e, AuthenticationError):
                    raise
                raise AuthenticationError(
                    SSEErrorCode.AUTHENTICATION_FAILED,
                    f"Authentication error: {str(e)}"
                )
        
        # Start the connection
        await connection.start(keep_alive=self.keep_alive)
        
        self._logger.info(f"New SSE connection: {connection.client_id}")
        return connection
    
    async def close_connection(self, client_id: str) -> bool:
        """Close a specific connection.
        
        Args:
            client_id: The client ID to close.
            
        Returns:
            True if the connection was found and closed, False otherwise.
        """
        connection = self._connections.get(client_id)
        if not connection:
            return False
        
        await connection.stop()
        await self._remove_connection(client_id)
        return True
    
    async def add_subscription(self, 
                             client_id: str, 
                             subscription_id: str) -> bool:
        """Add a subscription to a connection.
        
        Args:
            client_id: The client ID.
            subscription_id: The subscription ID.
            
        Returns:
            True if the subscription was added, False if the connection was not found.
        """
        connection = self._connections.get(client_id)
        if not connection:
            return False
        
        connection.add_subscription(subscription_id)
        
        # Update subscription map
        if subscription_id not in self._subscription_connections:
            self._subscription_connections[subscription_id] = set()
        self._subscription_connections[subscription_id].add(client_id)
        
        return True
    
    async def remove_subscription(self, 
                                client_id: str, 
                                subscription_id: str) -> bool:
        """Remove a subscription from a connection.
        
        Args:
            client_id: The client ID.
            subscription_id: The subscription ID.
            
        Returns:
            True if the subscription was removed, False if the connection was not found.
        """
        connection = self._connections.get(client_id)
        if not connection:
            return False
        
        connection.remove_subscription(subscription_id)
        
        # Update subscription map
        if subscription_id in self._subscription_connections:
            self._subscription_connections[subscription_id].discard(client_id)
            if not self._subscription_connections[subscription_id]:
                del self._subscription_connections[subscription_id]
        
        return True
    
    async def broadcast_event(self, 
                           event: Event, 
                           filter_func: Optional[Callable[[SSEConnection], bool]] = None) -> int:
        """Broadcast an event to all connections.
        
        Args:
            event: The event to broadcast.
            filter_func: Optional function to filter connections.
            
        Returns:
            The number of connections that received the event.
        """
        sent_count = 0
        tasks = []
        
        # Get all active connections
        connections = list(self._connections.values())
        
        # Apply filter if provided
        if filter_func:
            connections = [conn for conn in connections if filter_func(conn)]
        
        # Send the event to all connections
        for connection in connections:
            if connection.is_connected:
                tasks.append(connection.send_event(event))
        
        # Wait for all send operations to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent_count = sum(1 for r in results if r is True)
        
        return sent_count
    
    async def broadcast_to_users(self, 
                               event: Event, 
                               user_ids: List[str]) -> int:
        """Broadcast an event to specific users.
        
        Args:
            event: The event to broadcast.
            user_ids: The list of user IDs to broadcast to.
            
        Returns:
            The number of connections that received the event.
        """
        return await self.broadcast_event(
            event,
            filter_func=lambda conn: conn.user_id is not None and conn.user_id in user_ids
        )
    
    async def broadcast_to_subscriptions(self, 
                                       event: Event, 
                                       subscription_ids: List[str]) -> int:
        """Broadcast an event to specific subscriptions.
        
        Args:
            event: The event to broadcast.
            subscription_ids: The list of subscription IDs to broadcast to.
            
        Returns:
            The number of connections that received the event.
        """
        # For efficiency, get all client IDs from subscription map first
        client_ids = set()
        for sub_id in subscription_ids:
            sub_clients = self._subscription_connections.get(sub_id, set())
            client_ids.update(sub_clients)
        
        # Only broadcast to connections in the client_ids set
        return await self.broadcast_event(
            event,
            filter_func=lambda conn: conn.client_id in client_ids
        )
    
    async def broadcast_data(self, 
                          resource: str, 
                          data: Any,
                          user_ids: Optional[List[str]] = None,
                          subscription_ids: Optional[List[str]] = None,
                          priority: EventPriority = EventPriority.NORMAL) -> int:
        """Broadcast data to connections.
        
        Args:
            resource: The resource identifier.
            data: The data to broadcast.
            user_ids: Optional list of user IDs to target.
            subscription_ids: Optional list of subscription IDs to target.
            priority: The priority of the event.
            
        Returns:
            The number of connections that received the data.
        """
        event = create_data_event(resource, data, priority)
        
        if user_ids and subscription_ids:
            # Broadcast to intersection of users and subscriptions
            client_ids = set()
            
            # Get client IDs for targeted users
            for user_id in user_ids:
                user_clients = self._user_connections.get(user_id, set())
                client_ids.update(user_clients)
            
            # Get client IDs for targeted subscriptions
            sub_client_ids = set()
            for sub_id in subscription_ids:
                sub_clients = self._subscription_connections.get(sub_id, set())
                sub_client_ids.update(sub_clients)
            
            # Only consider clients that match both criteria
            client_ids.intersection_update(sub_client_ids)
            
            return await self.broadcast_event(
                event,
                filter_func=lambda conn: conn.client_id in client_ids
            )
        elif user_ids:
            # Broadcast to specific users
            return await self.broadcast_to_users(event, user_ids)
        elif subscription_ids:
            # Broadcast to specific subscriptions
            return await self.broadcast_to_subscriptions(event, subscription_ids)
        else:
            # Broadcast to all connections
            return await self.broadcast_event(event)
    
    async def broadcast_notification(self, 
                                  title: str, 
                                  message: str, 
                                  level: str = "info",
                                  actions: Optional[List[Dict[str, Any]]] = None,
                                  user_ids: Optional[List[str]] = None,
                                  subscription_ids: Optional[List[str]] = None,
                                  priority: EventPriority = EventPriority.HIGH) -> int:
        """Broadcast a notification to connections.
        
        Args:
            title: The notification title.
            message: The notification message.
            level: The notification level.
            actions: Optional list of actions the user can take.
            user_ids: Optional list of user IDs to target.
            subscription_ids: Optional list of subscription IDs to target.
            priority: The priority of the notification.
            
        Returns:
            The number of connections that received the notification.
        """
        event = create_notification_event(title, message, level, actions, priority)
        
        if user_ids and subscription_ids:
            # Same logic as in broadcast_data for intersection
            client_ids = set()
            
            for user_id in user_ids:
                user_clients = self._user_connections.get(user_id, set())
                client_ids.update(user_clients)
            
            sub_client_ids = set()
            for sub_id in subscription_ids:
                sub_clients = self._subscription_connections.get(sub_id, set())
                sub_client_ids.update(sub_clients)
            
            client_ids.intersection_update(sub_client_ids)
            
            return await self.broadcast_event(
                event,
                filter_func=lambda conn: conn.client_id in client_ids
            )
        elif user_ids:
            return await self.broadcast_to_users(event, user_ids)
        elif subscription_ids:
            return await self.broadcast_to_subscriptions(event, subscription_ids)
        else:
            return await self.broadcast_event(event)
    
    async def _remove_connection(self, client_id: str) -> None:
        """Remove a connection from the manager's tracking.
        
        Args:
            client_id: The client ID to remove.
        """
        # Clean up connection tracking
        connection = self._connections.pop(client_id, None)
        if not connection:
            return
        
        # Clean up user tracking
        if connection.user_id:
            user_conns = self._user_connections.get(connection.user_id, set())
            user_conns.discard(client_id)
            if not user_conns:
                self._user_connections.pop(connection.user_id, None)
        
        # Clean up subscription tracking
        for sub_id in list(self._subscription_connections.keys()):
            sub_conns = self._subscription_connections.get(sub_id, set())
            sub_conns.discard(client_id)
            if not sub_conns:
                self._subscription_connections.pop(sub_id, None)
        
        self._logger.info(f"Removed SSE connection: {client_id}")


# FastAPI integration

async def sse_endpoint(manager: SSEManager, 
                      request,
                      subscription: Optional[str] = None,
                      auth_data: Optional[Dict[str, Any]] = None,
                      client_info: Optional[Dict[str, Any]] = None):
    """FastAPI endpoint handler for SSE connections.
    
    Example usage:
    ```
    @app.get("/sse")
    async def sse(request: Request, subscription: Optional[str] = None):
        auth_data = {"token": request.headers.get("Authorization")}
        client_info = {"ip": request.client.host}
        return await sse_endpoint(sse_manager, request, subscription, auth_data, client_info)
    ```
    
    Args:
        manager: The SSE manager instance.
        request: The FastAPI request object.
        subscription: Optional subscription ID to automatically subscribe to.
        auth_data: Optional authentication data.
        client_info: Optional client information.
        
    Returns:
        A StreamingResponse that maintains the SSE connection.
    """
    from starlette.responses import StreamingResponse
    from uno.realtime.sse.connection import FastAPISSEWriter
    
    async def event_stream():
        """Generate the SSE event stream."""
        # Headers are handled by StreamingResponse
        # Send initial comment to establish the connection
        yield ": SSE connection established\n\n"
        
        # Wait for disconnection (this will keep the connection open)
        disconnect = request.scope.get("app").get("lifespan", {}).get("shutdown", asyncio.Event())
        await disconnect.wait()
    
    # Create response object
    response = StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # For Nginx
        }
    )
    
    # Create writer adapter
    writer = FastAPISSEWriter(response)
    
    # Create the connection
    connection = await manager.create_connection(
        response, writer, client_info=client_info, auth_data=auth_data
    )
    
    # Add subscription if provided
    if subscription:
        await manager.add_subscription(connection.client_id, subscription)
    
    return response