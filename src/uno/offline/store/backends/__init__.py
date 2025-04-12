"""Storage backend implementations for the offline store.

This package contains different storage backend implementations
for the offline store.
"""

# Import backend classes for easy access
from uno.offline.store.backends.memory import MemoryBackend
# Future imports
# from uno.offline.store.backends.indexeddb import IndexedDBBackend
# from uno.offline.store.backends.websql import WebSQLBackend
# from uno.offline.store.backends.localstorage import LocalStorageBackend

__all__ = [
    'MemoryBackend',
    # 'IndexedDBBackend',
    # 'WebSQLBackend',
    # 'LocalStorageBackend',
]