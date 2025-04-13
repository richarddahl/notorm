"""
Tests for the query optimizer module.

These tests verify the functionality of the query optimizer system.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy import text, select, MetaData, Table, Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncConnection
from sqlalchemy.sql import Select

from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    IndexType,
    QueryPlan,
    IndexRecommendation,
    QueryRewrite,
    QueryStatistics,
    OptimizationConfig,
    QueryOptimizer,
    optimize_query,
    optimized_query,
)
from uno.core.errors.result import Result, Ok, Err


# Test QueryPlan
def test_query_plan():
    """Test QueryPlan class."""
    # Create a query plan
    plan = QueryPlan(
        plan_type="Select",
        estimated_cost=100.0,
        estimated_rows=1000,
        operations=[
            {"type": "Seq Scan", "cost": 100.0, "rows": 1000, "width": 10},
            {"type": "Sort", "cost": 200.0, "rows": 1000, "width": 10},
        ],
        table_scans=["users"],
        join_types=["Nested Loop"],
        total_cost=300.0,
        execution_time=0.5,
    )
    
    # Test basic properties
    assert plan.plan_type == "Select"
    assert plan.estimated_cost == 100.0
    assert plan.estimated_rows == 1000
    assert len(plan.operations) == 2
    assert plan.total_cost == 300.0
    assert plan.execution_time == 0.5
    
    # Test derived properties
    assert plan.has_sequential_scans is True
    assert plan.has_nested_loops is True
    assert plan.complexity == QueryComplexity.MODERATE


# Test IndexRecommendation
def test_index_recommendation():
    """Test IndexRecommendation class."""
    # Create an index recommendation
    rec = IndexRecommendation(
        table_name="users",
        column_names=["email", "status"],
        index_type=IndexType.BTREE,
        index_name="idx_users_email_status",
        query_pattern="WHERE email = ? AND status = ?",
        estimated_improvement=0.6,
    )
    
    # Test basic properties
    assert rec.table_name == "users"
    assert rec.column_names == ["email", "status"]
    assert rec.index_type == IndexType.BTREE
    assert rec.index_name == "idx_users_email_status"
    assert rec.query_pattern == "WHERE email = ? AND status = ?"
    assert rec.estimated_improvement == 0.6
    assert rec.implemented is False
    assert rec._creation_sql is None
    
    # Test get_creation_sql
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email_status ON users (email, status)"
    assert rec._creation_sql == sql  # Cached
    
    # Test with different index type
    rec.index_type = IndexType.GIN
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email_status ON users USING gin (email, status)"
    
    # Test automatic index name generation
    rec = IndexRecommendation(
        table_name="users",
        column_names=["email", "status"],
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email_status ON users (email, status)"
    
    # Test to_dict
    rec_dict = rec.to_dict()
    assert rec_dict["table_name"] == "users"
    assert rec_dict["column_names"] == ["email", "status"]
    assert rec_dict["index_type"] == "btree"  # Default
    assert "creation_sql" in rec_dict


# Test QueryRewrite
def test_query_rewrite():
    """Test QueryRewrite class."""
    # Create a query rewrite
    rewrite = QueryRewrite(
        original_query="SELECT DISTINCT * FROM users",
        rewritten_query="SELECT * FROM users",
        rewrite_type="remove_unnecessary_distinct",
        estimated_improvement=0.2,
        reason="DISTINCT is unnecessary when selecting primary key",
    )
    
    # Test basic properties
    assert rewrite.original_query == "SELECT DISTINCT * FROM users"
    assert rewrite.rewritten_query == "SELECT * FROM users"
    assert rewrite.rewrite_type == "remove_unnecessary_distinct"
    assert rewrite.estimated_improvement == 0.2
    assert rewrite.reason == "DISTINCT is unnecessary when selecting primary key"
    
    # Test to_dict
    rewrite_dict = rewrite.to_dict()
    assert rewrite_dict["original_query"] == "SELECT DISTINCT * FROM users"
    assert rewrite_dict["rewritten_query"] == "SELECT * FROM users"
    assert rewrite_dict["rewrite_type"] == "remove_unnecessary_distinct"
    assert rewrite_dict["estimated_improvement"] == 0.2
    assert rewrite_dict["reason"] == "DISTINCT is unnecessary when selecting primary key"


# Test QueryStatistics
def test_query_statistics():
    """Test QueryStatistics class."""
    # Create query statistics
    stats = QueryStatistics(
        query_hash="abc123",
        query_text="SELECT * FROM users",
    )
    
    # Test initial state
    assert stats.query_hash == "abc123"
    assert stats.query_text == "SELECT * FROM users"
    assert stats.execution_count == 0
    assert stats.total_execution_time == 0.0
    assert stats.min_execution_time is None
    assert stats.max_execution_time is None
    assert stats.avg_result_size == 0.0
    assert stats.first_seen > 0
    assert stats.last_seen > 0
    assert stats.latest_plan is None
    
    # Test record_execution
    stats.record_execution(0.5, 100)
    assert stats.execution_count == 1
    assert stats.total_execution_time == 0.5
    assert stats.min_execution_time == 0.5
    assert stats.max_execution_time == 0.5
    assert stats.avg_result_size == 100.0
    
    # Record another execution
    stats.record_execution(0.3, 50)
    assert stats.execution_count == 2
    assert stats.total_execution_time == 0.8
    assert stats.min_execution_time == 0.3
    assert stats.max_execution_time == 0.5
    assert stats.avg_result_size == 75.0  # (100 + 50) / 2
    
    # Test derived properties
    assert stats.avg_execution_time == 0.4  # 0.8 / 2
    assert stats.frequency > 0  # Depends on timing
    
    # Test to_dict
    stats_dict = stats.to_dict()
    assert stats_dict["query_hash"] == "abc123"
    assert stats_dict["query_text"] == "SELECT * FROM users"
    assert stats_dict["execution_count"] == 2
    assert stats_dict["avg_execution_time"] == 0.4
    assert stats_dict["min_execution_time"] == 0.3
    assert stats_dict["max_execution_time"] == 0.5
    assert stats_dict["avg_result_size"] == 75.0


# Test OptimizationConfig
def test_optimization_config():
    """Test OptimizationConfig class."""
    # Test default config
    config = OptimizationConfig()
    assert config.enabled is True
    assert config.optimization_level == OptimizationLevel.STANDARD
    assert config.analyze_queries is True
    assert config.rewrite_queries is True
    assert config.recommend_indexes is True
    assert config.auto_implement_indexes is False
    
    # Test custom config
    config = OptimizationConfig(
        enabled=False,
        optimization_level=OptimizationLevel.AGGRESSIVE,
        auto_implement_indexes=True,
        slow_query_threshold=2.0,
    )
    assert config.enabled is False
    assert config.optimization_level == OptimizationLevel.AGGRESSIVE
    assert config.auto_implement_indexes is True
    assert config.slow_query_threshold == 2.0


# Test QueryOptimizer initialization
def test_query_optimizer_init():
    """Test QueryOptimizer initialization."""
    # Create with defaults
    optimizer = QueryOptimizer()
    assert optimizer.session is None
    assert optimizer.engine is None
    assert optimizer.config.enabled is True
    assert len(optimizer._query_stats) == 0
    assert len(optimizer._index_recommendations) == 0
    assert len(optimizer._query_rewrites) == 0
    
    # Create with custom config
    config = OptimizationConfig(
        enabled=False,
        optimization_level=OptimizationLevel.BASIC,
    )
    optimizer = QueryOptimizer(config=config)
    assert optimizer.config.enabled is False
    assert optimizer.config.optimization_level == OptimizationLevel.BASIC


# Test analyze_query
@pytest.mark.asyncio
async def test_analyze_query():
    """Test analyze_query method."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Setup mock response for EXPLAIN
    plan_data = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "users",
            "Total Cost": 100.0,
            "Plan Rows": 1000,
            "Plan Width": 10,
        },
        "Execution Time": 50.0,  # ms
    }
    
    # Mock the result of session.execute
    mock_result = AsyncMock()
    mock_result.scalar = AsyncMock(return_value=json.dumps([plan_data]))
    session.execute = AsyncMock(return_value=mock_result)
    
    # Create optimizer with mock session
    optimizer = QueryOptimizer(session=session)
    
    # Call analyze_query
    query = "SELECT * FROM users"
    plan = await optimizer.analyze_query(query)
    
    # Verify session.execute was called with EXPLAIN
    session.execute.assert_awaited_once()
    args, kwargs = session.execute.await_args
    assert "EXPLAIN" in args[0].text
    assert "FORMAT JSON" in args[0].text
    
    # Verify plan details
    assert plan.plan_type == "Seq Scan"
    assert plan.estimated_cost == 100.0
    assert plan.estimated_rows == 1000
    assert plan.execution_time == 0.05  # 50ms -> 0.05s
    
    # Test with SQLAlchemy executable
    session.execute.reset_mock()
    mock_result.scalar.reset_mock()
    
    query = select(text("*")).select_from(text("users"))
    plan = await optimizer.analyze_query(query)
    
    # Verify session.execute was called with EXPLAIN
    session.execute.assert_awaited_once()

    # Test with engine instead of session
    session.execute.reset_mock()
    mock_result.scalar.reset_mock()
    
    # Create mock engine and connection
    engine = AsyncMock(spec=AsyncEngine)
    connection = AsyncMock(spec=AsyncConnection)
    connection.execute = AsyncMock(return_value=mock_result)
    engine.connect.return_value.__aenter__.return_value = connection
    
    # Create optimizer with mock engine
    optimizer = QueryOptimizer(engine=engine)
    
    # Call analyze_query
    query = "SELECT * FROM users"
    plan = await optimizer.analyze_query(query)
    
    # Verify connection.execute was called with EXPLAIN
    connection.execute.assert_awaited_once()
    
    # Test error handling
    connection.execute.side_effect = Exception("Test error")
    plan = await optimizer.analyze_query(query)
    
    # Should return a default plan
    assert plan.plan_type == "Unknown"
    assert plan.estimated_cost == 0.0
    assert plan.estimated_rows == 0
    

