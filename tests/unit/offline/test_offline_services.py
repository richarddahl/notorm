import pytest
from datetime import datetime, timedelta, UTC
from unittest import mock
import uuid
import logging

from uno.core.result import Result
from uno.offline.entities import (
    StoreId,
    CollectionId,
    DocumentId,
    TransactionId,
    ChangeId,
    SyncId,
    ConflictId,
    Document,
    Transaction,
    Change,
    SyncEvent,
    Conflict,
    NetworkState,
    ChangeType,
    SyncStatus,
    SyncDirection,
    ConflictResolutionStrategy,
    NetworkStatus,
    CollectionSchema
)
from uno.offline.domain_services import (
    DocumentService,
    CollectionService,
    TransactionService,
    SyncService,
    NetworkService,
    OfflineService
)


# Mock repositories
class MockDocumentRepository:
    
    def __init__(self):
        self.documents = {}
        self.collections = {}
    
    async def create(self, collection_id, data):
        doc_id = data.get("id", str(uuid.uuid4()))
        document_id = DocumentId(doc_id)
        document = Document(
            id=document_id,
            collection_id=collection_id,
            data=data,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        self.documents[f"{collection_id.value}:{doc_id}"] = document
        return Result.success(document)
    
    async def get(self, collection_id, document_id):
        key = f"{collection_id.value}:{document_id.value}"
        if key not in self.documents:
            return Result.failure(f"Document not found: {document_id.value}")
        return Result.success(self.documents[key])
    
    async def update(self, collection_id, document_id, data):
        key = f"{collection_id.value}:{document_id.value}"
        if key not in self.documents:
            return Result.failure(f"Document not found: {document_id.value}")
        
        document = self.documents[key]
        document.update(data)
        return Result.success(document)
    
    async def delete(self, collection_id, document_id):
        key = f"{collection_id.value}:{document_id.value}"
        if key not in self.documents:
            return Result.failure(f"Document not found: {document_id.value}")
        
        document = self.documents[key]
        document.delete()
        return Result.success(True)
    
    async def query(self, collection_id, query):
        # Simple query implementation for testing
        results = []
        for key, doc in self.documents.items():
            if doc.collection_id == collection_id:
                match = True
                for field, value in query.items():
                    if field not in doc.data or doc.data[field] != value:
                        match = False
                        break
                if match:
                    results.append(doc)
        return Result.success(results)
    
    async def list(self, collection_id, limit=100, offset=0):
        results = []
        for key, doc in self.documents.items():
            if doc.collection_id == collection_id and not doc.deleted:
                results.append(doc)
        
        # Apply pagination
        return Result.success(results[offset:offset+limit])


class MockChangeRepository:
    
    def __init__(self):
        self.changes = {}
    
    async def create(self, change):
        self.changes[change.id.value] = change
        return Result.success(change)
    
    async def get(self, change_id):
        if change_id.value not in self.changes:
            return Result.failure(f"Change not found: {change_id.value}")
        return Result.success(self.changes[change_id.value])
    
    async def update(self, change):
        if change.id.value not in self.changes:
            return Result.failure(f"Change not found: {change.id.value}")
        self.changes[change.id.value] = change
        return Result.success(change)
    
    async def list_unsynchronized(self, collection_id=None):
        results = []
        for change in self.changes.values():
            if not change.synchronized:
                if collection_id is None or change.collection_id == collection_id:
                    results.append(change)
        return Result.success(results)
    
    async def mark_synchronized(self, change_id):
        if change_id.value not in self.changes:
            return Result.failure(f"Change not found: {change_id.value}")
        
        change = self.changes[change_id.value]
        change.mark_synchronized()
        return Result.success(change)


class MockCollectionRepository:
    
    def __init__(self):
        self.collections = {}
    
    async def create(self, schema):
        self.collections[schema.id.value] = schema
        return Result.success(schema)
    
    async def get(self, collection_id):
        if collection_id.value not in self.collections:
            return Result.failure(f"Collection not found: {collection_id.value}")
        return Result.success(self.collections[collection_id.value])
    
    async def get_by_name(self, store_id, name):
        for collection in self.collections.values():
            if collection.store_id == store_id and collection.name == name:
                return Result.success(collection)
        return Result.failure(f"Collection not found: {name}")
    
    async def update(self, schema):
        if schema.id.value not in self.collections:
            return Result.failure(f"Collection not found: {schema.id.value}")
        self.collections[schema.id.value] = schema
        return Result.success(schema)
    
    async def delete(self, collection_id):
        if collection_id.value not in self.collections:
            return Result.failure(f"Collection not found: {collection_id.value}")
        del self.collections[collection_id.value]
        return Result.success(True)
    
    async def list(self, store_id):
        results = []
        for collection in self.collections.values():
            if collection.store_id == store_id:
                results.append(collection)
        return Result.success(results)


class MockTransactionRepository:
    
    def __init__(self):
        self.transactions = {}
    
    async def create(self, transaction):
        self.transactions[transaction.id.value] = transaction
        return Result.success(transaction)
    
    async def get(self, transaction_id):
        if transaction_id.value not in self.transactions:
            return Result.failure(f"Transaction not found: {transaction_id.value}")
        return Result.success(self.transactions[transaction_id.value])
    
    async def update(self, transaction):
        if transaction.id.value not in self.transactions:
            return Result.failure(f"Transaction not found: {transaction.id.value}")
        self.transactions[transaction.id.value] = transaction
        return Result.success(transaction)
    
    async def list_active(self, store_id):
        results = []
        for transaction in self.transactions.values():
            if transaction.store_id == store_id and transaction.status == "pending":
                results.append(transaction)
        return Result.success(results)


class MockSyncRepository:
    
    def __init__(self):
        self.sync_events = {}
    
    async def create(self, sync_event):
        self.sync_events[sync_event.id.value] = sync_event
        return Result.success(sync_event)
    
    async def get(self, sync_id):
        if sync_id.value not in self.sync_events:
            return Result.failure(f"Sync event not found: {sync_id.value}")
        return Result.success(self.sync_events[sync_id.value])
    
    async def update(self, sync_event):
        if sync_event.id.value not in self.sync_events:
            return Result.failure(f"Sync event not found: {sync_event.id.value}")
        self.sync_events[sync_event.id.value] = sync_event
        return Result.success(sync_event)
    
    async def list_recent(self, store_id, limit=10):
        results = []
        for event in self.sync_events.values():
            if event.store_id == store_id:
                results.append(event)
        
        # Sort by start_time if it exists
        results.sort(key=lambda e: e.start_time if e.start_time else datetime.min.replace(tzinfo=UTC), reverse=True)
        
        return Result.success(results[:limit])
    
    async def get_last_successful(self, store_id):
        successful_events = []
        for event in self.sync_events.values():
            if event.store_id == store_id and event.status == SyncStatus.COMPLETED:
                successful_events.append(event)
        
        if not successful_events:
            return Result.success(None)
        
        # Get the most recent successful sync
        successful_events.sort(key=lambda e: e.end_time if e.end_time else datetime.min.replace(tzinfo=UTC), reverse=True)
        return Result.success(successful_events[0])


class MockConflictRepository:
    
    def __init__(self):
        self.conflicts = {}
    
    async def create(self, conflict):
        self.conflicts[conflict.id.value] = conflict
        return Result.success(conflict)
    
    async def get(self, conflict_id):
        if conflict_id.value not in self.conflicts:
            return Result.failure(f"Conflict not found: {conflict_id.value}")
        return Result.success(self.conflicts[conflict_id.value])
    
    async def update(self, conflict):
        if conflict.id.value not in self.conflicts:
            return Result.failure(f"Conflict not found: {conflict.id.value}")
        self.conflicts[conflict.id.value] = conflict
        return Result.success(conflict)
    
    async def list_unresolved(self, sync_id=None):
        results = []
        for conflict in self.conflicts.values():
            if not conflict.resolved:
                if sync_id is None or conflict.sync_id == sync_id:
                    results.append(conflict)
        return Result.success(results)
    
    async def resolve(self, conflict_id, resolved_data):
        if conflict_id.value not in self.conflicts:
            return Result.failure(f"Conflict not found: {conflict_id.value}")
        
        conflict = self.conflicts[conflict_id.value]
        conflict.resolve(ConflictResolutionStrategy.MANUAL, resolved_data)
        return Result.success(conflict)


class MockNetworkStateRepository:
    
    def __init__(self):
        self.current_state = NetworkState(status=NetworkStatus.ONLINE)
    
    async def get_current_state(self):
        return Result.success(self.current_state)
    
    async def update_state(self, state):
        self.current_state = state
        return Result.success(state)


class MockRemoteAdapter:
    
    def __init__(self):
        self.pushed_changes = []
        self.pulled_changes = []
        self.conflicts = {}
    
    async def push_change(self, change):
        self.pushed_changes.append(change)
        
        # If we want to simulate a conflict
        if change.id.value in self.conflicts:
            conflict_data = self.conflicts[change.id.value]
            return Result.success({"conflict": conflict_data})
        
        return Result.success({"success": True})
    
    async def pull_changes(self, collection_id, last_sync_time):
        changes = []
        for change in self.pulled_changes:
            if change["collection_id"] == collection_id.value:
                if last_sync_time is None or change["timestamp"] > last_sync_time:
                    changes.append(change)
        return Result.success(changes)


class TestDocumentService:
    
    @pytest.fixture
    def document_repository(self):
        return MockDocumentRepository()
    
    @pytest.fixture
    def change_repository(self):
        return MockChangeRepository()
    
    @pytest.fixture
    def document_service(self, document_repository, change_repository):
        return DocumentService(document_repository, change_repository)
    
    @pytest.mark.asyncio
    async def test_create_document(self, document_service):
        collection_id = CollectionId("test-collection")
        data = {"name": "Test Document", "active": True}
        
        result = await document_service.create_document(collection_id, data)
        
        assert result.is_success()
        document = result.value
        assert document.collection_id == collection_id
        assert document.data == data
        assert document.version == 1
        assert document.created_at is not None
        assert document.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_document(self, document_service, document_repository):
        # Create a document first
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("test-document")
        data = {"id": document_id.value, "name": "Test Document"}
        
        await document_repository.create(collection_id, data)
        
        # Get the document
        result = await document_service.get_document(collection_id, document_id)
        
        assert result.is_success()
        document = result.value
        assert document.id == document_id
        assert document.collection_id == collection_id
        assert document.data["name"] == "Test Document"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, document_service):
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("nonexistent")
        
        result = await document_service.get_document(collection_id, document_id)
        
        assert result.is_failure()
        assert "Document not found" in result.error
    
    @pytest.mark.asyncio
    async def test_update_document(self, document_service, document_repository, change_repository):
        # Create a document first
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("test-document")
        data = {"id": document_id.value, "name": "Original Name", "count": 1}
        
        await document_repository.create(collection_id, data)
        
        # Update the document
        update_data = {"name": "Updated Name", "status": "active"}
        result = await document_service.update_document(collection_id, document_id, update_data)
        
        assert result.is_success()
        document = result.value
        assert document.data["name"] == "Updated Name"
        assert document.data["count"] == 1  # Preserved
        assert document.data["status"] == "active"  # Added
        assert document.version == 2
        
        # Verify a change record was created
        changes = (await change_repository.list_unsynchronized()).value
        assert len(changes) == 1
        change = changes[0]
        assert change.document_id == document_id
        assert change.collection_id == collection_id
        assert change.change_type == ChangeType.UPDATE
        assert change.data == update_data
        assert change.version == 2
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, document_service):
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("nonexistent")
        data = {"name": "Updated Name"}
        
        result = await document_service.update_document(collection_id, document_id, data)
        
        assert result.is_failure()
        assert "Document not found" in result.error
    
    @pytest.mark.asyncio
    async def test_delete_document(self, document_service, document_repository, change_repository):
        # Create a document first
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("test-document")
        data = {"id": document_id.value, "name": "Test Document"}
        
        await document_repository.create(collection_id, data)
        
        # Delete the document
        result = await document_service.delete_document(collection_id, document_id)
        
        assert result.is_success()
        assert result.value is True
        
        # Verify the document was marked as deleted
        doc_result = await document_repository.get(collection_id, document_id)
        document = doc_result.value
        assert document.deleted is True
        assert document.deleted_at is not None
        
        # Verify a change record was created
        changes = (await change_repository.list_unsynchronized()).value
        assert len(changes) == 1
        change = changes[0]
        assert change.document_id == document_id
        assert change.collection_id == collection_id
        assert change.change_type == ChangeType.DELETE
        assert change.version == 2
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, document_service):
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("nonexistent")
        
        result = await document_service.delete_document(collection_id, document_id)
        
        assert result.is_failure()
        assert "Document not found" in result.error
    
    @pytest.mark.asyncio
    async def test_query_documents(self, document_service, document_repository):
        # Create some documents
        collection_id = CollectionId("test-collection")
        await document_repository.create(collection_id, {"id": "doc1", "category": "A", "active": True})
        await document_repository.create(collection_id, {"id": "doc2", "category": "B", "active": True})
        await document_repository.create(collection_id, {"id": "doc3", "category": "A", "active": False})
        
        # Query documents
        query = {"category": "A"}
        result = await document_service.query_documents(collection_id, query)
        
        assert result.is_success()
        documents = result.value
        assert len(documents) == 2
        assert all(doc.data["category"] == "A" for doc in documents)
        
        # Query with multiple criteria
        query = {"category": "A", "active": True}
        result = await document_service.query_documents(collection_id, query)
        
        assert result.is_success()
        documents = result.value
        assert len(documents) == 1
        assert documents[0].data["id"] == "doc1"
    
    @pytest.mark.asyncio
    async def test_list_documents(self, document_service, document_repository):
        # Create some documents
        collection_id = CollectionId("test-collection")
        await document_repository.create(collection_id, {"id": "doc1", "name": "Document 1"})
        await document_repository.create(collection_id, {"id": "doc2", "name": "Document 2"})
        await document_repository.create(collection_id, {"id": "doc3", "name": "Document 3"})
        
        # List documents
        result = await document_service.list_documents(collection_id)
        
        assert result.is_success()
        documents = result.value
        assert len(documents) == 3
        
        # Test pagination
        result = await document_service.list_documents(collection_id, limit=2, offset=1)
        
        assert result.is_success()
        documents = result.value
        assert len(documents) == 2
        assert documents[0].data["id"] == "doc2"
        assert documents[1].data["id"] == "doc3"


