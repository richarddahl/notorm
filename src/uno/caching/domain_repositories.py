"""
Domain repositories for the Caching module.

This module defines repository interfaces and implementations for the Caching module,
providing data access patterns for cache management.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator, TypeVar, Generic, Union

from uno.core.result import Result
from uno.domain.repository import AsyncDomainRepository

from uno.caching.entities import (
    CacheKeyId,
    CacheRegionId,
    CacheProviderId,
    InvalidationRuleId,
    CacheProviderType,
    InvalidationStrategyType,
    CacheStatsType,
    CacheLevel,
    CacheItem,
    CacheProvider,
    CacheRegion,
    InvalidationRule,
    CacheStatistic,
    CacheOperation,
    CacheHealth,
    CacheConfiguration
)


# Repository Protocols
@runtime_checkable
class CacheItemRepositoryProtocol(Protocol):
    """Protocol for cache item repository."""
    
    async def get(self, key: CacheKeyId, region: Optional[CacheRegionId] = None) -> Result[Optional[CacheItem]]:
        """
        Get a cached item by key.
        
        Args:
            key: The cache key ID.
            region: Optional region ID.
            
        Returns:
            Result containing the cached item or None if not found.
        """
        ...
    
    async def set(self, item: CacheItem) -> Result[bool]:
        """
        Set a cached item.
        
        Args:
            item: The cache item to set.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def delete(self, key: CacheKeyId, region: Optional[CacheRegionId] = None) -> Result[bool]:
        """
        Delete a cached item by key.
        
        Args:
            key: The cache key ID.
            region: Optional region ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def clear(self, region: Optional[CacheRegionId] = None) -> Result[bool]:
        """
        Clear all cached items.
        
        Args:
            region: Optional region ID to clear only items in that region.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def invalidate_pattern(self, pattern: str, region: Optional[CacheRegionId] = None) -> Result[int]:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: The pattern to match against cache keys.
            region: Optional region ID.
            
        Returns:
            Result containing the number of keys invalidated.
        """
        ...
    
    async def get_keys(self, region: Optional[CacheRegionId] = None) -> Result[List[CacheKeyId]]:
        """
        Get all cache keys.
        
        Args:
            region: Optional region ID to get only keys in that region.
            
        Returns:
            Result containing a list of cache key IDs.
        """
        ...
    
    async def get_size(self, region: Optional[CacheRegionId] = None) -> Result[int]:
        """
        Get the number of cached items.
        
        Args:
            region: Optional region ID to get only the size of that region.
            
        Returns:
            Result containing the number of cached items.
        """
        ...


@runtime_checkable
class CacheProviderRepositoryProtocol(Protocol):
    """Protocol for cache provider repository."""
    
    async def create(self, provider: CacheProvider) -> Result[CacheProvider]:
        """
        Create a new cache provider.
        
        Args:
            provider: The cache provider to create.
            
        Returns:
            Result containing the created provider.
        """
        ...
    
    async def get(self, provider_id: CacheProviderId) -> Result[CacheProvider]:
        """
        Get a cache provider by ID.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing the provider or an error if not found.
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[CacheProvider]:
        """
        Get a cache provider by name.
        
        Args:
            name: The provider name.
            
        Returns:
            Result containing the provider or an error if not found.
        """
        ...
    
    async def update(self, provider: CacheProvider) -> Result[CacheProvider]:
        """
        Update a cache provider.
        
        Args:
            provider: The updated provider.
            
        Returns:
            Result containing the updated provider.
        """
        ...
    
    async def delete(self, provider_id: CacheProviderId) -> Result[bool]:
        """
        Delete a cache provider.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def list(self) -> Result[List[CacheProvider]]:
        """
        List all cache providers.
        
        Returns:
            Result containing a list of providers.
        """
        ...


@runtime_checkable
class CacheRegionRepositoryProtocol(Protocol):
    """Protocol for cache region repository."""
    
    async def create(self, region: CacheRegion) -> Result[CacheRegion]:
        """
        Create a new cache region.
        
        Args:
            region: The cache region to create.
            
        Returns:
            Result containing the created region.
        """
        ...
    
    async def get(self, region_id: CacheRegionId) -> Result[CacheRegion]:
        """
        Get a cache region by ID.
        
        Args:
            region_id: The region ID.
            
        Returns:
            Result containing the region or an error if not found.
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[CacheRegion]:
        """
        Get a cache region by name.
        
        Args:
            name: The region name.
            
        Returns:
            Result containing the region or an error if not found.
        """
        ...
    
    async def update(self, region: CacheRegion) -> Result[CacheRegion]:
        """
        Update a cache region.
        
        Args:
            region: The updated region.
            
        Returns:
            Result containing the updated region.
        """
        ...
    
    async def delete(self, region_id: CacheRegionId) -> Result[bool]:
        """
        Delete a cache region.
        
        Args:
            region_id: The region ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def list(self) -> Result[List[CacheRegion]]:
        """
        List all cache regions.
        
        Returns:
            Result containing a list of regions.
        """
        ...


@runtime_checkable
class InvalidationRuleRepositoryProtocol(Protocol):
    """Protocol for invalidation rule repository."""
    
    async def create(self, rule: InvalidationRule) -> Result[InvalidationRule]:
        """
        Create a new invalidation rule.
        
        Args:
            rule: The invalidation rule to create.
            
        Returns:
            Result containing the created rule.
        """
        ...
    
    async def get(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]:
        """
        Get an invalidation rule by ID.
        
        Args:
            rule_id: The rule ID.
            
        Returns:
            Result containing the rule or an error if not found.
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[InvalidationRule]:
        """
        Get an invalidation rule by name.
        
        Args:
            name: The rule name.
            
        Returns:
            Result containing the rule or an error if not found.
        """
        ...
    
    async def update(self, rule: InvalidationRule) -> Result[InvalidationRule]:
        """
        Update an invalidation rule.
        
        Args:
            rule: The updated rule.
            
        Returns:
            Result containing the updated rule.
        """
        ...
    
    async def delete(self, rule_id: InvalidationRuleId) -> Result[bool]:
        """
        Delete an invalidation rule.
        
        Args:
            rule_id: The rule ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        ...
    
    async def list(self) -> Result[List[InvalidationRule]]:
        """
        List all invalidation rules.
        
        Returns:
            Result containing a list of rules.
        """
        ...
    
    async def get_by_strategy_type(self, strategy_type: InvalidationStrategyType) -> Result[List[InvalidationRule]]:
        """
        Get invalidation rules by strategy type.
        
        Args:
            strategy_type: The strategy type.
            
        Returns:
            Result containing a list of rules with the specified strategy type.
        """
        ...


@runtime_checkable
class CacheStatisticRepositoryProtocol(Protocol):
    """Protocol for cache statistic repository."""
    
    async def save(self, statistic: CacheStatistic) -> Result[CacheStatistic]:
        """
        Save a cache statistic.
        
        Args:
            statistic: The statistic to save.
            
        Returns:
            Result containing the saved statistic.
        """
        ...
    
    async def batch_save(self, statistics: List[CacheStatistic]) -> Result[List[CacheStatistic]]:
        """
        Save multiple cache statistics.
        
        Args:
            statistics: The statistics to save.
            
        Returns:
            Result containing the saved statistics.
        """
        ...
    
    async def get_for_provider(
        self, 
        provider_id: CacheProviderId,
        stat_type: Optional[CacheStatsType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Result[List[CacheStatistic]]:
        """
        Get statistics for a provider.
        
        Args:
            provider_id: The provider ID.
            stat_type: Optional filter by statistic type.
            start_time: Optional filter by start time.
            end_time: Optional filter by end time.
            limit: Maximum number of statistics to return.
            
        Returns:
            Result containing a list of statistics.
        """
        ...
    
    async def get_for_region(
        self,
        region_id: CacheRegionId,
        stat_type: Optional[CacheStatsType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Result[List[CacheStatistic]]:
        """
        Get statistics for a region.
        
        Args:
            region_id: The region ID.
            stat_type: Optional filter by statistic type.
            start_time: Optional filter by start time.
            end_time: Optional filter by end time.
            limit: Maximum number of statistics to return.
            
        Returns:
            Result containing a list of statistics.
        """
        ...
    
    async def summarize_by_provider(
        self,
        provider_id: CacheProviderId,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Result[Dict[str, float]]:
        """
        Summarize statistics by provider.
        
        Args:
            provider_id: The provider ID.
            start_time: Optional filter by start time.
            end_time: Optional filter by end time.
            
        Returns:
            Result containing a summary of statistics.
        """
        ...


@runtime_checkable
class CacheConfigurationRepositoryProtocol(Protocol):
    """Protocol for cache configuration repository."""
    
    async def save(self, configuration: CacheConfiguration) -> Result[CacheConfiguration]:
        """
        Save a cache configuration.
        
        Args:
            configuration: The configuration to save.
            
        Returns:
            Result containing the saved configuration.
        """
        ...
    
    async def get(self) -> Result[CacheConfiguration]:
        """
        Get the active cache configuration.
        
        Returns:
            Result containing the active configuration.
        """
        ...
    
    async def get_by_id(self, configuration_id: str) -> Result[CacheConfiguration]:
        """
        Get a cache configuration by ID.
        
        Args:
            configuration_id: The configuration ID.
            
        Returns:
            Result containing the configuration or an error if not found.
        """
        ...
    
    async def list(self) -> Result[List[CacheConfiguration]]:
        """
        List all cache configurations.
        
        Returns:
            Result containing a list of configurations.
        """
        ...


# Repository Implementations
class MemoryCacheItemRepository(AsyncDomainRepository, CacheItemRepositoryProtocol):
    """In-memory implementation of cache item repository."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items: Dict[str, CacheItem] = {}
    
    async def get(self, key: CacheKeyId, region: Optional[CacheRegionId] = None) -> Result[Optional[CacheItem]]:
        """Get a cached item by key."""
        composite_key = self._get_composite_key(key, region)
        item = self.items.get(composite_key)
        
        if item is None:
            return Result.success(None)
        
        if item.is_expired():
            await self.delete(key, region)
            return Result.success(None)
        
        item.access()
        return Result.success(item)
    
    async def set(self, item: CacheItem) -> Result[bool]:
        """Set a cached item."""
        composite_key = self._get_composite_key(item.key, item.region)
        self.items[composite_key] = item
        return Result.success(True)
    
    async def delete(self, key: CacheKeyId, region: Optional[CacheRegionId] = None) -> Result[bool]:
        """Delete a cached item by key."""
        composite_key = self._get_composite_key(key, region)
        if composite_key in self.items:
            del self.items[composite_key]
            return Result.success(True)
        return Result.success(False)
    
    async def clear(self, region: Optional[CacheRegionId] = None) -> Result[bool]:
        """Clear all cached items."""
        if region is None:
            self.items.clear()
        else:
            prefix = f"{region.value}:"
            keys_to_delete = [k for k in self.items.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self.items[key]
        
        return Result.success(True)
    
    async def invalidate_pattern(self, pattern: str, region: Optional[CacheRegionId] = None) -> Result[int]:
        """Invalidate all keys matching a pattern."""
        import re
        try:
            regex = re.compile(pattern.replace("*", ".*"))
            
            if region is None:
                keys_to_delete = [k for k in self.items.keys() if regex.match(k)]
            else:
                prefix = f"{region.value}:"
                keys_to_delete = [k for k in self.items.keys() if k.startswith(prefix) and regex.match(k)]
            
            for key in keys_to_delete:
                del self.items[key]
            
            return Result.success(len(keys_to_delete))
        except re.error as e:
            return Result.failure(f"Invalid pattern: {e}")
    
    async def get_keys(self, region: Optional[CacheRegionId] = None) -> Result[List[CacheKeyId]]:
        """Get all cache keys."""
        if region is None:
            return Result.success([CacheKeyId(key.split(":", 1)[1] if ":" in key else key) for key in self.items.keys()])
        
        prefix = f"{region.value}:"
        keys = [CacheKeyId(key.split(":", 1)[1]) for key in self.items.keys() if key.startswith(prefix)]
        return Result.success(keys)
    
    async def get_size(self, region: Optional[CacheRegionId] = None) -> Result[int]:
        """Get the number of cached items."""
        if region is None:
            return Result.success(len(self.items))
        
        prefix = f"{region.value}:"
        count = sum(1 for key in self.items.keys() if key.startswith(prefix))
        return Result.success(count)
    
    def _get_composite_key(self, key: CacheKeyId, region: Optional[CacheRegionId] = None) -> str:
        """
        Get a composite key for storing/retrieving cache items.
        
        Args:
            key: The cache key ID.
            region: Optional region ID.
            
        Returns:
            A composite key string.
        """
        if region is None:
            return key.value
        return f"{region.value}:{key.value}"


# Additional repository implementations would follow a similar pattern
# For brevity, we'll implement them as needed