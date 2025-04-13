"""
Example usage of the query optimizer metrics system.

This example demonstrates how to use the metrics collection and monitoring 
system for tracking query optimizer performance.
"""

import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import text, select, func, Table, Column, Integer, String, MetaData
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    IndexType,
    QueryPlan,
    QueryRewrite,
    QueryStatistics,
    OptimizationConfig,
    QueryOptimizer,
)
from uno.database.pg_optimizer_strategies import (
    PgQueryOptimizer,
    create_pg_optimizer,
)
from uno.database.optimizer_metrics import (
    OptimizerMetricsSnapshot,
    OptimizerMetricsCollector,
    OptimizerMetricsMiddleware,
    track_query_performance,
    with_query_metrics,
    collect_optimizer_metrics,
)
from uno.database.enhanced_pool_session import enhanced_pool_session
from uno.core.monitoring.metrics import MetricsManager, MetricType


async def basic_metrics_collection():
    """Basic example of collecting optimizer metrics."""
    print("Basic Metrics Collection Example:")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer
        optimizer = QueryOptimizer(session=session)
        
        # Create a metrics collector
        metrics_collector = OptimizerMetricsCollector()
        
        # Simulate some optimizer usage
        print("Simulating optimizer usage...")
        
        # Add a tracked query with statistics
        query1 = "SELECT * FROM users WHERE status = 'active'"
        optimizer._query_stats["query1"] = QueryStatistics(
            query_hash="query1",
            query_text=query1,
        )
        optimizer._query_stats["query1"].record_execution(0.1, 100)
        optimizer._query_stats["query1"].record_execution(0.2, 100)
        
        # Add another query with different performance characteristics
        query2 = "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id"
        optimizer._query_stats["query2"] = QueryStatistics(
            query_hash="query2",
            query_text=query2,
        )
        optimizer._query_stats["query2"].record_execution(1.5, 500)
        
        # Add a query plan for the second query
        plan = QueryPlan(
            plan_type="Select",
            estimated_cost=100.0,
            estimated_rows=1000,
            operations=[
                {"type": "Hash Join", "cost": 100.0, "rows": 1000, "width": 10},
                {"type": "Seq Scan", "cost": 10.0, "rows": 100, "width": 10},
            ],
            table_scans=["users", "orders"],
            join_types=["Hash Join"],
            execution_time=1.5,
        )
        optimizer._query_stats["query2"].latest_plan = plan
        
        # Add some index recommendations
        optimizer._index_recommendations = [
            {
                "table_name": "users",
                "column_names": ["status"],
                "index_type": IndexType.BTREE,
                "implemented": True,
            },
            {
                "table_name": "orders",
                "column_names": ["user_id"],
                "index_type": IndexType.BTREE,
                "implemented": False,
            }
        ]
        
        # Add some query rewrites
        optimizer._query_rewrites = {
            "query3": QueryRewrite(
                original_query="SELECT DISTINCT * FROM users",
                rewritten_query="SELECT * FROM users",
                rewrite_type="remove_unnecessary_distinct",
                estimated_improvement=0.2,
            )
        }
        
        # Collect metrics
        print("Collecting metrics snapshot...")
        snapshot = metrics_collector.collect_metrics(optimizer)
        
        # Display collected metrics
        print("\nCollected Metrics Snapshot:")
        print(f"  Timestamp: {datetime.fromtimestamp(snapshot.timestamp)}")
        print(f"  Query count: {snapshot.query_count}")
        print(f"  Slow query count: {snapshot.slow_query_count}")
        print(f"  Avg execution time: {snapshot.avg_execution_time:.2f}s")
        print(f"  P95 execution time: {snapshot.p95_execution_time:.2f}s")
        
        print("\nQuery Complexity Distribution:")
        print(f"  Simple queries: {snapshot.simple_queries}")
        print(f"  Moderate queries: {snapshot.moderate_queries}")
        print(f"  Complex queries: {snapshot.complex_queries}")
        print(f"  Very complex queries: {snapshot.very_complex_queries}")
        
        print("\nOptimizer Recommendations:")
        print(f"  Index recommendations: {snapshot.index_recommendations}")
        print(f"  Implemented indexes: {snapshot.implemented_indexes}")
        print(f"  Query rewrites: {snapshot.query_rewrites}")


