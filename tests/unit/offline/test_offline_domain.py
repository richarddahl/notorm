import pytest
from datetime import datetime, timedelta, UTC
from unittest import mock
import uuid

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
    RelationshipType,
    ChangeType,
    SyncStatus,
    SyncDirection,
    ConflictResolutionStrategy,
    NetworkStatus
)


class TestValueObjects:
    
    def test_store_id(self):
        store_id = StoreId("store123")
        assert store_id.value == "store123"
    
    def test_collection_id(self):
        collection_id = CollectionId("coll123")
        assert collection_id.value == "coll123"
    
    def test_document_id(self):
        document_id = DocumentId("doc123")
        assert document_id.value == "doc123"
    
    def test_transaction_id(self):
        transaction_id = TransactionId("trans123")
        assert transaction_id.value == "trans123"
    
    def test_change_id(self):
        change_id = ChangeId("change123")
        assert change_id.value == "change123"
    
    def test_sync_id(self):
        sync_id = SyncId("sync123")
        assert sync_id.value == "sync123"
    
    def test_conflict_id(self):
        conflict_id = ConflictId("conflict123")
        assert conflict_id.value == "conflict123"


class TestEnums:
    
    def test_storage_type(self):
        assert StorageType.MEMORY.value == "memory"
        assert StorageType.LOCAL_STORAGE.value == "local_storage"
        assert StorageType.INDEXED_DB.value == "indexed_db"
        assert StorageType.SQLITE.value == "sqlite"
        assert StorageType.CUSTOM.value == "custom"
    
    def test_relationship_type(self):
        assert RelationshipType.ONE_TO_ONE.value == "one_to_one"
        assert RelationshipType.ONE_TO_MANY.value == "one_to_many"
        assert RelationshipType.MANY_TO_ONE.value == "many_to_one"
        assert RelationshipType.MANY_TO_MANY.value == "many_to_many"
    
    def test_change_type(self):
        assert ChangeType.CREATE.value == "create"
        assert ChangeType.UPDATE.value == "update"
        assert ChangeType.DELETE.value == "delete"
    
    def test_sync_status(self):
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.IN_PROGRESS.value == "in_progress"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"
        assert SyncStatus.PARTIAL.value == "partial"
    
    def test_sync_direction(self):
        assert SyncDirection.PUSH.value == "push"
        assert SyncDirection.PULL.value == "pull"
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"
    
    def test_conflict_resolution_strategy(self):
        assert ConflictResolutionStrategy.CLIENT_WINS.value == "client_wins"
        assert ConflictResolutionStrategy.SERVER_WINS.value == "server_wins"
        assert ConflictResolutionStrategy.LATEST_WINS.value == "latest_wins"
        assert ConflictResolutionStrategy.MANUAL.value == "manual"
        assert ConflictResolutionStrategy.MERGE.value == "merge"
    
    def test_network_status(self):
        assert NetworkStatus.ONLINE.value == "online"
        assert NetworkStatus.OFFLINE.value == "offline"
        assert NetworkStatus.LIMITED.value == "limited"


class TestStorageOptions:
    
    def test_create_storage_options(self):
        store_id = StoreId("store123")
        options = StorageOptions(
            id=store_id,
            name="Test Store",
            storage_type=StorageType.MEMORY,
            version="1.2",
            auto_compaction=True,
            compaction_interval=1800,
            max_size=10_000_000,
            encryption_enabled=True,
            encryption_key="secret_key",
            encrypt_field_names=True,
            compress=True,
            serialize_dates=True,
            collection_defaults={"versioned": True},
            metadata={"created_by": "test"}
        )
        
        assert options.id == store_id
        assert options.name == "Test Store"
        assert options.storage_type == StorageType.MEMORY
        assert options.version == "1.2"
        assert options.auto_compaction is True
        assert options.compaction_interval == 1800
        assert options.max_size == 10_000_000
        assert options.encryption_enabled is True
        assert options.encryption_key == "secret_key"
        assert options.encrypt_field_names is True
        assert options.compress is True
        assert options.serialize_dates is True
        assert options.collection_defaults == {"versioned": True}
        assert options.metadata == {"created_by": "test"}
    
    def test_storage_options_defaults(self):
        store_id = StoreId("store123")
        options = StorageOptions(id=store_id, name="Test Store")
        
        assert options.id == store_id
        assert options.name == "Test Store"
        assert options.storage_type == StorageType.MEMORY
        assert options.version == "1.0"
        assert options.auto_compaction is True
        assert options.compaction_interval == 3600
        assert options.max_size is None
        assert options.encryption_enabled is False
        assert options.encryption_key is None
        assert options.encrypt_field_names is False
        assert options.compress is False
        assert options.serialize_dates is True
        assert options.collection_defaults == {}
        assert options.metadata == {}


