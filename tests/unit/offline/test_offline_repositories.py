import pytest
from datetime import datetime, timedelta, UTC
from unittest import mock
import json
import uuid

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
from uno.offline.domain_repositories import (
    DocumentRepository,
    CollectionRepository,
    TransactionRepository,
    ChangeRepository,
    SyncRepository,
    ConflictRepository,
    NetworkStateRepository
)


class MockDB:
    """Mock database session for testing repositories."""
    
    def __init__(self):
        self.queries = []
        self.params = []
        self.results = []
        self.result_index = 0
    
    async def query_one(self, query, params=None):
        """Execute a query and return one result."""
        self.queries.append(query)
        self.params.append(params)
        
        if self.result_index < len(self.results):
            result = self.results[self.result_index]
            self.result_index += 1
            return result
        return None
    
    async def query(self, query, params=None):
        """Execute a query and return all results."""
        self.queries.append(query)
        self.params.append(params)
        
        if self.result_index < len(self.results):
            result = self.results[self.result_index]
            self.result_index += 1
            return result
        return []
    
    def set_result(self, result):
        """Set a single result to be returned."""
        self.results = [result]
        self.result_index = 0
    
    def set_results(self, results):
        """Set multiple results to be returned in sequence."""
        self.results = results
        self.result_index = 0
    
    def get_last_query(self):
        """Get the last executed query."""
        if not self.queries:
            return None
        return self.queries[-1]
    
    def get_last_params(self):
        """Get the parameters of the last executed query."""
        if not self.params:
            return None
        return self.params[-1]
    
    def reset(self):
        """Reset the mock."""
        self.queries = []
        self.params = []
        self.results = []
        self.result_index = 0


