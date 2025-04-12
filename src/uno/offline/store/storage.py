"""Storage backend implementations for the offline store.

This module defines the interfaces and implementations for storage backends
used by the offline store.
"""

import abc
import logging
from typing import (
    Dict, List, Any, Optional, Union, TypeVar, Generic, 
    Protocol, Callable, Awaitable, Tuple
)

from uno.offline.store.options import StorageOptions, CollectionSchema


# Type variables for generic types
T = TypeVar('T')
K = TypeVar('K')


class StorageBackend(abc.ABC):
    """Abstract base class for storage backends.
    
    Storage backends provide low-level access to different storage mechanisms
    such as IndexedDB, WebSQL, LocalStorage, etc.
    """
    
    @abc.abstractmethod
    async def initialize(self, options: StorageOptions) -> None:
        """Initialize the storage backend.
        
        Args:
            options: Storage configuration options.
            
        Raises:
            StorageError: If initialization fails.
        """
        pass
    
    @abc.abstractmethod
    async def close(self) -> None:
        """Close the storage backend.
        
        Raises:
            StorageError: If closing fails.
        """
        pass
    
    @abc.abstractmethod
    async def create_collection(self, schema: CollectionSchema) -> None:
        """Create a new collection.
        
        Args:
            schema: Schema definition for the collection.
            
        Raises:
            StorageError: If collection creation fails.
        """
        pass
    
    @abc.abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: The name of the collection to delete.
            
        Raises:
            StorageError: If collection deletion fails.
        """
        pass
    
    @abc.abstractmethod
    async def clear_collection(self, name: str) -> None:
        """Clear all records from a collection.
        
        Args:
            name: The name of the collection to clear.
            
        Raises:
            StorageError: If clearing the collection fails.
        """
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    async def begin_transaction(self, collections: List[str]) -> 'Transaction':
        """Begin a transaction.
        
        Args:
            collections: The collections to include in the transaction.
            
        Returns:
            A transaction object.
            
        Raises:
            StorageError: If transaction creation fails.
        """
        pass
    
    @abc.abstractmethod
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage usage.
        
        Returns:
            A dictionary with storage information.
            
        Raises:
            StorageError: If getting storage info fails.
        """
        pass
    
    @abc.abstractmethod
    async def compact(self) -> None:
        """Compact the storage to reclaim space.
        
        Raises:
            StorageError: If compaction fails.
        """
        pass