# Test _extract methods
def test_extract_methods():
    """Test the _extract_* methods."""
    # Create an optimizer
    optimizer = QueryOptimizer()
    
    # Test _extract_operations
    plan_node = {
        "Node Type": "Seq Scan",
        "Relation Name": "users",
        "Total Cost": 100.0,
        "Plan Rows": 1000,
        "Plan Width": 10,
        "Plans": [
            {
                "Node Type": "Sort",
                "Total Cost": 200.0,
                "Plan Rows": 1000,
                "Plan Width": 10,
            }
        ]
    }
    
    operations = optimizer._extract_operations(plan_node)
    assert len(operations) == 2
    assert operations[0]["type"] == "Seq Scan"
    assert operations[1]["type"] == "Sort"
    
    # Test _extract_table_scans
    scans = optimizer._extract_table_scans(plan_node)
    assert len(scans) == 1
    assert scans[0] == "users"
    
    # Test _extract_index_usage
    plan_node = {
        "Node Type": "Index Scan",
        "Relation Name": "users",
        "Index Name": "users_pkey",
        "Plans": [
            {
                "Node Type": "Index Only Scan",
                "Relation Name": "posts",
                "Index Name": "posts_user_id_idx",
            }
        ]
    }
    
    index_usage = optimizer._extract_index_usage(plan_node)
    assert len(index_usage) == 2
    assert index_usage["users"] == "users_pkey"
    assert index_usage["posts"] == "posts_user_id_idx"
    
    # Test _extract_join_types
    plan_node = {
        "Node Type": "Nested Loop",
        "Plans": [
            {
                "Node Type": "Hash Join",
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                    }
                ]
            }
        ]
    }
    
    join_types = optimizer._extract_join_types(plan_node)
    assert len(join_types) == 2
    assert "Nested Loop" in join_types
    assert "Hash Join" in join_types


