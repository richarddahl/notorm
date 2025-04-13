"""
Performance benchmarks for database module functionality.

These benchmarks measure the performance of database operations
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

from sqlalchemy import (
    select,
    func,
    text,
    Table,
    Column,
    String,
    Integer,
    MetaData,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

from uno.database.session import AsyncSessionFactory, AsyncSessionContext, async_session
from uno.database.config import ConnectionConfig
from uno.database.engine.asynceng import AsyncEngineFactory
from uno.database.db_manager import DBManager
from uno.settings import uno_settings


# Skip these benchmarks in normal test runs
pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(
        "not config.getoption('--run-benchmark')",
        reason="Only run when --run-benchmark is specified"
    )
]


@pytest.fixture(scope="module")
def connection_config():
    """Create a connection configuration for tests."""
    return ConnectionConfig(
        db_role=uno_settings.DB_ROLE,
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_ASYNC_DRIVER,
    )


@pytest.fixture(scope="module")
def engine_factory():
    """Create an engine factory for tests."""
    return AsyncEngineFactory()


@pytest.fixture(scope="module")
def session_factory(engine_factory):
    """Create a session factory for tests."""
    return AsyncSessionFactory(engine_factory=engine_factory)


@pytest.fixture(scope="module")
async def setup_benchmark_environment(connection_config):
    """Set up the benchmark environment."""
    # Create a session context
    session_context = AsyncSessionContext(
        db_driver=connection_config.db_driver,
        db_name=connection_config.db_name,
        db_user_pw=connection_config.db_user_pw,
        db_role=connection_config.db_role,
        db_host=connection_config.db_host,
        db_port=connection_config.db_port,
    )
    
    # Create a test table for benchmarking
    async with session_context as session:
        await session.execute(text("""
        DROP TABLE IF EXISTS benchmark_db_test;
        
        CREATE TABLE benchmark_db_test (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data JSONB
        );
        
        CREATE INDEX benchmark_db_test_name_idx ON benchmark_db_test(name);
        CREATE INDEX benchmark_db_test_value_idx ON benchmark_db_test(value);
        """))
        
        await session.commit()
    
    # Insert test data
    record_counts = [100, 1000, 5000]
    batches = {}
    
    for count in record_counts:
        batch_name = f"batch_{count}"
        batches[batch_name] = []
        
        for i in range(count):
            record = {
                "id": str(uuid.uuid4()),
                "name": f"{batch_name}_record_{i}",
                "value": random.randint(1, 1000),
                "created_at": datetime.utcnow(),
                "data": json.dumps({
                    "field1": f"value_{i}",
                    "field2": random.randint(1, 100),
                    "field3": [1, 2, 3, 4, 5],
                    "field4": {"nested1": "value", "nested2": i}
                })
            }
            batches[batch_name].append(record)
    
    # Insert the batches
    async with session_context as session:
        for batch_name, records in batches.items():
            for i in range(0, len(records), 100):
                batch = records[i:i+100]
                stmt = text("""
                INSERT INTO benchmark_db_test (id, name, value, created_at, data)
                VALUES (:id, :name, :value, :created_at, :data::jsonb)
                """)
                await session.execute(stmt, batch)
            
            await session.commit()
            print(f"Inserted batch {batch_name} with {len(records)} records")
    
    yield {
        "batches": batches,
        "record_counts": record_counts,
    }
    
    # Cleanup
    async with session_context as session:
        await session.execute(text("DROP TABLE IF EXISTS benchmark_db_test;"))
        await session.commit()


@pytest.mark.asyncio
async def test_connection_establishment_performance(connection_config, benchmark):
    """Benchmark the performance of establishing a database connection."""
    
    # Define async benchmark function
    async def connection_benchmark():
        engine_factory = AsyncEngineFactory()
        engine = engine_factory.create_engine(connection_config)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(connection_benchmark()),
        iterations=5,
        rounds=3,
        name="connection_establishment"
    )
    
    print(f"Connection establishment took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_session_creation_performance(session_factory, connection_config, benchmark):
    """Benchmark the performance of creating a database session."""
    
    # Define async benchmark function
    async def session_creation_benchmark():
        session = session_factory.create_session(connection_config)
        await session.execute(text("SELECT 1"))
        await session.close()
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(session_creation_benchmark()),
        iterations=10,
        rounds=3,
        name="session_creation"
    )
    
    print(f"Session creation took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_session_context_performance(connection_config, benchmark):
    """Benchmark the performance of using a session context."""
    
    # Define async benchmark function
    async def session_context_benchmark():
        async with async_session(
            db_driver=connection_config.db_driver,
            db_name=connection_config.db_name,
            db_user_pw=connection_config.db_user_pw,
            db_role=connection_config.db_role,
            db_host=connection_config.db_host,
            db_port=connection_config.db_port,
        ) as session:
            await session.execute(text("SELECT 1"))
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(session_context_benchmark()),
        iterations=10,
        rounds=3,
        name="session_context"
    )
    
    print(f"Session context usage took {runtime:.4f} seconds")


@pytest.mark.asyncio
async def test_query_performance_by_size(setup_benchmark_environment, benchmark):
    """Benchmark the performance of queries on different dataset sizes."""
    
    record_counts = setup_benchmark_environment["record_counts"]
    results = {}
    
    for count in record_counts:
        batch_name = f"batch_{count}"
        
        # Define async benchmark function
        async def query_benchmark():
            async with async_session() as session:
                stmt = text(f"SELECT * FROM benchmark_db_test WHERE name LIKE '{batch_name}%%' LIMIT 100")
                result = await session.execute(stmt)
                rows = result.fetchall()
                return rows
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_benchmark()),
            iterations=5,
            rounds=3,
            name=f"query_size_{count}"
        )
        
        results[count] = runtime
        print(f"Query on {count} records took {runtime:.4f} seconds")
    
    # Compare results
    print("\nQuery performance by dataset size:")
    for count, time in results.items():
        print(f"  {count} records: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_transaction_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of database transactions."""
    
    # Define async benchmark function for single inserts
    async def single_insert_benchmark():
        records_to_insert = 100
        async with async_session() as session:
            for i in range(records_to_insert):
                record = {
                    "id": str(uuid.uuid4()),
                    "name": f"benchmark_single_insert_{i}",
                    "value": random.randint(1, 1000),
                    "created_at": datetime.utcnow(),
                    "data": json.dumps({"field1": f"value_{i}"})
                }
                stmt = text("""
                INSERT INTO benchmark_db_test (id, name, value, created_at, data)
                VALUES (:id, :name, :value, :created_at, :data::jsonb)
                """)
                await session.execute(stmt, record)
            
            await session.commit()
    
    # Define async benchmark function for batch inserts
    async def batch_insert_benchmark():
        records_to_insert = 100
        records = []
        
        for i in range(records_to_insert):
            record = {
                "id": str(uuid.uuid4()),
                "name": f"benchmark_batch_insert_{i}",
                "value": random.randint(1, 1000),
                "created_at": datetime.utcnow(),
                "data": json.dumps({"field1": f"value_{i}"})
            }
            records.append(record)
        
        async with async_session() as session:
            stmt = text("""
            INSERT INTO benchmark_db_test (id, name, value, created_at, data)
            VALUES (:id, :name, :value, :created_at, :data::jsonb)
            """)
            await session.execute(stmt, records)
            await session.commit()
    
    # Run benchmark for single inserts
    single_runtime = benchmark.pedantic(
        lambda: asyncio.run(single_insert_benchmark()),
        iterations=3,
        rounds=2,
        name="single_insert_transaction"
    )
    
    print(f"Single insert transaction took {single_runtime:.4f} seconds")
    
    # Run benchmark for batch inserts
    batch_runtime = benchmark.pedantic(
        lambda: asyncio.run(batch_insert_benchmark()),
        iterations=3,
        rounds=2,
        name="batch_insert_transaction"
    )
    
    print(f"Batch insert transaction took {batch_runtime:.4f} seconds")
    print(f"Performance improvement: {single_runtime / batch_runtime:.2f}x")


