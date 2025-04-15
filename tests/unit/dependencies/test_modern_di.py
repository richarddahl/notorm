"""
Unit tests for modern dependency injection.

This module contains tests for the new dependency injection components,
including the scoped container, service provider, and decorators.
"""

import pytest
import asyncio
from typing import Protocol, List, Dict, Any, Optional

from uno.dependencies.scoped_container import (
    ServiceScope,
    ServiceCollection,
    ServiceResolver,
    initialize_container,
    get_container,
    get_service,
    create_scope,
    create_async_scope,
)
from uno.dependencies.decorators import (
    service,
    singleton,
    scoped,
    transient,
    inject,
    inject_params,
    injectable_class,
)


# Test interfaces
class TestServiceProtocol(Protocol):
    """Protocol for test services."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    def get_value(self) -> str: ...


class SingletonServiceProtocol(Protocol):
    """Protocol for singleton services."""

    def get_id(self) -> int: ...


class ScopedServiceProtocol(Protocol):
    """Protocol for scoped services."""

    def get_id(self) -> int: ...


class TransientServiceProtocol(Protocol):
    """Protocol for transient services."""

    def get_id(self) -> int: ...


class DependentServiceProtocol(Protocol):
    """Protocol for services with dependencies."""

    def get_value(self) -> str: ...


# Test implementations
class TestService:
    """Test service implementation."""

    def get_value(self) -> str:
        return "test"


@singleton(TestServiceProtocol)
class SingletonService:
    """Singleton service implementation."""

    def __init__(self):
        self._id = id(self)

    def get_id(self) -> int:
        return self._id


@scoped(ScopedServiceProtocol)
class ScopedService:
    """Scoped service implementation."""

    def __init__(self):
        self._id = id(self)

    def get_id(self) -> int:
        return self._id


@transient(TransientServiceProtocol)
class TransientService:
    """Transient service implementation."""

    def __init__(self):
        self._id = id(self)

    def get_id(self) -> int:
        return self._id


@injectable_class()
class DependentService:
    """Service with dependencies."""

    def __init__(self, test_service: TestServiceProtocol):
        self.test_service = test_service

    def get_value(self) -> str:
        return f"Dependent: {self.test_service.get_value()}"


# Test functions
@inject(TestServiceProtocol)
def test_function_with_inject(test_service):
    """Function with injected dependencies."""
    return f"Function: {test_service.get_value()}"


@inject_params()
def test_function_with_inject_params(test_service: TestServiceProtocol):
    """Function with parameters injected based on types."""
    return f"Function: {test_service.get_value()}"


class TestScopedContainer:
    """Tests for the scoped container."""

    def test_service_collection(self):
        """Test creating a service collection."""
        # Create a service collection
        services = ServiceCollection()

        # Add some services
        services.add_singleton(TestServiceProtocol, TestService)
        services.add_instance(SingletonServiceProtocol, SingletonService())
        services.add_scoped(ScopedServiceProtocol, ScopedService)
        services.add_transient(TransientServiceProtocol, TransientService)

        # Build a container
        container = services.build()

        # Verify services are registered
        assert container.resolve(TestServiceProtocol).get_value() == "test"
        assert isinstance(container.resolve(SingletonServiceProtocol), SingletonService)
        assert isinstance(container.resolve(ScopedServiceProtocol), ScopedService)
        assert isinstance(container.resolve(TransientServiceProtocol), TransientService)

    def test_singleton_resolution(self):
        """Test resolving singleton services."""
        # Create a service collection
        services = ServiceCollection()
        services.add_singleton(SingletonServiceProtocol, SingletonService)

        # Build a container
        container = services.build()

        # Get the service multiple times
        service1 = container.resolve(SingletonServiceProtocol)
        service2 = container.resolve(SingletonServiceProtocol)

        # Verify they are the same instance
        assert service1.get_id() == service2.get_id()

    def test_scoped_resolution(self):
        """Test resolving scoped services."""
        # Create a service collection
        services = ServiceCollection()
        services.add_scoped(ScopedServiceProtocol, ScopedService)

        # Build a container
        container = services.build()

        # Create two scopes
        with container.create_scope("scope1") as scope1:
            # Get the service in scope 1
            service1a = scope1.resolve(ScopedServiceProtocol)
            service1b = scope1.resolve(ScopedServiceProtocol)

            # Verify they are the same instance within the scope
            assert service1a.get_id() == service1b.get_id()

            # Create a different scope
            with container.create_scope("scope2") as scope2:
                # Get the service in scope 2
                service2 = scope2.resolve(ScopedServiceProtocol)

                # Verify it's a different instance
                assert service1a.get_id() != service2.get_id()

    def test_transient_resolution(self):
        """Test resolving transient services."""
        # Create a service collection
        services = ServiceCollection()
        services.add_transient(TransientServiceProtocol, TransientService)

        # Build a container
        container = services.build()

        # Get the service multiple times
        service1 = container.resolve(TransientServiceProtocol)
        service2 = container.resolve(TransientServiceProtocol)

        # Verify they are different instances
        assert service1.get_id() != service2.get_id()

    def test_dependency_resolution(self):
        """Test resolving services with dependencies."""
        # Create a service collection
        services = ServiceCollection()
        services.add_singleton(TestServiceProtocol, TestService)
        services.add_singleton(DependentServiceProtocol, DependentService)

        # Build a container
        container = services.build()

        # Get the dependent service
        service = container.resolve(DependentServiceProtocol)

        # Verify its dependency was resolved
        assert service.get_value() == "Dependent: test"

    @pytest.mark.asyncio
    async def test_async_scope(self):
        """Test async scope."""
        # Create a service collection
        services = ServiceCollection()
        services.add_scoped(ScopedServiceProtocol, ScopedService)

        # Build a container
        container = services.build()

        # Create an async scope
        async with container.create_async_scope("async_scope") as scope:
            # Get the service
            service1 = scope.resolve(ScopedServiceProtocol)
            service2 = scope.resolve(ScopedServiceProtocol)

            # Verify they are the same instance
            assert service1.get_id() == service2.get_id()


class TestDecorators:
    """Tests for dependency injection decorators."""

    def setup_method(self):
        """Set up the test."""
        # Create a service collection
        services = ServiceCollection()
        services.add_singleton(TestServiceProtocol, TestService)
        services.add_singleton(SingletonServiceProtocol, SingletonService)
        services.add_scoped(ScopedServiceProtocol, ScopedService)
        services.add_transient(TransientServiceProtocol, TransientService)
        services.add_singleton(DependentServiceProtocol, DependentService)

        # Initialize the container
        initialize_container(services)

    def test_service_decorator(self):
        """Test service decorator."""

        # Define a service with the decorator
        @service(TestServiceProtocol, ServiceScope.SINGLETON, False)
        class DecoratedService:
            def get_value(self) -> str:
                return "decorated"

        # Verify the decorator set the metadata
        assert getattr(DecoratedService, "__uno_service__", False)
        assert getattr(DecoratedService, "__uno_service_type__") == TestServiceProtocol
        assert (
            getattr(DecoratedService, "__uno_service_scope__") == ServiceScope.SINGLETON
        )

    def test_singleton_decorator(self):
        """Test singleton decorator."""

        # Define a service with the decorator
        @singleton(TestServiceProtocol)
        class DecoratedSingleton:
            def get_value(self) -> str:
                return "singleton"

        # Verify the decorator set the metadata
        assert getattr(DecoratedSingleton, "__uno_service__", False)
        assert (
            getattr(DecoratedSingleton, "__uno_service_type__") == TestServiceProtocol
        )
        assert (
            getattr(DecoratedSingleton, "__uno_service_scope__")
            == ServiceScope.SINGLETON
        )

    def test_scoped_decorator(self):
        """Test scoped decorator."""

        # Define a service with the decorator
        @scoped(TestServiceProtocol)
        class DecoratedScoped:
            def get_value(self) -> str:
                return "scoped"

        # Verify the decorator set the metadata
        assert getattr(DecoratedScoped, "__uno_service__", False)
        assert getattr(DecoratedScoped, "__uno_service_type__") == TestServiceProtocol
        assert getattr(DecoratedScoped, "__uno_service_scope__") == ServiceScope.SCOPED

    def test_transient_decorator(self):
        """Test transient decorator."""

        # Define a service with the decorator
        @transient(TestServiceProtocol)
        class DecoratedTransient:
            def get_value(self) -> str:
                return "transient"

        # Verify the decorator set the metadata
        assert getattr(DecoratedTransient, "__uno_service__", False)
        assert (
            getattr(DecoratedTransient, "__uno_service_type__") == TestServiceProtocol
        )
        assert (
            getattr(DecoratedTransient, "__uno_service_scope__")
            == ServiceScope.TRANSIENT
        )

    def test_inject_decorator(self):
        """Test inject decorator."""
        # Call a function with the decorator
        result = test_function_with_inject()

        # Verify the dependency was injected
        assert result == "Function: test"

    def test_inject_params_decorator(self):
        """Test inject_params decorator."""
        # Call a function with the decorator
        result = test_function_with_inject_params()

        # Verify the dependency was injected
        assert result == "Function: test"

    def test_injectable_class_decorator(self):
        """Test injectable_class decorator."""
        # Get a service with the decorator
        service = get_service(DependentServiceProtocol)

        # Verify the dependency was injected
        assert service.get_value() == "Dependent: test"
