"""
Domain entities for the Offline module.

This module defines the core domain entities for the Offline module,
including storage, synchronization, and change tracking concepts.
"""

from datetime import datetime, UTC
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, TypeVar, Generic, Union

from uno.domain.core import Entity, AggregateRoot, ValueObject


# Value Objects
@dataclass(frozen=True)
class StoreId(ValueObject):
    """Identifier for a store."""
    value: str


@dataclass(frozen=True)
class CollectionId(ValueObject):
    """Identifier for a collection."""
    value: str


@dataclass(frozen=True)
class DocumentId(ValueObject):
    """Identifier for a document."""
    value: str


@dataclass(frozen=True)
class TransactionId(ValueObject):
    """Identifier for a transaction."""
    value: str


@dataclass(frozen=True)
class ChangeId(ValueObject):
    """Identifier for a change."""
    value: str


@dataclass(frozen=True)
class SyncId(ValueObject):
    """Identifier for a synchronization event."""
    value: str


@dataclass(frozen=True)
class ConflictId(ValueObject):
    """Identifier for a conflict."""
    value: str


# Enums
class StorageType(str, Enum):
    """Type of storage backend."""
    MEMORY = "memory"
    LOCAL_STORAGE = "local_storage"
    INDEXED_DB = "indexed_db"
    SQLITE = "sqlite"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    """Type of relationship between collections."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class ChangeType(str, Enum):
    """Type of change to a document."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatus(str, Enum):
    """Status of a synchronization event."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncDirection(str, Enum):
    """Direction of a synchronization event."""
    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolutionStrategy(str, Enum):
    """Strategy for resolving conflicts."""
    CLIENT_WINS = "client_wins"
    SERVER_WINS = "server_wins"
    LATEST_WINS = "latest_wins"
    MANUAL = "manual"
    MERGE = "merge"


class NetworkStatus(str, Enum):
    """Network connectivity status."""
    ONLINE = "online"
    OFFLINE = "offline"
    LIMITED = "limited"


# Entities
@dataclass
class StorageOptions(Entity):
    """Configuration options for storage."""
    
    id: StoreId
    name: str
    storage_type: StorageType = StorageType.MEMORY
    version: str = "1.0"
    auto_compaction: bool = True
    compaction_interval: int = 3600  # seconds
    max_size: Optional[int] = None  # bytes
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    encrypt_field_names: bool = False
    compress: bool = False
    serialize_dates: bool = True
    collection_defaults: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionSchema(Entity):
    """Schema definition for a collection."""
    
    id: CollectionId
    name: str
    store_id: StoreId
    key_path: Union[str, List[str]]
    auto_increment: bool = False
    indexes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    validators: List[Dict[str, Any]] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    max_items: Optional[int] = None
    versioned: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_index(self, name: str, key_path: Union[str, List[str]], unique: bool = False) -> None:
        """
        Add an index to the collection schema.
        
        Args:
            name: Name of the index.
            key_path: Path to the indexed key or keys.
            unique: Whether the index enforces uniqueness.
        """
        self.indexes[name] = {
            "key_path": key_path,
            "unique": unique
        }
    
    def add_relationship(
        self,
        name: str,
        collection: str,
        relationship_type: RelationshipType,
        foreign_key: str,
        local_key: Optional[str] = None
    ) -> None:
        """
        Add a relationship to the collection schema.
        
        Args:
            name: Name of the relationship.
            collection: Name of the related collection.
            relationship_type: Type of relationship.
            foreign_key: Foreign key in the related collection.
            local_key: Local key in this collection.
        """
        self.relationships.append({
            "name": name,
            "collection": collection,
            "type": relationship_type,
            "foreign_key": foreign_key,
            "local_key": local_key
        })
    
    def add_validator(self, name: str, validator_fn: str, error_message: str = "") -> None:
        """
        Add a validator to the collection schema.
        
        Args:
            name: Name of the validator.
            validator_fn: Function name or code for validation.
            error_message: Error message to display on validation failure.
        """
        self.validators.append({
            "name": name,
            "function": validator_fn,
            "error_message": error_message
        })


@dataclass
class Document(Entity):
    """A document stored in a collection."""
    
    id: DocumentId
    collection_id: CollectionId
    data: Dict[str, Any]
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted: bool = False
    deleted_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the document data.
        
        Args:
            data: New data to update with.
        """
        # Merge data
        self.data.update(data)
        self.updated_at = datetime.now(UTC)
        self.version += 1
    
    def patch(self, path: str, value: Any) -> None:
        """
        Apply a patch to a specific path in the document.
        
        Args:
            path: Path to update, using dot notation.
            value: New value to set.
        """
        # Split path into parts
        parts = path.split('.')
        
        # Navigate to the target location
        target = self.data
        for i, part in enumerate(parts[:-1]):
            if part not in target:
                target[part] = {}
            target = target[part]
        
        # Set the value
        target[parts[-1]] = value
        
        self.updated_at = datetime.now(UTC)
        self.version += 1
    
    def delete(self) -> None:
        """Mark the document as deleted."""
        self.deleted = True
        self.deleted_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.version += 1


