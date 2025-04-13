import asyncio
import json
import os
import pytest
import time
import uuid
from typing import Any, Dict, List, Optional
from functools import wraps

from src.uno.caching.manager import CacheManager
from src.uno.caching.key import generate_cache_key
from src.uno.caching.config import CacheConfig
from src.uno.caching.decorators import cached, async_cached
from src.uno.caching.local.memory import MemoryCache
from src.uno.caching.distributed.redis import RedisCache
from src.uno.caching.invalidation.time_based import TimeBasedInvalidationStrategy
from src.uno.caching.invalidation.pattern_based import PatternBasedInvalidationStrategy
from src.uno.caching.monitoring.monitor import CacheMonitor


# Test fixtures
@pytest.fixture(scope="module")
def cache_config():
    """Create various cache configurations for testing."""
    configs = {
        # Memory-only configuration
        "memory_only": CacheConfig(
            local={
                "type": "memory",
                "max_size": 1000,
                "ttl": 60
            },
            distributed=None
        ),
        
        # Memory with Redis configuration
        "memory_redis": CacheConfig(
            local={
                "type": "memory",
                "max_size": 1000,
                "ttl": 60
            },
            distributed={
                "type": "redis",
                "connection_string": "redis://localhost:6379/0",
                "ttl": 300
            }
        ),
        
        # Memory with file backup configuration
        "memory_file": CacheConfig(
            local={
                "type": "memory",
                "max_size": 1000,
                "ttl": 60
            },
            local_backup={
                "type": "file",
                "directory": "/tmp/cache",
                "ttl": 3600
            },
            distributed=None
        )
    }
    
    return configs


@pytest.fixture
def memory_cache_manager(cache_config):
    """Create a memory-only cache manager."""
    return CacheManager(config=cache_config["memory_only"])


@pytest.fixture
def multilevel_cache_manager(cache_config):
    """Create a multi-level cache manager with memory and Redis."""
    return CacheManager(config=cache_config["memory_redis"])


@pytest.fixture
def memory_file_cache_manager(cache_config):
    """Create a cache manager with memory and file backup."""
    return CacheManager(config=cache_config["memory_file"])


@pytest.fixture
def test_data():
    """Create test data of various sizes."""
    small_data = {"id": 1, "name": "Test Item", "value": 42.5}
    
    medium_data = {
        "id": str(uuid.uuid4()),
        "name": "Medium Test Item",
        "created_at": time.time(),
        "metadata": {
            "owner": "test_user",
            "permissions": ["read", "write"],
            "tags": ["test", "benchmark", "cache"]
        },
        "values": [i for i in range(50)]
    }
    
    large_data = {
        "id": str(uuid.uuid4()),
        "name": "Large Test Item",
        "created_at": time.time(),
        "description": "A very long description " * 100,  # 2400 characters
        "metadata": {
            "owner": "test_user",
            "permissions": ["read", "write", "admin"],
            "tags": ["test", "benchmark", "cache"],
            "attributes": {k: f"value_{k}" for k in range(100)}
        },
        "values": [{"id": i, "name": f"Item {i}", "value": i * 10.5} for i in range(100)]
    }
    
    # Create a very large dataset (approximately 1MB)
    huge_data = {
        "id": str(uuid.uuid4()),
        "name": "Huge Test Item",
        "records": [{
            "id": i,
            "data": "X" * 1000,  # 1KB of data per record
            "metadata": {
                "timestamp": time.time(),
                "source": f"benchmark_{i}",
                "hash": str(uuid.uuid4())
            }
        } for i in range(1000)]  # 1000 records × 1KB ≈ 1MB
    }
    
    return {
        "small": small_data,
        "medium": medium_data,
        "large": large_data,
        "huge": huge_data
    }


# Synchronous test functions to be cached
def compute_expensive_operation(input_data, delay=0.01):
    """Simulate an expensive operation that should be cached."""
    # Simulate processing delay
    time.sleep(delay)
    
    # Simple transformation of input data
    if isinstance(input_data, dict):
        result = {
            "processed": True,
            "input_size": len(json.dumps(input_data)),
            "timestamp": time.time(),
            "id": input_data.get("id", str(uuid.uuid4())),
            "computed_value": hash(str(input_data)) % 10000
        }
    elif isinstance(input_data, list):
        result = {
            "processed": True,
            "input_count": len(input_data),
            "timestamp": time.time(),
            "computed_value": sum(hash(str(item)) % 100 for item in input_data)
        }
    else:
        result = {
            "processed": True,
            "input_type": str(type(input_data)),
            "timestamp": time.time(),
            "computed_value": hash(str(input_data)) % 10000
        }
    
    return result


