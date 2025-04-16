"""
Domain provider for the Caching module.

This module provides dependency injection configuration for the Caching module.
"""

from typing import Optional, Any, Dict, cast

import inject

from uno.database.session import AsyncSession
from uno.dependencies.container import UnoContainer
from uno.core.result import Result

from uno.caching.entities import (
    CacheKeyId,
    CacheRegionId,
    CacheProviderId,
    CacheProviderType,
    InvalidationStrategyType,
    CacheItem,
    CacheProvider,
    CacheRegion,
    InvalidationRule,
    CacheConfiguration
)
from uno.caching.domain_repositories import (
    CacheItemRepositoryProtocol,
    CacheProviderRepositoryProtocol,
    CacheRegionRepositoryProtocol,
    InvalidationRuleRepositoryProtocol,
    CacheStatisticRepositoryProtocol,
    CacheConfigurationRepositoryProtocol,
    MemoryCacheItemRepository
)
from uno.caching.domain_services import (
    CacheProviderService,
    CacheRegionService,
    InvalidationRuleService,
    CacheItemService,
    CacheMonitoringService,
    CacheConfigurationService,
    CacheProviderServiceProtocol,
    CacheRegionServiceProtocol,
    InvalidationRuleServiceProtocol,
    CacheItemServiceProtocol,
    CacheMonitoringServiceProtocol,
    CacheConfigurationServiceProtocol
)


def configure_caching_dependencies(container: UnoContainer) -> None:
    """
    Configure caching dependencies in the container.
    
    Args:
        container: The dependency injection container.
    """
    # Register repositories
    container.bind(
        CacheItemRepositoryProtocol,
        MemoryCacheItemRepository
    )
    
    # Note: Other repository implementations would be registered here.
    # For now, we only have the MemoryCacheItemRepository implemented.
    
    # Register services
    container.bind(
        CacheProviderServiceProtocol,
        CacheProviderService
    )
    
    container.bind(
        CacheRegionServiceProtocol,
        CacheRegionService
    )
    
    container.bind(
        InvalidationRuleServiceProtocol,
        InvalidationRuleService
    )
    
    container.bind(
        CacheItemServiceProtocol,
        CacheItemService
    )
    
    container.bind(
        CacheMonitoringServiceProtocol,
        CacheMonitoringService
    )
    
    container.bind(
        CacheConfigurationServiceProtocol,
        CacheConfigurationService
    )


# Helper functions for accessing domain services
async def get_cache_provider_service() -> CacheProviderServiceProtocol:
    """
    Get the cache provider service.
    
    Returns:
        The cache provider service.
    """
    return inject.instance(CacheProviderServiceProtocol)


async def get_cache_region_service() -> CacheRegionServiceProtocol:
    """
    Get the cache region service.
    
    Returns:
        The cache region service.
    """
    return inject.instance(CacheRegionServiceProtocol)


async def get_invalidation_rule_service() -> InvalidationRuleServiceProtocol:
    """
    Get the invalidation rule service.
    
    Returns:
        The invalidation rule service.
    """
    return inject.instance(InvalidationRuleServiceProtocol)


async def get_cache_item_service() -> CacheItemServiceProtocol:
    """
    Get the cache item service.
    
    Returns:
        The cache item service.
    """
    return inject.instance(CacheItemServiceProtocol)


async def get_cache_monitoring_service() -> CacheMonitoringServiceProtocol:
    """
    Get the cache monitoring service.
    
    Returns:
        The cache monitoring service.
    """
    return inject.instance(CacheMonitoringServiceProtocol)


async def get_cache_configuration_service() -> CacheConfigurationServiceProtocol:
    """
    Get the cache configuration service.
    
    Returns:
        The cache configuration service.
    """
    return inject.instance(CacheConfigurationServiceProtocol)


# Convenience functions for common cache operations
async def get_cache_item(key: str, region_name: Optional[str] = None) -> Result[Optional[CacheItem]]:
    """
    Get a cached item by key.
    
    Args:
        key: The cache key.
        region_name: Optional region name.
        
    Returns:
        Result containing the cached item or None if not found.
    """
    service = await get_cache_item_service()
    return await service.get_item(key, region_name)


async def set_cache_item(
    key: str, 
    value: Any, 
    ttl_seconds: Optional[int] = None,
    region_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Result[CacheItem]:
    """
    Set a cached item.
    
    Args:
        key: The cache key.
        value: The value to cache.
        ttl_seconds: Optional time-to-live in seconds.
        region_name: Optional region name.
        metadata: Optional metadata.
        
    Returns:
        Result containing the cached item.
    """
    service = await get_cache_item_service()
    
    expiry = None
    if ttl_seconds is not None:
        from datetime import datetime, timedelta, UTC
        expiry = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
    
    return await service.set_item(key, value, expiry, region_name, metadata)


async def delete_cache_item(key: str, region_name: Optional[str] = None) -> Result[bool]:
    """
    Delete a cached item by key.
    
    Args:
        key: The cache key.
        region_name: Optional region name.
        
    Returns:
        Result containing a boolean indicating success.
    """
    service = await get_cache_item_service()
    return await service.delete_item(key, region_name)


async def clear_cache_region(region_name: Optional[str] = None) -> Result[bool]:
    """
    Clear all cached items in a region.
    
    Args:
        region_name: Optional region name.
        
    Returns:
        Result containing a boolean indicating success.
    """
    service = await get_cache_item_service()
    return await service.clear_region(region_name)


async def invalidate_cache_pattern(pattern: str, region_name: Optional[str] = None) -> Result[int]:
    """
    Invalidate all keys matching a pattern.
    
    Args:
        pattern: The pattern to match against cache keys.
        region_name: Optional region name.
        
    Returns:
        Result containing the number of keys invalidated.
    """
    service = await get_cache_item_service()
    return await service.invalidate_by_pattern(pattern, region_name)


# Register with FastAPI dependency system
def get_caching_dependencies():
    """
    Get dependencies for use with FastAPI.
    
    This function can be called from FastAPI app startup to register
    the caching module's dependencies with the application.
    """
    from fastapi import Depends
    from uno.dependencies.fastapi_integration import (
        inject_dependency,
        register_dependency
    )
    
    # Register domain services for injection in FastAPI routes
    register_dependency(CacheProviderServiceProtocol, lambda: inject.instance(CacheProviderServiceProtocol))
    register_dependency(CacheRegionServiceProtocol, lambda: inject.instance(CacheRegionServiceProtocol))
    register_dependency(InvalidationRuleServiceProtocol, lambda: inject.instance(InvalidationRuleServiceProtocol))
    register_dependency(CacheItemServiceProtocol, lambda: inject.instance(CacheItemServiceProtocol))
    register_dependency(CacheMonitoringServiceProtocol, lambda: inject.instance(CacheMonitoringServiceProtocol))
    register_dependency(CacheConfigurationServiceProtocol, lambda: inject.instance(CacheConfigurationServiceProtocol))
    
    # Return dependency accessors for FastAPI
    return {
        "get_cache_provider_service": Depends(inject_dependency(CacheProviderServiceProtocol)),
        "get_cache_region_service": Depends(inject_dependency(CacheRegionServiceProtocol)),
        "get_invalidation_rule_service": Depends(inject_dependency(InvalidationRuleServiceProtocol)),
        "get_cache_item_service": Depends(inject_dependency(CacheItemServiceProtocol)),
        "get_cache_monitoring_service": Depends(inject_dependency(CacheMonitoringServiceProtocol)),
        "get_cache_configuration_service": Depends(inject_dependency(CacheConfigurationServiceProtocol)),
    }