"""
Unit tests for the health check framework.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from uno.core.health.framework import (
    HealthStatus, HealthCheckResult, HealthCheck, HealthRegistry,
    health_check, register_health_check, get_health_registry, HealthConfig
)


@pytest.fixture
def mock_health_check():
    """Create a mock health check."""
    async def check_func():
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Test check passed"
        )

    return HealthCheck(
        name="test_check",
        check_func=check_func,
        description="Test health check",
        tags=["test"],
        critical=False,
        group="test"
    )


@pytest.fixture
def health_registry():
    """Create a health registry."""
    return HealthRegistry()


class TestHealthStatus:
    """Tests for the HealthStatus enum."""

    def test_from_resource_health(self):
        """Test conversion from ResourceHealth to HealthStatus."""
        from uno.core.health.framework import ResourceHealth

        # Test all mappings
        assert HealthStatus.from_resource_health(ResourceHealth.HEALTHY) == HealthStatus.HEALTHY
        assert HealthStatus.from_resource_health(ResourceHealth.DEGRADED) == HealthStatus.DEGRADED
        assert HealthStatus.from_resource_health(ResourceHealth.UNHEALTHY) == HealthStatus.UNHEALTHY
        assert HealthStatus.from_resource_health(ResourceHealth.UNKNOWN) == HealthStatus.UNKNOWN

    def test_http_status(self):
        """Test HTTP status code mapping."""
        from fastapi import status

        # Test all mappings
        assert HealthStatus.HEALTHY.http_status == status.HTTP_200_OK
        assert HealthStatus.DEGRADED.http_status == status.HTTP_200_OK
        assert HealthStatus.UNHEALTHY.http_status == status.HTTP_503_SERVICE_UNAVAILABLE
        assert HealthStatus.UNKNOWN.http_status == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestHealthCheckResult:
    """Tests for the HealthCheckResult class."""

    def test_initialization(self):
        """Test initialization with default values."""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Test message"
        )

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test message"
        assert isinstance(result.details, dict)
        assert isinstance(result.timestamp, float)
        assert result.check_duration_ms is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Test message",
            details={"key": "value"},
            timestamp=1234567890.0,
            check_duration_ms=123.45
        )

        result_dict = result.to_dict()
        assert result_dict["status"] == "healthy"
        assert result_dict["message"] == "Test message"
        assert result_dict["details"] == {"key": "value"}
        assert result_dict["timestamp"] == 1234567890.0
        assert result_dict["check_duration_ms"] == 123.45


class TestHealthCheck:
    """Tests for the HealthCheck class."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_health_check):
        """Test initialization."""
        assert mock_health_check.name == "test_check"
        assert mock_health_check.description == "Test health check"
        assert mock_health_check.tags == ["test"]
        assert mock_health_check.critical is False
        assert mock_health_check.group == "test"
        assert mock_health_check.last_result is None
        assert mock_health_check.last_check_time == 0

    @pytest.mark.asyncio
    async def test_check(self, mock_health_check):
        """Test performing a health check."""
        result = await mock_health_check.check()
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test check passed"
        assert mock_health_check.last_result == result
        assert mock_health_check.last_check_time > 0

    @pytest.mark.asyncio
    async def test_check_caching(self, mock_health_check):
        """Test that health check results are cached."""
        # First check
        result1 = await mock_health_check.check()
        check_time = mock_health_check.last_check_time

        # Second check (should use cached result)
        result2 = await mock_health_check.check()
        assert result2 is result1
        assert mock_health_check.last_check_time == check_time

        # Force refresh
        result3 = await mock_health_check.check(force=True)
        assert result3 is not result1
        assert mock_health_check.last_check_time > check_time

    @pytest.mark.asyncio
    async def test_check_timeout(self):
        """Test health check timeout."""
        async def slow_check():
            await asyncio.sleep(0.2)
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Slow check passed"
            )

        check = HealthCheck(
            name="slow_check",
            check_func=slow_check,
            timeout=0.1
        )

        result = await check.check()
        assert result.status == HealthStatus.UNHEALTHY
        assert "timed out" in result.message

    @pytest.mark.asyncio
    async def test_check_error(self):
        """Test health check error handling."""
        async def error_check():
            raise ValueError("Test error")

        check = HealthCheck(
            name="error_check",
            check_func=error_check
        )

        result = await check.check()
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test error" in result.message
        assert "error" in result.details

    def test_to_dict(self, mock_health_check):
        """Test conversion to dictionary."""
        # First perform a check to have a last_result
        asyncio.run(mock_health_check.check())

        # Convert to dict
        check_dict = mock_health_check.to_dict()
        assert check_dict["id"] == mock_health_check.id
        assert check_dict["name"] == "test_check"
        assert check_dict["description"] == "Test health check"
        assert check_dict["tags"] == ["test"]
        assert check_dict["critical"] is False
        assert check_dict["group"] == "test"
        assert "last_result" in check_dict
        assert check_dict["last_check_time"] > 0