# Test recommend_indexes
@pytest.mark.asyncio
async def test_recommend_indexes():
    """Test recommend_indexes method."""
    # Create an optimizer
    optimizer = QueryOptimizer()
    
    # Add table info
    optimizer._table_info = {
        "users": {
            "schema": "public",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "email", "type": "varchar"},
                {"name": "status", "type": "varchar"},
            ]
        }
    }
    
    # Add existing indexes
    optimizer._existing_indexes = {
        "users": [
            {
                "name": "users_pkey",
                "columns": ["id"],
                "unique": True,
                "type": "btree",
            }
        ]
    }
    
    # Create a query plan with sequential scans
    plan = QueryPlan(
        plan_type="Select",
        estimated_cost=100.0,
        estimated_rows=1000,
        operations=[
            {"type": "Seq Scan", "cost": 100.0, "rows": 1000, "width": 10},
        ],
        table_scans=["users"],
        join_types=[],
    )
    
    # Call recommend_indexes
    recommendations = optimizer.recommend_indexes(plan)
    
    # Should recommend an index on users
    assert len(recommendations) > 0
    assert recommendations[0].table_name == "users"
    assert len(recommendations[0].column_names) > 0
    
    # Test with existing index
    optimizer._existing_indexes["users"].append({
        "name": "users_status_idx",
        "columns": ["status"],
        "unique": False,
        "type": "btree",
    })
    
    # Use monkeypatch to make _extract_filter_columns return 'status'
    optimizer._extract_filter_columns = lambda table, ops: ["status"]
    
    # Call recommend_indexes
    recommendations = optimizer.recommend_indexes(plan)
    
    # Should not recommend index since it exists
    assert len(recommendations) == 0
    
    # Test with recommendation disabled
    optimizer.config.recommend_indexes = False
    recommendations = optimizer.recommend_indexes(plan)
    assert len(recommendations) == 0


