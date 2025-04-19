# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Health check framework for the Uno application.

This module provides a comprehensive health check system for monitoring
application components, services, dependencies, and resources. It includes:

1. Health status tracking for services and components
2. Customizable health check registration and execution
3. Health check aggregation with different check types 
4. FastAPI integration for health check endpoints
5. Integration with resource monitoring system
6. Context propagation for health check data
"""

from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic, Union, Awaitable, Set
import asyncio
import time
import logging
import uuid
import datetime
import contextvars
import json
from enum import Enum, auto
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path

from fastapi import FastAPI, APIRouter, Response, status, Request
from pydantic import BaseModel, Field, ConfigDict

from uno.core.errors import Result, Error, ErrorCatalog, ErrorContext
from uno.core.logging import get_logger

# Type variables
T = TypeVar('T')

# Context variables for health information
health_context = contextvars.ContextVar("health_context", default={})


class ResourceHealth(Enum):
    """Health status for a resource."""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


class HealthStatus(Enum):
    """Health status for a service or component."""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()
    
    @classmethod
    def from_resource_health(cls, health: ResourceHealth) -> 'HealthStatus':
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
            ResourceHealth.UNKNOWN: HealthStatus.UNKNOWN
        }
        return mapping.get(health, HealthStatus.UNKNOWN)

    @property
    def http_status(self) -> int:
        """
        Get the corresponding HTTP status code.
        
        Returns:
            HTTP status code
        """
        mapping = {
            HealthStatus.HEALTHY: status.HTTP_200_OK,
            HealthStatus.DEGRADED: status.HTTP_200_OK,  # Still usable
            HealthStatus.UNHEALTHY: status.HTTP_503_SERVICE_UNAVAILABLE,
            HealthStatus.UNKNOWN: status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        return mapping.get(self, status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthCheckResult(BaseModel):
    """Result of a health check."""
    status: HealthStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    check_duration_ms: Optional[float] = None
    
    model_config = ConfigDict(
        use_enum_values=False,
        json_encoders={
            HealthStatus: lambda v: v.name.lower(),
            datetime.datetime: lambda v: v.isoformat(),
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary.
        
        Returns:
            Dictionary representation of the result
        """
        result = self.model_dump()
        result["status"] = self.status.name.lower()
        return result


