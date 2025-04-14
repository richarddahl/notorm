"""
Dependency Injection system for the Uno framework.

This module provides a comprehensive dependency injection system that focuses on
performance, type safety, and ease of use. It supports three service lifetimes:
singleton, scoped, and transient, with proper lifecycle management for resources.
"""

import inspect
import logging
from abc import abstractmethod
from contextlib import contextmanager, asynccontextmanager
from enum import Enum, auto
import threading
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Callable, cast, Generic, get_type_hints
import weakref

from .errors.base import ErrorCategory, UnoError
from .errors import with_error_context
from .protocols import ServiceProvider, ServiceScope, Initializable, Disposable, AsyncDisposable

# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")
TImpl = TypeVar("TImpl")

# =============================================================================
# Enums
# =============================================================================

class ServiceLifetime(Enum):
    """Defines the lifetime of a service in the dependency injection container."""
    
    SINGLETON = auto()  # Single instance for the entire application
    SCOPED = auto()     # New instance per scope
    TRANSIENT = auto()  # New instance per request


# =============================================================================
# Registration and Resolution
# =============================================================================

class ServiceRegistration(Generic[T]):
    """Represents a service registration in the dependency injection container."""
    
    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Type[T] | None = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Callable[..., T] | None = None,
        instance: T | None = None,
    ):
        """
        Initialize a service registration.
        
        Args:
            service_type: The type of service being registered
            implementation_type: The concrete implementation type
            lifetime: The service lifetime
            factory: Optional factory function to create instances
            instance: Optional existing instance to use
        """
        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.lifetime = lifetime
        self.factory = factory
        self.instance = instance
        
        # Validate the registration
        if instance is not None and lifetime != ServiceLifetime.SINGLETON:
            raise UnoError(
                message="Instance can only be provided for singleton services",
                error_code="INVALID_SERVICE_REGISTRATION",
                category=ErrorCategory.VALIDATION,
            )
        
        if factory is not None and implementation_type is not None and implementation_type != service_type:
            raise UnoError(
                message="Cannot specify both a factory and an implementation type",
                error_code="INVALID_SERVICE_REGISTRATION",
                category=ErrorCategory.VALIDATION,
            )


