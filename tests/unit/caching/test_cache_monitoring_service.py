"""
Tests for the CacheMonitoringService in the Caching module.

This module contains comprehensive tests for the CacheMonitoringService, which handles
cache statistics, operation tracking, and health monitoring.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional

from uno.core.result import Result, Success, Failure

from uno.caching.entities import (
    CacheKeyId,
    CacheRegionId,
    CacheProviderId,
    CacheStatsType,
    CacheStatistic,
    CacheOperation,
    CacheHealth
)

from uno.caching.domain_repositories import (
    CacheStatisticRepositoryProtocol,
    CacheProviderRepositoryProtocol,
    CacheRegionRepositoryProtocol
)

from uno.caching.domain_services import CacheMonitoringService


# Test constants
TEST_PROVIDER_ID = "test-provider-id"
TEST_REGION_ID = "test-region"
TEST_KEY = "test-key"


class TestCacheMonitoringService:
    """Tests for the CacheMonitoringService."""
    
    @pytest.fixture
    def mock_statistic_repository(self):
        """Create a mock statistic repository for testing."""
        repository = AsyncMock(spec=CacheStatisticRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def mock_provider_repository(self):
        """Create a mock provider repository for testing."""
        repository = AsyncMock(spec=CacheProviderRepositoryProtocol)
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        
        # Set up the get method to return success for the test provider
        repository.get.return_value = Success(MagicMock(id=provider_id))
        
        return repository
    
    @pytest.fixture
    def mock_region_repository(self):
        """Create a mock region repository for testing."""
        repository = AsyncMock(spec=CacheRegionRepositoryProtocol)
        region_id = CacheRegionId(TEST_REGION_ID)
        
        # Set up the get method to return success for the test region
        repository.get.return_value = Success(MagicMock(id=region_id))
        
        return repository
    
    @pytest.fixture
    def service(self, mock_statistic_repository, mock_provider_repository, mock_region_repository):
        """Create a service with mock repositories for testing."""
        return CacheMonitoringService(
            statistic_repository=mock_statistic_repository,
            provider_repository=mock_provider_repository,
            region_repository=mock_region_repository
        )
    
    @pytest.mark.asyncio
    async def test_record_statistic(self, service, mock_statistic_repository):
        """Test recording a cache statistic."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        stat_type = CacheStatsType.HIT_RATE
        value = 0.85
        metadata = {"source": "test"}
        
        statistic = CacheStatistic(
            provider_id=provider_id,
            stat_type=stat_type,
            value=value,
            metadata=metadata
        )
        
        mock_statistic_repository.save.return_value = Success(statistic)
        
        # Execute
        result = await service.record_statistic(
            provider_id=provider_id,
            stat_type=stat_type,
            value=value,
            metadata=metadata
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.provider_id == provider_id
        assert result.value.stat_type == stat_type
        assert result.value.value == value
        assert result.value.metadata == metadata
        mock_statistic_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_statistic_with_region(self, service, mock_statistic_repository):
        """Test recording a cache statistic with a region."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        region_id = CacheRegionId(TEST_REGION_ID)
        stat_type = CacheStatsType.HIT_RATE
        value = 0.85
        metadata = {"source": "test"}
        
        statistic = CacheStatistic(
            provider_id=provider_id,
            stat_type=stat_type,
            value=value,
            region=region_id,
            metadata=metadata
        )
        
        mock_statistic_repository.save.return_value = Success(statistic)
        
        # Execute
        result = await service.record_statistic(
            provider_id=provider_id,
            stat_type=stat_type,
            value=value,
            region=region_id,
            metadata=metadata
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.provider_id == provider_id
        assert result.value.stat_type == stat_type
        assert result.value.value == value
        assert result.value.region == region_id
        assert result.value.metadata == metadata
        mock_statistic_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_operation(self, service, mock_provider_repository):
        """Test recording a cache operation."""
        # Setup
        key_id = CacheKeyId(TEST_KEY)
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        operation_type = "get"
        duration_ms = 5.2
        metadata = {"source": "test"}
        
        # Execute
        result = await service.record_operation(
            key=key_id,
            provider_id=provider_id,
            operation_type=operation_type,
            duration_ms=duration_ms,
            metadata=metadata
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.key == key_id
        assert result.value.provider_id == provider_id
        assert result.value.operation_type == operation_type
        assert result.value.duration_ms == duration_ms
        assert result.value.success is True
        assert result.value.metadata == metadata
        mock_provider_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_failed_operation(self, service, mock_provider_repository):
        """Test recording a failed cache operation."""
        # Setup
        key_id = CacheKeyId(TEST_KEY)
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        operation_type = "get"
        duration_ms = 5.2
        error_message = "Cache miss"
        metadata = {"source": "test"}
        
        # Execute
        result = await service.record_operation(
            key=key_id,
            provider_id=provider_id,
            operation_type=operation_type,
            duration_ms=duration_ms,
            success=False,
            error_message=error_message,
            metadata=metadata
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.key == key_id
        assert result.value.provider_id == provider_id
        assert result.value.operation_type == operation_type
        assert result.value.duration_ms == duration_ms
        assert result.value.success is False
        assert result.value.error_message == error_message
        assert result.value.metadata == metadata
        mock_provider_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_health_check(self, service, mock_provider_repository):
        """Test recording a cache health check."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        is_healthy = True
        latency_ms = 5.2
        details = {"memory_usage": "10%"}
        
        # Execute
        result = await service.record_health_check(
            provider_id=provider_id,
            is_healthy=is_healthy,
            latency_ms=latency_ms,
            details=details
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.provider_id == provider_id
        assert result.value.is_healthy is True
        assert result.value.latency_ms == latency_ms
        assert result.value.details == details
        mock_provider_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_unhealthy_check(self, service, mock_provider_repository):
        """Test recording an unhealthy cache health check."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        is_healthy = False
        latency_ms = 500.0
        error_message = "Connection timeout"
        details = {"error_type": "timeout"}
        
        # Execute
        result = await service.record_health_check(
            provider_id=provider_id,
            is_healthy=is_healthy,
            latency_ms=latency_ms,
            error_message=error_message,
            details=details
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.provider_id == provider_id
        assert result.value.is_healthy is False
        assert result.value.latency_ms == latency_ms
        assert result.value.error_message == error_message
        assert result.value.details == details
        mock_provider_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_provider_statistics(self, service, mock_statistic_repository):
        """Test getting provider statistics."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        start_time = datetime.now(UTC) - timedelta(days=1)
        end_time = datetime.now(UTC)
        limit = 50
        
        statistics = [
            CacheStatistic(
                provider_id=provider_id,
                stat_type=CacheStatsType.HIT_RATE,
                value=0.85
            ),
            CacheStatistic(
                provider_id=provider_id,
                stat_type=CacheStatsType.MISS_RATE,
                value=0.15
            )
        ]
        
        mock_statistic_repository.get_for_provider.return_value = Success(statistics)
        
        # Execute
        result = await service.get_provider_statistics(
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].provider_id == provider_id
        assert result.value[0].stat_type == CacheStatsType.HIT_RATE
        assert result.value[1].stat_type == CacheStatsType.MISS_RATE
        mock_statistic_repository.get_for_provider.assert_called_once_with(
            provider_id, None, start_time, end_time, limit
        )
    
    @pytest.mark.asyncio
    async def test_get_region_statistics(self, service, mock_statistic_repository):
        """Test getting region statistics."""
        # Setup
        region_id = CacheRegionId(TEST_REGION_ID)
        start_time = datetime.now(UTC) - timedelta(days=1)
        end_time = datetime.now(UTC)
        limit = 50
        
        statistics = [
            CacheStatistic(
                provider_id=CacheProviderId(TEST_PROVIDER_ID),
                region=region_id,
                stat_type=CacheStatsType.HIT_RATE,
                value=0.85
            ),
            CacheStatistic(
                provider_id=CacheProviderId(TEST_PROVIDER_ID),
                region=region_id,
                stat_type=CacheStatsType.MISS_RATE,
                value=0.15
            )
        ]
        
        mock_statistic_repository.get_for_region.return_value = Success(statistics)
        
        # Execute
        result = await service.get_region_statistics(
            region_id=region_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].region == region_id
        assert result.value[0].stat_type == CacheStatsType.HIT_RATE
        assert result.value[1].stat_type == CacheStatsType.MISS_RATE
        mock_statistic_repository.get_for_region.assert_called_once_with(
            region_id, None, start_time, end_time, limit
        )
    
    @pytest.mark.asyncio
    async def test_get_provider_summary(self, service, mock_statistic_repository):
        """Test getting provider summary."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        start_time = datetime.now(UTC) - timedelta(days=1)
        end_time = datetime.now(UTC)
        
        summary = {
            "hit_rate": 0.85,
            "miss_rate": 0.15,
            "avg_latency_ms": 3.2,
            "max_latency_ms": 15.7,
            "total_requests": 1000
        }
        
        mock_statistic_repository.summarize_by_provider.return_value = Success(summary)
        
        # Execute
        result = await service.get_provider_summary(
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value["hit_rate"] == 0.85
        assert result.value["miss_rate"] == 0.15
        assert result.value["avg_latency_ms"] == 3.2
        assert result.value["max_latency_ms"] == 15.7
        assert result.value["total_requests"] == 1000
        mock_statistic_repository.summarize_by_provider.assert_called_once_with(
            provider_id, start_time, end_time
        )
    
    @pytest.mark.asyncio
    async def test_get_health_history(self, service):
        """Test getting health check history."""
        # Setup
        provider_id = CacheProviderId(TEST_PROVIDER_ID)
        start_time = datetime.now(UTC) - timedelta(days=1)
        end_time = datetime.now(UTC)
        limit = 50
        
        # Add some health checks to the service's internal list
        health_check1 = CacheHealth(
            provider_id=provider_id,
            is_healthy=True,
            latency_ms=5.2,
            timestamp=start_time + timedelta(hours=1),
            details={"memory_usage": "10%"}
        )
        
        health_check2 = CacheHealth(
            provider_id=provider_id,
            is_healthy=False,
            latency_ms=500.0,
            timestamp=start_time + timedelta(hours=2),
            error_message="Connection timeout",
            details={"error_type": "timeout"}
        )
        
        # Add health checks to the service
        service.health_checks = [health_check1, health_check2]
        
        # Execute
        result = await service.get_health_history(
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        # Newest first
        assert result.value[0].timestamp == health_check2.timestamp
        assert result.value[1].timestamp == health_check1.timestamp
        assert result.value[0].is_healthy is False
        assert result.value[1].is_healthy is True