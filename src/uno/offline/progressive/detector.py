"""Connectivity and capability detection for progressive enhancement.

This module provides tools for detecting network connectivity and client
capabilities to support progressive enhancement.
"""
import abc
import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Dict, List, Any, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class ConnectivityStatus(Enum):
    """Enum representing different connectivity statuses."""
    
    OFFLINE = "offline"
    POOR = "poor"
    GOOD = "good"
    EXCELLENT = "excellent"


class ConnectivityDetector:
    """Detects and monitors network connectivity.
    
    The ConnectivityDetector is responsible for detecting and monitoring
    network connectivity, notifying listeners when the connectivity status
    changes.
    """
    
    def __init__(
        self,
        check_interval: float = 5.0,
        endpoints: Optional[List[str]] = None,
        timeout: float = 2.0
    ):
        """Initialize the connectivity detector.
        
        Args:
            check_interval: Interval in seconds between connectivity checks
            endpoints: List of endpoints to check for connectivity
            timeout: Timeout for connectivity checks in seconds
        """
        self.check_interval = check_interval
        self.endpoints = endpoints or [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.amazon.com"
        ]
        self.timeout = timeout
        
        self._status = ConnectivityStatus.OFFLINE
        self._listeners: List[Callable[[ConnectivityStatus], None]] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_successful_endpoint: Optional[str] = None
        self._last_check_time = 0.0
        self._last_check_duration = 0.0
    
    @property
    def status(self) -> ConnectivityStatus:
        """Get the current connectivity status.
        
        Returns:
            The current connectivity status
        """
        return self._status
    
    @property
    def is_online(self) -> bool:
        """Check if there is any connectivity.
        
        Returns:
            True if there is connectivity, False otherwise
        """
        return self._status != ConnectivityStatus.OFFLINE
    
    def add_listener(self, listener: Callable[[ConnectivityStatus], None]) -> None:
        """Add a listener to be notified of connectivity changes.
        
        Args:
            listener: A function to call when connectivity status changes
        """
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[ConnectivityStatus], None]) -> None:
        """Remove a listener.
        
        Args:
            listener: The listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def start(self) -> None:
        """Start monitoring connectivity.
        
        This starts a background task that periodically checks connectivity
        and notifies listeners when the status changes.
        """
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor())
    
    async def stop(self) -> None:
        """Stop monitoring connectivity."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def check_now(self) -> ConnectivityStatus:
        """Check connectivity immediately.
        
        Returns:
            The current connectivity status
        """
        await self._check_connectivity()
        return self._status
    
    async def _monitor(self) -> None:
        """Background task for monitoring connectivity."""
        while self._running:
            try:
                await self._check_connectivity()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connectivity monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_connectivity(self) -> None:
        """Check connectivity to determine status."""
        # Record start time
        start_time = time.time()
        
        # Initialize counters
        successful = 0
        total_latency = 0.0
        
        # Try each endpoint
        for endpoint in self.endpoints:
            try:
                # Attempt to fetch the endpoint
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    start = time.time()
                    async with session.get(endpoint, timeout=self.timeout) as response:
                        end = time.time()
                        if response.status < 400:
                            successful += 1
                            latency = end - start
                            total_latency += latency
                            self._last_successful_endpoint = endpoint
            except Exception:
                # Any error means this endpoint failed
                continue
        
        # Record end time and duration
        self._last_check_time = time.time()
        self._last_check_duration = self._last_check_time - start_time
        
        # Determine status based on results
        new_status = self._determine_status(successful, total_latency)
        
        # Notify listeners if status changed
        if new_status != self._status:
            old_status = self._status
            self._status = new_status
            self._notify_listeners()
            logger.info(f"Connectivity changed: {old_status.value} -> {new_status.value}")
    
    def _determine_status(self, successful: int, total_latency: float) -> ConnectivityStatus:
        """Determine connectivity status based on check results.
        
        Args:
            successful: Number of successful endpoint checks
            total_latency: Total latency of successful checks
            
        Returns:
            The determined connectivity status
        """
        if successful == 0:
            return ConnectivityStatus.OFFLINE
        
        # Calculate average latency
        avg_latency = total_latency / successful if successful > 0 else float('inf')
        
        # Calculate success ratio
        success_ratio = successful / len(self.endpoints)
        
        # Determine status based on success ratio and latency
        if success_ratio == 1.0 and avg_latency < 0.5:
            return ConnectivityStatus.EXCELLENT
        elif success_ratio >= 0.5 and avg_latency < 1.0:
            return ConnectivityStatus.GOOD
        else:
            return ConnectivityStatus.POOR
    
    def _notify_listeners(self) -> None:
        """Notify all listeners of a connectivity status change."""
        for listener in self._listeners:
            try:
                listener(self._status)
            except Exception as e:
                logger.error(f"Error in connectivity listener: {e}")


class CapabilityDetector:
    """Detects client capabilities for progressive enhancement.
    
    The CapabilityDetector is responsible for detecting client capabilities
    such as storage availability, network type, and device capabilities.
    """
    
    def __init__(self):
        """Initialize the capability detector."""
        self._storage_quota = None
        self._network_type = None
        self._device_memory = None
        self._cpu_cores = None
        self._battery_status = None
    
    async def detect_storage_quota(self) -> Optional[int]:
        """Detect available storage quota.
        
        Returns:
            The available storage quota in bytes, or None if it cannot be determined
        """
        # This would use platform-specific APIs
        # For now, return a placeholder
        return 1024 * 1024 * 100  # 100 MB
    
    async def detect_network_type(self) -> Optional[str]:
        """Detect network connection type.
        
        Returns:
            The network type as a string, or None if it cannot be determined
        """
        # This would use platform-specific APIs
        # For now, return a placeholder
        return "wifi"
    
    async def detect_device_memory(self) -> Optional[float]:
        """Detect available device memory.
        
        Returns:
            The available memory in GB, or None if it cannot be determined
        """
        # This would use platform-specific APIs
        # For now, return a placeholder
        return 4.0  # 4 GB
    
    async def detect_cpu_cores(self) -> Optional[int]:
        """Detect number of CPU cores.
        
        Returns:
            The number of CPU cores, or None if it cannot be determined
        """
        # This would use platform-specific APIs
        # For now, return a placeholder
        return 4
    
    async def detect_battery_status(self) -> Optional[Dict[str, Any]]:
        """Detect battery status.
        
        Returns:
            A dictionary with battery status information, or None if it cannot be determined
        """
        # This would use platform-specific APIs
        # For now, return a placeholder
        return {
            "charging": True,
            "level": 0.8  # 80%
        }
    
    async def detect_all(self) -> Dict[str, Any]:
        """Detect all capabilities.
        
        Returns:
            A dictionary with all detected capabilities
        """
        return {
            "storage_quota": await self.detect_storage_quota(),
            "network_type": await self.detect_network_type(),
            "device_memory": await self.detect_device_memory(),
            "cpu_cores": await self.detect_cpu_cores(),
            "battery_status": await self.detect_battery_status()
        }