class TestHealthRegistry:
    """Tests for the HealthRegistry class."""

    @pytest.mark.asyncio
    async def test_register(self, health_registry, mock_health_check):
        """Test registering a health check."""
        await health_registry.register(mock_health_check)
        assert mock_health_check.id in health_registry._checks

        # Check that it was added to the correct group
        assert "test" in health_registry._groups
        assert mock_health_check.id in health_registry._groups["test"]

    @pytest.mark.asyncio
    async def test_unregister(self, health_registry, mock_health_check):
        """Test unregistering a health check."""
        await health_registry.register(mock_health_check)
        await health_registry.unregister(mock_health_check.id)

        assert mock_health_check.id not in health_registry._checks
        assert "test" not in health_registry._groups

    @pytest.mark.asyncio
    async def test_check_all(self, health_registry, mock_health_check):
        """Test running all health checks."""
        await health_registry.register(mock_health_check)
        results = await health_registry.check_all()

        assert mock_health_check.id in results
        assert results[mock_health_check.id].status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_group(self, health_registry, mock_health_check):
        """Test running health checks for a specific group."""
        await health_registry.register(mock_health_check)

        # Add another check in a different group
        async def other_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Other check passed"
            )

        other = HealthCheck(
            name="other_check",
            check_func=other_check,
            group="other"
        )
        await health_registry.register(other)

        # Check only the test group
        results = await health_registry.check_group("test")
        assert len(results) == 1
        assert mock_health_check.id in results
        assert other.id not in results

    @pytest.mark.asyncio
    async def test_get_status(self, health_registry, mock_health_check):
        """Test getting overall health status."""
        await health_registry.register(mock_health_check)
        status = await health_registry.get_status()
        assert status == HealthStatus.HEALTHY

        # Add an unhealthy check
        async def unhealthy_check():
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Unhealthy check"
            )

        unhealthy = HealthCheck(
            name="unhealthy_check",
            check_func=unhealthy_check
        )
        await health_registry.register(unhealthy)

        # Status should now be unhealthy
        status = await health_registry.get_status()
        assert status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_group_status(self, health_registry, mock_health_check):
        """Test getting health status for a specific group."""
        await health_registry.register(mock_health_check)

        # Add a degraded check in the same group
        async def degraded_check():
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message="Degraded check"
            )

        degraded = HealthCheck(
            name="degraded_check",
            check_func=degraded_check,
            group="test"
        )
        await health_registry.register(degraded)

        # Group status should be degraded (worst status)
        status = await health_registry.get_group_status("test")
        assert status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_get_health_report(self, health_registry, mock_health_check):
        """Test getting a health report."""
        await health_registry.register(mock_health_check)
        report = await health_registry.get_health_report()

        assert report["status"] == "healthy"
        assert report["checks_total"] == 1
        assert report["checks_by_status"]["healthy"] == 1
        assert len(report["checks"]["healthy"]) == 1
        assert report["checks"]["healthy"][0]["name"] == "test_check"

        # Check groups in report
        assert len(report["groups"]) == 1
        assert report["groups"][0]["name"] == "test"
        assert report["groups"][0]["status"] == "healthy"
        assert len(report["groups"][0]["checks"]) == 1


class TestHelperFunctions:
    """Tests for helper functions."""

    @pytest.mark.asyncio
    async def test_register_health_check(self):
        """Test registering a health check."""
        # Create a mock check function
        async def check_func():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Test check passed"
            )

        # Clear global registry for test
        from uno.core.health.framework import _health_registry
        _health_registry = None

        # Register the check
        check_id = await register_health_check(
            name="test_check",
            check_func=check_func,
            description="Test health check",
            tags=["test"],
            timeout=5.0
        )

        # Get the registry and verify
        registry = get_health_registry()
        assert check_id in registry._checks
        assert registry._checks[check_id].name == "test_check"

    @pytest.mark.asyncio
    async def test_health_check_decorator():
        """Test health check decorator."""
        # Clear global registry for test
        from uno.core.health.framework import _health_registry
        _health_registry = None

        # Define a check function with the decorator
        @health_check(
            name="decorated_check",
            description="Decorated health check",
            tags=["test"],
            critical=True,
            group="test"
        )
        async def decorated_check():
            return True

        # Run the check to ensure it's registered
        await decorated_check()

        # Check that it was registered
        registry = get_health_registry()
        checks = list(registry._checks.values())
        
        # Find our check by name
        check = next((c for c in checks if c.name == "decorated_check"), None)
        assert check is not None
        assert check.description == "Decorated health check"
        assert check.tags == ["test"]
        assert check.critical is True
        assert check.group == "test"


class TestHealthEndpoint:
    """Tests for the HealthEndpoint class."""

    def test_create_router(self):
        """Test creating a router with health check endpoints."""
        from uno.core.health.framework import HealthEndpoint
        from fastapi import APIRouter

        router = HealthEndpoint.create_router(
            prefix="/health",
            tags=["health"],
            include_details=True
        )

        assert isinstance(router, APIRouter)
        assert router.prefix == "/health"
        assert router.tags == ["health"]

        # Check that routes were created
        route_paths = [route.path for route in router.routes]
        assert "" in route_paths  # Main health check endpoint
        assert "/details" in route_paths  # Detailed health check endpoint
        assert "/resources" in route_paths  # Resource health endpoint
        assert "/groups/{group}" in route_paths  # Group health endpoint
        assert "/groups" in route_paths  # List groups endpoint

    def test_create_router_without_details(self):
        """Test creating a router without detailed endpoints."""
        from uno.core.health.framework import HealthEndpoint
        from fastapi import APIRouter

        router = HealthEndpoint.create_router(
            prefix="/health",
            tags=["health"],
            include_details=False
        )

        assert isinstance(router, APIRouter)
        
        # Check that detailed routes were not created
        route_paths = [route.path for route in router.routes]
        assert "" in route_paths  # Main health check endpoint
        assert "/details" not in route_paths  # No detailed endpoint
        assert "/resources" not in route_paths  # No resource endpoint
        assert "/groups/{group}" not in route_paths  # No group endpoint
        assert "/groups" not in route_paths  # No list groups endpoint