class TestCollectionSchema:
    
    def test_create_collection_schema(self):
        collection_id = CollectionId("coll123")
        store_id = StoreId("store123")
        schema = CollectionSchema(
            id=collection_id,
            name="Test Collection",
            store_id=store_id,
            key_path="id",
            auto_increment=True,
            indexes={},
            relationships=[],
            validators=[],
            default_values={"active": True},
            max_items=1000,
            versioned=True,
            metadata={"created_by": "test"}
        )
        
        assert schema.id == collection_id
        assert schema.name == "Test Collection"
        assert schema.store_id == store_id
        assert schema.key_path == "id"
        assert schema.auto_increment is True
        assert schema.indexes == {}
        assert schema.relationships == []
        assert schema.validators == []
        assert schema.default_values == {"active": True}
        assert schema.max_items == 1000
        assert schema.versioned is True
        assert schema.metadata == {"created_by": "test"}
    
    def test_add_index(self):
        collection_id = CollectionId("coll123")
        store_id = StoreId("store123")
        schema = CollectionSchema(
            id=collection_id,
            name="Test Collection",
            store_id=store_id,
            key_path="id"
        )
        
        # Add index
        schema.add_index("name_index", "name", unique=True)
        
        assert "name_index" in schema.indexes
        assert schema.indexes["name_index"]["key_path"] == "name"
        assert schema.indexes["name_index"]["unique"] is True
        
        # Add another index
        schema.add_index("multi_index", ["category", "date"])
        
        assert "multi_index" in schema.indexes
        assert schema.indexes["multi_index"]["key_path"] == ["category", "date"]
        assert schema.indexes["multi_index"]["unique"] is False
    
    def test_add_relationship(self):
        collection_id = CollectionId("coll123")
        store_id = StoreId("store123")
        schema = CollectionSchema(
            id=collection_id,
            name="Test Collection",
            store_id=store_id,
            key_path="id"
        )
        
        # Add relationship
        schema.add_relationship(
            name="author",
            collection="authors",
            relationship_type=RelationshipType.MANY_TO_ONE,
            foreign_key="author_id",
            local_key="id"
        )
        
        assert len(schema.relationships) == 1
        relationship = schema.relationships[0]
        assert relationship["name"] == "author"
        assert relationship["collection"] == "authors"
        assert relationship["type"] == RelationshipType.MANY_TO_ONE
        assert relationship["foreign_key"] == "author_id"
        assert relationship["local_key"] == "id"
    
    def test_add_validator(self):
        collection_id = CollectionId("coll123")
        store_id = StoreId("store123")
        schema = CollectionSchema(
            id=collection_id,
            name="Test Collection",
            store_id=store_id,
            key_path="id"
        )
        
        # Add validator
        schema.add_validator(
            name="required_fields",
            validator_fn="doc => doc.name && doc.email",
            error_message="Name and email are required"
        )
        
        assert len(schema.validators) == 1
        validator = schema.validators[0]
        assert validator["name"] == "required_fields"
        assert validator["function"] == "doc => doc.name && doc.email"
        assert validator["error_message"] == "Name and email are required"


