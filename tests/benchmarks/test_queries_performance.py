"""
Performance benchmarks for queries module functionality.

These benchmarks measure the performance of query operations
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
from datetime import datetime

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import create_model, BaseModel, Field

from uno.database.session import async_session
from uno.queries.filter import UnoFilter
from uno.queries.filter_manager import UnoFilterManager
from uno.queries.executor import QueryExecutor, get_query_executor
from uno.queries.models import QueryModel
from uno.queries.objs import Query, QueryValue, QueryPath
from uno.enums import Include, Match


# Skip these benchmarks in normal test runs
pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(
        "not config.getoption('--run-benchmark')",
        reason="Only run when --run-benchmark is specified"
    )
]


@pytest.fixture(scope="module")
async def setup_benchmark_environment():
    """Set up the benchmark environment with test data."""
    # Create a session context
    async with async_session() as session:
        # Create test tables
        await session.execute(text("""
        DROP TABLE IF EXISTS benchmark_query_test;
        
        CREATE TABLE benchmark_query_test (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            value INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            data JSONB
        );
        
        CREATE INDEX benchmark_query_test_name_idx ON benchmark_query_test(name);
        CREATE INDEX benchmark_query_test_category_idx ON benchmark_query_test(category);
        CREATE INDEX benchmark_query_test_value_idx ON benchmark_query_test(value);
        CREATE INDEX benchmark_query_test_is_active_idx ON benchmark_query_test(is_active);
        
        -- Create QueryPath table if it doesn't exist
        CREATE TABLE IF NOT EXISTS query_path (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            cypher_path TEXT NOT NULL,
            source_meta_type_id TEXT NOT NULL,
            target_meta_type_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create query tables if they don't exist
        CREATE TABLE IF NOT EXISTS query (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            query_meta_type_id TEXT NOT NULL,
            match_values TEXT DEFAULT 'ANY',
            include_values TEXT DEFAULT 'INCLUDE',
            match_queries TEXT DEFAULT 'ANY',
            include_queries TEXT DEFAULT 'INCLUDE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS query_value (
            id TEXT PRIMARY KEY,
            query_id TEXT NOT NULL,
            query_path_id TEXT NOT NULL,
            lookup TEXT DEFAULT 'equal',
            include TEXT DEFAULT 'INCLUDE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (query_id) REFERENCES query(id) ON DELETE CASCADE,
            FOREIGN KEY (query_path_id) REFERENCES query_path(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS query_value_ref (
            id TEXT PRIMARY KEY,
            query_value_id TEXT NOT NULL,
            ref_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (query_value_id) REFERENCES query_value(id) ON DELETE CASCADE
        );
        """))
        
        await session.commit()
        
        # Insert test data
        categories = ["Category A", "Category B", "Category C"]
        record_counts = 1000
        records = []
        
        for i in range(record_counts):
            record = {
                "id": str(uuid.uuid4()),
                "name": f"Record_{i}",
                "category": categories[i % len(categories)],
                "value": random.randint(1, 1000),
                "created_at": datetime.utcnow(),
                "is_active": random.choice([True, False]),
                "data": json.dumps({
                    "field1": f"value_{i}",
                    "field2": random.randint(1, 100),
                    "tags": [f"tag_{j}" for j in range(random.randint(1, 5))],
                    "metadata": {"key1": f"val_{i}", "key2": random.randint(1, 10)}
                })
            }
            records.append(record)
        
        # Insert records in batches
        for i in range(0, len(records), 100):
            batch = records[i:i+100]
            stmt = text("""
            INSERT INTO benchmark_query_test (id, name, category, value, created_at, is_active, data)
            VALUES (:id, :name, :category, :value, :created_at, :is_active, :data::jsonb)
            """)
            await session.execute(stmt, batch)
        
        await session.commit()
        print(f"Inserted {len(records)} test records")
        
        # Create query paths
        query_paths = [
            {
                "id": "path_name",
                "name": "Name Path",
                "description": "Path for querying by name",
                "cypher_path": "(s:BenchmarkQueryTest)-[:HAS_NAME]->(t:Name)",
                "source_meta_type_id": "benchmark_query_test",
                "target_meta_type_id": "name"
            },
            {
                "id": "path_category",
                "name": "Category Path",
                "description": "Path for querying by category",
                "cypher_path": "(s:BenchmarkQueryTest)-[:HAS_CATEGORY]->(t:Category)",
                "source_meta_type_id": "benchmark_query_test",
                "target_meta_type_id": "category"
            },
            {
                "id": "path_value",
                "name": "Value Path",
                "description": "Path for querying by value",
                "cypher_path": "(s:BenchmarkQueryTest)-[:HAS_VALUE]->(t:Value)",
                "source_meta_type_id": "benchmark_query_test",
                "target_meta_type_id": "value"
            },
            {
                "id": "path_active",
                "name": "Active Path",
                "description": "Path for querying by active status",
                "cypher_path": "(s:BenchmarkQueryTest)-[:IS_ACTIVE]->(t:Active)",
                "source_meta_type_id": "benchmark_query_test",
                "target_meta_type_id": "active"
            }
        ]
        
        for path in query_paths:
            stmt = text("""
            INSERT INTO query_path (id, name, description, cypher_path, source_meta_type_id, target_meta_type_id)
            VALUES (:id, :name, :description, :cypher_path, :source_meta_type_id, :target_meta_type_id)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                cypher_path = EXCLUDED.cypher_path,
                source_meta_type_id = EXCLUDED.source_meta_type_id,
                target_meta_type_id = EXCLUDED.target_meta_type_id,
                updated_at = CURRENT_TIMESTAMP
            """)
            await session.execute(stmt, path)
        
        await session.commit()
        print(f"Created {len(query_paths)} query paths")
        
        # Create sample queries
        queries = [
            {
                "id": "query_category_a",
                "name": "Category A Query",
                "description": "Query for records in Category A",
                "query_meta_type_id": "benchmark_query_test",
                "match_values": "ANY",
                "include_values": "INCLUDE",
            },
            {
                "id": "query_high_value",
                "name": "High Value Query",
                "description": "Query for records with high value",
                "query_meta_type_id": "benchmark_query_test",
                "match_values": "ANY",
                "include_values": "INCLUDE",
            },
            {
                "id": "query_active_records",
                "name": "Active Records Query",
                "description": "Query for active records",
                "query_meta_type_id": "benchmark_query_test",
                "match_values": "ANY",
                "include_values": "INCLUDE",
            },
            {
                "id": "query_complex",
                "name": "Complex Query",
                "description": "Complex query with multiple conditions",
                "query_meta_type_id": "benchmark_query_test",
                "match_values": "ALL",
                "include_values": "INCLUDE",
            }
        ]
        
        for query_data in queries:
            stmt = text("""
            INSERT INTO query (id, name, description, query_meta_type_id, match_values, include_values)
            VALUES (:id, :name, :description, :query_meta_type_id, :match_values, :include_values)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                query_meta_type_id = EXCLUDED.query_meta_type_id,
                match_values = EXCLUDED.match_values,
                include_values = EXCLUDED.include_values,
                updated_at = CURRENT_TIMESTAMP
            """)
            await session.execute(stmt, query_data)
        
        await session.commit()
        print(f"Created {len(queries)} queries")
        
        # Create query values
        query_values = [
            {
                "id": "qv_category_a",
                "query_id": "query_category_a",
                "query_path_id": "path_category",
                "lookup": "equal",
                "include": "INCLUDE"
            },
            {
                "id": "qv_high_value",
                "query_id": "query_high_value",
                "query_path_id": "path_value",
                "lookup": "gt",
                "include": "INCLUDE"
            },
            {
                "id": "qv_active",
                "query_id": "query_active_records",
                "query_path_id": "path_active",
                "lookup": "equal",
                "include": "INCLUDE"
            },
            {
                "id": "qv_complex_1",
                "query_id": "query_complex",
                "query_path_id": "path_category",
                "lookup": "equal",
                "include": "INCLUDE"
            },
            {
                "id": "qv_complex_2",
                "query_id": "query_complex",
                "query_path_id": "path_value",
                "lookup": "gt",
                "include": "INCLUDE"
            },
            {
                "id": "qv_complex_3",
                "query_id": "query_complex",
                "query_path_id": "path_active",
                "lookup": "equal",
                "include": "INCLUDE"
            }
        ]
        
        for qv in query_values:
            stmt = text("""
            INSERT INTO query_value (id, query_id, query_path_id, lookup, include)
            VALUES (:id, :query_id, :query_path_id, :lookup, :include)
            ON CONFLICT (id) DO UPDATE SET
                query_id = EXCLUDED.query_id,
                query_path_id = EXCLUDED.query_path_id,
                lookup = EXCLUDED.lookup,
                include = EXCLUDED.include,
                updated_at = CURRENT_TIMESTAMP
            """)
            await session.execute(stmt, qv)
        
        await session.commit()
        print(f"Created {len(query_values)} query values")
        
        # Create query value references
        query_value_refs = [
            {"id": str(uuid.uuid4()), "query_value_id": "qv_category_a", "ref_id": "Category A"},
            {"id": str(uuid.uuid4()), "query_value_id": "qv_high_value", "ref_id": "500"},
            {"id": str(uuid.uuid4()), "query_value_id": "qv_active", "ref_id": "true"},
            {"id": str(uuid.uuid4()), "query_value_id": "qv_complex_1", "ref_id": "Category B"},
            {"id": str(uuid.uuid4()), "query_value_id": "qv_complex_2", "ref_id": "700"},
            {"id": str(uuid.uuid4()), "query_value_id": "qv_complex_3", "ref_id": "true"}
        ]
        
        for ref in query_value_refs:
            stmt = text("""
            INSERT INTO query_value_ref (id, query_value_id, ref_id)
            VALUES (:id, :query_value_id, :ref_id)
            ON CONFLICT (id) DO UPDATE SET
                query_value_id = EXCLUDED.query_value_id,
                ref_id = EXCLUDED.ref_id
            """)
            await session.execute(stmt, ref)
        
        await session.commit()
        print(f"Created {len(query_value_refs)} query value references")
    
    # Create a sample model for filter testing
    class BenchmarkQueryTestModel:
        __tablename__ = "benchmark_query_test"
        
        id = "id"
        name = "name"
        category = "category"
        value = "value"
        created_at = "created_at"
        is_active = "is_active"
        data = "data"
        
        @property
        def __table__(self):
            class TableMock:
                def __init__(self):
                    self.name = self.__tablename__
                    self.columns = {
                        "id": ColumnMock("id", str),
                        "name": ColumnMock("name", str),
                        "category": ColumnMock("category", str),
                        "value": ColumnMock("value", int),
                        "created_at": ColumnMock("created_at", datetime),
                        "is_active": ColumnMock("is_active", bool),
                        "data": ColumnMock("data", dict)
                    }
                    
                def columns_keys(self):
                    return list(self.columns.keys())
            
            return TableMock()
    
    # Mock column class for filter testing
    class ColumnMock:
        def __init__(self, name, python_type):
            self.name = name
            self.type = TypeMock(python_type)
            self.info = {}
            self.foreign_keys = []
            
    class TypeMock:
        def __init__(self, python_type):
            self.python_type = python_type
    
    # Create Pydantic model for tests
    ModelFields = {
        "id": (str, Field()),
        "name": (str, Field()),
        "category": (str, Field()),
        "value": (int, Field()),
        "created_at": (datetime, Field()),
        "is_active": (bool, Field()),
        "data": (Dict[str, Any], Field())
    }
    
    BenchmarkQueryTestSchema = create_model(
        "BenchmarkQueryTestSchema",
        **ModelFields
    )
    
    # Create the test environment data
    test_env = {
        "records": records,
        "model": BenchmarkQueryTestModel,
        "schema": BenchmarkQueryTestSchema,
        "query_paths": query_paths,
        "queries": queries,
        "query_values": query_values
    }
    
    yield test_env
    
    # Cleanup
    async with async_session() as session:
        await session.execute(text("DROP TABLE IF EXISTS benchmark_query_test"))
        await session.commit()


@pytest.mark.asyncio
async def test_filter_manager_creation_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of creating filters with UnoFilterManager."""
    model = setup_benchmark_environment["model"]
    
    # Define benchmark function
    def create_filters_benchmark():
        filter_manager = UnoFilterManager()
        filters = filter_manager.create_filters_from_table(model)
        return filters
    
    # Run benchmark
    runtime = benchmark.pedantic(
        create_filters_benchmark,
        iterations=50,
        rounds=3,
        name="filter_manager_creation"
    )
    
    print(f"Filter manager creation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_filter_params_creation_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of creating filter params with UnoFilterManager."""
    model = setup_benchmark_environment["model"]
    schema = setup_benchmark_environment["schema"]
    
    # Initialize filter manager with filters
    filter_manager = UnoFilterManager()
    filters = filter_manager.create_filters_from_table(model)
    
    # Define benchmark function
    def create_filter_params_benchmark():
        filter_params = filter_manager.create_filter_params(schema)
        return filter_params
    
    # Run benchmark
    runtime = benchmark.pedantic(
        create_filter_params_benchmark,
        iterations=50,
        rounds=3,
        name="filter_params_creation"
    )
    
    print(f"Filter params creation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_filter_validation_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of validating filter params."""
    model = setup_benchmark_environment["model"]
    schema = setup_benchmark_environment["schema"]
    
    # Initialize filter manager with filters
    filter_manager = UnoFilterManager()
    filters = filter_manager.create_filters_from_table(model)
    
    # Create filter params class
    FilterParams = filter_manager.create_filter_params(schema)
    
    # Create sample filter params
    filter_params = FilterParams(
        limit=10,
        offset=0,
        order_by="name",
        category="Category A",
        value={"gt": 500},
        is_active=True
    )
    
    # Define benchmark function
    def validate_filters_benchmark():
        try:
            validated_filters = filter_manager.validate_filter_params(filter_params, schema)
            return validated_filters
        except Exception:
            # Handle validation errors
            return None
    
    # Run benchmark
    runtime = benchmark.pedantic(
        validate_filters_benchmark,
        iterations=100,
        rounds=3,
        name="filter_validation"
    )
    
    print(f"Filter validation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_query_execution_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of executing queries with different complexities."""
    # Load the queries data
    queries_data = setup_benchmark_environment["queries"]
    
    # Create a query executor
    query_executor = QueryExecutor(cache_enabled=False)
    
    # Create sample query objects with increasing complexity
    async with async_session() as session:
        # Simple query (single condition)
        simple_query_result = await session.execute(
            select(Query).where(Query.id == "query_category_a")
        )
        simple_query = simple_query_result.scalars().first()
        
        # Medium query (single condition with range)
        medium_query_result = await session.execute(
            select(Query).where(Query.id == "query_high_value")
        )
        medium_query = medium_query_result.scalars().first()
        
        # Complex query (multiple conditions, AND)
        complex_query_result = await session.execute(
            select(Query).where(Query.id == "query_complex")
        )
        complex_query = complex_query_result.scalars().first()
        
        if not simple_query or not medium_query or not complex_query:
            pytest.skip("Required test queries not found")
        
        # Load query values
        for query in [simple_query, medium_query, complex_query]:
            query_values_result = await session.execute(
                select(QueryValue).where(QueryValue.query_id == query.id)
            )
            query.query_values = query_values_result.scalars().all()
            
            # Load values for each query value
            for qv in query.query_values:
                # Mock the values as these would come from a different table
                # In a real implementation this would load the actual values
                qv.values = [type('Value', (), {'id': 'mocked_value_id'})]
    
    # Define benchmark functions for each query type
    queries = {
        "simple_query": simple_query,
        "medium_query": medium_query,
        "complex_query": complex_query
    }
    
    results = {}
    
    for query_name, query in queries.items():
        # Define async benchmark function
        async def execute_query_benchmark():
            result = await query_executor.execute_query(query)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(execute_query_benchmark()),
            iterations=5,
            rounds=3,
            name=f"query_execution_{query_name}"
        )
        
        results[query_name] = runtime
        print(f"Query execution for {query_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nQuery execution performance by complexity:")
    for query_name, time in results.items():
        print(f"  {query_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_query_match_check_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of checking if a record matches a query."""
    # Create a query executor with cache disabled for benchmarks
    query_executor = QueryExecutor(cache_enabled=False)
    
    # Get a sample record ID
    records = setup_benchmark_environment["records"]
    record_id = records[0]["id"] if records else None
    
    if not record_id:
        pytest.skip("No test records available")
    
    # Create a sample query
    query = Query(
        id="benchmark_match_query",
        name="Benchmark Match Query",
        description="Query for benchmarking match checks",
        query_meta_type_id="benchmark_query_test",
        match_values=Match.ANY,
        include_values=Include.INCLUDE,
        # Add sample query values with mocked paths
        query_values=[
            QueryValue(
                id="match_qv_1",
                query_path_id="path_category",
                lookup="equal",
                include=Include.INCLUDE,
                # Mocked values
                values=[type('Value', (), {'id': 'Category A'})]
            ),
            QueryValue(
                id="match_qv_2",
                query_path_id="path_value",
                lookup="gt",
                include=Include.INCLUDE,
                # Mocked values
                values=[type('Value', (), {'id': '500'})]
            )
        ]
    )
    
    # Define async benchmark function
    async def check_match_benchmark():
        result = await query_executor.check_record_matches_query(query, record_id)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(check_match_benchmark()),
        iterations=20,
        rounds=3,
        name="query_match_check"
    )
    
    print(f"Query match check took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_query_count_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of counting query matches."""
    # Create a query executor with cache disabled for benchmarks
    query_executor = QueryExecutor(cache_enabled=False)
    
    # Create a sample query
    query = Query(
        id="benchmark_count_query",
        name="Benchmark Count Query",
        description="Query for benchmarking count operation",
        query_meta_type_id="benchmark_query_test",
        match_values=Match.ANY,
        include_values=Include.INCLUDE,
        # Add sample query values with mocked paths
        query_values=[
            QueryValue(
                id="count_qv_1",
                query_path_id="path_category",
                lookup="equal",
                include=Include.INCLUDE,
                # Mocked values
                values=[type('Value', (), {'id': 'Category A'})]
            )
        ]
    )
    
    # Define async benchmark function
    async def count_matches_benchmark():
        result = await query_executor.count_query_matches(query)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(count_matches_benchmark()),
        iterations=10,
        rounds=3,
        name="query_count"
    )
    
    print(f"Query count took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_query_cache_performance(benchmark):
    """Benchmark the performance of query caching."""
    # Create a query executor with cache enabled
    query_executor = QueryExecutor(cache_enabled=True, cache_ttl=60)
    
    # Create a sample query with a unique ID for cache testing
    query_id = f"cache_test_{uuid.uuid4()}"
    query = Query(
        id=query_id,
        name="Cache Test Query",
        description="Query for cache testing",
        query_meta_type_id="benchmark_query_test",
        match_values=Match.ANY,
        include_values=Include.INCLUDE,
        # Add minimal query values
        query_values=[
            QueryValue(
                id=f"cache_qv_{uuid.uuid4()}",
                query_path_id="path_category",
                lookup="equal",
                include=Include.INCLUDE,
                # Mocked values
                values=[type('Value', (), {'id': 'Category A'})]
            )
        ]
    )
    
    # Define async benchmark functions for first and subsequent executions
    async def first_execution_benchmark():
        # This will be a cache miss
        result = await query_executor.execute_query(query, force_refresh=True)
        return result
    
    async def cached_execution_benchmark():
        # This should be a cache hit
        result = await query_executor.execute_query(query, force_refresh=False)
        return result
    
    # Run first execution benchmark (cache miss)
    first_runtime = benchmark.pedantic(
        lambda: asyncio.run(first_execution_benchmark()),
        iterations=5,
        rounds=2,
        name="query_cache_miss"
    )
    
    print(f"Query execution with cache miss took {first_runtime:.4f} seconds")
    
    # Run cached execution benchmark (cache hit)
    cached_runtime = benchmark.pedantic(
        lambda: asyncio.run(cached_execution_benchmark()),
        iterations=20,
        rounds=3,
        name="query_cache_hit"
    )
    
    print(f"Query execution with cache hit took {cached_runtime:.4f} seconds")
    print(f"Cache speedup factor: {first_runtime / cached_runtime:.2f}x")