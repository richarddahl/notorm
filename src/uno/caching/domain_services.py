"""
Domain services for the Caching module.

This module defines service classes for the Caching module,
providing business logic for cache management.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic, cast, Protocol, runtime_checkable
import asyncio
import logging
import uuid
import re
from dataclasses import dataclass, field

from uno.core.result import Result, Success, Failure
from uno.domain.service import DomainService

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
    CacheConfigurationRepositoryProtocol
)

T = TypeVar('T')
logger = logging.getLogger("uno.caching.services")


# Service Protocols
@runtime_checkable
class CacheProviderServiceProtocol(Protocol):
    """Protocol for cache provider service."""
    
    async def register_provider(
        self, 
        name: str, 
        provider_type: CacheProviderType,
        connection_details: Dict[str, Any] = None,
        configuration: Dict[str, Any] = None
    ) -> Result[CacheProvider]: ...
    
    async def get_provider(self, provider_id: CacheProviderId) -> Result[CacheProvider]: ...
    
    async def get_provider_by_name(self, name: str) -> Result[CacheProvider]: ...
    
    async def update_provider(
        self, 
        provider_id: CacheProviderId, 
        name: Optional[str] = None,
        provider_type: Optional[CacheProviderType] = None,
        connection_details: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Result[CacheProvider]: ...
    
    async def delete_provider(self, provider_id: CacheProviderId) -> Result[bool]: ...
    
    async def list_providers(self) -> Result[List[CacheProvider]]: ...
    
    async def activate_provider(self, provider_id: CacheProviderId) -> Result[CacheProvider]: ...
    
    async def deactivate_provider(self, provider_id: CacheProviderId) -> Result[CacheProvider]: ...
    
    async def check_provider_health(self, provider_id: CacheProviderId) -> Result[CacheHealth]: ...


@runtime_checkable
class CacheRegionServiceProtocol(Protocol):
    """Protocol for cache region service."""
    
    async def create_region(
        self, 
        name: str, 
        provider_id: CacheProviderId,
        ttl: int = 300,
        max_size: Optional[int] = None,
        invalidation_strategy: Optional[InvalidationStrategyType] = None,
        configuration: Dict[str, Any] = None
    ) -> Result[CacheRegion]: ...
    
    async def get_region(self, region_id: CacheRegionId) -> Result[CacheRegion]: ...
    
    async def get_region_by_name(self, name: str) -> Result[CacheRegion]: ...
    
    async def update_region(
        self, 
        region_id: CacheRegionId, 
        name: Optional[str] = None,
        provider_id: Optional[CacheProviderId] = None,
        ttl: Optional[int] = None,
        max_size: Optional[int] = None,
        invalidation_strategy: Optional[InvalidationStrategyType] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[CacheRegion]: ...
    
    async def delete_region(self, region_id: CacheRegionId) -> Result[bool]: ...
    
    async def list_regions(self) -> Result[List[CacheRegion]]: ...
    
    async def list_regions_by_provider(self, provider_id: CacheProviderId) -> Result[List[CacheRegion]]: ...


@runtime_checkable
class InvalidationRuleServiceProtocol(Protocol):
    """Protocol for invalidation rule service."""
    
    async def create_rule(
        self, 
        name: str, 
        strategy_type: InvalidationStrategyType,
        pattern: Optional[str] = None,
        ttl: Optional[int] = None,
        events: List[str] = None,
        configuration: Dict[str, Any] = None
    ) -> Result[InvalidationRule]: ...
    
    async def get_rule(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]: ...
    
    async def get_rule_by_name(self, name: str) -> Result[InvalidationRule]: ...
    
    async def update_rule(
        self, 
        rule_id: InvalidationRuleId, 
        name: Optional[str] = None,
        strategy_type: Optional[InvalidationStrategyType] = None,
        pattern: Optional[str] = None,
        ttl: Optional[int] = None,
        events: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Result[InvalidationRule]: ...
    
    async def delete_rule(self, rule_id: InvalidationRuleId) -> Result[bool]: ...
    
    async def list_rules(self) -> Result[List[InvalidationRule]]: ...
    
    async def list_rules_by_strategy(self, strategy_type: InvalidationStrategyType) -> Result[List[InvalidationRule]]: ...
    
    async def activate_rule(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]: ...
    
    async def deactivate_rule(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]: ...
    
    async def find_matching_rules(self, key: str) -> Result[List[InvalidationRule]]: ...


@runtime_checkable
class CacheItemServiceProtocol(Protocol):
    """Protocol for cache item service."""
    
    async def get_item(self, key: str, region_name: Optional[str] = None) -> Result[Optional[CacheItem]]: ...
    
    async def set_item(
        self, 
        key: str, 
        value: Any, 
        expiry: Optional[datetime] = None,
        region_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[CacheItem]: ...
    
    async def delete_item(self, key: str, region_name: Optional[str] = None) -> Result[bool]: ...
    
    async def clear_region(self, region_name: Optional[str] = None) -> Result[bool]: ...
    
    async def invalidate_by_pattern(self, pattern: str, region_name: Optional[str] = None) -> Result[int]: ...
    
    async def get_keys(self, region_name: Optional[str] = None) -> Result[List[str]]: ...
    
    async def get_region_size(self, region_name: Optional[str] = None) -> Result[int]: ...
    
    async def check_key_matches_rule(self, key: str, rule: InvalidationRule) -> Result[bool]: ...


@runtime_checkable
class CacheMonitoringServiceProtocol(Protocol):
    """Protocol for cache monitoring service."""
    
    async def record_statistic(
        self, 
        provider_id: CacheProviderId,
        stat_type: CacheStatsType,
        value: Union[int, float],
        region: Optional[CacheRegionId] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[CacheStatistic]: ...
    
    async def record_operation(
        self, 
        key: CacheKeyId,
        provider_id: CacheProviderId,
        operation_type: str,
        duration_ms: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[CacheOperation]: ...
    
    async def record_health_check(
        self, 
        provider_id: CacheProviderId,
        is_healthy: bool = True,
        latency_ms: float = 0.0,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Result[CacheHealth]: ...
    
    async def get_provider_statistics(
        self, 
        provider_id: CacheProviderId,
        stat_type: Optional[CacheStatsType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Result[List[CacheStatistic]]: ...
    
    async def get_region_statistics(
        self, 
        region_id: CacheRegionId,
        stat_type: Optional[CacheStatsType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Result[List[CacheStatistic]]: ...
    
    async def get_provider_summary(
        self, 
        provider_id: CacheProviderId,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Result[Dict[str, float]]: ...
    
    async def get_health_history(
        self, 
        provider_id: CacheProviderId,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Result[List[CacheHealth]]: ...


@runtime_checkable
class CacheConfigurationServiceProtocol(Protocol):
    """Protocol for cache configuration service."""
    
    async def get_active_configuration(self) -> Result[CacheConfiguration]: ...
    
    async def save_configuration(self, configuration: CacheConfiguration) -> Result[CacheConfiguration]: ...
    
    async def update_configuration(
        self, 
        enabled: Optional[bool] = None,
        key_prefix: Optional[str] = None,
        use_hash_keys: Optional[bool] = None,
        hash_algorithm: Optional[str] = None,
        use_multi_level: Optional[bool] = None,
        fallback_on_error: Optional[bool] = None,
        local_config: Optional[Dict[str, Any]] = None,
        distributed_config: Optional[Dict[str, Any]] = None,
        invalidation_config: Optional[Dict[str, Any]] = None,
        monitoring_config: Optional[Dict[str, Any]] = None,
        regions: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Result[CacheConfiguration]: ...
    
    async def add_region_config(self, name: str, config: Dict[str, Any]) -> Result[CacheConfiguration]: ...
    
    async def remove_region_config(self, name: str) -> Result[CacheConfiguration]: ...
    
    async def enable_caching(self) -> Result[CacheConfiguration]: ...
    
    async def disable_caching(self) -> Result[CacheConfiguration]: ...
    
    async def enable_multi_level(self) -> Result[CacheConfiguration]: ...
    
    async def disable_multi_level(self) -> Result[CacheConfiguration]: ...
    
    async def enable_distributed(self) -> Result[CacheConfiguration]: ...
    
    async def disable_distributed(self) -> Result[CacheConfiguration]: ...
    
    async def enable_monitoring(self) -> Result[CacheConfiguration]: ...
    
    async def disable_monitoring(self) -> Result[CacheConfiguration]: ...


# Service Implementations
class CacheProviderService(DomainService, CacheProviderServiceProtocol):
    """Service for managing cache providers."""
    
    def __init__(self, repository: CacheProviderRepositoryProtocol):
        self.repository = repository
    
    async def register_provider(
        self, 
        name: str, 
        provider_type: CacheProviderType,
        connection_details: Dict[str, Any] = None,
        configuration: Dict[str, Any] = None
    ) -> Result[CacheProvider]:
        """
        Register a new cache provider.
        
        Args:
            name: The provider name.
            provider_type: The provider type.
            connection_details: Optional connection details.
            configuration: Optional configuration.
            
        Returns:
            Result containing the registered provider.
        """
        try:
            provider_id = CacheProviderId(str(uuid.uuid4()))
            
            provider = CacheProvider(
                id=provider_id,
                name=name,
                provider_type=provider_type,
                connection_details=connection_details or {},
                configuration=configuration or {},
            )
            
            return await self.repository.create(provider)
        except Exception as e:
            logger.error(f"Error registering cache provider: {e}")
            return Failure(f"Failed to register cache provider '{name}': {str(e)}")
    
    async def get_provider(self, provider_id: CacheProviderId) -> Result[CacheProvider]:
        """
        Get a cache provider by ID.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing the provider.
        """
        return await self.repository.get(provider_id)
    
    async def get_provider_by_name(self, name: str) -> Result[CacheProvider]:
        """
        Get a cache provider by name.
        
        Args:
            name: The provider name.
            
        Returns:
            Result containing the provider.
        """
        return await self.repository.get_by_name(name)
    
    async def update_provider(
        self, 
        provider_id: CacheProviderId, 
        name: Optional[str] = None,
        provider_type: Optional[CacheProviderType] = None,
        connection_details: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Result[CacheProvider]:
        """
        Update a cache provider.
        
        Args:
            provider_id: The provider ID.
            name: Optional new name.
            provider_type: Optional new provider type.
            connection_details: Optional new connection details.
            configuration: Optional new configuration.
            is_active: Optional new active status.
            
        Returns:
            Result containing the updated provider.
        """
        provider_result = await self.repository.get(provider_id)
        if not provider_result.is_success():
            return provider_result
        
        provider = provider_result.value
        
        if name is not None:
            provider.name = name
        
        if provider_type is not None:
            provider.provider_type = provider_type
        
        if connection_details is not None:
            provider.connection_details = connection_details
        
        if configuration is not None:
            provider.configuration = configuration
        
        if is_active is not None:
            provider.is_active = is_active
        
        return await self.repository.update(provider)
    
    async def delete_provider(self, provider_id: CacheProviderId) -> Result[bool]:
        """
        Delete a cache provider.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        return await self.repository.delete(provider_id)
    
    async def list_providers(self) -> Result[List[CacheProvider]]:
        """
        List all cache providers.
        
        Returns:
            Result containing a list of providers.
        """
        return await self.repository.list()
    
    async def activate_provider(self, provider_id: CacheProviderId) -> Result[CacheProvider]:
        """
        Activate a cache provider.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing the activated provider.
        """
        provider_result = await self.repository.get(provider_id)
        if not provider_result.is_success():
            return provider_result
        
        provider = provider_result.value
        provider.activate()
        
        return await self.repository.update(provider)
    
    async def deactivate_provider(self, provider_id: CacheProviderId) -> Result[CacheProvider]:
        """
        Deactivate a cache provider.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing the deactivated provider.
        """
        provider_result = await self.repository.get(provider_id)
        if not provider_result.is_success():
            return provider_result
        
        provider = provider_result.value
        provider.deactivate()
        
        return await self.repository.update(provider)
    
    async def check_provider_health(self, provider_id: CacheProviderId) -> Result[CacheHealth]:
        """
        Check the health of a cache provider.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing a health status.
        """
        provider_result = await self.repository.get(provider_id)
        if not provider_result.is_success():
            return Failure(f"Provider not found: {provider_id.value}")
        
        provider = provider_result.value
        
        # In a real implementation, we would connect to the provider
        # and check its health status.
        # For now, we'll just return a simulated health check.
        
        health = CacheHealth(
            provider_id=provider_id,
            is_healthy=provider.is_active,
            latency_ms=0.0,
            details={"simulated": True}
        )
        
        return Success(health)


