"""Server-Sent Events (SSE) error definitions.

This module defines error types for SSE operations in the Uno framework.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any


class SSEErrorCode(Enum):
    """Error codes for SSE operations."""
    
    # Connection errors
    CONNECTION_FAILED = auto()
    CONNECTION_CLOSED_UNEXPECTEDLY = auto()
    CONNECTION_REJECTED = auto()
    CONNECTION_TIMED_OUT = auto()
    
    # Authentication errors
    AUTHENTICATION_REQUIRED = auto()
    AUTHENTICATION_FAILED = auto()
    UNAUTHORIZED = auto()
    
    # Stream errors
    STREAM_ERROR = auto()
    STREAM_CLOSED = auto()
    
    # Server errors
    SERVER_ERROR = auto()
    SERVICE_UNAVAILABLE = auto()
    
    # Client errors
    CLIENT_ERROR = auto()
    
    # Operation errors
    OPERATION_FAILED = auto()
    SUBSCRIPTION_FAILED = auto()
    RESOURCE_NOT_FOUND = auto()


class SSEError(Exception):
    """Base exception class for SSE errors.
    
    Attributes:
        code: The error code.
        message: The error message.
        details: Optional dictionary with additional error details.
    """
    
    def __init__(self, 
                code: SSEErrorCode,
                message: str,
                details: Optional[Dict[str, Any]] = None):
        """Initialize the SSE error.
        
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


class ConnectionError(SSEError):
    """Raised when an SSE connection operation fails."""
    
    def __init__(self, 
                code: SSEErrorCode = SSEErrorCode.CONNECTION_FAILED,
                message: str = "Failed to establish or maintain SSE connection",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the connection error.
        
        Args:
            code: The error code, defaults to CONNECTION_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class AuthenticationError(SSEError):
    """Raised when SSE authentication fails."""
    
    def __init__(self, 
                code: SSEErrorCode = SSEErrorCode.AUTHENTICATION_FAILED,
                message: str = "SSE authentication failed",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the authentication error.
        
        Args:
            code: The error code, defaults to AUTHENTICATION_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class StreamError(SSEError):
    """Raised when there's an issue with an SSE stream."""
    
    def __init__(self, 
                code: SSEErrorCode = SSEErrorCode.STREAM_ERROR,
                message: str = "SSE stream error",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the stream error.
        
        Args:
            code: The error code, defaults to STREAM_ERROR.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class OperationError(SSEError):
    """Raised when an SSE operation fails."""
    
    def __init__(self, 
                code: SSEErrorCode = SSEErrorCode.OPERATION_FAILED,
                message: str = "SSE operation failed",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the operation error.
        
        Args:
            code: The error code, defaults to OPERATION_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)