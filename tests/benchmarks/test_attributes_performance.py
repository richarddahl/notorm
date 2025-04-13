"""
Performance benchmarks for attribute module functionality.

These benchmarks measure the performance of attribute operations
under different conditions to help identify bottlenecks and
optimization opportunities.
"""

import pytest
import asyncio
import time
import uuid
import json
import random
from typing import Dict, List, Optional, Any, Tuple

from uno.core.errors.result import Result, Success, Failure
from uno.attributes.entities import AttributeType, Attribute, MetaTypeRef, QueryRef
from uno.attributes.domain_repositories import AttributeRepository, AttributeTypeRepository
from uno.attributes.domain_services import AttributeService, AttributeTypeService
from uno.database.session import async_session
from uno.dependencies import get_service, register_service


# Skip these benchmarks in normal test runs
pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(
        "not config.getoption('--run-benchmark')",
        reason="Only run when --run-benchmark is specified"
    )
]


@pytest.fixture(scope="module")
async def db_session():
    """Create a database session."""
    async with async_session() as session:
        yield session


@pytest.fixture(scope="module")
async def attribute_services():
    """Create attribute services for benchmarking."""
    # Create repositories
    attr_type_repo = AttributeTypeRepository()
    attr_repo = AttributeRepository()
    
    # Create services
    attr_type_service = AttributeTypeService(attr_type_repo)
    register_service(AttributeTypeService, attr_type_service)
    
    attr_service = AttributeService(attr_repo, attr_type_service)
    register_service(AttributeService, attr_service)
    
    services = {
        "attribute_type_service": attr_type_service,
        "attribute_service": attr_service,
    }
    
    yield services


@pytest.fixture(scope="module")
async def setup_benchmark_environment(db_session, attribute_services):
    """Set up the benchmark environment with test data."""
    attr_type_service = attribute_services["attribute_type_service"]
    attr_service = attribute_services["attribute_service"]
    
    # Create test data with different sizes
    type_counts = [10, 20, 50]
    attribute_counts = [50, 200, 1000]
    
    created_types = []
    created_attributes = []
    
    print(f"Setting up attribute benchmark environment...")
    
    # Create attribute types
    for size_index, type_count in enumerate(type_counts):
        # Create a root type for this size category
        root_type = AttributeType(
            id=str(uuid.uuid4()),
            name=f"Root_Type_{size_index}",
            text=f"Root type for size category {size_index}",
            description=f"Benchmark root type for size {size_index}",
            required=False,
            multiple_allowed=True,
        )
        
        root_result = await attr_type_service.create(root_type)
        if root_result.is_success:
            root_type = root_result.value
            created_types.append(root_type)
            
            # Create child types for this root
            for i in range(type_count - 1):  # -1 because we already created the root
                child_type = AttributeType(
                    id=str(uuid.uuid4()),
                    name=f"Type_{size_index}_{i}",
                    text=f"Type {i} for size {size_index}",
                    parent_id=root_type.id,
                    required=i % 3 == 0,
                    multiple_allowed=i % 2 == 0,
                    comment_required=i % 4 == 0,
                    display_with_objects=i % 5 == 0,
                    initial_comment=f"Initial comment for type {i}" if i % 4 == 0 else None,
                )
                
                type_result = await attr_type_service.create(child_type)
                if type_result.is_success:
                    created_types.append(type_result.value)
    
    print(f"Created {len(created_types)} attribute types")
    
    # Create attributes
    for size_index, attribute_count in enumerate(type_counts):
        types_for_size = [t for t in created_types if f"Type_{size_index}_" in t.name or f"Root_Type_{size_index}" == t.name]
        
        for i in range(attribute_counts[size_index]):
            # Select a random type for this attribute
            attr_type = random.choice(types_for_size)
            
            attribute = Attribute(
                id=str(uuid.uuid4()),
                attribute_type_id=attr_type.id,
                comment=f"Comment for attribute {i}" if attr_type.comment_required or i % 3 == 0 else None,
                follow_up_required=i % 5 == 0,
            )
            
            attr_result = await attr_service.create(attribute)
            if attr_result.is_success:
                created_attributes.append(attr_result.value)
    
    print(f"Created {len(created_attributes)} attributes")
    
    # Return created data for tests to use
    yield {
        "attribute_types": created_types,
        "attributes": created_attributes,
        "sizes": {
            "small": 0,
            "medium": 1,
            "large": 2,
        }
    }


