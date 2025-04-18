"""
Tests for the dependency injection system.
"""
import pytest
from typing import Protocol, List, Optional, runtime_checkable

from uno.core.di.container import Container
from uno.core.di.scope import Scope
from uno.core.di.provider import Provider
from uno.core.di.protocols import ServiceLifetime, ProviderProtocol, ContainerProtocol, ScopeProtocol


# Test protocols
@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol for loggers."""
    
    def log(self, message: str) -> None:
        """Log a message."""
        ...


@runtime_checkable
class ConfigProtocol(Protocol):
    """Protocol for configuration."""
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value."""
        ...


@runtime_checkable
class ServiceProtocol(Protocol):
    """Protocol for services."""
    
    def do_something(self) -> str:
        """Do something."""
        ...


# Test implementations
class Logger:
    """Simple logger implementation."""
    
    def __init__(self):
        self.messages: List[str] = []
    
    def log(self, message: str) -> None:
        """Log a message."""
        self.messages.append(message)


class Config:
    """Simple configuration implementation."""
    
    def __init__(self, values: Optional[dict] = None):
        self.values = values or {}
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value."""
        return self.values.get(key, default)


class Service:
    """Simple service implementation."""
    
    def __init__(self, logger: LoggerProtocol, config: ConfigProtocol):
        self.logger = logger
        self.config = config
    
    def do_something(self) -> str:
        """Do something."""
        message = self.config.get("message", "Hello, World!")
        self.logger.log(f"Service did something: {message}")
        return message


class DisposableService:
    """Service that can be disposed."""
    
    def __init__(self):
        self.disposed = False
    
    def dispose(self) -> None:
        """Dispose of resources."""
        self.disposed = True


# Tests for the container
def test_container_registration():
    """Test registering services with the container."""
    container = Container()
    
    # Register services
    container.register(LoggerProtocol, Logger)
    container.register(ConfigProtocol, Config)
    container.register(ServiceProtocol, Service)
    
    # Check registrations
    assert container.is_registered(LoggerProtocol)
    assert container.is_registered(ConfigProtocol)
    assert container.is_registered(ServiceProtocol)
    assert not container.is_registered(str)


def test_container_resolve():
    """Test resolving services from the container."""
    container = Container()
    
    # Register services
    container.register(LoggerProtocol, Logger)
    container.register(ConfigProtocol, Config)
    container.register(ServiceProtocol, Service)
    
    # Resolve services
    logger = container.resolve(LoggerProtocol)
    config = container.resolve(ConfigProtocol)
    service = container.resolve(ServiceProtocol)
    
    # Check types
    assert isinstance(logger, Logger)
    assert isinstance(config, Config)
    assert isinstance(service, Service)
    
    # Check dependencies were injected
    assert service.logger is not None
    assert service.config is not None


def test_container_resolve_with_kwargs():
    """Test resolving services with additional parameters."""
    container = Container()
    
    # Register services
    container.register(ConfigProtocol, Config)
    
    # Resolve with values
    config = container.resolve(ConfigProtocol, values={"message": "Custom message"})
    
    # Check values were passed
    assert config.get("message") == "Custom message"


def test_container_singleton():
    """Test singleton service lifetime."""
    container = Container()
    
    # Register singleton
    container.register(LoggerProtocol, Logger, lifetime=ServiceLifetime.SINGLETON)
    
    # Resolve twice
    logger1 = container.resolve(LoggerProtocol)
    logger2 = container.resolve(LoggerProtocol)
    
    # Check same instance
    assert logger1 is logger2


def test_container_transient():
    """Test transient service lifetime."""
    container = Container()
    
    # Register transient
    container.register(LoggerProtocol, Logger, lifetime=ServiceLifetime.TRANSIENT)
    
    # Resolve twice
    logger1 = container.resolve(LoggerProtocol)
    logger2 = container.resolve(LoggerProtocol)
    
    # Check different instances
    assert logger1 is not logger2


def test_container_factory():
    """Test factory registration."""
    container = Container()
    
    # Define factory
    def config_factory(**kwargs):
        return Config(values={"message": "Factory message"})
    
    # Register factory
    container.register_factory(ConfigProtocol, config_factory)
    
    # Resolve
    config = container.resolve(ConfigProtocol)
    
    # Check factory was used
    assert config.get("message") == "Factory message"


def test_container_instance():
    """Test instance registration."""
    container = Container()
    
    # Create instance
    logger = Logger()
    
    # Register instance
    container.register_instance(LoggerProtocol, logger)
    
    # Resolve
    resolved = container.resolve(LoggerProtocol)
    
    # Check same instance
    assert resolved is logger


# Tests for scopes
def test_scope_create():
    """Test creating a scope."""
    container = Container()
    
    # Create scope
    scope = container.create_scope()
    
    # Check scope
    assert isinstance(scope, Scope)


def test_scope_get():
    """Test getting services from a scope."""
    container = Container()
    
    # Register services
    container.register(LoggerProtocol, Logger)
    container.register(ConfigProtocol, Config)
    container.register(ServiceProtocol, Service)
    
    # Create scope
    scope = container.create_scope()
    
    # Get services
    logger = scope.get(LoggerProtocol)
    config = scope.get(ConfigProtocol)
    service = scope.get(ServiceProtocol)
    
    # Check types
    assert isinstance(logger, Logger)
    assert isinstance(config, Config)
    assert isinstance(service, Service)


def test_scope_scoped_lifetime():
    """Test scoped service lifetime."""
    container = Container()
    
    # Register scoped service
    container.register(LoggerProtocol, Logger, lifetime=ServiceLifetime.SCOPED)
    
    # Create scopes
    scope1 = container.create_scope()
    scope2 = container.create_scope()
    
    # Get services from each scope
    logger1_1 = scope1.get(LoggerProtocol)
    logger1_2 = scope1.get(LoggerProtocol)
    logger2 = scope2.get(LoggerProtocol)
    
    # Check instances
    assert logger1_1 is logger1_2  # Same instance within same scope
    assert logger1_1 is not logger2  # Different instances between scopes


def test_scope_dispose():
    """Test disposing a scope."""
    container = Container()
    
    # Register disposable service
    container.register(DisposableService, lifetime=ServiceLifetime.SCOPED)
    
    # Create scope and get service
    scope = container.create_scope()
    service = scope.get(DisposableService)
    
    # Dispose scope
    scope.dispose()
    
    # Check service was disposed
    assert service.disposed


def test_scope_child():
    """Test creating a child scope."""
    container = Container()
    
    # Register singleton
    container.register(LoggerProtocol, Logger, lifetime=ServiceLifetime.SINGLETON)
    
    # Create parent and child scopes
    parent_scope = container.create_scope()
    child_scope = parent_scope.create_child_scope()
    
    # Get services
    parent_logger = parent_scope.get(LoggerProtocol)
    child_logger = child_scope.get(LoggerProtocol)
    
    # Check same instance (singleton)
    assert parent_logger is child_logger


# Tests for the provider
def test_provider_create():
    """Test creating a provider."""
    provider = Provider()
    
    # Check provider
    assert isinstance(provider, Provider)
    assert isinstance(provider, ProviderProtocol)


def test_provider_configure():
    """Test configuring a provider."""
    provider = Provider()
    
    # Configure
    provider.configure_services()
    
    # Check configured
    assert provider._configured


def test_provider_get_service():
    """Test getting a service from a provider."""
    container = Container()
    provider = Provider(container)
    
    # Register a service
    container.register(LoggerProtocol, Logger)
    
    # Get service
    logger = provider.get_service(LoggerProtocol)
    
    # Check service
    assert isinstance(logger, Logger)


def test_provider_create_scope():
    """Test creating a scope from a provider."""
    provider = Provider()
    
    # Create scope
    scope = provider.create_scope()
    
    # Check scope
    assert isinstance(scope, ScopeProtocol)


def test_provider_dispose():
    """Test disposing a provider."""
    container = Container()
    provider = Provider(container)
    
    # Register disposable service
    container.register(DisposableService, lifetime=ServiceLifetime.SCOPED)
    
    # Get service (creates root scope)
    service = provider.get_service(DisposableService)
    
    # Dispose provider
    provider.dispose()
    
    # Check service was disposed
    assert service.disposed


# Custom provider test
class CustomProvider(Provider):
    """Custom provider with pre-configured services."""
    
    def configure_services(self, container: Optional[ContainerProtocol] = None) -> None:
        """Configure services in the container."""
        container = container or self._container
        
        # Register services
        container.register(LoggerProtocol, Logger, lifetime=ServiceLifetime.SINGLETON)
        container.register(ConfigProtocol, Config, values={"app_name": "TestApp"})
        container.register(ServiceProtocol, Service)
        
        super().configure_services(container)


def test_custom_provider():
    """Test a custom provider with pre-configured services."""
    provider = CustomProvider()
    
    # Get services
    logger = provider.get_service(LoggerProtocol)
    config = provider.get_service(ConfigProtocol)
    service = provider.get_service(ServiceProtocol)
    
    # Check services
    assert isinstance(logger, Logger)
    assert isinstance(config, Config)
    assert isinstance(service, Service)
    
    # Check config values
    assert config.get("app_name") == "TestApp"