class TestDocument:
    
    def test_create_document(self):
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        data = {"name": "Test Document", "active": True, "tags": ["test", "document"]}
        
        document = Document(
            id=document_id,
            collection_id=collection_id,
            data=data,
            version=2,
            created_at=datetime(2023, 1, 1, tzinfo=UTC),
            updated_at=datetime(2023, 1, 2, tzinfo=UTC),
            deleted=False,
            deleted_at=None,
            metadata={"created_by": "test"}
        )
        
        assert document.id == document_id
        assert document.collection_id == collection_id
        assert document.data == data
        assert document.version == 2
        assert document.created_at == datetime(2023, 1, 1, tzinfo=UTC)
        assert document.updated_at == datetime(2023, 1, 2, tzinfo=UTC)
        assert document.deleted is False
        assert document.deleted_at is None
        assert document.metadata == {"created_by": "test"}
    
    def test_update_document(self):
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        data = {"name": "Original Name", "count": 1}
        
        document = Document(
            id=document_id,
            collection_id=collection_id,
            data=data,
            version=1
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Update the document
            document.update({"name": "Updated Name", "status": "active"})
            
            assert document.data == {
                "name": "Updated Name",
                "count": 1,
                "status": "active"
            }
            assert document.version == 2
            assert document.updated_at == fixed_time
    
    def test_patch_document(self):
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        data = {
            "name": "Original Name",
            "nested": {
                "field1": "value1"
            }
        }
        
        document = Document(
            id=document_id,
            collection_id=collection_id,
            data=data,
            version=1
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Patch a top-level field
            document.patch("name", "Patched Name")
            
            assert document.data["name"] == "Patched Name"
            assert document.version == 2
            assert document.updated_at == fixed_time
            
            # Patch a nested field
            document.patch("nested.field1", "updated value1")
            
            assert document.data["nested"]["field1"] == "updated value1"
            assert document.version == 3
            
            # Patch a deeply nested field that doesn't exist yet
            document.patch("nested.deep.new", "new value")
            
            assert document.data["nested"]["deep"]["new"] == "new value"
            assert document.version == 4
    
    def test_delete_document(self):
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        data = {"name": "Test Document"}
        
        document = Document(
            id=document_id,
            collection_id=collection_id,
            data=data,
            version=1
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Delete the document
            document.delete()
            
            assert document.deleted is True
            assert document.deleted_at == fixed_time
            assert document.updated_at == fixed_time
            assert document.version == 2


class TestTransaction:
    
    def test_create_transaction(self):
        transaction_id = TransactionId("trans123")
        store_id = StoreId("store123")
        start_time = datetime(2023, 1, 1, tzinfo=UTC)
        
        transaction = Transaction(
            id=transaction_id,
            store_id=store_id,
            operations=[],
            start_time=start_time,
            commit_time=None,
            rollback_time=None,
            status="pending",
            metadata={"created_by": "test"}
        )
        
        assert transaction.id == transaction_id
        assert transaction.store_id == store_id
        assert transaction.operations == []
        assert transaction.start_time == start_time
        assert transaction.commit_time is None
        assert transaction.rollback_time is None
        assert transaction.status == "pending"
        assert transaction.metadata == {"created_by": "test"}
    
    def test_add_operation(self):
        transaction_id = TransactionId("trans123")
        store_id = StoreId("store123")
        
        transaction = Transaction(
            id=transaction_id,
            store_id=store_id
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            mock_datetime.isoformat = datetime.isoformat
            
            # Add create operation
            collection_id = CollectionId("coll123")
            document_id = DocumentId("doc123")
            data = {"name": "Test Document"}
            
            transaction.add_operation(
                operation_type="create",
                collection_id=collection_id,
                document_id=document_id,
                data=data
            )
            
            assert len(transaction.operations) == 1
            operation = transaction.operations[0]
            assert operation["type"] == "create"
            assert operation["collection_id"] == collection_id.value
            assert operation["document_id"] == document_id.value
            assert operation["data"] == data
            assert operation["timestamp"] == fixed_time.isoformat()
            
            # Add update operation
            transaction.add_operation(
                operation_type="update",
                collection_id=collection_id,
                document_id=document_id,
                data={"name": "Updated Name"}
            )
            
            assert len(transaction.operations) == 2
            
            # Add delete operation
            transaction.add_operation(
                operation_type="delete",
                collection_id=collection_id,
                document_id=document_id
            )
            
            assert len(transaction.operations) == 3
            delete_op = transaction.operations[2]
            assert delete_op["type"] == "delete"
            assert delete_op["data"] is None
    
    def test_commit_transaction(self):
        transaction_id = TransactionId("trans123")
        store_id = StoreId("store123")
        
        transaction = Transaction(
            id=transaction_id,
            store_id=store_id,
            status="pending"
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Commit the transaction
            transaction.commit()
            
            assert transaction.status == "committed"
            assert transaction.commit_time == fixed_time
            assert transaction.rollback_time is None
    
    def test_rollback_transaction(self):
        transaction_id = TransactionId("trans123")
        store_id = StoreId("store123")
        
        transaction = Transaction(
            id=transaction_id,
            store_id=store_id,
            status="pending"
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Rollback the transaction
            transaction.rollback()
            
            assert transaction.status == "rolled_back"
            assert transaction.rollback_time == fixed_time
            assert transaction.commit_time is None


class TestChange:
    
    def test_create_change(self):
        change_id = ChangeId("change123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        timestamp = datetime(2023, 1, 1, tzinfo=UTC)
        transaction_id = TransactionId("trans123")
        
        change = Change(
            id=change_id,
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.UPDATE,
            data={"name": "Updated Name"},
            timestamp=timestamp,
            transaction_id=transaction_id,
            version=2,
            synchronized=False,
            metadata={"source": "client"}
        )
        
        assert change.id == change_id
        assert change.document_id == document_id
        assert change.collection_id == collection_id
        assert change.change_type == ChangeType.UPDATE
        assert change.data == {"name": "Updated Name"}
        assert change.timestamp == timestamp
        assert change.transaction_id == transaction_id
        assert change.version == 2
        assert change.synchronized is False
        assert change.metadata == {"source": "client"}
    
    def test_mark_synchronized(self):
        change_id = ChangeId("change123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        
        change = Change(
            id=change_id,
            document_id=document_id,
            collection_id=collection_id,
            change_type=ChangeType.UPDATE,
            data={"name": "Updated Name"},
            synchronized=False
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            mock_datetime.isoformat = datetime.isoformat
            
            # Mark as synchronized
            change.mark_synchronized()
            
            assert change.synchronized is True
            assert change.metadata["synchronized_at"] == fixed_time.isoformat()


class TestSyncEvent:
    
    def test_create_sync_event(self):
        sync_id = SyncId("sync123")
        store_id = StoreId("store123")
        collections = [CollectionId("coll1"), CollectionId("coll2")]
        start_time = datetime(2023, 1, 1, tzinfo=UTC)
        end_time = datetime(2023, 1, 1, 1, tzinfo=UTC)
        conflicts = [ConflictId("conflict1"), ConflictId("conflict2")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.BIDIRECTIONAL,
            collections=collections,
            status=SyncStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            changes_pushed=10,
            changes_pulled=5,
            conflicts=conflicts,
            error=None,
            metadata={"device_id": "device123"}
        )
        
        assert sync_event.id == sync_id
        assert sync_event.store_id == store_id
        assert sync_event.direction == SyncDirection.BIDIRECTIONAL
        assert sync_event.collections == collections
        assert sync_event.status == SyncStatus.COMPLETED
        assert sync_event.start_time == start_time
        assert sync_event.end_time == end_time
        assert sync_event.changes_pushed == 10
        assert sync_event.changes_pulled == 5
        assert sync_event.conflicts == conflicts
        assert sync_event.error is None
        assert sync_event.metadata == {"device_id": "device123"}
    
    def test_start_sync(self):
        sync_id = SyncId("sync123")
        store_id = StoreId("store123")
        collections = [CollectionId("coll1")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.PUSH,
            collections=collections
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Start the sync
            sync_event.start()
            
            assert sync_event.status == SyncStatus.IN_PROGRESS
            assert sync_event.start_time == fixed_time
            assert sync_event.end_time is None
    
    def test_complete_sync(self):
        sync_id = SyncId("sync123")
        store_id = StoreId("store123")
        collections = [CollectionId("coll1")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.PULL,
            collections=collections,
            status=SyncStatus.IN_PROGRESS
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Complete the sync
            sync_event.complete(changes_pushed=0, changes_pulled=15)
            
            assert sync_event.status == SyncStatus.COMPLETED
            assert sync_event.end_time == fixed_time
            assert sync_event.changes_pushed == 0
            assert sync_event.changes_pulled == 15
            assert sync_event.error is None
    
    def test_fail_sync(self):
        sync_id = SyncId("sync123")
        store_id = StoreId("store123")
        collections = [CollectionId("coll1")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.BIDIRECTIONAL,
            collections=collections,
            status=SyncStatus.IN_PROGRESS
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Fail the sync
            sync_event.fail("Network error")
            
            assert sync_event.status == SyncStatus.FAILED
            assert sync_event.end_time == fixed_time
            assert sync_event.error == "Network error"
    
    def test_partial_complete_sync(self):
        sync_id = SyncId("sync123")
        store_id = StoreId("store123")
        collections = [CollectionId("coll1")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.BIDIRECTIONAL,
            collections=collections,
            status=SyncStatus.IN_PROGRESS
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Partially complete the sync
            sync_event.partial_complete(
                changes_pushed=10,
                changes_pulled=0,
                error="Failed to pull changes"
            )
            
            assert sync_event.status == SyncStatus.PARTIAL
            assert sync_event.end_time == fixed_time
            assert sync_event.changes_pushed == 10
            assert sync_event.changes_pulled == 0
            assert sync_event.error == "Failed to pull changes"
    
    def test_add_conflict(self):
        sync_id = SyncId("sync123")
        store_id = StoreId("store123")
        collections = [CollectionId("coll1")]
        
        sync_event = SyncEvent(
            id=sync_id,
            store_id=store_id,
            direction=SyncDirection.BIDIRECTIONAL,
            collections=collections
        )
        
        # Add a conflict
        conflict_id = ConflictId("conflict123")
        sync_event.add_conflict(conflict_id)
        
        assert conflict_id in sync_event.conflicts
        
        # Add another conflict
        conflict_id2 = ConflictId("conflict456")
        sync_event.add_conflict(conflict_id2)
        
        assert conflict_id2 in sync_event.conflicts
        assert len(sync_event.conflicts) == 2


class TestConflict:
    
    def test_create_conflict(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        created_at = datetime(2023, 1, 1, tzinfo=UTC)
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            resolved=False,
            resolution_strategy=None,
            resolved_data=None,
            sync_id=sync_id,
            created_at=created_at,
            resolved_at=None,
            metadata={"conflict_type": "update"}
        )
        
        assert conflict.id == conflict_id
        assert conflict.document_id == document_id
        assert conflict.collection_id == collection_id
        assert conflict.client_data == {"name": "Client Name"}
        assert conflict.server_data == {"name": "Server Name"}
        assert conflict.client_version == 2
        assert conflict.server_version == 3
        assert conflict.resolved is False
        assert conflict.resolution_strategy is None
        assert conflict.resolved_data is None
        assert conflict.sync_id == sync_id
        assert conflict.created_at == created_at
        assert conflict.resolved_at is None
        assert conflict.metadata == {"conflict_type": "update"}
    
    def test_resolve_conflict_client_wins(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Resolve using client wins strategy
            conflict.resolve(ConflictResolutionStrategy.CLIENT_WINS)
            
            assert conflict.resolved is True
            assert conflict.resolution_strategy == ConflictResolutionStrategy.CLIENT_WINS
            assert conflict.resolved_at == fixed_time
            assert conflict.resolved_data == {"name": "Client Name"}
    
    def test_resolve_conflict_server_wins(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        
        # Resolve using server wins strategy
        conflict.resolve(ConflictResolutionStrategy.SERVER_WINS)
        
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ConflictResolutionStrategy.SERVER_WINS
        assert conflict.resolved_data == {"name": "Server Name"}
    
    def test_resolve_conflict_latest_wins_client(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=4,  # Client version is higher
            server_version=3,
            sync_id=sync_id
        )
        
        # Resolve using latest wins strategy
        conflict.resolve(ConflictResolutionStrategy.LATEST_WINS)
        
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ConflictResolutionStrategy.LATEST_WINS
        assert conflict.resolved_data == {"name": "Client Name"}  # Client wins because its version is higher
    
    def test_resolve_conflict_latest_wins_server(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=5,  # Server version is higher
            sync_id=sync_id
        )
        
        # Resolve using latest wins strategy
        conflict.resolve(ConflictResolutionStrategy.LATEST_WINS)
        
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ConflictResolutionStrategy.LATEST_WINS
        assert conflict.resolved_data == {"name": "Server Name"}  # Server wins because its version is higher
    
    def test_resolve_conflict_merge(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name", "email": "client@example.com"},
            server_data={"name": "Server Name", "phone": "123-456-7890"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        
        # Resolve using merge strategy
        merged_data = {
            "name": "Merged Name",
            "email": "client@example.com",  # From client
            "phone": "123-456-7890"  # From server
        }
        
        conflict.resolve(ConflictResolutionStrategy.MERGE, merged_data)
        
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ConflictResolutionStrategy.MERGE
        assert conflict.resolved_data == merged_data
    
    def test_resolve_conflict_merge_without_data(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        
        # Attempt to resolve using merge strategy without providing data
        with pytest.raises(ValueError) as exc:
            conflict.resolve(ConflictResolutionStrategy.MERGE)
        
        assert "Resolved data must be provided for merge strategy" in str(exc.value)
        assert conflict.resolved is False
    
    def test_resolve_conflict_manual(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        
        # Resolve using manual strategy
        manual_data = {"name": "Manually Resolved Name"}
        conflict.resolve(ConflictResolutionStrategy.MANUAL, manual_data)
        
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ConflictResolutionStrategy.MANUAL
        assert conflict.resolved_data == manual_data
    
    def test_resolve_conflict_manual_without_data(self):
        conflict_id = ConflictId("conflict123")
        document_id = DocumentId("doc123")
        collection_id = CollectionId("coll123")
        sync_id = SyncId("sync123")
        
        conflict = Conflict(
            id=conflict_id,
            document_id=document_id,
            collection_id=collection_id,
            client_data={"name": "Client Name"},
            server_data={"name": "Server Name"},
            client_version=2,
            server_version=3,
            sync_id=sync_id
        )
        
        # Attempt to resolve using manual strategy without providing data
        with pytest.raises(ValueError) as exc:
            conflict.resolve(ConflictResolutionStrategy.MANUAL)
        
        assert "Resolved data must be provided for manual strategy" in str(exc.value)
        assert conflict.resolved is False


class TestNetworkState:
    
    def test_create_network_state(self):
        network_state = NetworkState(
            id="net123",
            status=NetworkStatus.ONLINE,
            last_online=datetime(2023, 1, 1, tzinfo=UTC),
            last_offline=datetime(2022, 12, 31, tzinfo=UTC),
            check_interval=60,
            last_check=datetime(2023, 1, 1, 1, tzinfo=UTC),
            metadata={"connection_type": "wifi"}
        )
        
        assert network_state.id == "net123"
        assert network_state.status == NetworkStatus.ONLINE
        assert network_state.last_online == datetime(2023, 1, 1, tzinfo=UTC)
        assert network_state.last_offline == datetime(2022, 12, 31, tzinfo=UTC)
        assert network_state.check_interval == 60
        assert network_state.last_check == datetime(2023, 1, 1, 1, tzinfo=UTC)
        assert network_state.metadata == {"connection_type": "wifi"}
    
    def test_update_status_to_online(self):
        network_state = NetworkState(
            status=NetworkStatus.OFFLINE
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Update to online
            network_state.update_status(NetworkStatus.ONLINE)
            
            assert network_state.status == NetworkStatus.ONLINE
            assert network_state.last_online == fixed_time
            assert network_state.last_check == fixed_time
    
    def test_update_status_to_offline(self):
        network_state = NetworkState(
            status=NetworkStatus.ONLINE
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Update to offline
            network_state.update_status(NetworkStatus.OFFLINE)
            
            assert network_state.status == NetworkStatus.OFFLINE
            assert network_state.last_offline == fixed_time
            assert network_state.last_check == fixed_time
    
    def test_update_status_no_change(self):
        network_state = NetworkState(
            status=NetworkStatus.ONLINE,
            last_online=datetime(2022, 12, 31, tzinfo=UTC)
        )
        
        # Set up mock datetime
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Update to same status
            network_state.update_status(NetworkStatus.ONLINE)
            
            assert network_state.status == NetworkStatus.ONLINE
            assert network_state.last_online == datetime(2022, 12, 31, tzinfo=UTC)  # Unchanged
            assert network_state.last_check == fixed_time  # Still updated
    
    def test_is_online(self):
        online_state = NetworkState(status=NetworkStatus.ONLINE)
        offline_state = NetworkState(status=NetworkStatus.OFFLINE)
        limited_state = NetworkState(status=NetworkStatus.LIMITED)
        
        assert online_state.is_online() is True
        assert offline_state.is_online() is False
        assert limited_state.is_online() is False