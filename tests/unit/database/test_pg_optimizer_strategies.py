"""
Tests for the PostgreSQL-specific query optimizer strategies.

These tests verify the functionality of the PostgreSQL-specific optimization strategies.
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
)
from uno.database.pg_optimizer_strategies import (
    PgIndexRecommendation,
    PgOptimizationStrategies,
    PgQueryOptimizer,
    add_pg_strategies,
    create_pg_optimizer,
)
from uno.core.errors.result import Result, Ok, Err


# Test PgIndexRecommendation
def test_pg_index_recommendation():
    """Test PgIndexRecommendation class."""
    # Create a basic index recommendation
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
    )
    
    # Test default properties
    assert rec.include_columns == []
    assert rec.is_unique is False
    assert rec.is_partial is False
    assert rec.where_clause is None
    assert rec.operator_class is None
    assert rec.index_tablespace is None
    
    # Test basic creation SQL (should be same as base class)
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email ON users (email)"
    
    # Test with include columns (covering index)
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
        include_columns=["name", "status"],
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email ON users (email) INCLUDE (name, status)"
    
    # Test with unique constraint
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
        is_unique=True,
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE UNIQUE INDEX idx_users_email ON users (email)"
    
    # Test with partial index
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
        is_partial=True,
        where_clause="status = 'active'",
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email ON users (email) WHERE status = 'active'"
    
    # Test with operator class
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
        operator_class="text_pattern_ops",
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email ON users (email text_pattern_ops)"
    
    # Test with tablespace
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
        index_tablespace="fast_ssd",
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE INDEX idx_users_email ON users (email) TABLESPACE fast_ssd"
    
    # Test with multiple features combined
    rec = PgIndexRecommendation(
        table_name="users",
        column_names=["email"],
        include_columns=["name"],
        is_unique=True,
        is_partial=True,
        where_clause="status = 'active'",
        index_type=IndexType.GIN,
    )
    sql = rec.get_creation_sql()
    assert sql == "CREATE UNIQUE INDEX idx_users_email ON users USING gin (email) INCLUDE (name) WHERE status = 'active'"


# Test PgOptimizationStrategies initialization
def test_pg_optimization_strategies_init():
    """Test PgOptimizationStrategies initialization."""
    # Create a mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.logger = MagicMock()
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Verify initialization
    assert strategies.optimizer is optimizer
    assert strategies.logger is optimizer.logger


# Test add_pg_strategies helper
def test_add_pg_strategies():
    """Test add_pg_strategies helper function."""
    # Create a mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.logger = MagicMock()
    
    # Add strategies
    strategies = add_pg_strategies(optimizer)
    
    # Verify
    assert isinstance(strategies, PgOptimizationStrategies)
    assert strategies.optimizer is optimizer


# Test create_pg_optimizer helper
def test_create_pg_optimizer():
    """Test create_pg_optimizer helper function."""
    # Create a PostgreSQL optimizer
    optimizer = create_pg_optimizer()
    
    # Verify
    assert isinstance(optimizer, PgQueryOptimizer)
    assert isinstance(optimizer.pg_strategies, PgOptimizationStrategies)


# Test analyze_table
@pytest.mark.asyncio
async def test_analyze_table():
    """Test analyze_table method."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.session = session
    optimizer.engine = None
    optimizer.logger = MagicMock()
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Test analyze_table
    result = await strategies.analyze_table("users")
    
    # Verify SQL execution
    session.execute.assert_awaited_once()
    args, kwargs = session.execute.await_args
    assert "ANALYZE users" in args[0].text
    
    # Verify result
    assert result.is_ok()
    assert "message" in result.unwrap()
    
    # Test with engine instead of session
    session.execute.reset_mock()
    session.commit.reset_mock()
    
    # Create mock engine and connection
    engine = AsyncMock(spec=AsyncEngine)
    connection = AsyncMock(spec=AsyncConnection)
    connection.execute = AsyncMock()
    connection.commit = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = connection
    
    # Update optimizer
    optimizer.session = None
    optimizer.engine = engine
    
    # Test analyze_table
    result = await strategies.analyze_table("users")
    
    # Verify SQL execution
    connection.execute.assert_awaited_once()
    args, kwargs = connection.execute.await_args
    assert "ANALYZE users" in args[0].text
    
    # Test error handling
    connection.execute.side_effect = Exception("Test error")
    result = await strategies.analyze_table("users")
    
    # Verify error handling
    assert result.is_err()
    assert "Error analyzing table" in result.unwrap_err()
    
    # Test with missing session and engine
    optimizer.session = None
    optimizer.engine = None
    result = await strategies.analyze_table("users")
    
    # Verify error
    assert result.is_err()
    assert "Either session or engine must be provided" in result.unwrap_err()


