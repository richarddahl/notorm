"""
Domain repositories for the Offline module.

This module defines repository interfaces and implementations for the Offline module.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator, Set, Union
from dataclasses import dataclass

from uno.core.result import Result
from uno.domain.repository import DomainRepository, AsyncDomainRepository

from uno.offline.entities import (
    StoreId,
    CollectionId,
    DocumentId,
    TransactionId,
    ChangeId,
    SyncId,
    ConflictId,
    StorageOptions,
    CollectionSchema,
    Document,
    Transaction,
    Change,
    SyncEvent,
    Conflict,
    NetworkState,
    ChangeType,
    SyncStatus
)


@runtime_checkable
class DocumentRepositoryProtocol(Protocol):
    """Protocol for document repository."""
    
    async def create(
        self, 
        collection_id: CollectionId, 
        data: Dict[str, Any]
    ) -> Result[Document]:
        """
        Create a new document.
        
        Args:
            collection_id: ID of the collection to create in
            data: Document data
            
        Returns:
            Result containing the created document or an error
        """
        ...
    
    async def get(
        self, 
        collection_id: CollectionId, 
        document_id: DocumentId
    ) -> Result[Document]:
        """
        Get a document by ID.
        
        Args:
            collection_id: Collection ID
            document_id: Document ID
            
        Returns:
            Result containing the document or an error if not found
        """
        ...
    
    async def update(
        self, 
        collection_id: CollectionId, 
        document_id: DocumentId, 
        data: Dict[str, Any]
    ) -> Result[Document]:
        """
        Update a document.
        
        Args:
            collection_id: Collection ID
            document_id: Document ID
            data: Updated data
            
        Returns:
            Result containing the updated document or an error
        """
        ...
    
    async def delete(
        self, 
        collection_id: CollectionId, 
        document_id: DocumentId
    ) -> Result[bool]:
        """
        Delete a document.
        
        Args:
            collection_id: Collection ID
            document_id: Document ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def query(
        self, 
        collection_id: CollectionId, 
        query: Dict[str, Any]
    ) -> Result[List[Document]]:
        """
        Query documents.
        
        Args:
            collection_id: Collection ID
            query: Query parameters
            
        Returns:
            Result containing a list of matching documents or an error
        """
        ...
    
    async def list(
        self, 
        collection_id: CollectionId, 
        limit: int = 100, 
        offset: int = 0
    ) -> Result[List[Document]]:
        """
        List documents in a collection.
        
        Args:
            collection_id: Collection ID
            limit: Maximum number of documents to return
            offset: Offset to start from
            
        Returns:
            Result containing a list of documents or an error
        """
        ...


@runtime_checkable
class CollectionRepositoryProtocol(Protocol):
    """Protocol for collection repository."""
    
    async def create(self, schema: CollectionSchema) -> Result[CollectionSchema]:
        """
        Create a new collection.
        
        Args:
            schema: Collection schema
            
        Returns:
            Result containing the created collection schema or an error
        """
        ...
    
    async def get(self, collection_id: CollectionId) -> Result[CollectionSchema]:
        """
        Get a collection by ID.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Result containing the collection schema or an error if not found
        """
        ...
    
    async def get_by_name(
        self, 
        store_id: StoreId, 
        name: str
    ) -> Result[CollectionSchema]:
        """
        Get a collection by name.
        
        Args:
            store_id: Store ID
            name: Collection name
            
        Returns:
            Result containing the collection schema or an error if not found
        """
        ...
    
    async def update(self, schema: CollectionSchema) -> Result[CollectionSchema]:
        """
        Update a collection schema.
        
        Args:
            schema: Updated collection schema
            
        Returns:
            Result containing the updated collection schema or an error
        """
        ...
    
    async def delete(self, collection_id: CollectionId) -> Result[bool]:
        """
        Delete a collection.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def list(self, store_id: StoreId) -> Result[List[CollectionSchema]]:
        """
        List collections in a store.
        
        Args:
            store_id: Store ID
            
        Returns:
            Result containing a list of collection schemas or an error
        """
        ...


@runtime_checkable
class TransactionRepositoryProtocol(Protocol):
    """Protocol for transaction repository."""
    
    async def create(self, transaction: Transaction) -> Result[Transaction]:
        """
        Create a new transaction.
        
        Args:
            transaction: Transaction to create
            
        Returns:
            Result containing the created transaction or an error
        """
        ...
    
    async def get(self, transaction_id: TransactionId) -> Result[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Result containing the transaction or an error if not found
        """
        ...
    
    async def update(self, transaction: Transaction) -> Result[Transaction]:
        """
        Update a transaction.
        
        Args:
            transaction: Updated transaction
            
        Returns:
            Result containing the updated transaction or an error
        """
        ...
    
    async def list_active(self, store_id: StoreId) -> Result[List[Transaction]]:
        """
        List active transactions for a store.
        
        Args:
            store_id: Store ID
            
        Returns:
            Result containing a list of active transactions or an error
        """
        ...


