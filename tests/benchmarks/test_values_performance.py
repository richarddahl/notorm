"""
Performance benchmarks for values module functionality.

These benchmarks measure the performance of value operations
under different conditions to help identify bottlenecks and
optimization opportunities.
"""

import pytest
import asyncio
import time
import uuid
import json
import random
import datetime
import decimal
from typing import Dict, List, Optional, Any, Tuple, Type

from uno.core.errors.result import Result, Success, Failure
from uno.values.entities import (
    BaseValue,
    Attachment,
    BooleanValue,
    DateTimeValue, 
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue
)
from uno.values.domain_repositories import (
    AttachmentRepository,
    BooleanValueRepository,
    DateTimeValueRepository,
    DateValueRepository,
    DecimalValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    TimeValueRepository
)
from uno.values.domain_services import (
    AttachmentService,
    BooleanValueService,
    DateTimeValueService,
    DateValueService,
    DecimalValueService,
    IntegerValueService,
    TextValueService,
    TimeValueService
)
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
async def value_services():
    """Create value services for benchmarking."""
    # Create repositories
    attachment_repo = AttachmentRepository()
    boolean_repo = BooleanValueRepository()
    datetime_repo = DateTimeValueRepository()
    date_repo = DateValueRepository()
    decimal_repo = DecimalValueRepository()
    integer_repo = IntegerValueRepository()
    text_repo = TextValueRepository()
    time_repo = TimeValueRepository()
    
    # Create services
    attachment_service = AttachmentService(Attachment, attachment_repo)
    boolean_service = BooleanValueService(BooleanValue, boolean_repo)
    datetime_service = DateTimeValueService(DateTimeValue, datetime_repo)
    date_service = DateValueService(DateValue, date_repo)
    decimal_service = DecimalValueService(DecimalValue, decimal_repo)
    integer_service = IntegerValueService(IntegerValue, integer_repo)
    text_service = TextValueService(TextValue, text_repo)
    time_service = TimeValueService(TimeValue, time_repo)
    
    # Register services
    register_service(AttachmentService, attachment_service)
    register_service(BooleanValueService, boolean_service)
    register_service(DateTimeValueService, datetime_service)
    register_service(DateValueService, date_service)
    register_service(DecimalValueService, decimal_service)
    register_service(IntegerValueService, integer_service)
    register_service(TextValueService, text_service)
    register_service(TimeValueService, time_service)
    
    services = {
        "attachment_service": attachment_service,
        "boolean_service": boolean_service,
        "datetime_service": datetime_service,
        "date_service": date_service,
        "decimal_service": decimal_service,
        "integer_service": integer_service,
        "text_service": text_service,
        "time_service": time_service,
    }
    
    yield services


@pytest.fixture(scope="module")
async def setup_benchmark_environment(db_session, value_services):
    """Set up the benchmark environment with test data."""
    # Define the number of entities to create for each type
    counts = {
        "attachment": 50,
        "boolean": 50,
        "datetime": 50,
        "date": 50,
        "decimal": 50,
        "integer": 50,
        "text": 500,  # More text values as they're more commonly used
        "time": 50,
    }
    
    created_values = {
        "attachment": [],
        "boolean": [],
        "datetime": [],
        "date": [],
        "decimal": [],
        "integer": [],
        "text": [],
        "time": [],
    }
    
    print(f"Setting up values benchmark environment...")
    
    # Create attachment values
    for i in range(counts["attachment"]):
        attachment = Attachment(
            id=str(uuid.uuid4()),
            name=f"Attachment_{i}_{uuid.uuid4().hex[:8]}",
            file_path=f"/path/to/file_{i}.txt",
        )
        
        result = await value_services["attachment_service"].create(attachment)
        if result.is_success:
            created_values["attachment"].append(result.value)
    
    # Create boolean values
    for i in range(counts["boolean"]):
        boolean_value = BooleanValue(
            id=str(uuid.uuid4()),
            name=f"Boolean_{i}_{uuid.uuid4().hex[:8]}",
            value=i % 2 == 0,
        )
        
        result = await value_services["boolean_service"].create(boolean_value)
        if result.is_success:
            created_values["boolean"].append(result.value)
    
    # Create datetime values
    for i in range(counts["datetime"]):
        datetime_value = DateTimeValue(
            id=str(uuid.uuid4()),
            name=f"DateTime_{i}_{uuid.uuid4().hex[:8]}",
            value=datetime.datetime(2023, 1, 1) + datetime.timedelta(days=i, hours=i),
        )
        
        result = await value_services["datetime_service"].create(datetime_value)
        if result.is_success:
            created_values["datetime"].append(result.value)
    
    # Create date values
    for i in range(counts["date"]):
        date_value = DateValue(
            id=str(uuid.uuid4()),
            name=f"Date_{i}_{uuid.uuid4().hex[:8]}",
            value=datetime.date(2023, 1, 1) + datetime.timedelta(days=i),
        )
        
        result = await value_services["date_service"].create(date_value)
        if result.is_success:
            created_values["date"].append(result.value)
    
    # Create decimal values
    for i in range(counts["decimal"]):
        decimal_value = DecimalValue(
            id=str(uuid.uuid4()),
            name=f"Decimal_{i}_{uuid.uuid4().hex[:8]}",
            value=decimal.Decimal(f"{i}.{i}"),
        )
        
        result = await value_services["decimal_service"].create(decimal_value)
        if result.is_success:
            created_values["decimal"].append(result.value)
    
    # Create integer values
    for i in range(counts["integer"]):
        integer_value = IntegerValue(
            id=str(uuid.uuid4()),
            name=f"Integer_{i}_{uuid.uuid4().hex[:8]}",
            value=i * 10,
        )
        
        result = await value_services["integer_service"].create(integer_value)
        if result.is_success:
            created_values["integer"].append(result.value)
    
    # Create text values
    for i in range(counts["text"]):
        text_value = TextValue(
            id=str(uuid.uuid4()),
            name=f"Text_{i}_{uuid.uuid4().hex[:8]}",
            value=f"This is a test value for benchmark #{i}. It contains some random text to test performance of text value operations. ID: {uuid.uuid4().hex}"
        )
        
        result = await value_services["text_service"].create(text_value)
        if result.is_success:
            created_values["text"].append(result.value)
    
    # Create time values
    for i in range(counts["time"]):
        time_value = TimeValue(
            id=str(uuid.uuid4()),
            name=f"Time_{i}_{uuid.uuid4().hex[:8]}",
            value=datetime.time(hour=i % 24, minute=i % 60, second=i % 60),
        )
        
        result = await value_services["time_service"].create(time_value)
        if result.is_success:
            created_values["time"].append(result.value)
    
    total_created = sum(len(values) for values in created_values.values())
    print(f"Created {total_created} value entities")
    
    yield created_values