# Test get_table_statistics
@pytest.mark.asyncio
async def test_get_table_statistics():
    """Test get_table_statistics method."""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.session = session
    optimizer.engine = None
    optimizer.logger = MagicMock()
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Mock the query results
    table_stats = AsyncMock()
    table_stats.mappings().first.return_value = {
        "table_name": "users",
        "row_estimate": 1000,
        "page_count": 10,
        "total_bytes": 102400,
        "table_bytes": 81920,
        "index_bytes": 20480,
        "seq_scan_count": 5,
        "seq_scan_rows": 5000,
        "seq_scan_rows_fetched": 4500,
    }
    
    col_stats = AsyncMock()
    col_stats.mappings.return_value = [
        {
            "column_name": "id",
            "distinct_values": -1,
            "null_fraction": 0,
            "common_values": None,
            "common_freqs": None,
            "correlation": 1.0,
        },
        {
            "column_name": "email",
            "distinct_values": 1000,
            "null_fraction": 0,
            "common_values": None,
            "common_freqs": None,
            "correlation": 0.1,
        }
    ]
    
    # Setup session.execute to return different results for different queries
    def mock_execute(query, *args, **kwargs):
        if "pg_class.relname" in query.text:
            return table_stats
        elif "pg_stats" in query.text:
            return col_stats
        return AsyncMock()
    
    session.execute = AsyncMock(side_effect=mock_execute)
    
    # Test get_table_statistics
    result = await strategies.get_table_statistics("users")
    
    # Verify
    assert result.is_ok()
    stats = result.unwrap()
    assert stats["table_name"] == "users"
    assert stats["row_estimate"] == 1000
    assert "columns" in stats
    assert len(stats["columns"]) == 2
    assert "avg_row_size" in stats
    assert "total_bytes_human" in stats
    
    # Test table not found
    table_stats.mappings().first.return_value = None
    result = await strategies.get_table_statistics("nonexistent")
    
    # Verify error
    assert result.is_err()
    assert "not found" in result.unwrap_err()
    
    # Test error handling
    session.execute.side_effect = Exception("Test error")
    result = await strategies.get_table_statistics("users")
    
    # Verify error handling
    assert result.is_err()
    assert "Error getting statistics" in result.unwrap_err()


# Test recommend_table_maintenance
@pytest.mark.asyncio
async def test_recommend_table_maintenance():
    """Test recommend_table_maintenance method."""
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.logger = MagicMock()
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Mock get_table_statistics
    stats_result = Ok({
        "table_name": "users",
        "row_estimate": 1000,
        "page_count": 10,
        "total_bytes": 102400,
        "table_bytes": 81920,
        "index_bytes": 102400,  # Larger than table_bytes
        "seq_scan_count": 20,   # High scan count
        "seq_scan_rows": 5000,
        "seq_scan_rows_fetched": 4500,
        "avg_row_size": 40,
        "columns": [
            {
                "column_name": "id",
                "correlation": 1.0,
            },
            {
                "column_name": "email",
                "correlation": 0.1,  # Low correlation
            }
        ]
    })
    strategies.get_table_statistics = AsyncMock(return_value=stats_result)
    
    # Test recommend_table_maintenance
    result = await strategies.recommend_table_maintenance("users")
    
    # Verify
    assert result.is_ok()
    recommendations = result.unwrap()
    assert "table_name" in recommendations
    assert "statistics" in recommendations
    assert "recommendations" in recommendations
    assert len(recommendations["recommendations"]) > 0
    
    # Check that we have multiple types of recommendations
    rec_types = [rec["type"] for rec in recommendations["recommendations"]]
    assert "ANALYZE" in rec_types
    assert "REVIEW_INDEXES" in rec_types
    assert "CLUSTER" in rec_types
    
    # Test error handling
    strategies.get_table_statistics = AsyncMock(return_value=Err("Stats error"))
    result = await strategies.recommend_table_maintenance("users")
    
    # Verify error is passed through
    assert result.is_err()
    assert "Stats error" in result.unwrap_err()


