"""In-memory storage backend for the offline store.

This module provides an in-memory implementation of the storage backend
interface for the offline store.
"""

import copy
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
import logging

from uno.offline.store.storage import StorageBackend, Transaction
from uno.offline.store.options import StorageOptions, CollectionSchema
from uno.offline.store.transaction import MemoryTransaction
from uno.offline.store.query import Query, QueryResult, Filter, FilterOperator


class MemoryBackend(StorageBackend):
    """In-memory implementation of the storage backend.
    
    This backend stores all data in memory, making it suitable for
    testing and development but not for production use.
    """
    
    def __init__(self):
        """Initialize the in-memory backend."""
        self.logger = logging.getLogger(__name__)
        self._collections: Dict[str, Dict[str, Any]] = {}
        self._schemas: Dict[str, CollectionSchema] = {}
        self._initialized = False
        self._options: Optional[StorageOptions] = None
    
    async def initialize(self, options: StorageOptions) -> None:
        """Initialize the storage backend.
        
        Args:
            options: Storage configuration options.
            
        Raises:
            StorageError: If initialization fails.
        """
        if self._initialized:
            return
        
        self._options = options
        self._initialized = True
        self.logger.info("Initialized in-memory storage backend")
    
    async def close(self) -> None:
        """Close the storage backend.
        
        Raises:
            StorageError: If closing fails.
        """
        if not self._initialized:
            return
        
        # Clear all data
        self._collections = {}
        self._schemas = {}
        self._initialized = False
        self._options = None
        
        self.logger.info("Closed in-memory storage backend")
    
    async def create_collection(self, schema: CollectionSchema) -> None:
        """Create a new collection.
        
        Args:
            schema: Schema definition for the collection.
            
        Raises:
            StorageError: If collection creation fails.
        """
        self._ensure_initialized()
        
        if schema.name in self._collections:
            # Collection already exists, check if schema matches
            existing_schema = self._schemas[schema.name]
            if existing_schema.key_path != schema.key_path:
                raise ValueError(f"Cannot change key path for existing collection {schema.name}")
            
            # Update schema
            self._schemas[schema.name] = schema
            return
        
        # Create new collection
        self._collections[schema.name] = {}
        self._schemas[schema.name] = schema
        
        self.logger.info(f"Created collection {schema.name}")
    
    async def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: The name of the collection to delete.
            
        Raises:
            StorageError: If collection deletion fails.
        """
        self._ensure_initialized()
        
        if name not in self._collections:
            return
        
        # Delete collection
        del self._collections[name]
        del self._schemas[name]
        
        self.logger.info(f"Deleted collection {name}")
    
    async def clear_collection(self, name: str) -> None:
        """Clear all records from a collection.
        
        Args:
            name: The name of the collection to clear.
            
        Raises:
            StorageError: If clearing the collection fails.
        """
        self._ensure_initialized()
        
        if name not in self._collections:
            raise ValueError(f"Collection {name} does not exist")
        
        # Clear all records
        self._collections[name] = {}
        
        self.logger.info(f"Cleared collection {name}")
    
    async def create(self, collection: str, record: Dict[str, Any]) -> str:
        """Create a new record in a collection.
        
        Args:
            collection: The name of the collection.
            record: The record data to create.
            
        Returns:
            The ID of the created record.
            
        Raises:
            StorageError: If record creation fails.
        """
        self._ensure_initialized()
        self._ensure_collection_exists(collection)
        
        # Copy record to avoid modifying the original
        record = copy.deepcopy(record)
        
        # Get key field and value
        schema = self._schemas[collection]
        key_field = self._get_key_field(schema)
        
        # Generate key if not provided
        if key_field not in record:
            record[key_field] = str(uuid.uuid4())
        
        key = record[key_field]
        
        # Check if record already exists
        if key in self._collections[collection]:
            raise ValueError(f"Record with key {key} already exists in collection {collection}")
        
        # Store record
        self._collections[collection][key] = record
        
        return key
    
    async def read(self, collection: str, key: Any) -> Optional[Dict[str, Any]]:
        """Read a record from a collection.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            The record data, or None if not found.
            
        Raises:
            StorageError: If record reading fails.
        """
        self._ensure_initialized()
        self._ensure_collection_exists(collection)
        
        # Get record
        record = self._collections[collection].get(key)
        
        # Return copy to avoid modifying the stored record
        return copy.deepcopy(record) if record else None
    
    async def update(self, collection: str, record: Dict[str, Any]) -> bool:
        """Update a record in a collection.
        
        Args:
            collection: The name of the collection.
            record: The updated record data.
            
        Returns:
            True if the record was updated, False if not found.
            
        Raises:
            StorageError: If record update fails.
        """
        self._ensure_initialized()
        self._ensure_collection_exists(collection)
        
        # Copy record to avoid modifying the original
        record = copy.deepcopy(record)
        
        # Get key field and value
        schema = self._schemas[collection]
        key_field = self._get_key_field(schema)
        
        if key_field not in record:
            raise ValueError(f"Record does not have a value for key field {key_field}")
        
        key = record[key_field]
        
        # Check if record exists
        if key not in self._collections[collection]:
            return False
        
        # Update record
        self._collections[collection][key] = record
        
        return True
    
    async def delete(self, collection: str, key: Any) -> bool:
        """Delete a record from a collection.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            True if the record was deleted, False if not found.
            
        Raises:
            StorageError: If record deletion fails.
        """
        self._ensure_initialized()
        self._ensure_collection_exists(collection)
        
        # Check if record exists
        if key not in self._collections[collection]:
            return False
        
        # Delete record
        del self._collections[collection][key]
        
        return True
    
    async def query(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query records from a collection.
        
        Args:
            collection: The name of the collection.
            query: The query parameters.
            
        Returns:
            List of matching records.
            
        Raises:
            StorageError: If querying fails.
        """
        self._ensure_initialized()
        self._ensure_collection_exists(collection)
        
        # Parse query
        parsed_query = Query.parse(query)
        
        # Get all records
        records = list(self._collections[collection].values())
        
        # Filter records
        if parsed_query.filters:
            records = [r for r in records if parsed_query.matches(r)]
        
        # Sort records
        if parsed_query.sort:
            records = parsed_query.apply_sort(records)
        
        # Apply limit and offset
        records = parsed_query.apply_limit_offset(records)
        
        # Return copies to avoid modifying stored records
        return [copy.deepcopy(r) for r in records]
    
    async def count(self, collection: str, query: Optional[Dict[str, Any]] = None) -> int:
        """Count records in a collection.
        
        Args:
            collection: The name of the collection.
            query: Optional query parameters to filter the count.
            
        Returns:
            The number of matching records.
            
        Raises:
            StorageError: If counting fails.
        """
        self._ensure_initialized()
        self._ensure_collection_exists(collection)
        
        # If no query, return total count
        if not query:
            return len(self._collections[collection])
        
        # Parse query
        parsed_query = Query.parse(query)
        
        # Get all records
        records = list(self._collections[collection].values())
        
        # Filter records
        if parsed_query.filters:
            records = [r for r in records if parsed_query.matches(r)]
        
        return len(records)
    
    async def begin_transaction(self, collections: List[str]) -> Transaction:
        """Begin a transaction.
        
        Args:
            collections: The collections to include in the transaction.
            
        Returns:
            A transaction object.
            
        Raises:
            StorageError: If transaction creation fails.
        """
        self._ensure_initialized()
        
        # Check that all collections exist
        for collection in collections:
            self._ensure_collection_exists(collection)
        
        # Create transaction
        return MemoryTransaction(self, collections)
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage usage.
        
        Returns:
            A dictionary with storage information.
            
        Raises:
            StorageError: If getting storage info fails.
        """
        self._ensure_initialized()
        
        # Calculate storage usage
        collection_usage = {}
        total_records = 0
        
        for name, records in self._collections.items():
            record_count = len(records)
            collection_usage[name] = {
                "record_count": record_count,
                "size_estimate": self._estimate_size(records)
            }
            total_records += record_count
        
        return {
            "total_records": total_records,
            "collection_usage": collection_usage,
            "backend_type": "memory",
            "used_bytes": sum(info["size_estimate"] for info in collection_usage.values()),
            "available_bytes": None,  # Memory backend doesn't have a fixed size limit
        }
    
    async def compact(self) -> None:
        """Compact the storage to reclaim space.
        
        For in-memory storage, this is a no-op.
        
        Raises:
            StorageError: If compaction fails.
        """
        self._ensure_initialized()
        
        # Nothing to do for in-memory storage
        pass
    
    def get_key_field(self, collection: str) -> str:
        """Get the key field for a collection.
        
        Args:
            collection: The name of the collection.
            
        Returns:
            The name of the key field.
            
        Raises:
            ValueError: If the collection does not exist.
        """
        self._ensure_collection_exists(collection)
        return self._get_key_field(self._schemas[collection])
    
    def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized.
        
        Raises:
            RuntimeError: If the backend is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Storage backend not initialized")
    
    def _ensure_collection_exists(self, collection: str) -> None:
        """Ensure a collection exists.
        
        Args:
            collection: The name of the collection.
            
        Raises:
            ValueError: If the collection does not exist.
        """
        if collection not in self._collections:
            raise ValueError(f"Collection {collection} does not exist")
    
    def _get_key_field(self, schema: CollectionSchema) -> str:
        """Get the key field for a schema.
        
        Args:
            schema: The collection schema.
            
        Returns:
            The name of the key field.
        """
        if isinstance(schema.key_path, str):
            return schema.key_path
        elif isinstance(schema.key_path, list) and len(schema.key_path) > 0:
            return schema.key_path[0]
        else:
            raise ValueError(f"Invalid key path for collection {schema.name}")
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate the size of data in bytes.
        
        Args:
            data: The data to estimate.
            
        Returns:
            Estimated size in bytes.
        """
        if isinstance(data, dict):
            return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in data.items())
        elif isinstance(data, list):
            return sum(self._estimate_size(item) for item in data)
        elif isinstance(data, str):
            return len(data) * 2  # Approximate size for strings
        elif isinstance(data, (int, float, bool)):
            return 8  # Approximate size for numeric types
        elif data is None:
            return 4  # Approximate size for None
        else:
            return 16  # Default size for unknown types