class CacheRegionService(DomainService, CacheRegionServiceProtocol):
    """Service for managing cache regions."""
    
    def __init__(
        self, 
        repository: CacheRegionRepositoryProtocol,
        provider_repository: CacheProviderRepositoryProtocol
    ):
        self.repository = repository
        self.provider_repository = provider_repository
    
    async def create_region(
        self, 
        name: str, 
        provider_id: CacheProviderId,
        ttl: int = 300,
        max_size: Optional[int] = None,
        invalidation_strategy: Optional[InvalidationStrategyType] = None,
        configuration: Dict[str, Any] = None
    ) -> Result[CacheRegion]:
        """
        Create a new cache region.
        
        Args:
            name: The region name.
            provider_id: The provider ID.
            ttl: The time-to-live in seconds.
            max_size: Optional maximum size.
            invalidation_strategy: Optional invalidation strategy.
            configuration: Optional configuration.
            
        Returns:
            Result containing the created region.
        """
        try:
            # Verify provider exists
            provider_result = await self.provider_repository.get(provider_id)
            if not provider_result.is_success():
                return Failure(f"Provider not found: {provider_id.value}")
            
            region_id = CacheRegionId(name)
            
            region = CacheRegion(
                id=region_id,
                name=name,
                ttl=ttl,
                provider_id=provider_id,
                max_size=max_size,
                invalidation_strategy=invalidation_strategy,
                configuration=configuration or {},
            )
            
            return await self.repository.create(region)
        except Exception as e:
            logger.error(f"Error creating cache region: {e}")
            return Failure(f"Failed to create cache region '{name}': {str(e)}")
    
    async def get_region(self, region_id: CacheRegionId) -> Result[CacheRegion]:
        """
        Get a cache region by ID.
        
        Args:
            region_id: The region ID.
            
        Returns:
            Result containing the region.
        """
        return await self.repository.get(region_id)
    
    async def get_region_by_name(self, name: str) -> Result[CacheRegion]:
        """
        Get a cache region by name.
        
        Args:
            name: The region name.
            
        Returns:
            Result containing the region.
        """
        return await self.repository.get_by_name(name)
    
    async def update_region(
        self, 
        region_id: CacheRegionId, 
        name: Optional[str] = None,
        provider_id: Optional[CacheProviderId] = None,
        ttl: Optional[int] = None,
        max_size: Optional[int] = None,
        invalidation_strategy: Optional[InvalidationStrategyType] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Result[CacheRegion]:
        """
        Update a cache region.
        
        Args:
            region_id: The region ID.
            name: Optional new name.
            provider_id: Optional new provider ID.
            ttl: Optional new TTL.
            max_size: Optional new maximum size.
            invalidation_strategy: Optional new invalidation strategy.
            configuration: Optional new configuration.
            
        Returns:
            Result containing the updated region.
        """
        region_result = await self.repository.get(region_id)
        if not region_result.is_success():
            return region_result
        
        region = region_result.value
        
        if name is not None:
            region.name = name
        
        if provider_id is not None:
            # Verify provider exists
            provider_result = await self.provider_repository.get(provider_id)
            if not provider_result.is_success():
                return Failure(f"Provider not found: {provider_id.value}")
            region.provider_id = provider_id
        
        if ttl is not None:
            region.ttl = ttl
        
        if max_size is not None:
            region.max_size = max_size
        
        if invalidation_strategy is not None:
            region.invalidation_strategy = invalidation_strategy
        
        if configuration is not None:
            region.configuration = configuration
        
        return await self.repository.update(region)
    
    async def delete_region(self, region_id: CacheRegionId) -> Result[bool]:
        """
        Delete a cache region.
        
        Args:
            region_id: The region ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        return await self.repository.delete(region_id)
    
    async def list_regions(self) -> Result[List[CacheRegion]]:
        """
        List all cache regions.
        
        Returns:
            Result containing a list of regions.
        """
        return await self.repository.list()
    
    async def list_regions_by_provider(self, provider_id: CacheProviderId) -> Result[List[CacheRegion]]:
        """
        List cache regions by provider.
        
        Args:
            provider_id: The provider ID.
            
        Returns:
            Result containing a list of regions.
        """
        regions_result = await self.repository.list()
        if not regions_result.is_success():
            return regions_result
        
        regions = [region for region in regions_result.value if region.provider_id.value == provider_id.value]
        
        return Success(regions)


class InvalidationRuleService(DomainService, InvalidationRuleServiceProtocol):
    """Service for managing invalidation rules."""
    
    def __init__(self, repository: InvalidationRuleRepositoryProtocol):
        self.repository = repository
    
    async def create_rule(
        self, 
        name: str, 
        strategy_type: InvalidationStrategyType,
        pattern: Optional[str] = None,
        ttl: Optional[int] = None,
        events: List[str] = None,
        configuration: Dict[str, Any] = None
    ) -> Result[InvalidationRule]:
        """
        Create a new invalidation rule.
        
        Args:
            name: The rule name.
            strategy_type: The strategy type.
            pattern: Optional pattern for pattern-based invalidation.
            ttl: Optional TTL for time-based invalidation.
            events: Optional list of events for event-based invalidation.
            configuration: Optional configuration.
            
        Returns:
            Result containing the created rule.
        """
        try:
            # Validate based on strategy type
            if strategy_type == InvalidationStrategyType.PATTERN_BASED and not pattern:
                return Failure("Pattern is required for pattern-based invalidation")
            
            if strategy_type == InvalidationStrategyType.TIME_BASED and not ttl:
                return Failure("TTL is required for time-based invalidation")
            
            if strategy_type == InvalidationStrategyType.EVENT_BASED and not events:
                return Failure("Events are required for event-based invalidation")
            
            rule_id = InvalidationRuleId(str(uuid.uuid4()))
            
            rule = InvalidationRule(
                id=rule_id,
                name=name,
                strategy_type=strategy_type,
                pattern=pattern,
                ttl=ttl,
                events=events or [],
                configuration=configuration or {},
            )
            
            return await self.repository.create(rule)
        except Exception as e:
            logger.error(f"Error creating invalidation rule: {e}")
            return Failure(f"Failed to create invalidation rule '{name}': {str(e)}")
    
    async def get_rule(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]:
        """
        Get an invalidation rule by ID.
        
        Args:
            rule_id: The rule ID.
            
        Returns:
            Result containing the rule.
        """
        return await self.repository.get(rule_id)
    
    async def get_rule_by_name(self, name: str) -> Result[InvalidationRule]:
        """
        Get an invalidation rule by name.
        
        Args:
            name: The rule name.
            
        Returns:
            Result containing the rule.
        """
        return await self.repository.get_by_name(name)
    
    async def update_rule(
        self, 
        rule_id: InvalidationRuleId, 
        name: Optional[str] = None,
        strategy_type: Optional[InvalidationStrategyType] = None,
        pattern: Optional[str] = None,
        ttl: Optional[int] = None,
        events: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Result[InvalidationRule]:
        """
        Update an invalidation rule.
        
        Args:
            rule_id: The rule ID.
            name: Optional new name.
            strategy_type: Optional new strategy type.
            pattern: Optional new pattern.
            ttl: Optional new TTL.
            events: Optional new list of events.
            configuration: Optional new configuration.
            is_active: Optional new active status.
            
        Returns:
            Result containing the updated rule.
        """
        rule_result = await self.repository.get(rule_id)
        if not rule_result.is_success():
            return rule_result
        
        rule = rule_result.value
        new_strategy_type = strategy_type if strategy_type is not None else rule.strategy_type
        
        # Validate based on strategy type
        if new_strategy_type == InvalidationStrategyType.PATTERN_BASED:
            new_pattern = pattern if pattern is not None else rule.pattern
            if not new_pattern:
                return Failure("Pattern is required for pattern-based invalidation")
        
        if new_strategy_type == InvalidationStrategyType.TIME_BASED:
            new_ttl = ttl if ttl is not None else rule.ttl
            if not new_ttl:
                return Failure("TTL is required for time-based invalidation")
        
        if new_strategy_type == InvalidationStrategyType.EVENT_BASED:
            new_events = events if events is not None else rule.events
            if not new_events:
                return Failure("Events are required for event-based invalidation")
        
        if name is not None:
            rule.name = name
        
        if strategy_type is not None:
            rule.strategy_type = strategy_type
        
        if pattern is not None:
            rule.pattern = pattern
        
        if ttl is not None:
            rule.ttl = ttl
        
        if events is not None:
            rule.events = events
        
        if configuration is not None:
            rule.configuration = configuration
        
        if is_active is not None:
            if is_active:
                rule.activate()
            else:
                rule.deactivate()
        
        return await self.repository.update(rule)
    
    async def delete_rule(self, rule_id: InvalidationRuleId) -> Result[bool]:
        """
        Delete an invalidation rule.
        
        Args:
            rule_id: The rule ID.
            
        Returns:
            Result containing a boolean indicating success.
        """
        return await self.repository.delete(rule_id)
    
    async def list_rules(self) -> Result[List[InvalidationRule]]:
        """
        List all invalidation rules.
        
        Returns:
            Result containing a list of rules.
        """
        return await self.repository.list()
    
    async def list_rules_by_strategy(self, strategy_type: InvalidationStrategyType) -> Result[List[InvalidationRule]]:
        """
        List invalidation rules by strategy type.
        
        Args:
            strategy_type: The strategy type.
            
        Returns:
            Result containing a list of rules.
        """
        return await self.repository.get_by_strategy_type(strategy_type)
    
    async def activate_rule(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]:
        """
        Activate an invalidation rule.
        
        Args:
            rule_id: The rule ID.
            
        Returns:
            Result containing the activated rule.
        """
        rule_result = await self.repository.get(rule_id)
        if not rule_result.is_success():
            return rule_result
        
        rule = rule_result.value
        rule.activate()
        
        return await self.repository.update(rule)
    
    async def deactivate_rule(self, rule_id: InvalidationRuleId) -> Result[InvalidationRule]:
        """
        Deactivate an invalidation rule.
        
        Args:
            rule_id: The rule ID.
            
        Returns:
            Result containing the deactivated rule.
        """
        rule_result = await self.repository.get(rule_id)
        if not rule_result.is_success():
            return rule_result
        
        rule = rule_result.value
        rule.deactivate()
        
        return await self.repository.update(rule)
    
    async def find_matching_rules(self, key: str) -> Result[List[InvalidationRule]]:
        """
        Find all rules that match a given key.
        
        Args:
            key: The cache key.
            
        Returns:
            Result containing a list of matching rules.
        """
        rules_result = await self.repository.list()
        if not rules_result.is_success():
            return rules_result
        
        matching_rules = []
        for rule in rules_result.value:
            if rule.is_active and rule.matches(key):
                matching_rules.append(rule)
        
        return Success(matching_rules)


class CacheItemService(DomainService, CacheItemServiceProtocol):
    """Service for managing cache items."""
    
    def __init__(
        self, 
        repository: CacheItemRepositoryProtocol,
        region_repository: CacheRegionRepositoryProtocol
    ):
        self.repository = repository
        self.region_repository = region_repository
    
    async def get_item(self, key: str, region_name: Optional[str] = None) -> Result[Optional[CacheItem]]:
        """
        Get a cached item by key.
        
        Args:
            key: The cache key.
            region_name: Optional region name.
            
        Returns:
            Result containing the cached item or None if not found.
        """
        try:
            key_id = CacheKeyId(key)
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            return await self.repository.get(key_id, region_id)
        except Exception as e:
            logger.error(f"Error getting cache item: {e}")
            return Failure(f"Failed to get cache item for key '{key}': {str(e)}")
    
    async def set_item(
        self, 
        key: str, 
        value: Any, 
        expiry: Optional[datetime] = None,
        region_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[CacheItem]:
        """
        Set a cached item.
        
        Args:
            key: The cache key.
            value: The value to cache.
            expiry: Optional expiry datetime.
            region_name: Optional region name.
            metadata: Optional metadata.
            
        Returns:
            Result containing the cached item.
        """
        try:
            key_id = CacheKeyId(key)
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            item = CacheItem(
                key=key_id,
                value=value,
                expiry=expiry,
                region=region_id,
                metadata=metadata or {},
            )
            
            result = await self.repository.set(item)
            if result.is_success():
                return Success(item)
            return Failure(f"Failed to set cache item: {result.error}")
        except Exception as e:
            logger.error(f"Error setting cache item: {e}")
            return Failure(f"Failed to set cache item for key '{key}': {str(e)}")
    
    async def delete_item(self, key: str, region_name: Optional[str] = None) -> Result[bool]:
        """
        Delete a cached item by key.
        
        Args:
            key: The cache key.
            region_name: Optional region name.
            
        Returns:
            Result containing a boolean indicating success.
        """
        try:
            key_id = CacheKeyId(key)
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            return await self.repository.delete(key_id, region_id)
        except Exception as e:
            logger.error(f"Error deleting cache item: {e}")
            return Failure(f"Failed to delete cache item for key '{key}': {str(e)}")
    
    async def clear_region(self, region_name: Optional[str] = None) -> Result[bool]:
        """
        Clear all cached items in a region.
        
        Args:
            region_name: Optional region name.
            
        Returns:
            Result containing a boolean indicating success.
        """
        try:
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            return await self.repository.clear(region_id)
        except Exception as e:
            logger.error(f"Error clearing cache region: {e}")
            region_desc = f"'{region_name}'" if region_name else "all regions"
            return Failure(f"Failed to clear cache for {region_desc}: {str(e)}")
    
    async def invalidate_by_pattern(self, pattern: str, region_name: Optional[str] = None) -> Result[int]:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: The pattern to match against cache keys.
            region_name: Optional region name.
            
        Returns:
            Result containing the number of keys invalidated.
        """
        try:
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            return await self.repository.invalidate_pattern(pattern, region_id)
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {e}")
            return Failure(f"Failed to invalidate cache pattern '{pattern}': {str(e)}")
    
    async def get_keys(self, region_name: Optional[str] = None) -> Result[List[str]]:
        """
        Get all cache keys.
        
        Args:
            region_name: Optional region name.
            
        Returns:
            Result containing a list of cache keys.
        """
        try:
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            keys_result = await self.repository.get_keys(region_id)
            if keys_result.is_success():
                return Success([key.value for key in keys_result.value])
            return keys_result
        except Exception as e:
            logger.error(f"Error getting cache keys: {e}")
            return Failure(f"Failed to get cache keys: {str(e)}")
    
    async def get_region_size(self, region_name: Optional[str] = None) -> Result[int]:
        """
        Get the number of cached items in a region.
        
        Args:
            region_name: Optional region name.
            
        Returns:
            Result containing the number of cached items.
        """
        try:
            region_id = None
            
            if region_name:
                region_result = await self.region_repository.get_by_name(region_name)
                if region_result.is_success():
                    region_id = region_result.value.id
                else:
                    return Failure(f"Region not found: {region_name}")
            
            return await self.repository.get_size(region_id)
        except Exception as e:
            logger.error(f"Error getting cache size: {e}")
            region_desc = f"'{region_name}'" if region_name else "all regions"
            return Failure(f"Failed to get cache size for {region_desc}: {str(e)}")
    
    async def check_key_matches_rule(self, key: str, rule: InvalidationRule) -> Result[bool]:
        """
        Check if a key matches an invalidation rule.
        
        Args:
            key: The cache key.
            rule: The invalidation rule.
            
        Returns:
            Result containing a boolean indicating if the key matches the rule.
        """
        try:
            return Success(rule.matches(key))
        except Exception as e:
            logger.error(f"Error checking key match: {e}")
            return Failure(f"Failed to check if key '{key}' matches rule '{rule.name}': {str(e)}")


class CacheMonitoringService(DomainService, CacheMonitoringServiceProtocol):
    """Service for monitoring cache operations."""
    
    def __init__(
        self, 
        statistic_repository: CacheStatisticRepositoryProtocol,
        provider_repository: CacheProviderRepositoryProtocol,
        region_repository: CacheRegionRepositoryProtocol
    ):
        self.statistic_repository = statistic_repository
        self.provider_repository = provider_repository
        self.region_repository = region_repository
        self.operations: List[CacheOperation] = []
        self.health_checks: List[CacheHealth] = []
    
    async def record_statistic(
        self, 
        provider_id: CacheProviderId,
        stat_type: CacheStatsType,
        value: Union[int, float],
        region: Optional[CacheRegionId] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[CacheStatistic]:
        """
        Record a cache statistic.
        
        Args:
            provider_id: The provider ID.
            stat_type: The statistic type.
            value: The statistic value.
            region: Optional region ID.
            metadata: Optional metadata.
            
        Returns:
            Result containing the recorded statistic.
        """
        try:
            # Verify provider exists
            provider_result = await self.provider_repository.get(provider_id)
            if not provider_result.is_success():
                return Failure(f"Provider not found: {provider_id.value}")
            
            if region:
                # Verify region exists
                region_result = await self.region_repository.get(region)
                if not region_result.is_success():
                    return Failure(f"Region not found: {region.value}")
            
            statistic = CacheStatistic(
                provider_id=provider_id,
                stat_type=stat_type,
                value=value,
                region=region,
                metadata=metadata or {},
            )
            
            return await self.statistic_repository.save(statistic)
        except Exception as e:
            logger.error(f"Error recording cache statistic: {e}")
            return Failure(f"Failed to record cache statistic: {str(e)}")
    
    async def record_operation(
        self, 
        key: CacheKeyId,
        provider_id: CacheProviderId,
        operation_type: str,
        duration_ms: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[CacheOperation]:
        """
        Record a cache operation.
        
        Args:
            key: The cache key ID.
            provider_id: The provider ID.
            operation_type: The operation type.
            duration_ms: The operation duration in milliseconds.
            success: Whether the operation was successful.
            error_message: Optional error message.
            metadata: Optional metadata.
            
        Returns:
            Result containing the recorded operation.
        """
        try:
            # Verify provider exists
            provider_result = await self.provider_repository.get(provider_id)
            if not provider_result.is_success():
                return Failure(f"Provider not found: {provider_id.value}")
            
            operation = CacheOperation(
                key=key,
                provider_id=provider_id,
                operation_type=operation_type,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )
            
            # In a real implementation, we would persist the operation
            # or emit it to a monitoring system.
            # For now, we'll just store it in memory.
            self.operations.append(operation)
            
            # Keep only the most recent operations in memory (e.g., 1000)
            max_operations = 1000
            if len(self.operations) > max_operations:
                self.operations = self.operations[-max_operations:]
            
            return Success(operation)
        except Exception as e:
            logger.error(f"Error recording cache operation: {e}")
            return Failure(f"Failed to record cache operation: {str(e)}")
    
    async def record_health_check(
        self, 
        provider_id: CacheProviderId,
        is_healthy: bool = True,
        latency_ms: float = 0.0,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Result[CacheHealth]:
        """
        Record a cache health check.
        
        Args:
            provider_id: The provider ID.
            is_healthy: Whether the provider is healthy.
            latency_ms: The latency in milliseconds.
            error_message: Optional error message.
            details: Optional details.
            
        Returns:
            Result containing the recorded health check.
        """
        try:
            # Verify provider exists
            provider_result = await self.provider_repository.get(provider_id)
            if not provider_result.is_success():
                return Failure(f"Provider not found: {provider_id.value}")
            
            health = CacheHealth(
                provider_id=provider_id,
                is_healthy=is_healthy,
                latency_ms=latency_ms,
                error_message=error_message,
                details=details or {},
            )
            
            # In a real implementation, we would persist the health check
            # or emit it to a monitoring system.
            # For now, we'll just store it in memory.
            self.health_checks.append(health)
            
            # Keep only the most recent health checks in memory (e.g., 1000)
            max_health_checks = 1000
            if len(self.health_checks) > max_health_checks:
                self.health_checks = self.health_checks[-max_health_checks:]
            
            return Success(health)
        except Exception as e:
            logger.error(f"Error recording cache health check: {e}")
            return Failure(f"Failed to record cache health check: {str(e)}")
    
    async def get_provider_statistics(
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
        return await self.statistic_repository.get_for_provider(
            provider_id, stat_type, start_time, end_time, limit
        )
    
    async def get_region_statistics(
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
        return await self.statistic_repository.get_for_region(
            region_id, stat_type, start_time, end_time, limit
        )
    
    async def get_provider_summary(
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
        return await self.statistic_repository.summarize_by_provider(
            provider_id, start_time, end_time
        )
    
    async def get_health_history(
        self, 
        provider_id: CacheProviderId,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Result[List[CacheHealth]]:
        """
        Get health check history for a provider.
        
        Args:
            provider_id: The provider ID.
            start_time: Optional filter by start time.
            end_time: Optional filter by end time.
            limit: Maximum number of health checks to return.
            
        Returns:
            Result containing a list of health checks.
        """
        # In a real implementation, we would retrieve this from a persistent store.
        # For now, we'll just filter the in-memory list.
        
        filtered_checks = self.health_checks
        
        if provider_id:
            filtered_checks = [check for check in filtered_checks 
                              if check.provider_id.value == provider_id.value]
        
        if start_time:
            filtered_checks = [check for check in filtered_checks 
                              if check.timestamp >= start_time]
        
        if end_time:
            filtered_checks = [check for check in filtered_checks 
                              if check.timestamp <= end_time]
        
        # Sort by timestamp, most recent first
        filtered_checks.sort(key=lambda check: check.timestamp, reverse=True)
        
        # Apply limit
        filtered_checks = filtered_checks[:limit]
        
        return Success(filtered_checks)


class CacheConfigurationService(DomainService, CacheConfigurationServiceProtocol):
    """Service for managing cache configuration."""
    
    def __init__(self, repository: CacheConfigurationRepositoryProtocol):
        self.repository = repository
    
    async def get_active_configuration(self) -> Result[CacheConfiguration]:
        """
        Get the active cache configuration.
        
        Returns:
            Result containing the active configuration.
        """
        return await self.repository.get()
    
    async def save_configuration(self, configuration: CacheConfiguration) -> Result[CacheConfiguration]:
        """
        Save a cache configuration.
        
        Args:
            configuration: The configuration to save.
            
        Returns:
            Result containing the saved configuration.
        """
        return await self.repository.save(configuration)
    
    async def update_configuration(
        self, 
        enabled: Optional[bool] = None,
        key_prefix: Optional[str] = None,
        use_hash_keys: Optional[bool] = None,
        hash_algorithm: Optional[str] = None,
        use_multi_level: Optional[bool] = None,
        fallback_on_error: Optional[bool] = None,
        local_config: Optional[Dict[str, Any]] = None,
        distributed_config: Optional[Dict[str, Any]] = None,
        invalidation_config: Optional[Dict[str, Any]] = None,
        monitoring_config: Optional[Dict[str, Any]] = None,
        regions: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Result[CacheConfiguration]:
        """
        Update the active cache configuration.
        
        Args:
            enabled: Optional enabled flag.
            key_prefix: Optional key prefix.
            use_hash_keys: Optional use hash keys flag.
            hash_algorithm: Optional hash algorithm.
            use_multi_level: Optional use multi-level flag.
            fallback_on_error: Optional fallback on error flag.
            local_config: Optional local cache configuration.
            distributed_config: Optional distributed cache configuration.
            invalidation_config: Optional invalidation configuration.
            monitoring_config: Optional monitoring configuration.
            regions: Optional regions configuration.
            
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                # Create a new configuration if none exists
                config = CacheConfiguration()
            else:
                config = config_result.value
            
            if enabled is not None:
                config.enabled = enabled
            
            if key_prefix is not None:
                config.key_prefix = key_prefix
            
            if use_hash_keys is not None:
                config.use_hash_keys = use_hash_keys
            
            if hash_algorithm is not None:
                config.hash_algorithm = hash_algorithm
            
            if use_multi_level is not None:
                config.use_multi_level = use_multi_level
            
            if fallback_on_error is not None:
                config.fallback_on_error = fallback_on_error
            
            if local_config is not None:
                config.local_config.update(local_config)
            
            if distributed_config is not None:
                config.distributed_config.update(distributed_config)
            
            if invalidation_config is not None:
                config.invalidation_config.update(invalidation_config)
            
            if monitoring_config is not None:
                config.monitoring_config.update(monitoring_config)
            
            if regions is not None:
                config.regions.update(regions)
            
            return await self.repository.save(config)
        except Exception as e:
            logger.error(f"Error updating cache configuration: {e}")
            return Failure(f"Failed to update cache configuration: {str(e)}")
    
    async def add_region_config(self, name: str, config: Dict[str, Any]) -> Result[CacheConfiguration]:
        """
        Add a region configuration.
        
        Args:
            name: The region name.
            config: The region configuration.
            
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                # Create a new configuration if none exists
                configuration = CacheConfiguration()
            else:
                configuration = config_result.value
            
            configuration.add_region(name, config)
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error adding region configuration: {e}")
            return Failure(f"Failed to add region configuration for '{name}': {str(e)}")
    
    async def remove_region_config(self, name: str) -> Result[CacheConfiguration]:
        """
        Remove a region configuration.
        
        Args:
            name: The region name.
            
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                return Failure("No active configuration found")
            
            configuration = config_result.value
            removed = configuration.remove_region(name)
            
            if not removed:
                return Failure(f"Region '{name}' not found in configuration")
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error removing region configuration: {e}")
            return Failure(f"Failed to remove region configuration for '{name}': {str(e)}")
    
    async def enable_caching(self) -> Result[CacheConfiguration]:
        """
        Enable caching.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                # Create a new configuration if none exists
                configuration = CacheConfiguration()
            else:
                configuration = config_result.value
            
            configuration.enable()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error enabling caching: {e}")
            return Failure(f"Failed to enable caching: {str(e)}")
    
    async def disable_caching(self) -> Result[CacheConfiguration]:
        """
        Disable caching.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                return Failure("No active configuration found")
            
            configuration = config_result.value
            configuration.disable()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error disabling caching: {e}")
            return Failure(f"Failed to disable caching: {str(e)}")
    
    async def enable_multi_level(self) -> Result[CacheConfiguration]:
        """
        Enable multi-level caching.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                # Create a new configuration if none exists
                configuration = CacheConfiguration()
            else:
                configuration = config_result.value
            
            configuration.enable_multi_level()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error enabling multi-level caching: {e}")
            return Failure(f"Failed to enable multi-level caching: {str(e)}")
    
    async def disable_multi_level(self) -> Result[CacheConfiguration]:
        """
        Disable multi-level caching.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                return Failure("No active configuration found")
            
            configuration = config_result.value
            configuration.disable_multi_level()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error disabling multi-level caching: {e}")
            return Failure(f"Failed to disable multi-level caching: {str(e)}")
    
    async def enable_distributed(self) -> Result[CacheConfiguration]:
        """
        Enable distributed caching.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                # Create a new configuration if none exists
                configuration = CacheConfiguration()
            else:
                configuration = config_result.value
            
            configuration.enable_distributed()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error enabling distributed caching: {e}")
            return Failure(f"Failed to enable distributed caching: {str(e)}")
    
    async def disable_distributed(self) -> Result[CacheConfiguration]:
        """
        Disable distributed caching.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                return Failure("No active configuration found")
            
            configuration = config_result.value
            configuration.disable_distributed()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error disabling distributed caching: {e}")
            return Failure(f"Failed to disable distributed caching: {str(e)}")
    
    async def enable_monitoring(self) -> Result[CacheConfiguration]:
        """
        Enable cache monitoring.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                # Create a new configuration if none exists
                configuration = CacheConfiguration()
            else:
                configuration = config_result.value
            
            configuration.enable_monitoring()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error enabling cache monitoring: {e}")
            return Failure(f"Failed to enable cache monitoring: {str(e)}")
    
    async def disable_monitoring(self) -> Result[CacheConfiguration]:
        """
        Disable cache monitoring.
        
        Returns:
            Result containing the updated configuration.
        """
        try:
            config_result = await self.repository.get()
            if not config_result.is_success():
                return Failure("No active configuration found")
            
            configuration = config_result.value
            configuration.disable_monitoring()
            
            return await self.repository.save(configuration)
        except Exception as e:
            logger.error(f"Error disabling cache monitoring: {e}")
            return Failure(f"Failed to disable cache monitoring: {str(e)}")