class TestCollectionService:
    
    @pytest.fixture
    def collection_repository(self):
        return MockCollectionRepository()
    
    @pytest.fixture
    def collection_service(self, collection_repository):
        return CollectionService(collection_repository)
    
    @pytest.mark.asyncio
    async def test_create_collection(self, collection_service):
        store_id = StoreId("test-store")
        
        result = await collection_service.create_collection(
            store_id=store_id,
            name="test_collection",
            key_path="id",
            auto_increment=False,
            versioned=True
        )
        
        assert result.is_success()
        schema = result.value
        assert schema.store_id == store_id
        assert schema.name == "test_collection"
        assert schema.key_path == "id"
        assert schema.auto_increment is False
        assert schema.versioned is True
    
    @pytest.mark.asyncio
    async def test_create_duplicate_collection(self, collection_service, collection_repository):
        store_id = StoreId("test-store")
        
        # Create a collection
        schema = CollectionSchema(
            id=CollectionId("coll-1"),
            name="test_collection",
            store_id=store_id,
            key_path="id"
        )
        await collection_repository.create(schema)
        
        # Try to create another with the same name
        result = await collection_service.create_collection(
            store_id=store_id,
            name="test_collection",
            key_path="id"
        )
        
        assert result.is_failure()
        assert "Collection 'test_collection' already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_get_collection(self, collection_service, collection_repository):
        store_id = StoreId("test-store")
        collection_id = CollectionId("coll-1")
        
        # Create a collection
        schema = CollectionSchema(
            id=collection_id,
            name="test_collection",
            store_id=store_id,
            key_path="id"
        )
        await collection_repository.create(schema)
        
        # Get the collection
        result = await collection_service.get_collection(collection_id)
        
        assert result.is_success()
        retrieved_schema = result.value
        assert retrieved_schema.id == collection_id
        assert retrieved_schema.name == "test_collection"
        assert retrieved_schema.store_id == store_id
    
    @pytest.mark.asyncio
    async def test_get_collection_by_name(self, collection_service, collection_repository):
        store_id = StoreId("test-store")
        
        # Create a collection
        schema = CollectionSchema(
            id=CollectionId("coll-1"),
            name="test_collection",
            store_id=store_id,
            key_path="id"
        )
        await collection_repository.create(schema)
        
        # Get by name
        result = await collection_service.get_collection_by_name(store_id, "test_collection")
        
        assert result.is_success()
        retrieved_schema = result.value
        assert retrieved_schema.name == "test_collection"
        assert retrieved_schema.store_id == store_id
    
    @pytest.mark.asyncio
    async def test_update_collection(self, collection_service, collection_repository):
        store_id = StoreId("test-store")
        collection_id = CollectionId("coll-1")
        
        # Create a collection
        schema = CollectionSchema(
            id=collection_id,
            name="test_collection",
            store_id=store_id,
            key_path="id",
            versioned=False
        )
        await collection_repository.create(schema)
        
        # Update the collection
        schema.versioned = True
        schema.add_index("name_index", "name", unique=True)
        
        result = await collection_service.update_collection(schema)
        
        assert result.is_success()
        updated_schema = result.value
        assert updated_schema.versioned is True
        assert "name_index" in updated_schema.indexes
    
    @pytest.mark.asyncio
    async def test_delete_collection(self, collection_service, collection_repository):
        store_id = StoreId("test-store")
        collection_id = CollectionId("coll-1")
        
        # Create a collection
        schema = CollectionSchema(
            id=collection_id,
            name="test_collection",
            store_id=store_id,
            key_path="id"
        )
        await collection_repository.create(schema)
        
        # Delete the collection
        result = await collection_service.delete_collection(collection_id)
        
        assert result.is_success()
        assert result.value is True
        
        # Verify it's gone
        get_result = await collection_service.get_collection(collection_id)
        assert get_result.is_failure()
    
    @pytest.mark.asyncio
    async def test_list_collections(self, collection_service, collection_repository):
        store_id = StoreId("test-store")
        other_store_id = StoreId("other-store")
        
        # Create collections in different stores
        schema1 = CollectionSchema(id=CollectionId("coll-1"), name="collection1", store_id=store_id, key_path="id")
        schema2 = CollectionSchema(id=CollectionId("coll-2"), name="collection2", store_id=store_id, key_path="id")
        schema3 = CollectionSchema(id=CollectionId("coll-3"), name="collection3", store_id=other_store_id, key_path="id")
        
        await collection_repository.create(schema1)
        await collection_repository.create(schema2)
        await collection_repository.create(schema3)
        
        # List collections for test-store
        result = await collection_service.list_collections(store_id)
        
        assert result.is_success()
        collections = result.value
        assert len(collections) == 2
        assert all(c.store_id == store_id for c in collections)
        
        # List collections for other-store
        result = await collection_service.list_collections(other_store_id)
        
        assert result.is_success()
        collections = result.value
        assert len(collections) == 1
        assert collections[0].name == "collection3"