class HealthConfig(BaseModel):
    """Configuration for health checks."""
    enabled: bool = True
    path_prefix: str = "/health"
    tags: List[str] = Field(default_factory=lambda: ["health"])
    include_details: bool = True
    register_resource_checks: bool = True
    cache_ttl: int = 60  # seconds
    check_timeout: float = 5.0  # seconds
    include_in_context: bool = True
    alerting_enabled: bool = True
    dashboard_enabled: bool = True
    log_health_checks: bool = True


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
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        critical: bool = False,
        group: Optional[str] = None,
    ):
        """
        Initialize a health check.
        
        Args:
            name: Name of the health check
            check_func: Async function that performs the check
            timeout: Timeout in seconds for the check
            description: Description of the check
            tags: Tags for categorizing the check
            critical: Whether this check is critical for system health
            group: Group name for organizing related checks
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.description = description
        self.tags = tags or []
        self.critical = critical
        self.group = group
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
            start_time = time.perf_counter()
            try:
                result = await asyncio.wait_for(self.check_func(), self.timeout)
                
                # Add check duration if not already present
                if result.check_duration_ms is None:
                    result.check_duration_ms = (time.perf_counter() - start_time) * 1000
                    
                self.last_result = result
                self.last_check_time = now
                return result
            
            except asyncio.TimeoutError:
                # Timeout counts as unhealthy
                duration_ms = (time.perf_counter() - start_time) * 1000
                result = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {self.timeout} seconds",
                    details={"timeout": self.timeout},
                    check_duration_ms=duration_ms
                )
                self.last_result = result
                self.last_check_time = now
                return result
            
            except Exception as e:
                # Any error counts as unhealthy
                duration_ms = (time.perf_counter() - start_time) * 1000
                result = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e)},
                    check_duration_ms=duration_ms
                )
                self.last_result = result
                self.last_check_time = now
                return result
    
    def to_dict(self) -> Dict[str, Any]:
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
            "critical": self.critical,
            "group": self.group,
            "timeout": self.timeout,
            "last_check_time": self.last_check_time,
            "last_result": self.last_result.to_dict() if self.last_result else None
        }


class HealthRegistry:
    """
    Registry for health checks.
    
    This class manages health checks and provides aggregated health status.
    """
    
    def __init__(
        self, 
        config: Optional[HealthConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the health registry.
        
        Args:
            config: Health configuration
            logger: Logger to use
        """
        self.config = config or HealthConfig()
        self.logger = logger or get_logger("uno.health")
        self._checks: Dict[str, HealthCheck] = {}
        self._groups: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            check: The health check to register
        """
        async with self._lock:
            self._checks[check.id] = check
            
            # Add to group if specified
            if check.group:
                if check.group not in self._groups:
                    self._groups[check.group] = set()
                self._groups[check.group].add(check.id)
                
            self.logger.debug(f"Registered health check: {check.name}")
    
    async def unregister(self, check_id: str) -> None:
        """
        Unregister a health check.
        
        Args:
            check_id: ID of the check to unregister
        """
        async with self._lock:
            if check_id in self._checks:
                check = self._checks[check_id]
                
                # Remove from group if needed
                if check.group and check.group in self._groups:
                    self._groups[check.group].discard(check_id)
                    if not self._groups[check.group]:
                        del self._groups[check.group]
                
                # Remove check
                del self._checks[check_id]
                self.logger.debug(f"Unregistered health check: {check_id}")
    
    async def check_all(self, force: bool = False) -> Dict[str, HealthCheckResult]:
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
                    details={"error": str(result)}
                )
            else:
                results[check.id] = result
                
                # Log health check results if configured
                if self.config.log_health_checks:
                    status_name = result.status.name
                    if status_name != "HEALTHY":
                        log_level = logging.WARNING if status_name == "DEGRADED" else logging.ERROR
                        self.logger.log(
                            log_level, 
                            f"Health check '{check.name}' is {status_name.lower()}: {result.message}"
                        )
        
        # Update context if enabled
        if self.config.include_in_context:
            context = health_context.get()
            context["health_status"] = await self.get_status(False)
            context["health_checks"] = len(results)
            context["health_timestamp"] = time.time()
            health_context.set(context)
        
        return results
    
    async def check_group(self, group: str, force: bool = False) -> Dict[str, HealthCheckResult]:
        """
        Run health checks for a specific group.
        
        Args:
            group: The group name to check
            force: Whether to force fresh checks
            
        Returns:
            Dictionary of check IDs to results
        """
        results = {}
        
        # Get a list of checks for this group
        async with self._lock:
            check_ids = self._groups.get(group, set())
            checks = [self._checks[check_id] for check_id in check_ids if check_id in self._checks]
        
        # Run checks concurrently
        tasks = [check.check(force) for check in checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for check, result in zip(checks, check_results):
            if isinstance(result, Exception):
                # Handle check failure
                results[check.id] = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                    details={"error": str(result)}
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
    
    async def get_group_status(self, group: str, force: bool = False) -> HealthStatus:
        """
        Get health status for a specific group.
        
        Args:
            group: The group name to check
            force: Whether to force fresh checks
            
        Returns:
            Group health status
        """
        results = await self.check_group(group, force)
        
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
    
    async def get_health_report(self, force: bool = False) -> Dict[str, Any]:
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
        
        # Group results by group
        groups = {}
        
        for check_id, result in results.items():
            # Get the check info
            check = self._checks.get(check_id)
            if not check:
                continue
            
            # Add to the appropriate status group
            status_name = result.status.name.lower()
            check_info = {
                "id": check_id,
                "name": check.name,
                "description": check.description,
                "tags": check.tags,
                "critical": check.critical,
                "group": check.group,
                "result": result.to_dict()
            }
            
            by_status[status_name].append(check_info)
            
            # Add to group
            if check.group:
                if check.group not in groups:
                    groups[check.group] = {
                        "name": check.group,
                        "checks": [],
                        "status": "unknown",
                        "critical_checks": 0,
                        "unhealthy_checks": 0,
                        "healthy_checks": 0,
                        "degraded_checks": 0,
                        "unknown_checks": 0,
                    }
                
                groups[check.group]["checks"].append(check_info)
                groups[check.group][f"{status_name}_checks"] += 1
                
                if check.critical:
                    groups[check.group]["critical_checks"] += 1
        
        # Update group statuses
        for group_name, group_info in groups.items():
            if group_info["unhealthy_checks"] > 0:
                group_info["status"] = "unhealthy"
            elif group_info["degraded_checks"] > 0:
                group_info["status"] = "degraded"
            elif group_info["healthy_checks"] > group_info["unknown_checks"]:
                group_info["status"] = "healthy"
            else:
                group_info["status"] = "unknown"
        
        # Build the report
        return {
            "status": overall.name.lower(),
            "timestamp": time.time(),
            "checks_total": len(results),
            "checks_by_status": {
                status: len(checks) for status, checks in by_status.items()
            },
            "checks": by_status,
            "groups": list(groups.values()) if groups else []
        }
    
    async def get_resource_health(self) -> Dict[str, Any]:
        """
        Get health from resource monitor.
        
        This integrates with the resource monitoring system.
        
        Returns:
            Resource health report
        """
        try:
            # Import here to avoid circular imports
            from uno.core.resources import get_resource_monitor
            monitor = get_resource_monitor()
            return await monitor.get_health_summary()
        except Exception as e:
            self.logger.error(f"Error getting resource health: {str(e)}")
            return {
                "overall_health": "UNKNOWN",
                "resource_count": 0,
                "error": str(e)
            }
    
    async def add_resource_checks(self) -> None:
        """
        Add health checks from resource monitor.
        
        This creates health checks for resources in the resource monitor.
        """
        try:
            # Import here to avoid circular imports
            from uno.core.resources import get_resource_monitor
            monitor = get_resource_monitor()
            summary = await monitor.get_health_summary()
            
            for name, info in summary.get("resources", {}).items():
                # Create a health check for this resource
                check = HealthCheck(
                    name=f"resource:{name}",
                    check_func=self._create_resource_check(name),
                    description=f"Health check for resource: {name}",
                    tags=["resource", info.get("type", "").lower()],
                    group="resources"
                )
                
                await self.register(check)
        
        except Exception as e:
            self.logger.error(f"Error adding resource checks: {str(e)}")
    
    def _create_resource_check(
        self,
        resource_name: str
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
                # Import here to avoid circular imports
                from uno.core.resources import get_resource_monitor
                
                # Get the resource health
                monitor = get_resource_monitor()
                health = await monitor.get_resource_health(resource_name)
                
                # Convert to HealthCheckResult
                return HealthCheckResult(
                    status=HealthStatus.from_resource_health(health),
                    message=f"Resource {resource_name} is {health.name.lower()}",
                    details={"resource_name": resource_name, "resource_health": health.name}
                )
            
            except Exception as e:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message=f"Failed to check resource {resource_name}: {str(e)}",
                    details={"resource_name": resource_name, "error": str(e)}
                )
        
        return check_resource


# Global health registry and its access function
_health_registry: Optional[HealthRegistry] = None


def get_health_registry() -> HealthRegistry:
    """
    Get the global health registry.
    
    Returns:
        The global health registry
    """
    global _health_registry
    if _health_registry is None:
        _health_registry = HealthRegistry()
    return _health_registry


async def register_health_check(
    name: str,
    check_func: Callable[[], Awaitable[HealthCheckResult]],
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    timeout: float = 5.0,
    critical: bool = False,
    group: Optional[str] = None,
) -> str:
    """
    Register a health check.
    
    Args:
        name: Name of the health check
        check_func: Async function that performs the check
        description: Description of the check
        tags: Tags for categorizing the check
        timeout: Timeout in seconds for the check
        critical: Whether this check is critical for system health
        group: Group name for organizing related checks
        
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
        critical=critical,
        group=group
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