@dataclass
class Transaction(Entity):
    """A transaction in the offline store."""
    
    id: TransactionId
    store_id: StoreId
    operations: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    commit_time: Optional[datetime] = None
    rollback_time: Optional[datetime] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_operation(
        self,
        operation_type: str,
        collection_id: CollectionId,
        document_id: Optional[DocumentId] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an operation to the transaction.
        
        Args:
            operation_type: Type of operation (create, update, delete, etc.).
            collection_id: ID of the collection to operate on.
            document_id: ID of the document to operate on (if applicable).
            data: Data for the operation (if applicable).
        """
        self.operations.append({
            "type": operation_type,
            "collection_id": collection_id.value,
            "document_id": document_id.value if document_id else None,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    def commit(self) -> None:
        """Mark the transaction as committed."""
        self.status = "committed"
        self.commit_time = datetime.now(UTC)
    
    def rollback(self) -> None:
        """Mark the transaction as rolled back."""
        self.status = "rolled_back"
        self.rollback_time = datetime.now(UTC)


@dataclass
class Change(Entity):
    """A change to a document."""
    
    id: ChangeId
    document_id: DocumentId
    collection_id: CollectionId
    change_type: ChangeType
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    transaction_id: Optional[TransactionId] = None
    version: int = 1
    synchronized: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_synchronized(self) -> None:
        """Mark the change as synchronized."""
        self.synchronized = True
        self.metadata["synchronized_at"] = datetime.now(UTC).isoformat()


@dataclass
class SyncEvent(Entity):
    """A synchronization event."""
    
    id: SyncId
    store_id: StoreId
    direction: SyncDirection
    collections: List[CollectionId]
    status: SyncStatus = SyncStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    changes_pushed: int = 0
    changes_pulled: int = 0
    conflicts: List[ConflictId] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Mark the sync event as started."""
        self.status = SyncStatus.IN_PROGRESS
        self.start_time = datetime.now(UTC)
    
    def complete(self, changes_pushed: int = 0, changes_pulled: int = 0) -> None:
        """
        Mark the sync event as completed.
        
        Args:
            changes_pushed: Number of changes pushed to server.
            changes_pulled: Number of changes pulled from server.
        """
        self.status = SyncStatus.COMPLETED
        self.end_time = datetime.now(UTC)
        self.changes_pushed = changes_pushed
        self.changes_pulled = changes_pulled
    
    def fail(self, error: str) -> None:
        """
        Mark the sync event as failed.
        
        Args:
            error: Error message.
        """
        self.status = SyncStatus.FAILED
        self.end_time = datetime.now(UTC)
        self.error = error
    
    def partial_complete(
        self,
        changes_pushed: int = 0,
        changes_pulled: int = 0,
        error: Optional[str] = None
    ) -> None:
        """
        Mark the sync event as partially completed.
        
        Args:
            changes_pushed: Number of changes pushed to server.
            changes_pulled: Number of changes pulled from server.
            error: Optional error message.
        """
        self.status = SyncStatus.PARTIAL
        self.end_time = datetime.now(UTC)
        self.changes_pushed = changes_pushed
        self.changes_pulled = changes_pulled
        self.error = error
    
    def add_conflict(self, conflict_id: ConflictId) -> None:
        """
        Add a conflict to the sync event.
        
        Args:
            conflict_id: ID of the conflict.
        """
        self.conflicts.append(conflict_id)


@dataclass
class Conflict(Entity):
    """A conflict between client and server data."""
    
    id: ConflictId
    document_id: DocumentId
    collection_id: CollectionId
    client_data: Dict[str, Any]
    server_data: Dict[str, Any]
    client_version: int
    server_version: int
    resolved: bool = False
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    resolved_data: Optional[Dict[str, Any]] = None
    sync_id: SyncId
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(
        self,
        strategy: ConflictResolutionStrategy,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Resolve the conflict.
        
        Args:
            strategy: Strategy used to resolve the conflict.
            data: Resolved data (if applicable).
        """
        self.resolved = True
        self.resolution_strategy = strategy
        self.resolved_at = datetime.now(UTC)
        
        # Set resolved data based on strategy
        if strategy == ConflictResolutionStrategy.CLIENT_WINS:
            self.resolved_data = self.client_data
        elif strategy == ConflictResolutionStrategy.SERVER_WINS:
            self.resolved_data = self.server_data
        elif strategy == ConflictResolutionStrategy.LATEST_WINS:
            if self.client_version > self.server_version:
                self.resolved_data = self.client_data
            else:
                self.resolved_data = self.server_data
        elif strategy == ConflictResolutionStrategy.MERGE:
            # For merge, resolved data must be provided
            if data is None:
                raise ValueError("Resolved data must be provided for merge strategy")
            self.resolved_data = data
        elif strategy == ConflictResolutionStrategy.MANUAL:
            # For manual resolution, resolved data must be provided
            if data is None:
                raise ValueError("Resolved data must be provided for manual strategy")
            self.resolved_data = data


@dataclass
class NetworkState(Entity):
    """Network connectivity state."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: NetworkStatus = NetworkStatus.ONLINE
    last_online: Optional[datetime] = None
    last_offline: Optional[datetime] = None
    check_interval: int = 30  # seconds
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, status: NetworkStatus) -> None:
        """
        Update the network status.
        
        Args:
            status: New network status.
        """
        if status != self.status:
            now = datetime.now(UTC)
            
            if status == NetworkStatus.ONLINE:
                self.last_online = now
            elif status == NetworkStatus.OFFLINE:
                self.last_offline = now
            
            self.status = status
        
        self.last_check = datetime.now(UTC)
    
    def is_online(self) -> bool:
        """
        Check if the network is online.
        
        Returns:
            True if the network is online, False otherwise.
        """
        return self.status == NetworkStatus.ONLINE