class TestDocumentRepository:
    
    @pytest.fixture
    def db(self):
        return MockDB()
    
    @pytest.fixture
    def repository(self, db):
        repo = DocumentRepository()
        repo.db = db
        return repo
    
    @pytest.mark.asyncio
    async def test_create(self, repository, db):
        collection_id = CollectionId("coll-1")
        data = {"name": "Test Document", "tags": ["tag1", "tag2"]}
        
        # Set up the mock to return a successful result
        db.set_result({"id": "doc-1", "collection_id": "coll-1", "data": json.dumps(data)})
        
        result = await repository.create(collection_id, data)
        
        assert result.is_success()
        document = result.value
        assert document.id.value == "doc-1"
        assert document.collection_id == collection_id
        assert document.data == data
        
        # Verify the correct queries were executed
        assert len(db.queries) == 2
        assert "INSERT INTO offline_documents" in db.queries[0]
        assert "INSERT INTO offline_changes" in db.queries[1]
        
        # Verify parameters for document insert
        params = db.params[0]
        assert params["collection_id"] == collection_id.value
        assert params["deleted"] is False
        assert params["deleted_at"] is None
        
        # Verify parameters for change record
        change_params = db.params[1]
        assert change_params["change_type"] == ChangeType.CREATE.value
        assert change_params["synchronized"] is False
    
    @pytest.mark.asyncio
    async def test_create_error(self, repository, db):
        collection_id = CollectionId("coll-1")
        data = {"name": "Test Document"}
        
        # Mock an error during database insert
        async def mock_query_one(*args, **kwargs):
            raise Exception("Database error")
        
        db.query_one = mock_query_one
        
        result = await repository.create(collection_id, data)
        
        assert result.is_failure()
        assert "Failed to create document" in result.error
    
    @pytest.mark.asyncio
    async def test_get(self, repository, db):
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        data = {"name": "Test Document"}
        
        # Set up the mock to return a document
        db.set_result({
            "id": document_id.value,
            "collection_id": collection_id.value,
            "data": json.dumps(data),
            "version": 1,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted": False,
            "deleted_at": None,
            "metadata": json.dumps({})
        })
        
        result = await repository.get(collection_id, document_id)
        
        assert result.is_success()
        document = result.value
        assert document.id == document_id
        assert document.collection_id == collection_id
        assert document.data == data
        assert document.version == 1
        assert document.deleted is False
        
        # Verify the correct query was executed
        assert "WHERE id =" in db.get_last_query()
        assert "AND collection_id =" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["id"] == document_id.value
        assert params["collection_id"] == collection_id.value
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, repository, db):
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        
        # Set up the mock to return no results
        db.set_result(None)
        
        result = await repository.get(collection_id, document_id)
        
        assert result.is_failure()
        assert "Document not found" in result.error
    
    @pytest.mark.asyncio
    async def test_update(self, repository, db):
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        existing_data = {"name": "Original Name", "count": 1}
        update_data = {"name": "Updated Name", "status": "active"}
        
        # Set up the mock to return the existing document first
        db.set_results([
            # For the get query
            {
                "id": document_id.value,
                "collection_id": collection_id.value,
                "data": json.dumps(existing_data),
                "version": 1,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            },
            # For the update query
            {
                "id": document_id.value,
                "collection_id": collection_id.value,
                "data": json.dumps({**existing_data, **update_data}),
                "version": 2,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            }
        ])
        
        result = await repository.update(collection_id, document_id, update_data)
        
        assert result.is_success()
        document = result.value
        assert document.id == document_id
        assert document.collection_id == collection_id
        assert document.data["name"] == "Updated Name"
        assert document.data["count"] == 1  # Preserved from original
        assert document.data["status"] == "active"  # Added
        assert document.version == 2
        
        # Verify the correct queries were executed
        assert len(db.queries) >= 3
        assert "SELECT" in db.queries[0]  # Get existing document
        assert "UPDATE" in db.queries[1]  # Update document
        assert "INSERT INTO offline_changes" in db.queries[2]  # Create change record
        
        # Verify parameters for update
        params = db.params[1]
        assert params["id"] == document_id.value
        assert params["collection_id"] == collection_id.value
        assert json.loads(params["data"])["name"] == "Updated Name"
        assert params["version"] == 2
        
        # Verify parameters for change record
        change_params = db.params[2]
        assert change_params["change_type"] == ChangeType.UPDATE.value
        assert json.loads(change_params["data"])["name"] == "Updated Name"
        assert change_params["version"] == 2
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, db):
        collection_id = CollectionId("coll-1")
        document_id = DocumentId("doc-1")
        existing_data = {"name": "Test Document"}
        
        # Set up the mock to return the existing document first
        db.set_results([
            # For the get query
            {
                "id": document_id.value,
                "collection_id": collection_id.value,
                "data": json.dumps(existing_data),
                "version": 1,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            },
            # For the update query (soft delete)
            {
                "id": document_id.value,
                "collection_id": collection_id.value,
                "data": json.dumps(existing_data),
                "version": 2,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": True,
                "deleted_at": datetime.now(UTC),
                "metadata": json.dumps({})
            }
        ])
        
        result = await repository.delete(collection_id, document_id)
        
        assert result.is_success()
        assert result.value is True
        
        # Verify the correct queries were executed
        assert len(db.queries) >= 3
        assert "SELECT" in db.queries[0]  # Get existing document
        assert "UPDATE" in db.queries[1]  # Soft delete document
        assert "INSERT INTO offline_changes" in db.queries[2]  # Create change record
        
        # Verify parameters for update
        params = db.params[1]
        assert params["id"] == document_id.value
        assert params["deleted"] is True
        assert params["deleted_at"] is not None
        
        # Verify parameters for change record
        change_params = db.params[2]
        assert change_params["change_type"] == ChangeType.DELETE.value
        assert change_params["document_id"] == document_id.value
    
    @pytest.mark.asyncio
    async def test_query(self, repository, db):
        collection_id = CollectionId("coll-1")
        query = {"category": "A", "active": True}
        
        # Set up the mock to return matching documents
        db.set_result([
            {
                "id": "doc1",
                "collection_id": collection_id.value,
                "data": json.dumps({"name": "Doc 1", "category": "A", "active": True}),
                "version": 1,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            },
            {
                "id": "doc2",
                "collection_id": collection_id.value,
                "data": json.dumps({"name": "Doc 2", "category": "A", "active": True}),
                "version": 1,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            }
        ])
        
        result = await repository.query(collection_id, query)
        
        assert result.is_success()
        documents = result.value
        assert len(documents) == 2
        assert documents[0].data["name"] == "Doc 1"
        assert documents[1].data["name"] == "Doc 2"
        
        # Verify query parameters
        assert db.get_last_params()["collection_id"] == collection_id.value
        assert "json_extract" in db.get_last_query()  # SQL function to query JSON fields
        assert "category" in db.get_last_query()
        assert "active" in db.get_last_query()
    
    @pytest.mark.asyncio
    async def test_list(self, repository, db):
        collection_id = CollectionId("coll-1")
        
        # Set up the mock to return documents
        db.set_result([
            {
                "id": "doc1",
                "collection_id": collection_id.value,
                "data": json.dumps({"name": "Doc 1"}),
                "version": 1,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            },
            {
                "id": "doc2",
                "collection_id": collection_id.value,
                "data": json.dumps({"name": "Doc 2"}),
                "version": 1,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "deleted": False,
                "deleted_at": None,
                "metadata": json.dumps({})
            }
        ])
        
        result = await repository.list(collection_id, limit=10, offset=0)
        
        assert result.is_success()
        documents = result.value
        assert len(documents) == 2
        assert documents[0].data["name"] == "Doc 1"
        assert documents[1].data["name"] == "Doc 2"
        
        # Verify query parameters
        params = db.get_last_params()
        assert params["collection_id"] == collection_id.value
        assert params["limit"] == 10
        assert params["offset"] == 0
        assert "WHERE collection_id = :collection_id" in db.get_last_query()
        assert "AND deleted = FALSE" in db.get_last_query()
        assert "LIMIT :limit OFFSET :offset" in db.get_last_query()