@pytest.mark.asyncio
async def test_query_with_filters_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of queries with different filter types."""
    
    # Define different query types to benchmark
    query_types = [
        ("simple_equality", "SELECT * FROM benchmark_db_test WHERE value = 500 LIMIT 10"),
        ("like_query", "SELECT * FROM benchmark_db_test WHERE name LIKE 'batch_1000%' LIMIT 10"),
        ("range_query", "SELECT * FROM benchmark_db_test WHERE value BETWEEN 100 AND 200 LIMIT 10"),
        ("json_query", "SELECT * FROM benchmark_db_test WHERE data->'field2' = '50' LIMIT 10"),
        ("complex_query", "SELECT * FROM benchmark_db_test WHERE value > 500 AND name LIKE 'batch_100%' AND data->'field2' > '50' LIMIT 10"),
    ]
    
    results = {}
    
    for query_name, query_sql in query_types:
        # Define async benchmark function
        async def filter_query_benchmark():
            async with async_session() as session:
                stmt = text(query_sql)
                result = await session.execute(stmt)
                rows = result.fetchall()
                return rows
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(filter_query_benchmark()),
            iterations=10,
            rounds=3,
            name=f"filter_{query_name}"
        )
        
        results[query_name] = runtime
        print(f"Query with {query_name} filter took {runtime:.4f} seconds")
    
    # Compare results
    print("\nQuery performance by filter type:")
    for query_name, time in results.items():
        print(f"  {query_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_connection_pooling_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of connection pooling with different concurrencies."""
    
    # Define concurrency levels to test
    concurrency_levels = [1, 5, 10, 20, 50]
    results = {}
    
    for concurrency in concurrency_levels:
        # Define async benchmark function that creates multiple sessions simultaneously
        async def pooling_benchmark():
            async def run_query():
                async with async_session() as session:
                    stmt = text("SELECT * FROM benchmark_db_test WHERE value > 500 LIMIT 10")
                    result = await session.execute(stmt)
                    rows = result.fetchall()
                    return rows
            
            # Run queries concurrently
            tasks = [run_query() for _ in range(concurrency)]
            return await asyncio.gather(*tasks)
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(pooling_benchmark()),
            iterations=3,
            rounds=2,
            name=f"pooling_concurrency_{concurrency}"
        )
        
        results[concurrency] = runtime
        print(f"Connection pooling with concurrency {concurrency} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nConnection pooling performance by concurrency level:")
    for concurrency, time in results.items():
        print(f"  Concurrency {concurrency}: {time:.4f} seconds, {time/concurrency:.4f} seconds per query")


