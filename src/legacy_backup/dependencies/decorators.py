"""
Dependency injection decorators for Uno framework.

This module provides decorators that can be used to automatically register
services with the dependency injection container and to inject dependencies
into functions and methods.
"""

import inspect
import functools
import logging
from enum import Enum
from typing import Dict, Any, Type, TypeVar, Optional, Union, Callable, Generic, cast, get_type_hints, List, Set

from uno.dependencies.interfaces import ConfigProtocol

from uno.dependencies.scoped_container import ServiceScope
from uno.dependencies.modern_provider import get_service_provider


T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def service(
    service_type: Optional[Type] = None,
    scope: ServiceScope = ServiceScope.SINGLETON,
    auto_register: bool = True
) -> Callable[[Type[T]], Type[T]]:
    """
    Register a class as a service.
    
    This decorator registers a class as a service with the dependency injection
    container, allowing it to be resolved by other services.
    
    Args:
        service_type: Optional interface type to register the service as
        scope: The service lifetime scope
        auto_register: Whether to automatically register the service
        
    Returns:
        A decorator function that registers the class
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Store metadata on the class for manual registration
        setattr(cls, "__uno_service__", True)
        setattr(cls, "__uno_service_type__", service_type or cls)
        setattr(cls, "__uno_service_scope__", scope)
        
        # If auto_register is True, register the service immediately
        if auto_register:
            try:
                # Get the current ServiceCollection from initialization or create a new one
                from uno.dependencies.scoped_container import get_container
                try:
                    container = get_container()
                    container.register(
                        service_type or cls,
                        cls,
                        scope,
                        {}  # No params, will be resolved by the container
                    )
                except RuntimeError:
                    # Container not initialized yet, service will be registered during startup
                    pass
            except ImportError:
                # Module not available, skip registration
                pass
        
        return cls
    
    return decorator


def singleton(service_type: Optional[Type] = None) -> Callable[[Type[T]], Type[T]]:
    """
    Register a class as a singleton service.
    
    This decorator registers a class as a singleton service with the dependency
    injection container, allowing it to be resolved by other services.
    
    Args:
        service_type: Optional interface type to register the service as
        
    Returns:
        A decorator function that registers the class
    """
    return service(service_type, ServiceScope.SINGLETON)


def scoped(service_type: Optional[Type] = None) -> Callable[[Type[T]], Type[T]]:
    """
    Register a class as a scoped service.
    
    This decorator registers a class as a scoped service with the dependency
    injection container, allowing it to be resolved by other services.
    
    Args:
        service_type: Optional interface type to register the service as
        
    Returns:
        A decorator function that registers the class
    """
    return service(service_type, ServiceScope.SCOPED)


def transient(service_type: Optional[Type] = None) -> Callable[[Type[T]], Type[T]]:
    """
    Register a class as a transient service.
    
    This decorator registers a class as a transient service with the dependency
    injection container, allowing it to be resolved by other services.
    
    Args:
        service_type: Optional interface type to register the service as
        
    Returns:
        A decorator function that registers the class
    """
    return service(service_type, ServiceScope.TRANSIENT)


def inject(*dependencies: Type[Any]) -> Callable[[F], F]:
    """
    Inject dependencies into a function or method.
    
    This decorator injects dependencies into a function or method, resolving
    them from the dependency injection container.
    
    Args:
        *dependencies: Types of dependencies to inject
        
    Returns:
        A decorator function that injects dependencies
        
    Example:
        @inject(ConfigProtocol, UnoDatabaseProviderProtocol)
        def my_function(config, db_provider):
            # Use config and db_provider
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the service provider
            provider = get_service_provider()
            
            # Resolve dependencies
            resolved_deps = [provider.get_service(dep) for dep in dependencies]
            
            # Call the function with dependencies
            return func(*args, *resolved_deps, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def inject_params() -> Callable[[F], F]:
    """
    Inject dependencies based on parameter types.
    
    This decorator injects dependencies into a function or method based on
    the parameter type annotations, resolving them from the dependency injection
    container.
    
    Returns:
        A decorator function that injects dependencies
        
    Example:
        @inject_params()
        def my_function(config: ConfigProtocol, db_provider: UnoDatabaseProviderProtocol):
            # Use config and db_provider
            pass
    """
    def decorator(func: F) -> F:
        # Get parameter type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Determine which parameters to inject
        params_to_inject = {
            name: type_hints[name]
            for name, param in sig.parameters.items()
            if name in type_hints and param.default is param.empty
        }
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip self or cls for methods
            offset = 0
            if args and inspect.ismethod(func) or (
                inspect.isfunction(func) and 
                func.__name__ == "__init__" and 
                len(args) > 0
            ):
                offset = 1
            
            # Get the service provider
            provider = get_service_provider()
            
            # Calculate which parameters still need to be injected
            num_args = len(args) - offset
            param_names = list(params_to_inject.keys())
            remaining_params = {
                name: type_
                for i, (name, type_) in enumerate(params_to_inject.items())
                if i >= num_args and name not in kwargs
            }
            
            # Resolve remaining dependencies
            for name, type_ in remaining_params.items():
                try:
                    kwargs[name] = provider.get_service(type_)
                except Exception as e:
                    logging.getLogger("uno.di").warning(f"Error injecting {name}: {e}")
            
            # Call the function with dependencies
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def injectable_class() -> Callable[[Type[T]], Type[T]]:
    """
    Make a class's constructor use dependency injection.
    
    This decorator makes a class's constructor use dependency injection to
    resolve its parameters.
    
    Returns:
        A decorator function that makes the class's constructor injectable
        
    Example:
        @injectable_class()
        class MyService:
            def __init__(self, config: ConfigProtocol, db_provider: UnoDatabaseProviderProtocol):
                self.config = config
                self.db_provider = db_provider
    """
    def decorator(cls: Type[T]) -> Type[T]:
        original_init = cls.__init__
        
        # Apply inject_params to the constructor
        cls.__init__ = inject_params()(original_init)  # type: ignore
        
        return cls
    
    return decorator


def injectable_endpoint() -> Callable[[F], F]:
    """
    Make a FastAPI endpoint use dependency injection.
    
    This decorator makes a FastAPI endpoint use dependency injection to
    resolve its parameters.
    
    Returns:
        A decorator function that makes the endpoint injectable
        
    Example:
        @app.get("/example")
        @injectable_endpoint()
        async def example_endpoint(
            request: Request,
            config: ConfigProtocol,
            db_provider: UnoDatabaseProviderProtocol
        ):
            # Use request, config, and db_provider
            pass
    """
    def decorator(func: F) -> F:
        # Get parameter type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Determine which parameters to inject
        params_to_inject = {
            name: type_hints[name]
            for name, param in sig.parameters.items()
            if name in type_hints and param.default is param.empty
            # Skip parameters typically provided by FastAPI
            and name not in {"request", "response", "background_tasks", "depends"}
        }
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip self or cls for methods
            offset = 0
            if args and inspect.ismethod(func):
                offset = 1
            
            # Get the service provider
            provider = get_service_provider()
            
            # Create a scope for this request
            async with provider.create_scope() as scope:
                # Calculate which parameters still need to be injected
                num_args = len(args) - offset
                param_names = list(params_to_inject.keys())
                remaining_params = {
                    name: type_
                    for i, (name, type_) in enumerate(params_to_inject.items())
                    if i >= num_args and name not in kwargs
                }
                
                # Resolve remaining dependencies from scope
                for name, type_ in remaining_params.items():
                    try:
                        kwargs[name] = scope.resolve(type_)
                    except Exception as e:
                        logging.getLogger("uno.di").warning(f"Error injecting {name}: {e}")
                
                # Call the function with dependencies
                return await func(*args, **kwargs)
        
        # If it's not an async function, wrap it differently
        if not inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Skip self or cls for methods
                offset = 0
                if args and inspect.ismethod(func):
                    offset = 1
                
                # Get the service provider
                provider = get_service_provider()
                
                # Calculate which parameters still need to be injected
                num_args = len(args) - offset
                param_names = list(params_to_inject.keys())
                remaining_params = {
                    name: type_
                    for i, (name, type_) in enumerate(params_to_inject.items())
                    if i >= num_args and name not in kwargs
                }
                
                # Resolve remaining dependencies
                for name, type_ in remaining_params.items():
                    try:
                        kwargs[name] = provider.get_service(type_)
                    except Exception as e:
                        logging.getLogger("uno.di").warning(f"Error injecting {name}: {e}")
                
                # Call the function with dependencies
                return func(*args, **kwargs)
            
            return cast(F, sync_wrapper)
        
        return cast(F, wrapper)
    
    return decorator