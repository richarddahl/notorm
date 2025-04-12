"""Network adapters for the synchronization engine.

This module defines the interfaces for network adapters used by the
synchronization engine to communicate with remote servers.
"""

import abc
import logging
from typing import Dict, List, Any, Optional, Union, Set, Callable, AsyncIterator


class NetworkAdapter(abc.ABC):
    """Abstract base class for network adapters.
    
    Network adapters handle communication with remote servers for the
    synchronization engine, abstracting away the details of the specific
    protocol (REST, GraphQL, etc.).
    """
    
    def __init__(self):
        """Initialize the network adapter."""
        self.logger = logging.getLogger(__name__)
        self._online = True
    
    @property
    def online(self) -> bool:
        """Get the online status of the adapter.
        
        Returns:
            True if the adapter is online, False otherwise.
        """
        return self._online
    
    @online.setter
    def online(self, value: bool) -> None:
        """Set the online status of the adapter.
        
        Args:
            value: The new online status.
        """
        self._online = value
    
    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the network adapter.
        
        Raises:
            NetworkError: If initialization fails.
        """
        pass
    
    @abc.abstractmethod
    async def fetch_changes(
        self,
        collection: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch changes from the server.
        
        Args:
            collection: The collection name.
            query_params: Optional query parameters for filtering changes.
            
        Returns:
            An async iterator of records.
            
        Raises:
            NetworkError: If fetching changes fails.
            NotOnlineError: If the adapter is not online.
        """
        self._check_online()
    
    @abc.abstractmethod
    async def send_changes(
        self,
        collection: str,
        changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Send changes to the server.
        
        Args:
            collection: The collection name.
            changes: The changes to send.
            
        Returns:
            The server response for each change.
            
        Raises:
            NetworkError: If sending changes fails.
            NotOnlineError: If the adapter is not online.
        """
        self._check_online()
    
    @abc.abstractmethod
    async def fetch_record(
        self,
        collection: str,
        record_id: Any
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single record from the server.
        
        Args:
            collection: The collection name.
            record_id: The record ID.
            
        Returns:
            The record if found, None otherwise.
            
        Raises:
            NetworkError: If fetching the record fails.
            NotOnlineError: If the adapter is not online.
        """
        self._check_online()
    
    @abc.abstractmethod
    async def check_connection(self) -> bool:
        """Check if a connection to the server can be established.
        
        Returns:
            True if a connection can be established, False otherwise.
        """
        pass
    
    def _check_online(self) -> None:
        """Check if the adapter is online.
        
        Raises:
            NotOnlineError: If the adapter is not online.
        """
        if not self._online:
            from uno.offline.sync.errors import NotOnlineError
            raise NotOnlineError("Network adapter is offline")
    
    async def __aenter__(self):
        """Enter the async context."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        pass  # No resources to clean up


class BatchSupportMixin:
    """Mixin for network adapters that support batch operations.
    
    Batch operations allow for more efficient communication with the server
    by sending multiple changes in a single request.
    """
    
    @abc.abstractmethod
    async def fetch_changes_batch(
        self,
        collection: str,
        query_params: Optional[Dict[str, Any]] = None,
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch changes from the server in a batch.
        
        Args:
            collection: The collection name.
            query_params: Optional query parameters for filtering changes.
            batch_size: The maximum number of records to fetch.
            
        Returns:
            A list of records.
            
        Raises:
            NetworkError: If fetching changes fails.
            NotOnlineError: If the adapter is not online.
        """
        self._check_online()  # type: ignore
    
    @abc.abstractmethod
    async def send_changes_batch(
        self,
        collection: str,
        changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Send changes to the server in a batch.
        
        Args:
            collection: The collection name.
            changes: The changes to send.
            
        Returns:
            The server response for the batch.
            
        Raises:
            NetworkError: If sending changes fails.
            NotOnlineError: If the adapter is not online.
        """
        self._check_online()  # type: ignore