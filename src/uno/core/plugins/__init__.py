"""
Plugin architecture for the Uno framework.

This module provides a system for extending the framework's functionality
through plugins without modifying the core code.
"""

from uno.core.plugins.registry import (
    PluginRegistry, plugin_registry, register_plugin, 
    get_plugin, get_plugins, get_plugins_by_type
)
from uno.core.plugins.plugin import (
    Plugin, PluginConfig, PluginInfo, PluginStatus, 
    PluginType, PluginLifecycleHook
)
from uno.core.plugins.manager import (
    PluginManager, init_plugins, load_plugin, unload_plugin,
    enable_plugin, disable_plugin, reload_plugin
)
from uno.core.plugins.discovery import (
    discover_plugins, load_plugins_from_directory, 
    load_plugins_from_entry_points
)
from uno.core.plugins.extension import (
    ExtensionPoint, extension_registry, register_extension_point,
    get_extension_point, get_extension_points,
    register_extension, get_extensions
)
from uno.core.plugins.hooks import (
    HookRegistry, hook_registry, register_hook,
    get_hook, get_hooks, call_hook
)
from uno.core.plugins.dependencies import (
    resolve_plugin_dependencies, check_plugin_compatibility,
    PluginDependency, PluginDependencyResolution
)

__all__ = [
    # Registry
    "PluginRegistry", "plugin_registry", "register_plugin", 
    "get_plugin", "get_plugins", "get_plugins_by_type",
    
    # Plugin base
    "Plugin", "PluginConfig", "PluginInfo", "PluginStatus", 
    "PluginType", "PluginLifecycleHook",
    
    # Manager
    "PluginManager", "init_plugins", "load_plugin", "unload_plugin",
    "enable_plugin", "disable_plugin", "reload_plugin",
    
    # Discovery
    "discover_plugins", "load_plugins_from_directory", 
    "load_plugins_from_entry_points",
    
    # Extension points
    "ExtensionPoint", "extension_registry", "register_extension_point",
    "get_extension_point", "get_extension_points",
    "register_extension", "get_extensions",
    
    # Hooks
    "HookRegistry", "hook_registry", "register_hook",
    "get_hook", "get_hooks", "call_hook",
    
    # Dependencies
    "resolve_plugin_dependencies", "check_plugin_compatibility",
    "PluginDependency", "PluginDependencyResolution"
]