@pytest.mark.asyncio
async def test_attribute_type_creation_performance(attribute_services, benchmark):
    """Benchmark the performance of creating attribute types."""
    attr_type_service = attribute_services["attribute_type_service"]
    
    # Define async benchmark function
    async def create_attribute_type():
        # Create a unique attribute type
        attr_type = AttributeType(
            id=str(uuid.uuid4()),
            name=f"BenchType_{uuid.uuid4().hex[:8]}",
            text=f"Benchmark attribute type",
            required=False,
            multiple_allowed=True,
        )
        
        result = await attr_type_service.create(attr_type)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(create_attribute_type()),
        iterations=10,
        rounds=3,
        name="attribute_type_create"
    )
    
    print(f"Attribute type creation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_attribute_type_query_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying attribute types with different filters."""
    attr_type_service = attribute_services["attribute_type_service"]
    
    # Define different query types to benchmark
    query_benchmarks = [
        ("find_all", None),
        ("find_by_name", "Type_1_"),
    ]
    
    results = {}
    
    for query_name, query_param in query_benchmarks:
        # Define async benchmark function based on query type
        async def query_benchmark():
            if query_name == "find_all":
                result = await attr_type_service.list()
                return result
            elif query_name == "find_by_name":
                # This is a prefix search
                result = await attr_type_service.find_by_name(query_param)
                return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_benchmark()),
            iterations=10,
            rounds=3,
            name=f"attribute_type_query_{query_name}"
        )
        
        results[query_name] = runtime
        print(f"Attribute type query {query_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nAttribute type query performance by query type:")
    for query_name, time in results.items():
        print(f"  {query_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_attribute_creation_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of creating attributes."""
    attr_service = attribute_services["attribute_service"]
    attr_types = setup_benchmark_environment["attribute_types"]
    
    # Define async benchmark function
    async def create_attribute():
        # Select a random attribute type
        attr_type = random.choice(attr_types)
        
        # Create a unique attribute
        attribute = Attribute(
            id=str(uuid.uuid4()),
            attribute_type_id=attr_type.id,
            comment=f"Benchmark comment {uuid.uuid4().hex[:8]}" if attr_type.comment_required else None,
            follow_up_required=random.choice([True, False]),
        )
        
        result = await attr_service.create(attribute)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(create_attribute()),
        iterations=10,
        rounds=3,
        name="attribute_create"
    )
    
    print(f"Attribute creation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_attribute_query_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying attributes with different filters."""
    attr_service = attribute_services["attribute_service"]
    
    attr_types = setup_benchmark_environment["attribute_types"]
    
    # Get a type ID from each size category
    size_type_ids = {}
    for size in [0, 1, 2]:
        size_types = [t for t in attr_types if f"Type_{size}_" in t.name or f"Root_Type_{size}" == t.name]
        if size_types:
            size_type_ids[size] = size_types[0].id
    
    results = {}
    
    # Test finding attributes by type for each size
    for size, type_id in size_type_ids.items():
        # Define async benchmark function
        async def query_benchmark():
            result = await attr_service.find_by_attribute_type(type_id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_benchmark()),
            iterations=5,
            rounds=3,
            name=f"attribute_query_by_type_{size}"
        )
        
        results[f"size_{size}"] = runtime
        print(f"Attribute query by type for size {size} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nAttribute query performance by size:")
    for size_key, time in results.items():
        print(f"  {size_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_attribute_type_hierarchy_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of getting attribute type hierarchies of different depths."""
    attr_type_service = attribute_services["attribute_type_service"]
    
    # Find root types for each size
    attr_types = setup_benchmark_environment["attribute_types"]
    root_types = [t for t in attr_types if t.name.startswith("Root_Type_")]
    
    results = {}
    
    for root_type in root_types:
        size_index = int(root_type.name.split("_")[-1])
        
        # Define async benchmark function
        async def hierarchy_benchmark():
            result = await attr_type_service.get_hierarchy(root_type.id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(hierarchy_benchmark()),
            iterations=5,
            rounds=3,
            name=f"attribute_type_hierarchy_{size_index}"
        )
        
        results[f"size_{size_index}"] = runtime
        print(f"Attribute type hierarchy for size {size_index} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nAttribute type hierarchy performance by size:")
    for size_key, time in results.items():
        print(f"  {size_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_attribute_relationship_loading_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of loading attributes with relationships."""
    attr_service = attribute_services["attribute_service"]
    
    # Get some attributes to test
    attributes = setup_benchmark_environment["attributes"]
    test_attributes = []
    
    # Take samples from the beginning, middle, and end
    if attributes:
        test_attributes.append(attributes[0])
        if len(attributes) > 1:
            test_attributes.append(attributes[len(attributes) // 2])
        if len(attributes) > 2:
            test_attributes.append(attributes[-1])
    
    results = {}
    
    for i, attribute in enumerate(test_attributes):
        # Define async benchmark function
        async def relationship_benchmark():
            result = await attr_service.get_with_related_data(attribute.id)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(relationship_benchmark()),
            iterations=5,
            rounds=3,
            name=f"attribute_with_relationships_{i}"
        )
        
        results[f"attribute_{i}"] = runtime
        print(f"Loading attribute {i} with relationships took {runtime:.4f} seconds")
    
    # Compare results
    print("\nAttribute relationship loading performance:")
    for attr_key, time in results.items():
        print(f"  {attr_key}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_batch_attribute_creation_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of creating attributes in batches."""
    attr_service = attribute_services["attribute_service"]
    attr_types = setup_benchmark_environment["attribute_types"]
    
    # Define batch sizes to test
    batch_sizes = [5, 20, 50]
    results = {}
    
    for batch_size in batch_sizes:
        # Define async benchmark function for this batch size
        async def batch_creation_benchmark():
            # Create a batch of attributes
            attributes = []
            for _ in range(batch_size):
                attr_type = random.choice(attr_types)
                attribute = Attribute(
                    id=str(uuid.uuid4()),
                    attribute_type_id=attr_type.id,
                    comment=f"Batch comment {uuid.uuid4().hex[:8]}" if attr_type.comment_required else None,
                    follow_up_required=random.choice([True, False]),
                )
                attributes.append(attribute)
            
            # Create them one by one (in a real implementation, you'd do this in a batch)
            created_attributes = []
            for attribute in attributes:
                result = await attr_service.create(attribute)
                if result.is_success:
                    created_attributes.append(result.value)
            
            return created_attributes
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(batch_creation_benchmark()),
            iterations=3,
            rounds=3,
            name=f"batch_attribute_create_{batch_size}"
        )
        
        results[batch_size] = runtime
        print(f"Creating {batch_size} attributes in batch took {runtime:.4f} seconds")
    
    # Calculate per-attribute time
    per_attribute_times = {size: time/size for size, time in results.items()}
    
    # Compare results
    print("\nBatch attribute creation performance:")
    for size, time in results.items():
        print(f"  Batch size {size}: {time:.4f} seconds total, {per_attribute_times[size]:.4f} seconds per attribute")


@pytest.mark.asyncio
async def test_add_value_performance(attribute_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of adding values to attributes."""
    attr_service = attribute_services["attribute_service"]
    
    # Get some attributes to test
    attributes = setup_benchmark_environment["attributes"]
    test_attributes = random.sample(attributes, min(10, len(attributes)))
    
    # Generate some value IDs
    value_ids = [str(uuid.uuid4()) for _ in range(20)]
    
    results = {}
    
    # Run benchmark
    async def add_value_benchmark():
        results = []
        for attribute in test_attributes:
            # Pick a random value ID
            value_id = random.choice(value_ids)
            result = await attr_service.add_value(attribute.id, value_id)
            results.append(result)
        return results
    
    runtime = benchmark.pedantic(
        lambda: asyncio.run(add_value_benchmark()),
        iterations=5,
        rounds=3,
        name="add_value"
    )
    
    print(f"Adding values to {len(test_attributes)} attributes took {runtime:.4f} seconds")
    print(f"Average time per attribute: {runtime/len(test_attributes):.4f} seconds")