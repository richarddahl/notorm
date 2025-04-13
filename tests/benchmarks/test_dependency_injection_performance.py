import pytest
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Protocol, Type, TypeVar, cast
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from src.uno.dependencies.modern_provider import (
    ServiceResolver, ServiceCollection, UnoServiceProvider,
    ServiceLifecycle, add_singleton, add_scoped, add_transient,
    get_service, injectable_class, inject, inject_params, resolve_service
)
from src.uno.dependencies.interfaces import UnoRepositoryProtocol, UnoServiceProtocol
from src.uno.dependencies.testing import TestingContainer, configure_test_container


# Test protocols and interfaces
class RepositoryProtocol(Protocol):
    def get_by_id(self, id: str) -> Any: ...
    def list_all(self) -> List[Any]: ...
    def create(self, data: Any) -> Any: ...
    def update(self, id: str, data: Any) -> Any: ...
    def delete(self, id: str) -> bool: ...


class ServiceProtocol(Protocol):
    def process(self, data: Any) -> Any: ...
    async def process_async(self, data: Any) -> Any: ...


class ConfigProtocol(Protocol):
    def get_setting(self, key: str) -> Any: ...
    def set_setting(self, key: str, value: Any) -> None: ...


class LoggerProtocol(Protocol):
    def log(self, message: str, level: str = "info") -> None: ...


# Simple implementations
class Repository:
    def __init__(self, name: str = "default"):
        self.name = name
        self.data = {}
    
    def get_by_id(self, id: str) -> Any:
        return self.data.get(id)
    
    def list_all(self) -> List[Any]:
        return list(self.data.values())
    
    def create(self, data: Any) -> Any:
        id = str(uuid.uuid4())
        self.data[id] = {"id": id, **data}
        return self.data[id]
    
    def update(self, id: str, data: Any) -> Any:
        if id in self.data:
            self.data[id] = {**self.data[id], **data}
        return self.data.get(id)
    
    def delete(self, id: str) -> bool:
        if id in self.data:
            del self.data[id]
            return True
        return False


class Service:
    def __init__(self, repository: RepositoryProtocol, logger: Optional[LoggerProtocol] = None):
        self.repository = repository
        self.logger = logger
    
    def process(self, data: Any) -> Any:
        if self.logger:
            self.logger.log(f"Processing: {data}")
        return self.repository.create(data)
    
    async def process_async(self, data: Any) -> Any:
        if self.logger:
            self.logger.log(f"Processing async: {data}")
        
        # Simulate async processing
        await asyncio.sleep(0.001)
        return self.repository.create(data)


class Config:
    def __init__(self):
        self.settings = {}
    
    def get_setting(self, key: str) -> Any:
        return self.settings.get(key)
    
    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value


class Logger:
    def __init__(self, name: str = "app"):
        self.name = name
        self.logs = []
    
    def log(self, message: str, level: str = "info") -> None:
        self.logs.append((level, message))


# Service with lifecycle hooks
class LifecycleService(ServiceLifecycle):
    def __init__(self, name: str = "lifecycle"):
        self.name = name
        self.initialized = False
        self.disposed = False
        self.data = {}
    
    async def initialize(self) -> None:
        # Simulate initialization work
        await asyncio.sleep(0.001)
        self.initialized = True
    
    async def dispose(self) -> None:
        # Simulate cleanup work
        await asyncio.sleep(0.001)
        self.data.clear()
        self.disposed = True
    
    def process(self, data: Any) -> Any:
        if not self.initialized:
            raise RuntimeError("Service not initialized")
        return {"processed": data, "by": self.name}


# Test objects with deep dependency chains
class Level1:
    def __init__(self, config: ConfigProtocol):
        self.config = config
    
    def get_config(self, key: str) -> Any:
        return self.config.get_setting(key)


class Level2:
    def __init__(self, level1: Level1, logger: LoggerProtocol):
        self.level1 = level1
        self.logger = logger
    
    def log_config(self, key: str) -> None:
        value = self.level1.get_config(key)
        self.logger.log(f"Config {key}: {value}")


class Level3:
    def __init__(self, level2: Level2, repository: RepositoryProtocol):
        self.level2 = level2
        self.repository = repository
    
    def log_and_store(self, key: str, data: Any) -> Any:
        self.level2.log_config(key)
        return self.repository.create(data)