class TestCollectionRepository:
    
    @pytest.fixture
    def db(self):
        return MockDB()
    
    @pytest.fixture
    def repository(self, db):
        repo = CollectionRepository()
        repo.db = db
        return repo
    
    @pytest.mark.asyncio
    async def test_create(self, repository, db):
        store_id = StoreId("store-1")
        collection_id = CollectionId("coll-1")
        
        schema = CollectionSchema(
            id=collection_id,
            name="test_collection",
            store_id=store_id,
            key_path="id",
            auto_increment=False,
            indexes={"name_index": {"key_path": "name", "unique": True}},
            relationships=[],
            validators=[],
            default_values={"active": True},
            max_items=1000,
            versioned=True,
            metadata={"created_by": "test"}
        )
        
        # Set up the mock to return a successful result
        db.set_result({
            "id": collection_id.value,
            "name": "test_collection",
            "store_id": store_id.value,
            "key_path": json.dumps("id"),
            "auto_increment": False,
            "indexes": json.dumps({"name_index": {"key_path": "name", "unique": True}}),
            "relationships": json.dumps([]),
            "validators": json.dumps([]),
            "default_values": json.dumps({"active": True}),
            "max_items": 1000,
            "versioned": True,
            "metadata": json.dumps({"created_by": "test"})
        })
        
        result = await repository.create(schema)
        
        assert result.is_success()
        created_schema = result.value
        assert created_schema.id == collection_id
        assert created_schema.name == "test_collection"
        assert created_schema.store_id == store_id
        assert created_schema.key_path == "id"
        assert created_schema.auto_increment is False
        assert "name_index" in created_schema.indexes
        assert created_schema.indexes["name_index"]["unique"] is True
        
        # Verify the correct query was executed
        assert "INSERT INTO offline_collections" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["id"] == collection_id.value
        assert params["name"] == "test_collection"
        assert params["store_id"] == store_id.value
        assert json.loads(params["indexes"])["name_index"]["key_path"] == "name"
    
    @pytest.mark.asyncio
    async def test_get(self, repository, db):
        collection_id = CollectionId("coll-1")
        store_id = StoreId("store-1")
        
        # Set up the mock to return a collection
        db.set_result({
            "id": collection_id.value,
            "name": "test_collection",
            "store_id": store_id.value,
            "key_path": json.dumps("id"),
            "auto_increment": False,
            "indexes": json.dumps({}),
            "relationships": json.dumps([]),
            "validators": json.dumps([]),
            "default_values": json.dumps({}),
            "max_items": None,
            "versioned": False,
            "metadata": json.dumps({})
        })
        
        result = await repository.get(collection_id)
        
        assert result.is_success()
        schema = result.value
        assert schema.id == collection_id
        assert schema.name == "test_collection"
        assert schema.store_id == store_id
        
        # Verify the correct query was executed
        assert "SELECT * FROM offline_collections WHERE id = :id" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["id"] == collection_id.value
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, repository, db):
        collection_id = CollectionId("nonexistent")
        
        # Set up the mock to return no results
        db.set_result(None)
        
        result = await repository.get(collection_id)
        
        assert result.is_failure()
        assert "Collection not found" in result.error
    
    @pytest.mark.asyncio
    async def test_get_by_name(self, repository, db):
        store_id = StoreId("store-1")
        collection_id = CollectionId("coll-1")
        
        # Set up the mock to return a collection
        db.set_result({
            "id": collection_id.value,
            "name": "test_collection",
            "store_id": store_id.value,
            "key_path": json.dumps("id"),
            "auto_increment": False,
            "indexes": json.dumps({}),
            "relationships": json.dumps([]),
            "validators": json.dumps([]),
            "default_values": json.dumps({}),
            "max_items": None,
            "versioned": False,
            "metadata": json.dumps({})
        })
        
        result = await repository.get_by_name(store_id, "test_collection")
        
        assert result.is_success()
        schema = result.value
        assert schema.id == collection_id
        assert schema.name == "test_collection"
        assert schema.store_id == store_id
        
        # Verify the correct query was executed
        assert "WHERE store_id = :store_id AND name = :name" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["store_id"] == store_id.value
        assert params["name"] == "test_collection"
    
    @pytest.mark.asyncio
    async def test_update(self, repository, db):
        store_id = StoreId("store-1")
        collection_id = CollectionId("coll-1")
        
        schema = CollectionSchema(
            id=collection_id,
            name="test_collection",
            store_id=store_id,
            key_path="id",
            auto_increment=False,
            versioned=True
        )
        
        # Add an index
        schema.add_index("name_index", "name", unique=True)
        
        # Set up the mock to return a successful result
        db.set_result({
            "id": collection_id.value,
            "name": "test_collection",
            "store_id": store_id.value,
            "key_path": json.dumps("id"),
            "auto_increment": False,
            "indexes": json.dumps({"name_index": {"key_path": "name", "unique": True}}),
            "relationships": json.dumps([]),
            "validators": json.dumps([]),
            "default_values": json.dumps({}),
            "max_items": None,
            "versioned": True,
            "metadata": json.dumps({})
        })
        
        result = await repository.update(schema)
        
        assert result.is_success()
        updated_schema = result.value
        assert updated_schema.id == collection_id
        assert updated_schema.versioned is True
        assert "name_index" in updated_schema.indexes
        
        # Verify the correct query was executed
        assert "UPDATE offline_collections SET" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["id"] == collection_id.value
        assert params["versioned"] is True
        assert json.loads(params["indexes"])["name_index"]["unique"] is True
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, db):
        collection_id = CollectionId("coll-1")
        
        # Set up the mock to return a successful result
        db.set_result({"affected_rows": 1})
        
        result = await repository.delete(collection_id)
        
        assert result.is_success()
        assert result.value is True
        
        # Verify the correct query was executed
        assert "DELETE FROM offline_collections WHERE id = :id" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["id"] == collection_id.value
    
    @pytest.mark.asyncio
    async def test_list(self, repository, db):
        store_id = StoreId("store-1")
        
        # Set up the mock to return collections
        db.set_result([
            {
                "id": "coll1",
                "name": "collection1",
                "store_id": store_id.value,
                "key_path": json.dumps("id"),
                "auto_increment": False,
                "indexes": json.dumps({}),
                "relationships": json.dumps([]),
                "validators": json.dumps([]),
                "default_values": json.dumps({}),
                "max_items": None,
                "versioned": False,
                "metadata": json.dumps({})
            },
            {
                "id": "coll2",
                "name": "collection2",
                "store_id": store_id.value,
                "key_path": json.dumps("id"),
                "auto_increment": False,
                "indexes": json.dumps({}),
                "relationships": json.dumps([]),
                "validators": json.dumps([]),
                "default_values": json.dumps({}),
                "max_items": None,
                "versioned": False,
                "metadata": json.dumps({})
            }
        ])
        
        result = await repository.list(store_id)
        
        assert result.is_success()
        collections = result.value
        assert len(collections) == 2
        assert collections[0].name == "collection1"
        assert collections[1].name == "collection2"
        assert all(c.store_id == store_id for c in collections)
        
        # Verify the correct query was executed
        assert "WHERE store_id = :store_id" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["store_id"] == store_id.value


