"""Conflict resolution strategies for synchronization.

This module provides conflict resolution strategies for handling data conflicts
during synchronization between client and server.
"""
import logging
import abc
from typing import Dict, Any, Callable, Optional, Coroutine, TypeVar, Union

from .errors import ConflictResolutionError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Dict[str, Any])
ConflictResolverFunction = Callable[
    [str, Dict[str, Any], Dict[str, Any]],
    Union[Dict[str, Any], Coroutine[Any, Any, Dict[str, Any]]]
]


class ConflictResolverBase(abc.ABC):
    """Base class for conflict resolvers."""
    
    @abc.abstractmethod
    async def resolve(
        self,
        collection: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a conflict between local and server data.
        
        Args:
            collection: The collection containing the conflict
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            The resolved data
            
        Raises:
            ConflictResolutionError: If the conflict cannot be resolved
        """
        pass


class ServerWinsResolver(ConflictResolverBase):
    """A conflict resolver that always chooses the server's version."""
    
    async def resolve(
        self,
        collection: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a conflict by choosing the server's version.
        
        Args:
            collection: The collection containing the conflict
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            The server's version of the data
        """
        logger.debug(
            f"Resolving conflict in {collection}/{local_data.get('id')} using server-wins strategy"
        )
        return server_data


class ClientWinsResolver(ConflictResolverBase):
    """A conflict resolver that always chooses the client's version."""
    
    async def resolve(
        self,
        collection: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a conflict by choosing the client's version.
        
        Args:
            collection: The collection containing the conflict
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            The client's version of the data
        """
        logger.debug(
            f"Resolving conflict in {collection}/{local_data.get('id')} using client-wins strategy"
        )
        return local_data


class TimestampBasedResolver(ConflictResolverBase):
    """A conflict resolver that chooses the most recent version based on timestamps."""
    
    def __init__(self, timestamp_field: str = "updated_at"):
        """Initialize the timestamp-based resolver.
        
        Args:
            timestamp_field: The field containing the timestamp to compare
        """
        self.timestamp_field = timestamp_field
    
    async def resolve(
        self,
        collection: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a conflict by choosing the most recent version.
        
        Args:
            collection: The collection containing the conflict
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            The most recent version of the data
            
        Raises:
            ConflictResolutionError: If the timestamp field is missing
        """
        local_ts = local_data.get(self.timestamp_field)
        server_ts = server_data.get(self.timestamp_field)
        
        if local_ts is None or server_ts is None:
            raise ConflictResolutionError(
                f"Missing timestamp field '{self.timestamp_field}'",
                collection,
                local_data.get("id", "unknown")
            )
        
        if local_ts > server_ts:
            logger.debug(
                f"Resolving conflict in {collection}/{local_data.get('id')} using timestamp strategy: client wins"
            )
            return local_data
        else:
            logger.debug(
                f"Resolving conflict in {collection}/{local_data.get('id')} using timestamp strategy: server wins"
            )
            return server_data


class MergeFieldsResolver(ConflictResolverBase):
    """A conflict resolver that merges specific fields from both versions."""
    
    def __init__(
        self,
        client_fields: Optional[list[str]] = None,
        server_fields: Optional[list[str]] = None,
        timestamp_field: str = "updated_at"
    ):
        """Initialize the merge fields resolver.
        
        Args:
            client_fields: Fields to take from the client version
            server_fields: Fields to take from the server version
            timestamp_field: Field to use for timestamp comparison for unlisted fields
        """
        self.client_fields = client_fields or []
        self.server_fields = server_fields or []
        self.timestamp_field = timestamp_field
    
    async def resolve(
        self,
        collection: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a conflict by merging fields from both versions.
        
        Args:
            collection: The collection containing the conflict
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            The merged data
        """
        result = server_data.copy()
        
        # Apply client fields
        for field in self.client_fields:
            if field in local_data:
                result[field] = local_data[field]
        
        # For fields not explicitly listed, use the timestamp
        local_ts = local_data.get(self.timestamp_field)
        server_ts = server_data.get(self.timestamp_field)
        
        if local_ts is not None and server_ts is not None and local_ts > server_ts:
            # Local is newer, so use local fields that aren't explicitly set to use server
            for field, value in local_data.items():
                if (field not in self.server_fields and 
                    field not in self.client_fields and
                    field != "id"):
                    result[field] = value
        
        logger.debug(
            f"Resolved conflict in {collection}/{local_data.get('id')} using merge fields strategy"
        )
        return result


class ConflictResolver(ConflictResolverBase):
    """A conflict resolver that uses a custom function to resolve conflicts."""
    
    def __init__(self, resolver_function: ConflictResolverFunction):
        """Initialize the custom function resolver.
        
        Args:
            resolver_function: The function to use for conflict resolution
        """
        self.resolver_function = resolver_function
    
    async def resolve(
        self,
        collection: str,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve a conflict using the custom function.
        
        Args:
            collection: The collection containing the conflict
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            The resolved data
            
        Raises:
            ConflictResolutionError: If the resolver function fails
        """
        try:
            result = self.resolver_function(collection, local_data, server_data)
            
            # Handle both synchronous and asynchronous resolver functions
            if hasattr(result, "__await__"):
                result = await result
            
            if not isinstance(result, dict):
                raise ConflictResolutionError(
                    "Resolver function returned a non-dict value",
                    collection,
                    local_data.get("id", "unknown")
                )
            
            logger.debug(
                f"Resolved conflict in {collection}/{local_data.get('id')} using custom resolver"
            )
            return result
            
        except Exception as e:
            if isinstance(e, ConflictResolutionError):
                raise
            
            raise ConflictResolutionError(
                f"Resolver function failed: {str(e)}",
                collection,
                local_data.get("id", "unknown")
            )