class TestTransactionService:
    
    @pytest.fixture
    def transaction_repository(self):
        return MockTransactionRepository()
    
    @pytest.fixture
    def document_repository(self):
        return MockDocumentRepository()
    
    @pytest.fixture
    def transaction_service(self, transaction_repository, document_repository):
        return TransactionService(transaction_repository, document_repository)
    
    @pytest.mark.asyncio
    async def test_begin_transaction(self, transaction_service):
        store_id = StoreId("test-store")
        
        result = await transaction_service.begin_transaction(store_id)
        
        assert result.is_success()
        transaction = result.value
        assert transaction.store_id == store_id
        assert transaction.status == "pending"
        assert transaction.operations == []
        assert transaction.start_time is not None
        assert transaction.commit_time is None
        assert transaction.rollback_time is None
    
    @pytest.mark.asyncio
    async def test_add_operation(self, transaction_service, transaction_repository):
        store_id = StoreId("test-store")
        transaction_id = TransactionId("trans-1")
        
        # Create a transaction
        transaction = Transaction(id=transaction_id, store_id=store_id)
        await transaction_repository.create(transaction)
        
        # Add an operation
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        data = {"name": "Test Document"}
        
        result = await transaction_service.add_operation(
            transaction_id=transaction_id,
            operation_type="create",
            collection_id=collection_id,
            document_id=document_id,
            data=data
        )
        
        assert result.is_success()
        updated_transaction = result.value
        assert len(updated_transaction.operations) == 1
        operation = updated_transaction.operations[0]
        assert operation["type"] == "create"
        assert operation["collection_id"] == collection_id.value
        assert operation["document_id"] == document_id.value
        assert operation["data"] == data
    
    @pytest.mark.asyncio
    async def test_commit_transaction(self, transaction_service, transaction_repository, document_repository):
        store_id = StoreId("test-store")
        transaction_id = TransactionId("trans-1")
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        
        # Create a transaction with operations
        transaction = Transaction(id=transaction_id, store_id=store_id)
        await transaction_repository.create(transaction)
        
        # Add operations
        await transaction_service.add_operation(
            transaction_id=transaction_id,
            operation_type="create",
            collection_id=collection_id,
            document_id=document_id,
            data={"id": document_id.value, "name": "Test Document"}
        )
        
        # Commit the transaction
        result = await transaction_service.commit_transaction(transaction_id)
        
        assert result.is_success()
        committed_transaction = result.value
        assert committed_transaction.status == "committed"
        assert committed_transaction.commit_time is not None
        
        # Verify the document was created
        doc_result = await document_repository.get(collection_id, document_id)
        assert doc_result.is_success()
        document = doc_result.value
        assert document.id == document_id
        assert document.data["name"] == "Test Document"
    
    @pytest.mark.asyncio
    async def test_rollback_transaction(self, transaction_service, transaction_repository):
        store_id = StoreId("test-store")
        transaction_id = TransactionId("trans-1")
        
        # Create a transaction
        transaction = Transaction(id=transaction_id, store_id=store_id)
        await transaction_repository.create(transaction)
        
        # Add some operations
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        await transaction_service.add_operation(
            transaction_id=transaction_id,
            operation_type="create",
            collection_id=collection_id,
            document_id=document_id,
            data={"name": "Test Document"}
        )
        
        # Rollback the transaction
        result = await transaction_service.rollback_transaction(transaction_id)
        
        assert result.is_success()
        rolled_back_transaction = result.value
        assert rolled_back_transaction.status == "rolled_back"
        assert rolled_back_transaction.rollback_time is not None
        assert rolled_back_transaction.commit_time is None


