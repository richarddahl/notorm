"""Subscription management error definitions.

This module defines error types for subscription operations in the Uno framework.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any


class SubscriptionErrorCode(Enum):
    """Error codes for subscription operations."""
    
    # Input validation errors
    INVALID_SUBSCRIPTION = auto()
    INVALID_FILTER = auto()
    INVALID_TOPIC = auto()
    INVALID_RESOURCE = auto()
    INVALID_QUERY = auto()
    
    # Operation errors
    OPERATION_FAILED = auto()
    SUBSCRIPTION_EXISTS = auto()
    SUBSCRIPTION_NOT_FOUND = auto()
    SUBSCRIPTION_INACTIVE = auto()
    SUBSCRIPTION_LIMIT_REACHED = auto()
    
    # Permission errors
    PERMISSION_DENIED = auto()
    UNAUTHORIZED = auto()
    
    # System errors
    STORE_ERROR = auto()
    CONFIGURATION_ERROR = auto()


class SubscriptionError(Exception):
    """Base exception class for subscription errors.
    
    Attributes:
        code: The error code.
        message: The error message.
        details: Optional dictionary with additional error details.
    """
    
    def __init__(self, 
                code: SubscriptionErrorCode,
                message: str,
                details: Optional[Dict[str, Any]] = None):
        """Initialize the subscription error.
        
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


class ValidationError(SubscriptionError):
    """Raised when subscription validation fails."""
    
    def __init__(self, 
                code: SubscriptionErrorCode = SubscriptionErrorCode.INVALID_SUBSCRIPTION,
                message: str = "Invalid subscription data",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the validation error.
        
        Args:
            code: The error code, defaults to INVALID_SUBSCRIPTION.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class PermissionError(SubscriptionError):
    """Raised when a subscription operation is not permitted."""
    
    def __init__(self, 
                code: SubscriptionErrorCode = SubscriptionErrorCode.PERMISSION_DENIED,
                message: str = "Permission denied for subscription operation",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the permission error.
        
        Args:
            code: The error code, defaults to PERMISSION_DENIED.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)


class StoreError(SubscriptionError):
    """Raised when subscription storage operations fail."""
    
    def __init__(self, 
                code: SubscriptionErrorCode = SubscriptionErrorCode.STORE_ERROR,
                message: str = "Subscription storage operation failed",
                details: Optional[Dict[str, Any]] = None):
        """Initialize the store error.
        
        Args:
            code: The error code, defaults to STORE_ERROR.
            message: The error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(code, message, details)