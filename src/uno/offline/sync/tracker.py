"""Change tracking for synchronization.

This module provides functionality for tracking changes that need to be
synchronized between client and server.
"""
import logging
from typing import Dict, List, Any, Optional, Set

from ..store.store import OfflineStore
from .errors import ChangeTrackingError

logger = logging.getLogger(__name__)


class ChangeTracker:
    """Tracks changes that need to be synchronized.
    
    The ChangeTracker is responsible for:
    1. Keeping track of changes made locally that need to be sent to the server
    2. Marking changes as synchronized when they've been successfully sent
    3. Providing information about which records have unsynchronized changes
    """
    
    def __init__(self, store: OfflineStore):
        """Initialize the change tracker.
        
        Args:
            store: The offline store to track changes for
        """
        self.store = store
        self._metadata_prefix = "sync:changes"
    
    async def track_change(self, collection: str, record_id: str) -> None:
        """Track a change to a record.
        
        Args:
            collection: The collection containing the record
            record_id: The ID of the record that changed
            
        Raises:
            ChangeTrackingError: If tracking fails
        """
        try:
            # Get the current set of unsynchronized changes
            changes = await self._get_unsynchronized_changes(collection)
            
            # Add the record ID if it's not already there
            if record_id not in changes:
                changes.add(record_id)
                await self._save_unsynchronized_changes(collection, changes)
                
                logger.debug(f"Tracked change to {collection}/{record_id}")
        except Exception as e:
            raise ChangeTrackingError(f"Failed to track change: {str(e)}")
    
    async def mark_synchronized(self, collection: str, record_id: str) -> None:
        """Mark a change as synchronized.
        
        Args:
            collection: The collection containing the record
            record_id: The ID of the record that was synchronized
            
        Raises:
            ChangeTrackingError: If marking fails
        """
        try:
            # Get the current set of unsynchronized changes
            changes = await self._get_unsynchronized_changes(collection)
            
            # Remove the record ID if it's there
            if record_id in changes:
                changes.remove(record_id)
                await self._save_unsynchronized_changes(collection, changes)
                
                logger.debug(f"Marked {collection}/{record_id} as synchronized")
        except Exception as e:
            raise ChangeTrackingError(f"Failed to mark as synchronized: {str(e)}")
    
    async def get_local_changes(self, collection: str) -> List[Dict[str, Any]]:
        """Get all local changes that need to be synchronized.
        
        Args:
            collection: The collection to get changes for
            
        Returns:
            A list of record data that needs to be synchronized
            
        Raises:
            ChangeTrackingError: If fetching changes fails
        """
        try:
            # Get the set of unsynchronized changes
            changes = await self._get_unsynchronized_changes(collection)
            
            # Get the actual record data
            result = []
            for record_id in changes:
                record = await self.store.get(collection, record_id)
                if record is not None:
                    result.append(record)
                else:
                    # Remove this ID from the changes since the record no longer exists
                    await self.mark_synchronized(collection, record_id)
            
            return result
        except Exception as e:
            if isinstance(e, ChangeTrackingError):
                raise
            raise ChangeTrackingError(f"Failed to get local changes: {str(e)}")
    
    def has_unsynchronized_changes(self, collection: str, record_id: str) -> bool:
        """Check if a record has unsynchronized changes.
        
        Args:
            collection: The collection containing the record
            record_id: The ID of the record to check
            
        Returns:
            True if the record has unsynchronized changes, False otherwise
            
        Note:
            This is a synchronous method that should only be used when you've
            already loaded the unsynchronized changes. For other cases, use
            get_local_changes instead.
        """
        # This is a synchronous method for checking during conflict resolution
        # It's not 100% accurate (needs to check the metadata) but it's fast
        # when resolving conflicts during pull operations
        metadata_key = f"{self._metadata_prefix}:{collection}"
        changes_str = self.store.get_metadata_sync(metadata_key)
        
        if changes_str:
            try:
                changes = set(changes_str.split(","))
                return record_id in changes
            except Exception:
                return False
        
        return False
    
    async def _get_unsynchronized_changes(self, collection: str) -> Set[str]:
        """Get the set of record IDs with unsynchronized changes.
        
        Args:
            collection: The collection to get changes for
            
        Returns:
            A set of record IDs with unsynchronized changes
        """
        metadata_key = f"{self._metadata_prefix}:{collection}"
        changes_str = await self.store.get_metadata(metadata_key)
        
        if changes_str:
            return set(changes_str.split(","))
        
        return set()
    
    async def _save_unsynchronized_changes(self, collection: str, changes: Set[str]) -> None:
        """Save the set of record IDs with unsynchronized changes.
        
        Args:
            collection: The collection to save changes for
            changes: The set of record IDs with unsynchronized changes
        """
        metadata_key = f"{self._metadata_prefix}:{collection}"
        
        if changes:
            changes_str = ",".join(changes)
            await self.store.set_metadata(metadata_key, changes_str)
        else:
            # If there are no changes, remove the metadata entry
            await self.store.delete_metadata(metadata_key)