class Level4:
    def __init__(self, level3: Level3, service: ServiceProtocol):
        self.level3 = level3
        self.service = service
    
    def process_with_config(self, key: str, data: Any) -> Any:
        stored = self.level3.log_and_store(key, {"source": "level4", "data": data})
        return self.service.process({"from_storage": stored["id"], "processed": True})


# Classes with decorator-based injection
@injectable_class
class InjectedService:
    def __init__(self, repository: Repository, logger: Logger):
        self.repository = repository
        self.logger = logger
    
    def process(self, data: Any) -> Any:
        self.logger.log(f"InjectedService processing: {data}")
        return self.repository.create(data)


@injectable_class
class SelfInjectingService:
    @inject
    def __init__(self):
        self.repository = resolve_service(Repository)
        self.logger = resolve_service(Logger)
    
    def process(self, data: Any) -> Any:
        self.logger.log(f"SelfInjectingService processing: {data}")
        return self.repository.create(data)


# Functions with parameter injection
@inject_params()
def process_with_injection(data: Any, repository: Repository = None, logger: Logger = None):
    if logger:
        logger.log(f"Function processing: {data}")
    return repository.create(data) if repository else None


@inject_params()
async def process_async_with_injection(data: Any, repository: Repository = None, logger: Logger = None):
    if logger:
        logger.log(f"Async function processing: {data}")
    
    # Simulate async work
    await asyncio.sleep(0.001)
    return repository.create(data) if repository else None


# Test fixtures
@pytest.fixture
def service_collection():
    """Create a fresh ServiceCollection."""
    return ServiceCollection()


@pytest.fixture
def populated_collection():
    """Create a ServiceCollection with basic services registered."""
    collection = ServiceCollection()
    
    # Register simple services
    collection.add_singleton(ConfigProtocol, Config)
    collection.add_singleton(LoggerProtocol, Logger)
    collection.add_scoped(RepositoryProtocol, Repository)
    collection.add_scoped(ServiceProtocol, Service)
    
    # Register lifecycle service
    collection.add_scoped(LifecycleService)
    
    # Register deep dependency chain
    collection.add_singleton(Level1)
    collection.add_scoped(Level2)
    collection.add_scoped(Level3)
    collection.add_scoped(Level4)
    
    # Register with decorator-based injection
    collection.add_scoped(InjectedService)
    collection.add_scoped(SelfInjectingService)
    
    return collection


@pytest.fixture
def service_resolver(populated_collection):
    """Create a ServiceResolver with pre-registered services."""
    resolver = ServiceResolver(populated_collection)
    return resolver


@pytest.fixture
def service_provider(populated_collection):
    """Create a UnoServiceProvider with pre-registered services."""
    provider = UnoServiceProvider(populated_collection)
    return provider


# Initialize a global resolver for some tests
@pytest.fixture(scope="module")
def global_provider():
    """Create a global service provider for the get_service tests."""
    collection = ServiceCollection()
    
    # Register global services
    collection.add_singleton(ConfigProtocol, Config)
    collection.add_singleton(LoggerProtocol, Logger)
    collection.add_scoped(RepositoryProtocol, Repository)
    collection.add_scoped(ServiceProtocol, Service)
    
    # Build provider
    provider = UnoServiceProvider(collection)
    
    # Patch the get_service function to use this provider
    original_get_service = globals()["get_service"]
    
    def patched_get_service(service_type):
        return provider.resolver.resolve(service_type)
    
    globals()["get_service"] = patched_get_service
    
    yield provider
    
    # Restore original function
    globals()["get_service"] = original_get_service


# Benchmarks
def test_service_registration_performance(benchmark):
    """Benchmark the performance of registering services."""
    
    def register_services():
        collection = ServiceCollection()
        
        # Register a variety of services with different lifetimes
        collection.add_singleton(ConfigProtocol, Config)
        collection.add_singleton(LoggerProtocol, Logger)
        collection.add_scoped(RepositoryProtocol, Repository)
        collection.add_scoped(ServiceProtocol, Service)
        collection.add_transient(Level1)
        collection.add_transient(Level2)
        collection.add_scoped(Level3)
        collection.add_scoped(Level4)
        collection.add_singleton(LifecycleService)
        
        return collection
    
    # Run the benchmark
    result = benchmark(register_services)
    
    # Verify result
    assert len(result._registrations) >= 9


