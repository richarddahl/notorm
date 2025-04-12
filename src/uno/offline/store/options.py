"""Options for configuring the offline store.

This module defines the configuration options for the offline store,
including storage backend, encryption, and schema options.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Type


@dataclass
class EncryptionOptions:
    """Options for configuring encryption in the offline store.
    
    Attributes:
        enabled: Whether encryption is enabled.
        algorithm: The encryption algorithm to use.
        sensitive_fields: List of field names that should be encrypted.
        encryption_key_provider: Strategy for providing encryption keys.
        key_rotation_interval: Interval in days for key rotation, if applicable.
    """
    
    enabled: bool = False
    algorithm: str = "AES-GCM"
    sensitive_fields: List[str] = field(default_factory=list)
    encryption_key_provider: str = "user_passphrase"
    key_rotation_interval: Optional[int] = None
    
    def __post_init__(self):
        """Validate encryption options."""
        if self.enabled:
            if not self.algorithm:
                raise ValueError("Encryption algorithm must be specified when encryption is enabled")
            
            valid_algorithms = ["AES-GCM", "AES-CBC", "ChaCha20"]
            if self.algorithm not in valid_algorithms:
                raise ValueError(f"Invalid encryption algorithm: {self.algorithm}. "
                               f"Valid options are: {', '.join(valid_algorithms)}")
            
            valid_providers = ["user_passphrase", "secure_storage", "key_service", "application_key"]
            if self.encryption_key_provider not in valid_providers:
                raise ValueError(f"Invalid encryption key provider: {self.encryption_key_provider}. "
                               f"Valid options are: {', '.join(valid_providers)}")


@dataclass
class IndexDefinition:
    """Definition of an index on a collection.
    
    Attributes:
        name: The name of the index.
        key_path: The field or fields to index.
        unique: Whether the index values must be unique.
        multi_entry: Whether to create an entry for each array element.
    """
    
    name: str
    key_path: Union[str, List[str]]
    unique: bool = False
    multi_entry: bool = False


@dataclass
class RelationshipDefinition:
    """Definition of a relationship between collections.
    
    Attributes:
        name: The name of the relationship.
        collection: The related collection.
        type: The type of relationship.
        foreign_key: The foreign key field.
        local_key: The local key field (defaults to primary key).
    """
    
    name: str
    collection: str
    type: str  # "one-to-one", "one-to-many", "many-to-one", "many-to-many"
    foreign_key: str
    local_key: Optional[str] = None
    
    def __post_init__(self):
        """Validate relationship definition."""
        valid_types = ["one-to-one", "one-to-many", "many-to-one", "many-to-many"]
        if self.type not in valid_types:
            raise ValueError(f"Invalid relationship type: {self.type}. "
                           f"Valid options are: {', '.join(valid_types)}")


@dataclass
class CollectionSchema:
    """Schema definition for a collection.
    
    Attributes:
        name: The name of the collection.
        key_path: The primary key field or fields.
        indexes: List of index definitions.
        relationships: List of relationship definitions.
        versioned: Whether to track version history for records.
        encryption: Collection-specific encryption options.
        eviction_policy: Eviction policy for this collection.
    """
    
    name: str
    key_path: Union[str, List[str]]
    indexes: List[IndexDefinition] = field(default_factory=list)
    relationships: List[RelationshipDefinition] = field(default_factory=list)
    versioned: bool = False
    encryption: Optional[EncryptionOptions] = None
    eviction_policy: Optional[Dict[str, Any]] = None


@dataclass
class StorageOptions:
    """Options for configuring the offline store.
    
    Attributes:
        storage_backend: The storage backend to use.
        database_name: The name of the database.
        version: The database schema version.
        collections: List of collection schemas.
        size_limit: Maximum size in bytes (0 means no limit).
        eviction_strategy: Default eviction strategy.
        encryption: Encryption options.
        auto_compaction: Whether to automatically compact storage.
        compaction_interval: Interval in milliseconds between compactions.
        migration_manager: Optional migration manager.
    """
    
    storage_backend: Union[str, Any]
    database_name: str
    version: int = 1
    collections: List[CollectionSchema] = field(default_factory=list)
    size_limit: int = 0  # 0 means no limit
    eviction_strategy: str = "lru"
    encryption: EncryptionOptions = field(default_factory=EncryptionOptions)
    auto_compaction: bool = True
    compaction_interval: int = 86400000  # 24 hours in milliseconds
    migration_manager: Optional[Any] = None
    
    def __post_init__(self):
        """Validate storage options."""
        if isinstance(self.storage_backend, str):
            valid_backends = ["indexeddb", "websql", "localstorage", "memory"]
            if self.storage_backend not in valid_backends:
                raise ValueError(f"Invalid storage backend: {self.storage_backend}. "
                               f"Valid options are: {', '.join(valid_backends)}")
        
        valid_strategies = ["lru", "lfu", "fifo", "ttl", "size", "none"]
        if self.eviction_strategy not in valid_strategies:
            raise ValueError(f"Invalid eviction strategy: {self.eviction_strategy}. "
                           f"Valid options are: {', '.join(valid_strategies)}")
        
        # Ensure collection names are unique
        collection_names = [collection.name for collection in self.collections]
        if len(collection_names) != len(set(collection_names)):
            raise ValueError("Collection names must be unique")