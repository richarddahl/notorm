"""Synchronization module for the Uno framework.

This module provides support for synchronizing data between local storage
and remote servers, enabling offline-first applications.
"""

from .engine import SynchronizationEngine
from .options import SyncOptions
from .adapter import NetworkAdapter, BatchSupportMixin
from .conflict import (
    ConflictResolverBase,
    ServerWinsResolver,
    ClientWinsResolver,
    TimestampBasedResolver,
    MergeFieldsResolver,
    ConflictResolver
)
from .errors import (
    SyncError,
    NetworkError,
    ConflictError,
    SyncCancelledError,
    ConfigurationError,
    StrategyError,
    AdapterError,
    ConflictResolutionError,
    ChangeTrackingError
)
from .tracker import ChangeTracker
from .adapters import RestAdapter

__all__ = [
    # Core classes
    'SynchronizationEngine',
    'SyncOptions',
    'NetworkAdapter',
    'BatchSupportMixin',
    
    # Conflict resolution
    'ConflictResolverBase',
    'ServerWinsResolver',
    'ClientWinsResolver',
    'TimestampBasedResolver',
    'MergeFieldsResolver',
    'ConflictResolver',
    
    # Error types
    'SyncError',
    'NetworkError',
    'ConflictError',
    'SyncCancelledError',
    'ConfigurationError',
    'StrategyError',
    'AdapterError',
    'ConflictResolutionError',
    'ChangeTrackingError',
    
    # Utilities
    'ChangeTracker',
    
    # Adapters
    'RestAdapter'
]