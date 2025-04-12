"""
Base plugin classes and interfaces.

This module defines the core Plugin class and related components that form the
foundation of the plugin system.
"""

import os
import sys
import inspect
import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Type, Set, Union


class PluginType(Enum):
    """Types of plugins in the system."""
    CORE = auto()  # Core functionality extension
    MODEL = auto()  # Adds new models
    API = auto()  # Extends API functionality
    UI = auto()  # UI components or themes
    INTEGRATION = auto()  # External system integration
    UTILITY = auto()  # Utility functions
    MIDDLEWARE = auto()  # Request/response middleware
    DATABASE = auto()  # Database extensions
    CUSTOM = auto()  # Custom plugin type


class PluginStatus(Enum):
    """Status of a plugin in the system."""
    REGISTERED = auto()  # Plugin is registered but not loaded
    LOADED = auto()  # Plugin is loaded but not enabled
    ENABLED = auto()  # Plugin is enabled and active
    DISABLED = auto()  # Plugin is loaded but disabled
    ERROR = auto()  # Plugin encountered an error


class PluginLifecycleHook(Enum):
    """Lifecycle hooks for plugins."""
    PRE_REGISTER = auto()  # Before plugin is registered
    POST_REGISTER = auto()  # After plugin is registered
    PRE_LOAD = auto()  # Before plugin is loaded
    POST_LOAD = auto()  # After plugin is loaded
    PRE_ENABLE = auto()  # Before plugin is enabled
    POST_ENABLE = auto()  # After plugin is enabled
    PRE_DISABLE = auto()  # Before plugin is disabled
    POST_DISABLE = auto()  # After plugin is disabled
    PRE_UNLOAD = auto()  # Before plugin is unloaded
    POST_UNLOAD = auto()  # After plugin is unloaded


@dataclass
class PluginDependency:
    """Defines a dependency on another plugin."""
    
    plugin_id: str
    """ID of the plugin that is required."""
    
    min_version: Optional[str] = None
    """Minimum version required (optional)."""
    
    max_version: Optional[str] = None
    """Maximum version supported (optional)."""
    
    optional: bool = False
    """Whether this dependency is optional."""


@dataclass
class PluginInfo:
    """Metadata about a plugin."""
    
    id: str
    """Unique identifier for the plugin."""
    
    name: str
    """Human-readable name of the plugin."""
    
    version: str
    """Version string in semantic versioning format."""
    
    description: str
    """Detailed description of the plugin."""
    
    author: str
    """Author of the plugin."""
    
    website: Optional[str] = None
    """Plugin website URL."""
    
    license: Optional[str] = None
    """License under which the plugin is distributed."""
    
    plugin_type: PluginType = PluginType.CUSTOM
    """Type of the plugin."""
    
    requires_restart: bool = False
    """Whether the application needs to be restarted after enabling/disabling."""
    
    dependencies: List[PluginDependency] = field(default_factory=list)
    """List of plugin dependencies."""
    
    tags: List[str] = field(default_factory=list)
    """Tags for categorizing the plugin."""
    
    min_app_version: Optional[str] = None
    """Minimum application version required."""
    
    max_app_version: Optional[str] = None
    """Maximum application version supported."""
    
    python_dependencies: List[str] = field(default_factory=list)
    """Python package dependencies (pip requirements format)."""


