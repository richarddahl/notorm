"""Uno Caching Framework.

This module provides a comprehensive caching framework for Uno applications,
including multi-level caching, distributed caching, cache invalidation strategies,
and monitoring tools.
"""

# Use the domain-driven approach instead of legacy exports
# See domain-based components below

# Domain-driven design exports
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
    CacheProviderServiceProtocol,
    CacheRegionServiceProtocol,
    InvalidationRuleServiceProtocol,
    CacheItemServiceProtocol,
    CacheMonitoringServiceProtocol,
    CacheConfigurationServiceProtocol,
    CacheProviderService,
    CacheRegionService,
    InvalidationRuleService,
    CacheItemService,
    CacheMonitoringService,
    CacheConfigurationService
)

    configure_caching_dependencies,
    get_cache_provider_service,
    get_cache_region_service,
    get_invalidation_rule_service,
    get_cache_item_service,
    get_cache_monitoring_service,
    get_cache_configuration_service,
    get_cache_item,
    set_cache_item,
    delete_cache_item,
    clear_cache_region,
    invalidate_cache_pattern,
    get_caching_dependencies
)

__version__ = "0.2.0"

__all__ = [
    # Modern domain-driven implementation only
    
    # Domain-driven design exports
    # Entities
    "CacheKeyId",
    "CacheRegionId",
    "CacheProviderId",
    "InvalidationRuleId",
    "CacheProviderType",
    "InvalidationStrategyType",
    "CacheStatsType",
    "CacheLevel",
    "CacheItem",
    "CacheProvider",
    "CacheRegion",
    "InvalidationRule",
    "CacheStatistic",
    "CacheOperation",
    "CacheHealth",
    "CacheConfiguration",
    
    # Repositories
    "CacheItemRepositoryProtocol",
    "CacheProviderRepositoryProtocol",
    "CacheRegionRepositoryProtocol",
    "InvalidationRuleRepositoryProtocol",
    "CacheStatisticRepositoryProtocol",
    "CacheConfigurationRepositoryProtocol",
    "MemoryCacheItemRepository",
    
    # Services
    "CacheProviderServiceProtocol",
    "CacheRegionServiceProtocol",
    "InvalidationRuleServiceProtocol",
    "CacheItemServiceProtocol",
    "CacheMonitoringServiceProtocol",
    "CacheConfigurationServiceProtocol",
    "CacheProviderService",
    "CacheRegionService",
    "InvalidationRuleService",
    "CacheItemService",
    "CacheMonitoringService",
    "CacheConfigurationService",
    
    # Provider
    "configure_caching_dependencies",
    "get_cache_provider_service",
    "get_cache_region_service",
    "get_invalidation_rule_service",
    "get_cache_item_service",
    "get_cache_monitoring_service",
    "get_cache_configuration_service",
    "get_cache_item",
    "set_cache_item",
    "delete_cache_item",
    "clear_cache_region",
    "invalidate_cache_pattern",
    "get_caching_dependencies"
]