"""
Example usage of the query optimizer system.

This example demonstrates how to use the query optimizer for
analyzing and improving database query performance.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional

from sqlalchemy import text, select, func, Table, Column, Integer, String, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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
from uno.database.enhanced_pool_session import enhanced_pool_session


# Basic configuration for examples
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/example"


async def basic_analyzer_example():
    """Basic example of analyzing query execution plans."""
    print("Basic query analyzer example:")

    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer instance with the session
        optimizer = QueryOptimizer(session=session)

        # Example query to analyze
        query = """
        SELECT u.id, u.name, u.email, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        GROUP BY u.id, u.name, u.email
        ORDER BY order_count DESC
        LIMIT 10
        """

        # Analyze the query
        try:
            plan = await optimizer.analyze_query(query)

            # Print plan details
            print(f"Query plan type: {plan.plan_type}")
            print(f"Estimated cost: {plan.estimated_cost}")
            print(f"Estimated rows: {plan.estimated_rows}")
            print(f"Execution time: {plan.execution_time:.2f} seconds")
            print(f"Query complexity: {plan.complexity.value}")

            # Check for sequential scans
            if plan.has_sequential_scans:
                print("\nTables with sequential scans:")
                for table in plan.table_scans:
                    print(f"  - {table}")

            # Check for index usage
            if plan.index_usage:
                print("\nIndex usage:")
                for table, index in plan.index_usage.items():
                    print(f"  - {table}: {index}")

            # Check for nested loops
            if plan.has_nested_loops:
                print("\nQuery contains nested loop joins!")

        except Exception as e:
            print(f"Error analyzing query: {e}")


async def index_recommendation_example():
    """Example of getting index recommendations for a query."""
    print("\nIndex recommendation example:")

    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer instance with the session
        optimizer = QueryOptimizer(session=session)

        # Load schema information
        try:
            await optimizer.load_schema_information()
            print("Loaded database schema information")
        except Exception as e:
            print(f"Error loading schema: {e}")
            print("Using mock schema information for example")

            # Mock some table info for the example
            optimizer._table_info = {
                "users": {
                    "schema": "public",
                    "columns": [
                        {"name": "id", "type": "integer"},
                        {"name": "email", "type": "varchar"},
                        {"name": "status", "type": "varchar"},
                    ],
                },
                "orders": {
                    "schema": "public",
                    "columns": [
                        {"name": "id", "type": "integer"},
                        {"name": "user_id", "type": "integer"},
                        {"name": "status", "type": "varchar"},
                    ],
                },
            }

            optimizer._existing_indexes = {
                "users": [
                    {
                        "name": "users_pkey",
                        "columns": ["id"],
                        "unique": True,
                        "type": "btree",
                    }
                ],
                "orders": [
                    {
                        "name": "orders_pkey",
                        "columns": ["id"],
                        "unique": True,
                        "type": "btree",
                    }
                ],
            }

        # Example query for recommendation
        query = """
        SELECT * FROM users
        WHERE status = 'active' AND email LIKE '%example.com'
        """

        # First analyze the query
        try:
            plan = await optimizer.analyze_query(query)

            # Get index recommendations
            recommendations = optimizer.recommend_indexes(plan)

            if recommendations:
                print(f"Found {len(recommendations)} index recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"\nRecommendation {i}:")
                    print(f"  Table: {rec.table_name}")
                    print(f"  Columns: {', '.join(rec.column_names)}")
                    print(f"  Index type: {rec.index_type.value}")
                    if rec.estimated_improvement:
                        print(
                            f"  Estimated improvement: {rec.estimated_improvement*100:.1f}%"
                        )
                    print(f"  SQL: {rec.get_creation_sql()}")
            else:
                print("No index recommendations found")

        except Exception as e:
            print(f"Error getting recommendations: {e}")


async def query_rewrite_example():
    """Example of query rewriting for better performance."""
    print("\nQuery rewrite example:")

    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer instance with aggressive optimization
        config = OptimizationConfig(
            optimization_level=OptimizationLevel.AGGRESSIVE,
            rewrite_queries=True,
        )
        optimizer = QueryOptimizer(session=session, config=config)

        # Example queries to rewrite
        queries = [
            # Unnecessary DISTINCT
            "SELECT DISTINCT id, name FROM users WHERE id < 100",
            # COUNT(*) optimization
            "SELECT COUNT(*) FROM users",
            # OR conditions on different columns
            "SELECT * FROM users WHERE email = 'test@example.com' OR status = 'active'",
            # Large IN clause
            "SELECT * FROM users WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)",
        ]

        # Try to rewrite each query
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")

            result = await optimizer.rewrite_query(query)
            if result.is_success:
                rewrite = result.value
                print(f"Rewritten as: {rewrite.rewritten_query}")
                print(f"Rewrite type: {rewrite.rewrite_type}")
                if rewrite.estimated_improvement:
                    print(
                        f"Estimated improvement: {rewrite.estimated_improvement*100:.1f}%"
                    )
                if rewrite.reason:
                    print(f"Reason: {rewrite.reason}")
            else:
                print(f"No rewrite applied: {result.error}")


async def optimized_execution_example():
    """Example of using optimized query execution."""
    print("\nOptimized query execution example:")

    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create an optimizer instance
        optimizer = QueryOptimizer(session=session)

        # Example query to execute
        query = """
        SELECT id, name, email FROM users
        WHERE status = 'active'
        ORDER BY name
        """

        # Example with execute_optimized_query
        print("Executing query with optimization...")
        start_time = time.time()

        try:
            # Execute the query
            result = await optimizer.execute_optimized_query(query)

            # In a real scenario, result would be the query result rows
            # For this example, simulate some results
            result = [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ]

            execution_time = time.time() - start_time
            print(f"Query executed in {execution_time:.2f} seconds")
            print(f"Returned {len(result)} rows")

            # Get stats for the query
            query_hash = optimizer._hash_query(query)
            if query_hash in optimizer._query_stats:
                stats = optimizer._query_stats[query_hash]
                print(f"\nQuery statistics:")
                print(f"  Execution count: {stats.execution_count}")
                print(
                    f"  Average execution time: {stats.avg_execution_time:.2f} seconds"
                )
                print(f"  Max execution time: {stats.max_execution_time:.2f} seconds")

                # Get index recommendations for slow queries
                if stats.avg_execution_time >= optimizer.config.slow_query_threshold:
                    print("\nQuery is considered slow. Analyzing for optimization...")

                    if stats.latest_plan:
                        recommendations = optimizer.recommend_indexes(stats.latest_plan)

                        if recommendations:
                            print(
                                f"Found {len(recommendations)} index recommendations:"
                            )
                            for i, rec in enumerate(recommendations, 1):
                                print(f"  {i}. {rec.get_creation_sql()}")

            # Show all statistics collected
            all_stats = optimizer.get_statistics()
            print(f"\nTotal queries tracked: {len(all_stats)}")

            # Get slow queries
            slow_queries = optimizer.get_slow_queries()
            print(f"Slow queries detected: {len(slow_queries)}")

        except Exception as e:
            print(f"Error executing query: {e}")


async def decorator_example():
    """Example of using the optimized_query decorator."""
    print("\nOptimized query decorator example:")

    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Define a function with the optimized_query decorator
        @optimized_query()
        async def get_active_users(session: AsyncSession) -> list[dict[str, Any]]:
            print("  Executing get_active_users query...")

            # In a real scenario, this would execute a database query
            # For this example, simulate query execution
            await asyncio.sleep(0.1)

            # Simulate query result
            return [
                {"id": 1, "name": "User 1", "status": "active"},
                {"id": 2, "name": "User 2", "status": "active"},
            ]

        # Call the optimized function
        print("First call:")
        users1 = await get_active_users(session)
        print(f"  Found {len(users1)} active users")

        print("Second call:")
        users2 = await get_active_users(session)
        print(f"  Found {len(users2)} active users")


async def integration_example():
    """Example of integrating query optimizer with other components."""
    print("\nIntegration example with other components:")

    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Step 1: Analyze and optimize a query before execution
        query = "SELECT * FROM users WHERE status = 'active'"
        params = {}

        print("1. Pre-optimize query before execution:")

        try:
            # Use the helper function to optimize
            optimized_query, recommendations = await optimize_query(
                query=query,
                params=params,
                session=session,
            )

            # Show the optimized query
            if optimized_query != query:
                print(f"  Query was optimized:")
                print(f"  Original: {query}")
                print(f"  Optimized: {optimized_query}")
            else:
                print("  No optimization applied")

            # Show recommendations
            if recommendations:
                print(f"  {len(recommendations)} index recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"    {i}. {rec.get_creation_sql()}")

        except Exception as e:
            print(f"  Error in optimization: {e}")

        # Step 2: Demonstrate automated implementation of indexes
        print("\n2. Automatic index implementation:")

        # Create a configuration that allows auto-implementation
        config = OptimizationConfig(
            auto_implement_indexes=True,
        )

        # Create optimizer with this config
        optimizer = QueryOptimizer(session=session, config=config)

        # Mock table info
        optimizer._table_info = {
            "users": {
                "schema": "public",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "email", "type": "varchar"},
                    {"name": "status", "type": "varchar"},
                ],
            }
        }
        optimizer._existing_indexes = {"users": []}

        # Create a recommendation
        recommendation = IndexRecommendation(
            table_name="users",
            column_names=["status"],
            index_type=IndexType.BTREE,
            estimated_improvement=0.6,
        )

        # Add to recommendations list
        optimizer._index_recommendations.append(recommendation)

        # In a real scenario, we would implement this index
        # For this example, we'll just simulate it
        print(f"  Recommendation: {recommendation.get_creation_sql()}")
        print("  Simulating index implementation...")

        try:
            # For demonstration, we'll just simulate the implementation
            # Note: This would actually use the real method in a live example
            # and would require unittest.mock.patch in a real test
            print("  Would execute: " + recommendation.get_creation_sql())
            print("  Index successfully implemented")
            recommendation.implemented = True
            recommendation.implementation_time = time.time()

        except Exception as e:
            print(f"  Error implementing index: {e}")

        # Step 3: Show how optimizer works with monitoring
        print("\n3. Integration with monitoring:")

        # In a real scenario, we would collect metrics from the optimizer
        # For this example, we'll just show how to access the metrics

        # Add some sample statistics
        query_hash = optimizer._hash_query("SELECT * FROM users")
        optimizer._query_stats[query_hash] = QueryStatistics(
            query_hash=query_hash,
            query_text="SELECT * FROM users",
        )
        optimizer._query_stats[query_hash].record_execution(0.5, 100)
        optimizer._query_stats[query_hash].record_execution(0.7, 110)
        optimizer._query_stats[query_hash].record_execution(0.3, 90)

        # Get slow queries for monitoring
        slow_queries = optimizer.get_slow_queries(0.4)  # Threshold of 400ms
        print(f"  Slow queries: {len(slow_queries)}")

        if slow_queries:
            sq = slow_queries[0]
            print(f"  Sample slow query: {sq.query_text}")
            print(f"  Avg execution time: {sq.avg_execution_time:.2f} seconds")
            print(f"  Execution count: {sq.execution_count}")

        # Get frequent queries that might need optimization
        frequent_queries = optimizer.get_frequent_queries(5.0)  # 5+ executions per hour
        print(f"  Frequent queries: {len(frequent_queries)}")

        # Get index recommendations
        print(
            f"  Pending index recommendations: {len(optimizer.get_index_recommendations())}"
        )


async def main():
    """Run all examples."""
    print("QUERY OPTIMIZER EXAMPLES")
    print("=======================\n")

    await basic_analyzer_example()
    await index_recommendation_example()
    await query_rewrite_example()
    await optimized_execution_example()
    await decorator_example()
    await integration_example()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