@dataclass
class PluginConfig:
    """Configuration for a plugin."""
    
    schema: Dict[str, Any] = field(default_factory=dict)
    """JSON schema defining the configuration options."""
    
    defaults: Dict[str, Any] = field(default_factory=dict)
    """Default values for configuration options."""
    
    current: Dict[str, Any] = field(default_factory=dict)
    """Current configuration values."""
    
    def validate(self) -> List[str]:
        """
        Validate the current configuration against the schema.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        # Simple validation for now
        errors = []
        
        for key, schema_def in self.schema.items():
            if key not in self.current and schema_def.get("required", False):
                errors.append(f"Missing required configuration: {key}")
            
            if key in self.current:
                value_type = type(self.current[key])
                expected_type = self._get_type_from_schema(schema_def.get("type", "string"))
                
                if not isinstance(self.current[key], expected_type):
                    errors.append(
                        f"Invalid type for {key}: expected {schema_def.get('type')}, got {value_type.__name__}"
                    )
        
        return errors
    
    def _get_type_from_schema(self, schema_type: str) -> Type:
        """
        Convert JSON schema type to Python type.
        
        Args:
            schema_type: JSON schema type string
            
        Returns:
            Python type class
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        return type_map.get(schema_type, str)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.current.get(key, self.defaults.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.current[key] = value
    
    def reset(self, key: str = None) -> None:
        """
        Reset configuration to defaults.
        
        Args:
            key: Specific key to reset (None for all)
        """
        if key is None:
            self.current = self.defaults.copy()
        elif key in self.defaults:
            self.current[key] = self.defaults[key]
        elif key in self.current:
            del self.current[key]


class Plugin(ABC):
    """
    Base class for all plugins.
    
    A plugin extends the functionality of the Uno framework without modifying
    the core code. Plugins can add new features, modify existing behavior,
    or integrate with external systems.
    """
    
    def __init__(self, info: PluginInfo, config: Optional[PluginConfig] = None):
        """
        Initialize the plugin.
        
        Args:
            info: Plugin metadata
            config: Plugin configuration
        """
        self.info = info
        self.config = config or PluginConfig()
        self.status = PluginStatus.REGISTERED
        self.logger = logging.getLogger(f"uno.plugins.{info.id}")
    
    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return self.info.id
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return self.info.name
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return self.info.version
    
    @property
    def is_enabled(self) -> bool:
        """Check if the plugin is enabled."""
        return self.status == PluginStatus.ENABLED
    
    @property
    def is_loaded(self) -> bool:
        """Check if the plugin is loaded."""
        return self.status in (PluginStatus.LOADED, PluginStatus.ENABLED, PluginStatus.DISABLED)
    
    @abstractmethod
    async def load(self) -> None:
        """
        Load the plugin.
        
        This method is called when the plugin is being loaded into the system.
        It should perform any initialization needed before the plugin can be enabled.
        
        Raises:
            Exception: If the plugin cannot be loaded
        """
        pass
    
    @abstractmethod
    async def unload(self) -> None:
        """
        Unload the plugin.
        
        This method is called when the plugin is being unloaded from the system.
        It should clean up any resources used by the plugin.
        
        Raises:
            Exception: If the plugin cannot be unloaded
        """
        pass
    
    @abstractmethod
    async def enable(self) -> None:
        """
        Enable the plugin.
        
        This method is called when the plugin is being enabled.
        It should activate the plugin's functionality.
        
        Raises:
            Exception: If the plugin cannot be enabled
        """
        pass
    
    @abstractmethod
    async def disable(self) -> None:
        """
        Disable the plugin.
        
        This method is called when the plugin is being disabled.
        It should deactivate the plugin's functionality.
        
        Raises:
            Exception: If the plugin cannot be disabled
        """
        pass
    
    async def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            JSON schema for configuration options
        """
        return self.config.schema
    
    async def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate the given configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        # Store current config temporarily
        original_config = self.config.current.copy()
        
        # Set new config for validation
        self.config.current = config
        
        # Validate
        errors = self.config.validate()
        
        # Restore original config
        self.config.current = original_config
        
        return errors
    
    async def update_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Update the plugin configuration.
        
        Args:
            config: New configuration values
            
        Returns:
            List of validation error messages (empty if valid)
        """
        # Validate first
        errors = await self.validate_config(config)
        if errors:
            return errors
        
        # Apply new config
        self.config.current.update(config)
        
        # If plugin is enabled, apply configuration changes
        if self.is_enabled:
            await self.apply_config()
        
        return []
    
    async def apply_config(self) -> None:
        """
        Apply configuration changes.
        
        This method is called when the configuration has changed and needs to be applied.
        Override this method to handle configuration changes while the plugin is running.
        """
        pass


class CorePlugin(Plugin):
    """
    Base class for core plugins that extend the framework's basic functionality.
    
    Core plugins are integrated more tightly with the framework and have
    access to lower-level components.
    """
    
    def __init__(self, info: PluginInfo, config: Optional[PluginConfig] = None):
        """
        Initialize the core plugin.
        
        Args:
            info: Plugin metadata
            config: Plugin configuration
        """
        # Ensure plugin type is CORE
        if info.plugin_type != PluginType.CORE:
            info.plugin_type = PluginType.CORE
        
        super().__init__(info, config)
    
    @abstractmethod
    async def register_components(self) -> None:
        """
        Register components with the framework.
        
        This method is called during the enable process and should register
        any components that the plugin provides.
        """
        pass
    
    @abstractmethod
    async def unregister_components(self) -> None:
        """
        Unregister components from the framework.
        
        This method is called during the disable process and should unregister
        any components that the plugin had registered.
        """
        pass


def create_plugin_info(
    id: str,
    name: str,
    version: str,
    description: str,
    author: str,
    plugin_type: PluginType = PluginType.CUSTOM,
    **kwargs
) -> PluginInfo:
    """
    Create a PluginInfo object with the given parameters.
    
    Args:
        id: Unique identifier for the plugin
        name: Human-readable name of the plugin
        version: Version string
        description: Detailed description of the plugin
        author: Author of the plugin
        plugin_type: Type of the plugin
        **kwargs: Additional fields for PluginInfo
        
    Returns:
        PluginInfo object
    """
    return PluginInfo(
        id=id,
        name=name,
        version=version,
        description=description,
        author=author,
        plugin_type=plugin_type,
        **kwargs
    )


def create_plugin_config(
    schema: Dict[str, Any] = None,
    defaults: Dict[str, Any] = None
) -> PluginConfig:
    """
    Create a PluginConfig object with the given parameters.
    
    Args:
        schema: JSON schema defining the configuration options
        defaults: Default values for configuration options
        
    Returns:
        PluginConfig object
    """
    return PluginConfig(
        schema=schema or {},
        defaults=defaults or {},
        current=defaults.copy() if defaults else {}
    )