"""
Plugin dependency resolution and compatibility checking.

This module provides utilities for resolving plugin dependencies and checking
compatibility between plugins and the application.
"""

import semver
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any

from uno.core.plugins.plugin import PluginInfo, PluginDependency


@dataclass
class PluginDependencyResolution:
    """
    Result of resolving dependencies for a plugin.
    
    This class holds the results of dependency resolution, including which
    dependencies were satisfied and which were missing.
    """
    
    success: bool
    """Whether all required dependencies were satisfied."""
    
    plugin_id: str
    """ID of the plugin whose dependencies were resolved."""
    
    satisfied: List[str]
    """List of satisfied dependency IDs."""
    
    missing: List[str]
    """List of missing dependency IDs."""
    
    optional_missing: List[str]
    """List of missing optional dependency IDs."""


async def resolve_plugin_dependencies(
    plugin_info: PluginInfo,
    registry: Any
) -> PluginDependencyResolution:
    """
    Resolve dependencies for a plugin.
    
    Args:
        plugin_info: Plugin metadata containing dependencies
        registry: Plugin registry to check for dependencies
        
    Returns:
        Resolution result
    """
    satisfied = []
    missing = []
    optional_missing = []
    
    for dependency in plugin_info.dependencies:
        # Check if the dependency is available
        dep_plugin = registry.get(dependency.plugin_id)
        
        if dep_plugin is None:
            # Dependency not available
            if dependency.optional:
                optional_missing.append(dependency.plugin_id)
            else:
                missing.append(dependency.plugin_id)
            continue
        
        # Check version constraints
        if dependency.min_version and semver.compare(dep_plugin.version, dependency.min_version) < 0:
            # Dependency version too old
            if dependency.optional:
                optional_missing.append(dependency.plugin_id)
            else:
                missing.append(dependency.plugin_id)
            continue
        
        if dependency.max_version and semver.compare(dep_plugin.version, dependency.max_version) > 0:
            # Dependency version too new
            if dependency.optional:
                optional_missing.append(dependency.plugin_id)
            else:
                missing.append(dependency.plugin_id)
            continue
        
        # Dependency satisfied
        satisfied.append(dependency.plugin_id)
    
    # Resolution is successful if all required dependencies are satisfied
    success = len(missing) == 0
    
    return PluginDependencyResolution(
        success=success,
        plugin_id=plugin_info.id,
        satisfied=satisfied,
        missing=missing,
        optional_missing=optional_missing
    )


def check_plugin_compatibility(plugin_info: PluginInfo, app_version: str) -> bool:
    """
    Check if a plugin is compatible with the application version.
    
    Args:
        plugin_info: Plugin metadata with version constraints
        app_version: Application version to check against
        
    Returns:
        True if the plugin is compatible, False otherwise
    """
    # If no version constraints are specified, assume compatible
    if plugin_info.min_app_version is None and plugin_info.max_app_version is None:
        return True
    
    # Check minimum version constraint
    if plugin_info.min_app_version is not None:
        if semver.compare(app_version, plugin_info.min_app_version) < 0:
            # Application version too old
            return False
    
    # Check maximum version constraint
    if plugin_info.max_app_version is not None:
        if semver.compare(app_version, plugin_info.max_app_version) > 0:
            # Application version too new
            return False
    
    # All constraints satisfied
    return True


async def resolve_dependency_order(
    plugin_infos: List[PluginInfo],
    registry: Any
) -> List[PluginInfo]:
    """
    Resolve the order in which plugins should be loaded based on dependencies.
    
    Args:
        plugin_infos: List of plugin metadata
        registry: Plugin registry to check for dependencies
        
    Returns:
        List of plugin metadata in dependency order (dependencies first)
        
    Raises:
        ValueError: If circular dependencies are detected
    """
    # Build dependency graph
    graph: Dict[str, List[str]] = {}
    for plugin_info in plugin_infos:
        graph[plugin_info.id] = []
        
        for dependency in plugin_info.dependencies:
            if not dependency.optional:
                graph[plugin_info.id].append(dependency.plugin_id)
    
    # Topological sort
    result: List[PluginInfo] = []
    visiting: Set[str] = set()
    visited: Set[str] = set()
    
    plugin_info_map = {p.id: p for p in plugin_infos}
    
    def visit(node_id: str):
        if node_id in visiting:
            # Detect cycles
            cycle_path = " -> ".join(list(visiting) + [node_id])
            raise ValueError(f"Circular dependency detected: {cycle_path}")
        
        if node_id not in visited:
            visiting.add(node_id)
            
            # Visit dependencies first
            for dep_id in graph.get(node_id, []):
                if dep_id in plugin_info_map:
                    visit(dep_id)
            
            visiting.remove(node_id)
            visited.add(node_id)
            
            if node_id in plugin_info_map:
                result.append(plugin_info_map[node_id])
    
    # Visit all nodes
    for plugin_info in plugin_infos:
        if plugin_info.id not in visited:
            visit(plugin_info.id)
    
    return result