async def metrics_tracking_over_time():
    """Example of tracking metrics over time."""
    print("\nMetrics Tracking Over Time Example:")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer
        optimizer = QueryOptimizer(session=session)
        
        # Create a metrics collector
        metrics_collector = OptimizerMetricsCollector()
        
        # Simulate optimizer usage over time
        print("Simulating optimizer usage over time...")
        
        # Track metrics every 0.5 seconds for 2 seconds
        for i in range(5):
            # Add a new query with random performance
            query_hash = f"query{i+1}"
            query_text = f"SELECT * FROM table{i+1}"
            
            optimizer._query_stats[query_hash] = QueryStatistics(
                query_hash=query_hash,
                query_text=query_text,
            )
            
            # Record multiple executions with varying performance
            for j in range(5):
                execution_time = 0.1 + random.random() * (i * 0.2)
                optimizer._query_stats[query_hash].record_execution(execution_time, 100)
                
                # Make some queries slow
                if execution_time > 0.5:
                    optimizer._query_stats[query_hash].latest_plan = QueryPlan(
                        plan_type="Select",
                        estimated_cost=100.0,
                        estimated_rows=1000,
                        operations=[{"type": "Seq Scan"}],
                        table_scans=[f"table{i+1}"],
                        join_types=[],
                        execution_time=execution_time,
                    )
            
            # Add a recommendation in each iteration
            optimizer._index_recommendations.append({
                "table_name": f"table{i+1}",
                "column_names": ["id"],
                "index_type": IndexType.BTREE,
                "implemented": i % 2 == 0,  # Implement every other recommendation
            })
            
            # Collect metrics for this iteration
            metrics_collector.collect_metrics(optimizer)
            
            # Wait a bit
            await asyncio.sleep(0.5)
        
        # Generate a report
        print("\nGenerating metrics report...")
        report = metrics_collector.generate_report(optimizer)
        
        # Display report summary
        print("\nMetrics Report Summary:")
        print(f"  Time range: {datetime.fromtimestamp(report['time_range']['start'])} - "
              f"{datetime.fromtimestamp(report['time_range']['end'])}")
        print(f"  Duration: {report['time_range']['duration_hours']:.2f} hours")
        print(f"  Snapshot count: {report['snapshot_count']}")
        
        print("\nLatest Metrics:")
        latest = report['latest']
        print(f"  Query count: {latest['query_count']}")
        print(f"  Slow query count: {latest['slow_query_count']}")
        print(f"  Avg execution time: {latest['avg_execution_time']:.2f}s")
        
        print("\nComplexity Distribution:")
        complexity = latest['complexity_distribution']
        print(f"  Simple: {complexity['simple']}")
        print(f"  Moderate: {complexity['moderate']}")
        print(f"  Complex: {complexity['complex']}")
        print(f"  Very complex: {complexity['very_complex']}")
        
        print("\nRecommendations:")
        recs = latest['recommendations']
        print(f"  Index recommendations: {recs['index_recommendations']}")
        print(f"  Implemented indexes: {recs['implemented_indexes']}")
        print(f"  Query rewrites: {recs['query_rewrites']}")
        
        if 'trends' in report:
            print("\nTrends:")
            trends = report['trends']
            print(f"  Query count change: {trends['query_count_change']}")
            print(f"  Slow query change: {trends['slow_query_change']}")
            
            if 'avg_execution_time_pct_change' in trends:
                print(f"  Avg execution time change: {trends['avg_execution_time_pct_change']:.2f}%")