@pytest.mark.asyncio
async def test_index_usage_performance(setup_benchmark_environment, benchmark):
    """Benchmark the performance of queries with and without indexes."""
    
    # Define queries to test
    queries = [
        # With index
        ("with_index_name", "SELECT * FROM benchmark_db_test WHERE name = 'batch_1000_record_500' LIMIT 1"),
        ("with_index_value", "SELECT * FROM benchmark_db_test WHERE value = 500 LIMIT 10"),
        
        # Without index (full scan)
        ("without_index", "SELECT * FROM benchmark_db_test WHERE data->>'field1' = 'value_500' LIMIT 1"),
    ]
    
    results = {}
    
    for query_name, query_sql in queries:
        # Define async benchmark function
        async def index_query_benchmark():
            async with async_session() as session:
                stmt = text(query_sql)
                result = await session.execute(stmt)
                rows = result.fetchall()
                return rows
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(index_query_benchmark()),
            iterations=10,
            rounds=3,
            name=f"index_{query_name}"
        )
        
        results[query_name] = runtime
        print(f"Query {query_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nQuery performance with and without indexes:")
    for query_name, time in results.items():
        print(f"  {query_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_db_manager_operations_performance(connection_config, benchmark):
    """Benchmark the performance of DBManager operations."""
    
    # Create a connection provider
    def get_connection():
        return psycopg.connect(
            host=connection_config.db_host,
            port=connection_config.db_port,
            user=connection_config.db_role,
            password=connection_config.db_user_pw,
            dbname=connection_config.db_name,
        )
    
    # Create a DBManager
    import psycopg
    from contextlib import contextmanager
    
    @contextmanager
    def connection_provider():
        conn = get_connection()
        try:
            yield conn
        finally:
            conn.close()
    
    db_manager = DBManager(connection_provider)
    
    # Define different operations to benchmark
    operations = [
        ("schema_exists", lambda: db_manager.table_exists("benchmark_db_test")),
        ("create_schema", lambda: db_manager.create_schema("benchmark_schema")),
        ("drop_schema", lambda: db_manager.drop_schema("benchmark_schema", cascade=True)),
    ]
    
    results = {}
    
    for op_name, op_func in operations:
        # Define benchmark function
        def operation_benchmark():
            return op_func()
        
        # Run benchmark
        runtime = benchmark.pedantic(
            operation_benchmark,
            iterations=5,
            rounds=3,
            name=f"db_manager_{op_name}"
        )
        
        results[op_name] = runtime
        print(f"DBManager operation {op_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nDBManager operation performance:")
    for op_name, time in results.items():
        print(f"  {op_name}: {time:.4f} seconds")