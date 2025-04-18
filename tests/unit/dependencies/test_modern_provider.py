"""
Tests for the modern service provider implementation.

This module tests the UnoServiceProvider and related DI functionality,
ensuring proper service registration, resolution, lifecycle management,
and scope handling.
"""

import asyncio
import logging
import pytest
from typing import Dict, List, Any, Optional, Protocol, TypeVar, Type
from unittest.mock import AsyncMock, MagicMock, patch

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
    register_singleton,
    get_service_provider,
    T,
)
from uno.dependencies.scoped_container import (
    ServiceCollection,
    ServiceScope,
    ServiceResolver,
    initialize_container,
    get_container,
    get_service,
    create_scope,
    create_async_scope,
)
from uno.core.errors.core_errors import (
    DependencyNotFoundError,
    DependencyResolutionError,
    DependencyCycleError,
)


# =============================================================================
# Test Protocols and Classes
# =============================================================================

class TestServiceProtocol(Protocol):
    """Protocol for test services."""
    
    def get_value(self) -> str:
        """Get a value from the service."""
        ...


class TestDependencyProtocol(Protocol):
    """Protocol for test dependencies."""
    
    def get_name(self) -> str:
        """Get the name of the dependency."""
        ...


class TestConfigProtocol(Protocol):
    """Protocol for test configuration."""
    
    def get_setting(self, key: str) -> Any:
        """Get a configuration setting."""
        ...


class TestService(TestServiceProtocol):
    """Concrete implementation of TestServiceProtocol."""
    
    def __init__(self, value: str = "default"):
        self.value = value
    
    def get_value(self) -> str:
        return self.value


class TestDependency(TestDependencyProtocol):
    """Concrete implementation of TestDependencyProtocol."""
    
    def __init__(self, name: str = "dependency"):
        self.name = name
    
    def get_name(self) -> str:
        return self.name


class TestConfig(TestConfigProtocol):
    """Concrete implementation of TestConfigProtocol."""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.settings = settings or {"default": "value"}
    
    def get_setting(self, key: str) -> Any:
        return self.settings.get(key)


class TestLifecycleService(ServiceLifecycle):
    """Test service with lifecycle hooks."""
    
    def __init__(self):
        self.initialized = False
        self.disposed = False
        self.initialize_count = 0
        self.dispose_count = 0
    
    async def initialize(self) -> None:
        self.initialized = True
        self.initialize_count += 1
    
    async def dispose(self) -> None:
        self.disposed = True
        self.dispose_count += 1


class TestDependentService:
    """Service that depends on other services."""
    
    def __init__(self, dependency: TestDependencyProtocol, config: TestConfigProtocol):
        self.dependency = dependency
        self.config = config
    
    def get_combined(self) -> str:
        return f"{self.dependency.get_name()}:{self.config.get_setting('default')}"


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def clean_container():
    """Reset the container before and after each test."""
    # Clean up any existing container
    from uno.dependencies.scoped_container import _container
    # Create new empty container
    initialize_container(ServiceCollection())
    yield
    # Reset after test
    initialize_container(ServiceCollection())


@pytest.fixture
def service_provider(clean_container):
    """Create a fresh service provider for testing."""
    provider = UnoServiceProvider(logger=logging.getLogger("test"))
    return provider


@pytest.fixture
def service_collection():
    """Create a service collection for testing."""
    collection = ServiceCollection()
    return collection


# =============================================================================
# Test Cases
# =============================================================================

