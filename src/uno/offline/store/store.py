"""Offline store implementation.

This module provides the main OfflineStore class, which is the primary
interface for offline data storage and retrieval.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Set, TypeVar, Generic

from uno.offline.store.options import StorageOptions, CollectionSchema
from uno.offline.store.storage import StorageManager, Transaction
from uno.offline.store.query import Query, QueryResult


# Type variable for query results
T = TypeVar('T')


class OfflineStore:
    """Main interface for offline data storage and retrieval.
    
    The OfflineStore provides a high-level API for storing and retrieving
    data in the offline store, with support for transactions, querying,
    and relationship loading.
    """
    
    def __init__(self, options: StorageOptions):
        """Initialize the offline store.
        
        Args:
            options: Configuration options for the offline store.
        """
        self.options = options
        self.logger = logging.getLogger(__name__)
        self.storage = StorageManager(options)
        self._initialized = False
        
        # Set up compaction timer if auto-compaction is enabled
        self._compaction_task = None
        
        # Track relationships for collections
        self._relationships: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for collection in options.collections:
            self._register_relationships(collection)
    
    def _register_relationships(self, schema: CollectionSchema) -> None:
        """Register relationships for a collection.
        
        Args:
            schema: The collection schema.
        """
        if schema.name not in self._relationships:
            self._relationships[schema.name] = {}
        
        for rel in schema.relationships:
            self._relationships[schema.name][rel.name] = {
                "collection": rel.collection,
                "type": rel.type,
                "foreign_key": rel.foreign_key,
                "local_key": rel.local_key or (
                    schema.key_path if isinstance(schema.key_path, str) else schema.key_path[0]
                )
            }
    
    async def initialize(self) -> None:
        """Initialize the offline store.
        
        This initializes the underlying storage and starts the
        auto-compaction timer if enabled.
        
        Raises:
            StorageError: If initialization fails.
        """
        if self._initialized:
            return
        
        # Initialize storage
        await self.storage.initialize()
        self._initialized = True
        
        # Start auto-compaction if enabled
        if self.options.auto_compaction and self.options.compaction_interval > 0:
            self._start_auto_compaction()
        
        self.logger.info("Offline store initialized")
    
    async def close(self) -> None:
        """Close the offline store.
        
        This closes the underlying storage and stops the auto-compaction timer.
        
        Raises:
            StorageError: If closing fails.
        """
        if not self._initialized:
            return
        
        # Stop auto-compaction
        self._stop_auto_compaction()
        
        # Close storage
        await self.storage.close()
        self._initialized = False
        
        self.logger.info("Offline store closed")
    
    def _start_auto_compaction(self) -> None:
        """Start the auto-compaction timer."""
        if self._compaction_task is not None:
            return
        
        async def compaction_loop():
            while True:
                await asyncio.sleep(self.options.compaction_interval / 1000)
                try:
                    await self.compact()
                except Exception as e:
                    self.logger.error(f"Auto-compaction failed: {e}")
        
        self._compaction_task = asyncio.create_task(compaction_loop())
    
    def _stop_auto_compaction(self) -> None:
        """Stop the auto-compaction timer."""
        if self._compaction_task is None:
            return
        
        self._compaction_task.cancel()
        self._compaction_task = None
    
    def _ensure_initialized(self) -> None:
        """Ensure the offline store is initialized.
        
        Raises:
            RuntimeError: If the offline store is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Offline store not initialized. Call initialize() first.")
    
    async def create(self, collection: str, record: Dict[str, Any]) -> str:
        """Create a new record in a collection.
        
        Args:
            collection: The name of the collection.
            record: The record data to create.
            
        Returns:
            The ID of the created record.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If record creation fails.
        """
        self._ensure_initialized()
        return await self.storage.create(collection, record)
    
    async def create_batch(self, collection: str, records: List[Dict[str, Any]]) -> List[str]:
        """Create multiple records in a collection.
        
        Args:
            collection: The name of the collection.
            records: The records data to create.
            
        Returns:
            The IDs of the created records.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If batch creation fails.
        """
        self._ensure_initialized()
        
        # Start a transaction for batch operation
        transaction = await self.begin_transaction([collection])
        
        try:
            # Create each record in the transaction
            ids = []
            for record in records:
                id = await transaction.create(collection, record)
                ids.append(id)
            
            # Commit the transaction
            await transaction.commit()
            
            return ids
        except Exception as e:
            # Rollback on error
            await transaction.rollback()
            raise e
    
    async def get(self, collection: str, key: Any, include: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get a record from a collection.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            include: Optional list of relationships to include.
            
        Returns:
            The record data, or None if not found.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If getting the record fails.
        """
        self._ensure_initialized()
        
        # Get the base record
        record = await self.storage.read(collection, key)
        
        # If record not found or no relationships to include, return as is
        if record is None or not include:
            return record
        
        # Load included relationships
        return await self._load_relationships(collection, record, include)
    
    async def update(self, collection: str, record: Dict[str, Any]) -> bool:
        """Update a record in a collection.
        
        Args:
            collection: The name of the collection.
            record: The updated record data.
            
        Returns:
            True if the record was updated, False if not found.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If record update fails.
        """
        self._ensure_initialized()
        return await self.storage.update(collection, record)
    
    async def update_batch(self, collection: str, records: List[Dict[str, Any]]) -> int:
        """Update multiple records in a collection.
        
        Args:
            collection: The name of the collection.
            records: The records data to update.
            
        Returns:
            The number of records updated.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If batch update fails.
        """
        self._ensure_initialized()
        
        # Start a transaction for batch operation
        transaction = await self.begin_transaction([collection])
        
        try:
            # Update each record in the transaction
            count = 0
            for record in records:
                if await transaction.update(collection, record):
                    count += 1
            
            # Commit the transaction
            await transaction.commit()
            
            return count
        except Exception as e:
            # Rollback on error
            await transaction.rollback()
            raise e
    
    async def delete(self, collection: str, key: Any) -> bool:
        """Delete a record from a collection.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            True if the record was deleted, False if not found.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If record deletion fails.
        """
        self._ensure_initialized()
        return await self.storage.delete(collection, key)
    
    async def delete_batch(self, collection: str, keys: List[Any]) -> int:
        """Delete multiple records from a collection.
        
        Args:
            collection: The name of the collection.
            keys: The record keys to delete.
            
        Returns:
            The number of records deleted.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If batch deletion fails.
        """
        self._ensure_initialized()
        
        # Start a transaction for batch operation
        transaction = await self.begin_transaction([collection])
        
        try:
            # Delete each record in the transaction
            count = 0
            for key in keys:
                if await transaction.delete(collection, key):
                    count += 1
            
            # Commit the transaction
            await transaction.commit()
            
            return count
        except Exception as e:
            # Rollback on error
            await transaction.rollback()
            raise e
    
    async def query(
        self, 
        collection: str, 
        query_params: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> QueryResult[Dict[str, Any]]:
        """Query records from a collection.
        
        Args:
            collection: The name of the collection.
            query_params: The query parameters.
            include: Optional list of relationships to include.
            
        Returns:
            A QueryResult with the matching records.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If querying fails.
        """
        self._ensure_initialized()
        
        # Parse query parameters
        query = Query.parse(query_params or {})
        
        # Apply include from parameters if not explicitly provided
        if include is None and query.include:
            include = query.include
        
        # Query records
        records = await self.storage.query(collection, query.to_dict())
        
        # Count total records (for pagination)
        count_query = {k: v for k, v in (query_params or {}).items() if k not in ['limit', 'offset']}
        total = await self.storage.count(collection, count_query)
        
        # Load included relationships
        if records and include:
            loaded_records = []
            for record in records:
                loaded_record = await self._load_relationships(collection, record, include)
                loaded_records.append(loaded_record)
            records = loaded_records
        
        # Create result
        return QueryResult(
            items=records,
            total=total,
            limit=query.limit,
            offset=query.offset
        )
    
    async def count(self, collection: str, query_params: Optional[Dict[str, Any]] = None) -> int:
        """Count records in a collection.
        
        Args:
            collection: The name of the collection.
            query_params: Optional query parameters to filter the count.
            
        Returns:
            The number of matching records.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If counting fails.
        """
        self._ensure_initialized()
        return await self.storage.count(collection, query_params)
    
    async def begin_transaction(self, collections: List[str]) -> Transaction:
        """Begin a transaction.
        
        Args:
            collections: The collections to include in the transaction.
            
        Returns:
            A transaction object.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If transaction creation fails.
        """
        self._ensure_initialized()
        return await self.storage.begin_transaction(collections)
    
    async def clear(self, collections: Optional[List[str]] = None) -> None:
        """Clear data from specified collections.
        
        Args:
            collections: The collections to clear. If None, all collections are cleared.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If clearing fails.
        """
        self._ensure_initialized()
        
        if collections is None:
            # Clear all collections
            collections = [schema.name for schema in self.options.collections]
        
        # Clear each collection
        for collection in collections:
            await self.storage.clear_collection(collection)
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage usage.
        
        Returns:
            A dictionary with storage information.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If getting storage info fails.
        """
        self._ensure_initialized()
        return await self.storage.get_storage_info()
    
    async def compact(self) -> None:
        """Compact the storage to reclaim space.
        
        Raises:
            RuntimeError: If the offline store is not initialized.
            StorageError: If compaction fails.
        """
        self._ensure_initialized()
        await self.storage.compact()
    
    async def set_eviction_policy(self, collection: str, policy: Dict[str, Any]) -> None:
        """Set an eviction policy for a collection.
        
        Args:
            collection: The name of the collection.
            policy: The eviction policy configuration.
            
        Raises:
            RuntimeError: If the offline store is not initialized.
            ValueError: If the policy is invalid.
            StorageError: If setting the policy fails.
        """
        self._ensure_initialized()
        
        # Validate policy
        if "strategy" not in policy:
            raise ValueError("Eviction policy must include a strategy")
        
        valid_strategies = ["lru", "lfu", "fifo", "ttl", "size", "none"]
        if policy["strategy"] not in valid_strategies:
            raise ValueError(f"Invalid eviction strategy: {policy['strategy']}. "
                          f"Valid options are: {', '.join(valid_strategies)}")
        
        # Find the collection schema
        collection_schema = next(
            (schema for schema in self.options.collections if schema.name == collection),
            None
        )
        
        if collection_schema is None:
            raise ValueError(f"Collection {collection} not found")
        
        # Update schema with eviction policy
        collection_schema.eviction_policy = policy
    
    async def _load_relationships(
        self, 
        collection: str, 
        record: Dict[str, Any], 
        include: List[str]
    ) -> Dict[str, Any]:
        """Load related records for a record.
        
        Args:
            collection: The collection name.
            record: The base record.
            include: Names of relationships to include.
            
        Returns:
            The record with related records included.
            
        Raises:
            ValueError: If a relationship is not defined.
        """
        # Create a copy of the record to avoid modifying the original
        result = record.copy()
        
        # Load each relationship
        for rel_name in include:
            # Check if relationship exists
            if collection not in self._relationships or rel_name not in self._relationships[collection]:
                raise ValueError(f"Relationship {rel_name} not defined for collection {collection}")
            
            # Get relationship info
            rel_info = self._relationships[collection][rel_name]
            rel_type = rel_info["type"]
            rel_collection = rel_info["collection"]
            local_key = rel_info["local_key"]
            foreign_key = rel_info["foreign_key"]
            
            # Load related data based on relationship type
            if rel_type == "one-to-one" or rel_type == "many-to-one":
                # Load single related record
                if local_key in record:
                    local_value = record[local_key]
                    if local_value is not None:
                        # For many-to-one, query by foreign key
                        if rel_type == "many-to-one":
                            query_result = await self.query(
                                rel_collection,
                                {"filters": {foreign_key: local_value}}
                            )
                            if query_result.items:
                                result[rel_name] = query_result.items[0]
                            else:
                                result[rel_name] = None
                        else:
                            # For one-to-one, direct lookup by ID
                            related = await self.get(rel_collection, local_value)
                            result[rel_name] = related
                    else:
                        result[rel_name] = None
                else:
                    result[rel_name] = None
            
            elif rel_type == "one-to-many" or rel_type == "many-to-many":
                # Load multiple related records
                if local_key in record:
                    local_value = record[local_key]
                    if local_value is not None:
                        # Query related records
                        query_result = await self.query(
                            rel_collection,
                            {"filters": {foreign_key: local_value}}
                        )
                        result[rel_name] = query_result.items
                    else:
                        result[rel_name] = []
                else:
                    result[rel_name] = []
            
            else:
                # Unknown relationship type (shouldn't happen due to validation)
                result[rel_name] = None
        
        return result
    
    async def __aenter__(self):
        """Async context manager entry.
        
        Returns:
            The OfflineStore instance.
        """
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit.
        
        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        await self.close()