class ServiceRegistry:
    """Registry of service registrations in a dependency injection container."""
    
    def __init__(self):
        """Initialize an empty service registry."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        
    def register(self, registration: ServiceRegistration) -> None:
        """
        Register a service.
        
        Args:
            registration: The service registration
        """
        service_type = registration.service_type
        self._registrations[service_type] = registration
        
        # If it's a singleton with an instance, store it
        if registration.lifetime == ServiceLifetime.SINGLETON and registration.instance is not None:
            self._singleton_instances[service_type] = registration.instance
            
    def get_registration(self, service_type: Type[T]) -> Optional[ServiceRegistration]:
        """
        Get a service registration.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            The service registration, or None if not registered
        """
        return self._registrations.get(service_type)
    
    def has_registration(self, service_type: Type) -> bool:
        """
        Check if a service type is registered.
        
        Args:
            service_type: The type of service to check
            
        Returns:
            True if the service is registered, False otherwise
        """
        return service_type in self._registrations


# =============================================================================
# Service Scope Implementation
# =============================================================================

class ServiceScopeImpl(ServiceScope):
    """Implementation of a service scope for resolving scoped services."""
    
    def __init__(
        self,
        provider: "DIContainer",
        parent_scope: Optional["ServiceScopeImpl"] = None,
        scope_id: str = "default",
    ):
        """
        Initialize a service scope.
        
        Args:
            provider: The DI container that created this scope
            parent_scope: Optional parent scope
            scope_id: Identifier for this scope
        """
        self._provider = provider
        self._parent_scope = parent_scope
        self._scope_id = scope_id
        self._scoped_instances: Dict[Type, Any] = {}
        self._disposables: List[Disposable] = []
        self._async_disposables: List[AsyncDisposable] = []
        self._disposed = False
        self._logger = logging.getLogger(f"uno.di.scope.{scope_id}")
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service of the specified type.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            Instance of the requested service
            
        Raises:
            UnoError: If the scope has been disposed or the service is not registered
        """
        if self._disposed:
            raise UnoError(
                message=f"Cannot resolve service {service_type.__name__} from a disposed scope",
                error_code="SCOPE_DISPOSED",
                category=ErrorCategory.UNEXPECTED,
            )
        
        return self._provider._resolve_service(service_type, self)
    
    def dispose(self) -> None:
        """
        Dispose of the scope and its services.
        
        This method disposes all disposable services created within this scope.
        """
        if self._disposed:
            return
            
        # Dispose in reverse order of creation to handle dependencies correctly
        for disposable in reversed(self._disposables):
            try:
                disposable.dispose()
            except Exception as e:
                self._logger.error(f"Error disposing service: {str(e)}")
        
        self._scoped_instances.clear()
        self._disposables.clear()
        self._async_disposables.clear()
        self._disposed = True
    
    async def dispose_async(self) -> None:
        """
        Dispose of the scope and its services asynchronously.
        
        This method asynchronously disposes all async disposable services
        created within this scope.
        """
        if self._disposed:
            return
            
        # Dispose async disposables first
        for disposable in reversed(self._async_disposables):
            try:
                await disposable.dispose_async()
            except Exception as e:
                self._logger.error(f"Error async disposing service: {str(e)}")
        
        # Dispose synchronous disposables
        for disposable in reversed(self._disposables):
            try:
                disposable.dispose()
            except Exception as e:
                self._logger.error(f"Error disposing service: {str(e)}")
        
        self._scoped_instances.clear()
        self._disposables.clear()
        self._async_disposables.clear()
        self._disposed = True
    
    def __enter__(self) -> "ServiceScopeImpl":
        """Enter the scope context."""
        return self
    
    def __exit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Exit the scope context."""
        self.dispose()


# =============================================================================
# Main Container Implementation
# =============================================================================

class DIContainer(ServiceProvider):
    """
    Main dependency injection container implementation.
    
    The container manages service registrations and creates service instances
    according to their registered lifetime.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the DI container.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self._registry = ServiceRegistry()
        self._logger = logger or logging.getLogger("uno.di")
        self._root_scope = ServiceScopeImpl(self, None, "root")
        self._scope_lock = threading.RLock()
        self._initialization_lock = threading.RLock()
        self._initialized_services: Set[Type] = set()
        
        # Register the container itself
        self.register_instance(ServiceProvider, self)
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service of the specified type.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            Instance of the requested service
            
        Raises:
            UnoError: If the service is not registered
        """
        return self._resolve_service(service_type, self._root_scope)
    
    def register_singleton(self, service_type: Type[T], implementation: Type[T] | T | None = None) -> None:
        """
        Register a singleton service.
        
        Args:
            service_type: The type of service to register
            implementation: The implementation or instance to use
        """
        if implementation is None:
            # Self-registration
            self._register(service_type, None, ServiceLifetime.SINGLETON)
        elif isinstance(implementation, type):
            # Type-based registration
            self._register(service_type, implementation, ServiceLifetime.SINGLETON)
        else:
            # Instance-based registration
            self._register_instance(service_type, implementation)
    
    def register_scoped(self, service_type: Type[T], implementation: Type[T] | None = None) -> None:
        """
        Register a scoped service.
        
        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        self._register(service_type, implementation, ServiceLifetime.SCOPED)
    
    def register_transient(self, service_type: Type[T], implementation: Type[T] | None = None) -> None:
        """
        Register a transient service.
        
        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        self._register(service_type, implementation, ServiceLifetime.TRANSIENT)
    
    def register_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[..., T], 
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """
        Register a service with a factory function.
        
        Args:
            service_type: The type of service to register
            factory: Factory function to create instances
            lifetime: Service lifetime
        """
        registration = ServiceRegistration(
            service_type=service_type,
            lifetime=lifetime,
            factory=factory
        )
        self._registry.register(registration)
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance as a singleton service.
        
        Args:
            service_type: The type of service to register
            instance: The instance to use
        """
        self._register_instance(service_type, instance)
    
    def create_scope(self) -> ServiceScope:
        """
        Create a new service scope.
        
        Returns:
            The new service scope
        """
        with self._scope_lock:
            return ServiceScopeImpl(self, self._root_scope, f"scope_{id(threading.current_thread())}")
    
    @contextmanager
    def create_scope_context(self, scope_id: Optional[str] = None) -> ServiceScope:
        """
        Create a new service scope with context manager support.
        
        Args:
            scope_id: Optional scope identifier
            
        Yields:
            The new service scope
        """
        scope = ServiceScopeImpl(
            self, 
            self._root_scope, 
            scope_id or f"scope_{id(threading.current_thread())}"
        )
        
        try:
            yield scope
        finally:
            scope.dispose()
    
    @asynccontextmanager
    async def create_async_scope(self, scope_id: Optional[str] = None) -> ServiceScope:
        """
        Create a new service scope with async context manager support.
        
        Args:
            scope_id: Optional scope identifier
            
        Yields:
            The new service scope
        """
        scope = ServiceScopeImpl(
            self, 
            self._root_scope, 
            scope_id or f"scope_{id(threading.current_thread())}"
        )
        
        try:
            yield scope
        finally:
            await scope.dispose_async()
    
    def _register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]],
        lifetime: ServiceLifetime
    ) -> None:
        """
        Register a service with the given lifetime.
        
        Args:
            service_type: The type of service to register
            implementation_type: The concrete implementation type
            lifetime: The service lifetime
        """
        registration = ServiceRegistration(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime
        )
        self._registry.register(registration)
    
    def _register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance.
        
        Args:
            service_type: The type of service to register
            instance: The instance to use
        """
        registration = ServiceRegistration(
            service_type=service_type,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance
        )
        self._registry.register(registration)
    
    def _resolve_service(self, service_type: Type[T], scope: ServiceScopeImpl) -> T:
        """
        Resolve a service based on its registration.
        
        Args:
            service_type: The type of service to resolve
            scope: The active service scope
            
        Returns:
            An instance of the requested service
            
        Raises:
            UnoError: If the service is not registered or cannot be created
        """
        with with_error_context(service_type=service_type.__name__):
            # Check if the service is registered
            registration = self._registry.get_registration(service_type)
            if registration is None:
                raise UnoError(
                    message=f"Service {service_type.__name__} is not registered",
                    error_code="SERVICE_NOT_REGISTERED",
                    category=ErrorCategory.UNEXPECTED,
                )
            
            # Handle different lifetime cases
            if registration.lifetime == ServiceLifetime.SINGLETON:
                # Use existing instance if available
                if service_type in self._registry._singleton_instances:
                    return self._registry._singleton_instances[service_type]
                
                # Create and store singleton instance
                instance = self._create_instance(registration, scope)
                self._registry._singleton_instances[service_type] = instance
                return instance
                
            elif registration.lifetime == ServiceLifetime.SCOPED:
                # Check if already created in this scope
                if service_type in scope._scoped_instances:
                    return scope._scoped_instances[service_type]
                
                # Create and store scoped instance
                instance = self._create_instance(registration, scope)
                scope._scoped_instances[service_type] = instance
                return instance
                
            else:  # TRANSIENT
                # Always create a new instance
                return self._create_instance(registration, scope)
    
    def _create_instance(self, registration: ServiceRegistration, scope: ServiceScopeImpl) -> Any:
        """
        Create a service instance based on its registration.
        
        Args:
            registration: The service registration
            scope: The active service scope
            
        Returns:
            The created service instance
            
        Raises:
            UnoError: If the service cannot be created
        """
        try:
            instance = None
            
            # Use factory if provided
            if registration.factory is not None:
                instance = registration.factory()
            else:
                # Get implementation type to instantiate
                impl_type = registration.implementation_type
                
                # Get constructor parameters
                constructor = impl_type.__init__
                if constructor is object.__init__:
                    # No custom constructor
                    instance = impl_type()
                else:
                    # Resolve constructor parameters
                    params = inspect.signature(constructor).parameters
                    
                    # Skip 'self' parameter
                    args = {}
                    for name, param in params.items():
                        if name == 'self':
                            continue
                        
                        # Get parameter type hint
                        type_hints = get_type_hints(constructor)
                        if name in type_hints:
                            param_type = type_hints[name]
                            # Resolve from container
                            args[name] = self._resolve_service(param_type, scope)
                        else:
                            # Handle parameters without type hints
                            if param.default is inspect.Parameter.empty:
                                raise UnoError(
                                    message=f"Cannot resolve parameter '{name}' for {impl_type.__name__} without type hint",
                                    error_code="MISSING_TYPE_HINT",
                                    category=ErrorCategory.UNEXPECTED,
                                )
                    
                    # Create instance with resolved parameters
                    instance = impl_type(**args)
            
            # Add to disposal tracking if applicable
            if instance is not None:
                if isinstance(instance, Disposable):
                    scope._disposables.append(instance)
                if isinstance(instance, AsyncDisposable):
                    scope._async_disposables.append(instance)
                
                # Initialize if needed
                if isinstance(instance, Initializable) and registration.service_type not in self._initialized_services:
                    with self._initialization_lock:
                        if registration.service_type not in self._initialized_services:
                            instance.initialize()
                            self._initialized_services.add(registration.service_type)
            
            return instance
        except Exception as e:
            # Wrap in UnoError if not already
            if not isinstance(e, UnoError):
                raise UnoError(
                    message=f"Failed to create instance of {registration.service_type.__name__}: {str(e)}",
                    error_code="SERVICE_CREATION_FAILED",
                    category=ErrorCategory.UNEXPECTED,
                    cause=e
                )
            raise


# =============================================================================
# Public API Functions
# =============================================================================

# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    Get the global DI container instance.
    
    Returns:
        The global container instance
        
    Raises:
        UnoError: If the container is not initialized
    """
    global _container
    if _container is None:
        raise UnoError(
            message="DI container is not initialized",
            error_code="CONTAINER_NOT_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    return _container


def initialize_container(logger: Optional[logging.Logger] = None) -> None:
    """
    Initialize the global DI container.
    
    Args:
        logger: Optional logger for diagnostic information
        
    Raises:
        UnoError: If the container is already initialized
    """
    global _container
    if _container is not None:
        raise UnoError(
            message="DI container is already initialized",
            error_code="CONTAINER_ALREADY_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    _container = DIContainer(logger)


def reset_container() -> None:
    """Reset the global DI container (primarily for testing)."""
    global _container
    _container = None


def get_service(service_type: Type[T]) -> T:
    """
    Get a service from the global container.
    
    Args:
        service_type: The type of service to get
        
    Returns:
        Instance of the requested service
    """
    return get_container().get_service(service_type)


@contextmanager
def create_scope(scope_id: Optional[str] = None) -> ServiceScope:
    """
    Create a new service scope from the global container.
    
    Args:
        scope_id: Optional scope identifier
        
    Yields:
        The new service scope
    """
    with get_container().create_scope_context(scope_id) as scope:
        yield scope


@asynccontextmanager
async def create_async_scope(scope_id: Optional[str] = None) -> ServiceScope:
    """
    Create a new async service scope from the global container.
    
    Args:
        scope_id: Optional scope identifier
        
    Yields:
        The new service scope
    """
    async with get_container().create_async_scope(scope_id) as scope:
        yield scope