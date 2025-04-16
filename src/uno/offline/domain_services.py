"""
Domain services for the Offline module.

This module defines the core domain services for the Offline module,
providing high-level operations for offline storage and synchronization.
"""

import logging
import asyncio
import json
import time
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic

from uno.core.result import Result
from uno.domain.service import DomainService

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
    StorageType,
    ChangeType,
    SyncStatus,
    SyncDirection,
    ConflictResolutionStrategy,
    NetworkStatus
)
from uno.offline.domain_repositories import (
    DocumentRepositoryProtocol,
    CollectionRepositoryProtocol,
    TransactionRepositoryProtocol,
    ChangeRepositoryProtocol,
    SyncRepositoryProtocol,
    ConflictRepositoryProtocol,
    NetworkStateRepositoryProtocol
)


class DocumentService(DomainService):
    """Service for managing documents in the offline store."""
    
    def __init__(
        self,
        document_repository: DocumentRepositoryProtocol,
        change_repository: ChangeRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the document service.
        
        Args:
            document_repository: Document repository
            change_repository: Change repository
            logger: Optional logger
        """
        self.document_repository = document_repository
        self.change_repository = change_repository
        self.logger = logger or logging.getLogger("uno.offline.document")
    
    async def create_document(
        self,
        collection_id: CollectionId,
        data: Dict[str, Any]
    ) -> Result[Document]:
        """
        Create a new document.
        
        Args:
            collection_id: Collection ID
            data: Document data
            
        Returns:
            Result containing the created document or an error
        """
        return await self.document_repository.create(collection_id, data)
    
    async def get_document(
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
        return await self.document_repository.get(collection_id, document_id)
    
    async def update_document(
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
        # Get existing document
        document_result = await self.document_repository.get(collection_id, document_id)
        if document_result.is_failure():
            return document_result
        
        document = document_result.value
        
        # Update document
        result = await self.document_repository.update(collection_id, document_id, data)
        if result.is_failure():
            return result
        
        updated_document = result.value
        
        # Create change record
        change = Change(
            id=ChangeId(str(uuid.uuid4())),
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.UPDATE,
            data=data,
            timestamp=updated_document.updated_at,
            version=updated_document.version
        )
        
        await self.change_repository.create(change)
        
        return result
    
    async def delete_document(
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
        # Get existing document before deleting
        document_result = await self.document_repository.get(collection_id, document_id)
        if document_result.is_failure():
            return document_result
        
        # Delete document
        result = await self.document_repository.delete(collection_id, document_id)
        if result.is_failure():
            return result
        
        # Create change record
        change = Change(
            id=ChangeId(str(uuid.uuid4())),
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.DELETE,
            timestamp=datetime.now(UTC),
            version=document_result.value.version + 1
        )
        
        await self.change_repository.create(change)
        
        return result
    
    async def query_documents(
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
        return await self.document_repository.query(collection_id, query)
    
    async def list_documents(
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
        return await self.document_repository.list(collection_id, limit, offset)


class CollectionService(DomainService):
    """Service for managing collections in the offline store."""
    
    def __init__(
        self,
        collection_repository: CollectionRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the collection service.
        
        Args:
            collection_repository: Collection repository
            logger: Optional logger
        """
        self.collection_repository = collection_repository
        self.logger = logger or logging.getLogger("uno.offline.collection")
    
    async def create_collection(
        self,
        store_id: StoreId,
        name: str,
        key_path: Union[str, List[str]],
        **kwargs
    ) -> Result[CollectionSchema]:
        """
        Create a new collection.
        
        Args:
            store_id: Store ID
            name: Collection name
            key_path: Path to the primary key
            **kwargs: Additional collection properties
            
        Returns:
            Result containing the created collection schema or an error
        """
        try:
            # Check if collection already exists
            existing_result = await self.collection_repository.get_by_name(store_id, name)
            if existing_result.is_success():
                return Result.failure(f"Collection '{name}' already exists")
            
            # Create collection schema
            schema = CollectionSchema(
                id=CollectionId(str(uuid.uuid4())),
                name=name,
                store_id=store_id,
                key_path=key_path,
                **kwargs
            )
            
            # Create collection
            return await self.collection_repository.create(schema)
        except Exception as e:
            self.logger.error(f"Failed to create collection: {str(e)}")
            return Result.failure(f"Failed to create collection: {str(e)}")
    
    async def get_collection(self, collection_id: CollectionId) -> Result[CollectionSchema]:
        """
        Get a collection by ID.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Result containing the collection schema or an error if not found
        """
        return await self.collection_repository.get(collection_id)
    
    async def get_collection_by_name(
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
        return await self.collection_repository.get_by_name(store_id, name)
    
    async def update_collection(self, schema: CollectionSchema) -> Result[CollectionSchema]:
        """
        Update a collection schema.
        
        Args:
            schema: Updated collection schema
            
        Returns:
            Result containing the updated collection schema or an error
        """
        return await self.collection_repository.update(schema)
    
    async def delete_collection(self, collection_id: CollectionId) -> Result[bool]:
        """
        Delete a collection.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        return await self.collection_repository.delete(collection_id)
    
    async def list_collections(self, store_id: StoreId) -> Result[List[CollectionSchema]]:
        """
        List collections in a store.
        
        Args:
            store_id: Store ID
            
        Returns:
            Result containing a list of collection schemas or an error
        """
        return await self.collection_repository.list(store_id)


class TransactionService(DomainService):
    """Service for managing transactions in the offline store."""
    
    def __init__(
        self,
        transaction_repository: TransactionRepositoryProtocol,
        document_repository: DocumentRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the transaction service.
        
        Args:
            transaction_repository: Transaction repository
            document_repository: Document repository
            logger: Optional logger
        """
        self.transaction_repository = transaction_repository
        self.document_repository = document_repository
        self.logger = logger or logging.getLogger("uno.offline.transaction")
    
    async def begin_transaction(self, store_id: StoreId) -> Result[Transaction]:
        """
        Begin a new transaction.
        
        Args:
            store_id: Store ID
            
        Returns:
            Result containing the created transaction or an error
        """
        try:
            # Create transaction
            transaction = Transaction(
                id=TransactionId(str(uuid.uuid4())),
                store_id=store_id
            )
            
            # Save transaction
            return await self.transaction_repository.create(transaction)
        except Exception as e:
            self.logger.error(f"Failed to begin transaction: {str(e)}")
            return Result.failure(f"Failed to begin transaction: {str(e)}")
    
    async def commit_transaction(self, transaction_id: TransactionId) -> Result[Transaction]:
        """
        Commit a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Result containing the committed transaction or an error
        """
        try:
            # Get transaction
            transaction_result = await self.transaction_repository.get(transaction_id)
            if transaction_result.is_failure():
                return transaction_result
            
            transaction = transaction_result.value
            
            # Check if already committed or rolled back
            if transaction.status != "pending":
                return Result.failure(f"Transaction is already {transaction.status}")
            
            # Execute operations
            for operation in transaction.operations:
                await self._execute_operation(operation)
            
            # Commit transaction
            transaction.commit()
            
            # Update transaction
            return await self.transaction_repository.update(transaction)
        except Exception as e:
            self.logger.error(f"Failed to commit transaction: {str(e)}")
            return Result.failure(f"Failed to commit transaction: {str(e)}")
    
    async def rollback_transaction(self, transaction_id: TransactionId) -> Result[Transaction]:
        """
        Rollback a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Result containing the rolled back transaction or an error
        """
        try:
            # Get transaction
            transaction_result = await self.transaction_repository.get(transaction_id)
            if transaction_result.is_failure():
                return transaction_result
            
            transaction = transaction_result.value
            
            # Check if already committed or rolled back
            if transaction.status != "pending":
                return Result.failure(f"Transaction is already {transaction.status}")
            
            # Rollback transaction
            transaction.rollback()
            
            # Update transaction
            return await self.transaction_repository.update(transaction)
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {str(e)}")
            return Result.failure(f"Failed to rollback transaction: {str(e)}")
    
    async def add_operation(
        self,
        transaction_id: TransactionId,
        operation_type: str,
        collection_id: CollectionId,
        document_id: Optional[DocumentId] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Result[Transaction]:
        """
        Add an operation to a transaction.
        
        Args:
            transaction_id: Transaction ID
            operation_type: Operation type
            collection_id: Collection ID
            document_id: Document ID (if applicable)
            data: Operation data (if applicable)
            
        Returns:
            Result containing the updated transaction or an error
        """
        try:
            # Get transaction
            transaction_result = await self.transaction_repository.get(transaction_id)
            if transaction_result.is_failure():
                return transaction_result
            
            transaction = transaction_result.value
            
            # Check if already committed or rolled back
            if transaction.status != "pending":
                return Result.failure(f"Transaction is already {transaction.status}")
            
            # Add operation
            transaction.add_operation(
                operation_type,
                collection_id,
                document_id,
                data
            )
            
            # Update transaction
            return await self.transaction_repository.update(transaction)
        except Exception as e:
            self.logger.error(f"Failed to add operation: {str(e)}")
            return Result.failure(f"Failed to add operation: {str(e)}")
    
    async def _execute_operation(self, operation: Dict[str, Any]) -> None:
        """
        Execute a transaction operation.
        
        Args:
            operation: Operation details
        """
        operation_type = operation["type"]
        collection_id = CollectionId(operation["collection_id"])
        document_id = DocumentId(operation["document_id"]) if operation["document_id"] else None
        data = operation["data"]
        
        if operation_type == "create":
            await self.document_repository.create(collection_id, data)
        elif operation_type == "update":
            await self.document_repository.update(collection_id, document_id, data)
        elif operation_type == "delete":
            await self.document_repository.delete(collection_id, document_id)


class SyncService(DomainService):
    """Service for synchronizing data with the server."""
    
    def __init__(
        self,
        sync_repository: SyncRepositoryProtocol,
        change_repository: ChangeRepositoryProtocol,
        conflict_repository: ConflictRepositoryProtocol,
        document_repository: DocumentRepositoryProtocol,
        network_state_repository: NetworkStateRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the sync service.
        
        Args:
            sync_repository: Sync repository
            change_repository: Change repository
            conflict_repository: Conflict repository
            document_repository: Document repository
            network_state_repository: Network state repository
            logger: Optional logger
        """
        self.sync_repository = sync_repository
        self.change_repository = change_repository
        self.conflict_repository = conflict_repository
        self.document_repository = document_repository
        self.network_state_repository = network_state_repository
        self.logger = logger or logging.getLogger("uno.offline.sync")
        
        # Remote adapter for synchronization with server
        self.remote_adapter = None
    
    def set_remote_adapter(self, adapter: Any) -> None:
        """
        Set the remote adapter for synchronization.
        
        Args:
            adapter: Remote adapter
        """
        self.remote_adapter = adapter
    
    async def can_sync(self) -> Result[bool]:
        """
        Check if synchronization is possible.
        
        Returns:
            Result containing a boolean indicating if sync is possible or an error
        """
        try:
            # Check if remote adapter is set
            if not self.remote_adapter:
                return Result.failure("Remote adapter is not set")
            
            # Check network state
            network_result = await self.network_state_repository.get_current_state()
            if network_result.is_failure():
                return Result.failure(f"Failed to get network state: {network_result.error}")
            
            network_state = network_result.value
            
            # Check if online
            return Result.success(network_state.is_online())
        except Exception as e:
            self.logger.error(f"Failed to check sync capability: {str(e)}")
            return Result.failure(f"Failed to check sync capability: {str(e)}")
    
    async def synchronize(
        self,
        store_id: StoreId,
        collections: List[CollectionId],
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> Result[SyncEvent]:
        """
        Synchronize data with the server.
        
        Args:
            store_id: Store ID
            collections: Collections to synchronize
            direction: Synchronization direction
            
        Returns:
            Result containing the sync event or an error
        """
        try:
            # Check if sync is possible
            can_sync_result = await self.can_sync()
            if can_sync_result.is_failure():
                return Result.failure(f"Cannot synchronize: {can_sync_result.error}")
            
            if not can_sync_result.value:
                return Result.failure("Cannot synchronize: offline")
            
            # Create sync event
            sync_event = SyncEvent(
                id=SyncId(str(uuid.uuid4())),
                store_id=store_id,
                direction=direction,
                collections=collections
            )
            
            # Start sync
            sync_event.start()
            await self.sync_repository.create(sync_event)
            
            changes_pushed = 0
            changes_pulled = 0
            
            try:
                # Push changes
                if direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                    push_result = await self._push_changes(sync_event, collections)
                    if push_result.is_failure():
                        sync_event.fail(push_result.error)
                        await self.sync_repository.update(sync_event)
                        return Result.failure(push_result.error)
                    
                    changes_pushed = push_result.value
                
                # Pull changes
                if direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                    pull_result = await self._pull_changes(sync_event, collections)
                    if pull_result.is_failure():
                        # If push succeeded but pull failed, mark as partial
                        if direction == SyncDirection.BIDIRECTIONAL and changes_pushed > 0:
                            sync_event.partial_complete(
                                changes_pushed=changes_pushed,
                                error=pull_result.error
                            )
                            await self.sync_repository.update(sync_event)
                            return Result.success(sync_event)
                        else:
                            sync_event.fail(pull_result.error)
                            await self.sync_repository.update(sync_event)
                            return Result.failure(pull_result.error)
                    
                    changes_pulled = pull_result.value
                
                # Complete sync
                sync_event.complete(changes_pushed=changes_pushed, changes_pulled=changes_pulled)
                await self.sync_repository.update(sync_event)
                
                return Result.success(sync_event)
            except Exception as e:
                # Handle unexpected errors
                error_message = f"Sync failed: {str(e)}"
                self.logger.error(error_message)
                
                sync_event.fail(error_message)
                await self.sync_repository.update(sync_event)
                
                return Result.failure(error_message)
        except Exception as e:
            self.logger.error(f"Failed to synchronize: {str(e)}")
            return Result.failure(f"Failed to synchronize: {str(e)}")
    
    async def _push_changes(
        self,
        sync_event: SyncEvent,
        collections: List[CollectionId]
    ) -> Result[int]:
        """
        Push local changes to the server.
        
        Args:
            sync_event: Sync event
            collections: Collections to push
            
        Returns:
            Result containing the number of changes pushed or an error
        """
        try:
            changes_pushed = 0
            
            # Get unsynchronized changes
            for collection_id in collections:
                changes_result = await self.change_repository.list_unsynchronized(collection_id)
                if changes_result.is_failure():
                    return Result.failure(f"Failed to get changes: {changes_result.error}")
                
                changes = changes_result.value
                
                for change in changes:
                    # Push change to server
                    push_result = await self.remote_adapter.push_change(change)
                    if push_result.is_failure():
                        return Result.failure(f"Failed to push change: {push_result.error}")
                    
                    # Check for conflicts
                    if "conflict" in push_result.value:
                        # Create conflict
                        conflict_data = push_result.value["conflict"]
                        conflict = Conflict(
                            id=ConflictId(str(uuid.uuid4())),
                            document_id=change.document_id,
                            collection_id=change.collection_id,
                            client_data=change.data,
                            server_data=conflict_data["server_data"],
                            client_version=change.version,
                            server_version=conflict_data["server_version"],
                            sync_id=sync_event.id
                        )
                        
                        await self.conflict_repository.create(conflict)
                        sync_event.add_conflict(conflict.id)
                    else:
                        # Mark change as synchronized
                        await self.change_repository.mark_synchronized(change.id)
                        changes_pushed += 1
            
            return Result.success(changes_pushed)
        except Exception as e:
            self.logger.error(f"Failed to push changes: {str(e)}")
            return Result.failure(f"Failed to push changes: {str(e)}")
    
    async def _pull_changes(
        self,
        sync_event: SyncEvent,
        collections: List[CollectionId]
    ) -> Result[int]:
        """
        Pull remote changes from the server.
        
        Args:
            sync_event: Sync event
            collections: Collections to pull
            
        Returns:
            Result containing the number of changes pulled or an error
        """
        try:
            changes_pulled = 0
            
            # Get last successful sync
            last_sync_result = await self.sync_repository.get_last_successful(sync_event.store_id)
            
            # Get changes from server
            for collection_id in collections:
                # Get last sync time for this collection
                last_sync_time = None
                if last_sync_result.is_success() and last_sync_result.value:
                    last_sync_time = last_sync_result.value.end_time
                
                # Pull changes from server
                pull_result = await self.remote_adapter.pull_changes(
                    collection_id,
                    last_sync_time
                )
                if pull_result.is_failure():
                    return Result.failure(f"Failed to pull changes: {pull_result.error}")
                
                changes = pull_result.value
                
                for change_data in changes:
                    # Process change
                    document_id = DocumentId(change_data["document_id"])
                    
                    if change_data["change_type"] == ChangeType.CREATE.value:
                        # Create document
                        await self.document_repository.create(
                            collection_id,
                            change_data["data"]
                        )
                    elif change_data["change_type"] == ChangeType.UPDATE.value:
                        # Update document
                        await self.document_repository.update(
                            collection_id,
                            document_id,
                            change_data["data"]
                        )
                    elif change_data["change_type"] == ChangeType.DELETE.value:
                        # Delete document
                        await self.document_repository.delete(
                            collection_id,
                            document_id
                        )
                    
                    changes_pulled += 1
            
            return Result.success(changes_pulled)
        except Exception as e:
            self.logger.error(f"Failed to pull changes: {str(e)}")
            return Result.failure(f"Failed to pull changes: {str(e)}")
    
    async def resolve_conflict(
        self,
        conflict_id: ConflictId,
        strategy: ConflictResolutionStrategy,
        resolved_data: Optional[Dict[str, Any]] = None
    ) -> Result[Conflict]:
        """
        Resolve a conflict.
        
        Args:
            conflict_id: Conflict ID
            strategy: Resolution strategy
            resolved_data: Resolved data (required for MERGE and MANUAL strategies)
            
        Returns:
            Result containing the resolved conflict or an error
        """
        try:
            # Get conflict
            conflict_result = await self.conflict_repository.get(conflict_id)
            if conflict_result.is_failure():
                return conflict_result
            
            conflict = conflict_result.value
            
            # Check if already resolved
            if conflict.resolved:
                return Result.failure("Conflict is already resolved")
            
            # Resolve conflict
            conflict.resolve(strategy, resolved_data)
            
            # Update document with resolved data
            await self.document_repository.update(
                conflict.collection_id,
                conflict.document_id,
                conflict.resolved_data
            )
            
            # Create change record for resolution
            change = Change(
                id=ChangeId(str(uuid.uuid4())),
                document_id=conflict.document_id,
                collection_id=conflict.collection_id,
                change_type=ChangeType.UPDATE,
                data=conflict.resolved_data,
                timestamp=datetime.now(UTC),
                version=max(conflict.client_version, conflict.server_version) + 1
            )
            
            await self.change_repository.create(change)
            
            # Update conflict
            return await self.conflict_repository.update(conflict)
        except Exception as e:
            self.logger.error(f"Failed to resolve conflict: {str(e)}")
            return Result.failure(f"Failed to resolve conflict: {str(e)}")
    
    async def list_unresolved_conflicts(
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
        return await self.conflict_repository.list_unresolved(sync_id)


class NetworkService(DomainService):
    """Service for managing network connectivity."""
    
    def __init__(
        self,
        network_state_repository: NetworkStateRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the network service.
        
        Args:
            network_state_repository: Network state repository
            logger: Optional logger
        """
        self.network_state_repository = network_state_repository
        self.logger = logger or logging.getLogger("uno.offline.network")
        self._check_task = None
    
    async def get_network_state(self) -> Result[NetworkState]:
        """
        Get the current network state.
        
        Returns:
            Result containing the current network state or an error
        """
        return await self.network_state_repository.get_current_state()
    
    async def update_network_status(
        self,
        status: NetworkStatus
    ) -> Result[NetworkState]:
        """
        Update the network status.
        
        Args:
            status: New network status
            
        Returns:
            Result containing the updated network state or an error
        """
        try:
            # Get current state
            state_result = await self.network_state_repository.get_current_state()
            if state_result.is_failure():
                # Create new state if doesn't exist
                state = NetworkState()
            else:
                state = state_result.value
            
            # Update status
            state.update_status(status)
            
            # Save state
            return await self.network_state_repository.update_state(state)
        except Exception as e:
            self.logger.error(f"Failed to update network status: {str(e)}")
            return Result.failure(f"Failed to update network status: {str(e)}")
    
    async def start_monitoring(
        self,
        check_interval: int = 30,
        check_fn: Optional[callable] = None
    ) -> Result[bool]:
        """
        Start monitoring network connectivity.
        
        Args:
            check_interval: Interval between checks in seconds
            check_fn: Custom function to check connectivity
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            # Stop existing monitoring
            if self._check_task and not self._check_task.done():
                self._check_task.cancel()
            
            # Set check function
            self._check_fn = check_fn or self._default_check_fn
            
            # Start monitoring task
            self._check_task = asyncio.create_task(
                self._monitor_network(check_interval)
            )
            
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {str(e)}")
            return Result.failure(f"Failed to start monitoring: {str(e)}")
    
    async def stop_monitoring(self) -> Result[bool]:
        """
        Stop monitoring network connectivity.
        
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            if self._check_task and not self._check_task.done():
                self._check_task.cancel()
                self._check_task = None
            
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {str(e)}")
            return Result.failure(f"Failed to stop monitoring: {str(e)}")
    
    async def _monitor_network(self, check_interval: int) -> None:
        """
        Monitor network connectivity.
        
        Args:
            check_interval: Interval between checks in seconds
        """
        try:
            while True:
                # Check network status
                is_online = await self._check_fn()
                status = NetworkStatus.ONLINE if is_online else NetworkStatus.OFFLINE
                
                # Update status
                await self.update_network_status(status)
                
                # Wait for next check
                await asyncio.sleep(check_interval)
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            self.logger.error(f"Network monitoring error: {str(e)}")
    
    async def _default_check_fn(self) -> bool:
        """
        Default function to check network connectivity.
        
        Returns:
            True if online, False if offline
        """
        # This is a placeholder. In a real implementation, this would
        # check actual network connectivity.
        return True


class OfflineService(DomainService):
    """Coordinating service for offline operations."""
    
    def __init__(
        self,
        document_service: DocumentService,
        collection_service: CollectionService,
        transaction_service: TransactionService,
        sync_service: SyncService,
        network_service: NetworkService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the offline service.
        
        Args:
            document_service: Document service
            collection_service: Collection service
            transaction_service: Transaction service
            sync_service: Sync service
            network_service: Network service
            logger: Optional logger
        """
        self.document_service = document_service
        self.collection_service = collection_service
        self.transaction_service = transaction_service
        self.sync_service = sync_service
        self.network_service = network_service
        self.logger = logger or logging.getLogger("uno.offline")