"""
Tests for the Caching module domain entities, repositories, and services.

This module contains comprehensive tests for all domain components of the Caching module,
focusing on value objects, entities, repositories, and domain services related to
cache management, invalidation, and configuration.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional

from uno.core.result import Result, Success, Failure
from uno.domain.core import ValueObject, Entity

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
    CacheProviderService,
    CacheRegionService,
    InvalidationRuleService,
    CacheItemService,
    CacheMonitoringService,
    CacheConfigurationService
)


# Test constants
TEST_PROVIDER_ID = "test-provider-id"
TEST_REGION_ID = "test-region"
TEST_RULE_ID = "test-rule-id"
TEST_KEY = "test-key"


# Value Object Tests
class TestValueObjects:
    """Tests for value objects in the Caching domain."""

    def test_cache_key_id(self):
        """Test CacheKeyId value object."""
        key = "test-key"
        cache_key_id = CacheKeyId(key)
        
        assert cache_key_id.value == key
        assert isinstance(cache_key_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            cache_key_id.value = "new-key"
            
        # Test equality
        same_id = CacheKeyId(key)
        different_id = CacheKeyId("different-key")
        
        assert cache_key_id == same_id
        assert cache_key_id != different_id
        assert hash(cache_key_id) == hash(same_id)

    def test_cache_region_id(self):
        """Test CacheRegionId value object."""
        region = "test-region"
        region_id = CacheRegionId(region)
        
        assert region_id.value == region
        assert isinstance(region_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            region_id.value = "new-region"
            
        # Test equality
        same_id = CacheRegionId(region)
        different_id = CacheRegionId("different-region")
        
        assert region_id == same_id
        assert region_id != different_id
        assert hash(region_id) == hash(same_id)

    def test_cache_provider_id(self):
        """Test CacheProviderId value object."""
        provider_id_str = str(uuid.uuid4())
        provider_id = CacheProviderId(provider_id_str)
        
        assert provider_id.value == provider_id_str
        assert isinstance(provider_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            provider_id.value = "new-id"
            
        # Test equality
        same_id = CacheProviderId(provider_id_str)
        different_id = CacheProviderId(str(uuid.uuid4()))
        
        assert provider_id == same_id
        assert provider_id != different_id
        assert hash(provider_id) == hash(same_id)

    def test_invalidation_rule_id(self):
        """Test InvalidationRuleId value object."""
        rule_id_str = str(uuid.uuid4())
        rule_id = InvalidationRuleId(rule_id_str)
        
        assert rule_id.value == rule_id_str
        assert isinstance(rule_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            rule_id.value = "new-id"
            
        # Test equality
        same_id = InvalidationRuleId(rule_id_str)
        different_id = InvalidationRuleId(str(uuid.uuid4()))
        
        assert rule_id == same_id
        assert rule_id != different_id
        assert hash(rule_id) == hash(same_id)


# Entity Tests
class TestCacheItemEntity:
    """Tests for the CacheItem entity."""
    
    def test_create_cache_item(self):
        """Test creating a cache item entity."""
        key_id = CacheKeyId("test-key")
        region_id = CacheRegionId("test-region")
        now = datetime.now(UTC)
        expiry = now + timedelta(seconds=300)
        
        item = CacheItem(
            key=key_id,
            value="test-value",
            expiry=expiry,
            region=region_id,
            metadata={"source": "test"}
        )
        
        assert item.key == key_id
        assert item.value == "test-value"
        assert item.expiry == expiry
        assert item.region == region_id
        assert item.metadata == {"source": "test"}
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.last_accessed, datetime)
        
    def test_is_expired(self):
        """Test the is_expired method."""
        key_id = CacheKeyId("test-key")
        
        # Not expired
        future_expiry = datetime.now(UTC) + timedelta(seconds=300)
        item1 = CacheItem(
            key=key_id,
            value="test-value",
            expiry=future_expiry
        )
        assert not item1.is_expired()
        
        # Expired
        past_expiry = datetime.now(UTC) - timedelta(seconds=300)
        item2 = CacheItem(
            key=key_id,
            value="test-value",
            expiry=past_expiry
        )
        assert item2.is_expired()
        
        # No expiry
        item3 = CacheItem(
            key=key_id,
            value="test-value",
            expiry=None
        )
        assert not item3.is_expired()
    
    def test_access(self):
        """Test the access method."""
        key_id = CacheKeyId("test-key")
        item = CacheItem(
            key=key_id,
            value="test-value"
        )
        
        original_accessed = item.last_accessed
        
        # Ensure some time passes
        import time
        time.sleep(0.01)
        
        item.access()
        
        assert item.last_accessed > original_accessed


class TestCacheProviderEntity:
    """Tests for the CacheProvider entity."""
    
    def test_create_cache_provider(self):
        """Test creating a cache provider entity."""
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        
        provider = CacheProvider(
            id=provider_id,
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            connection_details={"host": "localhost"},
            configuration={"max_size": 1000}
        )
        
        assert provider.id == provider_id
        assert provider.name == "test-provider"
        assert provider.provider_type == CacheProviderType.MEMORY
        assert provider.connection_details == {"host": "localhost"}
        assert provider.configuration == {"max_size": 1000}
        assert provider.is_active is True
        assert isinstance(provider.created_at, datetime)
    
    def test_activate_deactivate(self):
        """Test the activate and deactivate methods."""
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        provider = CacheProvider(
            id=provider_id,
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            is_active=False
        )
        
        assert provider.is_active is False
        
        provider.activate()
        assert provider.is_active is True
        
        provider.deactivate()
        assert provider.is_active is False


class TestCacheRegionEntity:
    """Tests for the CacheRegion entity."""
    
    def test_create_cache_region(self):
        """Test creating a cache region entity."""
        region_id = CacheRegionId(TEST_REGION_ID)
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        
        region = CacheRegion(
            id=region_id,
            name="test-region",
            ttl=300,
            provider_id=provider_id,
            max_size=1000,
            invalidation_strategy=InvalidationStrategyType.TIME_BASED,
            configuration={"eviction_policy": "LRU"}
        )
        
        assert region.id == region_id
        assert region.name == "test-region"
        assert region.ttl == 300
        assert region.provider_id == provider_id
        assert region.max_size == 1000
        assert region.invalidation_strategy == InvalidationStrategyType.TIME_BASED
        assert region.configuration == {"eviction_policy": "LRU"}
        assert isinstance(region.created_at, datetime)


class TestInvalidationRuleEntity:
    """Tests for the InvalidationRule entity."""
    
    def test_create_invalidation_rule(self):
        """Test creating an invalidation rule entity."""
        rule_id = InvalidationRuleId(TEST_RULE_ID)
        
        rule = InvalidationRule(
            id=rule_id,
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            events=["user_updated"],
            is_active=True,
            configuration={"priority": 10}
        )
        
        assert rule.id == rule_id
        assert rule.name == "test-rule"
        assert rule.strategy_type == InvalidationStrategyType.PATTERN_BASED
        assert rule.pattern == "user:*"
        assert rule.events == ["user_updated"]
        assert rule.is_active is True
        assert rule.configuration == {"priority": 10}
        assert isinstance(rule.created_at, datetime)
    
    def test_activate_deactivate(self):
        """Test the activate and deactivate methods."""
        rule_id = InvalidationRuleId(TEST_RULE_ID)
        rule = InvalidationRule(
            id=rule_id,
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            is_active=False
        )
        
        assert rule.is_active is False
        
        rule.activate()
        assert rule.is_active is True
        
        rule.deactivate()
        assert rule.is_active is False
    
    def test_matches(self):
        """Test the matches method."""
        rule_id = InvalidationRuleId(TEST_RULE_ID)
        
        # Pattern-based rule
        pattern_rule = InvalidationRule(
            id=rule_id,
            name="pattern-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*"
        )
        
        assert pattern_rule.matches("user:123") is True
        assert pattern_rule.matches("product:123") is False
        
        # Time-based rule (no pattern)
        time_rule = InvalidationRule(
            id=rule_id,
            name="time-rule",
            strategy_type=InvalidationStrategyType.TIME_BASED,
            ttl=300
        )
        
        assert time_rule.matches("any_key") is False
        
        # Invalid pattern
        invalid_rule = InvalidationRule(
            id=rule_id,
            name="invalid-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="["  # Invalid regex
        )
        
        assert invalid_rule.matches("any_key") is False


class TestCacheConfigurationEntity:
    """Tests for the CacheConfiguration entity."""
    
    def test_create_cache_configuration(self):
        """Test creating a cache configuration entity."""
        config = CacheConfiguration(
            id="config-1",
            enabled=True,
            key_prefix="app:",
            use_hash_keys=True,
            hash_algorithm="md5",
            use_multi_level=True,
            fallback_on_error=True,
            local_config={"type": "memory", "max_size": 1000},
            distributed_config={"type": "redis", "host": "localhost"},
            invalidation_config={"time_based": True, "default_ttl": 300},
            monitoring_config={"enabled": True, "collect_latency": True},
            regions={"users": {"ttl": 600}, "products": {"ttl": 3600}}
        )
        
        assert config.id == "config-1"
        assert config.enabled is True
        assert config.key_prefix == "app:"
        assert config.use_hash_keys is True
        assert config.hash_algorithm == "md5"
        assert config.use_multi_level is True
        assert config.fallback_on_error is True
        assert config.local_config == {"type": "memory", "max_size": 1000}
        assert config.distributed_config == {"type": "redis", "host": "localhost"}
        assert config.invalidation_config == {"time_based": True, "default_ttl": 300}
        assert config.monitoring_config == {"enabled": True, "collect_latency": True}
        assert config.regions == {"users": {"ttl": 600}, "products": {"ttl": 3600}}
    
    def test_enable_disable(self):
        """Test the enable and disable methods."""
        config = CacheConfiguration()
        
        config.enable()
        assert config.enabled is True
        
        config.disable()
        assert config.enabled is False
    
    def test_enable_disable_multi_level(self):
        """Test the enable_multi_level and disable_multi_level methods."""
        config = CacheConfiguration()
        
        config.enable_multi_level()
        assert config.use_multi_level is True
        
        config.disable_multi_level()
        assert config.use_multi_level is False
    
    def test_enable_disable_distributed(self):
        """Test the enable_distributed and disable_distributed methods."""
        config = CacheConfiguration()
        
        config.enable_distributed()
        assert config.distributed_config["enabled"] is True
        
        config.disable_distributed()
        assert config.distributed_config["enabled"] is False
    
    def test_enable_disable_monitoring(self):
        """Test the enable_monitoring and disable_monitoring methods."""
        config = CacheConfiguration()
        
        config.enable_monitoring()
        assert config.monitoring_config["enabled"] is True
        
        config.disable_monitoring()
        assert config.monitoring_config["enabled"] is False
    
    def test_add_remove_region(self):
        """Test the add_region and remove_region methods."""
        config = CacheConfiguration()
        
        # Add a region
        region_config = {"ttl": 300, "max_size": 1000}
        config.add_region("test-region", region_config)
        assert "test-region" in config.regions
        assert config.regions["test-region"] == region_config
        
        # Remove a region
        result = config.remove_region("test-region")
        assert result is True
        assert "test-region" not in config.regions
        
        # Remove a non-existent region
        result = config.remove_region("non-existent")
        assert result is False


# Repository Tests
class TestMemoryCacheItemRepository:
    """Tests for the MemoryCacheItemRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository for testing."""
        return MemoryCacheItemRepository()
    
    @pytest.fixture
    def sample_item(self):
        """Create a sample cache item for testing."""
        return CacheItem(
            key=CacheKeyId(TEST_KEY),
            value="test-value",
            expiry=datetime.now(UTC) + timedelta(seconds=300),
            region=CacheRegionId(TEST_REGION_ID),
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_set_get(self, repository, sample_item):
        """Test setting and getting a cache item."""
        # Set the item
        result = await repository.set(sample_item)
        assert isinstance(result, Success)
        assert result.value is True
        
        # Get the item
        result = await repository.get(sample_item.key, sample_item.region)
        assert isinstance(result, Success)
        assert result.value is not None
        assert result.value.key == sample_item.key
        assert result.value.value == sample_item.value
        assert result.value.region == sample_item.region
    
    @pytest.mark.asyncio
    async def test_get_expired(self, repository):
        """Test getting an expired cache item."""
        # Create an expired item
        expired_item = CacheItem(
            key=CacheKeyId("expired-key"),
            value="expired-value",
            expiry=datetime.now(UTC) - timedelta(seconds=1),
            region=CacheRegionId(TEST_REGION_ID)
        )
        
        # Set the item
        await repository.set(expired_item)
        
        # Get the item (should be None since it's expired)
        result = await repository.get(expired_item.key, expired_item.region)
        assert isinstance(result, Success)
        assert result.value is None
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, sample_item):
        """Test deleting a cache item."""
        # Set the item
        await repository.set(sample_item)
        
        # Delete the item
        result = await repository.delete(sample_item.key, sample_item.region)
        assert isinstance(result, Success)
        assert result.value is True
        
        # Get the item (should be None)
        result = await repository.get(sample_item.key, sample_item.region)
        assert isinstance(result, Success)
        assert result.value is None
        
        # Delete a non-existent item
        result = await repository.delete(CacheKeyId("non-existent"), sample_item.region)
        assert isinstance(result, Success)
        assert result.value is False
    
    @pytest.mark.asyncio
    async def test_clear(self, repository, sample_item):
        """Test clearing cache items."""
        # Set the item
        await repository.set(sample_item)
        
        # Set another item in a different region
        other_item = CacheItem(
            key=CacheKeyId("other-key"),
            value="other-value",
            region=CacheRegionId("other-region")
        )
        await repository.set(other_item)
        
        # Clear only the test region
        result = await repository.clear(sample_item.region)
        assert isinstance(result, Success)
        assert result.value is True
        
        # Get the item from the test region (should be None)
        result = await repository.get(sample_item.key, sample_item.region)
        assert isinstance(result, Success)
        assert result.value is None
        
        # Get the item from the other region (should still exist)
        result = await repository.get(other_item.key, other_item.region)
        assert isinstance(result, Success)
        assert result.value is not None
        
        # Clear all regions
        result = await repository.clear()
        assert isinstance(result, Success)
        assert result.value is True
        
        # Get the item from the other region (should be None now)
        result = await repository.get(other_item.key, other_item.region)
        assert isinstance(result, Success)
        assert result.value is None
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, repository):
        """Test invalidating cache items by pattern."""
        # Set some items
        user_items = [
            CacheItem(key=CacheKeyId("user:1"), value="User 1"),
            CacheItem(key=CacheKeyId("user:2"), value="User 2"),
            CacheItem(key=CacheKeyId("user:3"), value="User 3")
        ]
        product_items = [
            CacheItem(key=CacheKeyId("product:1"), value="Product 1"),
            CacheItem(key=CacheKeyId("product:2"), value="Product 2")
        ]
        
        for item in user_items + product_items:
            await repository.set(item)
        
        # Invalidate user items
        result = await repository.invalidate_pattern("user:.*")
        assert isinstance(result, Success)
        assert result.value == 3  # 3 user items should be invalidated
        
        # Verify user items are gone
        for item in user_items:
            result = await repository.get(item.key)
            assert isinstance(result, Success)
            assert result.value is None
        
        # Verify product items still exist
        for item in product_items:
            result = await repository.get(item.key)
            assert isinstance(result, Success)
            assert result.value is not None
        
        # Test with invalid pattern
        result = await repository.invalidate_pattern("[")  # Invalid regex
        assert isinstance(result, Failure)
        assert "Invalid pattern" in result.error
    
    @pytest.mark.asyncio
    async def test_get_keys(self, repository, sample_item):
        """Test getting all cache keys."""
        # Set the item
        await repository.set(sample_item)
        
        # Set another item in a different region
        other_item = CacheItem(
            key=CacheKeyId("other-key"),
            value="other-value",
            region=CacheRegionId("other-region")
        )
        await repository.set(other_item)
        
        # Get keys from the test region
        result = await repository.get_keys(sample_item.region)
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_item.key
        
        # Get all keys
        result = await repository.get_keys()
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert sorted([k.value for k in result.value]) == sorted([TEST_KEY, "other-key"])
    
    @pytest.mark.asyncio
    async def test_get_size(self, repository, sample_item):
        """Test getting the cache size."""
        # Set the item
        await repository.set(sample_item)
        
        # Set another item in a different region
        other_item = CacheItem(
            key=CacheKeyId("other-key"),
            value="other-value",
            region=CacheRegionId("other-region")
        )
        await repository.set(other_item)
        
        # Get size of the test region
        result = await repository.get_size(sample_item.region)
        assert isinstance(result, Success)
        assert result.value == 1
        
        # Get total size
        result = await repository.get_size()
        assert isinstance(result, Success)
        assert result.value == 2


# Service Tests
class TestCacheProviderService:
    """Tests for the CacheProviderService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=CacheProviderRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with a mock repository for testing."""
        return CacheProviderService(repository=mock_repository)
    
    @pytest.fixture
    def sample_provider(self):
        """Create a sample provider for testing."""
        return CacheProvider(
            id=CacheProviderId(TEST_PROVIDER_ID),
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            connection_details={"host": "localhost"},
            configuration={"max_size": 1000}
        )
    
    @pytest.mark.asyncio
    @patch("uuid.uuid4", return_value=uuid.UUID(TEST_PROVIDER_ID))
    async def test_register_provider(self, mock_uuid, service, mock_repository, sample_provider):
        """Test registering a provider."""
        # Setup
        mock_repository.create.return_value = Success(sample_provider)
        
        # Execute
        result = await service.register_provider(
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            connection_details={"host": "localhost"},
            configuration={"max_size": 1000}
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_PROVIDER_ID
        assert result.value.name == "test-provider"
        assert result.value.provider_type == CacheProviderType.MEMORY
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_provider(self, service, mock_repository, sample_provider):
        """Test getting a provider by ID."""
        # Setup
        mock_repository.get.return_value = Success(sample_provider)
        
        # Execute
        result = await service.get_provider(CacheProviderId(TEST_PROVIDER_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_provider
        mock_repository.get.assert_called_once_with(CacheProviderId(TEST_PROVIDER_ID))
    
    @pytest.mark.asyncio
    async def test_get_provider_by_name(self, service, mock_repository, sample_provider):
        """Test getting a provider by name."""
        # Setup
        mock_repository.get_by_name.return_value = Success(sample_provider)
        
        # Execute
        result = await service.get_provider_by_name("test-provider")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_provider
        mock_repository.get_by_name.assert_called_once_with("test-provider")
    
    @pytest.mark.asyncio
    async def test_update_provider(self, service, mock_repository, sample_provider):
        """Test updating a provider."""
        # Setup
        mock_repository.get.return_value = Success(sample_provider)
        updated_provider = sample_provider
        updated_provider.name = "updated-provider"
        mock_repository.update.return_value = Success(updated_provider)
        
        # Execute
        result = await service.update_provider(
            provider_id=CacheProviderId(TEST_PROVIDER_ID),
            name="updated-provider"
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.name == "updated-provider"
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_provider(self, service, mock_repository):
        """Test deleting a provider."""
        # Setup
        mock_repository.delete.return_value = Success(True)
        
        # Execute
        result = await service.delete_provider(CacheProviderId(TEST_PROVIDER_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_repository.delete.assert_called_once_with(CacheProviderId(TEST_PROVIDER_ID))
    
    @pytest.mark.asyncio
    async def test_list_providers(self, service, mock_repository, sample_provider):
        """Test listing all providers."""
        # Setup
        mock_repository.list.return_value = Success([sample_provider])
        
        # Execute
        result = await service.list_providers()
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_provider
        mock_repository.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_activate_provider(self, service, mock_repository, sample_provider):
        """Test activating a provider."""
        # Setup
        deactivated_provider = CacheProvider(
            id=CacheProviderId(TEST_PROVIDER_ID),
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            is_active=False
        )
        mock_repository.get.return_value = Success(deactivated_provider)
        
        activated_provider = CacheProvider(
            id=CacheProviderId(TEST_PROVIDER_ID),
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            is_active=True
        )
        mock_repository.update.return_value = Success(activated_provider)
        
        # Execute
        result = await service.activate_provider(CacheProviderId(TEST_PROVIDER_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.is_active is True
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_provider(self, service, mock_repository, sample_provider):
        """Test deactivating a provider."""
        # Setup
        mock_repository.get.return_value = Success(sample_provider)
        
        deactivated_provider = CacheProvider(
            id=CacheProviderId(TEST_PROVIDER_ID),
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            is_active=False
        )
        mock_repository.update.return_value = Success(deactivated_provider)
        
        # Execute
        result = await service.deactivate_provider(CacheProviderId(TEST_PROVIDER_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.is_active is False
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_provider_health(self, service, mock_repository, sample_provider):
        """Test checking provider health."""
        # Setup
        mock_repository.get.return_value = Success(sample_provider)
        
        # Execute
        result = await service.check_provider_health(CacheProviderId(TEST_PROVIDER_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.provider_id == CacheProviderId(TEST_PROVIDER_ID)
        assert result.value.is_healthy is True
        assert "simulated" in result.value.details
        mock_repository.get.assert_called_once()


class TestCacheRegionService:
    """Tests for the CacheRegionService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=CacheRegionRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def mock_provider_repository(self):
        """Create a mock provider repository for testing."""
        repository = AsyncMock(spec=CacheProviderRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository, mock_provider_repository):
        """Create a service with mock repositories for testing."""
        return CacheRegionService(
            repository=mock_repository,
            provider_repository=mock_provider_repository
        )
    
    @pytest.fixture
    def sample_provider(self):
        """Create a sample provider for testing."""
        return CacheProvider(
            id=CacheProviderId(TEST_PROVIDER_ID),
            name="test-provider",
            provider_type=CacheProviderType.MEMORY
        )
    
    @pytest.fixture
    def sample_region(self):
        """Create a sample region for testing."""
        return CacheRegion(
            id=CacheRegionId(TEST_REGION_ID),
            name="test-region",
            ttl=300,
            provider_id=CacheProviderId(TEST_PROVIDER_ID)
        )
    
    @pytest.mark.asyncio
    async def test_create_region(self, service, mock_repository, mock_provider_repository, sample_provider, sample_region):
        """Test creating a region."""
        # Setup
        mock_provider_repository.get.return_value = Success(sample_provider)
        mock_repository.create.return_value = Success(sample_region)
        
        # Execute
        result = await service.create_region(
            name="test-region",
            provider_id=CacheProviderId(TEST_PROVIDER_ID),
            ttl=300
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_REGION_ID
        assert result.value.name == "test-region"
        assert result.value.ttl == 300
        assert result.value.provider_id.value == TEST_PROVIDER_ID
        mock_provider_repository.get.assert_called_once()
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_region_provider_not_found(self, service, mock_provider_repository):
        """Test creating a region with a non-existent provider."""
        # Setup
        mock_provider_repository.get.return_value = Failure("Provider not found")
        
        # Execute
        result = await service.create_region(
            name="test-region",
            provider_id=CacheProviderId("non-existent"),
            ttl=300
        )
        
        # Assert
        assert isinstance(result, Failure)
        assert "Provider not found" in result.error
        mock_provider_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_region(self, service, mock_repository, sample_region):
        """Test getting a region by ID."""
        # Setup
        mock_repository.get.return_value = Success(sample_region)
        
        # Execute
        result = await service.get_region(CacheRegionId(TEST_REGION_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_region
        mock_repository.get.assert_called_once_with(CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_get_region_by_name(self, service, mock_repository, sample_region):
        """Test getting a region by name."""
        # Setup
        mock_repository.get_by_name.return_value = Success(sample_region)
        
        # Execute
        result = await service.get_region_by_name("test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_region
        mock_repository.get_by_name.assert_called_once_with("test-region")
    
    @pytest.mark.asyncio
    async def test_update_region(self, service, mock_repository, sample_region):
        """Test updating a region."""
        # Setup
        mock_repository.get.return_value = Success(sample_region)
        updated_region = sample_region
        updated_region.ttl = 600
        mock_repository.update.return_value = Success(updated_region)
        
        # Execute
        result = await service.update_region(
            region_id=CacheRegionId(TEST_REGION_ID),
            ttl=600
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.ttl == 600
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_region(self, service, mock_repository):
        """Test deleting a region."""
        # Setup
        mock_repository.delete.return_value = Success(True)
        
        # Execute
        result = await service.delete_region(CacheRegionId(TEST_REGION_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_repository.delete.assert_called_once_with(CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_list_regions(self, service, mock_repository, sample_region):
        """Test listing all regions."""
        # Setup
        mock_repository.list.return_value = Success([sample_region])
        
        # Execute
        result = await service.list_regions()
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_region
        mock_repository.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_regions_by_provider(self, service, mock_repository, sample_region):
        """Test listing regions by provider."""
        # Setup
        regions = [
            sample_region,
            CacheRegion(
                id=CacheRegionId("other-region"),
                name="other-region",
                ttl=300,
                provider_id=CacheProviderId("other-provider")
            )
        ]
        mock_repository.list.return_value = Success(regions)
        
        # Execute
        result = await service.list_regions_by_provider(CacheProviderId(TEST_PROVIDER_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_region
        mock_repository.list.assert_called_once()


class TestInvalidationRuleService:
    """Tests for the InvalidationRuleService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=InvalidationRuleRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with a mock repository for testing."""
        return InvalidationRuleService(repository=mock_repository)
    
    @pytest.fixture
    def sample_rule(self):
        """Create a sample rule for testing."""
        return InvalidationRule(
            id=InvalidationRuleId(TEST_RULE_ID),
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            events=["user_updated"],
            is_active=True
        )
    
    @pytest.mark.asyncio
    @patch("uuid.uuid4", return_value=uuid.UUID(TEST_RULE_ID))
    async def test_create_rule(self, mock_uuid, service, mock_repository, sample_rule):
        """Test creating a rule."""
        # Setup
        mock_repository.create.return_value = Success(sample_rule)
        
        # Execute
        result = await service.create_rule(
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            events=["user_updated"]
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_RULE_ID
        assert result.value.name == "test-rule"
        assert result.value.strategy_type == InvalidationStrategyType.PATTERN_BASED
        assert result.value.pattern == "user:*"
        assert result.value.events == ["user_updated"]
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_rule_validation(self, service):
        """Test validation when creating a rule."""
        # Test pattern-based rule without pattern
        result = await service.create_rule(
            name="invalid-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED
        )
        assert isinstance(result, Failure)
        assert "Pattern is required" in result.error
        
        # Test time-based rule without TTL
        result = await service.create_rule(
            name="invalid-rule",
            strategy_type=InvalidationStrategyType.TIME_BASED
        )
        assert isinstance(result, Failure)
        assert "TTL is required" in result.error
        
        # Test event-based rule without events
        result = await service.create_rule(
            name="invalid-rule",
            strategy_type=InvalidationStrategyType.EVENT_BASED
        )
        assert isinstance(result, Failure)
        assert "Events are required" in result.error
    
    @pytest.mark.asyncio
    async def test_get_rule(self, service, mock_repository, sample_rule):
        """Test getting a rule by ID."""
        # Setup
        mock_repository.get.return_value = Success(sample_rule)
        
        # Execute
        result = await service.get_rule(InvalidationRuleId(TEST_RULE_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_rule
        mock_repository.get.assert_called_once_with(InvalidationRuleId(TEST_RULE_ID))
    
    @pytest.mark.asyncio
    async def test_get_rule_by_name(self, service, mock_repository, sample_rule):
        """Test getting a rule by name."""
        # Setup
        mock_repository.get_by_name.return_value = Success(sample_rule)
        
        # Execute
        result = await service.get_rule_by_name("test-rule")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_rule
        mock_repository.get_by_name.assert_called_once_with("test-rule")
    
    @pytest.mark.asyncio
    async def test_update_rule(self, service, mock_repository, sample_rule):
        """Test updating a rule."""
        # Setup
        mock_repository.get.return_value = Success(sample_rule)
        updated_rule = sample_rule
        updated_rule.pattern = "user:[0-9]+"
        mock_repository.update.return_value = Success(updated_rule)
        
        # Execute
        result = await service.update_rule(
            rule_id=InvalidationRuleId(TEST_RULE_ID),
            pattern="user:[0-9]+"
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.pattern == "user:[0-9]+"
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_rule_validation(self, service, mock_repository):
        """Test validation when updating a rule."""
        # Setup for pattern-based rule
        pattern_rule = InvalidationRule(
            id=InvalidationRuleId(TEST_RULE_ID),
            name="pattern-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*"
        )
        mock_repository.get.return_value = Success(pattern_rule)
        
        # Test updating pattern to None
        result = await service.update_rule(
            rule_id=InvalidationRuleId(TEST_RULE_ID),
            pattern=None
        )
        assert isinstance(result, Success)  # No validation error since we're not changing the strategy type
        
        # Test updating to pattern-based without pattern
        result = await service.update_rule(
            rule_id=InvalidationRuleId(TEST_RULE_ID),
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern=None
        )
        assert isinstance(result, Failure)
        assert "Pattern is required" in result.error
    
    @pytest.mark.asyncio
    async def test_delete_rule(self, service, mock_repository):
        """Test deleting a rule."""
        # Setup
        mock_repository.delete.return_value = Success(True)
        
        # Execute
        result = await service.delete_rule(InvalidationRuleId(TEST_RULE_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_repository.delete.assert_called_once_with(InvalidationRuleId(TEST_RULE_ID))
    
    @pytest.mark.asyncio
    async def test_list_rules(self, service, mock_repository, sample_rule):
        """Test listing all rules."""
        # Setup
        mock_repository.list.return_value = Success([sample_rule])
        
        # Execute
        result = await service.list_rules()
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_rule
        mock_repository.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_rules_by_strategy(self, service, mock_repository, sample_rule):
        """Test listing rules by strategy type."""
        # Setup
        mock_repository.get_by_strategy_type.return_value = Success([sample_rule])
        
        # Execute
        result = await service.list_rules_by_strategy(InvalidationStrategyType.PATTERN_BASED)
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_rule
        mock_repository.get_by_strategy_type.assert_called_once_with(InvalidationStrategyType.PATTERN_BASED)
    
    @pytest.mark.asyncio
    async def test_activate_rule(self, service, mock_repository, sample_rule):
        """Test activating a rule."""
        # Setup
        inactive_rule = InvalidationRule(
            id=InvalidationRuleId(TEST_RULE_ID),
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            is_active=False
        )
        mock_repository.get.return_value = Success(inactive_rule)
        
        activated_rule = InvalidationRule(
            id=InvalidationRuleId(TEST_RULE_ID),
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            is_active=True
        )
        mock_repository.update.return_value = Success(activated_rule)
        
        # Execute
        result = await service.activate_rule(InvalidationRuleId(TEST_RULE_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.is_active is True
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_rule(self, service, mock_repository, sample_rule):
        """Test deactivating a rule."""
        # Setup
        mock_repository.get.return_value = Success(sample_rule)
        
        deactivated_rule = InvalidationRule(
            id=InvalidationRuleId(TEST_RULE_ID),
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            is_active=False
        )
        mock_repository.update.return_value = Success(deactivated_rule)
        
        # Execute
        result = await service.deactivate_rule(InvalidationRuleId(TEST_RULE_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.is_active is False
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_matching_rules(self, service, mock_repository):
        """Test finding rules that match a key."""
        # Setup
        rules = [
            InvalidationRule(
                id=InvalidationRuleId("rule-1"),
                name="user-rule",
                strategy_type=InvalidationStrategyType.PATTERN_BASED,
                pattern="user:.*",
                is_active=True
            ),
            InvalidationRule(
                id=InvalidationRuleId("rule-2"),
                name="product-rule",
                strategy_type=InvalidationStrategyType.PATTERN_BASED,
                pattern="product:.*",
                is_active=True
            ),
            InvalidationRule(
                id=InvalidationRuleId("rule-3"),
                name="inactive-rule",
                strategy_type=InvalidationStrategyType.PATTERN_BASED,
                pattern="user:.*",
                is_active=False
            )
        ]
        mock_repository.list.return_value = Success(rules)
        
        # Execute
        result = await service.find_matching_rules("user:123")
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0].id.value == "rule-1"
        mock_repository.list.assert_called_once()


class TestCacheItemService:
    """Tests for the CacheItemService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=CacheItemRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def mock_region_repository(self):
        """Create a mock region repository for testing."""
        repository = AsyncMock(spec=CacheRegionRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository, mock_region_repository):
        """Create a service with mock repositories for testing."""
        return CacheItemService(
            repository=mock_repository,
            region_repository=mock_region_repository
        )
    
    @pytest.fixture
    def sample_region(self):
        """Create a sample region for testing."""
        return CacheRegion(
            id=CacheRegionId(TEST_REGION_ID),
            name="test-region",
            ttl=300,
            provider_id=CacheProviderId(TEST_PROVIDER_ID)
        )
    
    @pytest.fixture
    def sample_item(self):
        """Create a sample cache item for testing."""
        return CacheItem(
            key=CacheKeyId(TEST_KEY),
            value="test-value",
            expiry=datetime.now(UTC) + timedelta(seconds=300),
            region=CacheRegionId(TEST_REGION_ID),
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_get_item(self, service, mock_repository, mock_region_repository, sample_region, sample_item):
        """Test getting a cache item."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.get.return_value = Success(sample_item)
        
        # Execute
        result = await service.get_item(TEST_KEY, "test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_item
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.get.assert_called_once_with(CacheKeyId(TEST_KEY), CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_get_item_region_not_found(self, service, mock_region_repository):
        """Test getting a cache item with a non-existent region."""
        # Setup
        mock_region_repository.get_by_name.return_value = Failure("Region not found")
        
        # Execute
        result = await service.get_item(TEST_KEY, "non-existent")
        
        # Assert
        assert isinstance(result, Failure)
        assert "Region not found" in result.error
        mock_region_repository.get_by_name.assert_called_once_with("non-existent")
    
    @pytest.mark.asyncio
    async def test_set_item(self, service, mock_repository, mock_region_repository, sample_region, sample_item):
        """Test setting a cache item."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.set.return_value = Success(True)
        
        # Execute
        result = await service.set_item(
            key=TEST_KEY,
            value="test-value",
            region_name="test-region",
            metadata={"source": "test"}
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.key.value == TEST_KEY
        assert result.value.value == "test-value"
        assert result.value.region.value == TEST_REGION_ID
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_item(self, service, mock_repository, mock_region_repository, sample_region):
        """Test deleting a cache item."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.delete.return_value = Success(True)
        
        # Execute
        result = await service.delete_item(TEST_KEY, "test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.delete.assert_called_once_with(CacheKeyId(TEST_KEY), CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_clear_region(self, service, mock_repository, mock_region_repository, sample_region):
        """Test clearing a cache region."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.clear.return_value = Success(True)
        
        # Execute
        result = await service.clear_region("test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.clear.assert_called_once_with(CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self, service, mock_repository, mock_region_repository, sample_region):
        """Test invalidating cache items by pattern."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.invalidate_pattern.return_value = Success(3)
        
        # Execute
        result = await service.invalidate_by_pattern("user:.*", "test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == 3
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.invalidate_pattern.assert_called_once_with("user:.*", CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_get_keys(self, service, mock_repository, mock_region_repository, sample_region):
        """Test getting all cache keys."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.get_keys.return_value = Success([CacheKeyId(TEST_KEY)])
        
        # Execute
        result = await service.get_keys("test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == [TEST_KEY]
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.get_keys.assert_called_once_with(CacheRegionId(TEST_REGION_ID))
    
    @pytest.mark.asyncio
    async def test_get_region_size(self, service, mock_repository, mock_region_repository, sample_region):
        """Test getting the cache region size."""
        # Setup
        mock_region_repository.get_by_name.return_value = Success(sample_region)
        mock_repository.get_size.return_value = Success(10)
        
        # Execute
        result = await service.get_region_size("test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == 10
        mock_region_repository.get_by_name.assert_called_once_with("test-region")
        mock_repository.get_size.assert_called_once_with(CacheRegionId(TEST_REGION_ID))


class TestCacheConfigurationService:
    """Tests for the CacheConfigurationService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=CacheConfigurationRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with a mock repository for testing."""
        return CacheConfigurationService(repository=mock_repository)
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration for testing."""
        return CacheConfiguration(
            id="config-1",
            enabled=True,
            key_prefix="app:",
            use_hash_keys=True,
            hash_algorithm="md5",
            use_multi_level=True,
            fallback_on_error=True
        )
    
    @pytest.mark.asyncio
    async def test_get_active_configuration(self, service, mock_repository, sample_config):
        """Test getting the active configuration."""
        # Setup
        mock_repository.get.return_value = Success(sample_config)
        
        # Execute
        result = await service.get_active_configuration()
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_config
        mock_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_configuration(self, service, mock_repository, sample_config):
        """Test saving a configuration."""
        # Setup
        mock_repository.save.return_value = Success(sample_config)
        
        # Execute
        result = await service.save_configuration(sample_config)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_config
        mock_repository.save.assert_called_once_with(sample_config)
    
    @pytest.mark.asyncio
    async def test_update_configuration(self, service, mock_repository, sample_config):
        """Test updating a configuration."""
        # Setup
        mock_repository.get.return_value = Success(sample_config)
        updated_config = CacheConfiguration(
            id="config-1",
            enabled=False,
            key_prefix="app:",
            use_hash_keys=True,
            hash_algorithm="md5",
            use_multi_level=True,
            fallback_on_error=True
        )
        mock_repository.save.return_value = Success(updated_config)
        
        # Execute
        result = await service.update_configuration(enabled=False)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.enabled is False
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_configuration_create_if_not_exists(self, service, mock_repository):
        """Test updating a configuration when none exists (creates a new one)."""
        # Setup
        mock_repository.get.return_value = Failure("No configuration found")
        new_config = CacheConfiguration(enabled=False)
        mock_repository.save.return_value = Success(new_config)
        
        # Execute
        result = await service.update_configuration(enabled=False)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.enabled is False
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_region_config(self, service, mock_repository, sample_config):
        """Test adding a region configuration."""
        # Setup
        mock_repository.get.return_value = Success(sample_config)
        updated_config = sample_config
        updated_config.regions["test-region"] = {"ttl": 300}
        mock_repository.save.return_value = Success(updated_config)
        
        # Execute
        result = await service.add_region_config("test-region", {"ttl": 300})
        
        # Assert
        assert isinstance(result, Success)
        assert "test-region" in result.value.regions
        assert result.value.regions["test-region"] == {"ttl": 300}
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_region_config(self, service, mock_repository, sample_config):
        """Test removing a region configuration."""
        # Setup
        config_with_region = sample_config
        config_with_region.regions["test-region"] = {"ttl": 300}
        mock_repository.get.return_value = Success(config_with_region)
        
        updated_config = sample_config
        updated_config.regions = {}
        mock_repository.save.return_value = Success(updated_config)
        
        # Execute
        result = await service.remove_region_config("test-region")
        
        # Assert
        assert isinstance(result, Success)
        assert "test-region" not in result.value.regions
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_region_config_not_found(self, service, mock_repository, sample_config):
        """Test removing a non-existent region configuration."""
        # Setup
        mock_repository.get.return_value = Success(sample_config)
        
        # Execute
        result = await service.remove_region_config("non-existent")
        
        # Assert
        assert isinstance(result, Failure)
        assert "not found" in result.error
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_enable_disable_caching(self, service, mock_repository, sample_config):
        """Test enabling and disabling caching."""
        # Setup for enabling
        disabled_config = CacheConfiguration(
            id="config-1",
            enabled=False
        )
        mock_repository.get.return_value = Success(disabled_config)
        
        enabled_config = CacheConfiguration(
            id="config-1",
            enabled=True
        )
        mock_repository.save.return_value = Success(enabled_config)
        
        # Execute enable
        result = await service.enable_caching()
        
        # Assert enable
        assert isinstance(result, Success)
        assert result.value.enabled is True
        
        # Reset mocks
        mock_repository.reset_mock()
        
        # Setup for disabling
        mock_repository.get.return_value = Success(enabled_config)
        mock_repository.save.return_value = Success(disabled_config)
        
        # Execute disable
        result = await service.disable_caching()
        
        # Assert disable
        assert isinstance(result, Success)
        assert result.value.enabled is False
    
    @pytest.mark.asyncio
    async def test_enable_disable_multi_level(self, service, mock_repository, sample_config):
        """Test enabling and disabling multi-level caching."""
        # Setup for enabling
        single_level_config = CacheConfiguration(
            id="config-1",
            use_multi_level=False
        )
        mock_repository.get.return_value = Success(single_level_config)
        
        multi_level_config = CacheConfiguration(
            id="config-1",
            use_multi_level=True
        )
        mock_repository.save.return_value = Success(multi_level_config)
        
        # Execute enable
        result = await service.enable_multi_level()
        
        # Assert enable
        assert isinstance(result, Success)
        assert result.value.use_multi_level is True
        
        # Reset mocks
        mock_repository.reset_mock()
        
        # Setup for disabling
        mock_repository.get.return_value = Success(multi_level_config)
        mock_repository.save.return_value = Success(single_level_config)
        
        # Execute disable
        result = await service.disable_multi_level()
        
        # Assert disable
        assert isinstance(result, Success)
        assert result.value.use_multi_level is False
    
    @pytest.mark.asyncio
    async def test_enable_disable_distributed(self, service, mock_repository, sample_config):
        """Test enabling and disabling distributed caching."""
        # Setup for enabling
        local_config = CacheConfiguration(
            id="config-1",
            distributed_config={"enabled": False}
        )
        mock_repository.get.return_value = Success(local_config)
        
        distributed_config = CacheConfiguration(
            id="config-1",
            distributed_config={"enabled": True}
        )
        mock_repository.save.return_value = Success(distributed_config)
        
        # Execute enable
        result = await service.enable_distributed()
        
        # Assert enable
        assert isinstance(result, Success)
        assert result.value.distributed_config["enabled"] is True
        
        # Reset mocks
        mock_repository.reset_mock()
        
        # Setup for disabling
        mock_repository.get.return_value = Success(distributed_config)
        mock_repository.save.return_value = Success(local_config)
        
        # Execute disable
        result = await service.disable_distributed()
        
        # Assert disable
        assert isinstance(result, Success)
        assert result.value.distributed_config["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_enable_disable_monitoring(self, service, mock_repository, sample_config):
        """Test enabling and disabling cache monitoring."""
        # Setup for enabling
        no_monitoring_config = CacheConfiguration(
            id="config-1",
            monitoring_config={"enabled": False}
        )
        mock_repository.get.return_value = Success(no_monitoring_config)
        
        monitoring_config = CacheConfiguration(
            id="config-1",
            monitoring_config={"enabled": True}
        )
        mock_repository.save.return_value = Success(monitoring_config)
        
        # Execute enable
        result = await service.enable_monitoring()
        
        # Assert enable
        assert isinstance(result, Success)
        assert result.value.monitoring_config["enabled"] is True
        
        # Reset mocks
        mock_repository.reset_mock()
        
        # Setup for disabling
        mock_repository.get.return_value = Success(monitoring_config)
        mock_repository.save.return_value = Success(no_monitoring_config)
        
        # Execute disable
        result = await service.disable_monitoring()
        
        # Assert disable
        assert isinstance(result, Success)
        assert result.value.monitoring_config["enabled"] is False