"""Configuration for progressive enhancement.

This module provides the configuration class for progressive enhancement.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Callable

from .detector import ConnectivityStatus


@dataclass
class FeatureLevel:
    """Configuration for a feature at a specific enhancement level.
    
    This defines how a feature should behave at a specific enhancement level,
    such as offline, poor connectivity, good connectivity, or excellent 
    connectivity.
    """
    
    enabled: bool = True
    """Whether the feature is enabled at this level."""
    
    config: Dict[str, Any] = field(default_factory=dict)
    """Configuration for the feature at this level."""
    
    auto_degrade: bool = True
    """Whether to automatically degrade to a lower level if needed."""
    
    fallback_level: Optional[str] = None
    """The level to fall back to if this level cannot be used."""


@dataclass
class FeatureConfig:
    """Configuration for a progressive enhancement feature.
    
    This defines how a feature should behave at different enhancement levels.
    """
    
    name: str
    """The name of the feature."""
    
    levels: Dict[str, FeatureLevel] = field(default_factory=dict)
    """Configuration for each enhancement level."""
    
    dependencies: List[str] = field(default_factory=list)
    """Other features this feature depends on."""
    
    priority: int = 0
    """Priority of this feature (higher is more important)."""
    
    default_level: str = "offline"
    """The default enhancement level to use."""
    
    def get_level_config(
        self,
        level: Union[str, ConnectivityStatus]
    ) -> Optional[FeatureLevel]:
        """Get the configuration for a specific enhancement level.
        
        Args:
            level: The enhancement level
            
        Returns:
            The configuration for the level, or None if not defined
        """
        if isinstance(level, ConnectivityStatus):
            level = level.value
        
        return self.levels.get(level)


@dataclass
class ProgressiveConfig:
    """Configuration for progressive enhancement.
    
    This defines how an application should progressively enhance based on
    connectivity and client capabilities.
    """
    
    features: Dict[str, FeatureConfig] = field(default_factory=dict)
    """Configuration for each feature."""
    
    connectivity_check_interval: float = 5.0
    """Interval in seconds between connectivity checks."""
    
    connectivity_endpoints: List[str] = field(default_factory=list)
    """Endpoints to check for connectivity."""
    
    capability_check_interval: float = 60.0
    """Interval in seconds between capability checks."""
    
    auto_start: bool = True
    """Whether to automatically start monitoring on initialization."""
    
    default_connectivity_status: ConnectivityStatus = ConnectivityStatus.OFFLINE
    """The default connectivity status to assume."""
    
    store_settings: bool = True
    """Whether to store settings in local storage."""
    
    storage_key: str = "progressive_enhancement_config"
    """The key to use for storing settings in local storage."""
    
    def add_feature(self, feature: FeatureConfig) -> None:
        """Add a feature configuration.
        
        Args:
            feature: The feature configuration to add
        """
        self.features[feature.name] = feature
    
    def get_feature(self, name: str) -> Optional[FeatureConfig]:
        """Get a feature configuration by name.
        
        Args:
            name: The name of the feature
            
        Returns:
            The feature configuration, or None if not found
        """
        return self.features.get(name)
    
    def remove_feature(self, name: str) -> None:
        """Remove a feature configuration.
        
        Args:
            name: The name of the feature to remove
        """
        if name in self.features:
            del self.features[name]
    
    @classmethod
    def create_default(cls) -> "ProgressiveConfig":
        """Create a default configuration.
        
        Returns:
            A default configuration
        """
        config = cls()
        
        # Add some default features
        sync_feature = FeatureConfig(
            name="synchronization",
            default_level="good",
            priority=100,
            levels={
                "offline": FeatureLevel(
                    enabled=False,
                    config={"mode": "offline-only"}
                ),
                "poor": FeatureLevel(
                    enabled=True,
                    config={"mode": "essential-only", "interval": 300}
                ),
                "good": FeatureLevel(
                    enabled=True,
                    config={"mode": "background", "interval": 60}
                ),
                "excellent": FeatureLevel(
                    enabled=True,
                    config={"mode": "realtime", "interval": 10}
                )
            }
        )
        config.add_feature(sync_feature)
        
        image_feature = FeatureConfig(
            name="images",
            default_level="good",
            priority=50,
            levels={
                "offline": FeatureLevel(
                    enabled=True,
                    config={"quality": "low", "prefetch": False}
                ),
                "poor": FeatureLevel(
                    enabled=True,
                    config={"quality": "medium", "prefetch": False}
                ),
                "good": FeatureLevel(
                    enabled=True,
                    config={"quality": "high", "prefetch": True}
                ),
                "excellent": FeatureLevel(
                    enabled=True,
                    config={"quality": "original", "prefetch": True}
                )
            }
        )
        config.add_feature(image_feature)
        
        return config