# Test recommend_covering_index
def test_recommend_covering_index():
    """Test recommend_covering_index method."""
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer._table_info = {
        "users": {
            "schema": "public",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "email", "type": "varchar"},
                {"name": "name", "type": "varchar"},
                {"name": "status", "type": "varchar"},
            ]
        }
    }
    optimizer._extract_filter_columns = MagicMock(return_value=["status"])
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Mock _extract_output_columns
    strategies._extract_output_columns = MagicMock(return_value=["name", "email"])
    
    # Create a query plan
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
    
    # Test recommend_covering_index
    query = "SELECT name, email FROM users WHERE status = 'active'"
    recommendations = strategies.recommend_covering_index(plan, query)
    
    # Verify
    assert len(recommendations) == 1
    rec = recommendations[0]
    assert isinstance(rec, PgIndexRecommendation)
    assert rec.table_name == "users"
    assert rec.column_names == ["status"]
    assert rec.include_columns == ["name", "email"]
    
    # Check the SQL
    sql = rec.get_creation_sql()
    assert "INCLUDE (name, email)" in sql
    
    # Test with no sequential scans
    plan.table_scans = []
    recommendations = strategies.recommend_covering_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0
    
    # Test with no filter columns
    plan.table_scans = ["users"]
    optimizer._extract_filter_columns = MagicMock(return_value=[])
    recommendations = strategies.recommend_covering_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0
    
    # Test with no output columns
    optimizer._extract_filter_columns = MagicMock(return_value=["status"])
    strategies._extract_output_columns = MagicMock(return_value=[])
    recommendations = strategies.recommend_covering_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0


# Test recommend_partial_index
def test_recommend_partial_index():
    """Test recommend_partial_index method."""
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
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
    optimizer._extract_filter_columns = MagicMock(return_value=["email"])
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Mock extract methods
    strategies._extract_where_clauses = MagicMock(return_value=[
        "users.status = 'active'",
        "users.email LIKE '%example.com'"
    ])
    strategies._extract_partial_index_condition = MagicMock(return_value="status = 'active'")
    
    # Create a query plan
    plan = QueryPlan(
        plan_type="Select",
        estimated_cost=100.0,
        estimated_rows=1000,
        operations=[],
        table_scans=["users"],
        join_types=[],
    )
    
    # Test recommend_partial_index
    query = "SELECT * FROM users WHERE status = 'active' AND email LIKE '%example.com'"
    recommendations = strategies.recommend_partial_index(plan, query)
    
    # Verify
    assert len(recommendations) == 1
    rec = recommendations[0]
    assert isinstance(rec, PgIndexRecommendation)
    assert rec.table_name == "users"
    assert rec.column_names == ["email"]
    assert rec.is_partial is True
    assert rec.where_clause == "status = 'active'"
    
    # Check the SQL
    sql = rec.get_creation_sql()
    assert "WHERE status = 'active'" in sql
    
    # Test with no where clauses
    strategies._extract_where_clauses = MagicMock(return_value=[])
    recommendations = strategies.recommend_partial_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0
    
    # Test with no suitable partial index condition
    strategies._extract_where_clauses = MagicMock(return_value=["email LIKE '%example.com'"])
    strategies._extract_partial_index_condition = MagicMock(return_value=None)
    recommendations = strategies.recommend_partial_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0