# Similar tests can be written for the remaining repositories (TransactionRepository,
# ChangeRepository, SyncRepository, ConflictRepository, NetworkStateRepository)
# following the same pattern. These tests would follow the same structure as the
# ones for DocumentRepository and CollectionRepository.

# For brevity, we'll implement a simplified test for each of the remaining repositories
# focusing on their key functionality.

class TestChangeRepository:
    
    @pytest.fixture
    def db(self):
        return MockDB()
    
    @pytest.fixture
    def repository(self, db):
        repo = ChangeRepository()
        repo.db = db
        return repo
    
    @pytest.mark.asyncio
    async def test_create_and_list_unsynchronized(self, repository, db):
        document_id = DocumentId("doc-1")
        collection_id = CollectionId("coll-1")
        change_id = ChangeId("change-1")
        
        change = Change(
            id=change_id,
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.UPDATE,
            data={"name": "Updated Name"},
            timestamp=datetime.now(UTC),
            version=2,
            synchronized=False
        )
        
        # Set up the mock for create
        db.set_result({
            "id": change_id.value,
            "document_id": document_id.value,
            "collection_id": collection_id.value,
            "change_type": change.change_type.value,
            "data": json.dumps(change.data),
            "timestamp": change.timestamp,
            "version": change.version,
            "synchronized": change.synchronized,
            "metadata": json.dumps({})
        })
        
        # Create the change
        create_result = await repository.create(change)
        
        assert create_result.is_success()
        assert create_result.value.id == change_id
        
        # Reset the mock for list_unsynchronized
        db.reset()
        db.set_result([{
            "id": change_id.value,
            "document_id": document_id.value,
            "collection_id": collection_id.value,
            "change_type": change.change_type.value,
            "data": json.dumps(change.data),
            "timestamp": change.timestamp,
            "version": change.version,
            "synchronized": False,
            "metadata": json.dumps({})
        }])
        
        # List unsynchronized changes
        list_result = await repository.list_unsynchronized(collection_id)
        
        assert list_result.is_success()
        changes = list_result.value
        assert len(changes) == 1
        assert changes[0].id == change_id
        assert changes[0].synchronized is False
        
        # Verify the correct query was executed
        assert "WHERE synchronized = FALSE" in db.get_last_query()
        assert "AND collection_id = :collection_id" in db.get_last_query()


