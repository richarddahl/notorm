"""
Component discovery for documentation generation.

This module provides tools for discovering components in the codebase that
should be documented, such as models, endpoints, and schemas.
"""

import importlib
import inspect
import pkgutil
import sys
import re
from typing import Any, Dict, List, Optional, Set, Type, Callable, Union, Tuple


class DocProvider:
    """Provider for documentation components."""
    
    def __init__(self, name: str, discovery_fn: Callable[[List[str]], List[Any]]):
        """
        Initialize a documentation provider.
        
        Args:
            name: Name of the component type provided
            discovery_fn: Function to discover components
        """
        self.name = name
        self.discovery_fn = discovery_fn


class DocDiscovery:
    """
    Discovers components to document from the codebase.
    
    This class manages the registration and execution of component discovery
    functions for various types of components (models, endpoints, etc.).
    """
    
    def __init__(self):
        """Initialize the discovery system."""
        self.providers: Dict[str, DocProvider] = {}
    
    def register_provider(self, provider: DocProvider) -> None:
        """
        Register a documentation provider.
        
        Args:
            provider: Provider to register
        """
        self.providers[provider.name] = provider
    
    def discover(self, modules: List[str]) -> Dict[str, List[Any]]:
        """
        Discover components to document.
        
        Args:
            modules: List of module paths to search
            
        Returns:
            Dictionary of discovered components by type
        """
        result = {}
        
        for provider_name, provider in self.providers.items():
            discovered = provider.discovery_fn(modules)
            result[provider_name] = discovered
        
        return result


def discover_modules(root_modules: List[str]) -> List[str]:
    """
    Discover all modules under the given root modules.
    
    Args:
        root_modules: List of root module paths
        
    Returns:
        List of all module paths
    """
    result = []
    
    for root_module_name in root_modules:
        try:
            root_module = importlib.import_module(root_module_name)
        except ImportError as e:
            print(f"Error importing {root_module_name}: {e}")
            continue
        
        result.append(root_module_name)
        
        if hasattr(root_module, "__path__"):
            # It's a package, recursively import submodules
            for _, name, is_pkg in pkgutil.iter_modules(root_module.__path__, f"{root_module_name}."):
                result.append(name)
                
                # If it's a subpackage, recursively import its submodules
                if is_pkg:
                    try:
                        subpackage = importlib.import_module(name)
                        if hasattr(subpackage, "__path__"):
                            for submodule in discover_modules([name]):
                                if submodule not in result:
                                    result.append(submodule)
                    except ImportError:
                        # Skip if can't import
                        pass
    
    return result


def discover_models(modules: List[str]) -> List[Type]:
    """
    Discover model classes from the given modules.
    
    Args:
        modules: List of module paths to search
        
    Returns:
        List of discovered model classes
    """
    result = []
    
    # Model class naming patterns
    model_patterns = [
        r".*Model$",  # Classes ending with "Model"
        r".*Schema$",  # Classes ending with "Schema"
        r".*DTO$",     # Classes ending with "DTO"
        r".*Entity$"   # Classes ending with "Entity"
    ]
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            # Skip if can't import
            continue
        
        for name, obj in inspect.getmembers(module):
            # Check if it's a class
            if not inspect.isclass(obj):
                continue
                
            # Skip imported classes (only include classes defined in this module)
            if obj.__module__ != module_name:
                continue
            
            # Check if class has Model-like name
            is_model_name = any(re.match(pattern, name) for pattern in model_patterns)
            
            # Check if class has dataclass decorator or pydantic base
            is_dataclass = hasattr(obj, "__dataclass_fields__")
            is_pydantic = "pydantic" in str(obj.__bases__)
            
            # Check for typical model attributes
            has_model_attrs = (
                hasattr(obj, "__annotations__") or
                hasattr(obj, "schema") or
                hasattr(obj, "model_fields")
            )
            
            # Consider it a model if it meets name criteria or has model characteristics
            if is_model_name or (has_model_attrs and (is_dataclass or is_pydantic)):
                result.append(obj)
    
    return result


def discover_endpoints(modules: List[str]) -> List[Any]:
    """
    Discover endpoint functions or classes from the given modules.
    
    Args:
        modules: List of module paths to search
        
    Returns:
        List of discovered endpoint functions or classes
    """
    result = []
    
    # FastAPI decorator patterns
    fastapi_patterns = [
        r"@.*\.get\(",
        r"@.*\.post\(",
        r"@.*\.put\(",
        r"@.*\.delete\(",
        r"@.*\.patch\(",
        r"@.*\.options\(",
        r"@.*\.head\("
    ]
    
    # Class-based endpoint patterns
    endpoint_class_patterns = [
        r".*Handler$",
        r".*Controller$",
        r".*Resource$",
        r".*Endpoint$"
    ]
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            # Skip if can't import
            continue
        
        for name, obj in inspect.getmembers(module):
            # Skip private members
            if name.startswith("_"):
                continue
            
            # Check for endpoint functions (decorated with FastAPI decorators)
            if inspect.isfunction(obj) and obj.__module__ == module_name:
                try:
                    source = inspect.getsource(obj)
                    if any(re.search(pattern, source) for pattern in fastapi_patterns):
                        result.append(obj)
                except (OSError, TypeError):
                    # Can't get source, skip
                    pass
            
            # Check for class-based endpoints
            if inspect.isclass(obj) and obj.__module__ == module_name:
                # Check class name patterns
                is_endpoint_class = any(re.match(pattern, name) for pattern in endpoint_class_patterns)
                
                # Check for HTTP method handlers
                has_http_methods = any(
                    hasattr(obj, method) and inspect.isfunction(getattr(obj, method))
                    for method in ["get", "post", "put", "delete", "patch", "options", "head"]
                )
                
                if is_endpoint_class or has_http_methods:
                    result.append(obj)
    
    return result


def discover_schemas(modules: List[str]) -> List[Any]:
    """
    Discover API schemas from the given modules.
    
    Args:
        modules: List of module paths to search
        
    Returns:
        List of discovered API schemas
    """
    result = []
    
    # This is a placeholder implementation
    # The actual implementation would depend on how schemas are defined
    
    return result


# Register standard providers
def register_doc_provider(discovery: DocDiscovery, name: str, discovery_fn: Callable[[List[str]], List[Any]]) -> None:
    """
    Register a documentation provider.
    
    Args:
        discovery: Discovery instance to register with
        name: Name of the component type provided
        discovery_fn: Function to discover components
    """
    provider = DocProvider(name, discovery_fn)
    discovery.register_provider(provider)


def discover_components() -> DocDiscovery:
    """
    Create and initialize a DocDiscovery instance with standard providers.
    
    Returns:
        Initialized DocDiscovery instance
    """
    discovery = DocDiscovery()
    
    # Register standard providers
    register_doc_provider(discovery, "model", discover_models)
    register_doc_provider(discovery, "endpoint", discover_endpoints)
    register_doc_provider(discovery, "schema", discover_schemas)
    
    return discovery