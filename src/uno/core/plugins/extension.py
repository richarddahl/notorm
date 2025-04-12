"""
Extension point system for plugin extensibility.

This module provides an extension point system that allows plugins to extend
specific parts of the framework.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Type


@dataclass
class ExtensionPoint:
    """
    Definition of an extension point.
    
    An extension point is a specific location in the framework where plugins
    can provide extensions to add or modify functionality.
    """
    
    id: str
    """Unique identifier for the extension point."""
    
    name: str
    """Human-readable name of the extension point."""
    
    description: str
    """Detailed description of the extension point."""
    
    interface: Optional[Type] = None
    """Interface that extensions must implement (if any)."""
    
    schema: Optional[Dict[str, Any]] = None
    """JSON schema for extension configuration (if any)."""
    
    extensions: Dict[str, Any] = field(default_factory=dict)
    """Registered extensions for this extension point."""


class ExtensionRegistry:
    """
    Registry for managing extension points and extensions.
    
    The extension registry keeps track of all extension points and the
    extensions registered for each one.
    """
    
    def __init__(self):
        """Initialize the extension registry."""
        self.extension_points: Dict[str, ExtensionPoint] = {}
        self.logger = logging.getLogger("uno.plugins.extension")
    
    def register_extension_point(self, extension_point: ExtensionPoint) -> None:
        """
        Register an extension point.
        
        Args:
            extension_point: Extension point to register
            
        Raises:
            ValueError: If an extension point with the same ID is already registered
        """
        if extension_point.id in self.extension_points:
            raise ValueError(f"Extension point with ID '{extension_point.id}' is already registered")
        
        self.extension_points[extension_point.id] = extension_point
        self.logger.info(f"Registered extension point: {extension_point.name} ({extension_point.id})")
    
    def unregister_extension_point(self, extension_point_id: str) -> Optional[ExtensionPoint]:
        """
        Unregister an extension point.
        
        Args:
            extension_point_id: ID of the extension point to unregister
            
        Returns:
            The unregistered extension point or None if not found
        """
        if extension_point_id not in self.extension_points:
            return None
        
        extension_point = self.extension_points[extension_point_id]
        del self.extension_points[extension_point_id]
        self.logger.info(f"Unregistered extension point: {extension_point.name} ({extension_point.id})")
        
        return extension_point
    
    def get_extension_point(self, extension_point_id: str) -> Optional[ExtensionPoint]:
        """
        Get an extension point by ID.
        
        Args:
            extension_point_id: ID of the extension point to retrieve
            
        Returns:
            Extension point or None if not found
        """
        return self.extension_points.get(extension_point_id)
    
    def get_all_extension_points(self) -> List[ExtensionPoint]:
        """
        Get all registered extension points.
        
        Returns:
            List of all registered extension points
        """
        return list(self.extension_points.values())
    
    def register_extension(
        self,
        extension_point_id: str,
        extension_id: str,
        extension: Any,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an extension for an extension point.
        
        Args:
            extension_point_id: ID of the extension point
            extension_id: Unique ID for the extension
            extension: The extension implementation
            config: Optional configuration for the extension
            
        Returns:
            True if the extension was registered, False otherwise
            
        Raises:
            ValueError: If the extension ID is already registered for the extension point
            ValueError: If the extension doesn't implement the required interface
        """
        extension_point = self.get_extension_point(extension_point_id)
        if extension_point is None:
            self.logger.warning(f"Extension point not found: {extension_point_id}")
            return False
        
        if extension_id in extension_point.extensions:
            raise ValueError(
                f"Extension with ID '{extension_id}' is already registered for "
                f"extension point '{extension_point_id}'"
            )
        
        # Validate extension against interface
        if extension_point.interface is not None and not isinstance(extension, extension_point.interface):
            raise ValueError(
                f"Extension '{extension_id}' does not implement the required interface "
                f"for extension point '{extension_point_id}'"
            )
        
        # Validate extension configuration against schema
        if extension_point.schema is not None and config is not None:
            # TODO: Implement JSON schema validation
            pass
        
        # Register the extension
        extension_point.extensions[extension_id] = {
            "extension": extension,
            "config": config or {}
        }
        
        self.logger.info(
            f"Registered extension '{extension_id}' for extension point '{extension_point.name}' "
            f"({extension_point.id})"
        )
        
        return True
    
    def unregister_extension(self, extension_point_id: str, extension_id: str) -> bool:
        """
        Unregister an extension.
        
        Args:
            extension_point_id: ID of the extension point
            extension_id: ID of the extension to unregister
            
        Returns:
            True if the extension was unregistered, False otherwise
        """
        extension_point = self.get_extension_point(extension_point_id)
        if extension_point is None:
            return False
        
        if extension_id not in extension_point.extensions:
            return False
        
        del extension_point.extensions[extension_id]
        self.logger.info(
            f"Unregistered extension '{extension_id}' from extension point '{extension_point.name}' "
            f"({extension_point.id})"
        )
        
        return True
    
    def get_extensions(self, extension_point_id: str) -> Dict[str, Any]:
        """
        Get all extensions for an extension point.
        
        Args:
            extension_point_id: ID of the extension point
            
        Returns:
            Dictionary of extension ID to extension details
        """
        extension_point = self.get_extension_point(extension_point_id)
        if extension_point is None:
            return {}
        
        return extension_point.extensions
    
    def get_extension(self, extension_point_id: str, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific extension.
        
        Args:
            extension_point_id: ID of the extension point
            extension_id: ID of the extension
            
        Returns:
            Extension details or None if not found
        """
        extensions = self.get_extensions(extension_point_id)
        return extensions.get(extension_id)
    
    def clear(self) -> None:
        """
        Clear the registry by removing all extension points.
        
        Warning: This should only be used for testing purposes.
        """
        self.extension_points.clear()
        self.logger.warning("Extension registry cleared")


# Global extension registry instance
extension_registry = ExtensionRegistry()


def register_extension_point(extension_point: ExtensionPoint) -> None:
    """
    Register an extension point with the global registry.
    
    Args:
        extension_point: Extension point to register
        
    Raises:
        ValueError: If an extension point with the same ID is already registered
    """
    extension_registry.register_extension_point(extension_point)


def get_extension_point(extension_point_id: str) -> Optional[ExtensionPoint]:
    """
    Get an extension point by ID from the global registry.
    
    Args:
        extension_point_id: ID of the extension point to retrieve
        
    Returns:
        Extension point or None if not found
    """
    return extension_registry.get_extension_point(extension_point_id)


def get_extension_points() -> List[ExtensionPoint]:
    """
    Get all registered extension points from the global registry.
    
    Returns:
        List of all registered extension points
    """
    return extension_registry.get_all_extension_points()


def register_extension(
    extension_point_id: str,
    extension_id: str,
    extension: Any,
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Register an extension for an extension point in the global registry.
    
    Args:
        extension_point_id: ID of the extension point
        extension_id: Unique ID for the extension
        extension: The extension implementation
        config: Optional configuration for the extension
        
    Returns:
        True if the extension was registered, False otherwise
    """
    return extension_registry.register_extension(extension_point_id, extension_id, extension, config)


def get_extensions(extension_point_id: str) -> Dict[str, Any]:
    """
    Get all extensions for an extension point from the global registry.
    
    Args:
        extension_point_id: ID of the extension point
        
    Returns:
        Dictionary of extension ID to extension details
    """
    return extension_registry.get_extensions(extension_point_id)


def create_extension_point(
    id: str,
    name: str,
    description: str,
    interface: Optional[Type] = None,
    schema: Optional[Dict[str, Any]] = None
) -> ExtensionPoint:
    """
    Create a new extension point.
    
    Args:
        id: Unique identifier for the extension point
        name: Human-readable name of the extension point
        description: Detailed description of the extension point
        interface: Interface that extensions must implement (optional)
        schema: JSON schema for extension configuration (optional)
        
    Returns:
        New ExtensionPoint instance
    """
    return ExtensionPoint(
        id=id,
        name=name,
        description=description,
        interface=interface,
        schema=schema
    )