class TestSyncRepository:
    
    @pytest.fixture
    def db(self):
        return MockDB()
    
    @pytest.fixture
    def repository(self, db):
        repo = SyncRepository()
        repo.db = db
        return repo
    
    @pytest.mark.asyncio
    async def test_create_and_get_last_successful(self, repository, db):
        store_id = StoreId("store-1")
        sync_id = SyncId("sync-1")
        collection_ids = [CollectionId("coll-1"), CollectionId("coll-2")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.BIDIRECTIONAL,
            collections=collection_ids,
            status=SyncStatus.COMPLETED,
            start_time=datetime.now(UTC) - timedelta(minutes=30),
            end_time=datetime.now(UTC) - timedelta(minutes=25),
            changes_pushed=5,
            changes_pulled=3
        )
        
        # Set up the mock for create
        db.set_result({
            "id": sync_id.value,
            "store_id": store_id.value,
            "direction": sync_event.direction.value,
            "collections": json.dumps([c.value for c in collection_ids]),
            "status": sync_event.status.value,
            "start_time": sync_event.start_time,
            "end_time": sync_event.end_time,
            "changes_pushed": sync_event.changes_pushed,
            "changes_pulled": sync_event.changes_pulled,
            "conflicts": json.dumps([]),
            "error": None,
            "metadata": json.dumps({})
        })
        
        # Create the sync event
        create_result = await repository.create(sync_event)
        
        assert create_result.is_success()
        assert create_result.value.id == sync_id
        
        # Reset the mock for get_last_successful
        db.reset()
        db.set_result({
            "id": sync_id.value,
            "store_id": store_id.value,
            "direction": sync_event.direction.value,
            "collections": json.dumps([c.value for c in collection_ids]),
            "status": SyncStatus.COMPLETED.value,
            "start_time": sync_event.start_time,
            "end_time": sync_event.end_time,
            "changes_pushed": sync_event.changes_pushed,
            "changes_pulled": sync_event.changes_pulled,
            "conflicts": json.dumps([]),
            "error": None,
            "metadata": json.dumps({})
        })
        
        # Get last successful sync
        last_result = await repository.get_last_successful(store_id)
        
        assert last_result.is_success()
        last_sync = last_result.value
        assert last_sync.id == sync_id
        assert last_sync.status == SyncStatus.COMPLETED
        assert last_sync.changes_pushed == 5
        assert last_sync.changes_pulled == 3
        
        # Verify the correct query was executed
        assert "WHERE store_id = :store_id AND status = :status" in db.get_last_query()
        assert "ORDER BY end_time DESC LIMIT 1" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["store_id"] == store_id.value
        assert params["status"] == SyncStatus.COMPLETED.value


