"""
Resource monitoring for the Uno framework.

This module provides utilities for monitoring and reporting on resource usage,
including database connections, circuit breakers, and system resources.
"""

from typing import Dict, Any, Optional, List, Set, Tuple, Callable, Union
import asyncio
import logging
import time
import datetime
import platform
import os
import psutil
from enum import Enum, auto

from uno.core.resources import (
    ResourceRegistry,
    ConnectionPool,
    CircuitBreaker,
    BackgroundTask,
    get_resource_registry,
)


class ResourceHealth(Enum):
    """
    Health status of a resource.
    
    - HEALTHY: Resource is functioning normally
    - DEGRADED: Resource is functioning but with issues
    - UNHEALTHY: Resource is not functioning
    - UNKNOWN: Resource health cannot be determined
    """
    
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


class ResourceType(Enum):
    """
    Type of resource being monitored.
    
    - CONNECTION_POOL: Database connection pool
    - CIRCUIT_BREAKER: Circuit breaker
    - TASK: Background task
    - SYSTEM: System resource (CPU, memory, etc.)
    - CUSTOM: Custom resource type
    """
    
    CONNECTION_POOL = auto()
    CIRCUIT_BREAKER = auto()
    TASK = auto()
    SYSTEM = auto()
    CUSTOM = auto()