@pytest.mark.asyncio
async def test_value_creation_performance(value_services, benchmark):
    """Benchmark the performance of creating values of different types."""
    # Test value creation with different types
    value_types = [
        ("text", TextValue, value_services["text_service"], 
         lambda: (f"Text_{uuid.uuid4().hex[:8]}", f"Text value {uuid.uuid4().hex}")),
        ("integer", IntegerValue, value_services["integer_service"], 
         lambda: (f"Integer_{uuid.uuid4().hex[:8]}", random.randint(1, 10000))),
        ("decimal", DecimalValue, value_services["decimal_service"], 
         lambda: (f"Decimal_{uuid.uuid4().hex[:8]}", decimal.Decimal(str(random.random() * 100)))),
        ("boolean", BooleanValue, value_services["boolean_service"], 
         lambda: (f"Boolean_{uuid.uuid4().hex[:8]}", random.choice([True, False]))),
        ("date", DateValue, value_services["date_service"], 
         lambda: (f"Date_{uuid.uuid4().hex[:8]}", datetime.date(2023, 1, 1) + datetime.timedelta(days=random.randint(1, 365)))),
    ]
    
    results = {}
    
    for type_name, value_class, service, value_generator in value_types:
        # Define async benchmark function for this value type
        async def create_value_benchmark():
            name, value = value_generator()
            entity = value_class(
                id=str(uuid.uuid4()),
                name=name,
                value=value,
            )
            
            result = await service.create(entity)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(create_value_benchmark()),
            iterations=10,
            rounds=3,
            name=f"create_{type_name}_value"
        )
        
        results[type_name] = runtime
        print(f"Creating {type_name} value took {runtime:.4f} seconds")
    
    # Compare results
    print("\nValue creation performance by type:")
    for type_name, time in results.items():
        print(f"  {type_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_value_query_performance(value_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying values with different filters."""
    # Test querying different value types
    query_configs = [
        ("text_by_name", value_services["text_service"], setup_benchmark_environment["text"], 
         lambda values: values[0].name, "find_by_name"),
        ("text_by_value", value_services["text_service"], setup_benchmark_environment["text"], 
         lambda values: values[0].value, "find_by_value"),
        ("integer_by_name", value_services["integer_service"], setup_benchmark_environment["integer"], 
         lambda values: values[0].name, "find_by_name"),
        ("integer_by_value", value_services["integer_service"], setup_benchmark_environment["integer"], 
         lambda values: values[0].value, "find_by_value"),
    ]
    
    results = {}
    
    for config_name, service, values, value_extractor, method_name in query_configs:
        if not values:
            print(f"Skipping {config_name} benchmark: no test values available")
            continue
        
        query_value = value_extractor(values)
        
        # Define async benchmark function
        async def query_benchmark():
            if method_name == "find_by_name":
                result = await service.find_by_name(query_value)
            elif method_name == "find_by_value":
                result = await service.find_by_value(query_value)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_benchmark()),
            iterations=10,
            rounds=3,
            name=f"query_{config_name}"
        )
        
        results[config_name] = runtime
        print(f"Querying {config_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nValue query performance by type:")
    for config_name, time in results.items():
        print(f"  {config_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_text_search_performance(value_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of text search operations with different term lengths."""
    text_service = value_services["text_service"]
    
    # Define search terms of different lengths
    search_terms = [
        "test",         # Short term
        "benchmark",    # Medium term
        "performance",  # Longer term
        "nonexistent",  # Term that won't match
    ]
    
    results = {}
    
    for term in search_terms:
        # Define async benchmark function
        async def search_benchmark():
            result = await text_service.search(term)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(search_benchmark()),
            iterations=5,
            rounds=3,
            name=f"text_search_{term}"
        )
        
        results[term] = runtime
        print(f"Text search for '{term}' took {runtime:.4f} seconds")
    
    # Compare results
    print("\nText search performance by term:")
    for term, time in results.items():
        print(f"  '{term}': {time:.4f} seconds")


