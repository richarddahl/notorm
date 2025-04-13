"""
Example usage of the PostgreSQL-specific query optimizer.

This example demonstrates how to use the PostgreSQL-specific optimizer for
analyzing and improving database query performance using PostgreSQL features.
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
)
from uno.database.pg_optimizer_strategies import (
    PgIndexRecommendation,
    PgOptimizationStrategies,
    PgQueryOptimizer,
    add_pg_strategies,
    create_pg_optimizer,
)
from uno.database.enhanced_pool_session import enhanced_pool_session


# Basic configuration for examples
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/example"


async def pg_optimizer_overview():
    """Overview of PostgreSQL-specific optimizer features."""
    print("PostgreSQL-specific Query Optimizer Overview:")
    print("============================================")
    
    print("\nThe PostgreSQL-specific query optimizer extends the base optimizer with:")
    print("  1. PostgreSQL-specific index recommendations:")
    print("     - Covering indexes (with INCLUDE columns)")
    print("     - Partial indexes (with WHERE clauses)")
    print("     - Expression indexes (for functions and expressions)")
    
    print("\n  2. PostgreSQL-specific query rewrites:")
    print("     - Common Table Expressions (CTEs) for better readability")
    print("     - LATERAL JOIN for correlated subqueries")
    print("     - JSON operations using PostgreSQL operators")
    print("     - DISTINCT ON for more efficient grouping")
    
    print("\n  3. PostgreSQL table maintenance recommendations:")
    print("     - VACUUM and ANALYZE for optimal performance")
    print("     - Table statistics for informed optimization")
    print("     - Index usage analysis")
    
    print("\nThese features leverage PostgreSQL's advanced capabilities to provide")
    print("more tailored performance optimizations for PostgreSQL databases.")


async def pg_specific_index_examples():
    """Examples of PostgreSQL-specific index recommendations."""
    print("\nPostgreSQL-specific Index Examples:")
    print("=================================")
    
    # Example 1: Covering index
    print("\n1. Covering Index Example:")
    covering_index = PgIndexRecommendation(
        table_name="users",
        column_names=["status"],          # Index key (for filtering)
        include_columns=["name", "email"] # Additional columns (for covering)
    )
    
    print(f"  SQL: {covering_index.get_creation_sql()}")
    print("  Benefits: Allows index-only scans, reducing table lookups")
    print("  Use case: Queries that filter on status and retrieve name and email")
    
    # Example 2: Partial index
    print("\n2. Partial Index Example:")
    partial_index = PgIndexRecommendation(
        table_name="orders",
        column_names=["created_at"],
        is_partial=True,
        where_clause="status = 'active'"
    )
    
    print(f"  SQL: {partial_index.get_creation_sql()}")
    print("  Benefits: Smaller index size, focused on subset of data")
    print("  Use case: Queries that always include the WHERE condition")
    
    # Example 3: Expression index
    print("\n3. Expression Index Example:")
    expression_index = PgIndexRecommendation(
        table_name="users",
        column_names=["LOWER(email)"],
        index_type=IndexType.BTREE
    )
    
    print(f"  SQL: {expression_index.get_creation_sql()}")
    print("  Benefits: Enables indexing of expressions and functions")
    print("  Use case: Case-insensitive searches like WHERE LOWER(email) = 'user@example.com'")
    
    # Example 4: Combined features
    print("\n4. Combined Features Example:")
    combined_index = PgIndexRecommendation(
        table_name="products",
        column_names=["category"],
        include_columns=["name", "price"],
        is_partial=True,
        where_clause="active = true",
        is_unique=True
    )
    
    print(f"  SQL: {combined_index.get_creation_sql()}")
    print("  Benefits: Combines multiple PostgreSQL index features")
    print("  Use case: Complex queries with specific access patterns")


async def query_rewrite_examples():
    """Examples of PostgreSQL-specific query rewrites."""
    print("\nPostgreSQL-specific Query Rewrite Examples:")
    print("=========================================")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create a PostgreSQL optimizer
        optimizer = create_pg_optimizer(session=session)
        
        # Example 1: CTE rewrite
        print("\n1. Common Table Expression (CTE) Rewrite:")
        subquery = """
        SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count
        FROM users u
        WHERE (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 0
        """
        
        print("  Original query with subqueries:")
        print(f"  {subquery.strip()}")
        
        # In a real scenario, we would call:
        # result = await optimizer.rewrite_query(subquery)
        
        # For this example, we'll show the expected output
        cte_rewrite = """
        WITH order_counts AS (
            SELECT user_id, COUNT(*) AS count
            FROM orders
            GROUP BY user_id
        )
        SELECT u.name, oc.count AS order_count
        FROM users u
        JOIN order_counts oc ON u.id = oc.user_id
        WHERE oc.count > 0
        """
        
        print("\n  Rewritten with CTE:")
        print(f"  {cte_rewrite.strip()}")
        print("  Benefits: Improved readability and potentially better execution plan")
        
        # Example 2: LATERAL JOIN rewrite
        print("\n2. LATERAL JOIN Rewrite:")
        lateral_query = """
        SELECT u.name, o.order_count
        FROM users u
        JOIN (
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            WHERE orders.user_id = users.id
        ) AS o ON u.id = o.user_id
        """
        
        print("  Original query with correlated subquery:")
        print(f"  {lateral_query.strip()}")
        
        lateral_rewrite = """
        SELECT u.name, o.order_count
        FROM users u
        CROSS JOIN LATERAL (
            SELECT COUNT(*) as order_count
            FROM orders
            WHERE orders.user_id = u.id
        ) AS o
        """
        
        print("\n  Rewritten with LATERAL JOIN:")
        print(f"  {lateral_rewrite.strip()}")
        print("  Benefits: PostgreSQL can optimize LATERAL joins better than correlated subqueries")
        
        # Example 3: JSON operation rewrite
        print("\n3. JSON Operation Rewrite:")
        json_query = """
        SELECT id, JSON_EXTRACT(data, '$.name') as name, 
               JSON_EXTRACT_SCALAR(data, '$.email') as email
        FROM users
        """
        
        print("  Original query with generic JSON functions:")
        print(f"  {json_query.strip()}")
        
        json_rewrite = """
        SELECT id, data -> 'name' as name, 
               data ->> 'email' as email
        FROM users
        """
        
        print("\n  Rewritten with PostgreSQL JSON operators:")
        print(f"  {json_rewrite.strip()}")
        print("  Benefits: Uses native PostgreSQL JSON operators for better performance")
        
        # Example 4: DISTINCT ON rewrite
        print("\n4. DISTINCT ON Rewrite:")
        distinct_query = """
        SELECT user_id, MIN(created_at) as first_order_date
        FROM orders
        GROUP BY user_id
        ORDER BY user_id, created_at ASC
        """
        
        print("  Original query with GROUP BY and aggregate:")
        print(f"  {distinct_query.strip()}")
        
        distinct_rewrite = """
        SELECT DISTINCT ON (user_id) user_id, created_at as first_order_date
        FROM orders
        ORDER BY user_id, created_at ASC
        """
        
        print("\n  Rewritten with DISTINCT ON:")
        print(f"  {distinct_rewrite.strip()}")
        print("  Benefits: Often more efficient for 'first/last value per group' queries")


async def table_maintenance_example():
    """Example of PostgreSQL table maintenance recommendations."""
    print("\nPostgreSQL Table Maintenance Example:")
    print("===================================")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Create a PostgreSQL optimizer
        optimizer = create_pg_optimizer(session=session)
        
        # In a real scenario, we would get actual statistics
        # For this example, we'll simulate the results
        
        print("\n1. Table Statistics Analysis:")
        
        # Simulated table statistics
        table_stats = {
            "table_name": "users",
            "row_estimate": 1000000,
            "page_count": 12500,
            "total_bytes": 204800000,
            "table_bytes": 153600000,
            "index_bytes": 51200000,
            "seq_scan_count": 150,
            "seq_scan_rows": 75000000,
            "avg_row_size": 153.6,
            "total_bytes_human": "195.31 MB",
            "table_bytes_human": "146.48 MB",
            "index_bytes_human": "48.83 MB",
            "columns": [
                {
                    "column_name": "id",
                    "distinct_values": -1,
                    "null_fraction": 0,
                    "correlation": 0.98
                },
                {
                    "column_name": "email",
                    "distinct_values": 1000000,
                    "null_fraction": 0,
                    "correlation": 0.15
                },
                {
                    "column_name": "status",
                    "distinct_values": 3,
                    "null_fraction": 0,
                    "correlation": 0.02
                }
            ]
        }
        
        print("  Table: users")
        print(f"  Rows: {table_stats['row_estimate']:,}")
        print(f"  Size: {table_stats['total_bytes_human']}")
        print(f"  Sequential scans: {table_stats['seq_scan_count']}")
        
        # Show column statistics
        print("\n  Column Statistics:")
        for col in table_stats["columns"]:
            print(f"    {col['column_name']}:")
            print(f"      Distinct values: {col['distinct_values']:,}" if col['distinct_values'] != -1 
                  else "      Distinct values: unique")
            print(f"      Correlation: {col['correlation']:.2f}")
        
        print("\n2. Maintenance Recommendations:")
        
        # Simulated maintenance recommendations
        maintenance_recs = [
            {
                "type": "VACUUM",
                "reason": "Table has approximately 30% bloat",
                "sql": "VACUUM (FULL, ANALYZE) users",
                "priority": "high"
            },
            {
                "type": "ANALYZE",
                "reason": "Table has been scanned frequently, statistics may be outdated",
                "sql": "ANALYZE users",
                "priority": "medium"
            },
            {
                "type": "CLUSTER",
                "reason": "Column email has low correlation (0.15), table might benefit from clustering",
                "sql": "CLUSTER users USING users_pkey",
                "priority": "low"
            }
        ]
        
        for rec in maintenance_recs:
            print(f"  {rec['type']} ({rec['priority']} priority):")
            print(f"    Reason: {rec['reason']}")
            print(f"    SQL: {rec['sql']}")


async def practical_usage_example():
    """Practical usage example of PostgreSQL-specific optimizer."""
    print("\nPractical Usage of PostgreSQL-specific Query Optimizer:")
    print("====================================================")
    
    # Create a session using our enhanced pool
    async with enhanced_pool_session() as session:
        # Use the standard query optimizer
        standard_optimizer = QueryOptimizer(session=session)
        
        # Create the PostgreSQL-specific optimizer
        pg_optimizer = create_pg_optimizer(session=session)
        
        # Example query to analyze
        query = """
        SELECT u.id, u.name, u.email, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active' AND LOWER(u.email) LIKE '%company.com'
        GROUP BY u.id, u.name, u.email
        ORDER BY order_count DESC
        LIMIT 10
        """
        
        print("Example query to analyze:")
        print(f"{query.strip()}")
        
        print("\n1. Comparing Standard vs PostgreSQL-specific Optimizer:")
        
        # In a real scenario, we would actually analyze the query:
        # standard_plan = await standard_optimizer.analyze_query(query)
        # pg_plan = await pg_optimizer.analyze_query(query)
        
        # For this example, we'll simulate the results
        
        print("\n  Standard Optimizer Recommendations:")
        print("  - Standard B-tree index on (status)")
        print("  - Standard B-tree index on (email)")
        
        print("\n  PostgreSQL-specific Optimizer Recommendations:")
        print("  - Covering index on (status) INCLUDE (name, email)")
        print("  - Partial index on (email) WHERE status = 'active'")
        print("  - Expression index on LOWER(email)")
        
        print("\n2. PostgreSQL-specific Query Rewrite:")
        
        # In a real scenario, we would:
        # rewrite_result = await pg_optimizer.rewrite_query(query)
        
        # Simulated rewritten query
        rewritten_query = """
        WITH user_orders AS (
            SELECT user_id, COUNT(id) as order_count
            FROM orders
            GROUP BY user_id
        )
        SELECT u.id, u.name, u.email, COALESCE(uo.order_count,.0) as order_count
        FROM users u
        LEFT JOIN user_orders uo ON u.id = uo.user_id
        WHERE u.status = 'active' AND LOWER(u.email) LIKE '%company.com'
        ORDER BY order_count DESC
        LIMIT 10
        """
        
        print("  Rewritten query with CTE:")
        print(f"  {rewritten_query.strip()}")
        
        print("\n3. Table Maintenance Integration:")
        print("  1. Analyze tables after schema updates or major data changes")
        print("  2. Schedule regular maintenance based on recommendations")
        print("  3. Monitor table statistics to detect performance degradation")
        print("  4. Create recommended indexes during low-traffic periods")
        
        print("\n4. Production Integration Workflow:")
        print("  1. Start with standard query optimizer for basic optimizations")
        print("  2. Apply PostgreSQL-specific optimizations for problem queries")
        print("  3. Implement recommended indexes and query rewrites")
        print("  4. Monitor query performance with optimizer statistics")
        print("  5. Schedule regular table maintenance based on recommendations")


async def main():
    """Run all examples."""
    print("POSTGRESQL-SPECIFIC QUERY OPTIMIZER EXAMPLES")
    print("==========================================\n")
    
    await pg_optimizer_overview()
    await pg_specific_index_examples()
    await query_rewrite_examples()
    await table_maintenance_example()
    await practical_usage_example()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())