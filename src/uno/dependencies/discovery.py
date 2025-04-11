"""
Service discovery for Uno framework.

This module provides utilities for discovering services in the codebase
and automatically registering them with the dependency injection container.
"""

import inspect
import importlib
import pkgutil
import logging
import pathlib
from typing import Dict, Any, Type, TypeVar, Optional, Union, List, Set, cast, Callable, Iterator

from uno.dependencies.scoped_container import ServiceScope, ServiceCollection
from uno.dependencies.modern_provider import UnoServiceProvider, get_service_provider


T = TypeVar('T')


def find_modules(package_name: str) -> Iterator[str]:
    """
    Find all modules in a package.
    
    Args:
        package_name: The name of the package to search
        
    Yields:
        Module names
    """
    package = importlib.import_module(package_name)
    package_path = getattr(package, '__path__', None)
    
    if package_path:
        for loader, name, is_pkg in pkgutil.iter_modules(package_path):
            full_name = f"{package_name}.{name}"
            yield full_name
            
            if is_pkg:
                yield from find_modules(full_name)


def get_class_metadata(cls: Type) -> Dict[str, Any]:
    """
    Get metadata for a service class.
    
    Args:
        cls: The class to get metadata for
        
    Returns:
        A dictionary of metadata
    """
    is_service = hasattr(cls, "__uno_service__") and getattr(cls, "__uno_service__")
    
    if not is_service:
        return {}
    
    service_type = getattr(cls, "__uno_service_type__", cls)
    scope = getattr(cls, "__uno_service_scope__", ServiceScope.SINGLETON)
    
    return {
        "is_service": is_service,
        "service_type": service_type,
        "scope": scope
    }


def discover_services(
    package_name: str,
    service_collection: Optional[ServiceCollection] = None,
    logger: Optional[logging.Logger] = None
) -> ServiceCollection:
    """
    Discover and register services in a package.
    
    Args:
        package_name: The name of the package to search
        service_collection: Optional service collection to add services to
        logger: Optional logger for diagnostic information
        
    Returns:
        A service collection with all discovered services
    """
    logger = logger or logging.getLogger("uno.discovery")
    service_collection = service_collection or ServiceCollection()
    
    module_names = list(find_modules(package_name))
    logger.info(f"Discovered {len(module_names)} modules in {package_name}")
    
    # Import all modules
    modules = []
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            modules.append(module)
        except ImportError as e:
            logger.warning(f"Error importing module {module_name}: {e}")
    
    # Find all classes in the modules
    service_count = 0
    for module in modules:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip classes not defined in this module
            if obj.__module__ != module.__name__:
                continue
            
            # Get metadata
            metadata = get_class_metadata(obj)
            if not metadata.get("is_service", False):
                continue
            
            # Register the service
            service_type = metadata["service_type"]
            scope = metadata["scope"]
            
            if scope == ServiceScope.SINGLETON:
                service_collection.add_singleton(service_type, obj)
            elif scope == ServiceScope.SCOPED:
                service_collection.add_scoped(service_type, obj)
            elif scope == ServiceScope.TRANSIENT:
                service_collection.add_transient(service_type, obj)
            
            service_count += 1
            logger.debug(f"Discovered service {obj.__name__} as {service_type.__name__} with scope {scope.name}")
    
    logger.info(f"Discovered {service_count} services in {package_name}")
    return service_collection


def register_services_in_package(
    package_name: str,
    provider: Optional[UnoServiceProvider] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Discover and register services in a package.
    
    Args:
        package_name: The name of the package to search
        provider: Optional service provider to register services with
        logger: Optional logger for diagnostic information
    """
    provider = provider or get_service_provider()
    logger = logger or logging.getLogger("uno.discovery")
    
    services = discover_services(package_name, logger=logger)
    
    # Register with the provider
    extension_name = package_name.split(".")[-1]
    provider.register_extension(extension_name, services)
    logger.info(f"Registered services from {package_name} as extension '{extension_name}'")


def scan_directory_for_services(
    directory: Union[str, pathlib.Path],
    base_package: str,
    provider: Optional[UnoServiceProvider] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Scan a directory for packages containing services.
    
    Args:
        directory: The directory to scan
        base_package: The base package name
        provider: Optional service provider to register services with
        logger: Optional logger for diagnostic information
    """
    provider = provider or get_service_provider()
    logger = logger or logging.getLogger("uno.discovery")
    
    path = pathlib.Path(directory) if isinstance(directory, str) else directory
    
    # Find all subdirectories with an __init__.py file
    packages = [
        d.name
        for d in path.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    ]
    
    logger.info(f"Found {len(packages)} packages in {path}")
    
    # Register services in each package
    for package in packages:
        package_name = f"{base_package}.{package}"
        try:
            register_services_in_package(package_name, provider, logger)
        except Exception as e:
            logger.error(f"Error registering services in {package_name}: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())