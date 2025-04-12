"""WebSocket error definitions.

This module defines error types for WebSocket operations in the Uno framework.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any


class WebSocketErrorCode(Enum):
    """Error codes for WebSocket operations."""
    
    # Connection errors
    CONNECTION_FAILED = auto()
    CONNECTION_CLOSED_UNEXPECTEDLY = auto()
    CONNECTION_REJECTED = auto()
    CONNECTION_TIMED_OUT = auto()
    
    # Authentication errors
    AUTHENTICATION_REQUIRED = auto()
    AUTHENTICATION_FAILED = auto()
    UNAUTHORIZED = auto()
    
    # Message errors
    INVALID_MESSAGE_FORMAT = auto()
    MESSAGE_TOO_LARGE = auto()
    RATE_LIMITED = auto()
    
    # Protocol errors
    PROTOCOL_ERROR = auto()
    UNSUPPORTED_PROTOCOL_VERSION = auto()
    INCOMPATIBLE_EXTENSIONS = auto()
    
    # Server errors
    SERVER_ERROR = auto()
    SERVICE_UNAVAILABLE = auto()
    
    # Client errors
    CLIENT_ERROR = auto()
    
    # Operation errors
    OPERATION_FAILED = auto()
    SUBSCRIPTION_FAILED = auto()
    RESOURCE_NOT_FOUND = auto()


class WebSocketError(Exception):
    """Base exception class for WebSocket errors.
    
    Attributes:
        code: The error code.
        message: The error message.
        details: Optional dictionary with additional error details.
    """
    
    def __init__(self, 
                code: WebSocketErrorCode,
                message: str,
                details: Optional[Dict[str, Any]] = None):
        """Initialize the WebSocket error.
        
        Args:
            code: The error code.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code.name}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for serialization.
        
        Returns:
            A dictionary representation of the error.
        """
        return {
            "error": {
                "code": self.code.name,
                "message": self.message,
                "details": self.details
            }
        }


class ConnectionError(WebSocketError):
    """Raised when a WebSocket connection operation fails."""
    
    def __init__(self, 
                code: WebSocketErrorCode = WebSocketErrorCode.CONNECTION_FAILED,
                message: str = "Failed to establish or maintain WebSocket connection",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the connection error.
        
        Args:
            code: The error code, defaults to CONNECTION_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class AuthenticationError(WebSocketError):
    """Raised when WebSocket authentication fails."""
    
    def __init__(self, 
                code: WebSocketErrorCode = WebSocketErrorCode.AUTHENTICATION_FAILED,
                message: str = "WebSocket authentication failed",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the authentication error.
        
        Args:
            code: The error code, defaults to AUTHENTICATION_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class MessageError(WebSocketError):
    """Raised when there's an issue with a WebSocket message."""
    
    def __init__(self, 
                code: WebSocketErrorCode = WebSocketErrorCode.INVALID_MESSAGE_FORMAT,
                message: str = "Invalid WebSocket message format",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the message error.
        
        Args:
            code: The error code, defaults to INVALID_MESSAGE_FORMAT.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class ProtocolError(WebSocketError):
    """Raised when there's a WebSocket protocol error."""
    
    def __init__(self, 
                code: WebSocketErrorCode = WebSocketErrorCode.PROTOCOL_ERROR,
                message: str = "WebSocket protocol error",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the protocol error.
        
        Args:
            code: The error code, defaults to PROTOCOL_ERROR.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class OperationError(WebSocketError):
    """Raised when a WebSocket operation fails."""
    
    def __init__(self, 
                code: WebSocketErrorCode = WebSocketErrorCode.OPERATION_FAILED,
                message: str = "WebSocket operation failed",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the operation error.
        
        Args:
            code: The error code, defaults to OPERATION_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)