# Test rewrite_query
@pytest.mark.asyncio
async def test_rewrite_query():
    """Test rewrite_query method."""
    # Create an optimizer
    optimizer = QueryOptimizer()
    
    # Test with rewrite_queries disabled
    optimizer.config.rewrite_queries = False
    result = await optimizer.rewrite_query("SELECT * FROM users")
    assert result.is_err()
    
    # Enable rewrite_queries
    optimizer.config.rewrite_queries = True
    
    # Test rewrite_unnecessary_distinct
    result = await optimizer.rewrite_query("SELECT DISTINCT id, name FROM users")
    assert result.is_ok()
    rewrite = result.unwrap()
    assert rewrite.rewrite_type == "remove_unnecessary_distinct"
    assert rewrite.rewritten_query == "SELECT id, name FROM users"
    
    # Test rewrite_count_star
    result = await optimizer.rewrite_query("SELECT COUNT(*) FROM users")
    assert result.is_ok()
    rewrite = result.unwrap()
    assert rewrite.rewrite_type == "optimize_count"
    assert rewrite.rewritten_query == "SELECT COUNT(1) FROM users"
    
    # Test rewrite_or_to_union (requires AGGRESSIVE mode)
    optimizer.config.optimization_level = OptimizationLevel.AGGRESSIVE
    result = await optimizer.rewrite_query("SELECT * FROM users WHERE email = 'test@example.com' OR status = 'active'")
    assert result.is_ok()
    rewrite = result.unwrap()
    assert rewrite.rewrite_type == "or_to_union"
    assert "UNION ALL" in rewrite.rewritten_query
    
    # Test rewrite_in_clause (large IN)
    values = ", ".join([f"'{i}'" for i in range(150)])
    query = f"SELECT * FROM users WHERE id IN ({values})"
    result = await optimizer.rewrite_query(query)
    assert result.is_ok()
    rewrite = result.unwrap()
    assert rewrite.rewrite_type == "optimize_large_in"
    assert "WITH temp_in_values" in rewrite.rewritten_query
    
    # Test no applicable rewrites
    result = await optimizer.rewrite_query("SELECT * FROM users LIMIT 10")
    assert result.is_err()