def health_check(
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    timeout: float = 5.0,
    critical: bool = False,
    group: Optional[str] = None,
):
    """
    Decorator for health check functions.
    
    This decorator registers an async function as a health check.
    
    Args:
        name: Name of the health check (defaults to function name)
        description: Description of the check
        tags: Tags for categorizing the check
        timeout: Timeout in seconds for the check
        critical: Whether this check is critical for system health
        group: Group name for organizing related checks
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Create a wrapper that adapts the function to return HealthCheckResult
        @wraps(func)
        async def wrapper() -> HealthCheckResult:
            start_time = time.perf_counter()
            try:
                # Call the original function
                result = await func()
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Handle different return types
                if isinstance(result, HealthCheckResult):
                    # Function already returns HealthCheckResult
                    if result.check_duration_ms is None:
                        result.check_duration_ms = duration_ms
                    return result
                elif isinstance(result, dict):
                    # Function returns a dict, convert to HealthCheckResult
                    status = result.get("status", HealthStatus.UNKNOWN)
                    if isinstance(status, str):
                        try:
                            status = HealthStatus[status.upper()]
                        except KeyError:
                            status = HealthStatus.UNKNOWN
                    
                    return HealthCheckResult(
                        status=status,
                        message=result.get("message", "Health check completed"),
                        details=result.get("details", {}),
                        check_duration_ms=duration_ms
                    )
                elif isinstance(result, bool):
                    # Function returns a boolean, convert to HealthCheckResult
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    message = "Health check passed" if result else "Health check failed"
                    
                    return HealthCheckResult(
                        status=status,
                        message=message,
                        check_duration_ms=duration_ms
                    )
                elif isinstance(result, tuple) and len(result) == 2:
                    # Function returns a tuple of (bool, message)
                    status = HealthStatus.HEALTHY if result[0] else HealthStatus.UNHEALTHY
                    
                    return HealthCheckResult(
                        status=status,
                        message=result[1],
                        check_duration_ms=duration_ms
                    )
                elif isinstance(result, Result):
                    # Function returns a Result object
                    if result.is_failure:
                        error = result.error
                        return HealthCheckResult(
                            status=HealthStatus.UNHEALTHY,
                            message=str(error),
                            details={"error": error.as_dict() if hasattr(error, "as_dict") else str(error)},
                            check_duration_ms=duration_ms
                        )
                    else:
                        value = result.value
                        message = "Health check passed"
                        if isinstance(value, str):
                            message = value
                        
                        return HealthCheckResult(
                            status=HealthStatus.HEALTHY,
                            message=message,
                            check_duration_ms=duration_ms
                        )
                else:
                    # Function returns something else, assume success
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        message="Health check passed",
                        check_duration_ms=duration_ms
                    )
            
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e)},
                    check_duration_ms=duration_ms
                )
        
        # Register the check
        check_name = name or func.__name__
        
        # We need to use asyncio.create_task to register the check since
        # the decorator is called in a synchronous context
        async def register_check():
            await register_health_check(
                name=check_name,
                check_func=wrapper,
                description=description,
                tags=tags,
                timeout=timeout,
                critical=critical,
                group=group
            )
        
        asyncio.create_task(register_check())
        
        # Return the original function unmodified
        # This allows the function to be used normally
        return func
    
    return decorator


class HealthEndpoint:
    """
    FastAPI integration for health checking.
    
    This class provides health check endpoints for a FastAPI application.
    """
    
    @staticmethod
    def create_router(
        prefix: str = "/health",
        tags: List[str] = ["health"],
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
        async def health_check(response: Response, force: bool = False):
            """
            Check the health of the service.
            
            Returns a simple health status and sets the HTTP status code
            based on the health status.
            
            Args:
                response: FastAPI response object
                force: Whether to force fresh health checks
                
            Returns:
                Dictionary with health status
            """
            registry = get_health_registry()
            status = await registry.get_status(force)
            
            # Set HTTP status code based on health status
            response.status_code = status.http_status
            
            return {"status": status.name.lower()}
        
        if include_details:
            @router.get("/details", summary="Get detailed health report")
            async def health_details(force: bool = False):
                """
                Get a detailed health report.
                
                Returns detailed information about all health checks.
                
                Args:
                    force: Whether to force fresh health checks
                    
                Returns:
                    Detailed health report
                """
                registry = get_health_registry()
                return await registry.get_health_report(force)
            
            @router.get("/resources", summary="Get resource health")
            async def resource_health():
                """
                Get resource health.
                
                Returns health information from the resource monitor.
                
                Returns:
                    Resource health information
                """
                registry = get_health_registry()
                return await registry.get_resource_health()
            
            @router.get("/groups/{group}", summary="Get health for a specific group")
            async def group_health(group: str, force: bool = False):
                """
                Get health for a specific group.
                
                Args:
                    group: Name of the group to check
                    force: Whether to force fresh health checks
                    
                Returns:
                    Health status for the group
                """
                registry = get_health_registry()
                status = await registry.get_group_status(group, force)
                return {"group": group, "status": status.name.lower()}
            
            @router.get("/groups", summary="List health check groups")
            async def list_groups():
                """
                List health check groups.
                
                Returns:
                    List of health check groups
                """
                registry = get_health_registry()
                async with registry._lock:
                    groups = list(registry._groups.keys())
                
                return {"groups": groups}
        
        return router
    
    @staticmethod
    def setup(
        app: FastAPI,
        prefix: str = "/health",
        tags: List[str] = ["health"],
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
    
    @staticmethod
    def middleware():
        """
        Create middleware for adding health context to requests.
        
        Returns:
            Middleware function
        """
        @app.middleware("http")
        async def health_middleware(request: Request, call_next):
            # Add health context to request
            registry = get_health_registry()
            status = await registry.get_status(False)
            
            # Setup context
            context = health_context.get()
            context["health_status"] = status
            context["health_timestamp"] = time.time()
            health_context.set(context)
            
            # Process request
            response = await call_next(request)
            
            # Add health headers
            response.headers["X-Health-Status"] = status.name.lower()
            
            return response