# Asynchronous test functions to be cached
async def async_compute_expensive_operation(input_data, delay=0.01):
    """Simulate an expensive async operation that should be cached."""
    # Simulate processing delay
    await asyncio.sleep(delay)
    
    # Use the same logic as the synchronous version
    return compute_expensive_operation(input_data, 0)


# Benchmarks
def test_cache_key_generation_performance(benchmark):
    """Benchmark the performance of generating cache keys with different inputs."""
    # Test a variety of input types
    test_cases = [
        ("simple_string", "test_string"),
        ("integer", 12345),
        ("float", 123.45),
        ("list", [1, 2, 3, 4, 5]),
        ("dict", {"id": 1, "name": "test"}),
        ("nested_dict", {"id": 1, "user": {"name": "test", "roles": ["admin", "user"]}}),
        ("complex", {"id": str(uuid.uuid4()), "data": [{"value": i} for i in range(10)]})
    ]
    
    # Run the benchmark for each test case
    results = {}
    for name, value in test_cases:
        def generate_key():
            return generate_cache_key("test_prefix", value)
        
        result = benchmark.pedantic(
            generate_key,
            iterations=100,
            rounds=10
        )
        
        results[name] = result
    
    # Verify we got results (to avoid benchmark optimization)
    assert len(results) == len(test_cases)


def test_memory_cache_get_set_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance of get/set operations with memory cache."""
    # Test get/set operations with different data sizes
    data_sizes = ["small", "medium", "large"]
    operations = ["set", "get"]
    
    results = {}
    for size in data_sizes:
        for op in operations:
            data = test_data[size]
            key = f"test_key_{size}_{uuid.uuid4()}"
            
            if op == "set":
                def set_operation():
                    memory_cache_manager.set(key, data)
                
                result = benchmark.pedantic(
                    set_operation,
                    iterations=100,
                    rounds=10
                )
            else:  # "get"
                # Ensure the data is in the cache first
                memory_cache_manager.set(key, data)
                
                def get_operation():
                    return memory_cache_manager.get(key)
                
                result = benchmark.pedantic(
                    get_operation,
                    iterations=100,
                    rounds=10
                )
            
            results[f"{op}_{size}"] = result
    
    # Verify we got results
    assert len(results) == len(data_sizes) * len(operations)


def test_cache_hit_miss_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance difference between cache hits and misses."""
    # Prepare data
    data = test_data["medium"]
    hit_key = f"hit_key_{uuid.uuid4()}"
    miss_key = f"miss_key_{uuid.uuid4()}"
    
    # Set up for hits
    memory_cache_manager.set(hit_key, data)
    
    # Benchmark cache hit
    def cache_hit():
        return memory_cache_manager.get(hit_key)
    
    hit_result = benchmark.pedantic(
        cache_hit,
        iterations=100,
        rounds=10
    )
    
    # Benchmark cache miss
    def cache_miss():
        return memory_cache_manager.get(miss_key)
    
    miss_result = benchmark.pedantic(
        cache_miss,
        iterations=100,
        rounds=10
    )
    
    # Verify results (mostly to prevent benchmark optimization)
    assert hit_result is not None
    assert miss_result is not None