async def decorator_usage_example():
    """Example of using the metrics decorators."""
    print("\nDecorator Usage Example:")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer
        optimizer = QueryOptimizer(session=session)
        
        # Create a metrics collector
        metrics_collector = OptimizerMetricsCollector()
        
        # Define a query function with the with_query_metrics decorator
        @with_query_metrics(optimizer, metrics_collector)
        async def get_users(session: AsyncSession, status: str = None):
            # Simulate a database query
            print(f"  Executing get_users query (status={status})...")
            await asyncio.sleep(0.2)
            
            # In a real scenario, we would execute a query:
            # query = select(User).where(User.status == status) if status else select(User)
            # result = await session.execute(query)
            # return result.scalars().all()
            
            return [
                {"id": 1, "name": "User 1", "status": status or "active"},
                {"id": 2, "name": "User 2", "status": status or "active"},
            ]
        
        # Define another function with the track_query_performance decorator
        @track_query_performance(metrics_collector, optimizer)
        async def get_user_orders(session: AsyncSession, user_id: int):
            # Simulate a more complex query
            print(f"  Executing get_user_orders query (user_id={user_id})...")
            await asyncio.sleep(0.3 + random.random() * 0.3)  # Variable execution time
            
            # Simulate a result
            return [
                {"id": 101, "user_id": user_id, "total": 99.99},
                {"id": 102, "user_id": user_id, "total": 49.99},
            ]
        
        # Execute the functions multiple times
        print("Executing queries with metrics tracking...")
        
        # Get all users
        users = await get_users(session)
        print(f"  Found {len(users)} users")
        
        # Get active users
        active_users = await get_users(session, status="active")
        print(f"  Found {len(active_users)} active users")
        
        # Get inactive users
        inactive_users = await get_users(session, status="inactive")
        print(f"  Found {len(inactive_users)} inactive users")
        
        # Get orders for multiple users
        for user_id in [1, 2, 3]:
            orders = await get_user_orders(session, user_id)
            print(f"  Found {len(orders)} orders for user {user_id}")
        
        # Get the latest metrics snapshot
        snapshot = metrics_collector.get_latest_snapshot()
        
        if snapshot:
            print("\nLatest Metrics After Decorated Function Calls:")
            print(f"  Timestamp: {datetime.fromtimestamp(snapshot.timestamp)}")
            print(f"  Query count: {snapshot.query_count}")
            print(f"  Avg execution time: {snapshot.avg_execution_time:.2f}s")
            
            # Check the metadata added by the decorator
            if hasattr(snapshot, 'metadata') and snapshot.metadata:
                print("\nMetadata from Decorators:")
                for key, value in snapshot.metadata.items():
                    if key == 'timestamp':
                        value = datetime.fromtimestamp(value)
                    print(f"  {key}: {value}")


async def integration_with_metrics_system():
    """Example of integrating with a metrics system."""
    print("\nIntegration with Metrics System Example:")
    
    # Create a mock metrics manager
    class MockMetricsManager(MetricsManager):
        def __init__(self):
            self.metrics = {}
            self.values = {}
            
        def register_metric(self, name, description, metric_type, unit=None):
            self.metrics[name] = {
                'description': description,
                'type': metric_type,
                'unit': unit
            }
            
        def record_metric(self, name, value, tags=None, timestamp=None):
            self.values[name] = value
            print(f"  Recorded metric: {name} = {value}")
            
    metrics_manager = MockMetricsManager()
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer
        optimizer = QueryOptimizer(session=session)
        
        # Create a metrics collector with the metrics manager
        metrics_collector = OptimizerMetricsCollector(metrics_manager=metrics_manager)
        
        # Simulate optimizer usage
        print("Simulating optimizer usage...")
        
        # Add a regular query
        query1 = "SELECT * FROM products WHERE category = 'electronics'"
        optimizer._query_stats["query1"] = QueryStatistics(
            query_hash="query1",
            query_text=query1,
        )
        optimizer._query_stats["query1"].record_execution(0.05, 50)
        optimizer._query_stats["query1"].record_execution(0.06, 50)
        
        # Add a slow query
        query2 = "SELECT p.*, SUM(o.quantity) FROM products p JOIN order_items o ON p.id = o.product_id GROUP BY p.id"
        optimizer._query_stats["query2"] = QueryStatistics(
            query_hash="query2",
            query_text=query2,
        )
        optimizer._query_stats["query2"].record_execution(2.5, 200)
        
        plan = QueryPlan(
            plan_type="Select",
            estimated_cost=500.0,
            estimated_rows=2000,
            operations=[
                {"type": "HashAggregate", "cost": 500.0, "rows": 2000, "width": 20},
                {"type": "Hash Join", "cost": 300.0, "rows": 2000, "width": 20},
                {"type": "Seq Scan", "cost": 100.0, "rows": 1000, "width": 10},
            ],
            table_scans=["products", "order_items"],
            join_types=["Hash Join"],
            execution_time=2.5,
        )
        optimizer._query_stats["query2"].latest_plan = plan
        
        # Add some recommendations
        optimizer._index_recommendations = [
            {
                "table_name": "products",
                "column_names": ["category"],
                "index_type": IndexType.BTREE,
                "implemented": True,
            },
            {
                "table_name": "order_items",
                "column_names": ["product_id"],
                "index_type": IndexType.BTREE,
                "implemented": False,
            }
        ]
        
        # Collect metrics
        print("\nCollecting metrics with metrics manager integration...")
        metrics_collector.collect_metrics(optimizer)
        
        # Display registered metrics
        print("\nRegistered Metrics in Metrics Manager:")
        for name, info in metrics_manager.metrics.items():
            print(f"  {name}: {info['description']} ({info['type'].name})")
        
        # Display recorded metric values
        print("\nRecorded Metric Values in Metrics Manager:")
        for name, value in metrics_manager.values.items():
            print(f"  {name}: {value}")
        
        # Show how these metrics could be used in a monitoring dashboard
        print("\nExample Monitoring Dashboard Metrics:")
        print("  - Query count: " + str(metrics_manager.values.get("query_optimizer.query_count", "N/A")))
        print("  - Slow query count: " + str(metrics_manager.values.get("query_optimizer.slow_query_count", "N/A")))
        print("  - Avg execution time: " + str(metrics_manager.values.get("query_optimizer.avg_execution_time", "N/A")))
        print("  - Complex queries: " + str(metrics_manager.values.get("query_optimizer.complex_queries", "N/A")))
        print("  - Index recommendations: " + str(metrics_manager.values.get("query_optimizer.index_recommendations", "N/A")))


