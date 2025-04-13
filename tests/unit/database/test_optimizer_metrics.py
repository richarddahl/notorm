"""
Tests for the query optimizer metrics module.

These tests verify the functionality of the query optimizer metrics collection system.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
import json

from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    QueryPlan,
    QueryStatistics,
    OptimizationConfig,
    QueryOptimizer,
)
from uno.database.optimizer_metrics import (
    MetricSource,
    OptimizerMetricsSnapshot,
    OptimizerMetricsCollector,
    OptimizerMetricsMiddleware,
    track_query_performance,
    with_query_metrics,
    get_metrics_collector,
    set_metrics_collector,
    collect_optimizer_metrics,
)
from uno.core.monitoring.metrics import MetricsManager, MetricType


# Test OptimizerMetricsSnapshot
def test_optimizer_metrics_snapshot():
    """Test OptimizerMetricsSnapshot class."""
    # Create a basic snapshot
    snapshot = OptimizerMetricsSnapshot()
    
    # Test default properties
    assert snapshot.query_count == 0
    assert snapshot.slow_query_count == 0
    assert snapshot.avg_execution_time == 0.0
    assert snapshot.p95_execution_time == 0.0
    assert isinstance(snapshot.timestamp, float)
    assert snapshot.timestamp > 0
    
    # Test from_optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    
    # Mock query statistics
    stats1 = MagicMock(spec=QueryStatistics)
    stats1.avg_execution_time = 0.1
    stats1.latest_plan = MagicMock(spec=QueryPlan)
    stats1.latest_plan.complexity = QueryComplexity.SIMPLE
    
    stats2 = MagicMock(spec=QueryStatistics)
    stats2.avg_execution_time = 0.5
    stats2.latest_plan = MagicMock(spec=QueryPlan)
    stats2.latest_plan.complexity = QueryComplexity.COMPLEX
    
    optimizer.get_statistics.return_value = {
        "query1": stats1,
        "query2": stats2,
    }
    
    # Mock slow queries
    optimizer.get_slow_queries.side_effect = [
        [stats2],  # First call returns 1 slow query
        []         # Second call returns 0 very slow queries
    ]
    
    # Mock recommendations
    optimizer._index_recommendations = [
        MagicMock(implemented=True),
        MagicMock(implemented=False),
    ]
    optimizer._query_rewrites = {
        "query1": MagicMock(),
    }
    
    # Mock config
    optimizer.config = MagicMock(spec=OptimizationConfig)
    optimizer.config.very_slow_query_threshold = 1.0
    
    # Create snapshot from optimizer
    snapshot = OptimizerMetricsSnapshot.from_optimizer(optimizer)
    
    # Verify snapshot data
    assert snapshot.query_count == 2
    assert snapshot.slow_query_count == 1
    assert snapshot.very_slow_query_count == 0
    assert snapshot.simple_queries == 1
    assert snapshot.complex_queries == 1
    assert snapshot.index_recommendations == 2
    assert snapshot.implemented_indexes == 1
    assert snapshot.query_rewrites == 1
    
    # Test percentile calculation
    assert snapshot.avg_execution_time == 0.3  # (0.1 + 0.5) / 2
    assert snapshot.p50_execution_time == 0.3  # Approximation between 0.1 and 0.5
    assert snapshot.p90_execution_time == 0.5  # Only 2 values, so p90 is the max


# Test OptimizerMetricsCollector
def test_optimizer_metrics_collector():
    """Test OptimizerMetricsCollector class."""
    # Create a mock metrics manager
    metrics_manager = MagicMock(spec=MetricsManager)
    
    # Create collector with mock metrics manager
    collector = OptimizerMetricsCollector(metrics_manager=metrics_manager)
    
    # Verify metrics registration
    assert metrics_manager.register_metric.call_count > 0
    
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    
    # Mock statistics
    optimizer.get_statistics.return_value = {"query1": MagicMock(spec=QueryStatistics)}
    optimizer.get_slow_queries.return_value = []
    optimizer._index_recommendations = []
    optimizer._query_rewrites = {}
    
    # Mock config
    optimizer.config = MagicMock(spec=OptimizationConfig)
    optimizer.config.very_slow_query_threshold = 1.0
    
    # Collect metrics
    snapshot = collector.collect_metrics(optimizer)
    
    # Verify snapshot was created
    assert isinstance(snapshot, OptimizerMetricsSnapshot)
    
    # Verify metrics were reported
    assert metrics_manager.record_metric.call_count > 0
    
    # Get snapshots
    all_snapshots = collector.get_snapshots()
    assert len(all_snapshots) == 1
    assert all_snapshots[0] is snapshot
    
    # Get latest snapshot
    latest = collector.get_latest_snapshot()
    assert latest is snapshot
    
    # Test time filtering
    current_time = time.time()
    
    # Future start time should return empty list
    future_snapshots = collector.get_snapshots(start_time=current_time + 1000)
    assert len(future_snapshots) == 0
    
    # Past end time should return empty list
    past_snapshots = collector.get_snapshots(end_time=current_time - 1000)
    assert len(past_snapshots) == 0
    
    # Current time range should return the snapshot
    current_snapshots = collector.get_snapshots(
        start_time=current_time - 1000,
        end_time=current_time + 1000
    )
    assert len(current_snapshots) == 1
    
    # Generate report
    report = collector.generate_report(optimizer)
    
    # Verify report structure
    assert "time_range" in report
    assert "latest" in report
    assert report["latest"]["query_count"] == 1
    
    # No trends since we only have one snapshot
    assert "trends" not in report
    
    # Add another snapshot for trends
    # Modify mock to return different metrics
    optimizer.get_statistics.return_value = {
        "query1": MagicMock(spec=QueryStatistics),
        "query2": MagicMock(spec=QueryStatistics),
    }
    optimizer.get_slow_queries.return_value = [MagicMock()]
    
    # Collect metrics again
    time.sleep(0.001)  # Ensure timestamp is different
    collector.collect_metrics(optimizer)
    
    # Generate report with trends
    report = collector.generate_report()
    
    # Verify trends
    assert "trends" in report
    assert report["trends"]["query_count_change"] == 1
    assert report["trends"]["slow_query_change"] == 1


# Test OptimizerMetricsMiddleware
@pytest.mark.asyncio
async def test_optimizer_metrics_middleware():
    """Test OptimizerMetricsMiddleware class."""
    # Create mock collector
    collector = MagicMock(spec=OptimizerMetricsCollector)
    collector.collect_metrics = AsyncMock()
    
    # Create mock optimizer factory
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer_factory = MagicMock(return_value=optimizer)
    
    # Create middleware
    middleware = OptimizerMetricsMiddleware(
        metrics_collector=collector,
        optimizer_factory=optimizer_factory,
    )
    
    # Set collection interval to 0 to ensure collection
    middleware.collection_interval = 0
    
    # Mock request and call_next
    request = MagicMock()
    response = MagicMock()
    call_next = AsyncMock(return_value=response)
    
    # Call middleware
    result = await middleware(request, call_next)
    
    # Verify call_next was called
    call_next.assert_awaited_once_with(request)
    
    # Verify result is the response
    assert result is response
    
    # Verify metrics collection was attempted
    # Note: we need to wait for the async task to complete
    await asyncio.sleep(0.1)
    
    optimizer_factory.assert_called_once()
    collector.collect_metrics.assert_awaited_once_with(optimizer)


# Test track_query_performance decorator
@pytest.mark.asyncio
async def test_track_query_performance():
    """Test track_query_performance decorator."""
    # Create mock collector and optimizer
    collector = MagicMock(spec=OptimizerMetricsCollector)
    collector.collect_metrics = MagicMock()
    
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer._query_stats = {}
    
    # Create decorated function
    @track_query_performance(collector, optimizer)
    async def test_function(param1, param2=None):
        await asyncio.sleep(0.01)
        return param1 + (param2 or 0)
    
    # Call function
    result = await test_function(1, 2)
    
    # Verify result
    assert result == 3
    
    # Verify query stats were recorded
    query_hash = f"func:test_function"
    assert query_hash in optimizer._query_stats
    
    # Verify metrics were collected
    collector.collect_metrics.assert_called_once_with(optimizer)


# Test with_query_metrics decorator
@pytest.mark.asyncio
async def test_with_query_metrics():
    """Test with_query_metrics decorator."""
    # Create mock session, collector, and optimizer
    session = MagicMock(spec=AsyncSession)
    
    collector = MagicMock(spec=OptimizerMetricsCollector)
    collector.collect_metrics = MagicMock(return_value=MagicMock(spec=OptimizerMetricsSnapshot))
    
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.session = None
    
    # Create decorated function
    @with_query_metrics(optimizer, collector)
    async def query_function(session):
        await asyncio.sleep(0.01)
        return "query_result"
    
    # Call function
    result = await query_function(session)
    
    # Verify result
    assert result == "query_result"
    
    # Verify optimizer session was updated
    assert optimizer.session is session
    
    # Verify metrics were collected
    collector.collect_metrics.assert_called_once_with(optimizer)
    
    # Verify metadata was updated
    assert collector.collect_metrics.return_value.metadata.update.call_count == 1
    update_args = collector.collect_metrics.return_value.metadata.update.call_args[0][0]
    assert "last_function" in update_args
    assert "last_execution_time" in update_args
    assert "timestamp" in update_args


# Test global collector functions
def test_global_collector_functions():
    """Test global metrics collector functions."""
    # Get default collector
    default_collector = get_metrics_collector()
    assert isinstance(default_collector, OptimizerMetricsCollector)
    
    # Create new collector
    new_collector = OptimizerMetricsCollector()
    
    # Set as default
    set_metrics_collector(new_collector)
    
    # Verify it's the new default
    assert get_metrics_collector() is new_collector
    
    # Restore original default
    set_metrics_collector(default_collector)


# Test collect_optimizer_metrics
@pytest.mark.asyncio
async def test_collect_optimizer_metrics():
    """Test collect_optimizer_metrics function."""
    # Create mock optimizer
    optimizer = MagicMock(spec=QueryOptimizer)
    optimizer.get_statistics.return_value = {}
    optimizer.get_slow_queries.return_value = []
    optimizer._index_recommendations = []
    optimizer._query_rewrites = {}
    optimizer.config = MagicMock(spec=OptimizationConfig)
    
    # Create mock collector
    collector = MagicMock(spec=OptimizerMetricsCollector)
    collector.collect_metrics.return_value = MagicMock(spec=OptimizerMetricsSnapshot)
    
    # Collect metrics
    snapshot = await collect_optimizer_metrics(optimizer, collector)
    
    # Verify collector was used
    collector.collect_metrics.assert_called_once_with(optimizer)
    
    # Verify snapshot
    assert snapshot is collector.collect_metrics.return_value
    
    # Test with default collector
    with patch('uno.database.optimizer_metrics._default_metrics_collector') as mock_default:
        mock_default.collect_metrics.return_value = MagicMock(spec=OptimizerMetricsSnapshot)
        
        snapshot = await collect_optimizer_metrics(optimizer)
        
        # Verify default collector was used
        mock_default.collect_metrics.assert_called_once_with(optimizer)