def test_cached_decorator_overhead(memory_cache_manager, test_data, benchmark):
    """Benchmark the overhead of using the @cached decorator."""
    data = test_data["medium"]
    
    # Create test functions - one with decorator, one without
    @cached(ttl=60, key_prefix="test_cached")
    def with_decorator(input_data):
        return compute_expensive_operation(input_data, 0)
    
    def without_decorator(input_data):
        result = memory_cache_manager.get(f"test_cached:{input_data}")
        if result is None:
            result = compute_expensive_operation(input_data, 0)
            memory_cache_manager.set(f"test_cached:{input_data}", result, ttl=60)
        return result
    
    # Benchmark with decorator (first call - miss)
    def decorated_miss():
        return with_decorator(str(uuid.uuid4()))
    
    decorator_miss_result = benchmark.pedantic(
        decorated_miss,
        iterations=10,
        rounds=5
    )
    
    # Benchmark with decorator (second call - hit)
    cached_input = str(uuid.uuid4())
    with_decorator(cached_input)  # Warm up cache
    
    def decorated_hit():
        return with_decorator(cached_input)
    
    decorator_hit_result = benchmark.pedantic(
        decorated_hit,
        iterations=100,
        rounds=10
    )
    
    # Benchmark manual implementation (miss)
    def manual_miss():
        return without_decorator(str(uuid.uuid4()))
    
    manual_miss_result = benchmark.pedantic(
        manual_miss,
        iterations=10,
        rounds=5
    )
    
    # Benchmark manual implementation (hit)
    cached_input_manual = str(uuid.uuid4())
    without_decorator(cached_input_manual)  # Warm up cache
    
    def manual_hit():
        return without_decorator(cached_input_manual)
    
    manual_hit_result = benchmark.pedantic(
        manual_hit,
        iterations=100,
        rounds=10
    )
    
    # Verify results
    assert decorator_hit_result is not None
    assert decorator_miss_result is not None
    assert manual_hit_result is not None
    assert manual_miss_result is not None


def test_cache_invalidation_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance of different cache invalidation strategies."""
    # Create test data
    data = test_data["medium"]
    keys = [f"test_invalidate_{i}" for i in range(100)]
    
    # Populate cache
    for i, key in enumerate(keys):
        memory_cache_manager.set(key, {"index": i, "data": data})
    
    # Benchmark individual key deletion
    def delete_single_key():
        random_index = int(time.time() * 1000) % len(keys)
        memory_cache_manager.delete(keys[random_index])
    
    single_delete_result = benchmark.pedantic(
        delete_single_key,
        iterations=10,
        rounds=5
    )
    
    # Repopulate cache
    for i, key in enumerate(keys):
        memory_cache_manager.set(key, {"index": i, "data": data})
    
    # Benchmark pattern invalidation
    def invalidate_pattern():
        # Create a pattern that matches about 10% of the keys
        pattern_index = int(time.time() * 1000) % 10
        pattern = f"test_invalidate_{pattern_index}"
        memory_cache_manager.invalidate_pattern(pattern)
    
    pattern_invalidate_result = benchmark.pedantic(
        invalidate_pattern,
        iterations=10,
        rounds=5
    )
    
    # Verify results
    assert single_delete_result is not None
    assert pattern_invalidate_result is not None


def test_multilevel_cache_performance(memory_cache_manager, multilevel_cache_manager, test_data, benchmark):
    """Benchmark the performance difference between single-level and multi-level caching."""
    # Check if Redis is available
    try:
        multilevel_cache_manager.distributed_cache.ping()
        redis_available = True
    except:
        redis_available = False
        pytest.skip("Redis is not available for multi-level cache testing")
    
    if not redis_available:
        return
    
    # Prepare test data
    data = test_data["medium"]
    keys = {
        "memory": f"memory_only_{uuid.uuid4()}",
        "multilevel": f"multilevel_{uuid.uuid4()}"
    }
    
    # Benchmark memory-only cache set
    def memory_cache_set():
        memory_cache_manager.set(keys["memory"], data)
    
    memory_set_result = benchmark.pedantic(
        memory_cache_set,
        iterations=50,
        rounds=5
    )
    
    # Benchmark multi-level cache set
    def multilevel_cache_set():
        multilevel_cache_manager.set(keys["multilevel"], data)
    
    multilevel_set_result = benchmark.pedantic(
        multilevel_cache_set,
        iterations=50,
        rounds=5
    )
    
    # Set up cache for get operations
    memory_cache_manager.set(keys["memory"], data)
    multilevel_cache_manager.set(keys["multilevel"], data)
    
    # Benchmark memory-only cache get
    def memory_cache_get():
        return memory_cache_manager.get(keys["memory"])
    
    memory_get_result = benchmark.pedantic(
        memory_cache_get,
        iterations=50,
        rounds=5
    )
    
    # Benchmark multi-level cache get (should hit local cache)
    def multilevel_cache_get():
        return multilevel_cache_manager.get(keys["multilevel"])
    
    multilevel_get_result = benchmark.pedantic(
        multilevel_cache_get,
        iterations=50,
        rounds=5
    )
    
    # Clear local cache for multi-level to force distributed lookup
    multilevel_cache_manager.local_cache.clear()
    
    # Benchmark multi-level cache get with local miss
    def multilevel_cache_get_distributed():
        return multilevel_cache_manager.get(keys["multilevel"])
    
    multilevel_distributed_get_result = benchmark.pedantic(
        multilevel_cache_get_distributed,
        iterations=50,
        rounds=5
    )
    
    # Verify results
    assert memory_set_result is not None
    assert multilevel_set_result is not None
    assert memory_get_result is not None
    assert multilevel_get_result is not None
    assert multilevel_distributed_get_result is not None


def test_cache_serialize_deserialize_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance of serializing/deserializing different data types and sizes."""
    data_sizes = ["small", "medium", "large", "huge"]
    
    results = {}
    for size in data_sizes:
        data = test_data[size]
        key = f"serialize_test_{size}_{uuid.uuid4()}"
        
        # Benchmark set (which includes serialization)
        def set_with_serialize():
            memory_cache_manager.set(key, data)
        
        set_result = benchmark.pedantic(
            set_with_serialize,
            iterations=20,
            rounds=5
        )
        
        # Set the data for get testing
        memory_cache_manager.set(key, data)
        
        # Benchmark get (which includes deserialization)
        def get_with_deserialize():
            return memory_cache_manager.get(key)
        
        get_result = benchmark.pedantic(
            get_with_deserialize,
            iterations=20,
            rounds=5
        )
        
        results[f"set_{size}"] = set_result
        results[f"get_{size}"] = get_result
    
    # Verify results
    assert len(results) == len(data_sizes) * 2