class TestUnoServiceProvider:
    """Tests for the UnoServiceProvider class."""
    
    @pytest.mark.asyncio
    async def test_basic_service_registration_and_resolution(self, service_provider, service_collection):
        """Test basic service registration and resolution."""
        # Arrange
        service_collection.add_singleton(TestServiceProtocol, TestService, value="test_value")
        service_provider.configure_services(service_collection)
        
        # Act
        await service_provider.initialize()
        service = service_provider.get_service(TestServiceProtocol)
        
        # Assert
        assert service_provider.is_initialized()
        assert isinstance(service, TestService)
        assert service.get_value() == "test_value"
    
    @pytest.mark.asyncio
    async def test_extension_registration(self, service_provider, service_collection):
        """Test registering service extensions."""
        # Arrange
        service_collection.add_singleton(TestServiceProtocol, TestService, value="base")
        service_provider.configure_services(service_collection)
        
        # Create extension
        extension = ServiceCollection()
        extension.add_singleton(TestDependencyProtocol, TestDependency, name="extension")
        service_provider.register_extension("test_extension", extension)
        
        # Act
        await service_provider.initialize()
        service = service_provider.get_service(TestServiceProtocol)
        dependency = service_provider.get_service(TestDependencyProtocol)
        
        # Assert
        assert service.get_value() == "base"
        assert dependency.get_name() == "extension"
    
    @pytest.mark.asyncio
    async def test_lifecycle_service(self, service_provider, service_collection):
        """Test service lifecycle management."""
        # Arrange
        lifecycle_service = TestLifecycleService()
        service_collection.add_instance(TestLifecycleService, lifecycle_service)
        service_provider.configure_services(service_collection)
        service_provider.register_lifecycle_service(TestLifecycleService)
        
        # Act - Initialize
        await service_provider.initialize()
        
        # Assert - Initialized
        assert lifecycle_service.initialized
        assert lifecycle_service.initialize_count == 1
        assert not lifecycle_service.disposed
        
        # Act - Shutdown
        await service_provider.shutdown()
        
        # Assert - Disposed
        assert lifecycle_service.disposed
        assert lifecycle_service.dispose_count == 1
        assert not service_provider.is_initialized()
    
    @pytest.mark.asyncio
    async def test_reconfigure_after_init_error(self, service_provider, service_collection):
        """Test that reconfiguring after initialization raises an error."""
        # Arrange
        service_collection.add_singleton(TestServiceProtocol, TestService)
        service_provider.configure_services(service_collection)
        
        # Act - Initialize
        await service_provider.initialize()
        
        # Assert - Can't reconfigure
        with pytest.raises(Exception, match="Services have already been initialized"):
            service_provider.configure_services(ServiceCollection())
    
    @pytest.mark.asyncio
    async def test_extension_after_init_error(self, service_provider, service_collection):
        """Test that adding extensions after initialization raises an error."""
        # Arrange
        service_collection.add_singleton(TestServiceProtocol, TestService)
        service_provider.configure_services(service_collection)
        
        # Act - Initialize
        await service_provider.initialize()
        
        # Assert - Can't add extensions
        with pytest.raises(Exception, match="Services have already been initialized"):
            service_provider.register_extension("late_extension", ServiceCollection())
    
    @pytest.mark.asyncio
    async def test_service_resolution_before_init_error(self, service_provider, service_collection):
        """Test that resolving services before initialization raises an error."""
        # Arrange
        service_collection.add_singleton(TestServiceProtocol, TestService)
        service_provider.configure_services(service_collection)
        
        # Assert - Can't resolve yet
        with pytest.raises(Exception, match="Service provider must be initialized"):
            service_provider.get_service(TestServiceProtocol)
    
    @pytest.mark.asyncio
    async def test_service_in_scope(self, service_provider, service_collection):
        """Test resolving services in a scope."""
        # Arrange
        service_collection.add_scoped(TestServiceProtocol, TestService, value="scoped_value")
        service_provider.configure_services(service_collection)
        await service_provider.initialize()
        
        # Act - Get in scope
        service1 = service_provider.get_service_in_scope(TestServiceProtocol, "scope1")
        service2 = service_provider.get_service_in_scope(TestServiceProtocol, "scope2")
        
        # Assert - Different instances
        assert isinstance(service1, TestService)
        assert isinstance(service2, TestService)
        assert service1 is not service2
    
    @pytest.mark.asyncio
    async def test_async_scope(self, service_provider, service_collection):
        """Test async scope management."""
        # Arrange
        service_collection.add_scoped(TestServiceProtocol, TestService, value="async_scope")
        service_provider.configure_services(service_collection)
        await service_provider.initialize()
        
        # Act - Use async scope
        async with service_provider.create_scope("test_scope") as scope:
            service = scope.resolve(TestServiceProtocol)
            assert service.get_value() == "async_scope"
    
    @pytest.mark.asyncio
    async def test_service_dependency_resolution(self, service_provider, service_collection):
        """Test automatic resolution of service dependencies."""
        # Arrange
        service_collection.add_singleton(TestDependencyProtocol, TestDependency, name="test_dep")
        service_collection.add_singleton(TestConfigProtocol, TestConfig)
        service_collection.add_singleton(
            TestDependentService,
            TestDependentService,
            dependency=None,  # Will be auto-resolved
            config=None       # Will be auto-resolved
        )
        service_provider.configure_services(service_collection)
        
        # Act
        await service_provider.initialize()
        dependent_service = service_provider.get_service(TestDependentService)
        
        # Assert
        assert dependent_service.get_combined() == "test_dep:value"
    
    @pytest.mark.asyncio
    async def test_register_singleton_function(self, service_provider, service_collection, clean_container):
        """Test the register_singleton helper function."""
        # Arrange
        service_provider.configure_services(service_collection)
        await service_provider.initialize()
        
        # Act
        instance = TestService(value="singleton_value")
        register_singleton(TestServiceProtocol, instance)
        
        # Assert
        resolved = service_provider.get_service(TestServiceProtocol)
        assert resolved is instance
        assert resolved.get_value() == "singleton_value"
    
    @pytest.mark.asyncio
    async def test_global_service_provider(self, clean_container):
        """Test the global service provider instance."""
        # Arrange
        provider = get_service_provider()
        collection = ServiceCollection()
        collection.add_singleton(TestServiceProtocol, TestService, value="global_test")
        provider.configure_services(collection)
        
        # Act
        await provider.initialize()
        
        # Assert
        assert provider.is_initialized()
        service = provider.get_service(TestServiceProtocol)
        assert service.get_value() == "global_test"
        
        # Clean up
        await provider.shutdown()


