# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Health checking for the Uno application.

This module provides utilities for health checking, allowing services
to report their health status and clients to check service health.
"""

from typing import (
    Dict,
    List,
    Any,
    Optional,
    Callable,
    TypeVar,
    Generic,
    Union,
    Awaitable,
)
import asyncio
import time
import logging
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field

from fastapi import FastAPI, APIRouter, Response, status

from uno.core.resource_monitor import ResourceHealth, get_resource_monitor


T = TypeVar("T")


class HealthStatus(Enum):
    """Health status for a service or component."""

    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()

    @classmethod
    def from_resource_health(cls, health: ResourceHealth) -> "HealthStatus":
        """
        Convert ResourceHealth to HealthStatus.

        Args:
            health: ResourceHealth value

        Returns:
            Equivalent HealthStatus value
        """
        mapping = {
            ResourceHealth.HEALTHY: HealthStatus.HEALTHY,
            ResourceHealth.DEGRADED: HealthStatus.DEGRADED,
            ResourceHealth.UNHEALTHY: HealthStatus.UNHEALTHY,
            ResourceHealth.UNKNOWN: HealthStatus.UNKNOWN,
        }
        return mapping.get(health, HealthStatus.UNKNOWN)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    status: HealthStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result to a dictionary.

        Returns:
            Dictionary representation of the result
        """
        return {
            "status": self.status.name.lower(),
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class HealthCheck:
    """
    A health check for a service or component.

    Health checks are used to determine if a service is functioning correctly.
    """

    def __init__(
        self,
        name: str,
        check_func: Callable[[], Awaitable[HealthCheckResult]],
        timeout: float = 5.0,
        description: str | None = None,
        tags: list[str] | None = None,
    ):
        """
        Initialize a health check.

        Args:
            name: Name of the health check
            check_func: Async function that performs the check
            timeout: Timeout in seconds for the check
            description: Description of the check
            tags: Tags for categorizing the check
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.description = description
        self.tags = tags or []
        self.last_result: Optional[HealthCheckResult] = None
        self.last_check_time: float = 0
        self.lock = asyncio.Lock()

    async def check(self, force: bool = False) -> HealthCheckResult:
        """
        Perform the health check.

        Args:
            force: Whether to force a fresh check

        Returns:
            The health check result
        """
        async with self.lock:
            # Check if we have a recent result
            now = time.time()
            if not force and self.last_result and now - self.last_check_time < 60:
                return self.last_result

            # Perform the check with timeout
            try:
                result = await asyncio.wait_for(self.check_func(), self.timeout)
                self.last_result = result
                self.last_check_time = now
                return result

            except asyncio.TimeoutError:
                # Timeout counts as unhealthy
                result = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {self.timeout} seconds",
                    details={"timeout": self.timeout},
                )
                self.last_result = result
                self.last_check_time = now
                return result

            except Exception as e:
                # Any error counts as unhealthy
                result = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e)},
                )
                self.last_result = result
                self.last_check_time = now
                return result

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the health check to a dictionary.

        Returns:
            Dictionary representation of the health check
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "timeout": self.timeout,
            "last_check_time": self.last_check_time,
            "last_result": self.last_result.to_dict() if self.last_result else None,
        }


class HealthRegistry:
    """
    Registry for health checks.

    This class manages health checks and provides aggregated health status.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the health registry.

        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger(__name__)
        self._checks: dict[str, HealthCheck] = {}
        self._lock = asyncio.Lock()

    async def register(self, check: HealthCheck) -> None:
        """
        Register a health check.

        Args:
            check: The health check to register
        """
        async with self._lock:
            self._checks[check.id] = check
            self.logger.debug(f"Registered health check: {check.name}")

    async def unregister(self, check_id: str) -> None:
        """
        Unregister a health check.

        Args:
            check_id: ID of the check to unregister
        """
        async with self._lock:
            if check_id in self._checks:
                del self._checks[check_id]
                self.logger.debug(f"Unregistered health check: {check_id}")

    async def check_all(self, force: bool = False) -> dict[str, HealthCheckResult]:
        """
        Run all health checks.

        Args:
            force: Whether to force fresh checks

        Returns:
            Dictionary of check IDs to results
        """
        results = {}

        # Get a list of checks to avoid holding the lock during checks
        async with self._lock:
            checks = list(self._checks.values())

        # Run all checks concurrently
        tasks = [check.check(force) for check in checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for check, result in zip(checks, check_results):
            if isinstance(result, Exception):
                # Handle check failure
                results[check.id] = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                    details={"error": str(result)},
                )
            else:
                results[check.id] = result

        return results

    async def get_status(self, force: bool = False) -> HealthStatus:
        """
        Get the overall health status.

        This returns the worst status from all health checks.

        Args:
            force: Whether to force fresh checks

        Returns:
            Overall health status
        """
        results = await self.check_all(force)

        if not results:
            return HealthStatus.UNKNOWN

        # Count statuses
        counts = {status: 0 for status in HealthStatus}
        for result in results.values():
            counts[result.status] += 1

        # Determine overall status
        if counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif counts[HealthStatus.HEALTHY] > counts[HealthStatus.UNKNOWN]:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    async def get_health_report(self, force: bool = False) -> dict[str, Any]:
        """
        Get a health report.

        This includes overall status and individual check results.

        Args:
            force: Whether to force fresh checks

        Returns:
            Health report dictionary
        """
        results = await self.check_all(force)
        overall = await self.get_status(False)  # We already ran the checks

        # Organize results by status
        by_status = {status.name.lower(): [] for status in HealthStatus}

        for check_id, result in results.items():
            # Get the check info
            check = self._checks.get(check_id)
            if not check:
                continue

            # Add to the appropriate status group
            status_name = result.status.name.lower()
            by_status[status_name].append(
                {
                    "id": check_id,
                    "name": check.name,
                    "description": check.description,
                    "tags": check.tags,
                    "result": result.to_dict(),
                }
            )

        # Build the report
        return {
            "status": overall.name.lower(),
            "timestamp": time.time(),
            "checks_total": len(results),
            "checks_by_status": {
                status: len(checks) for status, checks in by_status.items()
            },
            "checks": by_status,
        }

    async def get_resource_health(self) -> dict[str, Any]:
        """
        Get health from resource monitor.

        This integrates with the resource monitoring system.

        Returns:
            Resource health report
        """
        try:
            monitor = get_resource_monitor()
            return await monitor.get_health_summary()
        except Exception as e:
            self.logger.error(f"Error getting resource health: {str(e)}")
            return {"overall_health": "UNKNOWN", "resource_count": 0, "error": str(e)}

    async def add_resource_checks(self) -> None:
        """
        Add health checks from resource monitor.

        This creates health checks for resources in the resource monitor.
        """
        try:
            monitor = get_resource_monitor()
            summary = await monitor.get_health_summary()

            for name, info in summary.get("resources", {}).items():
                # Create a health check for this resource
                check = HealthCheck(
                    name=f"resource:{name}",
                    check_func=self._create_resource_check(name),
                    description=f"Health check for resource: {name}",
                    tags=["resource", info.get("type", "").lower()],
                )

                await self.register(check)

        except Exception as e:
            self.logger.error(f"Error adding resource checks: {str(e)}")

    def _create_resource_check(
        self, resource_name: str
    ) -> Callable[[], Awaitable[HealthCheckResult]]:
        """
        Create a health check function for a resource.

        Args:
            resource_name: Name of the resource

        Returns:
            Async function that checks the resource health
        """

        async def check_resource() -> HealthCheckResult:
            try:
                # Get the resource health
                monitor = get_resource_monitor()
                health = await monitor.get_resource_health(resource_name)

                # Convert to HealthCheckResult
                return HealthCheckResult(
                    status=HealthStatus.from_resource_health(health),
                    message=f"Resource {resource_name} is {health.name.lower()}",
                    details={
                        "resource_name": resource_name,
                        "resource_health": health.name,
                    },
                )

            except Exception as e:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message=f"Failed to check resource {resource_name}: {str(e)}",
                    details={"resource_name": resource_name, "error": str(e)},
                )

        return check_resource