@runtime_checkable
class ChangeRepositoryProtocol(Protocol):
    """Protocol for change repository."""
    
    async def create(self, change: Change) -> Result[Change]:
        """
        Create a new change record.
        
        Args:
            change: Change to create
            
        Returns:
            Result containing the created change or an error
        """
        ...
    
    async def get(self, change_id: ChangeId) -> Result[Change]:
        """
        Get a change by ID.
        
        Args:
            change_id: Change ID
            
        Returns:
            Result containing the change or an error if not found
        """
        ...
    
    async def update(self, change: Change) -> Result[Change]:
        """
        Update a change.
        
        Args:
            change: Updated change
            
        Returns:
            Result containing the updated change or an error
        """
        ...
    
    async def list_unsynchronized(
        self, 
        collection_id: Optional[CollectionId] = None
    ) -> Result[List[Change]]:
        """
        List unsynchronized changes.
        
        Args:
            collection_id: Optional collection ID filter
            
        Returns:
            Result containing a list of unsynchronized changes or an error
        """
        ...
    
    async def mark_synchronized(self, change_id: ChangeId) -> Result[Change]:
        """
        Mark a change as synchronized.
        
        Args:
            change_id: Change ID
            
        Returns:
            Result containing the updated change or an error
        """
        ...


@runtime_checkable
class SyncRepositoryProtocol(Protocol):
    """Protocol for synchronization repository."""
    
    async def create(self, sync_event: SyncEvent) -> Result[SyncEvent]:
        """
        Create a new sync event.
        
        Args:
            sync_event: Sync event to create
            
        Returns:
            Result containing the created sync event or an error
        """
        ...
    
    async def get(self, sync_id: SyncId) -> Result[SyncEvent]:
        """
        Get a sync event by ID.
        
        Args:
            sync_id: Sync ID
            
        Returns:
            Result containing the sync event or an error if not found
        """
        ...
    
    async def update(self, sync_event: SyncEvent) -> Result[SyncEvent]:
        """
        Update a sync event.
        
        Args:
            sync_event: Updated sync event
            
        Returns:
            Result containing the updated sync event or an error
        """
        ...
    
    async def list_recent(
        self, 
        store_id: StoreId, 
        limit: int = 10
    ) -> Result[List[SyncEvent]]:
        """
        List recent sync events for a store.
        
        Args:
            store_id: Store ID
            limit: Maximum number of events to return
            
        Returns:
            Result containing a list of sync events or an error
        """
        ...
    
    async def get_last_successful(self, store_id: StoreId) -> Result[Optional[SyncEvent]]:
        """
        Get the last successful sync event for a store.
        
        Args:
            store_id: Store ID
            
        Returns:
            Result containing the last successful sync event or None if none exists
        """
        ...


@runtime_checkable
class ConflictRepositoryProtocol(Protocol):
    """Protocol for conflict repository."""
    
    async def create(self, conflict: Conflict) -> Result[Conflict]:
        """
        Create a new conflict.
        
        Args:
            conflict: Conflict to create
            
        Returns:
            Result containing the created conflict or an error
        """
        ...
    
    async def get(self, conflict_id: ConflictId) -> Result[Conflict]:
        """
        Get a conflict by ID.
        
        Args:
            conflict_id: Conflict ID
            
        Returns:
            Result containing the conflict or an error if not found
        """
        ...
    
    async def update(self, conflict: Conflict) -> Result[Conflict]:
        """
        Update a conflict.
        
        Args:
            conflict: Updated conflict
            
        Returns:
            Result containing the updated conflict or an error
        """
        ...
    
    async def list_unresolved(
        self, 
        sync_id: Optional[SyncId] = None
    ) -> Result[List[Conflict]]:
        """
        List unresolved conflicts.
        
        Args:
            sync_id: Optional sync ID filter
            
        Returns:
            Result containing a list of unresolved conflicts or an error
        """
        ...
    
    async def resolve(
        self, 
        conflict_id: ConflictId, 
        resolved_data: Dict[str, Any]
    ) -> Result[Conflict]:
        """
        Resolve a conflict.
        
        Args:
            conflict_id: Conflict ID
            resolved_data: Resolved data
            
        Returns:
            Result containing the resolved conflict or an error
        """
        ...


