"""Enhancement strategies for progressive enhancement.

This module provides strategies for determining how to enhance application
features based on connectivity and capability information.
"""
import abc
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Union

from .detector import ConnectivityStatus
from .config import FeatureConfig, FeatureLevel, ProgressiveConfig

logger = logging.getLogger(__name__)


class EnhancementStrategy(abc.ABC):
    """Abstract base class for enhancement strategies.
    
    Enhancement strategies determine how to enhance application features
    based on connectivity and capability information.
    """
    
    @abc.abstractmethod
    def determine_level(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> str:
        """Determine the enhancement level for a feature.
        
        Args:
            feature: The feature to determine the level for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The enhancement level to use
        """
        pass
    
    @abc.abstractmethod
    def get_feature_config(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get the configuration for a feature.
        
        Args:
            feature: The feature to get the configuration for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The feature configuration
        """
        pass


class DefaultStrategy(EnhancementStrategy):
    """Default enhancement strategy.
    
    This strategy maps connectivity statuses to enhancement levels and
    uses the level configuration for the feature.
    """
    
    def determine_level(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> str:
        """Determine the enhancement level for a feature.
        
        Args:
            feature: The feature to determine the level for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The enhancement level to use
        """
        # Map connectivity status to enhancement level
        level = connectivity.value
        
        # Check if the feature has a configuration for this level
        if level not in feature.levels:
            # Fall back to the default level
            logger.debug(
                f"Feature {feature.name} has no configuration for level {level}, "
                f"falling back to {feature.default_level}"
            )
            return feature.default_level
        
        # Check if the level is enabled
        level_config = feature.levels[level]
        if not level_config.enabled:
            # Find a fallback level
            if level_config.fallback_level and level_config.fallback_level in feature.levels:
                logger.debug(
                    f"Feature {feature.name} level {level} is disabled, "
                    f"falling back to {level_config.fallback_level}"
                )
                return level_config.fallback_level
            else:
                # Fall back to the default level
                logger.debug(
                    f"Feature {feature.name} level {level} is disabled, "
                    f"falling back to {feature.default_level}"
                )
                return feature.default_level
        
        # Check if the level is suitable for the capabilities
        if level == "excellent":
            # For excellent level, check if the device has enough resources
            if capabilities.get("device_memory", 0) < 2.0:
                # Not enough memory, fall back to good
                logger.debug(
                    f"Feature {feature.name} not enough memory for excellent level, "
                    f"falling back to good"
                )
                return "good"
        
        return level
    
    def get_feature_config(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get the configuration for a feature.
        
        Args:
            feature: The feature to get the configuration for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The feature configuration
        """
        # Determine the enhancement level
        level = self.determine_level(feature, connectivity, capabilities)
        
        # Get the level configuration
        level_config = feature.levels.get(level)
        if not level_config:
            # Fall back to the default level
            logger.debug(
                f"Feature {feature.name} has no configuration for level {level}, "
                f"falling back to {feature.default_level}"
            )
            level_config = feature.levels.get(feature.default_level)
            if not level_config:
                # Return an empty configuration
                logger.warning(
                    f"Feature {feature.name} has no configuration for default level "
                    f"{feature.default_level}, returning empty configuration"
                )
                return {}
        
        # Return the configuration
        return level_config.config.copy()


class BatteryAwareStrategy(DefaultStrategy):
    """Battery-aware enhancement strategy.
    
    This strategy takes into account the battery status when determining
    the enhancement level.
    """
    
    def determine_level(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> str:
        """Determine the enhancement level for a feature.
        
        Args:
            feature: The feature to determine the level for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The enhancement level to use
        """
        # Start with the default enhancement level
        level = super().determine_level(feature, connectivity, capabilities)
        
        # Check if battery status is available
        battery_status = capabilities.get("battery_status")
        if battery_status:
            # Check if the battery is low and not charging
            if not battery_status.get("charging", False) and battery_status.get("level", 1.0) < 0.2:
                # Battery is low, degrade to a lower level if possible
                if level == "excellent":
                    logger.debug(
                        f"Feature {feature.name} battery is low, "
                        f"degrading from excellent to good"
                    )
                    return "good"
                elif level == "good":
                    logger.debug(
                        f"Feature {feature.name} battery is low, "
                        f"degrading from good to poor"
                    )
                    return "poor"
        
        return level


class BandwidthAwareStrategy(DefaultStrategy):
    """Bandwidth-aware enhancement strategy.
    
    This strategy takes into account the network type and bandwidth when
    determining the enhancement level.
    """
    
    def determine_level(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> str:
        """Determine the enhancement level for a feature.
        
        Args:
            feature: The feature to determine the level for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The enhancement level to use
        """
        # Start with the default enhancement level
        level = super().determine_level(feature, connectivity, capabilities)
        
        # Check if network type is available
        network_type = capabilities.get("network_type")
        if network_type:
            # Degrade level for certain network types
            if network_type == "cellular" and level in ["excellent", "good"]:
                logger.debug(
                    f"Feature {feature.name} on cellular network, "
                    f"degrading to poor"
                )
                return "poor"
            elif network_type == "slow-2g" and level != "offline":
                logger.debug(
                    f"Feature {feature.name} on slow-2g network, "
                    f"degrading to offline"
                )
                return "offline"
        
        return level


class StorageAwareStrategy(DefaultStrategy):
    """Storage-aware enhancement strategy.
    
    This strategy takes into account the available storage when determining
    the enhancement level.
    """
    
    def determine_level(
        self,
        feature: FeatureConfig,
        connectivity: ConnectivityStatus,
        capabilities: Dict[str, Any]
    ) -> str:
        """Determine the enhancement level for a feature.
        
        Args:
            feature: The feature to determine the level for
            connectivity: The current connectivity status
            capabilities: The current client capabilities
            
        Returns:
            The enhancement level to use
        """
        # Start with the default enhancement level
        level = super().determine_level(feature, connectivity, capabilities)
        
        # Check if storage quota is available
        storage_quota = capabilities.get("storage_quota")
        if storage_quota:
            # If storage is low, degrade level for features that use storage
            if storage_quota < 10 * 1024 * 1024:  # Less than 10 MB
                if feature.name in ["caching", "offline-content", "media-library"]:
                    logger.debug(
                        f"Feature {feature.name} storage is low, "
                        f"degrading to offline"
                    )
                    return "offline"
            elif storage_quota < 100 * 1024 * 1024:  # Less than 100 MB
                if feature.name in ["media-library"] and level == "excellent":
                    logger.debug(
                        f"Feature {feature.name} storage is limited, "
                        f"degrading from excellent to good"
                    )
                    return "good"
        
        return level