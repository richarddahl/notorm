"""Synchronization engine implementation.

This module provides the main SynchronizationEngine class that manages
the synchronization process between local and remote data.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Callable, Union, Tuple

from ..store.store import OfflineStore
from ..store.query import Query
from .options import SyncOptions
from .adapter import NetworkAdapter
from .errors import (
    SyncError,
    NetworkError,
    ConflictError,
    SyncCancelledError
)
from .tracker import ChangeTracker
from .conflict import ConflictResolver, ServerWinsResolver

logger = logging.getLogger(__name__)


class SynchronizationEngine:
    """Main class for managing synchronization between client and server.
    
    The SynchronizationEngine coordinates the synchronization process,
    including fetching changes from the server, sending local changes,
    and resolving conflicts when they arise.
    """
    
    def __init__(
        self,
        offline_store: OfflineStore,
        options: SyncOptions,
        network_adapter: Optional[NetworkAdapter] = None,
    ):
        """Initialize the synchronization engine.
        
        Args:
            offline_store: The offline store to synchronize
            options: Configuration options for synchronization
            network_adapter: The network adapter to use for communication
                             (if None, uses the one from options)
        """
        self.store = offline_store
        self.options = options
        self.network_adapter = network_adapter or options.network_adapter
        self.change_tracker = ChangeTracker(offline_store)
        
        # Set up conflict resolver
        if isinstance(self.options.conflict_strategy, str):
            if self.options.conflict_strategy == "server-wins":
                self.conflict_resolver = ServerWinsResolver()
            else:
                raise ValueError(f"Unknown conflict strategy: {self.options.conflict_strategy}")
        elif callable(self.options.conflict_strategy):
            self.conflict_resolver = ConflictResolver(self.options.conflict_strategy)
        else:
            self.conflict_resolver = self.options.conflict_strategy
        
        self._running = False
        self._cancel_requested = False
        self._sync_lock = asyncio.Lock()
    
    async def sync(self, collections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Synchronize data between client and server.
        
        Args:
            collections: Optional list of collections to synchronize.
                         If None, uses the collections from options.
        
        Returns:
            A dictionary with synchronization results.
        
        Raises:
            SyncError: If synchronization fails
            NetworkError: If there's a network issue
            ConflictError: If conflicts cannot be resolved
            SyncCancelledError: If synchronization was cancelled
        """
        if self._running:
            raise SyncError("Synchronization is already running")
        
        async with self._sync_lock:
            try:
                self._running = True
                self._cancel_requested = False
                
                # Determine which collections to sync
                collections_to_sync = collections or self.options.collections
                
                # Initialize results
                results = {
                    "collections": collections_to_sync,
                    "uploaded": 0,
                    "downloaded": 0,
                    "conflicts": 0,
                    "errors": [],
                    "details": {}
                }
                
                # Check if we're online
                if not await self.network_adapter.is_online():
                    raise NetworkError("Network is offline")
                
                # For each collection
                for collection in collections_to_sync:
                    if self._cancel_requested:
                        raise SyncCancelledError("Synchronization was cancelled")
                    
                    collection_result = await self._sync_collection(collection)
                    results["details"][collection] = collection_result
                    results["uploaded"] += collection_result.get("uploaded", 0)
                    results["downloaded"] += collection_result.get("downloaded", 0)
                    results["conflicts"] += collection_result.get("conflicts", 0)
                
                return results
            
            except Exception as e:
                if not isinstance(e, SyncCancelledError):
                    logger.exception("Synchronization failed")
                    if not isinstance(e, (SyncError, NetworkError, ConflictError)):
                        e = SyncError(f"Synchronization failed: {str(e)}")
                raise e
            
            finally:
                self._running = False
    
    async def _sync_collection(self, collection: str) -> Dict[str, Any]:
        """Synchronize a single collection.
        
        Args:
            collection: The collection name to synchronize
        
        Returns:
            A dictionary with collection synchronization results
        """
        result = {
            "collection": collection,
            "uploaded": 0,
            "downloaded": 0,
            "conflicts": 0,
            "errors": []
        }
        
        try:
            # Apply sync strategy for this collection
            if self.options.strategy == "pull-only":
                await self._pull_changes(collection, result)
            elif self.options.strategy == "push-only":
                await self._push_changes(collection, result)
            else:  # Two-way sync
                # Get last sync timestamp for this collection
                last_sync = await self.store.get_metadata(f"sync:{collection}:last_sync")
                
                # Push local changes
                await self._push_changes(collection, result)
                
                # Pull remote changes
                await self._pull_changes(collection, result, since=last_sync)
                
                # Update last sync timestamp
                await self.store.set_metadata(
                    f"sync:{collection}:last_sync",
                    self.network_adapter.get_server_timestamp()
                )
        
        except Exception as e:
            if self._cancel_requested:
                raise SyncCancelledError("Synchronization was cancelled")
            
            logger.error(f"Error syncing collection {collection}: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    async def _push_changes(self, collection: str, result: Dict[str, Any]) -> None:
        """Push local changes to the server.
        
        Args:
            collection: The collection to push changes for
            result: Dictionary to update with results
        """
        # Get local changes since last sync
        local_changes = await self.change_tracker.get_local_changes(collection)
        
        if not local_changes:
            return
        
        # Push changes to server
        for change in local_changes:
            try:
                if self._cancel_requested:
                    raise SyncCancelledError("Synchronization was cancelled")
                
                await self.network_adapter.send_change(collection, change)
                result["uploaded"] += 1
                
                # Mark as synchronized
                await self.change_tracker.mark_synchronized(collection, change["id"])
                
            except ConflictError as ce:
                # Handle conflict
                result["conflicts"] += 1
                resolved = await self._handle_conflict(collection, change, ce.server_data)
                
                if resolved:
                    result["uploaded"] += 1
                else:
                    result["errors"].append(f"Conflict could not be resolved for {change['id']}")
            
            except Exception as e:
                result["errors"].append(f"Failed to push change for {change['id']}: {str(e)}")
    
    async def _pull_changes(
        self, 
        collection: str, 
        result: Dict[str, Any],
        since: Optional[str] = None
    ) -> None:
        """Pull remote changes from the server.
        
        Args:
            collection: The collection to pull changes for
            result: Dictionary to update with results
            since: Optional timestamp to fetch changes since
        """
        query_params = {"since": since} if since else None
        
        async for remote_change in self.network_adapter.fetch_changes(collection, query_params):
            if self._cancel_requested:
                raise SyncCancelledError("Synchronization was cancelled")
            
            try:
                # Check if we have this item locally
                local_item = await self.store.get(collection, remote_change["id"])
                
                if not local_item:
                    # Just insert it
                    await self.store.put(collection, remote_change)
                    result["downloaded"] += 1
                else:
                    # Check for conflict
                    if local_item.get("updated_at") > remote_change.get("updated_at"):
                        # Local is newer, potential conflict
                        if self.change_tracker.has_unsynchronized_changes(collection, remote_change["id"]):
                            # We have unsynchronized changes, resolve conflict
                            result["conflicts"] += 1
                            resolved = await self._handle_conflict(
                                collection, local_item, remote_change
                            )
                            
                            if resolved:
                                result["downloaded"] += 1
                            else:
                                result["errors"].append(
                                    f"Conflict could not be resolved for {remote_change['id']}"
                                )
                        else:
                            # We don't have unsynchronized changes, just overwrite
                            await self.store.put(collection, remote_change)
                            result["downloaded"] += 1
                    else:
                        # Remote is newer, just overwrite
                        await self.store.put(collection, remote_change)
                        result["downloaded"] += 1
            
            except Exception as e:
                result["errors"].append(
                    f"Failed to pull change for {remote_change.get('id', 'unknown')}: {str(e)}"
                )
    
    async def _handle_conflict(
        self, 
        collection: str, 
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> bool:
        """Handle a conflict between local and server data.
        
        Args:
            collection: The collection containing the conflicting data
            local_data: The local version of the data
            server_data: The server version of the data
            
        Returns:
            True if the conflict was resolved, False otherwise
        """
        try:
            # Use the conflict resolver to resolve the conflict
            resolved_data = await self.conflict_resolver.resolve(
                collection, local_data, server_data
            )
            
            # Update the store with the resolved data
            await self.store.put(collection, resolved_data)
            
            # Mark as synchronized if we're using the server's version
            if resolved_data == server_data:
                await self.change_tracker.mark_synchronized(collection, local_data["id"])
                
            return True
        
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {str(e)}")
            return False
    
    def cancel(self) -> None:
        """Cancel an ongoing synchronization."""
        if self._running:
            self._cancel_requested = True