class Transaction(abc.ABC):
    """Abstract base class for storage transactions.
    
    Transactions provide atomic operations across multiple collections.
    """
    
    @abc.abstractmethod
    async def create(self, collection: str, record: Dict[str, Any]) -> str:
        """Create a new record within the transaction.
        
        Args:
            collection: The name of the collection.
            record: The record data to create.
            
        Returns:
            The ID of the created record.
            
        Raises:
            StorageError: If record creation fails.
        """
        pass
    
    @abc.abstractmethod
    async def read(self, collection: str, key: Any) -> Optional[Dict[str, Any]]:
        """Read a record within the transaction.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            The record data, or None if not found.
            
        Raises:
            StorageError: If record reading fails.
        """
        pass
    
    @abc.abstractmethod
    async def update(self, collection: str, record: Dict[str, Any]) -> bool:
        """Update a record within the transaction.
        
        Args:
            collection: The name of the collection.
            record: The updated record data.
            
        Returns:
            True if the record was updated, False if not found.
            
        Raises:
            StorageError: If record update fails.
        """
        pass
    
    @abc.abstractmethod
    async def delete(self, collection: str, key: Any) -> bool:
        """Delete a record within the transaction.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            True if the record was deleted, False if not found.
            
        Raises:
            StorageError: If record deletion fails.
        """
        pass
    
    @abc.abstractmethod
    async def commit(self) -> None:
        """Commit the transaction.
        
        Raises:
            StorageError: If committing fails.
        """
        pass
    
    @abc.abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction.
        
        Raises:
            StorageError: If rollback fails.
        """
        pass


class StorageAdapter(Generic[T, K]):
    """Adapter for a specific storage backend.
    
    Storage adapters provide a bridge between the storage backends and 
    the storage manager, handling aspects like schema translation,
    record serialization, and type conversions.
    
    Type Parameters:
        T: The backend-specific transaction type.
        K: The backend-specific query type.
    """
    
    def __init__(self, backend: StorageBackend):
        """Initialize the storage adapter.
        
        Args:
            backend: The storage backend to adapt.
        """
        self.backend = backend
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, options: StorageOptions) -> None:
        """Initialize the storage adapter.
        
        Args:
            options: Storage configuration options.
            
        Raises:
            StorageError: If initialization fails.
        """
        await self.backend.initialize(options)
    
    async def close(self) -> None:
        """Close the storage adapter.
        
        Raises:
            StorageError: If closing fails.
        """
        await self.backend.close()
    
    async def create_collection(self, schema: CollectionSchema) -> None:
        """Create a new collection.
        
        Args:
            schema: Schema definition for the collection.
            
        Raises:
            StorageError: If collection creation fails.
        """
        await self.backend.create_collection(schema)
    
    async def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: The name of the collection to delete.
            
        Raises:
            StorageError: If collection deletion fails.
        """
        await self.backend.delete_collection(name)
    
    async def clear_collection(self, name: str) -> None:
        """Clear all records from a collection.
        
        Args:
            name: The name of the collection to clear.
            
        Raises:
            StorageError: If clearing the collection fails.
        """
        await self.backend.clear_collection(name)
    
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
        return await self.backend.create(collection, record)
    
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
        return await self.backend.read(collection, key)
    
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
        return await self.backend.update(collection, record)
    
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
        return await self.backend.delete(collection, key)
    
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
        return await self.backend.query(collection, query)
    
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
        return await self.backend.count(collection, query)
    
    async def begin_transaction(self, collections: List[str]) -> Transaction:
        """Begin a transaction.
        
        Args:
            collections: The collections to include in the transaction.
            
        Returns:
            A transaction object.
            
        Raises:
            StorageError: If transaction creation fails.
        """
        return await self.backend.begin_transaction(collections)
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage usage.
        
        Returns:
            A dictionary with storage information.
            
        Raises:
            StorageError: If getting storage info fails.
        """
        return await self.backend.get_storage_info()
    
    async def compact(self) -> None:
        """Compact the storage to reclaim space.
        
        Raises:
            StorageError: If compaction fails.
        """
        await self.backend.compact()


class StorageManager:
    """Manages storage operations across different backends.
    
    The storage manager coordinates operations across different storage
    backends, handling routing, caching, and other cross-cutting concerns.
    """
    
    def __init__(self, options: StorageOptions):
        """Initialize the storage manager.
        
        Args:
            options: Storage configuration options.
        """
        self.options = options
        self.logger = logging.getLogger(__name__)
        self.adapter = self._create_adapter()
        self._initialized = False
    
    def _create_adapter(self) -> StorageAdapter:
        """Create a storage adapter for the configured backend.
        
        Returns:
            A storage adapter for the configured backend.
            
        Raises:
            ValueError: If the storage backend is unknown.
        """
        if isinstance(self.options.storage_backend, str):
            backend_name = self.options.storage_backend.lower()
            
            if backend_name == "indexeddb":
                from uno.offline.store.backends.indexeddb import IndexedDBBackend
                return StorageAdapter(IndexedDBBackend())
            
            elif backend_name == "websql":
                from uno.offline.store.backends.websql import WebSQLBackend
                return StorageAdapter(WebSQLBackend())
            
            elif backend_name == "localstorage":
                from uno.offline.store.backends.localstorage import LocalStorageBackend
                return StorageAdapter(LocalStorageBackend())
            
            elif backend_name == "memory":
                from uno.offline.store.backends.memory import MemoryBackend
                return StorageAdapter(MemoryBackend())
            
            else:
                raise ValueError(f"Unknown storage backend: {backend_name}")
        else:
            # Custom backend
            return StorageAdapter(self.options.storage_backend)
    
    async def initialize(self) -> None:
        """Initialize the storage manager.
        
        Raises:
            StorageError: If initialization fails.
        """
        if self._initialized:
            return
        
        # Initialize the adapter
        await self.adapter.initialize(self.options)
        
        # Create collections
        for collection in self.options.collections:
            await self.adapter.create_collection(collection)
        
        # Run migrations if needed
        if self.options.migration_manager:
            await self.options.migration_manager.run_migrations(self)
        
        self._initialized = True
        self.logger.info(f"Storage manager initialized with {len(self.options.collections)} collections")
    
    async def close(self) -> None:
        """Close the storage manager.
        
        Raises:
            StorageError: If closing fails.
        """
        if not self._initialized:
            return
        
        await self.adapter.close()
        self._initialized = False
        self.logger.info("Storage manager closed")
    
    async def create_collection(self, schema: CollectionSchema) -> None:
        """Create a new collection.
        
        Args:
            schema: Schema definition for the collection.
            
        Raises:
            StorageError: If collection creation fails.
        """
        self._ensure_initialized()
        await self.adapter.create_collection(schema)
    
    async def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: The name of the collection to delete.
            
        Raises:
            StorageError: If collection deletion fails.
        """
        self._ensure_initialized()
        await self.adapter.delete_collection(name)
    
    async def clear_collection(self, name: str) -> None:
        """Clear all records from a collection.
        
        Args:
            name: The name of the collection to clear.
            
        Raises:
            StorageError: If clearing the collection fails.
        """
        self._ensure_initialized()
        await self.adapter.clear_collection(name)
    
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
        return await self.adapter.create(collection, record)
    
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
        return await self.adapter.read(collection, key)
    
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
        return await self.adapter.update(collection, record)
    
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
        return await self.adapter.delete(collection, key)
    
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
        return await self.adapter.query(collection, query)
    
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
        return await self.adapter.count(collection, query)
    
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
        return await self.adapter.begin_transaction(collections)
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage usage.
        
        Returns:
            A dictionary with storage information.
            
        Raises:
            StorageError: If getting storage info fails.
        """
        self._ensure_initialized()
        return await self.adapter.get_storage_info()
    
    async def compact(self) -> None:
        """Compact the storage to reclaim space.
        
        Raises:
            StorageError: If compaction fails.
        """
        self._ensure_initialized()
        await self.adapter.compact()
    
    def _ensure_initialized(self) -> None:
        """Ensure the storage manager is initialized.
        
        Raises:
            RuntimeError: If the storage manager is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Storage manager not initialized. Call initialize() first.")