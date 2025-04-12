"""
Plugin registry for managing plugin registrations.

This module provides a registry for tracking installed plugins and their status.
"""

import logging
from typing import Dict, List, Optional, Type, Set, Any

from uno.core.plugins.plugin import Plugin, PluginType, PluginStatus


class PluginRegistry:
    """
    Registry for managing plugins.
    
    The registry keeps track of all installed plugins, their status, and provides
    methods for querying the registry.
    """
    
    def __init__(self):
        """Initialize the plugin registry."""
        self.plugins: Dict[str, Plugin] = {}
        self.logger = logging.getLogger("uno.plugins.registry")
    
    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin with the registry.
        
        Args:
            plugin: Plugin instance to register
            
        Raises:
            ValueError: If a plugin with the same ID is already registered
        """
        if plugin.id in self.plugins:
            raise ValueError(f"Plugin with ID '{plugin.id}' is already registered")
        
        self.plugins[plugin.id] = plugin
        self.logger.info(f"Registered plugin: {plugin.name} ({plugin.id}) v{plugin.version}")
    
    def unregister(self, plugin_id: str) -> Optional[Plugin]:
        """
        Unregister a plugin from the registry.
        
        Args:
            plugin_id: ID of the plugin to unregister
            
        Returns:
            The unregistered plugin instance or None if not found
            
        Raises:
            ValueError: If the plugin is still enabled
        """
        if plugin_id not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_id]
        
        if plugin.status == PluginStatus.ENABLED:
            raise ValueError(f"Cannot unregister enabled plugin: {plugin_id}")
        
        del self.plugins[plugin_id]
        self.logger.info(f"Unregistered plugin: {plugin.name} ({plugin.id})")
        
        return plugin
    
    def get(self, plugin_id: str) -> Optional[Plugin]:
        """
        Get a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to retrieve
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_id)
    
    def get_all(self) -> List[Plugin]:
        """
        Get all registered plugins.
        
        Returns:
            List of all registered plugin instances
        """
        return list(self.plugins.values())
    
    def get_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        Get plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugins of the specified type
        """
        return [p for p in self.plugins.values() if p.info.plugin_type == plugin_type]
    
    def get_by_status(self, status: PluginStatus) -> List[Plugin]:
        """
        Get plugins with a specific status.
        
        Args:
            status: Status of plugins to retrieve
            
        Returns:
            List of plugins with the specified status
        """
        return [p for p in self.plugins.values() if p.status == status]
    
    def get_enabled(self) -> List[Plugin]:
        """
        Get all enabled plugins.
        
        Returns:
            List of enabled plugin instances
        """
        return self.get_by_status(PluginStatus.ENABLED)
    
    def get_loaded(self) -> List[Plugin]:
        """
        Get all loaded plugins (including enabled and disabled).
        
        Returns:
            List of loaded plugin instances
        """
        return [
            p for p in self.plugins.values() 
            if p.status in (PluginStatus.LOADED, PluginStatus.ENABLED, PluginStatus.DISABLED)
        ]
    
    def get_by_tag(self, tag: str) -> List[Plugin]:
        """
        Get plugins with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of plugins with the specified tag
        """
        return [p for p in self.plugins.values() if tag in p.info.tags]
    
    def is_registered(self, plugin_id: str) -> bool:
        """
        Check if a plugin is registered.
        
        Args:
            plugin_id: ID of the plugin to check
            
        Returns:
            True if the plugin is registered, False otherwise
        """
        return plugin_id in self.plugins
    
    def is_enabled(self, plugin_id: str) -> bool:
        """
        Check if a plugin is enabled.
        
        Args:
            plugin_id: ID of the plugin to check
            
        Returns:
            True if the plugin is enabled, False otherwise
        """
        plugin = self.get(plugin_id)
        return plugin is not None and plugin.status == PluginStatus.ENABLED
    
    def count(self) -> int:
        """
        Get the total number of registered plugins.
        
        Returns:
            Number of registered plugins
        """
        return len(self.plugins)
    
    def count_by_status(self, status: PluginStatus) -> int:
        """
        Get the number of plugins with a specific status.
        
        Args:
            status: Status to count
            
        Returns:
            Number of plugins with the specified status
        """
        return len(self.get_by_status(status))
    
    def clear(self) -> None:
        """
        Clear the registry by removing all plugins.
        
        Warning: This should only be used for testing purposes.
        """
        enabled_plugins = self.get_enabled()
        if enabled_plugins:
            enabled_ids = [p.id for p in enabled_plugins]
            raise ValueError(f"Cannot clear registry with enabled plugins: {', '.join(enabled_ids)}")
        
        self.plugins.clear()
        self.logger.warning("Plugin registry cleared")


# Global plugin registry instance
plugin_registry = PluginRegistry()


def register_plugin(plugin: Plugin) -> None:
    """
    Register a plugin with the global registry.
    
    Args:
        plugin: Plugin instance to register
        
    Raises:
        ValueError: If a plugin with the same ID is already registered
    """
    plugin_registry.register(plugin)


def get_plugin(plugin_id: str) -> Optional[Plugin]:
    """
    Get a plugin by ID from the global registry.
    
    Args:
        plugin_id: ID of the plugin to retrieve
        
    Returns:
        Plugin instance or None if not found
    """
    return plugin_registry.get(plugin_id)


def get_plugins() -> List[Plugin]:
    """
    Get all registered plugins from the global registry.
    
    Returns:
        List of all registered plugin instances
    """
    return plugin_registry.get_all()


def get_plugins_by_type(plugin_type: PluginType) -> List[Plugin]:
    """
    Get plugins of a specific type from the global registry.
    
    Args:
        plugin_type: Type of plugins to retrieve
        
    Returns:
        List of plugins of the specified type
    """
    return plugin_registry.get_by_type(plugin_type)