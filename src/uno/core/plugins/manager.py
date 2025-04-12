"""
Plugin manager for loading, enabling, and managing plugins.

This module provides the PluginManager class for managing the lifecycle of plugins,
including loading, enabling, disabling, and unloading.
"""

import os
import sys
import logging
import importlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set

from uno.core.plugins.plugin import Plugin, PluginStatus, PluginInfo, PluginLifecycleHook
from uno.core.plugins.registry import plugin_registry, register_plugin
from uno.core.plugins.hooks import call_hook
from uno.core.plugins.dependencies import (
    resolve_plugin_dependencies, check_plugin_compatibility,
    PluginDependencyResolution
)


class PluginManager:
    """
    Manager for plugin lifecycle operations.
    
    The plugin manager is responsible for loading, enabling, disabling, and unloading
    plugins, as well as managing plugin dependencies and configurations.
    """
    
    def __init__(self, app_version: str = "0.0.0"):
        """
        Initialize the plugin manager.
        
        Args:
            app_version: Version of the application (for compatibility checking)
        """
        self.app_version = app_version
        self.logger = logging.getLogger("uno.plugins.manager")
    
    async def load_plugin(self, plugin: Plugin) -> bool:
        """
        Load a plugin.
        
        Args:
            plugin: Plugin instance to load
            
        Returns:
            True if the plugin was loaded successfully, False otherwise
            
        Raises:
            ValueError: If the plugin is in an invalid state
        """
        if plugin.status != PluginStatus.REGISTERED:
            raise ValueError(f"Cannot load plugin {plugin.id} with status {plugin.status}")
        
        # Check if plugin is compatible with the application
        if not check_plugin_compatibility(plugin.info, self.app_version):
            self.logger.warning(
                f"Plugin {plugin.name} ({plugin.id}) v{plugin.version} is not compatible with "
                f"application version {self.app_version}"
            )
            return False
        
        try:
            # Call pre-load hook
            await call_hook(PluginLifecycleHook.PRE_LOAD, plugin)
            
            # Load the plugin
            await plugin.load()
            
            # Update plugin status
            plugin.status = PluginStatus.LOADED
            
            # Call post-load hook
            await call_hook(PluginLifecycleHook.POST_LOAD, plugin)
            
            self.logger.info(f"Loaded plugin: {plugin.name} ({plugin.id}) v{plugin.version}")
            return True
        
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            self.logger.error(f"Failed to load plugin {plugin.id}: {str(e)}", exc_info=True)
            return False
    
    async def unload_plugin(self, plugin: Plugin) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin: Plugin instance to unload
            
        Returns:
            True if the plugin was unloaded successfully, False otherwise
            
        Raises:
            ValueError: If the plugin is in an invalid state
        """
        if plugin.status not in (PluginStatus.LOADED, PluginStatus.DISABLED, PluginStatus.ERROR):
            raise ValueError(f"Cannot unload plugin {plugin.id} with status {plugin.status}")
        
        if plugin.status == PluginStatus.ENABLED:
            # Disable the plugin first
            if not await self.disable_plugin(plugin):
                return False
        
        try:
            # Call pre-unload hook
            await call_hook(PluginLifecycleHook.PRE_UNLOAD, plugin)
            
            # Unload the plugin
            await plugin.unload()
            
            # Update plugin status
            plugin.status = PluginStatus.REGISTERED
            
            # Call post-unload hook
            await call_hook(PluginLifecycleHook.POST_UNLOAD, plugin)
            
            self.logger.info(f"Unloaded plugin: {plugin.name} ({plugin.id})")
            return True
        
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            self.logger.error(f"Failed to unload plugin {plugin.id}: {str(e)}", exc_info=True)
            return False
    
    async def enable_plugin(self, plugin: Plugin) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin: Plugin instance to enable
            
        Returns:
            True if the plugin was enabled successfully, False otherwise
            
        Raises:
            ValueError: If the plugin is in an invalid state
        """
        if plugin.status not in (PluginStatus.LOADED, PluginStatus.DISABLED):
            raise ValueError(f"Cannot enable plugin {plugin.id} with status {plugin.status}")
        
        # Check dependencies
        resolution = await resolve_plugin_dependencies(plugin.info, plugin_registry)
        if not resolution.success:
            self.logger.error(
                f"Failed to enable plugin {plugin.id} due to unsatisfied dependencies: "
                f"{', '.join(resolution.missing)}"
            )
            return False
        
        try:
            # Call pre-enable hook
            await call_hook(PluginLifecycleHook.PRE_ENABLE, plugin)
            
            # Enable the plugin
            await plugin.enable()
            
            # Update plugin status
            plugin.status = PluginStatus.ENABLED
            
            # Call post-enable hook
            await call_hook(PluginLifecycleHook.POST_ENABLE, plugin)
            
            self.logger.info(f"Enabled plugin: {plugin.name} ({plugin.id})")
            return True
        
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            self.logger.error(f"Failed to enable plugin {plugin.id}: {str(e)}", exc_info=True)
            return False
    
    async def disable_plugin(self, plugin: Plugin) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin: Plugin instance to disable
            
        Returns:
            True if the plugin was disabled successfully, False otherwise
            
        Raises:
            ValueError: If the plugin is in an invalid state
        """
        if plugin.status != PluginStatus.ENABLED:
            raise ValueError(f"Cannot disable plugin {plugin.id} with status {plugin.status}")
        
        try:
            # Call pre-disable hook
            await call_hook(PluginLifecycleHook.PRE_DISABLE, plugin)
            
            # Disable the plugin
            await plugin.disable()
            
            # Update plugin status
            plugin.status = PluginStatus.DISABLED
            
            # Call post-disable hook
            await call_hook(PluginLifecycleHook.POST_DISABLE, plugin)
            
            self.logger.info(f"Disabled plugin: {plugin.name} ({plugin.id})")
            return True
        
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            self.logger.error(f"Failed to disable plugin {plugin.id}: {str(e)}", exc_info=True)
            return False
    
    async def reload_plugin(self, plugin: Plugin) -> bool:
        """
        Reload a plugin.
        
        Args:
            plugin: Plugin instance to reload
            
        Returns:
            True if the plugin was reloaded successfully, False otherwise
        """
        was_enabled = plugin.status == PluginStatus.ENABLED
        
        # Unload the plugin
        if not await self.unload_plugin(plugin):
            return False
        
        # Load the plugin
        if not await self.load_plugin(plugin):
            return False
        
        # Re-enable the plugin if it was enabled
        if was_enabled:
            return await self.enable_plugin(plugin)
        
        return True
    
    async def initialize_all(self) -> Tuple[int, int, int]:
        """
        Initialize all registered plugins.
        
        This loads and enables plugins in the correct order based on dependencies.
        
        Returns:
            Tuple of (total plugins, loaded count, enabled count)
        """
        # Get all registered plugins
        plugins = plugin_registry.get_all()
        total = len(plugins)
        
        # First, load all plugins
        loaded_count = 0
        for plugin in plugins:
            if await self.load_plugin(plugin):
                loaded_count += 1
        
        # Then, enable plugins in dependency order
        enabled_count = 0
        
        # Get resolutions for all plugins to determine order
        resolutions = []
        for plugin in plugin_registry.get_by_status(PluginStatus.LOADED):
            resolution = await resolve_plugin_dependencies(plugin.info, plugin_registry)
            if resolution.success:
                resolutions.append((plugin, resolution))
        
        # Sort by dependency level (lower level = fewer dependencies)
        resolutions.sort(key=lambda x: len(x[1].satisfied))
        
        # Enable plugins in order
        for plugin, _ in resolutions:
            if await self.enable_plugin(plugin):
                enabled_count += 1
        
        return total, loaded_count, enabled_count
    
    async def shutdown_all(self) -> Tuple[int, int]:
        """
        Shutdown all plugins.
        
        This disables and unloads all plugins in the reverse order of their dependencies.
        
        Returns:
            Tuple of (disabled count, unloaded count)
        """
        # Disable enabled plugins in reverse dependency order
        enabled_plugins = plugin_registry.get_enabled()
        
        # Get resolutions for all plugins to determine order
        plugin_deps = {}
        for plugin in enabled_plugins:
            resolution = await resolve_plugin_dependencies(plugin.info, plugin_registry)
            plugin_deps[plugin.id] = resolution.satisfied
        
        # Sort by dependency level (higher level = more dependencies)
        enabled_plugins.sort(key=lambda p: len(plugin_deps.get(p.id, [])), reverse=True)
        
        # Disable plugins in reverse order
        disabled_count = 0
        for plugin in enabled_plugins:
            if await self.disable_plugin(plugin):
                disabled_count += 1
        
        # Unload all loaded plugins
        unloaded_count = 0
        for plugin in plugin_registry.get_loaded():
            if await self.unload_plugin(plugin):
                unloaded_count += 1
        
        return disabled_count, unloaded_count


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance.
    
    Returns:
        Plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


async def load_plugin(plugin: Plugin) -> bool:
    """
    Load a plugin using the global plugin manager.
    
    Args:
        plugin: Plugin instance to load
        
    Returns:
        True if the plugin was loaded successfully, False otherwise
    """
    return await get_plugin_manager().load_plugin(plugin)


async def unload_plugin(plugin: Plugin) -> bool:
    """
    Unload a plugin using the global plugin manager.
    
    Args:
        plugin: Plugin instance to unload
        
    Returns:
        True if the plugin was unloaded successfully, False otherwise
    """
    return await get_plugin_manager().unload_plugin(plugin)


async def enable_plugin(plugin: Plugin) -> bool:
    """
    Enable a plugin using the global plugin manager.
    
    Args:
        plugin: Plugin instance to enable
        
    Returns:
        True if the plugin was enabled successfully, False otherwise
    """
    return await get_plugin_manager().enable_plugin(plugin)


async def disable_plugin(plugin: Plugin) -> bool:
    """
    Disable a plugin using the global plugin manager.
    
    Args:
        plugin: Plugin instance to disable
        
    Returns:
        True if the plugin was disabled successfully, False otherwise
    """
    return await get_plugin_manager().disable_plugin(plugin)


async def reload_plugin(plugin: Plugin) -> bool:
    """
    Reload a plugin using the global plugin manager.
    
    Args:
        plugin: Plugin instance to reload
        
    Returns:
        True if the plugin was reloaded successfully, False otherwise
    """
    return await get_plugin_manager().reload_plugin(plugin)


async def init_plugins(app_version: str = "0.0.0") -> Tuple[int, int, int]:
    """
    Initialize all registered plugins.
    
    Args:
        app_version: Version of the application
        
    Returns:
        Tuple of (total plugins, loaded count, enabled count)
    """
    global _plugin_manager
    _plugin_manager = PluginManager(app_version)
    return await _plugin_manager.initialize_all()


async def shutdown_plugins() -> Tuple[int, int]:
    """
    Shutdown all plugins.
    
    Returns:
        Tuple of (disabled count, unloaded count)
    """
    return await get_plugin_manager().shutdown_all()