# Global health registry
health_registry: Optional[HealthRegistry] = None


def get_health_registry() -> HealthRegistry:
    """
    Get the global health registry.

    Returns:
        The global health registry
    """
    global health_registry
    if health_registry is None:
        health_registry = HealthRegistry()
    return health_registry


async def register_health_check(
    name: str,
    check_func: Callable[[], Awaitable[HealthCheckResult]],
    description: str | None = None,
    tags: list[str] | None = None,
    timeout: float = 5.0,
) -> str:
    """
    Register a health check.

    Args:
        name: Name of the health check
        check_func: Async function that performs the check
        description: Description of the check
        tags: Tags for categorizing the check
        timeout: Timeout in seconds for the check

    Returns:
        ID of the registered check
    """
    registry = get_health_registry()

    check = HealthCheck(
        name=name,
        check_func=check_func,
        description=description,
        tags=tags,
        timeout=timeout,
    )

    await registry.register(check)
    return check.id


async def get_health_status(force: bool = False) -> HealthStatus:
    """
    Get the overall health status.

    Args:
        force: Whether to force fresh checks

    Returns:
        Overall health status
    """
    registry = get_health_registry()
    return await registry.get_status(force)


class HealthEndpoint:
    """
    FastAPI integration for health checking.

    This class provides health check endpoints for a FastAPI application.
    """

    @staticmethod
    def create_router(
        prefix: str = "/health",
        tags: list[str] = ["health"],
        include_details: bool = True,
    ) -> APIRouter:
        """
        Create a router with health check endpoints.

        Args:
            prefix: URL prefix for endpoints
            tags: OpenAPI tags for endpoints
            include_details: Whether to include detailed endpoints

        Returns:
            APIRouter with health check endpoints
        """
        router = APIRouter(prefix=prefix, tags=tags)

        @router.get("", summary="Check service health")
        async def health_check(response: Response):
            """
            Check the health of the service.

            Returns a simple health status and sets the HTTP status code
            based on the health status.
            """
            registry = get_health_registry()
            status = await registry.get_status()

            # Set HTTP status code based on health status
            if status == HealthStatus.HEALTHY:
                response.status_code = status.HTTP_200_OK
            elif status == HealthStatus.DEGRADED:
                response.status_code = status.HTTP_200_OK  # Still usable
            else:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

            return {"status": status.name.lower()}

        if include_details:

            @router.get("/details", summary="Get detailed health report")
            async def health_details():
                """
                Get a detailed health report.

                Returns detailed information about all health checks.
                """
                registry = get_health_registry()
                return await registry.get_health_report()

            @router.get("/resources", summary="Get resource health")
            async def resource_health():
                """
                Get resource health.

                Returns health information from the resource monitor.
                """
                registry = get_health_registry()
                return await registry.get_resource_health()

        return router

    @staticmethod
    def setup(
        app: FastAPI,
        prefix: str = "/health",
        tags: list[str] = ["health"],
        include_details: bool = True,
        register_resource_checks: bool = True,
    ) -> None:
        """
        Set up health check endpoints for a FastAPI application.

        Args:
            app: FastAPI application
            prefix: URL prefix for endpoints
            tags: OpenAPI tags for endpoints
            include_details: Whether to include detailed endpoints
            register_resource_checks: Whether to register resource health checks
        """
        # Create and include the router
        router = HealthEndpoint.create_router(prefix, tags, include_details)
        app.include_router(router)

        # Register startup event to initialize health checks
        @app.on_event("startup")
        async def startup_health_checks():
            if register_resource_checks:
                registry = get_health_registry()
                await registry.add_resource_checks()