# Test execute_optimized_query
@pytest.mark.asyncio
async def test_execute_optimized_query():
    """Test execute_optimized_query method."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.__iter__ = lambda self: iter([1, 2, 3])
    session.execute = AsyncMock(return_value=mock_result)
    
    # Create optimizer with mock session
    optimizer = QueryOptimizer(session=session)
    
    # Add a query rewrite
    query = "SELECT * FROM users"
    query_hash = optimizer._hash_query(query)
    optimizer._query_rewrites[query_hash] = QueryRewrite(
        original_query=query,
        rewritten_query="SELECT * FROM users LIMIT 100",
        rewrite_type="add_limit",
    )
    
    # Call execute_optimized_query
    result = await optimizer.execute_optimized_query(query)
    
    # Verify session.execute was called with rewritten query
    session.execute.assert_awaited_once()
    args, kwargs = session.execute.await_args
    assert "LIMIT 100" in args[0].text
    
    # Verify result
    assert list(result) == [1, 2, 3]
    
    # Test with optimizer disabled
    session.execute.reset_mock()
    optimizer.config.enabled = False
    
    await optimizer.execute_optimized_query(query)
    
    # Should have called with original query
    session.execute.assert_awaited_once()
    
    # Test slow query
    session.execute.reset_mock()
    optimizer.config.enabled = True
    optimizer.config.collect_statistics = True
    optimizer.config.slow_query_threshold = 0.0  # Always consider slow
    
    # Mock time.time to simulate query taking time
    with patch('time.time', side_effect=[0.0, 1.0]):
        await optimizer.execute_optimized_query(query)
    
    # Should record stats and analyze
    assert query_hash in optimizer._query_stats
    assert optimizer._query_stats[query_hash].execution_count == 1
    
    # Test with missing session
    optimizer = QueryOptimizer()
    with pytest.raises(ValueError):
        await optimizer.execute_optimized_query(query)


# Test load_schema_information
@pytest.mark.asyncio
async def test_load_schema_information():
    """Test load_schema_information method."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Setup mock responses
    tables_result = AsyncMock()
    tables_result.__iter__ = lambda self: iter([
        MagicMock(table_name="users", table_schema="public")
    ])
    
    columns_result = AsyncMock()
    columns_result.__iter__ = lambda self: iter([
        MagicMock(
            table_name="users",
            column_name="id",
            data_type="integer",
            is_nullable="NO",
            column_default="nextval('users_id_seq')"
        ),
        MagicMock(
            table_name="users",
            column_name="email",
            data_type="varchar",
            is_nullable="NO",
            column_default=None
        )
    ])
    
    indexes_result = AsyncMock()
    indexes_result.__iter__ = lambda self: iter([
        MagicMock(
            table_name="users",
            index_name="users_pkey",
            column_name="id",
            is_unique=True,
            index_type="btree"
        )
    ])
    
    # Setup session.execute to return different results
    execute_results = {
        "information_schema.tables": tables_result,
        "information_schema.columns": columns_result,
        "pg_index": indexes_result,
    }
    
    def mock_execute(query, *args, **kwargs):
        for key, result in execute_results.items():
            if key in query.text:
                return result
        return AsyncMock()
    
    session.execute = AsyncMock(side_effect=mock_execute)
    
    # Create optimizer with mock session
    optimizer = QueryOptimizer(session=session)
    
    # Call load_schema_information
    await optimizer.load_schema_information()
    
    # Verify session.execute was called 3 times
    assert session.execute.await_count == 3
    
    # Verify schema information was loaded
    assert "users" in optimizer._table_info
    assert len(optimizer._table_info["users"]["columns"]) == 2
    assert "users" in optimizer._existing_indexes
    assert len(optimizer._existing_indexes["users"]) == 1
    
    # Test with engine instead of session
    session.execute.reset_mock()
    
    # Create mock engine and connection
    engine = AsyncMock(spec=AsyncEngine)
    connection = AsyncMock(spec=AsyncConnection)
    connection.execute = AsyncMock(side_effect=mock_execute)
    engine.connect.return_value.__aenter__.return_value = connection
    
    # Create optimizer with mock engine
    optimizer = QueryOptimizer(engine=engine)
    
    # Call load_schema_information
    await optimizer.load_schema_information()
    
    # Verify connection.execute was called 3 times
    assert connection.execute.await_count == 3
    
    # Test error handling
    connection.execute.side_effect = Exception("Test error")
    
    # Should not raise exception
    await optimizer.load_schema_information()
    
    # Test with missing session and engine
    optimizer = QueryOptimizer()
    with pytest.raises(ValueError):
        await optimizer.load_schema_information()


# Test statistics and recommendations methods
def test_statistics_methods():
    """Test methods for retrieving statistics and recommendations."""
    # Create optimizer
    optimizer = QueryOptimizer()
    
    # Add some query statistics
    query1 = "SELECT * FROM users"
    query_hash1 = optimizer._hash_query(query1)
    stats1 = QueryStatistics(
        query_hash=query_hash1,
        query_text=query1,
    )
    stats1.execution_count = 10
    stats1.total_execution_time = 5.0
    
    query2 = "SELECT COUNT(*) FROM users"
    query_hash2 = optimizer._hash_query(query2)
    stats2 = QueryStatistics(
        query_hash=query_hash2,
        query_text=query2,
    )
    stats2.execution_count = 5
    stats2.total_execution_time = 0.5
    
    optimizer._query_stats[query_hash1] = stats1
    optimizer._query_stats[query_hash2] = stats2
    
    # Add some index recommendations
    optimizer._index_recommendations = [
        IndexRecommendation(
            table_name="users",
            column_names=["email"],
        ),
        IndexRecommendation(
            table_name="posts",
            column_names=["user_id"],
        )
    ]
    
    # Test get_statistics
    stats = optimizer.get_statistics()
    assert len(stats) == 2
    assert query_hash1 in stats
    assert query_hash2 in stats
    
    # Test get_slow_queries
    slow_queries = optimizer.get_slow_queries(0.4)
    assert len(slow_queries) == 1
    assert slow_queries[0].query_hash == query_hash1
    
    # Test get_frequent_queries
    # Note: frequency depends on timing, so we test the function call only
    frequent_queries = optimizer.get_frequent_queries(0)
    assert len(frequent_queries) > 0
    
    # Test get_index_recommendations
    recommendations = optimizer.get_index_recommendations()
    assert len(recommendations) == 2
    assert recommendations[0].table_name == "users"
    assert recommendations[1].table_name == "posts"