async def middleware_example():
    """Example of using the metrics middleware with a web application."""
    print("\nMiddleware Example:")
    
    # Create a mock FastAPI app
    class MockApp:
        def __init__(self):
            self.middleware = []
            
        def add_middleware(self, middleware_class, **kwargs):
            self.middleware.append((middleware_class, kwargs))
            
    # Create a mock FastAPI application
    app = MockApp()
    
    # Create an optimizer factory function
    optimizer = QueryOptimizer()
    def get_optimizer():
        return optimizer
    
    # Create a metrics collector
    metrics_collector = OptimizerMetricsCollector()
    
    # Create middleware
    middleware = OptimizerMetricsMiddleware(
        metrics_collector=metrics_collector,
        optimizer_factory=get_optimizer,
    )
    
    # Add middleware to app
    app.add_middleware(OptimizerMetricsMiddleware, 
                      metrics_collector=metrics_collector, 
                      optimizer_factory=get_optimizer)
    
    print("Added OptimizerMetricsMiddleware to FastAPI application")
    
    # Simulate a request with the middleware
    print("\nSimulating a request through the middleware...")
    
    # Mock request and response
    request = {"path": "/api/users", "method": "GET"}
    response = {"status_code": 200, "body": "[]"}
    
    # Mock call_next function
    async def call_next(request):
        print("  Processing request to " + request["path"])
        
        # Simulate optimizer usage during request processing
        optimizer._query_stats["query1"] = QueryStatistics(
            query_hash="query1",
            query_text="SELECT * FROM users",
        )
        optimizer._query_stats["query1"].record_execution(0.05, 10)
        
        return response
    
    # Process the request through middleware
    result = await middleware(request, call_next)
    
    print(f"  Request completed with status code {result['status_code']}")
    
    # Wait for async task to complete
    await asyncio.sleep(0.1)
    
    print("\nMiddleware collected metrics in background")
    
    # In a real application, metrics would be collected periodically
    # as requests are processed through the middleware