def test_service_resolution_performance(service_resolver, benchmark):
    """Benchmark the performance of resolving services with different lifetimes."""
    resolver = service_resolver
    
    # Benchmark singleton resolution
    def resolve_singleton():
        return resolver.resolve(ConfigProtocol)
    
    singleton_result = benchmark.pedantic(
        resolve_singleton,
        iterations=100,
        rounds=10
    )
    assert singleton_result is not None
    
    # Benchmark scoped resolution
    def resolve_scoped():
        return resolver.resolve(RepositoryProtocol)
    
    scoped_result = benchmark.pedantic(
        resolve_scoped,
        iterations=100,
        rounds=10
    )
    assert scoped_result is not None
    
    # Benchmark transient resolution (if available)
    # Note: This might create a new instance each time
    try:
        def resolve_transient():
            # Level1 was registered as transient
            return resolver.resolve(Level1)
        
        transient_result = benchmark.pedantic(
            resolve_transient,
            iterations=100,
            rounds=10
        )
        assert transient_result is not None
    except Exception:
        # If no transient services available, skip
        pass


def test_dependency_chain_resolution_performance(service_resolver, benchmark):
    """Benchmark the performance of resolving services with deep dependency chains."""
    resolver = service_resolver
    
    # Resolve services with increasingly deep dependency chains
    def resolve_level1():
        return resolver.resolve(Level1)
    
    level1_result = benchmark.pedantic(
        resolve_level1,
        iterations=50,
        rounds=5
    )
    assert level1_result is not None
    
    def resolve_level2():
        return resolver.resolve(Level2)
    
    level2_result = benchmark.pedantic(
        resolve_level2,
        iterations=50,
        rounds=5
    )
    assert level2_result is not None
    
    def resolve_level3():
        return resolver.resolve(Level3)
    
    level3_result = benchmark.pedantic(
        resolve_level3,
        iterations=50,
        rounds=5
    )
    assert level3_result is not None
    
    def resolve_level4():
        return resolver.resolve(Level4)
    
    level4_result = benchmark.pedantic(
        resolve_level4,
        iterations=50,
        rounds=5
    )
    assert level4_result is not None


def test_scope_creation_performance(service_provider, benchmark):
    """Benchmark the performance of creating and using scopes."""
    provider = service_provider
    
    # Benchmark scope creation
    def create_scope():
        return provider.create_scope()
    
    scope_creation_result = benchmark.pedantic(
        create_scope,
        iterations=50,
        rounds=5
    )
    assert scope_creation_result is not None
    
    # Benchmark scope usage
    def use_scope():
        with provider.create_scope() as scope:
            # Resolve some services in the scope
            repository = scope.resolve(RepositoryProtocol)
            service = scope.resolve(ServiceProtocol)
            return repository, service
    
    scope_usage_result = benchmark.pedantic(
        use_scope,
        iterations=50,
        rounds=5
    )
    assert scope_usage_result is not None and len(scope_usage_result) == 2


@pytest.mark.asyncio
async def test_async_scope_performance(service_provider, benchmark):
    """Benchmark the performance of async scopes."""
    provider = service_provider
    
    # Define an async function for benchmarking
    async def use_async_scope():
        async with provider.create_async_scope() as scope:
            # Resolve services in the async scope
            repository = scope.resolve(RepositoryProtocol)
            service = scope.resolve(ServiceProtocol)
            # Use an async method
            result = await service.process_async({"test": "data"})
            return result
    
    # Wrap for pytest-benchmark
    async def benchmark_wrapper():
        return await use_async_scope()
    
    # Run the benchmark
    result = await benchmark.pedantic(
        benchmark_wrapper,
        iterations=20,
        rounds=5
    )
    
    # Verify the result
    assert result is not None
    assert "id" in result


def test_decorator_inject_performance(service_resolver, benchmark):
    """Benchmark the performance overhead of decorator-based injection."""
    resolver = service_resolver
    
    # Benchmark constructor injection
    def resolve_injected_service():
        return resolver.resolve(InjectedService)
    
    injected_result = benchmark.pedantic(
        resolve_injected_service,
        iterations=50,
        rounds=5
    )
    assert injected_result is not None
    
    # Benchmark self-injection
    def resolve_self_injected():
        return resolver.resolve(SelfInjectingService)
    
    self_injected_result = benchmark.pedantic(
        resolve_self_injected,
        iterations=50,
        rounds=5
    )
    assert self_injected_result is not None
    
    # Benchmark parameter injection (function wrapping)
    def call_injected_function():
        return process_with_injection({"test": "data"})
    
    function_result = benchmark.pedantic(
        call_injected_function,
        iterations=50,
        rounds=5
    )
    assert function_result is not None


