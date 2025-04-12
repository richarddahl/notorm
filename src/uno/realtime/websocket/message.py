"""WebSocket message definitions.

This module defines the message structure for WebSocket communication.
"""

import json
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union, ClassVar


class MessageType(Enum):
    """Types of WebSocket messages."""
    
    # Connection lifecycle
    CONNECT = auto()
    CONNECT_ACK = auto()
    DISCONNECT = auto()
    
    # Authentication
    AUTHENTICATE = auto()
    AUTHENTICATE_SUCCESS = auto()
    AUTHENTICATE_FAILURE = auto()
    
    # Subscriptions
    SUBSCRIBE = auto()
    SUBSCRIBE_SUCCESS = auto()
    SUBSCRIBE_FAILURE = auto()
    UNSUBSCRIBE = auto()
    UNSUBSCRIBE_ACK = auto()
    
    # Data events
    EVENT = auto()
    DATA = auto()
    NOTIFICATION = auto()
    
    # Actions
    ACTION = auto()
    ACTION_RESULT = auto()
    
    # System messages
    PING = auto()
    PONG = auto()
    ERROR = auto()


@dataclass
class Message:
    """Represents a WebSocket message."""
    
    type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    # Serialization keys
    TYPE_KEY: ClassVar[str] = "type"
    PAYLOAD_KEY: ClassVar[str] = "payload"
    ID_KEY: ClassVar[str] = "id"
    CORRELATION_ID_KEY: ClassVar[str] = "correlation_id"
    TIMESTAMP_KEY: ClassVar[str] = "timestamp"
    
    @classmethod
    def create(cls, 
              message_type: MessageType, 
              payload: Optional[Dict[str, Any]] = None, 
              correlation_id: Optional[str] = None) -> "Message":
        """Create a new message.
        
        Args:
            message_type: The type of the message.
            payload: The message payload.
            correlation_id: Optional correlation ID for request-response pattern.
            
        Returns:
            A new Message instance.
        """
        return cls(
            type=message_type,
            payload=payload or {},
            correlation_id=correlation_id
        )
    
    @classmethod
    def from_json(cls, data: Union[str, bytes, Dict[str, Any]]) -> "Message":
        """Create a Message from JSON data.
        
        Args:
            data: JSON string, bytes, or already parsed dictionary.
            
        Returns:
            A Message instance.
            
        Raises:
            ValueError: If the JSON is invalid or missing required fields.
        """
        if isinstance(data, (str, bytes)):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            parsed_data = data
        
        if not isinstance(parsed_data, dict):
            raise ValueError(f"Invalid message format: expected dict, got {type(parsed_data)}")
        
        # Get required fields
        if cls.TYPE_KEY not in parsed_data:
            raise ValueError(f"Missing required field: {cls.TYPE_KEY}")
        
        try:
            message_type = MessageType[parsed_data[cls.TYPE_KEY]]
        except (KeyError, ValueError):
            raise ValueError(f"Invalid message type: {parsed_data.get(cls.TYPE_KEY)}")
        
        # Create the message
        return cls(
            type=message_type,
            payload=parsed_data.get(cls.PAYLOAD_KEY, {}),
            id=parsed_data.get(cls.ID_KEY, str(uuid.uuid4())),
            correlation_id=parsed_data.get(cls.CORRELATION_ID_KEY),
            timestamp=parsed_data.get(cls.TIMESTAMP_KEY, __import__('time').time())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary for serialization.
        
        Returns:
            A dictionary representation of the message.
        """
        return {
            self.TYPE_KEY: self.type.name,
            self.PAYLOAD_KEY: self.payload,
            self.ID_KEY: self.id,
            self.TIMESTAMP_KEY: self.timestamp,
            **({self.CORRELATION_ID_KEY: self.correlation_id} if self.correlation_id else {})
        }
    
    def to_json(self) -> str:
        """Convert the message to a JSON string.
        
        Returns:
            A JSON string representation of the message.
        """
        return json.dumps(self.to_dict())
    
    def create_response(self, 
                       message_type: MessageType, 
                       payload: Optional[Dict[str, Any]] = None) -> "Message":
        """Create a response message to this message.
        
        Args:
            message_type: The type of the response message.
            payload: The response payload.
            
        Returns:
            A new Message instance with correlation_id set to this message's id.
        """
        return Message(
            type=message_type,
            payload=payload or {},
            correlation_id=self.id
        )
    
    def create_error_response(self, 
                             error_code: str, 
                             error_message: str, 
                             details: Optional[Dict[str, Any]] = None) -> "Message":
        """Create an error response to this message.
        
        Args:
            error_code: The error code.
            error_message: The error message.
            details: Optional error details.
            
        Returns:
            A new ERROR Message instance with correlation_id set to this message's id.
        """
        return Message(
            type=MessageType.ERROR,
            payload={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    **({"details": details} if details else {})
                }
            },
            correlation_id=self.id
        )


# Convenience functions for common message types

def create_event_message(event_type: str, data: Any) -> Message:
    """Create an EVENT message.
    
    Args:
        event_type: The type of the event.
        data: The event data.
        
    Returns:
        An EVENT Message instance.
    """
    return Message(
        type=MessageType.EVENT,
        payload={
            "event_type": event_type,
            "data": data
        }
    )


def create_data_message(resource: str, data: Any) -> Message:
    """Create a DATA message.
    
    Args:
        resource: The resource the data belongs to.
        data: The data payload.
        
    Returns:
        A DATA Message instance.
    """
    return Message(
        type=MessageType.DATA,
        payload={
            "resource": resource,
            "data": data
        }
    )


def create_notification_message(title: str, message: str, level: str = "info", 
                               actions: Optional[List[Dict[str, Any]]] = None) -> Message:
    """Create a NOTIFICATION message.
    
    Args:
        title: The notification title.
        message: The notification message.
        level: The notification level (info, warning, error, etc.).
        actions: Optional list of actions the user can take.
        
    Returns:
        A NOTIFICATION Message instance.
    """
    return Message(
        type=MessageType.NOTIFICATION,
        payload={
            "title": title,
            "message": message,
            "level": level,
            **({"actions": actions} if actions else {})
        }
    )


def create_ping_message() -> Message:
    """Create a PING message.
    
    Returns:
        A PING Message instance.
    """
    return Message(type=MessageType.PING)


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