@pytest.mark.asyncio
async def test_async_cache_operations_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance of asynchronous cache operations."""
    data = test_data["medium"]
    key = f"async_test_{uuid.uuid4()}"
    
    # Define async benchmark functions
    async def async_get():
        return await memory_cache_manager.get_async(key)
    
    async def async_set():
        await memory_cache_manager.set_async(key, data)
    
    async def async_delete():
        await memory_cache_manager.delete_async(key)
    
    # Set up cache for get operations
    await memory_cache_manager.set_async(key, data)
    
    # Benchmark async get
    async_get_result = await benchmark.pedantic(
        async_get,
        iterations=50,
        rounds=5
    )
    
    # Benchmark async set
    async_set_result = await benchmark.pedantic(
        async_set,
        iterations=50,
        rounds=5
    )
    
    # Benchmark async delete
    async_delete_result = await benchmark.pedantic(
        async_delete,
        iterations=50,
        rounds=5
    )
    
    # Verify results
    assert async_get_result is not None
    assert async_set_result is not None
    assert async_delete_result is not None


@pytest.mark.asyncio
async def test_async_cached_decorator_performance(test_data, benchmark):
    """Benchmark the performance of the @async_cached decorator."""
    data = test_data["medium"]
    
    # Create test functions with decorator
    @async_cached(ttl=60, key_prefix="test_async_cached")
    async def cached_function(input_data, delay=0):
        return await async_compute_expensive_operation(input_data, delay)
    
    # Test first call (miss)
    async def async_decorated_miss():
        return await cached_function(str(uuid.uuid4()))
    
    async_miss_result = await benchmark.pedantic(
        async_decorated_miss,
        iterations=10,
        rounds=5
    )
    
    # Test second call (hit)
    cached_input = str(uuid.uuid4())
    await cached_function(cached_input)  # Warm up cache
    
    async def async_decorated_hit():
        return await cached_function(cached_input)
    
    async_hit_result = await benchmark.pedantic(
        async_decorated_hit,
        iterations=50,
        rounds=5
    )
    
    # Verify results
    assert async_miss_result is not None
    assert async_hit_result is not None


def test_cache_concurrency_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance of the cache under concurrent operations."""
    data = test_data["medium"]
    
    # Create a function that simulates concurrent access
    def concurrent_operation():
        # Simulate multiple threads accessing the cache
        concurrent_threads = 10
        operations_per_thread = 10
        
        def worker_task(worker_id):
            results = []
            for i in range(operations_per_thread):
                operation = i % 3  # 0=get, 1=set, 2=delete
                key = f"concurrent_test_{worker_id}_{i}"
                
                if operation == 0:
                    # Get operation
                    result = memory_cache_manager.get(key)
                    results.append(result)
                elif operation == 1:
                    # Set operation
                    memory_cache_manager.set(key, data)
                elif operation == 2:
                    # Delete operation
                    memory_cache_manager.delete(key)
            
            return results
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_threads) as executor:
            futures = [executor.submit(worker_task, i) for i in range(concurrent_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return results
    
    # Run the benchmark
    benchmark_result = benchmark(concurrent_operation)
    
    # Verify results
    assert benchmark_result is not None


def test_cache_monitoring_overhead(memory_cache_manager, test_data, benchmark):
    """Benchmark the overhead of cache monitoring."""
    data = test_data["medium"]
    
    # Create a monitored cache manager
    monitored_cache = CacheManager(
        config=CacheConfig(
            local={
                "type": "memory",
                "max_size": 1000,
                "ttl": 60
            },
            monitoring={
                "enabled": True,
                "collect_stats": True,
                "prometheus_enabled": False
            }
        )
    )
    
    # Create an unmonitored cache manager
    unmonitored_cache = CacheManager(
        config=CacheConfig(
            local={
                "type": "memory",
                "max_size": 1000,
                "ttl": 60
            },
            monitoring={
                "enabled": False,
                "collect_stats": False,
                "prometheus_enabled": False
            }
        )
    )
    
    # Benchmark monitored cache operations
    monitored_key = f"monitored_{uuid.uuid4()}"
    
    def monitored_operations():
        monitored_cache.set(monitored_key, data)
        return monitored_cache.get(monitored_key)
    
    monitored_result = benchmark.pedantic(
        monitored_operations,
        iterations=50,
        rounds=5
    )
    
    # Benchmark unmonitored cache operations
    unmonitored_key = f"unmonitored_{uuid.uuid4()}"
    
    def unmonitored_operations():
        unmonitored_cache.set(unmonitored_key, data)
        return unmonitored_cache.get(unmonitored_key)
    
    unmonitored_result = benchmark.pedantic(
        unmonitored_operations,
        iterations=50,
        rounds=5
    )
    
    # Verify results
    assert monitored_result is not None
    assert unmonitored_result is not None


def test_cache_bulk_operations_performance(memory_cache_manager, test_data, benchmark):
    """Benchmark the performance of bulk operations versus individual operations."""
    data = test_data["small"]
    
    # Create test keys
    batch_size = 100
    keys = [f"bulk_test_{i}_{uuid.uuid4()}" for i in range(batch_size)]
    
    # Benchmark individual set operations
    def individual_sets():
        for i, key in enumerate(keys):
            memory_cache_manager.set(key, {"index": i, "data": data})
    
    individual_set_result = benchmark.pedantic(
        individual_sets,
        iterations=5,
        rounds=3
    )
    
    # Benchmark bulk set operation (if supported by the cache manager)
    # Note: This assumes a bulk_set method exists, which might not be true
    # for all cache implementations. Adjust as needed.
    try:
        bulk_data = {key: {"index": i, "data": data} for i, key in enumerate(keys)}
        
        def bulk_sets():
            memory_cache_manager.bulk_set(bulk_data)
        
        bulk_set_result = benchmark.pedantic(
            bulk_sets,
            iterations=5,
            rounds=3
        )
    except AttributeError:
        # If bulk_set is not implemented, simulate it
        def simulated_bulk_sets():
            bulk_data = {key: {"index": i, "data": data} for i, key in enumerate(keys)}
            for key, value in bulk_data.items():
                memory_cache_manager.set(key, value)
        
        bulk_set_result = benchmark.pedantic(
            simulated_bulk_sets,
            iterations=5,
            rounds=3
        )
    
    # Benchmark individual get operations
    def individual_gets():
        results = []
        for key in keys:
            results.append(memory_cache_manager.get(key))
        return results
    
    individual_get_result = benchmark.pedantic(
        individual_gets,
        iterations=5,
        rounds=3
    )
    
    # Benchmark bulk get operation (if supported)
    try:
        def bulk_gets():
            return memory_cache_manager.bulk_get(keys)
        
        bulk_get_result = benchmark.pedantic(
            bulk_gets,
            iterations=5,
            rounds=3
        )
    except AttributeError:
        # If bulk_get is not implemented, simulate it
        def simulated_bulk_gets():
            results = {}
            for key in keys:
                results[key] = memory_cache_manager.get(key)
            return results
        
        bulk_get_result = benchmark.pedantic(
            simulated_bulk_gets,
            iterations=5,
            rounds=3
        )
    
    # Verify results
    assert individual_set_result is not None
    assert bulk_set_result is not None
    assert individual_get_result is not None
    assert bulk_get_result is not None