# Test recommend_expression_index
def test_recommend_expression_index():
    """Test recommend_expression_index method."""
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer._table_info = {
        "users": {
            "schema": "public",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "email", "type": "varchar"},
                {"name": "name", "type": "varchar"},
            ]
        }
    }
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Mock _extract_expressions
    strategies._extract_expressions = MagicMock(return_value=[
        {
            "table": "users",
            "expression": "LOWER(email)",
            "columns": ["email"],
            "type": "function"
        }
    ])
    
    # Create a query plan
    plan = QueryPlan(
        plan_type="Select",
        estimated_cost=100.0,
        estimated_rows=1000,
        operations=[],
        table_scans=["users"],
        join_types=[],
    )
    
    # Test recommend_expression_index
    query = "SELECT * FROM users WHERE LOWER(email) = 'test@example.com'"
    recommendations = strategies.recommend_expression_index(plan, query)
    
    # Verify
    assert len(recommendations) == 1
    rec = recommendations[0]
    assert isinstance(rec, PgIndexRecommendation)
    assert rec.table_name == "users"
    assert rec.column_names == ["LOWER(email)"]
    
    # Check the SQL
    sql = rec.get_creation_sql()
    assert "LOWER(email)" in sql
    
    # Test with no expressions
    strategies._extract_expressions = MagicMock(return_value=[])
    recommendations = strategies.recommend_expression_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0
    
    # Test with expression for table not in sequential scans
    strategies._extract_expressions = MagicMock(return_value=[
        {
            "table": "orders",
            "expression": "EXTRACT(YEAR FROM created_at)",
            "columns": ["created_at"],
            "type": "date_extract"
        }
    ])
    recommendations = strategies.recommend_expression_index(plan, query)
    
    # Verify no recommendations
    assert len(recommendations) == 0


# Test rewrite_for_pg_features
@pytest.mark.asyncio
async def test_rewrite_for_pg_features():
    """Test rewrite_for_pg_features method."""
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.logger = MagicMock()
    
    # Create strategies
    strategies = PgOptimizationStrategies(optimizer)
    
    # Test CTE rewrite
    query = """
    SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count
    FROM users u
    WHERE (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 0
    """
    
    result = await strategies.rewrite_for_pg_features(query)
    
    # Verify
    assert result.is_ok()
    rewrite = result.unwrap()
    assert "WITH" in rewrite.rewritten_query
    assert rewrite.rewrite_type == "cte_optimization"
    
    # Test LATERAL JOIN rewrite
    query = """
    SELECT u.name, o.count
    FROM users u
    JOIN (SELECT user_id, COUNT(*) as count FROM orders WHERE users.id = orders.user_id) AS o ON u.id = o.user_id
    """
    
    # Mock _rewrite_cte to return error so we hit the next rewrite
    strategies._rewrite_cte = AsyncMock(return_value=Err("No CTE rewrite"))
    
    result = await strategies.rewrite_for_pg_features(query)
    
    # Verify
    assert result.is_ok()
    rewrite = result.unwrap()
    assert "LATERAL" in rewrite.rewritten_query
    assert rewrite.rewrite_type == "lateral_join_optimization"
    
    # Test JSON functions rewrite
    query = """
    SELECT id, JSON_EXTRACT(data, '$.name') as name, JSON_EXTRACT_SCALAR(data, '$.email') as email
    FROM users
    """
    
    # Mock previous rewrites to return error
    strategies._rewrite_cte = AsyncMock(return_value=Err("No CTE rewrite"))
    strategies._rewrite_to_lateral = AsyncMock(return_value=Err("No LATERAL rewrite"))
    
    result = await strategies.rewrite_for_pg_features(query)
    
    # Verify
    assert result.is_ok()
    rewrite = result.unwrap()
    assert "data -> 'name'" in rewrite.rewritten_query
    assert "data ->> 'email'" in rewrite.rewritten_query
    assert rewrite.rewrite_type == "json_function_optimization"
    
    # Test DISTINCT ON rewrite
    query = """
    SELECT user_id, MIN(created_at) as first_order_date
    FROM orders
    GROUP BY user_id
    ORDER BY user_id, created_at ASC
    """
    
    # Mock previous rewrites to return error
    strategies._rewrite_cte = AsyncMock(return_value=Err("No CTE rewrite"))
    strategies._rewrite_to_lateral = AsyncMock(return_value=Err("No LATERAL rewrite"))
    strategies._rewrite_json_functions = AsyncMock(return_value=Err("No JSON rewrite"))
    
    result = await strategies.rewrite_for_pg_features(query)
    
    # Verify
    assert result.is_ok()
    rewrite = result.unwrap()
    assert "DISTINCT ON" in rewrite.rewritten_query
    assert rewrite.rewrite_type == "distinct_on_optimization"
    
    # Test no applicable rewrites
    query = "SELECT * FROM users LIMIT 10"
    
    # Mock all rewrites to return error
    strategies._rewrite_cte = AsyncMock(return_value=Err("No CTE rewrite"))
    strategies._rewrite_to_lateral = AsyncMock(return_value=Err("No LATERAL rewrite"))
    strategies._rewrite_json_functions = AsyncMock(return_value=Err("No JSON rewrite"))
    strategies._rewrite_to_distinct_on = AsyncMock(return_value=Err("No DISTINCT ON rewrite"))
    
    result = await strategies.rewrite_for_pg_features(query)
    
    # Verify
    assert result.is_err()
    assert "No PostgreSQL-specific rewrites applicable" in result.unwrap_err()


