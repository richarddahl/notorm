"""
Tests for the Caching module API endpoints.

This module contains comprehensive tests for all API endpoints of the Caching module,
focusing on cache provider endpoints, cache region endpoints, invalidation rule endpoints,
cache item endpoints, and configuration endpoints.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from uno.core.result import Result, Success, Failure

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

from uno.caching.domain_services import (
    CacheProviderServiceProtocol,
    CacheRegionServiceProtocol,
    InvalidationRuleServiceProtocol,
    CacheItemServiceProtocol,
    CacheMonitoringServiceProtocol,
    CacheConfigurationServiceProtocol
)

from uno.caching.domain_endpoints import (
    router,
    create_entity_response,
    ProviderResponse,
    RegionResponse,
    RuleResponse,
    CacheItemResponse,
    HealthResponse,
    ConfigurationResponse,
    ConfigurationSummaryResponse
)


# Test constants
TEST_PROVIDER_ID = "test-provider-id"
TEST_REGION_ID = "test-region"
TEST_RULE_ID = "test-rule-id"
TEST_KEY = "test-key"


# Endpoint Tests
class TestCacheProviderEndpoints:
    """Tests for the cache provider endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=CacheProviderServiceProtocol)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        app = FastAPI()
        
        # Mock the dependency injection
        def get_provider_service():
            return mock_service
        
        # Use the router from domain_endpoints
        from fastapi import Depends
        from uno.dependencies.fastapi_integration import inject_dependency
        
        # Patch the dependency injection in the router
        from unittest.mock import patch
        with patch('uno.caching.domain_endpoints.inject_dependency', lambda _: Depends(get_provider_service)):
            app.include_router(router)
        
        return TestClient(app)
    
    @pytest.fixture
    def sample_provider(self):
        """Create a sample provider for testing."""
        return CacheProvider(
            id=CacheProviderId(TEST_PROVIDER_ID),
            name="test-provider",
            provider_type=CacheProviderType.MEMORY,
            connection_details={"host": "localhost"},
            configuration={"max_size": 1000},
            is_active=True,
            created_at=datetime.now(UTC)
        )
    
    def test_create_provider(self, client, mock_service, sample_provider):
        """Test creating a provider endpoint."""
        # Setup
        mock_service.register_provider.return_value = Success(sample_provider)
        
        # Execute
        response = client.post(
            "/api/cache/providers",
            json={
                "name": "test-provider",
                "provider_type": "memory",
                "connection_details": {"host": "localhost"},
                "configuration": {"max_size": 1000}
            }
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == TEST_PROVIDER_ID
        assert response.json()["name"] == "test-provider"
        assert response.json()["provider_type"] == "memory"
        assert response.json()["is_active"] is True
        mock_service.register_provider.assert_called_once()
    
    def test_list_providers(self, client, mock_service, sample_provider):
        """Test listing providers endpoint."""
        # Setup
        mock_service.list_providers.return_value = Success([sample_provider])
        
        # Execute
        response = client.get("/api/cache/providers")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == TEST_PROVIDER_ID
        assert response.json()[0]["name"] == "test-provider"
        mock_service.list_providers.assert_called_once()
    
    def test_get_provider(self, client, mock_service, sample_provider):
        """Test getting a provider endpoint."""
        # Setup
        mock_service.get_provider.return_value = Success(sample_provider)
        
        # Execute
        response = client.get(f"/api/cache/providers/{TEST_PROVIDER_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_PROVIDER_ID
        assert response.json()["name"] == "test-provider"
        mock_service.get_provider.assert_called_once()
    
    def test_get_provider_not_found(self, client, mock_service):
        """Test getting a non-existent provider."""
        # Setup
        mock_service.get_provider.return_value = Failure("Provider not found")
        
        # Execute
        response = client.get(f"/api/cache/providers/{TEST_PROVIDER_ID}")
        
        # Assert
        assert response.status_code == 404
        assert "Provider not found" in response.json()["detail"]
        mock_service.get_provider.assert_called_once()
    
    def test_update_provider(self, client, mock_service, sample_provider):
        """Test updating a provider endpoint."""
        # Setup
        updated_provider = sample_provider
        updated_provider.name = "updated-provider"
        mock_service.update_provider.return_value = Success(updated_provider)
        
        # Execute
        response = client.put(
            f"/api/cache/providers/{TEST_PROVIDER_ID}",
            json={
                "name": "updated-provider"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_PROVIDER_ID
        assert response.json()["name"] == "updated-provider"
        mock_service.update_provider.assert_called_once()
    
    def test_delete_provider(self, client, mock_service):
        """Test deleting a provider endpoint."""
        # Setup
        mock_service.delete_provider.return_value = Success(True)
        
        # Execute
        response = client.delete(f"/api/cache/providers/{TEST_PROVIDER_ID}")
        
        # Assert
        assert response.status_code == 204
        mock_service.delete_provider.assert_called_once()
    
    def test_activate_provider(self, client, mock_service, sample_provider):
        """Test activating a provider endpoint."""
        # Setup
        mock_service.activate_provider.return_value = Success(sample_provider)
        
        # Execute
        response = client.post(f"/api/cache/providers/{TEST_PROVIDER_ID}/activate")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_PROVIDER_ID
        assert response.json()["is_active"] is True
        mock_service.activate_provider.assert_called_once()
    
    def test_deactivate_provider(self, client, mock_service, sample_provider):
        """Test deactivating a provider endpoint."""
        # Setup
        deactivated_provider = sample_provider
        deactivated_provider.is_active = False
        mock_service.deactivate_provider.return_value = Success(deactivated_provider)
        
        # Execute
        response = client.post(f"/api/cache/providers/{TEST_PROVIDER_ID}/deactivate")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_PROVIDER_ID
        assert response.json()["is_active"] is False
        mock_service.deactivate_provider.assert_called_once()
    
    def test_check_provider_health(self, client, mock_service):
        """Test checking provider health endpoint."""
        # Setup
        health_check = CacheHealth(
            id="health-1",
            provider_id=CacheProviderId(TEST_PROVIDER_ID),
            is_healthy=True,
            latency_ms=5.2,
            details={"memory_usage": "10%"}
        )
        mock_service.check_provider_health.return_value = Success(health_check)
        
        # Execute
        response = client.get(f"/api/cache/providers/{TEST_PROVIDER_ID}/health")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["provider_id"] == TEST_PROVIDER_ID
        assert response.json()["is_healthy"] is True
        assert response.json()["latency_ms"] == 5.2
        assert response.json()["details"] == {"memory_usage": "10%"}
        mock_service.check_provider_health.assert_called_once()


class TestCacheRegionEndpoints:
    """Tests for the cache region endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=CacheRegionServiceProtocol)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        app = FastAPI()
        
        # Mock the dependency injection
        def get_region_service():
            return mock_service
        
        # Use the router from domain_endpoints
        from fastapi import Depends
        from uno.dependencies.fastapi_integration import inject_dependency
        
        # Patch the dependency injection in the router
        from unittest.mock import patch
        with patch('uno.caching.domain_endpoints.inject_dependency', lambda _: Depends(get_region_service)):
            app.include_router(router)
        
        return TestClient(app)
    
    @pytest.fixture
    def sample_region(self):
        """Create a sample region for testing."""
        return CacheRegion(
            id=CacheRegionId(TEST_REGION_ID),
            name="test-region",
            ttl=300,
            provider_id=CacheProviderId(TEST_PROVIDER_ID),
            max_size=1000,
            invalidation_strategy=InvalidationStrategyType.TIME_BASED,
            created_at=datetime.now(UTC),
            configuration={"eviction_policy": "LRU"}
        )
    
    def test_create_region(self, client, mock_service, sample_region):
        """Test creating a region endpoint."""
        # Setup
        mock_service.create_region.return_value = Success(sample_region)
        
        # Execute
        response = client.post(
            "/api/cache/regions",
            json={
                "name": "test-region",
                "provider_id": TEST_PROVIDER_ID,
                "ttl": 300,
                "max_size": 1000,
                "invalidation_strategy": "time_based",
                "configuration": {"eviction_policy": "LRU"}
            }
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == TEST_REGION_ID
        assert response.json()["name"] == "test-region"
        assert response.json()["ttl"] == 300
        assert response.json()["provider_id"] == TEST_PROVIDER_ID
        assert response.json()["invalidation_strategy"] == "time_based"
        mock_service.create_region.assert_called_once()
    
    def test_list_regions(self, client, mock_service, sample_region):
        """Test listing regions endpoint."""
        # Setup
        mock_service.list_regions.return_value = Success([sample_region])
        
        # Execute
        response = client.get("/api/cache/regions")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == TEST_REGION_ID
        assert response.json()[0]["name"] == "test-region"
        mock_service.list_regions.assert_called_once()
    
    def test_list_regions_by_provider(self, client, mock_service, sample_region):
        """Test listing regions by provider endpoint."""
        # Setup
        mock_service.list_regions_by_provider.return_value = Success([sample_region])
        
        # Execute
        response = client.get(f"/api/cache/regions?provider_id={TEST_PROVIDER_ID}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == TEST_REGION_ID
        assert response.json()[0]["name"] == "test-region"
        mock_service.list_regions_by_provider.assert_called_once()
    
    def test_get_region(self, client, mock_service, sample_region):
        """Test getting a region endpoint."""
        # Setup
        mock_service.get_region.return_value = Success(sample_region)
        
        # Execute
        response = client.get(f"/api/cache/regions/{TEST_REGION_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_REGION_ID
        assert response.json()["name"] == "test-region"
        mock_service.get_region.assert_called_once()
    
    def test_get_region_by_name(self, client, mock_service, sample_region):
        """Test getting a region by name endpoint."""
        # Setup
        mock_service.get_region_by_name.return_value = Success(sample_region)
        
        # Execute
        response = client.get("/api/cache/regions/by-name/test-region")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_REGION_ID
        assert response.json()["name"] == "test-region"
        mock_service.get_region_by_name.assert_called_once()
    
    def test_update_region(self, client, mock_service, sample_region):
        """Test updating a region endpoint."""
        # Setup
        updated_region = sample_region
        updated_region.ttl = 600
        mock_service.update_region.return_value = Success(updated_region)
        
        # Execute
        response = client.put(
            f"/api/cache/regions/{TEST_REGION_ID}",
            json={
                "ttl": 600
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_REGION_ID
        assert response.json()["ttl"] == 600
        mock_service.update_region.assert_called_once()
    
    def test_delete_region(self, client, mock_service):
        """Test deleting a region endpoint."""
        # Setup
        mock_service.delete_region.return_value = Success(True)
        
        # Execute
        response = client.delete(f"/api/cache/regions/{TEST_REGION_ID}")
        
        # Assert
        assert response.status_code == 204
        mock_service.delete_region.assert_called_once()


class TestInvalidationRuleEndpoints:
    """Tests for the invalidation rule endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=InvalidationRuleServiceProtocol)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        app = FastAPI()
        
        # Mock the dependency injection
        def get_rule_service():
            return mock_service
        
        # Use the router from domain_endpoints
        from fastapi import Depends
        from uno.dependencies.fastapi_integration import inject_dependency
        
        # Patch the dependency injection in the router
        from unittest.mock import patch
        with patch('uno.caching.domain_endpoints.inject_dependency', lambda _: Depends(get_rule_service)):
            app.include_router(router)
        
        return TestClient(app)
    
    @pytest.fixture
    def sample_rule(self):
        """Create a sample rule for testing."""
        return InvalidationRule(
            id=InvalidationRuleId(TEST_RULE_ID),
            name="test-rule",
            strategy_type=InvalidationStrategyType.PATTERN_BASED,
            pattern="user:*",
            events=["user_updated"],
            is_active=True,
            created_at=datetime.now(UTC),
            configuration={"priority": 10}
        )
    
    def test_create_rule(self, client, mock_service, sample_rule):
        """Test creating a rule endpoint."""
        # Setup
        mock_service.create_rule.return_value = Success(sample_rule)
        
        # Execute
        response = client.post(
            "/api/cache/rules",
            json={
                "name": "test-rule",
                "strategy_type": "pattern_based",
                "pattern": "user:*",
                "events": ["user_updated"],
                "configuration": {"priority": 10}
            }
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == TEST_RULE_ID
        assert response.json()["name"] == "test-rule"
        assert response.json()["strategy_type"] == "pattern_based"
        assert response.json()["pattern"] == "user:*"
        assert response.json()["events"] == ["user_updated"]
        assert response.json()["is_active"] is True
        mock_service.create_rule.assert_called_once()
    
    def test_list_rules(self, client, mock_service, sample_rule):
        """Test listing rules endpoint."""
        # Setup
        mock_service.list_rules.return_value = Success([sample_rule])
        
        # Execute
        response = client.get("/api/cache/rules")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == TEST_RULE_ID
        assert response.json()[0]["name"] == "test-rule"
        mock_service.list_rules.assert_called_once()
    
    def test_list_rules_by_strategy(self, client, mock_service, sample_rule):
        """Test listing rules by strategy endpoint."""
        # Setup
        mock_service.list_rules_by_strategy.return_value = Success([sample_rule])
        
        # Execute
        response = client.get("/api/cache/rules?strategy_type=pattern_based")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == TEST_RULE_ID
        assert response.json()[0]["name"] == "test-rule"
        mock_service.list_rules_by_strategy.assert_called_once()
    
    def test_get_rule(self, client, mock_service, sample_rule):
        """Test getting a rule endpoint."""
        # Setup
        mock_service.get_rule.return_value = Success(sample_rule)
        
        # Execute
        response = client.get(f"/api/cache/rules/{TEST_RULE_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RULE_ID
        assert response.json()["name"] == "test-rule"
        mock_service.get_rule.assert_called_once()
    
    def test_get_rule_by_name(self, client, mock_service, sample_rule):
        """Test getting a rule by name endpoint."""
        # Setup
        mock_service.get_rule_by_name.return_value = Success(sample_rule)
        
        # Execute
        response = client.get("/api/cache/rules/by-name/test-rule")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RULE_ID
        assert response.json()["name"] == "test-rule"
        mock_service.get_rule_by_name.assert_called_once()
    
    def test_update_rule(self, client, mock_service, sample_rule):
        """Test updating a rule endpoint."""
        # Setup
        updated_rule = sample_rule
        updated_rule.pattern = "user:[0-9]+"
        mock_service.update_rule.return_value = Success(updated_rule)
        
        # Execute
        response = client.put(
            f"/api/cache/rules/{TEST_RULE_ID}",
            json={
                "pattern": "user:[0-9]+"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RULE_ID
        assert response.json()["pattern"] == "user:[0-9]+"
        mock_service.update_rule.assert_called_once()
    
    def test_delete_rule(self, client, mock_service):
        """Test deleting a rule endpoint."""
        # Setup
        mock_service.delete_rule.return_value = Success(True)
        
        # Execute
        response = client.delete(f"/api/cache/rules/{TEST_RULE_ID}")
        
        # Assert
        assert response.status_code == 204
        mock_service.delete_rule.assert_called_once()
    
    def test_activate_rule(self, client, mock_service, sample_rule):
        """Test activating a rule endpoint."""
        # Setup
        mock_service.activate_rule.return_value = Success(sample_rule)
        
        # Execute
        response = client.post(f"/api/cache/rules/{TEST_RULE_ID}/activate")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RULE_ID
        assert response.json()["is_active"] is True
        mock_service.activate_rule.assert_called_once()
    
    def test_deactivate_rule(self, client, mock_service, sample_rule):
        """Test deactivating a rule endpoint."""
        # Setup
        deactivated_rule = sample_rule
        deactivated_rule.is_active = False
        mock_service.deactivate_rule.return_value = Success(deactivated_rule)
        
        # Execute
        response = client.post(f"/api/cache/rules/{TEST_RULE_ID}/deactivate")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RULE_ID
        assert response.json()["is_active"] is False
        mock_service.deactivate_rule.assert_called_once()
    
    def test_find_matching_rules(self, client, mock_service, sample_rule):
        """Test finding matching rules endpoint."""
        # Setup
        mock_service.find_matching_rules.return_value = Success([sample_rule])
        
        # Execute
        response = client.get("/api/cache/rules/match/user:123")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == TEST_RULE_ID
        assert response.json()[0]["name"] == "test-rule"
        mock_service.find_matching_rules.assert_called_once()


class TestCacheItemEndpoints:
    """Tests for the cache item endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=CacheItemServiceProtocol)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        app = FastAPI()
        
        # Mock the dependency injection
        def get_cache_service():
            return mock_service
        
        # Use the router from domain_endpoints
        from fastapi import Depends
        from uno.dependencies.fastapi_integration import inject_dependency
        
        # Patch the dependency injection in the router
        from unittest.mock import patch
        with patch('uno.caching.domain_endpoints.inject_dependency', lambda _: Depends(get_cache_service)):
            app.include_router(router)
        
        return TestClient(app)
    
    @pytest.fixture
    def sample_item(self):
        """Create a sample cache item for testing."""
        return CacheItem(
            key=CacheKeyId(TEST_KEY),
            value="test-value",
            expiry=datetime.now(UTC) + timedelta(seconds=300),
            region=CacheRegionId(TEST_REGION_ID),
            created_at=datetime.now(UTC),
            last_accessed=datetime.now(UTC),
            metadata={"source": "test"}
        )
    
    def test_get_item(self, client, mock_service, sample_item):
        """Test getting a cache item endpoint."""
        # Setup
        mock_service.get_item.return_value = Success(sample_item)
        
        # Execute
        response = client.get(f"/api/cache/items/{TEST_KEY}?region={TEST_REGION_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == TEST_KEY
        assert response.json()["value"] == "test-value"
        assert response.json()["region"] == TEST_REGION_ID
        mock_service.get_item.assert_called_once()
    
    def test_get_item_not_found(self, client, mock_service):
        """Test getting a non-existent cache item."""
        # Setup
        mock_service.get_item.return_value = Success(None)
        
        # Execute
        response = client.get(f"/api/cache/items/{TEST_KEY}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        mock_service.get_item.assert_called_once()
    
    def test_set_item(self, client, mock_service, sample_item):
        """Test setting a cache item endpoint."""
        # Setup
        mock_service.set_item.return_value = Success(sample_item)
        
        # Execute
        response = client.put(
            f"/api/cache/items/{TEST_KEY}?region={TEST_REGION_ID}",
            json={
                "value": "test-value",
                "ttl_seconds": 300,
                "metadata": {"source": "test"}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == TEST_KEY
        assert response.json()["value"] == "test-value"
        assert response.json()["region"] == TEST_REGION_ID
        mock_service.set_item.assert_called_once()
    
    def test_delete_item(self, client, mock_service):
        """Test deleting a cache item endpoint."""
        # Setup
        mock_service.delete_item.return_value = Success(True)
        
        # Execute
        response = client.delete(f"/api/cache/items/{TEST_KEY}?region={TEST_REGION_ID}")
        
        # Assert
        assert response.status_code == 204
        mock_service.delete_item.assert_called_once()
    
    def test_clear_region(self, client, mock_service):
        """Test clearing a cache region endpoint."""
        # Setup
        mock_service.clear_region.return_value = Success(True)
        
        # Execute
        response = client.delete(f"/api/cache/items?region={TEST_REGION_ID}")
        
        # Assert
        assert response.status_code == 204
        mock_service.clear_region.assert_called_once()
    
    def test_invalidate_by_pattern(self, client, mock_service):
        """Test invalidating cache items by pattern endpoint."""
        # Setup
        mock_service.invalidate_by_pattern.return_value = Success(3)
        
        # Execute
        response = client.delete("/api/cache/items/pattern/user:.*")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["invalidated_count"] == 3
        mock_service.invalidate_by_pattern.assert_called_once()
    
    def test_get_keys(self, client, mock_service):
        """Test getting all cache keys endpoint."""
        # Setup
        mock_service.get_keys.return_value = Success([TEST_KEY, "other-key"])
        
        # Execute
        response = client.get("/api/cache/items")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert TEST_KEY in response.json()
        assert "other-key" in response.json()
        mock_service.get_keys.assert_called_once()
    
    def test_get_size(self, client, mock_service):
        """Test getting the cache size endpoint."""
        # Setup
        mock_service.get_region_size.return_value = Success(10)
        
        # Execute
        response = client.get("/api/cache/size")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["size"] == 10
        mock_service.get_region_size.assert_called_once()


class TestCacheConfigurationEndpoints:
    """Tests for the cache configuration endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=CacheConfigurationServiceProtocol)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        app = FastAPI()
        
        # Mock the dependency injection
        def get_config_service():
            return mock_service
        
        # Use the router from domain_endpoints
        from fastapi import Depends
        from uno.dependencies.fastapi_integration import inject_dependency
        
        # Patch the dependency injection in the router
        from unittest.mock import patch
        with patch('uno.caching.domain_endpoints.inject_dependency', lambda _: Depends(get_config_service)):
            app.include_router(router)
        
        return TestClient(app)
    
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
            fallback_on_error=True,
            local_config={"type": "memory", "max_size": 1000},
            distributed_config={"type": "redis", "host": "localhost"},
            invalidation_config={"time_based": True, "default_ttl": 300},
            monitoring_config={"enabled": True, "collect_latency": True},
            regions={"users": {"ttl": 600}, "products": {"ttl": 3600}}
        )
    
    def test_get_configuration(self, client, mock_service, sample_config):
        """Test getting the active configuration endpoint."""
        # Setup
        mock_service.get_active_configuration.return_value = Success(sample_config)
        
        # Execute
        response = client.get("/api/cache/configuration")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "config-1"
        assert response.json()["enabled"] is True
        assert response.json()["key_prefix"] == "app:"
        assert response.json()["use_hash_keys"] is True
        assert response.json()["hash_algorithm"] == "md5"
        assert response.json()["use_multi_level"] is True
        assert response.json()["fallback_on_error"] is True
        assert response.json()["local_config"] == {"type": "memory", "max_size": 1000}
        assert response.json()["distributed_config"] == {"type": "redis", "host": "localhost"}
        assert response.json()["invalidation_config"] == {"time_based": True, "default_ttl": 300}
        assert response.json()["monitoring_config"] == {"enabled": True, "collect_latency": True}
        assert response.json()["regions"] == {"users": {"ttl": 600}, "products": {"ttl": 3600}}
        mock_service.get_active_configuration.assert_called_once()
    
    def test_get_configuration_summary(self, client, mock_service, sample_config):
        """Test getting the configuration summary endpoint."""
        # Setup
        mock_service.get_active_configuration.return_value = Success(sample_config)
        
        # Execute
        response = client.get("/api/cache/configuration/summary")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "config-1"
        assert response.json()["enabled"] is True
        assert response.json()["use_multi_level"] is True
        assert response.json()["fallback_on_error"] is True
        assert response.json()["local_config"] == {"type": "memory", "max_size": 1000}
        assert response.json()["distributed_config"] == {"type": "redis", "host": "localhost"}
        assert response.json()["invalidation_config"] == {"time_based": True, "default_ttl": 300}
        assert response.json()["monitoring_config"] == {"enabled": True, "collect_latency": True}
        assert response.json()["regions_count"] == 2
        mock_service.get_active_configuration.assert_called_once()
    
    def test_update_configuration(self, client, mock_service, sample_config):
        """Test updating the configuration endpoint."""
        # Setup
        updated_config = sample_config
        updated_config.enabled = False
        mock_service.update_configuration.return_value = Success(updated_config)
        
        # Execute
        response = client.put(
            "/api/cache/configuration",
            json={
                "enabled": False
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "config-1"
        assert response.json()["enabled"] is False
        mock_service.update_configuration.assert_called_once()
    
    def test_enable_caching(self, client, mock_service, sample_config):
        """Test enabling caching endpoint."""
        # Setup
        mock_service.enable_caching.return_value = Success(sample_config)
        
        # Execute
        response = client.post("/api/cache/configuration/enable")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["enabled"] is True
        mock_service.enable_caching.assert_called_once()
    
    def test_disable_caching(self, client, mock_service, sample_config):
        """Test disabling caching endpoint."""
        # Setup
        disabled_config = sample_config
        disabled_config.enabled = False
        mock_service.disable_caching.return_value = Success(disabled_config)
        
        # Execute
        response = client.post("/api/cache/configuration/disable")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["enabled"] is False
        mock_service.disable_caching.assert_called_once()
    
    def test_add_region_config(self, client, mock_service, sample_config):
        """Test adding a region configuration endpoint."""
        # Setup
        updated_config = sample_config
        updated_config.regions["new-region"] = {"ttl": 900}
        mock_service.add_region_config.return_value = Success(updated_config)
        
        # Execute
        response = client.post(
            "/api/cache/configuration/regions/new-region",
            json={
                "config": {"ttl": 900}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert "new-region" in response.json()["regions"]
        assert response.json()["regions"]["new-region"] == {"ttl": 900}
        mock_service.add_region_config.assert_called_once()
    
    def test_remove_region_config(self, client, mock_service, sample_config):
        """Test removing a region configuration endpoint."""
        # Setup
        updated_config = sample_config
        updated_config.regions = {"products": {"ttl": 3600}}  # Remove "users" region
        mock_service.remove_region_config.return_value = Success(updated_config)
        
        # Execute
        response = client.delete("/api/cache/configuration/regions/users")
        
        # Assert
        assert response.status_code == 200
        assert "users" not in response.json()["regions"]
        assert "products" in response.json()["regions"]
        mock_service.remove_region_config.assert_called_once()