@runtime_checkable
class NetworkStateRepositoryProtocol(Protocol):
    """Protocol for network state repository."""
    
    async def get_current_state(self) -> Result[NetworkState]:
        """
        Get the current network state.
        
        Returns:
            Result containing the current network state or an error
        """
        ...
    
    async def update_state(self, state: NetworkState) -> Result[NetworkState]:
        """
        Update the network state.
        
        Args:
            state: Updated network state
            
        Returns:
            Result containing the updated network state or an error
        """
        ...


# Repository Implementations
class DocumentRepository(AsyncDomainRepository, DocumentRepositoryProtocol):
    """Implementation of document repository."""
    
    async def create(
        self, 
        collection_id: CollectionId, 
        data: Dict[str, Any]
    ) -> Result[Document]:
        """
        Create a new document.
        
        Args:
            collection_id: ID of the collection to create in
            data: Document data
            
        Returns:
            Result containing the created document or an error
        """
        try:
            # Generate ID if not provided
            document_id = DocumentId(data.get("id", str(uuid.uuid4())))
            
            # Create document
            document = Document(
                id=document_id,
                collection_id=collection_id,
                data=data,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            # Store document in database
            query = """
                INSERT INTO offline_documents (
                    id, collection_id, data, version, created_at, updated_at, deleted, deleted_at, metadata
                ) VALUES (
                    :id, :collection_id, :data, :version, :created_at, :updated_at, :deleted, :deleted_at, :metadata
                )
                RETURNING *
            """
            
            params = {
                "id": document.id.value,
                "collection_id": document.collection_id.value,
                "data": json.dumps(document.data),
                "version": document.version,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "deleted": document.deleted,
                "deleted_at": document.deleted_at,
                "metadata": json.dumps(document.metadata)
            }
            
            await self.db.query_one(query, params)
            
            # Create change record
            change = Change(
                id=ChangeId(str(uuid.uuid4())),
                document_id=document.id,
                collection_id=document.collection_id,
                change_type=ChangeType.CREATE,
                data=document.data,
                timestamp=document.created_at,
                version=document.version
            )
            
            change_query = """
                INSERT INTO offline_changes (
                    id, document_id, collection_id, change_type, data, timestamp, version, synchronized, metadata
                ) VALUES (
                    :id, :document_id, :collection_id, :change_type, :data, :timestamp, :version, :synchronized, :metadata
                )
            """
            
            change_params = {
                "id": change.id.value,
                "document_id": change.document_id.value,
                "collection_id": change.collection_id.value,
                "change_type": change.change_type.value,
                "data": json.dumps(change.data),
                "timestamp": change.timestamp,
                "version": change.version,
                "synchronized": change.synchronized,
                "metadata": json.dumps(change.metadata)
            }
            
            await self.db.query_one(change_query, change_params)
            
            return Result.success(document)
        except Exception as e:
            return Result.failure(f"Failed to create document: {str(e)}")
    
    # Implement other methods as defined in the protocol...


class CollectionRepository(AsyncDomainRepository, CollectionRepositoryProtocol):
    """Implementation of collection repository."""
    
    # Implement methods as defined in the protocol...


class TransactionRepository(AsyncDomainRepository, TransactionRepositoryProtocol):
    """Implementation of transaction repository."""
    
    # Implement methods as defined in the protocol...


class ChangeRepository(AsyncDomainRepository, ChangeRepositoryProtocol):
    """Implementation of change repository."""
    
    # Implement methods as defined in the protocol...


class SyncRepository(AsyncDomainRepository, SyncRepositoryProtocol):
    """Implementation of synchronization repository."""
    
    # Implement methods as defined in the protocol...


class ConflictRepository(AsyncDomainRepository, ConflictRepositoryProtocol):
    """Implementation of conflict repository."""
    
    # Implement methods as defined in the protocol...


class NetworkStateRepository(AsyncDomainRepository, NetworkStateRepositoryProtocol):
    """Implementation of network state repository."""
    
    # Implement methods as defined in the protocol...