class TestSyncService:
    
    @pytest.fixture
    def sync_repository(self):
        return MockSyncRepository()
    
    @pytest.fixture
    def change_repository(self):
        return MockChangeRepository()
    
    @pytest.fixture
    def conflict_repository(self):
        return MockConflictRepository()
    
    @pytest.fixture
    def document_repository(self):
        return MockDocumentRepository()
    
    @pytest.fixture
    def network_state_repository(self):
        return MockNetworkStateRepository()
    
    @pytest.fixture
    def remote_adapter(self):
        return MockRemoteAdapter()
    
    @pytest.fixture
    def sync_service(self, sync_repository, change_repository, conflict_repository, document_repository, network_state_repository, remote_adapter):
        service = SyncService(
            sync_repository=sync_repository,
            change_repository=change_repository,
            conflict_repository=conflict_repository,
            document_repository=document_repository,
            network_state_repository=network_state_repository
        )
        service.set_remote_adapter(remote_adapter)
        return service
    
    @pytest.mark.asyncio
    async def test_can_sync_online(self, sync_service, network_state_repository):
        # Make sure we're online
        network_state = NetworkState(status=NetworkStatus.ONLINE)
        await network_state_repository.update_state(network_state)
        
        result = await sync_service.can_sync()
        
        assert result.is_success()
        assert result.value is True
    
    @pytest.mark.asyncio
    async def test_can_sync_offline(self, sync_service, network_state_repository):
        # Set to offline
        network_state = NetworkState(status=NetworkStatus.OFFLINE)
        await network_state_repository.update_state(network_state)
        
        result = await sync_service.can_sync()
        
        assert result.is_success()
        assert result.value is False
    
    @pytest.mark.asyncio
    async def test_can_sync_no_adapter(self, sync_service):
        # Remove remote adapter
        sync_service.remote_adapter = None
        
        result = await sync_service.can_sync()
        
        assert result.is_failure()
        assert "Remote adapter is not set" in result.error
    
    @pytest.mark.asyncio
    async def test_synchronize_push(self, sync_service, change_repository, document_repository, remote_adapter):
        store_id = StoreId("test-store")
        collection_id = CollectionId("test-collection")
        
        # Create some unsynchronized changes
        document_id = DocumentId("doc1")
        await document_repository.create(collection_id, {"id": document_id.value, "name": "Test Document"})
        
        change = Change(
            id=ChangeId("change1"),
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.CREATE,
            data={"name": "Test Document"},
            timestamp=datetime.now(UTC),
            version=1,
            synchronized=False
        )
        await change_repository.create(change)
        
        # Synchronize
        result = await sync_service.synchronize(
            store_id=store_id,
            collections=[collection_id],
            direction=SyncDirection.PUSH
        )
        
        assert result.is_success()
        sync_event = result.value
        
        assert sync_event.status == SyncStatus.COMPLETED
        assert sync_event.changes_pushed == 1
        assert sync_event.changes_pulled == 0
        
        # Verify change was marked as synchronized
        updated_change = (await change_repository.get(ChangeId("change1"))).value
        assert updated_change.synchronized is True
        
        # Verify the change was pushed to remote
        assert len(remote_adapter.pushed_changes) == 1
        assert remote_adapter.pushed_changes[0].id == ChangeId("change1")
    
    @pytest.mark.asyncio
    async def test_synchronize_pull(self, sync_service, document_repository, remote_adapter):
        store_id = StoreId("test-store")
        collection_id = CollectionId("test-collection")
        
        # Set up remote changes to pull
        remote_adapter.pulled_changes = [
            {
                "document_id": "doc1",
                "collection_id": collection_id.value,
                "change_type": "create",
                "data": {"id": "doc1", "name": "Remote Document"},
                "timestamp": datetime.now(UTC).isoformat()
            }
        ]
        
        # Synchronize
        result = await sync_service.synchronize(
            store_id=store_id,
            collections=[collection_id],
            direction=SyncDirection.PULL
        )
        
        assert result.is_success()
        sync_event = result.value
        
        assert sync_event.status == SyncStatus.COMPLETED
        assert sync_event.changes_pushed == 0
        assert sync_event.changes_pulled == 1
        
        # Verify document was created locally
        doc_result = await document_repository.get(collection_id, DocumentId("doc1"))
        assert doc_result.is_success()
        document = doc_result.value
        assert document.data["name"] == "Remote Document"
    
    @pytest.mark.asyncio
    async def test_synchronize_bidirectional(self, sync_service, change_repository, document_repository, remote_adapter):
        store_id = StoreId("test-store")
        collection_id = CollectionId("test-collection")
        
        # Create a local change to push
        document_id = DocumentId("local-doc")
        await document_repository.create(collection_id, {"id": document_id.value, "name": "Local Document"})
        
        change = Change(
            id=ChangeId("local-change"),
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.CREATE,
            data={"name": "Local Document"},
            timestamp=datetime.now(UTC),
            version=1,
            synchronized=False
        )
        await change_repository.create(change)
        
        # Set up remote changes to pull
        remote_adapter.pulled_changes = [
            {
                "document_id": "remote-doc",
                "collection_id": collection_id.value,
                "change_type": "create",
                "data": {"id": "remote-doc", "name": "Remote Document"},
                "timestamp": datetime.now(UTC).isoformat()
            }
        ]
        
        # Synchronize
        result = await sync_service.synchronize(
            store_id=store_id,
            collections=[collection_id],
            direction=SyncDirection.BIDIRECTIONAL
        )
        
        assert result.is_success()
        sync_event = result.value
        
        assert sync_event.status == SyncStatus.COMPLETED
        assert sync_event.changes_pushed == 1
        assert sync_event.changes_pulled == 1
        
        # Verify local document was pushed
        assert len(remote_adapter.pushed_changes) == 1
        assert remote_adapter.pushed_changes[0].document_id == document_id
        
        # Verify remote document was pulled
        doc_result = await document_repository.get(collection_id, DocumentId("remote-doc"))
        assert doc_result.is_success()
        document = doc_result.value
        assert document.data["name"] == "Remote Document"
    
    @pytest.mark.asyncio
    async def test_synchronize_with_conflict(self, sync_service, change_repository, conflict_repository, remote_adapter):
        store_id = StoreId("test-store")
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("doc1")
        
        # Create a local change that will conflict
        change = Change(
            id=ChangeId("conflicting-change"),
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.UPDATE,
            data={"name": "Local Name"},
            timestamp=datetime.now(UTC),
            version=2,
            synchronized=False
        )
        await change_repository.create(change)
        
        # Set up a conflict on the server side
        remote_adapter.conflicts["conflicting-change"] = {
            "server_data": {"name": "Server Name"},
            "server_version": 3
        }
        
        # Synchronize
        result = await sync_service.synchronize(
            store_id=store_id,
            collections=[collection_id],
            direction=SyncDirection.PUSH
        )
        
        assert result.is_success()
        sync_event = result.value
        
        assert sync_event.status == SyncStatus.COMPLETED
        assert sync_event.changes_pushed == 0  # No changes pushed due to conflict
        assert len(sync_event.conflicts) == 1
        
        # Verify conflict was created
        conflicts_result = await conflict_repository.list_unresolved()
        assert conflicts_result.is_success()
        conflicts = conflicts_result.value
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert conflict.document_id == document_id
        assert conflict.collection_id == collection_id
        assert conflict.client_data == {"name": "Local Name"}
        assert conflict.server_data == {"name": "Server Name"}
        assert conflict.client_version == 2
        assert conflict.server_version == 3
        assert conflict.resolved is False
    
    @pytest.mark.asyncio
    async def test_resolve_conflict(self, sync_service, conflict_repository, document_repository, change_repository):
        store_id = StoreId("test-store")
        collection_id = CollectionId("test-collection")
        document_id = DocumentId("doc1")
        sync_id = SyncId("sync1")
        
        # Create a document
        await document_repository.create(collection_id, {"id": document_id.value, "name": "Original Name"})
        
        # Create a conflict
        conflict = Conflict(
            id=ConflictId("conflict1"),
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        await conflict_repository.create(conflict)
        
        # Resolve the conflict
        result = await sync_service.resolve_conflict(
            conflict_id=ConflictId("conflict1"),
            strategy=ConflictResolutionStrategy.MANUAL,
            resolved_data={"name": "Resolved Name"}
        )
        
        assert result.is_success()
        resolved_conflict = result.value
        
        assert resolved_conflict.resolved is True
        assert resolved_conflict.resolution_strategy == ConflictResolutionStrategy.MANUAL
        assert resolved_conflict.resolved_data == {"name": "Resolved Name"}
        
        # Verify document was updated
        doc_result = await document_repository.get(collection_id, document_id)
        assert doc_result.is_success()
        document = doc_result.value
        assert document.data["name"] == "Resolved Name"
        
        # Verify a change record was created
        changes_result = await change_repository.list_unsynchronized()
        assert changes_result.is_success()
        changes = changes_result.value
        assert len(changes) > 0
        latest_change = changes[-1]
        assert latest_change.document_id == document_id
        assert latest_change.collection_id == collection_id
        assert latest_change.change_type == ChangeType.UPDATE
        assert latest_change.data == {"name": "Resolved Name"}
        assert latest_change.version == 4  # max(client, server) + 1
    
    @pytest.mark.asyncio
    async def test_list_unresolved_conflicts(self, sync_service, conflict_repository):
        sync_id1 = SyncId("sync1")
        sync_id2 = SyncId("sync2")
        
        # Create some conflicts
        conflict1 = Conflict(
            id=ConflictId("conflict1"),
            document_id=DocumentId("doc1"),
            collection_id=CollectionId("coll1"),
            client_data={"name": "Client 1"},
            server_data={"name": "Server 1"},
            client_version=1,
            server_version=2,
            sync_id=sync_id1
        )
        
        conflict2 = Conflict(
            id=ConflictId("conflict2"),
            document_id=DocumentId("doc2"),
            collection_id=CollectionId("coll1"),
            client_data={"name": "Client 2"},
            server_data={"name": "Server 2"},
            client_version=1,
            server_version=2,
            sync_id=sync_id2
        )
        
        # Resolve one of them
        conflict2.resolve(ConflictResolutionStrategy.CLIENT_WINS)
        
        await conflict_repository.create(conflict1)
        await conflict_repository.create(conflict2)
        
        # List all unresolved conflicts
        result = await sync_service.list_unresolved_conflicts()
        
        assert result.is_success()
        conflicts = result.value
        assert len(conflicts) == 1
        assert conflicts[0].id == ConflictId("conflict1")
        
        # List unresolved conflicts for a specific sync
        result = await sync_service.list_unresolved_conflicts(sync_id1)
        
        assert result.is_success()
        conflicts = result.value
        assert len(conflicts) == 1
        assert conflicts[0].id == ConflictId("conflict1")
        
        # List unresolved conflicts for another sync
        result = await sync_service.list_unresolved_conflicts(sync_id2)
        
        assert result.is_success()
        conflicts = result.value
        assert len(conflicts) == 0


class TestNetworkService:
    
    @pytest.fixture
    def network_state_repository(self):
        return MockNetworkStateRepository()
    
    @pytest.fixture
    def network_service(self, network_state_repository):
        return NetworkService(network_state_repository)
    
    @pytest.mark.asyncio
    async def test_get_network_state(self, network_service, network_state_repository):
        # Set up an initial state
        initial_state = NetworkState(
            status=NetworkStatus.ONLINE,
            last_online=datetime(2023, 1, 1, tzinfo=UTC)
        )
        await network_state_repository.update_state(initial_state)
        
        # Get network state
        result = await network_service.get_network_state()
        
        assert result.is_success()
        state = result.value
        assert state.status == NetworkStatus.ONLINE
        assert state.last_online == datetime(2023, 1, 1, tzinfo=UTC)
    
    @pytest.mark.asyncio
    async def test_update_network_status(self, network_service):
        # Update to offline
        result = await network_service.update_network_status(NetworkStatus.OFFLINE)
        
        assert result.is_success()
        state = result.value
        assert state.status == NetworkStatus.OFFLINE
        assert state.last_offline is not None
        
        # Update back to online
        result = await network_service.update_network_status(NetworkStatus.ONLINE)
        
        assert result.is_success()
        state = result.value
        assert state.status == NetworkStatus.ONLINE
        assert state.last_online is not None
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, network_service):
        # Start monitoring
        start_result = await network_service.start_monitoring(check_interval=1)
        
        assert start_result.is_success()
        assert start_result.value is True
        assert network_service._check_task is not None
        
        # Stop monitoring
        stop_result = await network_service.stop_monitoring()
        
        assert stop_result.is_success()
        assert stop_result.value is True
        assert network_service._check_task is None


class TestOfflineService:
    
    @pytest.fixture
    def document_service(self):
        return mock.Mock()
    
    @pytest.fixture
    def collection_service(self):
        return mock.Mock()
    
    @pytest.fixture
    def transaction_service(self):
        return mock.Mock()
    
    @pytest.fixture
    def sync_service(self):
        return mock.Mock()
    
    @pytest.fixture
    def network_service(self):
        return mock.Mock()
    
    @pytest.fixture
    def offline_service(self, document_service, collection_service, transaction_service, sync_service, network_service):
        return OfflineService(
            document_service=document_service,
            collection_service=collection_service,
            transaction_service=transaction_service,
            sync_service=sync_service,
            network_service=network_service
        )
    
    def test_initialization(self, offline_service, document_service, collection_service, transaction_service, sync_service, network_service):
        assert offline_service.document_service == document_service
        assert offline_service.collection_service == collection_service
        assert offline_service.transaction_service == transaction_service
        assert offline_service.sync_service == sync_service
        assert offline_service.network_service == network_service