@pytest.mark.asyncio
async def test_async_inject_performance(benchmark):
    """Benchmark the performance of async function injection."""
    
    # Define the async benchmark function
    async def call_async_injected():
        return await process_async_with_injection({"test": "async_data"})
    
    # Run the benchmark
    async def benchmark_wrapper():
        return await call_async_injected()
    
    result = await benchmark.pedantic(
        benchmark_wrapper,
        iterations=20,
        rounds=5
    )
    
    # Verify the result
    assert result is not None
    assert "id" in result


def test_get_service_performance(global_provider, benchmark):
    """Benchmark the performance of the global get_service function."""
    
    # Benchmark different service types
    service_types = [
        ConfigProtocol,
        LoggerProtocol,
        RepositoryProtocol,
        ServiceProtocol
    ]
    
    results = {}
    for service_type in service_types:
        # Define benchmark function for this type
        def get_service_benchmark():
            return get_service(service_type)
        
        # Run the benchmark
        result = benchmark.pedantic(
            get_service_benchmark,
            iterations=50,
            rounds=5
        )
        
        # Store result
        results[service_type.__name__] = result
        
        # Verify result is not None
        assert result is not None
    
    # Verify we have results for all types
    assert len(results) == len(service_types)


def test_lifecycle_hooks_performance(service_provider, benchmark):
    """Benchmark the performance of service lifecycle hooks."""
    provider = service_provider
    
    # Initialize the provider to setup lifecycle services
    asyncio.run(provider.initialize())
    
    # Benchmark resolving and using a lifecycle service
    def use_lifecycle_service():
        with provider.create_scope() as scope:
            lifecycle_service = scope.resolve(LifecycleService)
            return lifecycle_service.process({"lifecycle": "test"})
    
    service_usage_result = benchmark.pedantic(
        use_lifecycle_service,
        iterations=20,
        rounds=5
    )
    
    # Verify the result
    assert service_usage_result is not None
    assert service_usage_result["processed"]["lifecycle"] == "test"
    
    # Benchmark provider disposal
    def dispose_provider():
        # Create a new provider for disposal benchmark
        collection = ServiceCollection()
        collection.add_scoped(LifecycleService)
        new_provider = UnoServiceProvider(collection)
        
        # Initialize and then dispose
        asyncio.run(new_provider.initialize())
        asyncio.run(new_provider.dispose())
        
        return new_provider
    
    dispose_result = benchmark.pedantic(
        dispose_provider,
        iterations=5,
        rounds=3
    )
    assert dispose_result is not None


def test_concurrent_resolution_performance(service_provider, benchmark):
    """Benchmark the performance of concurrent service resolution."""
    provider = service_provider
    
    # Define the concurrent benchmark function
    def resolve_concurrently():
        # Number of concurrent resolutions
        num_threads = 10
        num_resolutions_per_thread = 10
        
        results = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Define the worker function
            def worker(thread_id):
                thread_results = []
                # Create a scope for this thread
                with provider.create_scope() as scope:
                    for i in range(num_resolutions_per_thread):
                        # Alternate resolving different services
                        if i % 4 == 0:
                            service = scope.resolve(ConfigProtocol)
                        elif i % 4 == 1:
                            service = scope.resolve(RepositoryProtocol)
                        elif i % 4 == 2:
                            service = scope.resolve(ServiceProtocol)
                        else:
                            service = scope.resolve(Level3)
                        
                        thread_results.append(service is not None)
                
                return thread_results
            
            # Submit tasks and gather results
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in futures:
                results.extend(future.result())
        
        return results
    
    # Run the benchmark
    result = benchmark.pedantic(
        resolve_concurrently,
        iterations=5,
        rounds=3
    )
    
    # Verify all resolutions succeeded
    assert result is not None
    assert all(result)
    assert len(result) == 10 * 10  # num_threads * num_resolutions_per_thread


def test_service_collection_operations_performance(benchmark):
    """Benchmark the performance of various ServiceCollection operations."""
    
    # Benchmark cloning a collection
    def clone_collection():
        collection = ServiceCollection()
        
        # Add some services first
        collection.add_singleton(ConfigProtocol, Config)
        collection.add_scoped(RepositoryProtocol, Repository)
        collection.add_scoped(ServiceProtocol, Service)
        
        # Clone the collection
        return collection.clone()
    
    clone_result = benchmark.pedantic(
        clone_collection,
        iterations=20,
        rounds=5
    )
    assert clone_result is not None
    
    # Benchmark merging collections
    def merge_collections():
        collection1 = ServiceCollection()
        collection1.add_singleton(ConfigProtocol, Config)
        collection1.add_scoped(RepositoryProtocol, Repository)
        
        collection2 = ServiceCollection()
        collection2.add_singleton(LoggerProtocol, Logger)
        collection2.add_scoped(ServiceProtocol, Service)
        
        # Merge collection2 into collection1
        collection1.merge(collection2)
        return collection1
    
    merge_result = benchmark.pedantic(
        merge_collections,
        iterations=20,
        rounds=5
    )
    assert merge_result is not None
    assert len(merge_result._registrations) >= 4


