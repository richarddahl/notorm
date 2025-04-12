"""Error classes for the synchronization engine.

This module defines the error hierarchy for synchronization operations.
"""
from typing import Dict, Any, Optional


class SyncError(Exception):
    """Base class for all synchronization errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a synchronization error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.details = details or {}


class NetworkError(SyncError):
    """Error raised when there's a network issue during synchronization."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a network error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(f"Network error: {message}", details)


class ConflictError(SyncError):
    """Error raised when there's a conflict between local and server data."""
    
    def __init__(
        self,
        message: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize a conflict error.
        
        Args:
            message: Error message
            local_data: The local version of the conflicting data
            server_data: The server version of the conflicting data
            details: Optional additional error details
        """
        super().__init__(f"Conflict error: {message}", details)
        self.local_data = local_data
        self.server_data = server_data


class SyncCancelledError(SyncError):
    """Error raised when synchronization is cancelled."""
    
    def __init__(self, message: str = "Synchronization was cancelled", details: Optional[Dict[str, Any]] = None):
        """Initialize a synchronization cancelled error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message, details)


class ConfigurationError(SyncError):
    """Error raised when there's an issue with synchronization configuration."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a configuration error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(f"Configuration error: {message}", details)


class StrategyError(SyncError):
    """Error raised when there's an issue with the synchronization strategy."""
    
    def __init__(self, message: str, strategy: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a strategy error.
        
        Args:
            message: Error message
            strategy: The strategy that caused the error
            details: Optional additional error details
        """
        super().__init__(f"Strategy error ({strategy}): {message}", details)
        self.strategy = strategy


class AdapterError(SyncError):
    """Error raised when there's an issue with the network adapter."""
    
    def __init__(self, message: str, adapter_name: str, details: Optional[Dict[str, Any]] = None):
        """Initialize an adapter error.
        
        Args:
            message: Error message
            adapter_name: The name of the adapter that caused the error
            details: Optional additional error details
        """
        super().__init__(f"Adapter error ({adapter_name}): {message}", details)
        self.adapter_name = adapter_name


class ConflictResolutionError(SyncError):
    """Error raised when conflict resolution fails."""
    
    def __init__(
        self,
        message: str,
        collection: str,
        record_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize a conflict resolution error.
        
        Args:
            message: Error message
            collection: The collection containing the conflict
            record_id: The ID of the record with the conflict
            details: Optional additional error details
        """
        super().__init__(
            f"Conflict resolution error ({collection}/{record_id}): {message}",
            details
        )
        self.collection = collection
        self.record_id = record_id


class ChangeTrackingError(SyncError):
    """Error raised when there's an issue with change tracking."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a change tracking error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(f"Change tracking error: {message}", details)