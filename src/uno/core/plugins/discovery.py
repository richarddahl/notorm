"""
Plugin discovery for finding and loading plugins from various sources.

This module provides functions for discovering plugins from directories,
entry points, and other sources.
"""

import os
import sys
import inspect
import importlib
import importlib.util
import importlib.metadata
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Tuple, Set

from uno.core.plugins.plugin import Plugin, PluginInfo, PluginConfig
from uno.core.plugins.registry import plugin_registry, register_plugin


logger = logging.getLogger("uno.plugins.discovery")


async def discover_plugins() -> List[Plugin]:
    """
    Discover plugins from all registered sources.
    
    Returns:
        List of discovered plugins
    """
    discovered_plugins = []
    
    # Load from entry points
    entry_point_plugins = await load_plugins_from_entry_points()
    discovered_plugins.extend(entry_point_plugins)
    
    return discovered_plugins


async def load_plugins_from_directory(directory: str) -> List[Plugin]:
    """
    Load plugins from a directory.
    
    Args:
        directory: Directory path to scan for plugins
        
    Returns:
        List of discovered plugins
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        logger.warning(f"Plugin directory does not exist: {directory}")
        return []
    
    plugins = []
    
    # Get all Python files in the directory
    py_files = [f for f in os.listdir(directory) if f.endswith('.py') and not f.startswith('_')]
    
    for py_file in py_files:
        plugin_path = os.path.join(directory, py_file)
        module_name = os.path.splitext(py_file)[0]
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load plugin module: {plugin_path}")
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_classes = [
                obj for _, obj in inspect.getmembers(module)
                if (
                    inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin and
                    obj.__module__ == module.__name__
                )
            ]
            
            for plugin_class in plugin_classes:
                try:
                    # Look for PluginInfo and PluginConfig in the module
                    info = getattr(module, 'PLUGIN_INFO', None)
                    config = getattr(module, 'PLUGIN_CONFIG', None)
                    
                    if info is None:
                        # Try to find info in class attributes
                        info = getattr(plugin_class, 'plugin_info', None)
                    
                    if config is None:
                        # Try to find config in class attributes
                        config = getattr(plugin_class, 'plugin_config', None)
                    
                    # Create plugin instance
                    plugin = plugin_class(info, config)
                    
                    # Add the plugin path for debugging
                    plugin.path = plugin_path
                    
                    # Register plugin
                    register_plugin(plugin)
                    plugins.append(plugin)
                    
                    logger.info(f"Discovered plugin from file: {plugin.name} ({plugin.id}) v{plugin.version}")
                
                except Exception as e:
                    logger.error(f"Error loading plugin from {plugin_path}: {str(e)}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error loading module from {plugin_path}: {str(e)}", exc_info=True)
    
    return plugins


async def load_plugins_from_entry_points(group: str = "uno.plugins") -> List[Plugin]:
    """
    Load plugins from entry points.
    
    Args:
        group: Entry point group to scan for plugins
        
    Returns:
        List of discovered plugins
    """
    plugins = []
    
    try:
        # Find entry points
        entry_points = importlib.metadata.entry_points()
        
        # Filter by group
        if hasattr(entry_points, "select"):
            # New API (Python 3.10+)
            plugin_entry_points = entry_points.select(group=group)
        else:
            # Old API
            plugin_entry_points = entry_points.get(group, [])
        
        for entry_point in plugin_entry_points:
            try:
                # Load the entry point
                plugin_class = entry_point.load()
                
                # Check if it's a valid plugin class
                if inspect.isclass(plugin_class) and issubclass(plugin_class, Plugin) and plugin_class is not Plugin:
                    # Look for plugin info and config
                    info = getattr(plugin_class, 'plugin_info', None)
                    config = getattr(plugin_class, 'plugin_config', None)
                    
                    # Create plugin instance
                    plugin = plugin_class(info, config)
                    
                    # Register plugin
                    register_plugin(plugin)
                    plugins.append(plugin)
                    
                    logger.info(
                        f"Discovered plugin from entry point {entry_point.name}: "
                        f"{plugin.name} ({plugin.id}) v{plugin.version}"
                    )
            
            except Exception as e:
                logger.error(f"Error loading plugin from entry point {entry_point.name}: {str(e)}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error finding entry points: {str(e)}", exc_info=True)
    
    return plugins


async def load_plugins_from_module(module_name: str) -> List[Plugin]:
    """
    Load plugins from a Python module.
    
    Args:
        module_name: Name of the module to load plugins from
        
    Returns:
        List of discovered plugins
    """
    plugins = []
    
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Find plugin classes
        plugin_classes = [
            obj for _, obj in inspect.getmembers(module)
            if (
                inspect.isclass(obj) and 
                issubclass(obj, Plugin) and 
                obj is not Plugin and
                obj.__module__ == module.__name__
            )
        ]
        
        for plugin_class in plugin_classes:
            try:
                # Look for PluginInfo and PluginConfig in the module
                info = getattr(module, 'PLUGIN_INFO', None)
                config = getattr(module, 'PLUGIN_CONFIG', None)
                
                if info is None:
                    # Try to find info in class attributes
                    info = getattr(plugin_class, 'plugin_info', None)
                
                if config is None:
                    # Try to find config in class attributes
                    config = getattr(plugin_class, 'plugin_config', None)
                
                # Create plugin instance
                plugin = plugin_class(info, config)
                
                # Register plugin
                register_plugin(plugin)
                plugins.append(plugin)
                
                logger.info(f"Discovered plugin from module {module_name}: {plugin.name} ({plugin.id}) v{plugin.version}")
            
            except Exception as e:
                logger.error(f"Error loading plugin from {module_name}: {str(e)}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error importing module {module_name}: {str(e)}", exc_info=True)
    
    return plugins


async def load_plugin_from_class(plugin_class: Type[Plugin]) -> Optional[Plugin]:
    """
    Load a plugin from a class.
    
    Args:
        plugin_class: Plugin class to instantiate
        
    Returns:
        Plugin instance or None if loading failed
    """
    try:
        # Look for plugin info and config
        info = getattr(plugin_class, 'plugin_info', None)
        config = getattr(plugin_class, 'plugin_config', None)
        
        # Create plugin instance
        plugin = plugin_class(info, config)
        
        # Register plugin
        register_plugin(plugin)
        
        logger.info(f"Loaded plugin from class {plugin_class.__name__}: {plugin.name} ({plugin.id}) v{plugin.version}")
        
        return plugin
    
    except Exception as e:
        logger.error(f"Error loading plugin from class {plugin_class.__name__}: {str(e)}", exc_info=True)
        return None