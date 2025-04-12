"""Offline support module for the Uno framework.

This module provides support for offline operations, data synchronization,
conflict resolution, and progressive enhancement. It enables applications
to function reliably even with limited or no network connectivity.
"""

from uno.offline.store import (
    OfflineStore, 
    StorageOptions, 
    EncryptionOptions,
    StorageBackend,
    StorageAdapter,
    StorageManager
)

from uno.offline.sync import (
    SynchronizationEngine,
    SyncOptions,
    SyncStrategy,
    SyncStatus
)

from uno.offline.change_tracking import (
    ChangeTracker,
    ChangeType,
    Change
)

from uno.offline.resolution import (
    ConflictResolver,
    ConflictResolutionStrategy,
    Conflict
)

__all__ = [
    # Offline Store
    'OfflineStore',
    'StorageOptions',
    'EncryptionOptions',
    'StorageBackend',
    'StorageAdapter',
    'StorageManager',
    
    # Synchronization
    'SynchronizationEngine',
    'SyncOptions',
    'SyncStrategy',
    'SyncStatus',
    
    # Change Tracking
    'ChangeTracker',
    'ChangeType',
    'Change',
    
    # Conflict Resolution
    'ConflictResolver',
    'ConflictResolutionStrategy',
    'Conflict',
]