class TestConflictRepository:
    
    @pytest.fixture
    def db(self):
        return MockDB()
    
    @pytest.fixture
    def repository(self, db):
        repo = ConflictRepository()
        repo.db = db
        return repo
    
    @pytest.mark.asyncio
    async def test_create_and_list_unresolved(self, repository, db):
        document_id = DocumentId("doc-1")
        collection_id = CollectionId("coll-1")
        conflict_id = ConflictId("conflict-1")
        sync_id = SyncId("sync-1")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            resolved=False,
            sync_id=sync_id
        )
        
        # Set up the mock for create
        db.set_result({
            "id": conflict_id.value,
            "document_id": document_id.value,
            "collection_id": collection_id.value,
            "client_data": json.dumps(conflict.client_data),
            "server_data": json.dumps(conflict.server_data),
            "client_version": conflict.client_version,
            "server_version": conflict.server_version,
            "resolved": conflict.resolved,
            "resolution_strategy": None,
            "resolved_data": None,
            "sync_id": sync_id.value,
            "created_at": datetime.now(UTC),
            "resolved_at": None,
            "metadata": json.dumps({})
        })
        
        # Create the conflict
        create_result = await repository.create(conflict)
        
        assert create_result.is_success()
        assert create_result.value.id == conflict_id
        
        # Reset the mock for list_unresolved
        db.reset()
        db.set_result([{
            "id": conflict_id.value,
            "document_id": document_id.value,
            "collection_id": collection_id.value,
            "client_data": json.dumps(conflict.client_data),
            "server_data": json.dumps(conflict.server_data),
            "client_version": conflict.client_version,
            "server_version": conflict.server_version,
            "resolved": False,
            "resolution_strategy": None,
            "resolved_data": None,
            "sync_id": sync_id.value,
            "created_at": datetime.now(UTC),
            "resolved_at": None,
            "metadata": json.dumps({})
        }])
        
        # List unresolved conflicts
        list_result = await repository.list_unresolved(sync_id)
        
        assert list_result.is_success()
        conflicts = list_result.value
        assert len(conflicts) == 1
        assert conflicts[0].id == conflict_id
        assert conflicts[0].resolved is False
        
        # Verify the correct query was executed
        assert "WHERE resolved = FALSE" in db.get_last_query()
        assert "AND sync_id = :sync_id" in db.get_last_query()
        
        # Verify parameters
        params = db.get_last_params()
        assert params["sync_id"] == sync_id.value


class TestNetworkStateRepository:
    
    @pytest.fixture
    def db(self):
        return MockDB()
    
    @pytest.fixture
    def repository(self, db):
        repo = NetworkStateRepository()
        repo.db = db
        return repo
    
    @pytest.mark.asyncio
    async def test_get_and_update_state(self, repository, db):
        # Set up the mock for get_current_state
        db.set_result({
            "id": "network-1",
            "status": NetworkStatus.ONLINE.value,
            "last_online": datetime.now(UTC) - timedelta(minutes=10),
            "last_offline": datetime.now(UTC) - timedelta(hours=1),
            "check_interval": 30,
            "last_check": datetime.now(UTC) - timedelta(minutes=5),
            "metadata": json.dumps({})
        })
        
        # Get current state
        get_result = await repository.get_current_state()
        
        assert get_result.is_success()
        state = get_result.value
        assert state.status == NetworkStatus.ONLINE
        assert state.check_interval == 30
        
        # Reset the mock for update_state
        db.reset()
        db.set_result({
            "id": "network-1",
            "status": NetworkStatus.OFFLINE.value,
            "last_online": state.last_online,
            "last_offline": datetime.now(UTC),
            "check_interval": 30,
            "last_check": datetime.now(UTC),
            "metadata": json.dumps({})
        })
        
        # Update to offline
        state.update_status(NetworkStatus.OFFLINE)
        update_result = await repository.update_state(state)
        
        assert update_result.is_success()
        updated_state = update_result.value
        assert updated_state.status == NetworkStatus.OFFLINE
        assert updated_state.last_offline is not None
        
        # Verify the correct query was executed
        assert "UPDATE offline_network_state SET" in db.get_last_query()