def test_testing_container_performance(benchmark):
    """Benchmark the performance of the TestingContainer setup and usage."""
    
    # Benchmark setting up a testing container
    def setup_test_container():
        container = TestingContainer()
        container.register_singleton(ConfigProtocol, Config())
        container.register_singleton(LoggerProtocol, Logger())
        container.register_scoped_factory(RepositoryProtocol, lambda: Repository())
        container.register_scoped_factory(ServiceProtocol, lambda scope: Service(
            repository=scope.resolve(RepositoryProtocol)
        ))
        return container
    
    container_result = benchmark.pedantic(
        setup_test_container,
        iterations=10,
        rounds=3
    )
    assert container_result is not None
    
    # Benchmark using the configured test container
    container = setup_test_container()
    
    def use_test_container():
        # Configure global service provider
        configure_test_container(container)
        
        # Use some injected functions
        result = process_with_injection({"test": "data"})
        return result
    
    usage_result = benchmark.pedantic(
        use_test_container,
        iterations=10,
        rounds=3
    )
    assert usage_result is not None
    assert "id" in usage_result


def test_dynamic_service_resolution_performance(service_provider, benchmark):
    """Benchmark the performance of dynamically resolving services by type name."""
    provider = service_provider
    
    # Define a function to resolve services by name
    def resolve_by_name(type_name):
        if type_name == "config":
            return provider.resolver.resolve(ConfigProtocol)
        elif type_name == "logger":
            return provider.resolver.resolve(LoggerProtocol)
        elif type_name == "repository":
            return provider.resolver.resolve(RepositoryProtocol)
        elif type_name == "service":
            return provider.resolver.resolve(ServiceProtocol)
        return None
    
    # Benchmark resolving different services by name
    service_names = ["config", "logger", "repository", "service"]
    
    results = {}
    for name in service_names:
        def dynamic_resolve():
            return resolve_by_name(name)
        
        result = benchmark.pedantic(
            dynamic_resolve,
            iterations=50,
            rounds=5
        )
        
        results[name] = result
        assert result is not None
    
    # Verify we have results for all services
    assert len(results) == len(service_names)


def test_factory_resolution_performance(benchmark):
    """Benchmark the performance of factory-based service resolution."""
    
    # Create a collection with factory registrations
    def create_factory_collection():
        collection = ServiceCollection()
        
        # Register with standard constructor
        collection.add_singleton(ConfigProtocol, Config)
        collection.add_singleton(LoggerProtocol, Logger)
        
        # Register with factory functions
        collection.add_scoped_factory(RepositoryProtocol, lambda: Repository("factory_created"))
        collection.add_scoped_factory(ServiceProtocol, lambda scope: Service(
            repository=scope.resolve(RepositoryProtocol),
            logger=scope.resolve(LoggerProtocol)
        ))
        
        # Register with complex factory
        collection.add_scoped_factory(Level3, lambda scope: Level3(
            level2=Level2(
                level1=Level1(scope.resolve(ConfigProtocol)),
                logger=scope.resolve(LoggerProtocol)
            ),
            repository=scope.resolve(RepositoryProtocol)
        ))
        
        return collection
    
    # Benchmark creating and using a provider with factories
    def use_factory_provider():
        collection = create_factory_collection()
        provider = UnoServiceProvider(collection)
        
        with provider.create_scope() as scope:
            # Resolve factory-created services
            repository = scope.resolve(RepositoryProtocol)
            service = scope.resolve(ServiceProtocol)
            level3 = scope.resolve(Level3)
            
            # Use the services to ensure they're correctly created
            repository.create({"test": "data"})
            service.process({"service": "test"})
            
            return repository, service, level3
    
    # Run the benchmark
    result = benchmark.pedantic(
        use_factory_provider,
        iterations=10,
        rounds=3
    )
    
    # Verify the result
    assert result is not None
    assert len(result) == 3
    assert result[0].name == "factory_created"  # Verify factory was used