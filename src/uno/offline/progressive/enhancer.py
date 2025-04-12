"""Progressive enhancer for application features.

This module provides the main class for progressive enhancement, which
coordinates connectivity detection, capability detection, and feature
enhancement based on the current conditions.
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Callable

from .detector import ConnectivityDetector, CapabilityDetector, ConnectivityStatus
from .config import ProgressiveConfig, FeatureConfig
from .strategies import EnhancementStrategy, DefaultStrategy

logger = logging.getLogger(__name__)


class ProgressiveEnhancer:
    """Main class for progressive enhancement.
    
    The ProgressiveEnhancer is responsible for coordinating connectivity
    detection, capability detection, and feature enhancement based on the
    current conditions.
    """
    
    def __init__(
        self,
        config: Optional[ProgressiveConfig] = None,
        strategy: Optional[EnhancementStrategy] = None,
        connectivity_detector: Optional[ConnectivityDetector] = None,
        capability_detector: Optional[CapabilityDetector] = None
    ):
        """Initialize the progressive enhancer.
        
        Args:
            config: Configuration for progressive enhancement
            strategy: Strategy for determining enhancement levels
            connectivity_detector: Detector for network connectivity
            capability_detector: Detector for client capabilities
        """
        self.config = config or ProgressiveConfig.create_default()
        self.strategy = strategy or DefaultStrategy()
        
        # Set up detectors
        self.connectivity_detector = connectivity_detector or ConnectivityDetector(
            check_interval=self.config.connectivity_check_interval,
            endpoints=self.config.connectivity_endpoints
        )
        self.capability_detector = capability_detector or CapabilityDetector()
        
        # Set up feature enhancers and feature state
        self._feature_enhancers: Dict[str, Callable] = {}
        self._feature_status: Dict[str, Dict[str, Any]] = {}
        self._capabilities: Dict[str, Any] = {}
        self._running = False
        self._capability_check_task: Optional[asyncio.Task] = None
        
        # Set up listeners
        self.connectivity_detector.add_listener(self._on_connectivity_change)
    
    async def start(self) -> None:
        """Start the progressive enhancer.
        
        This starts connectivity monitoring and capability detection.
        """
        if self._running:
            return
        
        self._running = True
        
        # Start connectivity monitoring
        await self.connectivity_detector.start()
        
        # Start capability detection
        await self._detect_capabilities()
        self._capability_check_task = asyncio.create_task(self._capability_check_loop())
        
        # Initialize feature status
        await self._initialize_features()
        
        logger.info("Progressive enhancer started")
    
    async def stop(self) -> None:
        """Stop the progressive enhancer."""
        self._running = False
        
        # Stop connectivity monitoring
        await self.connectivity_detector.stop()
        
        # Stop capability detection
        if self._capability_check_task:
            self._capability_check_task.cancel()
            try:
                await self._capability_check_task
            except asyncio.CancelledError:
                pass
            self._capability_check_task = None
        
        logger.info("Progressive enhancer stopped")
    
    def register_feature_enhancer(
        self,
        feature_name: str,
        enhancer: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register an enhancer for a feature.
        
        The enhancer is called whenever the configuration for the feature
        changes, with the new configuration as an argument.
        
        Args:
            feature_name: The name of the feature
            enhancer: A function that enhances the feature based on the configuration
        """
        self._feature_enhancers[feature_name] = enhancer
        
        # If the feature is already initialized, call the enhancer
        if feature_name in self._feature_status:
            try:
                config = self._feature_status[feature_name]["config"]
                enhancer(config)
            except Exception as e:
                logger.error(f"Error in feature enhancer for {feature_name}: {e}")
    
    def unregister_feature_enhancer(self, feature_name: str) -> None:
        """Unregister an enhancer for a feature.
        
        Args:
            feature_name: The name of the feature
        """
        if feature_name in self._feature_enhancers:
            del self._feature_enhancers[feature_name]
    
    def get_feature_status(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a feature.
        
        Args:
            feature_name: The name of the feature
            
        Returns:
            The feature status, or None if the feature is not found
        """
        return self._feature_status.get(feature_name)
    
    def get_all_feature_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the current status of all features.
        
        Returns:
            A dictionary mapping feature names to their status
        """
        return self._feature_status.copy()
    
    def get_connectivity_status(self) -> ConnectivityStatus:
        """Get the current connectivity status.
        
        Returns:
            The current connectivity status
        """
        return self.connectivity_detector.status
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the current client capabilities.
        
        Returns:
            The current client capabilities
        """
        return self._capabilities.copy()
    
    async def manual_update(self, feature_name: Optional[str] = None) -> None:
        """Manually update a feature or all features.
        
        Args:
            feature_name: The name of the feature to update, or None to update all
        """
        if feature_name:
            # Update a specific feature
            await self._update_feature(feature_name)
        else:
            # Update all features
            await self._update_all_features()
    
    async def _detect_capabilities(self) -> None:
        """Detect client capabilities."""
        try:
            self._capabilities = await self.capability_detector.detect_all()
            logger.debug(f"Detected capabilities: {self._capabilities}")
        except Exception as e:
            logger.error(f"Error detecting capabilities: {e}")
    
    async def _capability_check_loop(self) -> None:
        """Background task for periodically checking capabilities."""
        while self._running:
            try:
                await asyncio.sleep(self.config.capability_check_interval)
                await self._detect_capabilities()
                await self._update_all_features()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in capability check loop: {e}")
    
    async def _initialize_features(self) -> None:
        """Initialize all features."""
        for feature_name, feature in self.config.features.items():
            await self._update_feature(feature_name)
    
    async def _update_all_features(self) -> None:
        """Update all features."""
        for feature_name in self.config.features:
            await self._update_feature(feature_name)
    
    async def _update_feature(self, feature_name: str) -> None:
        """Update a specific feature.
        
        Args:
            feature_name: The name of the feature to update
        """
        # Get the feature configuration
        feature = self.config.get_feature(feature_name)
        if not feature:
            logger.warning(f"Feature {feature_name} not found in configuration")
            return
        
        # Determine the enhancement level
        connectivity = self.connectivity_detector.status
        level = self.strategy.determine_level(
            feature,
            connectivity,
            self._capabilities
        )
        
        # Get the feature configuration
        config = self.strategy.get_feature_config(
            feature,
            connectivity,
            self._capabilities
        )
        
        # Update the feature status
        old_status = self._feature_status.get(feature_name, {})
        new_status = {
            "level": level,
            "connectivity": connectivity.value,
            "config": config,
            "enabled": feature.levels.get(level, FeatureConfig.levels).enabled
        }
        
        # Check if the status has changed
        if old_status.get("level") != new_status["level"] or old_status.get("config") != new_status["config"]:
            logger.debug(
                f"Feature {feature_name} updated: "
                f"{old_status.get('level', 'none')} -> {new_status['level']}"
            )
            
            # Update the status
            self._feature_status[feature_name] = new_status
            
            # Call the enhancer if registered
            enhancer = self._feature_enhancers.get(feature_name)
            if enhancer:
                try:
                    enhancer(config)
                except Exception as e:
                    logger.error(f"Error in feature enhancer for {feature_name}: {e}")
    
    def _on_connectivity_change(self, status: ConnectivityStatus) -> None:
        """Handle a connectivity status change.
        
        Args:
            status: The new connectivity status
        """
        logger.info(f"Connectivity changed to {status.value}")
        
        # Update all features
        asyncio.create_task(self._update_all_features())
    
    async def _load_settings(self) -> None:
        """Load settings from local storage."""
        if not self.config.store_settings:
            return
        
        try:
            # This would use platform-specific APIs to load from local storage
            # For now, do nothing
            pass
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    async def _save_settings(self) -> None:
        """Save settings to local storage."""
        if not self.config.store_settings:
            return
        
        try:
            # This would use platform-specific APIs to save to local storage
            # For now, do nothing
            pass
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    async def save_settings(self) -> None:
        """Save settings to local storage."""
        await self._save_settings()