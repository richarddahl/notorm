"""Notification system error definitions.

This module defines error types for notification operations in the Uno framework.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any


class NotificationErrorCode(Enum):
    """Error codes for notification operations."""
    
    # Delivery errors
    DELIVERY_FAILED = auto()
    DELIVERY_TIMEOUT = auto()
    
    # Storage errors
    STORAGE_ERROR = auto()
    NOTIFICATION_NOT_FOUND = auto()
    
    # Input validation errors
    INVALID_NOTIFICATION = auto()
    INVALID_RECIPIENT = auto()
    INVALID_CHANNEL = auto()
    
    # Operation errors
    OPERATION_FAILED = auto()
    UNSUPPORTED_OPERATION = auto()
    
    # Throttling errors
    RATE_LIMITED = auto()
    NOTIFICATION_REJECTED = auto()
    
    # System errors
    HUB_ERROR = auto()
    CONFIGURATION_ERROR = auto()


class NotificationError(Exception):
    """Base exception class for notification errors.
    
    Attributes:
        code: The error code.
        message: The error message.
        details: Optional dictionary with additional error details.
    """
    
    def __init__(self, 
                code: NotificationErrorCode,
                message: str,
                details: Optional[Dict[str, Any]] = None):
        """Initialize the notification error.
        
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


class DeliveryError(NotificationError):
    """Raised when notification delivery fails."""
    
    def __init__(self, 
                code: NotificationErrorCode = NotificationErrorCode.DELIVERY_FAILED,
                message: str = "Failed to deliver notification",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the delivery error.
        
        Args:
            code: The error code, defaults to DELIVERY_FAILED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class StorageError(NotificationError):
    """Raised when notification storage operations fail."""
    
    def __init__(self, 
                code: NotificationErrorCode = NotificationErrorCode.STORAGE_ERROR,
                message: str = "Notification storage operation failed",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the storage error.
        
        Args:
            code: The error code, defaults to STORAGE_ERROR.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class ValidationError(NotificationError):
    """Raised when notification validation fails."""
    
    def __init__(self, 
                code: NotificationErrorCode = NotificationErrorCode.INVALID_NOTIFICATION,
                message: str = "Invalid notification data",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the validation error.
        
        Args:
            code: The error code, defaults to INVALID_NOTIFICATION.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class RateLimitError(NotificationError):
    """Raised when notifications are rate limited."""
    
    def __init__(self, 
                code: NotificationErrorCode = NotificationErrorCode.RATE_LIMITED,
                message: str = "Notification rate limit exceeded",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the rate limit error.
        
        Args:
            code: The error code, defaults to RATE_LIMITED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)