async def practical_usage_scenario():
    """Practical example of using optimizer metrics in a production scenario."""
    print("\nPractical Usage Scenario:")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create a PostgreSQL optimizer with metrics integration
        optimizer = create_pg_optimizer(
            session=session,
            config=OptimizationConfig(
                optimization_level=OptimizationLevel.STANDARD,
                rewrite_queries=True,
                recommend_indexes=True,
            )
        )
        
        # Create a metrics collector
        metrics_collector = OptimizerMetricsCollector()
        
        print("Setting up optimizer metrics collection for production system...")
        
        # Simulate a production system where we:
        # 1. Periodically collect metrics
        # 2. Generate reports
        # 3. Implement recommendations based on metrics
        # 4. Track performance improvements
        
        print("\nPhase 1: Initial system state")
        
        # Simulate initial state with some slow queries
        for i in range(5):
            query_hash = f"query{i+1}"
            query_text = f"SELECT * FROM products WHERE category_id = {i+1}"
            
            optimizer._query_stats[query_hash] = QueryStatistics(
                query_hash=query_hash,
                query_text=query_text,
            )
            
            # Make some queries slow
            execution_time = 0.5 + random.random() * 0.5
            optimizer._query_stats[query_hash].record_execution(execution_time, 100)
            
            # Add query plans for analysis
            optimizer._query_stats[query_hash].latest_plan = QueryPlan(
                plan_type="Select",
                estimated_cost=100.0,
                estimated_rows=1000,
                operations=[{"type": "Seq Scan", "cost": 100.0}],
                table_scans=["products"],
                join_types=[],
                execution_time=execution_time,
            )
        
        # Collect initial metrics
        initial_snapshot = metrics_collector.collect_metrics(optimizer)
        
        print(f"  Initial metrics collected:")
        print(f"    Query count: {initial_snapshot.query_count}")
        print(f"    Slow query count: {initial_snapshot.slow_query_count}")
        print(f"    Avg execution time: {initial_snapshot.avg_execution_time:.2f}s")
        
        print("\nPhase 2: Analyze and generate recommendations")
        
        # Generate recommendations based on query performance
        optimizer._index_recommendations = [
            {
                "table_name": "products",
                "column_names": ["category_id"],
                "index_type": IndexType.BTREE,
                "estimated_improvement": 0.8,
                "implemented": False,
            }
        ]
        
        print("  Generated recommendations:")
        for i, rec in enumerate(optimizer._index_recommendations):
            print(f"    Recommendation {i+1}: Index on {rec['table_name']}({', '.join(rec['column_names'])})")
            print(f"      Estimated improvement: {rec['estimated_improvement']*100:.1f}%")
        
        print("\nPhase 3: Implement recommendations")
        
        # Simulate implementing the recommendations
        print("  Implementing index recommendations...")
        
        # Mark recommendations as implemented
        optimizer._index_recommendations[0]["implemented"] = True
        
        # Simulate improved query performance after index creation
        for query_hash, stats in optimizer._query_stats.items():
            # Reduce execution time by 80% (matching estimated improvement)
            new_execution_time = stats.avg_execution_time * 0.2
            
            # Record new executions with improved time
            for _ in range(3):
                stats.record_execution(new_execution_time, 100)
                
            # Update the query plan to use the new index
            if stats.latest_plan:
                stats.latest_plan = QueryPlan(
                    plan_type="Select",
                    estimated_cost=10.0,  # Lower cost
                    estimated_rows=1000,
                    operations=[{"type": "Index Scan", "cost": 10.0}],  # Now using index
                    table_scans=[],  # No more sequential scans
                    join_types=[],
                    execution_time=new_execution_time,
                )
                # Add index usage info
                stats.latest_plan.index_usage = {"products": "products_category_id_idx"}
        
        # Collect metrics after optimization
        optimized_snapshot = metrics_collector.collect_metrics(optimizer)
        
        print("  Metrics after optimization:")
        print(f"    Query count: {optimized_snapshot.query_count}")
        print(f"    Slow query count: {optimized_snapshot.slow_query_count}")
        print(f"    Avg execution time: {optimized_snapshot.avg_execution_time:.2f}s")
        
        print("\nPhase 4: Generate performance improvement report")
        
        # Calculate improvements
        execution_time_improvement = (
            (initial_snapshot.avg_execution_time - optimized_snapshot.avg_execution_time) 
            / initial_snapshot.avg_execution_time * 100
        )
        
        slow_query_reduction = (
            (initial_snapshot.slow_query_count - optimized_snapshot.slow_query_count)
            / max(initial_snapshot.slow_query_count, 1) * 100
        )
        
        print("  Performance improvement summary:")
        print(f"    Execution time reduction: {execution_time_improvement:.1f}%")
        print(f"    Slow query reduction: {slow_query_reduction:.1f}%")
        print(f"    Recommendations implemented: 1 of 1")
        
        print("\nPhase 5: Ongoing monitoring")
        
        # In a real system, we would continue monitoring and optimizing
        print("  Setting up ongoing metrics collection...")
        print("  - Scheduled metrics collection every 15 minutes")
        print("  - Weekly performance reports")
        print("  - Alerting on slow query increases")
        print("  - Dashboard with query optimizer metrics")


async def main():
    """Run all examples."""
    print("QUERY OPTIMIZER METRICS EXAMPLES")
    print("================================\n")
    
    await basic_metrics_collection()
    await metrics_tracking_over_time()
    await decorator_usage_example()
    await integration_with_metrics_system()
    await middleware_example()
    await practical_usage_scenario()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())