# Test PgQueryOptimizer
@pytest.mark.asyncio
async def test_pg_query_optimizer():
    """Test PgQueryOptimizer class."""
    # Create a PostgreSQL query optimizer
    session = AsyncMock(spec=AsyncSession)
    optimizer = PgQueryOptimizer(session=session)
    
    # Verify initialization
    assert isinstance(optimizer.pg_strategies, PgOptimizationStrategies)
    
    # Test analyze_query (should call parent method)
    with patch.object(QueryOptimizer, 'analyze_query', return_value=MagicMock()) as mock_analyze:
        await optimizer.analyze_query("SELECT * FROM users")
        mock_analyze.assert_awaited_once()
    
    # Test recommend_indexes with query_text
    with patch.object(QueryOptimizer, 'recommend_indexes', return_value=[]) as mock_recommend:
        with patch.object(optimizer.pg_strategies, 'recommend_covering_index', return_value=[]) as mock_covering:
            with patch.object(optimizer.pg_strategies, 'recommend_partial_index', return_value=[]) as mock_partial:
                with patch.object(optimizer.pg_strategies, 'recommend_expression_index', return_value=[]) as mock_expression:
                    query_plan = MagicMock(spec=QueryPlan)
                    query_text = "SELECT * FROM users"
                    
                    await optimizer.recommend_indexes(query_plan, query_text)
                    
                    mock_recommend.assert_awaited_once()
                    mock_covering.assert_called_once()
                    mock_partial.assert_called_once()
                    mock_expression.assert_called_once()
    
    # Test rewrite_query
    with patch.object(QueryOptimizer, 'rewrite_query', return_value=Err("No standard rewrite")) as mock_rewrite:
        with patch.object(optimizer.pg_strategies, 'rewrite_for_pg_features', return_value=Ok(MagicMock())) as mock_pg_rewrite:
            result = await optimizer.rewrite_query("SELECT * FROM users")
            
            mock_rewrite.assert_awaited_once()
            mock_pg_rewrite.assert_awaited_once()
            assert result.is_ok()
    
    # Test analyze_tables
    with patch.object(optimizer.pg_strategies, 'analyze_table', side_effect=[Ok({}), Ok({})]) as mock_analyze:
        result = await optimizer.analyze_tables(["users", "orders"])
        
        assert mock_analyze.await_count == 2
        assert "users" in result
        assert "orders" in result
    
    # Test get_maintenance_recommendations
    with patch.object(optimizer.pg_strategies, 'recommend_table_maintenance',
                     side_effect=[Ok({"recommendations": []}), Err("Error")]) as mock_recommend:
        result = await optimizer.get_maintenance_recommendations(["users", "orders"])
        
        assert mock_recommend.await_count == 2
        assert "users" in result
        assert "orders" in result
        assert "recommendations" in result["users"]
        assert "error" in result["orders"]