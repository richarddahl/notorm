"""Transaction support for the offline store.

This module provides transaction support for the offline store,
allowing atomic operations across multiple collections.
"""

import abc
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Awaitable


class Transaction(abc.ABC):
    """Base class for transactions in the offline store.
    
    A transaction represents a sequence of operations that are performed
    atomically, meaning that either all operations succeed or none of them
    do.
    """
    
    def __init__(self, collections: List[str]):
        """Initialize a transaction.
        
        Args:
            collections: The collections involved in the transaction.
        """
        self.collections = collections
        self.logger = logging.getLogger(__name__)
        self._active = True
    
    @property
    def active(self) -> bool:
        """Get the active state of the transaction.
        
        Returns:
            True if the transaction is active, False otherwise.
        """
        return self._active
    
    @abc.abstractmethod
    async def create(self, collection: str, record: Dict[str, Any]) -> str:
        """Create a new record within the transaction.
        
        Args:
            collection: The name of the collection.
            record: The record data to create.
            
        Returns:
            The ID of the created record.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        self._check_collection(collection)
        self._check_active()
    
    @abc.abstractmethod
    async def read(self, collection: str, key: Any) -> Optional[Dict[str, Any]]:
        """Read a record within the transaction.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            The record data, or None if not found.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        self._check_collection(collection)
        self._check_active()
    
    @abc.abstractmethod
    async def update(self, collection: str, record: Dict[str, Any]) -> bool:
        """Update a record within the transaction.
        
        Args:
            collection: The name of the collection.
            record: The updated record data.
            
        Returns:
            True if the record was updated, False if not found.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        self._check_collection(collection)
        self._check_active()
    
    @abc.abstractmethod
    async def delete(self, collection: str, key: Any) -> bool:
        """Delete a record within the transaction.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            True if the record was deleted, False if not found.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        self._check_collection(collection)
        self._check_active()
    
    @abc.abstractmethod
    async def commit(self) -> None:
        """Commit the transaction.
        
        This finalizes all changes made within the transaction.
        
        Raises:
            RuntimeError: If the transaction is not active.
            TransactionError: If committing fails.
        """
        self._check_active()
    
    @abc.abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction.
        
        This discards all changes made within the transaction.
        
        Raises:
            RuntimeError: If the transaction is not active.
            TransactionError: If rollback fails.
        """
        self._check_active()
    
    def _check_collection(self, collection: str) -> None:
        """Check if a collection is part of the transaction.
        
        Args:
            collection: The name of the collection to check.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
        """
        if collection not in self.collections:
            raise ValueError(f"Collection {collection} is not part of this transaction")
    
    def _check_active(self) -> None:
        """Check if the transaction is active.
        
        Raises:
            RuntimeError: If the transaction is not active.
        """
        if not self._active:
            raise RuntimeError("Transaction is not active")
    

class MemoryTransaction(Transaction):
    """In-memory implementation of a transaction.
    
    This implementation keeps track of changes in memory and applies
    them all at once during commit.
    """
    
    def __init__(self, storage, collections: List[str]):
        """Initialize an in-memory transaction.
        
        Args:
            storage: The underlying storage manager.
            collections: The collections involved in the transaction.
        """
        super().__init__(collections)
        self._storage = storage
        self._changes: List[Dict[str, Any]] = []
    
    async def create(self, collection: str, record: Dict[str, Any]) -> str:
        """Create a new record within the transaction.
        
        Args:
            collection: The name of the collection.
            record: The record data to create.
            
        Returns:
            The ID of the created record.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        super().create(collection, record)
        
        # Generate a key if not provided
        key_field = self._storage.get_key_field(collection)
        if key_field not in record:
            from uuid import uuid4
            record[key_field] = str(uuid4())
        
        # Record the operation
        self._changes.append({
            "operation": "create",
            "collection": collection,
            "record": record.copy()
        })
        
        return record[key_field]
    
    async def read(self, collection: str, key: Any) -> Optional[Dict[str, Any]]:
        """Read a record within the transaction.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            The record data, or None if not found.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        super().read(collection, key)
        
        # Check if the record is in our pending changes
        key_field = self._storage.get_key_field(collection)
        
        # Check if the record was deleted in this transaction
        for change in reversed(self._changes):
            if (change["operation"] == "delete" and
                change["collection"] == collection and
                change["key"] == key):
                return None
            
            if (change["operation"] in ["create", "update"] and
                change["collection"] == collection and
                change["record"].get(key_field) == key):
                return change["record"].copy()
        
        # If not in pending changes, read from storage
        return await self._storage.read(collection, key)
    
    async def update(self, collection: str, record: Dict[str, Any]) -> bool:
        """Update a record within the transaction.
        
        Args:
            collection: The name of the collection.
            record: The updated record data.
            
        Returns:
            True if the record was updated, False if not found.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        super().update(collection, record)
        
        # Check if the record exists
        key_field = self._storage.get_key_field(collection)
        key = record.get(key_field)
        if key is None:
            raise ValueError(f"Record does not have a value for key field {key_field}")
        
        # Check if the record exists in our pending changes or in storage
        existing = await self.read(collection, key)
        if existing is None:
            return False
        
        # Record the operation
        self._changes.append({
            "operation": "update",
            "collection": collection,
            "record": record.copy()
        })
        
        return True
    
    async def delete(self, collection: str, key: Any) -> bool:
        """Delete a record within the transaction.
        
        Args:
            collection: The name of the collection.
            key: The record key.
            
        Returns:
            True if the record was deleted, False if not found.
            
        Raises:
            ValueError: If the collection is not part of the transaction.
            RuntimeError: If the transaction is not active.
            TransactionError: If the operation fails.
        """
        super().delete(collection, key)
        
        # Check if the record exists
        existing = await self.read(collection, key)
        if existing is None:
            return False
        
        # Record the operation
        self._changes.append({
            "operation": "delete",
            "collection": collection,
            "key": key
        })
        
        return True
    
    async def commit(self) -> None:
        """Commit the transaction.
        
        This applies all changes to the underlying storage.
        
        Raises:
            RuntimeError: If the transaction is not active.
            TransactionError: If committing fails.
        """
        super().commit()
        
        # Apply all changes to storage
        for change in self._changes:
            if change["operation"] == "create":
                await self._storage.create(change["collection"], change["record"])
            elif change["operation"] == "update":
                await self._storage.update(change["collection"], change["record"])
            elif change["operation"] == "delete":
                await self._storage.delete(change["collection"], change["key"])
        
        # Mark the transaction as inactive
        self._active = False
        self._changes = []
    
    async def rollback(self) -> None:
        """Rollback the transaction.
        
        This discards all pending changes.
        
        Raises:
            RuntimeError: If the transaction is not active.
            TransactionError: If rollback fails.
        """
        super().rollback()
        
        # Discard all changes
        self._active = False
        self._changes = []
    
    async def __aenter__(self):
        """Enter the transaction context."""
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the transaction context.
        
        Commits the transaction if no exception occurred,
        otherwise rolls it back.
        """
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()