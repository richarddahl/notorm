"""Offline store module for the Uno framework.

The offline store provides a client-side storage system that enables
applications to function effectively without network connectivity.
"""

from uno.offline.store.options import StorageOptions, EncryptionOptions
from uno.offline.store.storage import StorageBackend, StorageAdapter, StorageManager
from uno.offline.store.store import OfflineStore
from uno.offline.store.schema import (
    CollectionSchema, 
    IndexDefinition, 
    RelationshipDefinition
)
from uno.offline.store.query import (
    Query,
    QueryResult,
    FilterOperator
)
from uno.offline.store.transaction import Transaction

__all__ = [
    'OfflineStore',
    'StorageOptions',
    'EncryptionOptions',
    'StorageBackend',
    'StorageAdapter',
    'StorageManager',
    'CollectionSchema',
    'IndexDefinition',
    'RelationshipDefinition',
    'Query',
    'QueryResult',
    'FilterOperator',
    'Transaction'
]