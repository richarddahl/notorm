"""Options for configuring the synchronization engine.

This module defines the configuration options for the synchronization
engine, including synchronization strategy, network adapter, and
conflict resolution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Set, Callable, Type


@dataclass
class SyncOptions:
    """Options for configuring the synchronization engine.
    
    Attributes:
        collections: Collections to synchronize.
        strategy: The synchronization strategy to use.
        network_adapter: The network adapter for server communication.
        conflict_strategy: Strategy for resolving conflicts.
        auto_sync_interval: Interval in seconds for automatic synchronization.
        sync_on_connect: Whether to sync when network connection is established.
        sync_on_background: Whether to sync in the background.
        sync_order: Order in which collections should be synchronized.
        max_sync_attempts: Maximum number of synchronization attempts.
        retry_delay: Delay in seconds between retry attempts.
        sync_filters: Filters to apply when syncing collections.
        field_inclusion: Fields to include in synchronization.
        priority_records: Functions to determine record sync priority.
        background_sync_mode: Priority mode for background synchronization.
        network_timeout: Timeout in seconds for network operations.
    """
    
    collections: List[str]
    strategy: Any
    network_adapter: Any
    conflict_strategy: Union[str, Callable, Any] = "server-wins"
    auto_sync_interval: int = 0  # 0 means no auto-sync
    sync_on_connect: bool = True
    sync_on_background: bool = False
    sync_order: Optional[List[str]] = None
    max_sync_attempts: int = 3
    retry_delay: int = 5  # seconds
    sync_filters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    field_inclusion: Dict[str, List[str]] = field(default_factory=dict)
    priority_records: Dict[str, Callable[[Dict[str, Any]], bool]] = field(default_factory=dict)
    background_sync_mode: str = "normal"  # "low-priority", "normal", "high-priority"
    network_timeout: int = 30  # seconds
    
    def __post_init__(self):
        """Validate synchronization options."""
        # Validate conflict strategy
        valid_conflict_strategies = ["server-wins", "client-wins", "timestamp-wins", "last-write-wins"]
        if isinstance(self.conflict_strategy, str) and self.conflict_strategy not in valid_conflict_strategies:
            raise ValueError(f"Invalid conflict strategy: {self.conflict_strategy}. "
                           f"Valid options are: {', '.join(valid_conflict_strategies)}")
        
        # Validate background sync mode
        valid_modes = ["low-priority", "normal", "high-priority"]
        if self.background_sync_mode not in valid_modes:
            raise ValueError(f"Invalid background sync mode: {self.background_sync_mode}. "
                           f"Valid options are: {', '.join(valid_modes)}")
        
        # Validate sync order if provided
        if self.sync_order:
            # Check if all collections in sync_order are in collections
            for collection in self.sync_order:
                if collection not in self.collections:
                    raise ValueError(f"Collection {collection} in sync_order is not in collections")
            
            # Check if all collections are in sync_order
            for collection in self.collections:
                if collection not in self.sync_order:
                    raise ValueError(f"Collection {collection} is not in sync_order")
        else:
            # Default sync order is the order of collections
            self.sync_order = list(self.collections)
        
        # Validate sync filters
        for collection, filter_spec in self.sync_filters.items():
            if collection not in self.collections:
                raise ValueError(f"Collection {collection} in sync_filters is not in collections")
        
        # Validate field inclusion
        for collection, fields in self.field_inclusion.items():
            if collection not in self.collections:
                raise ValueError(f"Collection {collection} in field_inclusion is not in collections")
        
        # Validate priority records
        for collection in self.priority_records.keys():
            if collection not in self.collections:
                raise ValueError(f"Collection {collection} in priority_records is not in collections")