# Test implement_index
@pytest.mark.asyncio
async def test_implement_index():
    """Test implement_index method."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    
    # Create optimizer with auto_implement_indexes enabled
    config = OptimizationConfig(auto_implement_indexes=True)
    optimizer = QueryOptimizer(session=session, config=config)
    
    # Add table info and existing indexes
    optimizer._table_info = {"users": {"schema": "public"}}
    optimizer._existing_indexes = {"users": []}
    
    # Create recommendation
    rec = IndexRecommendation(
        table_name="users",
        column_names=["email"],
    )
    
    # Call implement_index
    success = await optimizer.implement_index(rec)
    
    # Verify success and session calls
    assert success is True
    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()
    
    # Verify recommendation updated
    assert rec.implemented is True
    assert rec.implementation_time is not None
    
    # Verify existing indexes updated
    assert len(optimizer._existing_indexes["users"]) == 1
    
    # Test with engine instead of session
    session.execute.reset_mock()
    session.commit.reset_mock()
    
    # Create mock engine and connection
    engine = AsyncMock(spec=AsyncEngine)
    connection = AsyncMock(spec=AsyncConnection)
    connection.execute = AsyncMock()
    connection.commit = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = connection
    
    # Create optimizer with mock engine
    optimizer = QueryOptimizer(engine=engine, config=config)
    optimizer._table_info = {"users": {"schema": "public"}}
    optimizer._existing_indexes = {"users": []}
    
    # Call implement_index
    success = await optimizer.implement_index(rec)
    
    # Verify success and connection calls
    assert success is True
    connection.execute.assert_awaited_once()
    connection.commit.assert_awaited_once()
    
    # Test with auto_implement_indexes disabled
    optimizer.config.auto_implement_indexes = False
    with pytest.raises(ValueError):
        await optimizer.implement_index(rec)
    
    # Test with missing session and engine
    optimizer = QueryOptimizer(config=config)
    with pytest.raises(ValueError):
        await optimizer.implement_index(rec)
    
    # Test error handling
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(side_effect=Exception("Test error"))
    optimizer = QueryOptimizer(session=session, config=config)
    optimizer._table_info = {"users": {"schema": "public"}}
    optimizer._existing_indexes = {"users": []}
    
    success = await optimizer.implement_index(rec)
    assert success is False


# Test optimize_query helper function
@pytest.mark.asyncio
async def test_optimize_query_helper():
    """Test optimize_query helper function."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Setup mock responses for analyze_query and rewrite_query
    plan_data = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "users",
            "Total Cost": 100.0,
            "Plan Rows": 1000,
        },
        "Execution Time": 50.0,
    }
    
    mock_result = AsyncMock()
    mock_result.scalar = AsyncMock(return_value=json.dumps([plan_data]))
    session.execute = AsyncMock(return_value=mock_result)
    
    # Mock rewrite_query to always succeed
    with patch("uno.database.query_optimizer.QueryOptimizer.rewrite_query") as mock_rewrite:
        mock_rewrite.return_value = Ok(QueryRewrite(
            original_query="SELECT * FROM users",
            rewritten_query="SELECT * FROM users LIMIT 100",
            rewrite_type="add_limit",
        ))
        
        # Call optimize_query
        query = "SELECT * FROM users"
        optimized, recommendations = await optimize_query(
            query=query,
            session=session,
        )
        
        # Verify optimized query
        assert optimized == "SELECT * FROM users LIMIT 100"
        
        # Mock rewrite_query to fail
        mock_rewrite.return_value = Err("No applicable rewrites")
        
        # Call optimize_query
        optimized, recommendations = await optimize_query(
            query=query,
            session=session,
        )
        
        # Should return original query
        assert optimized == query


# Test optimized_query decorator
@pytest.mark.asyncio
async def test_optimized_query_decorator():
    """Test optimized_query decorator."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Create a function to decorate
    @optimized_query()
    async def get_users(session):
        return await session.execute("SELECT * FROM users")
    
    # Call the decorated function
    result = await get_users(session)
    
    # Verify session.execute was called
    session.execute.assert_awaited_once()