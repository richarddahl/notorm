"""
Tests for the scoped container implementation.

This module tests the ServiceCollection, ServiceScope, and related
functionality for dependency injection container scopes.
"""

import asyncio
import logging
import pytest
from typing import Dict, List, Any, Optional, Protocol, TypeVar, Type
from unittest.mock import AsyncMock, MagicMock, patch

from uno.dependencies.scoped_container import (
    ServiceCollection,
    ServiceScope,
    ServiceResolver,
    ServiceRegistration,
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


class DisposableProtocol(Protocol):
    """Protocol for disposable services."""
    
    async def dispose(self) -> None:
        """Dispose the service."""
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


class DisposableService(DisposableProtocol):
    """Concrete implementation of DisposableProtocol."""
    
    def __init__(self):
        self.disposed = False
    
    async def dispose(self) -> None:
        self.disposed = True


class DependentService:
    """Service that depends on other services."""
    
    def __init__(self, dependency: TestDependencyProtocol, service: TestServiceProtocol):
        self.dependency = dependency
        self.service = service
    
    def get_combined(self) -> str:
        return f"{self.dependency.get_name()}:{self.service.get_value()}"


class DisposableScope:
    """Service that implements an async context manager for disposing."""
    
    def __init__(self, name: str = "scope"):
        self.name = name
        self.disposed = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.dispose()
    
    async def dispose(self):
        self.disposed = True


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
def service_collection():
    """Create a service collection for testing."""
    collection = ServiceCollection()
    return collection


# =============================================================================
# Test Cases
# =============================================================================

class TestServiceCollection:
    """Tests for the ServiceCollection class."""
    
    def test_singleton_registration(self, service_collection):
        """Test registering a singleton service."""
        # Arrange & Act
        service_collection.add_singleton(TestServiceProtocol, TestService, value="singleton_test")
        
        # Assert
        registrations = service_collection._registrations
        assert TestServiceProtocol in registrations
        assert registrations[TestServiceProtocol].scope == ServiceScope.SINGLETON
        assert registrations[TestServiceProtocol].implementation == TestService
        assert registrations[TestServiceProtocol].params == {"value": "singleton_test"}
    
    def test_scoped_registration(self, service_collection):
        """Test registering a scoped service."""
        # Arrange & Act
        service_collection.add_scoped(TestServiceProtocol, TestService, value="scoped_test")
        
        # Assert
        registrations = service_collection._registrations
        assert TestServiceProtocol in registrations
        assert registrations[TestServiceProtocol].scope == ServiceScope.SCOPED
        assert registrations[TestServiceProtocol].params == {"value": "scoped_test"}
    
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
    
    def test_factory_registration(self, service_collection):
        """Test registering a factory function."""
        # Arrange
        def create_service():
            return TestService(value="factory_test")
        
        # Act
        service_collection.add_factory(TestServiceProtocol, create_service)
        
        # Assert
        factories = service_collection._factories
        assert TestServiceProtocol in factories
        assert factories[TestServiceProtocol]() is not None
        assert factories[TestServiceProtocol]().get_value() == "factory_test"


class TestServiceResolver:
    """Tests for service resolution."""
    
    @pytest.mark.asyncio
    async def test_singleton_resolution(self, service_collection, clean_container):
        """Test resolving a singleton service."""
        # Arrange
        service_collection.add_singleton(TestServiceProtocol, TestService, value="singleton_value")
        initialize_container(service_collection)
        
        # Act
        service1 = get_service(TestServiceProtocol)
        service2 = get_service(TestServiceProtocol)
        
        # Assert
        assert isinstance(service1, TestService)
        assert service1.get_value() == "singleton_value"
        assert service1 is service2  # Same instance
    
    @pytest.mark.asyncio
    async def test_scoped_resolution(self, service_collection, clean_container):
        """Test resolving a scoped service."""
        # Arrange
        service_collection.add_scoped(TestServiceProtocol, TestService, value="scoped_value")
        initialize_container(service_collection)
        
        # Act
        with create_scope("scope1") as scope1:
            service1 = scope1.resolve(TestServiceProtocol)
            service1_again = scope1.resolve(TestServiceProtocol)
            
            with create_scope("scope2") as scope2:
                service2 = scope2.resolve(TestServiceProtocol)
        
        # Assert
        assert isinstance(service1, TestService)
        assert service1.get_value() == "scoped_value"
        assert service1 is service1_again  # Same instance within scope
        assert service1 is not service2  # Different instances across scopes
    
    @pytest.mark.asyncio
    async def test_transient_resolution(self, service_collection, clean_container):
        """Test resolving a transient service."""
        # Arrange
        service_collection.add_transient(TestServiceProtocol, TestService, value="transient_value")
        initialize_container(service_collection)
        
        # Act
        service1 = get_service(TestServiceProtocol)
        service2 = get_service(TestServiceProtocol)
        
        # Assert
        assert isinstance(service1, TestService)
        assert service1.get_value() == "transient_value"
        assert service1 is not service2  # Different instances
    
    @pytest.mark.asyncio
    async def test_instance_resolution(self, service_collection, clean_container):
        """Test resolving a registered instance."""
        # Arrange
        instance = TestService(value="instance_value")
        service_collection.add_instance(TestServiceProtocol, instance)
        initialize_container(service_collection)
        
        # Act
        resolved = get_service(TestServiceProtocol)
        
        # Assert
        assert resolved is instance
        assert resolved.get_value() == "instance_value"
    
    @pytest.mark.asyncio
    async def test_factory_resolution(self, service_collection, clean_container):
        """Test resolving a service from a factory."""
        # Arrange
        counter = 0
        
        def create_service():
            nonlocal counter
            counter += 1
            return TestService(value=f"factory_{counter}")
        
        service_collection.add_factory(TestServiceProtocol, create_service)
        initialize_container(service_collection)
        
        # Act
        service1 = get_service(TestServiceProtocol)
        service2 = get_service(TestServiceProtocol)
        
        # Assert
        assert isinstance(service1, TestService)
        assert service1.get_value() == "factory_1"
        assert service2.get_value() == "factory_2"
        assert service1 is not service2  # Different instances
    
    @pytest.mark.asyncio
    async def test_dependency_resolution(self, service_collection, clean_container):
        """Test automatic resolution of dependencies."""
        # Arrange
        service_collection.add_singleton(TestDependencyProtocol, TestDependency, name="test_dep")
        service_collection.add_singleton(TestServiceProtocol, TestService, value="test_service")
        service_collection.add_singleton(DependentService, DependentService)
        initialize_container(service_collection)
        
        # Act
        service = get_service(DependentService)
        
        # Assert
        assert isinstance(service, DependentService)
        assert service.get_combined() == "test_dep:test_service"
    
    @pytest.mark.asyncio
    async def test_dependency_not_found(self, service_collection, clean_container):
        """Test error when dependency is not found."""
        # Arrange
        class MissingDependencyService:
            def __init__(self, missing: Type):
                self.missing = missing
        
        service_collection.add_singleton(MissingDependencyService, MissingDependencyService)
        initialize_container(service_collection)
        
        # Act & Assert
        with pytest.raises(DependencyNotFoundError):
            get_service(MissingDependencyService)
    
    @pytest.mark.asyncio
    async def test_dependency_cycle(self, service_collection, clean_container):
        """Test error when there is a dependency cycle."""
        # Arrange
        class Service1:
            def __init__(self, service2: "Service2"):
                self.service2 = service2
        
        class Service2:
            def __init__(self, service1: Service1):
                self.service1 = service1
        
        service_collection.add_singleton(Service1, Service1)
        service_collection.add_singleton(Service2, Service2)
        initialize_container(service_collection)
        
        # Act & Assert
        with pytest.raises(DependencyCycleError):
            get_service(Service1)


class TestAsyncScope:
    """Tests for async scopes."""
    
    @pytest.mark.asyncio
    async def test_async_scope_basic(self, service_collection, clean_container):
        """Test basic async scope functionality."""
        # Arrange
        service_collection.add_scoped(TestServiceProtocol, TestService, value="async_scoped")
        initialize_container(service_collection)
        
        # Act
        async with create_async_scope("async_scope") as scope:
            service1 = scope.resolve(TestServiceProtocol)
            service2 = scope.resolve(TestServiceProtocol)
        
        # Assert
        assert isinstance(service1, TestService)
        assert service1.get_value() == "async_scoped"
        assert service1 is service2  # Same instance within scope
    
    @pytest.mark.asyncio
    async def test_async_scope_disposal(self, service_collection, clean_container):
        """Test that disposable services are disposed when the scope ends."""
        # Arrange
        disposable = DisposableService()
        service_collection.add_instance(DisposableService, disposable)
        initialize_container(service_collection)
        
        # Act
        async with create_async_scope("async_scope") as scope:
            service = scope.resolve(DisposableService)
            assert not service.disposed
        
        # Assert
        assert service.disposed
    
    @pytest.mark.asyncio
    async def test_nested_async_scopes(self, service_collection, clean_container):
        """Test nested async scopes."""
        # Arrange
        service_collection.add_scoped(TestServiceProtocol, TestService, value="parent_scope")
        service_collection.add_scoped(DisposableScope, DisposableScope, name="test_scope")
        initialize_container(service_collection)
        
        # Act
        parent_scope_service = None
        child_scope_service = None
        
        async with create_async_scope("parent") as parent_scope:
            parent_scope_service = parent_scope.resolve(TestServiceProtocol)
            parent_disposable = parent_scope.resolve(DisposableScope)
            
            async with create_async_scope("child") as child_scope:
                child_scope_service = child_scope.resolve(TestServiceProtocol)
                child_disposable = child_scope.resolve(DisposableScope)
                
                # Assert during scope
                assert not parent_disposable.disposed
                assert not child_disposable.disposed
                assert parent_scope_service is not child_scope_service  # Different instances
            
            # Assert after child scope
            assert not parent_disposable.disposed
            assert child_disposable.disposed
        
        # Assert after parent scope
        assert parent_disposable.disposed