@pytest.mark.asyncio
async def test_batch_value_creation_performance(value_services, benchmark):
    """Benchmark the performance of creating values in batches."""
    text_service = value_services["text_service"]
    
    # Define batch sizes to test
    batch_sizes = [10, 50, 100]
    results = {}
    
    for batch_size in batch_sizes:
        # Define async benchmark function for this batch size
        async def batch_creation_benchmark():
            # Create a batch of text values
            values = []
            for i in range(batch_size):
                text_value = TextValue(
                    id=str(uuid.uuid4()),
                    name=f"BatchText_{i}_{uuid.uuid4().hex[:8]}",
                    value=f"Batch text value #{i}. Created for benchmark testing with batch size {batch_size}."
                )
                values.append(text_value)
            
            # Create them one by one (in a real implementation, you'd do this in a batch)
            created_values = []
            for value in values:
                result = await text_service.create(value)
                if result.is_success:
                    created_values.append(result.value)
            
            return created_values
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(batch_creation_benchmark()),
            iterations=3,
            rounds=3,
            name=f"batch_value_create_{batch_size}"
        )
        
        results[batch_size] = runtime
        print(f"Creating {batch_size} values in batch took {runtime:.4f} seconds")
    
    # Calculate per-value time
    per_value_times = {size: time/size for size, time in results.items()}
    
    # Compare results
    print("\nBatch value creation performance:")
    for size, time in results.items():
        print(f"  Batch size {size}: {time:.4f} seconds total, {per_value_times[size]:.4f} seconds per value")


@pytest.mark.asyncio
async def test_value_list_performance(value_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of listing values with different filters and limits."""
    text_service = value_services["text_service"]
    
    # Define different list configurations
    list_configs = [
        ("no_filter_limit_10", {}, 10),
        ("no_filter_limit_50", {}, 50),
        ("no_filter_limit_100", {}, 100),
        ("name_filter", {"name": {"lookup": "ilike", "val": "%Text_%"}}, 50),
        ("value_filter", {"value": {"lookup": "ilike", "val": "%benchmark%"}}, 50),
    ]
    
    results = {}
    
    for config_name, filters, limit in list_configs:
        # Define async benchmark function
        async def list_benchmark():
            result = await text_service.repository.list(filters=filters, limit=limit)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(list_benchmark()),
            iterations=5,
            rounds=3,
            name=f"value_list_{config_name}"
        )
        
        results[config_name] = runtime
        print(f"Listing values with config '{config_name}' took {runtime:.4f} seconds")
    
    # Compare results
    print("\nValue listing performance by configuration:")
    for config_name, time in results.items():
        print(f"  {config_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_value_validation_performance(benchmark):
    """Benchmark the performance of validating different types of values."""
    # Test validation with different value types
    validation_tests = [
        ("text_valid", lambda: TextValue(id=str(uuid.uuid4()), name="Valid Text", value="Valid text value")),
        ("text_invalid", lambda: TextValue(id=str(uuid.uuid4()), name="", value="Invalid text value")),
        ("integer_valid", lambda: IntegerValue(id=str(uuid.uuid4()), name="Valid Integer", value=100)),
        ("integer_invalid", lambda: IntegerValue(id=str(uuid.uuid4()), name="", value=100)),
        ("boolean_valid", lambda: BooleanValue(id=str(uuid.uuid4()), name="Valid Boolean", value=True)),
        ("boolean_invalid", lambda: BooleanValue(id=str(uuid.uuid4()), name="", value=True)),
        ("date_valid", lambda: DateValue(id=str(uuid.uuid4()), name="Valid Date", value=datetime.date(2023, 1, 1))),
        ("date_invalid", lambda: DateValue(id=str(uuid.uuid4()), name="", value=datetime.date(2023, 1, 1))),
    ]
    
    results = {}
    
    for test_name, entity_factory in validation_tests:
        # Define validation function
        def validation_benchmark():
            entity = entity_factory()
            try:
                entity.validate()
                return True
            except Exception:
                return False
        
        # Run benchmark
        runtime = benchmark.pedantic(
            validation_benchmark,
            iterations=1000,
            rounds=3,
            name=f"validation_{test_name}"
        )
        
        results[test_name] = runtime
        print(f"Validating {test_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nValue validation performance by type:")
    for test_name, time in results.items():
        print(f"  {test_name}: {time:.4f} seconds")