class TestServiceCollectionIntegration:
    """Tests for integration with ServiceCollection."""
    
    def test_singleton_registration(self, service_collection):
        """Test registering a singleton service."""
        # Arrange & Act
        service_collection.add_singleton(TestServiceProtocol, TestService, value="singleton_test")
        
        # Assert
        registrations = service_collection._registrations
        assert TestServiceProtocol in registrations
        assert registrations[TestServiceProtocol].scope == ServiceScope.SINGLETON
    
    def test_scoped_registration(self, service_collection):
        """Test registering a scoped service."""
        # Arrange & Act
        service_collection.add_scoped(TestServiceProtocol, TestService, value="scoped_test")
        
        # Assert
        registrations = service_collection._registrations
        assert TestServiceProtocol in registrations
        assert registrations[TestServiceProtocol].scope == ServiceScope.SCOPED
    
    def test_transient_registration(self, service_collection):
        """Test registering a transient service."""
        # Arrange & Act
        service_collection.add_transient(TestServiceProtocol, TestService, value="transient_test")
        
        # Assert
        registrations = service_collection._registrations
        assert TestServiceProtocol in registrations
        assert registrations[TestServiceProtocol].scope == ServiceScope.TRANSIENT
    
    def test_instance_registration(self, service_collection):
        """Test registering a service instance."""
        # Arrange
        instance = TestService(value="instance_test")
        
        # Act
        service_collection.add_instance(TestServiceProtocol, instance)
        
        # Assert
        instances = service_collection._instances
        assert TestServiceProtocol in instances
        assert instances[TestServiceProtocol] is instance
    
    @pytest.mark.asyncio
    async def test_factory_registration(self, service_collection, clean_container):
        """Test registering a factory function."""
        # Arrange
        def create_service():
            return TestService(value="factory_test")
        
        # Act
        service_collection.add_factory(TestServiceProtocol, create_service)
        
        # Initialize container
        initialize_container(service_collection)
        
        # Assert
        service = get_service(TestServiceProtocol)
        assert service.get_value() == "factory_test"
    
    @pytest.mark.asyncio
    async def test_complex_dependencies(self, service_collection, clean_container):
        """Test registering and resolving complex dependency chains."""
        # Arrange
        # First level dependency
        service_collection.add_singleton(TestDependencyProtocol, TestDependency, name="complex_dep")
        
        # Second level dependency using the first
        class SecondLevelService:
            def __init__(self, dep: TestDependencyProtocol):
                self.dep = dep
            def get_value(self):
                return f"second:{self.dep.get_name()}"
        
        service_collection.add_singleton(SecondLevelService, SecondLevelService)
        
        # Third level dependency using the second
        class ThirdLevelService:
            def __init__(self, second: SecondLevelService, dep: TestDependencyProtocol):
                self.second = second
                self.dep = dep
            def get_value(self):
                return f"third:{self.second.get_value()}:{self.dep.get_name()}"
        
        service_collection.add_singleton(ThirdLevelService, ThirdLevelService)
        
        # Initialize container
        initialize_container(service_collection)
        
        # Act
        third = get_service(ThirdLevelService)
        
        # Assert
        assert third.get_value() == "third:second:complex_dep:complex_dep"