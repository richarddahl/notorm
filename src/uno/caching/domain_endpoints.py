"""
Domain endpoints for the Caching module.

This module provides API endpoints for the Caching module using FastAPI.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field, validator

from uno.core.result import Failure
from uno.dependencies.fastapi_integration import inject_dependency

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
    CacheHealth,
    CacheConfiguration
)
from uno.caching.domain_services import (
    CacheProviderServiceProtocol,
    CacheRegionServiceProtocol,
    InvalidationRuleServiceProtocol,
    CacheItemServiceProtocol,
    CacheMonitoringServiceProtocol,
    CacheConfigurationServiceProtocol
)


# Schema models for API request/response
class ProviderTypeEnum(str, Enum):
    """Enum for provider types in API."""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"
    MEMCACHED = "memcached"
    CUSTOM = "custom"


class InvalidationStrategyEnum(str, Enum):
    """Enum for invalidation strategies in API."""
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    PATTERN_BASED = "pattern_based"
    COMPOSITE = "composite"


class StatsTypeEnum(str, Enum):
    """Enum for statistics types in API."""
    HIT = "hit"
    MISS = "miss"
    ERROR = "error"
    LATENCY = "latency"


class CacheLevelEnum(str, Enum):
    """Enum for cache levels in API."""
    LOCAL = "local"
    DISTRIBUTED = "distributed"


class ProviderCreateRequest(BaseModel):
    """Request model for creating a provider."""
    name: str
    provider_type: ProviderTypeEnum
    connection_details: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class ProviderUpdateRequest(BaseModel):
    """Request model for updating a provider."""
    name: Optional[str] = None
    provider_type: Optional[ProviderTypeEnum] = None
    connection_details: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProviderResponse(BaseModel):
    """Response model for a provider."""
    id: str
    name: str
    provider_type: ProviderTypeEnum
    is_active: bool
    created_at: datetime
    connection_details: Dict[str, Any]
    configuration: Dict[str, Any]

    class Config:
        """Pydantic config."""
        from_attributes = True


class RegionCreateRequest(BaseModel):
    """Request model for creating a region."""
    name: str
    provider_id: str
    ttl: int = 300
    max_size: Optional[int] = None
    invalidation_strategy: Optional[InvalidationStrategyEnum] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class RegionUpdateRequest(BaseModel):
    """Request model for updating a region."""
    name: Optional[str] = None
    provider_id: Optional[str] = None
    ttl: Optional[int] = None
    max_size: Optional[int] = None
    invalidation_strategy: Optional[InvalidationStrategyEnum] = None
    configuration: Optional[Dict[str, Any]] = None


class RegionResponse(BaseModel):
    """Response model for a region."""
    id: str
    name: str
    ttl: int
    provider_id: str
    max_size: Optional[int]
    invalidation_strategy: Optional[InvalidationStrategyEnum]
    created_at: datetime
    configuration: Dict[str, Any]

    class Config:
        """Pydantic config."""
        from_attributes = True


class RuleCreateRequest(BaseModel):
    """Request model for creating a rule."""
    name: str
    strategy_type: InvalidationStrategyEnum
    pattern: Optional[str] = None
    ttl: Optional[int] = None
    events: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class RuleUpdateRequest(BaseModel):
    """Request model for updating a rule."""
    name: Optional[str] = None
    strategy_type: Optional[InvalidationStrategyEnum] = None
    pattern: Optional[str] = None
    ttl: Optional[int] = None
    events: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RuleResponse(BaseModel):
    """Response model for a rule."""
    id: str
    name: str
    strategy_type: InvalidationStrategyEnum
    pattern: Optional[str]
    ttl: Optional[int]
    events: List[str]
    created_at: datetime
    is_active: bool
    configuration: Dict[str, Any]

    class Config:
        """Pydantic config."""
        from_attributes = True


class CacheItemRequest(BaseModel):
    """Request model for setting a cache item."""
    value: Any
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CacheItemResponse(BaseModel):
    """Response model for a cache item."""
    key: str
    value: Any
    expiry: Optional[datetime]
    created_at: datetime
    last_accessed: datetime
    region: Optional[str]
    metadata: Dict[str, Any]

    class Config:
        """Pydantic config."""
        from_attributes = True


class StatisticResponse(BaseModel):
    """Response model for a statistic."""
    id: str
    provider_id: str
    stat_type: StatsTypeEnum
    timestamp: datetime
    value: Union[int, float]
    region: Optional[str]
    metadata: Dict[str, Any]

    class Config:
        """Pydantic config."""
        from_attributes = True


class HealthResponse(BaseModel):
    """Response model for a health check."""
    id: str
    provider_id: str
    timestamp: datetime
    is_healthy: bool
    latency_ms: float
    error_message: Optional[str]
    details: Dict[str, Any]

    class Config:
        """Pydantic config."""
        from_attributes = True


class ConfigurationSummaryResponse(BaseModel):
    """Response model for a configuration summary."""
    id: str
    enabled: bool
    use_multi_level: bool
    fallback_on_error: bool
    local_config: Dict[str, Any]
    distributed_config: Dict[str, Any]
    invalidation_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]
    regions_count: int

    class Config:
        """Pydantic config."""
        from_attributes = True


class ConfigurationResponse(BaseModel):
    """Response model for a configuration."""
    id: str
    enabled: bool
    key_prefix: str
    use_hash_keys: bool
    hash_algorithm: str
    use_multi_level: bool
    fallback_on_error: bool
    local_config: Dict[str, Any]
    distributed_config: Dict[str, Any]
    invalidation_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]
    regions: Dict[str, Dict[str, Any]]

    class Config:
        """Pydantic config."""
        from_attributes = True


class ConfigurationUpdateRequest(BaseModel):
    """Request model for updating a configuration."""
    enabled: Optional[bool] = None
    key_prefix: Optional[str] = None
    use_hash_keys: Optional[bool] = None
    hash_algorithm: Optional[str] = None
    use_multi_level: Optional[bool] = None
    fallback_on_error: Optional[bool] = None
    local_config: Optional[Dict[str, Any]] = None
    distributed_config: Optional[Dict[str, Any]] = None
    invalidation_config: Optional[Dict[str, Any]] = None
    monitoring_config: Optional[Dict[str, Any]] = None


class RegionConfigRequest(BaseModel):
    """Request model for a region configuration."""
    config: Dict[str, Any]


class StatsSummaryResponse(BaseModel):
    """Response model for a statistics summary."""
    hits: int = 0
    misses: int = 0
    hit_ratio: float = 0.0
    average_latency_ms: float = 0.0
    error_count: int = 0
    total_operations: int = 0


# Create API router
router = APIRouter(prefix="/api/cache", tags=["cache"])


def create_entity_response(entity, response_class):
    """Helper to convert domain entities to response models."""
    # Handle CacheProviders
    if hasattr(entity, 'provider_type') and isinstance(entity.provider_type, CacheProviderType):
        entity_dict = entity.__dict__.copy()
        entity_dict['provider_type'] = ProviderTypeEnum(entity.provider_type.value)
        return response_class(**entity_dict)
    
    # Handle CacheRegions
    if hasattr(entity, 'invalidation_strategy') and entity.invalidation_strategy is not None and isinstance(entity.invalidation_strategy, InvalidationStrategyType):
        entity_dict = entity.__dict__.copy()
        entity_dict['invalidation_strategy'] = InvalidationStrategyEnum(entity.invalidation_strategy.value)
        return response_class(**entity_dict)
    
    # Handle InvalidationRules
    if hasattr(entity, 'strategy_type') and isinstance(entity.strategy_type, InvalidationStrategyType):
        entity_dict = entity.__dict__.copy()
        entity_dict['strategy_type'] = InvalidationStrategyEnum(entity.strategy_type.value)
        return response_class(**entity_dict)
    
    # Handle CacheStatistics
    if hasattr(entity, 'stat_type') and isinstance(entity.stat_type, CacheStatsType):
        entity_dict = entity.__dict__.copy()
        entity_dict['stat_type'] = StatsTypeEnum(entity.stat_type.value)
        return response_class(**entity_dict)
    
    # Handle ValueObjects (IDs)
    entity_dict = entity.__dict__.copy()
    for key, value in entity_dict.items():
        if hasattr(value, 'value') and any(isinstance(value, id_class) for id_class in [CacheKeyId, CacheRegionId, CacheProviderId, InvalidationRuleId]):
            entity_dict[key] = value.value
    
    # For CacheItems
    if isinstance(entity, CacheItem):
        entity_dict = entity.__dict__.copy()
        entity_dict['key'] = entity.key.value
        if entity.region:
            entity_dict['region'] = entity.region.value
        else:
            entity_dict['region'] = None
        return response_class(**entity_dict)
    
    return response_class(**entity_dict)


# Provider endpoints
@router.post("/providers", response_model=ProviderResponse, status_code=201)
async def create_provider(
    request: ProviderCreateRequest,
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Create a new cache provider."""
    result = await provider_service.register_provider(
        name=request.name,
        provider_type=CacheProviderType(request.provider_type.value),
        connection_details=request.connection_details,
        configuration=request.configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create provider")
    
    return create_entity_response(result.value, ProviderResponse)


@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """List all cache providers."""
    result = await provider_service.list_providers()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list providers")
    
    return [create_entity_response(provider, ProviderResponse) for provider in result.value]


@router.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str = Path(..., description="The provider ID"),
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Get a cache provider by ID."""
    result = await provider_service.get_provider(CacheProviderId(provider_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get provider")
    
    return create_entity_response(result.value, ProviderResponse)


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    request: ProviderUpdateRequest,
    provider_id: str = Path(..., description="The provider ID"),
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Update a cache provider."""
    provider_type = None
    if request.provider_type:
        provider_type = CacheProviderType(request.provider_type.value)
    
    result = await provider_service.update_provider(
        provider_id=CacheProviderId(provider_id),
        name=request.name,
        provider_type=provider_type,
        connection_details=request.connection_details,
        configuration=request.configuration,
        is_active=request.is_active
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update provider")
    
    return create_entity_response(result.value, ProviderResponse)


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str = Path(..., description="The provider ID"),
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Delete a cache provider."""
    result = await provider_service.delete_provider(CacheProviderId(provider_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete provider")


@router.post("/providers/{provider_id}/activate", response_model=ProviderResponse)
async def activate_provider(
    provider_id: str = Path(..., description="The provider ID"),
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Activate a cache provider."""
    result = await provider_service.activate_provider(CacheProviderId(provider_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to activate provider")
    
    return create_entity_response(result.value, ProviderResponse)


@router.post("/providers/{provider_id}/deactivate", response_model=ProviderResponse)
async def deactivate_provider(
    provider_id: str = Path(..., description="The provider ID"),
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Deactivate a cache provider."""
    result = await provider_service.deactivate_provider(CacheProviderId(provider_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to deactivate provider")
    
    return create_entity_response(result.value, ProviderResponse)


@router.get("/providers/{provider_id}/health", response_model=HealthResponse)
async def check_provider_health(
    provider_id: str = Path(..., description="The provider ID"),
    provider_service: CacheProviderServiceProtocol = Depends(inject_dependency(CacheProviderServiceProtocol))
):
    """Check the health of a cache provider."""
    result = await provider_service.check_provider_health(CacheProviderId(provider_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to check provider health")
    
    health = result.value
    return HealthResponse(
        id=health.id,
        provider_id=health.provider_id.value,
        timestamp=health.timestamp,
        is_healthy=health.is_healthy,
        latency_ms=health.latency_ms,
        error_message=health.error_message,
        details=health.details
    )


# Region endpoints
@router.post("/regions", response_model=RegionResponse, status_code=201)
async def create_region(
    request: RegionCreateRequest,
    region_service: CacheRegionServiceProtocol = Depends(inject_dependency(CacheRegionServiceProtocol))
):
    """Create a new cache region."""
    invalidation_strategy = None
    if request.invalidation_strategy:
        invalidation_strategy = InvalidationStrategyType(request.invalidation_strategy.value)
    
    result = await region_service.create_region(
        name=request.name,
        provider_id=CacheProviderId(request.provider_id),
        ttl=request.ttl,
        max_size=request.max_size,
        invalidation_strategy=invalidation_strategy,
        configuration=request.configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create region")
    
    return create_entity_response(result.value, RegionResponse)


@router.get("/regions", response_model=List[RegionResponse])
async def list_regions(
    provider_id: Optional[str] = Query(None, description="Filter by provider ID"),
    region_service: CacheRegionServiceProtocol = Depends(inject_dependency(CacheRegionServiceProtocol))
):
    """List all cache regions."""
    if provider_id:
        result = await region_service.list_regions_by_provider(CacheProviderId(provider_id))
    else:
        result = await region_service.list_regions()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list regions")
    
    return [create_entity_response(region, RegionResponse) for region in result.value]


@router.get("/regions/{region_id}", response_model=RegionResponse)
async def get_region(
    region_id: str = Path(..., description="The region ID"),
    region_service: CacheRegionServiceProtocol = Depends(inject_dependency(CacheRegionServiceProtocol))
):
    """Get a cache region by ID."""
    result = await region_service.get_region(CacheRegionId(region_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get region")
    
    return create_entity_response(result.value, RegionResponse)


@router.get("/regions/by-name/{name}", response_model=RegionResponse)
async def get_region_by_name(
    name: str = Path(..., description="The region name"),
    region_service: CacheRegionServiceProtocol = Depends(inject_dependency(CacheRegionServiceProtocol))
):
    """Get a cache region by name."""
    result = await region_service.get_region_by_name(name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get region")
    
    return create_entity_response(result.value, RegionResponse)


@router.put("/regions/{region_id}", response_model=RegionResponse)
async def update_region(
    request: RegionUpdateRequest,
    region_id: str = Path(..., description="The region ID"),
    region_service: CacheRegionServiceProtocol = Depends(inject_dependency(CacheRegionServiceProtocol))
):
    """Update a cache region."""
    provider_id = None
    if request.provider_id:
        provider_id = CacheProviderId(request.provider_id)
    
    invalidation_strategy = None
    if request.invalidation_strategy:
        invalidation_strategy = InvalidationStrategyType(request.invalidation_strategy.value)
    
    result = await region_service.update_region(
        region_id=CacheRegionId(region_id),
        name=request.name,
        provider_id=provider_id,
        ttl=request.ttl,
        max_size=request.max_size,
        invalidation_strategy=invalidation_strategy,
        configuration=request.configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update region")
    
    return create_entity_response(result.value, RegionResponse)


@router.delete("/regions/{region_id}", status_code=204)
async def delete_region(
    region_id: str = Path(..., description="The region ID"),
    region_service: CacheRegionServiceProtocol = Depends(inject_dependency(CacheRegionServiceProtocol))
):
    """Delete a cache region."""
    result = await region_service.delete_region(CacheRegionId(region_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete region")


# Rule endpoints
@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(
    request: RuleCreateRequest,
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Create a new invalidation rule."""
    result = await rule_service.create_rule(
        name=request.name,
        strategy_type=InvalidationStrategyType(request.strategy_type.value),
        pattern=request.pattern,
        ttl=request.ttl,
        events=request.events,
        configuration=request.configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create rule")
    
    return create_entity_response(result.value, RuleResponse)


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    strategy_type: Optional[InvalidationStrategyEnum] = Query(None, description="Filter by strategy type"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """List all invalidation rules."""
    if strategy_type:
        result = await rule_service.list_rules_by_strategy(InvalidationStrategyType(strategy_type.value))
    else:
        result = await rule_service.list_rules()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list rules")
    
    return [create_entity_response(rule, RuleResponse) for rule in result.value]


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str = Path(..., description="The rule ID"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Get an invalidation rule by ID."""
    result = await rule_service.get_rule(InvalidationRuleId(rule_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get rule")
    
    return create_entity_response(result.value, RuleResponse)


@router.get("/rules/by-name/{name}", response_model=RuleResponse)
async def get_rule_by_name(
    name: str = Path(..., description="The rule name"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Get an invalidation rule by name."""
    result = await rule_service.get_rule_by_name(name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get rule")
    
    return create_entity_response(result.value, RuleResponse)


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    request: RuleUpdateRequest,
    rule_id: str = Path(..., description="The rule ID"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Update an invalidation rule."""
    strategy_type = None
    if request.strategy_type:
        strategy_type = InvalidationStrategyType(request.strategy_type.value)
    
    result = await rule_service.update_rule(
        rule_id=InvalidationRuleId(rule_id),
        name=request.name,
        strategy_type=strategy_type,
        pattern=request.pattern,
        ttl=request.ttl,
        events=request.events,
        configuration=request.configuration,
        is_active=request.is_active
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update rule")
    
    return create_entity_response(result.value, RuleResponse)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str = Path(..., description="The rule ID"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Delete an invalidation rule."""
    result = await rule_service.delete_rule(InvalidationRuleId(rule_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete rule")


@router.post("/rules/{rule_id}/activate", response_model=RuleResponse)
async def activate_rule(
    rule_id: str = Path(..., description="The rule ID"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Activate an invalidation rule."""
    result = await rule_service.activate_rule(InvalidationRuleId(rule_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to activate rule")
    
    return create_entity_response(result.value, RuleResponse)


@router.post("/rules/{rule_id}/deactivate", response_model=RuleResponse)
async def deactivate_rule(
    rule_id: str = Path(..., description="The rule ID"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Deactivate an invalidation rule."""
    result = await rule_service.deactivate_rule(InvalidationRuleId(rule_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to deactivate rule")
    
    return create_entity_response(result.value, RuleResponse)


@router.get("/rules/match/{key}", response_model=List[RuleResponse])
async def find_matching_rules(
    key: str = Path(..., description="The cache key to match"),
    rule_service: InvalidationRuleServiceProtocol = Depends(inject_dependency(InvalidationRuleServiceProtocol))
):
    """Find all rules that match a given key."""
    result = await rule_service.find_matching_rules(key)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to find matching rules")
    
    return [create_entity_response(rule, RuleResponse) for rule in result.value]


# Cache item endpoints
@router.get("/items/{key}", response_model=CacheItemResponse)
async def get_cache_item(
    key: str = Path(..., description="The cache key"),
    region: Optional[str] = Query(None, description="Optional region name"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Get a cached item by key."""
    result = await cache_service.get_item(key, region)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get cache item")
    
    if result.value is None:
        raise HTTPException(status_code=404, detail="Cache item not found")
    
    return create_entity_response(result.value, CacheItemResponse)


@router.put("/items/{key}", response_model=CacheItemResponse)
async def set_cache_item(
    request: CacheItemRequest,
    key: str = Path(..., description="The cache key"),
    region: Optional[str] = Query(None, description="Optional region name"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Set a cached item."""
    expiry = None
    if request.ttl_seconds is not None:
        from datetime import datetime, timedelta, UTC
        expiry = datetime.now(UTC) + timedelta(seconds=request.ttl_seconds)
    
    result = await cache_service.set_item(
        key=key,
        value=request.value,
        expiry=expiry,
        region_name=region,
        metadata=request.metadata
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to set cache item")
    
    return create_entity_response(result.value, CacheItemResponse)


@router.delete("/items/{key}", status_code=204)
async def delete_cache_item(
    key: str = Path(..., description="The cache key"),
    region: Optional[str] = Query(None, description="Optional region name"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Delete a cached item by key."""
    result = await cache_service.delete_item(key, region)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete cache item")


@router.delete("/items", status_code=204)
async def clear_cache_region(
    region: Optional[str] = Query(None, description="Optional region name to clear"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Clear all cached items in a region."""
    result = await cache_service.clear_region(region)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.delete("/items/pattern/{pattern}", response_model=Dict[str, int])
async def invalidate_by_pattern(
    pattern: str = Path(..., description="The pattern to match against cache keys"),
    region: Optional[str] = Query(None, description="Optional region name"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Invalidate all keys matching a pattern."""
    result = await cache_service.invalidate_by_pattern(pattern, region)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to invalidate cache pattern")
    
    return {"invalidated_count": result.value}


@router.get("/items", response_model=List[str])
async def get_cache_keys(
    region: Optional[str] = Query(None, description="Optional region name"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Get all cache keys."""
    result = await cache_service.get_keys(region)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get cache keys")
    
    return result.value


@router.get("/size", response_model=Dict[str, int])
async def get_cache_size(
    region: Optional[str] = Query(None, description="Optional region name"),
    cache_service: CacheItemServiceProtocol = Depends(inject_dependency(CacheItemServiceProtocol))
):
    """Get the number of cached items."""
    result = await cache_service.get_region_size(region)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get cache size")
    
    return {"size": result.value}


# Configuration endpoints
@router.get("/configuration", response_model=ConfigurationResponse)
async def get_configuration(
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Get the active cache configuration."""
    result = await config_service.get_active_configuration()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    return ConfigurationResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        key_prefix=result.value.key_prefix,
        use_hash_keys=result.value.use_hash_keys,
        hash_algorithm=result.value.hash_algorithm,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions=result.value.regions
    )


@router.get("/configuration/summary", response_model=ConfigurationSummaryResponse)
async def get_configuration_summary(
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Get a summary of the active cache configuration."""
    result = await config_service.get_active_configuration()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    return ConfigurationSummaryResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions_count=len(result.value.regions)
    )


@router.put("/configuration", response_model=ConfigurationResponse)
async def update_configuration(
    request: ConfigurationUpdateRequest,
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Update the active cache configuration."""
    result = await config_service.update_configuration(
        enabled=request.enabled,
        key_prefix=request.key_prefix,
        use_hash_keys=request.use_hash_keys,
        hash_algorithm=request.hash_algorithm,
        use_multi_level=request.use_multi_level,
        fallback_on_error=request.fallback_on_error,
        local_config=request.local_config,
        distributed_config=request.distributed_config,
        invalidation_config=request.invalidation_config,
        monitoring_config=request.monitoring_config
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update configuration")
    
    return ConfigurationResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        key_prefix=result.value.key_prefix,
        use_hash_keys=result.value.use_hash_keys,
        hash_algorithm=result.value.hash_algorithm,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions=result.value.regions
    )


@router.post("/configuration/enable", response_model=ConfigurationResponse)
async def enable_caching(
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Enable caching."""
    result = await config_service.enable_caching()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to enable caching")
    
    return ConfigurationResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        key_prefix=result.value.key_prefix,
        use_hash_keys=result.value.use_hash_keys,
        hash_algorithm=result.value.hash_algorithm,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions=result.value.regions
    )


@router.post("/configuration/disable", response_model=ConfigurationResponse)
async def disable_caching(
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Disable caching."""
    result = await config_service.disable_caching()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to disable caching")
    
    return ConfigurationResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        key_prefix=result.value.key_prefix,
        use_hash_keys=result.value.use_hash_keys,
        hash_algorithm=result.value.hash_algorithm,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions=result.value.regions
    )


@router.post("/configuration/regions/{region_name}", response_model=ConfigurationResponse)
async def add_region_config(
    request: RegionConfigRequest,
    region_name: str = Path(..., description="The region name"),
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Add a region configuration."""
    result = await config_service.add_region_config(region_name, request.config)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to add region configuration")
    
    return ConfigurationResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        key_prefix=result.value.key_prefix,
        use_hash_keys=result.value.use_hash_keys,
        hash_algorithm=result.value.hash_algorithm,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions=result.value.regions
    )


@router.delete("/configuration/regions/{region_name}", response_model=ConfigurationResponse)
async def remove_region_config(
    region_name: str = Path(..., description="The region name"),
    config_service: CacheConfigurationServiceProtocol = Depends(inject_dependency(CacheConfigurationServiceProtocol))
):
    """Remove a region configuration."""
    result = await config_service.remove_region_config(region_name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to remove region configuration")
    
    return ConfigurationResponse(
        id=result.value.id,
        enabled=result.value.enabled,
        key_prefix=result.value.key_prefix,
        use_hash_keys=result.value.use_hash_keys,
        hash_algorithm=result.value.hash_algorithm,
        use_multi_level=result.value.use_multi_level,
        fallback_on_error=result.value.fallback_on_error,
        local_config=result.value.local_config,
        distributed_config=result.value.distributed_config,
        invalidation_config=result.value.invalidation_config,
        monitoring_config=result.value.monitoring_config,
        regions=result.value.regions
    )