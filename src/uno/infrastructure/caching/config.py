"""Cache configuration module.

This module provides configuration options for the Uno caching framework.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Literal


@dataclass
class LocalCacheConfig:
    """Configuration for local cache."""

    type: Literal["memory", "file"] = "memory"
    max_size: int = 1000  # Max number of items for memory cache or MB for file cache
    ttl: int = 300  # Default TTL in seconds
    serializer: str = "pickle"  # Default serializer

    # Memory cache specific options
    lru_policy: bool = True  # Use LRU eviction policy

    # File cache specific options
    directory: str | None = None  # Cache directory for file cache
    shards: int = 8  # Number of shards for file cache


@dataclass
class DistributedCacheConfig:
    """Configuration for distributed cache."""

    enabled: bool = False
    type: Literal["redis", "memcached"] = "redis"

    # Connection settings
    connection_string: str | None = None
    hosts: list[str] = field(default_factory=list)  # List of host:port strings
    username: str | None = None
    password: str | None = None
    database: int = 0  # Redis database number

    # Redis specific options
    use_connection_pool: bool = True
    max_connections: int = 10
    socket_timeout: float = 2.0
    socket_connect_timeout: float = 1.0
    retry_on_timeout: bool = True

    # Memcached specific options
    max_pool_size: int = 10
    connect_timeout: float = 1.0

    # General settings
    serializer: str = "pickle"
    prefix: str = "uno:"
    ttl: int = 300  # Default TTL in seconds


@dataclass
class InvalidationConfig:
    """Configuration for cache invalidation strategies."""

    time_based: bool = True  # Enable time-based invalidation
    event_based: bool = True  # Enable event-based invalidation
    pattern_based: bool = True  # Enable pattern-based invalidation
    consistent_hashing: bool = False  # Use consistent hashing for shard invalidation

    # Time-based invalidation settings
    default_ttl: int = 300  # Default TTL in seconds
    ttl_jitter: float = 0.1  # Jitter to add to TTL to prevent stampede

    # Event-based invalidation settings
    event_handlers: Dict[str, list[str]] = field(
        default_factory=dict
    )  # Event to patterns mapping

    # Pattern-based invalidation settings
    patterns: Dict[str, list[str]] = field(
        default_factory=dict
    )  # Entity to patterns mapping


@dataclass
class MonitoringConfig:
    """Configuration for cache monitoring."""

    enabled: bool = True
    collect_metrics: bool = True
    detailed_stats: bool = False
    log_level: str = "INFO"
    prometheus_export: bool = False
    export_port: int = 9090

    # Thresholds for alerts
    hit_rate_threshold: float = 0.5  # Alert if hit rate falls below this
    memory_usage_threshold: float = 0.9  # Alert if memory usage exceeds this
    latency_threshold: float = 50.0  # Alert if latency exceeds this (ms)


@dataclass
class CacheConfig:
    """Main configuration for the caching framework."""

    enabled: bool = True
    default_enabled: bool = True  # Default for new caches

    # Cache hierarchy and fallback
    use_multi_level: bool = True  # Use multi-level caching
    fallback_on_error: bool = True  # Try next level on error

    # Default layer configurations
    local: LocalCacheConfig = field(default_factory=LocalCacheConfig)
    distributed: DistributedCacheConfig = field(default_factory=DistributedCacheConfig)
    invalidation: InvalidationConfig = field(default_factory=InvalidationConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Key generation
    key_prefix: str = "uno:"
    use_hash_keys: bool = True  # Hash keys to ensure safe cache keys
    hash_algorithm: str = "md5"  # Algorithm for key hashing

    # Cache regions/namespaces
    regions: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def development_defaults(cls) -> "CacheConfig":
        """Create a configuration optimized for development."""
        return cls(
            enabled=True,
            default_enabled=True,
            use_multi_level=False,
            local=LocalCacheConfig(
                type="memory",
                max_size=100,
                ttl=60,  # Short TTL for development
            ),
            distributed=DistributedCacheConfig(
                enabled=False,  # Disabled by default in development
            ),
            invalidation=InvalidationConfig(
                time_based=True,
                event_based=True,
                pattern_based=False,  # Simplified in development
                default_ttl=60,  # Short TTL for development
            ),
            monitoring=MonitoringConfig(
                enabled=True,
                collect_metrics=True,
                detailed_stats=True,  # More detailed for development debugging
                log_level="DEBUG",
                prometheus_export=False,
            ),
        )

    @classmethod
    def production_defaults(cls) -> "CacheConfig":
        """Create a configuration optimized for production."""
        return cls(
            enabled=True,
            default_enabled=True,
            use_multi_level=True,
            local=LocalCacheConfig(
                type="memory",
                max_size=10000,
                ttl=3600,  # Longer TTL for production
                lru_policy=True,
            ),
            distributed=DistributedCacheConfig(
                enabled=True,
                type="redis",
                use_connection_pool=True,
                max_connections=50,
                ttl=3600,  # Longer TTL for production
            ),
            invalidation=InvalidationConfig(
                time_based=True,
                event_based=True,
                pattern_based=True,
                consistent_hashing=True,
                default_ttl=3600,  # Longer TTL for production
            ),
            monitoring=MonitoringConfig(
                enabled=True,
                collect_metrics=True,
                detailed_stats=False,  # Less overhead in production
                log_level="INFO",
                prometheus_export=True,
            ),
        )