class ResourceMetrics:
    """
    Metrics for a monitored resource.
    
    This class stores metrics for a resource, including usage statistics,
    health status, and historical data.
    """
    
    def __init__(
        self,
        name: str,
        resource_type: ResourceType,
        health: ResourceHealth = ResourceHealth.UNKNOWN,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize resource metrics.
        
        Args:
            name: Name of the resource
            resource_type: Type of resource
            health: Initial health status
            metadata: Additional metadata about the resource
        """
        self.name = name
        self.resource_type = resource_type
        self.health = health
        self.metadata = metadata or {}
        
        # Current metrics
        self.metrics: Dict[str, Any] = {}
        
        # Historical metrics
        self.history: List[Tuple[float, Dict[str, Any]]] = []
        self.history_max_size = 100  # Maximum number of historical entries
        
        # Timestamps
        self.first_seen = time.time()
        self.last_updated = self.first_seen
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update resource metrics.
        
        Args:
            metrics: New metrics to store
        """
        self.metrics = metrics
        now = time.time()
        self.last_updated = now
        
        # Add to history
        self.history.append((now, metrics.copy()))
        
        # Trim history if needed
        if len(self.history) > self.history_max_size:
            self.history = self.history[-self.history_max_size:]
    
    def update_health(self, health: ResourceHealth) -> None:
        """
        Update resource health.
        
        Args:
            health: New health status
        """
        self.health = health
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to a dictionary.
        
        Returns:
            Dictionary representation of the metrics
        """
        return {
            "name": self.name,
            "type": self.resource_type.name,
            "health": self.health.name,
            "metadata": self.metadata,
            "metrics": self.metrics,
            "first_seen": self.first_seen,
            "last_updated": self.last_updated,
            "age": time.time() - self.first_seen,
        }


class ResourceMonitor:
    """
    Monitor for tracking resource usage and health.
    
    This class provides monitoring for various resources, including
    database connections, circuit breakers, and system resources.
    """
    
    def __init__(
        self,
        resource_registry: Optional[ResourceRegistry] = None,
        logger: Optional[logging.Logger] = None,
        monitor_interval: float = 60.0,
        history_max_age: float = 3600.0,  # 1 hour
    ):
        """
        Initialize the resource monitor.
        
        Args:
            resource_registry: Optional resource registry
            logger: Optional logger instance
            monitor_interval: Interval between monitoring runs in seconds
            history_max_age: Maximum age of historical data in seconds
        """
        self.resource_registry = resource_registry or get_resource_registry()
        self.logger = logger or logging.getLogger(__name__)
        self.monitor_interval = monitor_interval
        self.history_max_age = history_max_age
        
        # Resource metrics
        self._metrics: Dict[str, ResourceMetrics] = {}
        self._metrics_lock = asyncio.Lock()
        
        # Custom health checks
        self._health_checks: Dict[str, Callable[[], ResourceHealth]] = {}
        
        # Monitoring task
        self._monitor_task: Optional[BackgroundTask] = None
        self._started = False
    
    async def start(self) -> None:
        """
        Start the resource monitor.
        
        This starts the background monitoring task.
        """
        if self._started:
            return
        
        # Create and start the monitoring task
        self._monitor_task = BackgroundTask(
            self._monitor_resources,
            name="resource_monitor",
            restart_on_failure=True,
            logger=self.logger,
        )
        
        await self._monitor_task.start()
        self._started = True
        
        # Register with the resource registry
        await self.resource_registry.register("resource_monitor", self)
        
        self.logger.info("Resource monitor started")
    
    async def stop(self) -> None:
        """
        Stop the resource monitor.
        """
        if not self._started:
            return
        
        # Stop the monitoring task
        if self._monitor_task:
            await self._monitor_task.stop()
            self._monitor_task = None
        
        self._started = False
        
        self.logger.info("Resource monitor stopped")
    
    async def close(self) -> None:
        """
        Close the resource monitor (alias for stop).
        """
        await self.stop()
    
    async def _monitor_resources(self) -> None:
        """
        Background task for monitoring resources.
        
        This runs periodically to update resource metrics.
        """
        while True:
            try:
                # Monitor resources
                await self._update_all_metrics()
                
                # Clean up old history
                await self._clean_history()
                
                # Wait for next run
                await asyncio.sleep(self.monitor_interval)
            
            except asyncio.CancelledError:
                # Expected during shutdown
                break
            
            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {str(e)}", exc_info=True)
                await asyncio.sleep(5.0)  # Wait a bit before retrying
    
    async def _update_all_metrics(self) -> None:
        """
        Update metrics for all resources.
        """
        # Monitor system resources
        await self._update_system_metrics()
        
        # Monitor registry resources
        registry_metrics = await self._get_registry_metrics()
        
        # Process registry resources
        for name, metrics in registry_metrics.items():
            await self._update_resource_metrics(name, metrics)
        
        # Run custom health checks
        await self._run_health_checks()
    
    async def _get_registry_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all resources in the registry.
        
        Returns:
            Dictionary of resource metrics
        """
        try:
            # Get metrics from the registry
            return self.resource_registry.get_metrics()
        except Exception as e:
            self.logger.error(f"Error getting registry metrics: {str(e)}")
            return {}
    
    async def _update_resource_metrics(
        self,
        name: str,
        metrics: Dict[str, Any],
    ) -> None:
        """
        Update metrics for a specific resource.
        
        Args:
            name: Resource name
            metrics: Resource metrics
        """
        # Determine resource type
        resource_type = ResourceType.CUSTOM
        if "type" in metrics:
            type_name = metrics["type"].lower()
            if "connection" in type_name and "pool" in type_name:
                resource_type = ResourceType.CONNECTION_POOL
            elif "circuit" in type_name:
                resource_type = ResourceType.CIRCUIT_BREAKER
            elif "task" in type_name:
                resource_type = ResourceType.TASK
        
        # Determine health status
        health = self._determine_health(name, resource_type, metrics)
        
        async with self._metrics_lock:
            # Create or update resource metrics
            if name not in self._metrics:
                self._metrics[name] = ResourceMetrics(
                    name=name,
                    resource_type=resource_type,
                    health=health,
                )
            
            # Update metrics and health
            self._metrics[name].update_metrics(metrics)
            self._metrics[name].update_health(health)
    
    def _determine_health(
        self,
        name: str,
        resource_type: ResourceType,
        metrics: Dict[str, Any],
    ) -> ResourceHealth:
        """
        Determine the health of a resource.
        
        Args:
            name: Resource name
            resource_type: Resource type
            metrics: Resource metrics
            
        Returns:
            Health status
        """
        # Check if resource has a health field
        if "health" in metrics:
            health_str = metrics["health"].upper()
            try:
                return ResourceHealth[health_str]
            except (KeyError, AttributeError):
                pass
        
        # Determine health based on resource type and metrics
        if resource_type == ResourceType.CONNECTION_POOL:
            # Check connection errors
            errors = metrics.get("connection_errors", 0)
            if errors > 10:
                return ResourceHealth.UNHEALTHY
            elif errors > 3:
                return ResourceHealth.DEGRADED
            
            # Check in_use vs total
            in_use = metrics.get("in_use_connections", 0)
            total = metrics.get("total_connections", 0)
            max_size = metrics.get("max_size", 0)
            
            if total <= 0:
                return ResourceHealth.UNHEALTHY
            
            # If we're at max capacity, degraded
            if max_size > 0 and total >= max_size * 0.9:
                return ResourceHealth.DEGRADED
            
            return ResourceHealth.HEALTHY
        
        elif resource_type == ResourceType.CIRCUIT_BREAKER:
            # Check circuit state
            state = metrics.get("state", "").lower()
            if state == "open":
                return ResourceHealth.UNHEALTHY
            elif state == "half_open":
                return ResourceHealth.DEGRADED
            elif state == "closed":
                return ResourceHealth.HEALTHY
        
        elif resource_type == ResourceType.TASK:
            # Check task running state
            running = metrics.get("running", False)
            if not running:
                return ResourceHealth.UNHEALTHY
            
            # Check restart count
            restarts = metrics.get("restart_count", 0)
            if restarts > 5:
                return ResourceHealth.DEGRADED
            
            return ResourceHealth.HEALTHY
        
        elif resource_type == ResourceType.SYSTEM:
            # Check CPU and memory usage
            cpu_percent = metrics.get("cpu_percent", 0.0)
            memory_percent = metrics.get("memory_percent", 0.0)
            
            if cpu_percent > 90.0 or memory_percent > 90.0:
                return ResourceHealth.UNHEALTHY
            elif cpu_percent > 75.0 or memory_percent > 75.0:
                return ResourceHealth.DEGRADED
            
            return ResourceHealth.HEALTHY
        
        # Default for unknown metrics
        return ResourceHealth.UNKNOWN
    
    async def _update_system_metrics(self) -> None:
        """
        Update system resource metrics.
        """
        try:
            # Get system metrics
            metrics = self._get_system_metrics()
            
            # Determine health
            health = self._determine_health(
                "system",
                ResourceType.SYSTEM,
                metrics,
            )
            
            async with self._metrics_lock:
                # Create or update system metrics
                if "system" not in self._metrics:
                    self._metrics["system"] = ResourceMetrics(
                        name="system",
                        resource_type=ResourceType.SYSTEM,
                        health=health,
                        metadata={
                            "hostname": platform.node(),
                            "platform": platform.platform(),
                            "python_version": platform.python_version(),
                        },
                    )
                
                # Update metrics and health
                self._metrics["system"].update_metrics(metrics)
                self._metrics["system"].update_health(health)
        
        except Exception as e:
            self.logger.error(f"Error updating system metrics: {str(e)}")
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system resource metrics.
        
        Returns:
            Dictionary of system metrics
        """
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Get disk usage
        disk = psutil.disk_usage("/")
        
        # Get process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "timestamp": time.time(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": cpu_percent,
            "memory_total": memory.total,
            "memory_available": memory.available,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "disk_percent": disk.percent,
            "process_cpu_percent": process.cpu_percent(),
            "process_memory_rss": process_memory.rss,
            "process_memory_vms": process_memory.vms,
            "process_threads": process.num_threads(),
            "process_open_files": len(process.open_files()),
            "process_connections": len(process.connections()),
        }
    
    async def _run_health_checks(self) -> None:
        """
        Run custom health checks.
        """
        for name, check_func in self._health_checks.items():
            try:
                # Run the health check
                health = check_func()
                
                async with self._metrics_lock:
                    # Update health if resource exists
                    if name in self._metrics:
                        self._metrics[name].update_health(health)
            
            except Exception as e:
                self.logger.error(f"Error running health check '{name}': {str(e)}")
    
    async def _clean_history(self) -> None:
        """
        Clean up old historical data.
        """
        now = time.time()
        cutoff = now - self.history_max_age
        
        async with self._metrics_lock:
            for metrics in self._metrics.values():
                # Remove entries older than cutoff
                metrics.history = [
                    (ts, data) for ts, data in metrics.history
                    if ts >= cutoff
                ]
    
    async def register_health_check(
        self,
        name: str,
        check_func: Callable[[], ResourceHealth],
    ) -> None:
        """
        Register a custom health check.
        
        Args:
            name: Name of the resource to check
            check_func: Function that returns the resource health
        """
        self._health_checks[name] = check_func
        self.logger.debug(f"Registered health check for '{name}'")
    
    async def unregister_health_check(self, name: str) -> None:
        """
        Unregister a custom health check.
        
        Args:
            name: Name of the resource
        """
        if name in self._health_checks:
            del self._health_checks[name]
            self.logger.debug(f"Unregistered health check for '{name}'")
    
    async def get_metrics(
        self,
        resource_name: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        include_history: bool = False,
    ) -> Dict[str, Any]:
        """
        Get metrics for resources.
        
        Args:
            resource_name: Optional name of a specific resource
            resource_type: Optional type of resources to include
            include_history: Whether to include historical data
            
        Returns:
            Dictionary of resource metrics
        """
        result: Dict[str, Any] = {
            "timestamp": time.time(),
            "resource_count": 0,
            "resources": {},
        }
        
        async with self._metrics_lock:
            # Filter resources
            filtered_metrics = {}
            
            for name, metrics in self._metrics.items():
                # Filter by name if specified
                if resource_name is not None and name != resource_name:
                    continue
                
                # Filter by type if specified
                if resource_type is not None and metrics.resource_type != resource_type:
                    continue
                
                # Include resource
                metrics_dict = metrics.to_dict()
                
                # Include history if requested
                if include_history:
                    metrics_dict["history"] = [
                        {"timestamp": ts, "metrics": data}
                        for ts, data in metrics.history
                    ]
                
                filtered_metrics[name] = metrics_dict
            
            # Update result
            result["resource_count"] = len(filtered_metrics)
            result["resources"] = filtered_metrics
        
        return result
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of resource health.
        
        Returns:
            Dictionary with health summary
        """
        summary = {
            "timestamp": time.time(),
            "overall_health": ResourceHealth.UNKNOWN.name,
            "resource_count": 0,
            "healthy_count": 0,
            "degraded_count": 0,
            "unhealthy_count": 0,
            "unknown_count": 0,
            "resources": {},
        }
        
        async with self._metrics_lock:
            # Count resources by health status
            for name, metrics in self._metrics.items():
                # Update counts
                summary["resource_count"] += 1
                
                if metrics.health == ResourceHealth.HEALTHY:
                    summary["healthy_count"] += 1
                elif metrics.health == ResourceHealth.DEGRADED:
                    summary["degraded_count"] += 1
                elif metrics.health == ResourceHealth.UNHEALTHY:
                    summary["unhealthy_count"] += 1
                else:
                    summary["unknown_count"] += 1
                
                # Include basic resource info
                summary["resources"][name] = {
                    "health": metrics.health.name,
                    "type": metrics.resource_type.name,
                    "last_updated": metrics.last_updated,
                }
            
            # Determine overall health
            if summary["unhealthy_count"] > 0:
                summary["overall_health"] = ResourceHealth.UNHEALTHY.name
            elif summary["degraded_count"] > 0:
                summary["overall_health"] = ResourceHealth.DEGRADED.name
            elif summary["healthy_count"] > 0:
                summary["overall_health"] = ResourceHealth.HEALTHY.name
        
        return summary
    
    async def get_resource_health(self, name: str) -> ResourceHealth:
        """
        Get the health of a specific resource.
        
        Args:
            name: Name of the resource
            
        Returns:
            Health status of the resource
            
        Raises:
            ValueError: If resource not found
        """
        async with self._metrics_lock:
            if name not in self._metrics:
                raise ValueError(f"Resource '{name}' not found")
            
            return self._metrics[name].health


# Global resource monitor
_resource_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """
    Get the global resource monitor.
    
    Returns:
        The global resource monitor
    """
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor


async def start_resource_monitoring() -> None:
    """
    Start the global resource monitor.
    """
    monitor = get_resource_monitor()
    await monitor.start()


async def stop_resource_monitoring() -> None:
    """
    Stop the global resource monitor.
    """
    global _resource_monitor
    if _resource_monitor is not None:
        await _resource_monitor.stop()
        _resource_monitor = None