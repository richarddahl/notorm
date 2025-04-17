"""WebSocket protocol implementation.

This module provides a protocol implementation for WebSocket connections.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set, Callable, Awaitable, Union, Protocol

from uno.realtime.websocket.connection import WebSocketConnection
from uno.realtime.websocket.message import Message, MessageType
from uno.realtime.websocket.errors import (
    WebSocketError,
    AuthenticationError,
    WebSocketErrorCode
)


class WebSocketProtocol(ABC):
    """Base class for WebSocket protocols.
    
    This abstract class defines the interface for WebSocket protocols, which handle
    the business logic of WebSocket communication.
    """
    
    @abstractmethod
    async def handle_connection_established(self, connection: WebSocketConnection) -> None:
        """Handle a new WebSocket connection.
        
        Args:
            connection: The WebSocket connection.
        """
        pass
    
    @abstractmethod
    async def handle_message(self, message: Message, connection: WebSocketConnection) -> None:
        """Handle a WebSocket message.
        
        Args:
            message: The message to handle.
            connection: The WebSocket connection.
        """
        pass
    
    @abstractmethod
    async def handle_connection_closed(self, 
                                      connection: WebSocketConnection, 
                                      code: int, 
                                      reason: str) -> None:
        """Handle a WebSocket connection being closed.
        
        Args:
            connection: The WebSocket connection.
            code: The close code.
            reason: The close reason.
        """
        pass
    
    @abstractmethod
    async def handle_error(self, 
                          connection: WebSocketConnection,
                          error: WebSocketError) -> None:
        """Handle a WebSocket error.
        
        Args:
            connection: The WebSocket connection.
            error: The error that occurred.
        """
        pass


class DefaultProtocol(WebSocketProtocol):
    """Default implementation of the WebSocket protocol.
    
    This class implements the basic WebSocket protocol with authentication and
    subscription support.
    """
    
    def __init__(self, 
                require_authentication: bool = True,
                auth_handler: Optional[Callable[[Dict[str, Any], WebSocketConnection], Awaitable[Optional[str]]]] = None):
        """Initialize the default protocol.
        
        Args:
            require_authentication: Whether authentication is required.
            auth_handler: Optional function to authenticate clients.
        """
        self.require_authentication = require_authentication
        self.auth_handler = auth_handler
    
    async def handle_connection_established(self, connection: WebSocketConnection) -> None:
        """Handle a new WebSocket connection.
        
        Args:
            connection: The WebSocket connection.
        """
        # Register message handlers
        connection.add_message_handler(MessageType.CONNECT, self._handle_connect)
        connection.add_message_handler(MessageType.AUTHENTICATE, self._handle_authenticate)
        connection.add_message_handler(MessageType.SUBSCRIBE, self._handle_subscribe)
        connection.add_message_handler(MessageType.UNSUBSCRIBE, self._handle_unsubscribe)
        
        # Send connection acknowledgement
        connect_ack = Message(
            type=MessageType.CONNECT_ACK,
            payload={
                "client_id": connection.client_id,
                "requires_auth": self.require_authentication
            }
        )
        await connection.send_message(connect_ack)
    
    async def handle_message(self, message: Message, connection: WebSocketConnection) -> None:
        """Handle a WebSocket message.
        
        Args:
            message: The message to handle.
            connection: The WebSocket connection.
        """
        # Check if authentication is required
        if (self.require_authentication and 
            not connection.authenticated and 
            message.type not in (MessageType.CONNECT, MessageType.AUTHENTICATE, MessageType.PING, MessageType.PONG)):
            # Authentication required
            error = AuthenticationError(
                WebSocketErrorCode.AUTHENTICATION_REQUIRED,
                "Authentication required"
            )
            await connection.handle_error(error)
            
            # Send error response
            error_response = message.create_error_response(
                error.code.name,
                error.message
            )
            await connection.send_message(error_response)
            return
        
        # Message is already being handled by the registered handlers
        pass
    
    async def handle_connection_closed(self, 
                                      connection: WebSocketConnection, 
                                      code: int, 
                                      reason: str) -> None:
        """Handle a WebSocket connection being closed.
        
        Args:
            connection: The WebSocket connection.
            code: The close code.
            reason: The close reason.
        """
        # Nothing to do here in the default implementation
        pass
    
    async def handle_error(self, 
                          connection: WebSocketConnection,
                          error: WebSocketError) -> None:
        """Handle a WebSocket error.
        
        Args:
            connection: The WebSocket connection.
            error: The error that occurred.
        """
        # Send error message to the client
        error_message = Message(
            type=MessageType.ERROR,
            payload=error.to_dict()["error"]
        )
        
        try:
            await connection.send_message(error_message)
        except Exception:
            # Ignore errors when sending the error message
            pass
    
    async def _handle_connect(self, message: Message, connection: WebSocketConnection) -> None:
        """Handle a CONNECT message.
        
        Args:
            message: The CONNECT message.
            connection: The WebSocket connection.
        """
        # CONNECT message is handled in handle_connection_established
        pass
    
    async def _handle_authenticate(self, message: Message, connection: WebSocketConnection) -> None:
        """Handle an AUTHENTICATE message.
        
        Args:
            message: The AUTHENTICATE message.
            connection: The WebSocket connection.
        """
        # Check if authentication is required
        if not self.require_authentication:
            # Authentication not required, but acknowledge it anyway
            auth_success = message.create_response(
                MessageType.AUTHENTICATE_SUCCESS,
                {
                    "user_id": None,
                    "message": "Authentication not required"
                }
            )
            await connection.send_message(auth_success)
            return
        
        # Get auth data from payload
        auth_data = message.payload.get("auth", {})
        
        try:
            # Authenticate using custom handler if provided
            user_id = None
            if self.auth_handler:
                user_id = await self.auth_handler(auth_data, connection)
            
            if user_id:
                # Authentication successful
                await connection.authenticate(user_id)
                
                # Send authentication success response
                auth_success = message.create_response(
                    MessageType.AUTHENTICATE_SUCCESS,
                    {
                        "user_id": user_id,
                    }
                )
                await connection.send_message(auth_success)
            else:
                # Authentication failed
                error = AuthenticationError(
                    WebSocketErrorCode.AUTHENTICATION_FAILED,
                    "Invalid authentication credentials"
                )
                await connection.handle_error(error)
                
                # Send authentication failure response
                auth_failure = message.create_response(
                    MessageType.AUTHENTICATE_FAILURE,
                    {
                        "error": {
                            "code": error.code.name,
                            "message": error.message
                        }
                    }
                )
                await connection.send_message(auth_failure)
        
        except Exception as e:
            # Authentication error
            error = AuthenticationError(
                WebSocketErrorCode.AUTHENTICATION_FAILED,
                str(e)
            )
            await connection.handle_error(error)
            
            # Send authentication failure response
            auth_failure = message.create_response(
                MessageType.AUTHENTICATE_FAILURE,
                {
                    "error": {
                        "code": error.code.name,
                        "message": error.message
                    }
                }
            )
            await connection.send_message(auth_failure)
    
    async def _handle_subscribe(self, message: Message, connection: WebSocketConnection) -> None:
        """Handle a SUBSCRIBE message.
        
        Args:
            message: The SUBSCRIBE message.
            connection: The WebSocket connection.
        """
        # Get subscription data from payload
        subscriptions = message.payload.get("subscriptions", [])
        if not isinstance(subscriptions, list):
            subscriptions = [subscriptions]
        
        # Add subscriptions
        added_subscriptions = []
        for subscription in subscriptions:
            try:
                await connection.add_subscription(subscription)
                added_subscriptions.append(subscription)
            except Exception as e:
                # Send subscription failure response
                sub_failure = message.create_response(
                    MessageType.SUBSCRIBE_FAILURE,
                    {
                        "subscription": subscription,
                        "error": {
                            "code": "SUBSCRIPTION_FAILED",
                            "message": str(e)
                        }
                    }
                )
                await connection.send_message(sub_failure)
        
        # Send subscription success response
        if added_subscriptions:
            sub_success = message.create_response(
                MessageType.SUBSCRIBE_SUCCESS,
                {
                    "subscriptions": added_subscriptions
                }
            )
            await connection.send_message(sub_success)
    
    async def _handle_unsubscribe(self, message: Message, connection: WebSocketConnection) -> None:
        """Handle an UNSUBSCRIBE message.
        
        Args:
            message: The UNSUBSCRIBE message.
            connection: The WebSocket connection.
        """
        # Get subscription data from payload
        subscriptions = message.payload.get("subscriptions", [])
        if not isinstance(subscriptions, list):
            subscriptions = [subscriptions]
        
        # Remove subscriptions
        for subscription in subscriptions:
            await connection.remove_subscription(subscription)
        
        # Send unsubscribe acknowledgement
        unsub_ack = message.create_response(
            MessageType.UNSUBSCRIBE_ACK,
            {
                "subscriptions": subscriptions
            }
        )
        await connection.send_message(unsub_ack)