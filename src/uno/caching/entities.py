"""
Domain entities for the Caching module.

This module defines the core domain entities for the Caching module,
providing a rich domain model for cache management.
"""

from datetime import datetime, UTC
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic

from uno.domain.core import Entity, AggregateRoot, ValueObject


# Value Objects
@dataclass(frozen=True)
class CacheKeyId(ValueObject):
    """Identifier for a cache key."""
    value: str


@dataclass(frozen=True)
class CacheRegionId(ValueObject):
    """Identifier for a cache region."""
    value: str


@dataclass(frozen=True)
class CacheProviderId(ValueObject):
    """Identifier for a cache provider."""
    value: str


@dataclass(frozen=True)
class InvalidationRuleId(ValueObject):
    """Identifier for an invalidation rule."""
    value: str


# Enums
class CacheProviderType(str, Enum):
    """Type of cache provider."""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"
    MEMCACHED = "memcached"
    CUSTOM = "custom"


class InvalidationStrategyType(str, Enum):
    """Type of invalidation strategy."""
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    PATTERN_BASED = "pattern_based"
    COMPOSITE = "composite"


class CacheStatsType(str, Enum):
    """Type of cache statistics."""
    HIT = "hit"
    MISS = "miss"
    ERROR = "error"
    LATENCY = "latency"


class CacheLevel(str, Enum):
    """Cache level in multi-level caching."""
    LOCAL = "local"
    DISTRIBUTED = "distributed"


# Entities
@dataclass
class CacheItem(Entity):
    """A cached item."""
    
    key: CacheKeyId
    value: Any
    expiry: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    region: Optional[CacheRegionId] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """
        Check if the cache item is expired.
        
        Returns:
            True if the item is expired, False otherwise.
        """
        return self.expiry is not None and datetime.now(UTC) > self.expiry
    
    def access(self) -> None:
        """Update the last accessed time."""
        self.last_accessed = datetime.now(UTC)


@dataclass
class CacheProvider(Entity):
    """A cache provider."""
    
    id: CacheProviderId
    name: str
    provider_type: CacheProviderType
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True
    connection_details: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def activate(self) -> None:
        """Activate the cache provider."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the cache provider."""
        self.is_active = False


@dataclass
class CacheRegion(Entity):
    """A cache region."""
    
    id: CacheRegionId
    name: str
    ttl: int
    provider_id: CacheProviderId
    max_size: Optional[int] = None
    invalidation_strategy: Optional[InvalidationStrategyType] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvalidationRule(Entity):
    """A cache invalidation rule."""
    
    id: InvalidationRuleId
    name: str
    strategy_type: InvalidationStrategyType
    pattern: Optional[str] = None
    ttl: Optional[int] = None
    events: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def activate(self) -> None:
        """Activate the invalidation rule."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the invalidation rule."""
        self.is_active = False
    
    def matches(self, key: str) -> bool:
        """
        Check if a key matches the invalidation rule pattern.
        
        Args:
            key: The key to check.
            
        Returns:
            True if the key matches the rule pattern, False otherwise.
        """
        if self.pattern is None:
            return False
        
        import re
        try:
            pattern = self.pattern.replace("*", ".*")
            return bool(re.match(pattern, key))
        except re.error:
            return False


@dataclass
class CacheStatistic(Entity):
    """A cache statistic."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: CacheProviderId
    stat_type: CacheStatsType
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    value: Union[int, float] = 0
    region: Optional[CacheRegionId] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheOperation(Entity):
    """A cache operation."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str
    key: CacheKeyId
    provider_id: CacheProviderId
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheHealth(Entity):
    """Cache health status."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: CacheProviderId
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_healthy: bool = True
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheConfiguration(AggregateRoot):
    """Cache configuration aggregate."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    key_prefix: str = ""
    use_hash_keys: bool = False
    hash_algorithm: str = "md5"
    use_multi_level: bool = True
    fallback_on_error: bool = True
    local_config: Dict[str, Any] = field(default_factory=lambda: {
        "type": "memory",
        "max_size": 1000,
        "ttl": 300,
        "lru_policy": True
    })
    distributed_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "type": "redis",
        "connection_string": "",
        "ttl": 3600,
        "prefix": ""
    })
    invalidation_config: Dict[str, Any] = field(default_factory=lambda: {
        "time_based": True,
        "event_based": False,
        "pattern_based": False,
        "default_ttl": 300,
        "ttl_jitter": 0.1
    })
    monitoring_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "collect_latency": True,
        "history_size": 1000
    })
    regions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def enable(self) -> None:
        """Enable caching."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable caching."""
        self.enabled = False
    
    def enable_multi_level(self) -> None:
        """Enable multi-level caching."""
        self.use_multi_level = True
    
    def disable_multi_level(self) -> None:
        """Disable multi-level caching."""
        self.use_multi_level = False
    
    def enable_distributed(self) -> None:
        """Enable distributed caching."""
        self.distributed_config["enabled"] = True
    
    def disable_distributed(self) -> None:
        """Disable distributed caching."""
        self.distributed_config["enabled"] = False
    
    def enable_monitoring(self) -> None:
        """Enable cache monitoring."""
        self.monitoring_config["enabled"] = True
    
    def disable_monitoring(self) -> None:
        """Disable cache monitoring."""
        self.monitoring_config["enabled"] = False
    
    def add_region(self, name: str, config: Dict[str, Any]) -> None:
        """
        Add a cache region.
        
        Args:
            name: Region name.
            config: Region configuration.
        """
        self.regions[name] = config
    
    def remove_region(self, name: str) -> bool:
        """
        Remove a cache region.
        
        Args:
            name: Region name.
            
        Returns:
            True if the region was removed, False if not found.
        """
        if name in self.regions:
            del self.regions[name]
            return True
        return False