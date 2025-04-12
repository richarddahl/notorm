"""
Hook system for plugin lifecycle and extension.

This module provides a hook system that allows plugins and framework components
to register callbacks for specific events or extension points.
"""

import logging
import inspect
import asyncio
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple, Set, Union, Type


class HookRegistry:
    """
    Registry for managing hooks and callbacks.
    
    The hook registry allows components to register and call hooks for specific
    events or lifecycle points.
    """
    
    def __init__(self):
        """Initialize the hook registry."""
        self.hooks: Dict[Any, List[Tuple[Callable, int]]] = {}
        self.logger = logging.getLogger("uno.plugins.hooks")
    
    def register_hook(
        self,
        hook_type: Any,
        callback: Callable,
        priority: int = 100
    ) -> None:
        """
        Register a hook callback.
        
        Args:
            hook_type: Type or identifier of the hook (can be enum, string, etc.)
            callback: Function to call when the hook is triggered
            priority: Priority of the callback (lower values run first, default: 100)
            
        Raises:
            ValueError: If the callback is already registered for the hook
        """
        if hook_type not in self.hooks:
            self.hooks[hook_type] = []
        
        # Check if the callback is already registered
        for registered_callback, _ in self.hooks[hook_type]:
            if registered_callback == callback:
                raise ValueError(f"Callback already registered for hook: {hook_type}")
        
        # Add the callback
        self.hooks[hook_type].append((callback, priority))
        
        # Sort by priority
        self.hooks[hook_type].sort(key=lambda x: x[1])
        
        self.logger.debug(f"Registered hook callback for {hook_type} with priority {priority}")
    
    def unregister_hook(self, hook_type: Any, callback: Callable) -> bool:
        """
        Unregister a hook callback.
        
        Args:
            hook_type: Type or identifier of the hook
            callback: Callback to unregister
            
        Returns:
            True if the callback was unregistered, False otherwise
        """
        if hook_type not in self.hooks:
            return False
        
        for i, (registered_callback, _) in enumerate(self.hooks[hook_type]):
            if registered_callback == callback:
                del self.hooks[hook_type][i]
                self.logger.debug(f"Unregistered hook callback for {hook_type}")
                return True
        
        return False
    
    def get_hooks(self, hook_type: Any) -> List[Callable]:
        """
        Get all callbacks for a hook.
        
        Args:
            hook_type: Type or identifier of the hook
            
        Returns:
            List of callbacks for the hook
        """
        if hook_type not in self.hooks:
            return []
        
        return [callback for callback, _ in self.hooks[hook_type]]
    
    def has_hooks(self, hook_type: Any) -> bool:
        """
        Check if a hook has any callbacks.
        
        Args:
            hook_type: Type or identifier of the hook
            
        Returns:
            True if the hook has callbacks, False otherwise
        """
        return hook_type in self.hooks and len(self.hooks[hook_type]) > 0
    
    async def call_hooks(self, hook_type: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """
        Call all callbacks for a hook.
        
        Args:
            hook_type: Type or identifier of the hook
            *args: Positional arguments to pass to the callbacks
            **kwargs: Keyword arguments to pass to the callbacks
            
        Returns:
            List of results from all callbacks
        """
        if not self.has_hooks(hook_type):
            return []
        
        results = []
        for callback, _ in self.hooks[hook_type]:
            try:
                # Call the callback
                result = callback(*args, **kwargs)
                
                # Handle async callbacks
                if inspect.isawaitable(result):
                    result = await result
                
                results.append(result)
            
            except Exception as e:
                self.logger.error(f"Error calling hook callback for {hook_type}: {str(e)}", exc_info=True)
        
        return results
    
    def clear(self) -> None:
        """
        Clear the registry by removing all hooks.
        
        Warning: This should only be used for testing purposes.
        """
        self.hooks.clear()
        self.logger.warning("Hook registry cleared")


# Global hook registry instance
hook_registry = HookRegistry()


def register_hook(
    hook_type: Any,
    callback: Callable,
    priority: int = 100
) -> None:
    """
    Register a hook callback with the global registry.
    
    Args:
        hook_type: Type or identifier of the hook (can be enum, string, etc.)
        callback: Function to call when the hook is triggered
        priority: Priority of the callback (lower values run first, default: 100)
        
    Raises:
        ValueError: If the callback is already registered for the hook
    """
    hook_registry.register_hook(hook_type, callback, priority)


def unregister_hook(hook_type: Any, callback: Callable) -> bool:
    """
    Unregister a hook callback from the global registry.
    
    Args:
        hook_type: Type or identifier of the hook
        callback: Callback to unregister
        
    Returns:
        True if the callback was unregistered, False otherwise
    """
    return hook_registry.unregister_hook(hook_type, callback)


def get_hook(hook_type: Any) -> List[Callable]:
    """
    Get all callbacks for a hook from the global registry.
    
    Args:
        hook_type: Type or identifier of the hook
        
    Returns:
        List of callbacks for the hook
    """
    return hook_registry.get_hooks(hook_type)


def get_hooks() -> Dict[Any, List[Tuple[Callable, int]]]:
    """
    Get all hooks from the global registry.
    
    Returns:
        Dictionary of hook types to callbacks
    """
    return hook_registry.hooks


async def call_hook(hook_type: Any, *args: Any, **kwargs: Any) -> List[Any]:
    """
    Call all callbacks for a hook using the global registry.
    
    Args:
        hook_type: Type or identifier of the hook
        *args: Positional arguments to pass to the callbacks
        **kwargs: Keyword arguments to pass to the callbacks
        
    Returns:
        List of results from all callbacks
    """
    return await hook_registry.call_hooks(hook_type, *args, **kwargs)