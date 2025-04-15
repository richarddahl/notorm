# Query Optimizer

The query optimizer system analyzes, optimizes, and improves SQL queries for better database performance.

## Overview

The query optimizer provides tools to analyze query execution plans, identify performance bottlenecks, recommend indexes, and rewrite inefficient queries automatically. It's designed to work seamlessly with SQLAlchemy's async engine and session system.

## Features

- **Query plan analysis**: Extract and parse PostgreSQL's EXPLAIN output to understand query execution details
- **Index recommendations**: Automatically suggest indexes to improve query performance
- **Query rewriting**: Transform inefficient queries into more performant versions
- **Performance monitoring**: Track query statistics to identify slow queries
- **Adaptive optimization**: Apply different optimization strategies based on query complexity
- **Integration**: Seamless integration with SQLAlchemy's async session and engine

## Components

### QueryPlan

Represents a parsed database execution plan. Contains information about the query operations, table scans, index usage, and join types.

```python
plan = await optimizer.analyze_query("SELECT * FROM users WHERE status = 'active'")
print(f"Plan type: {plan.plan_type}")
print(f"Estimated cost: {plan.estimated_cost}")
print(f"Query complexity: {plan.complexity}")

if plan.has_sequential_scans:```

print("Sequential scans detected on tables:", plan.table_scans)
```
```

### IndexRecommendation

Recommendation for a database index to improve query performance. Includes table name, column names, index type, and SQL creation statement.

```python
recommendations = optimizer.recommend_indexes(plan)
for rec in recommendations:```

print(f"Recommended index: {rec.get_creation_sql()}")
print(f"Estimated improvement: {rec.estimated_improvement * 100:.1f}%")
```
```

### QueryRewrite

Represents a rewritten query for better performance. Contains both the original and rewritten versions, along with the reason for the rewrite.

```python
result = await optimizer.rewrite_query("SELECT DISTINCT id, name FROM users")
if result.is_ok():```

rewrite = result.unwrap()
print(f"Rewritten query: {rewrite.rewritten_query}")
print(f"Reason: {rewrite.reason}")
```
```

### QueryStatistics

Tracks performance statistics for queries, including execution counts, times, and patterns.

```python
stats = optimizer.get_statistics()
for query_hash, query_stats in stats.items():```

print(f"Query: {query_stats.query_text}")
print(f"Execution count: {query_stats.execution_count}")
print(f"Avg execution time: {query_stats.avg_execution_time:.2f}s")
```
```

### OptimizationConfig

Configuration for the query optimizer, controlling behavior and optimization settings.

```python
config = OptimizationConfig(```

optimization_level=OptimizationLevel.AGGRESSIVE,
rewrite_queries=True,
recommend_indexes=True,
auto_implement_indexes=False,
slow_query_threshold=1.0,  # 1 second
```
)
optimizer = QueryOptimizer(session=session, config=config)
```

### QueryOptimizer

The main optimizer class that analyzes, optimizes, and tracks queries.

## Usage Examples

### Basic Setup

```python
from uno.database.query_optimizer import QueryOptimizer, OptimizationConfig

# Create an optimizer with default configuration
optimizer = QueryOptimizer(session=session)

# Or with custom configuration
config = OptimizationConfig(```

optimization_level=OptimizationLevel.STANDARD,
recommend_indexes=True,
rewrite_queries=True,
```
)
optimizer = QueryOptimizer(session=session, config=config)
```

### Analyzing a Query

```python
# Analyze a SQL query string
plan = await optimizer.analyze_query("SELECT * FROM users WHERE status = 'active'")

# Or a SQLAlchemy executable
query = select(User).where(User.status == 'active')
plan = await optimizer.analyze_query(query)

# Examine the plan
print(f"Estimated cost: {plan.estimated_cost}")
print(f"Execution time: {plan.execution_time:.2f}s")
print(f"Query complexity: {plan.complexity}")

if plan.has_sequential_scans:```

print("Sequential scans detected on:", plan.table_scans)
```
    
if plan.has_nested_loops:```

print("Nested loops detected in the execution plan")
```
```

### Getting Index Recommendations

```python
# Load schema information for better recommendations
await optimizer.load_schema_information()

# Analyze a query
plan = await optimizer.analyze_query("SELECT * FROM users WHERE email LIKE '%example.com'")

# Get index recommendations
recommendations = optimizer.recommend_indexes(plan)

for rec in recommendations:```

print(f"Recommendation: {rec.get_creation_sql()}")
print(f"Estimated improvement: {rec.estimated_improvement * 100:.1f}%")
``````

```
```

# Implement the index if desired
if rec.estimated_improvement > 0.5:  # 50% improvement```

await optimizer.implement_index(rec)
```
```
```

### Rewriting Queries

```python
# Rewrite a query for better performance
result = await optimizer.rewrite_query(```

"SELECT DISTINCT * FROM users WHERE id < 1000"
```
)

if result.is_ok():```

rewrite = result.unwrap()
print(f"Original: {rewrite.original_query}")
print(f"Rewritten: {rewrite.rewritten_query}")
print(f"Reason: {rewrite.reason}")
```
```

### Executing Optimized Queries

```python
# Execute a query with automatic optimization
result = await optimizer.execute_optimized_query(```

"SELECT * FROM users WHERE status = 'active'"
```
)

# Works with SQLAlchemy queries too
query = select(User).where(User.status == 'active')
result = await optimizer.execute_optimized_query(query)
```

### Using the Decorator

```python
from uno.database.query_optimizer import optimized_query

@optimized_query()
async def get_active_users(session):```

return await session.execute(```

select(User).where(User.status == 'active')
```
)
```
```

### Monitoring Query Performance

```python
# Get all tracked query statistics
stats = optimizer.get_statistics()

# Get slow queries
slow_queries = optimizer.get_slow_queries(threshold=1.0)  # 1 second
for query in slow_queries:```

print(f"Slow query: {query.query_text}")
print(f"Avg time: {query.avg_execution_time:.2f}s")
```
    
# Get frequent queries
frequent_queries = optimizer.get_frequent_queries(min_frequency=10.0)  # 10 per hour
```

## Optimization Levels

The optimizer supports different optimization levels:

- **NONE**: No optimization, just analysis
- **BASIC**: Simple optimizations only
- **STANDARD**: Default level with balanced optimizations
- **AGGRESSIVE**: All optimizations, including those that might alter query behavior slightly

```python
from uno.database.query_optimizer import OptimizationLevel

config = OptimizationConfig(```

optimization_level=OptimizationLevel.AGGRESSIVE
```
)
```

## Rewrite Strategies

The optimizer can apply various rewrite strategies:

1. **Remove unnecessary DISTINCT**: Removes DISTINCT when it's not needed
2. **Optimize COUNT(*) queries**: Rewrites to COUNT(1) for better performance
3. **Convert OR to UNION**: Splits OR conditions on different columns into UNION for better index usage
4. **Optimize large IN clauses**: Rewrites large IN clauses to use temporary tables

## Index Types

The optimizer supports different index types:

- **BTREE**: Standard B-tree index (default)
- **HASH**: Hash index for equality comparisons
- **GIN**: GIN index for full-text search or arrays
- **GIST**: GiST index for geometric data types
- **BRIN**: BRIN index for large tables with natural ordering
- **VECTOR**: Vector index for vector similarity search

```python
from uno.database.query_optimizer import IndexType

rec = IndexRecommendation(```

table_name="products",
column_names=["description"],
index_type=IndexType.GIN
```
)
```

## Best Practices

1. **Initialize once**: Create a single optimizer instance per session or engine
2. **Load schema information**: Call `load_schema_information()` to enable better recommendations
3. **Track performance**: Review the statistics regularly to identify optimization opportunities
4. **Start conservatively**: Begin with STANDARD optimization level and increase if needed
5. **Verify recommendations**: Always validate index recommendations before implementing in production
6. **Monitor impact**: Track query performance before and after optimization

## Integration with Monitoring

The optimizer integrates with the monitoring system to track query performance metrics:

```python
# Get the query optimizer metrics for monitoring
metrics = optimizer.get_statistics()

# Push metrics to monitoring system
for query_hash, stats in metrics.items():```

monitoring.track_metric(```

name="query.execution_time",
value=stats.avg_execution_time,
tags={"query_hash": query_hash}
```
)
``````

```
```

monitoring.track_metric(```

name="query.execution_count",
value=stats.execution_count,
tags={"query_hash": query_hash}
```
)
```
```

## Advanced Configuration

```python
config = OptimizationConfig(```

# General settings
enabled=True,
optimization_level=OptimizationLevel.STANDARD,
``````

```
```

# Analysis settings
analyze_queries=True,
collect_statistics=True,
``````

```
```

# Rewrite settings
rewrite_queries=True,
safe_rewrites_only=True,
``````

```
```

# Index settings
recommend_indexes=True,
auto_implement_indexes=False,
index_creation_threshold=0.5,  # 50% estimated improvement
``````

```
```

# Performance thresholds
slow_query_threshold=1.0,  # 1 second
very_slow_query_threshold=5.0,  # 5 seconds
``````

```
```

# Logging
log_recommendations=True,
log_rewrites=True,
log_slow_queries=True,
```
)
```

## Helper Functions

### optimize_query

A helper function to optimize a query and get index recommendations in one call:

```python
from uno.database.query_optimizer import optimize_query

optimized_query, recommendations = await optimize_query(```

query="SELECT * FROM users WHERE status = 'active'",
session=session
```
)
```

### optimized_query

A decorator to automatically optimize functions that execute queries:

```python
from uno.database.query_optimizer import optimized_query

@optimized_query()
async def get_user_by_id(session, user_id):```

return await session.execute(```

select(User).where(User.id == user_id)
```
)
```
```

## Performance Impact

The query optimizer itself has minimal overhead for most operations:

- **analyze_query**: Adds an additional EXPLAIN query (recommended only for debugging and development)
- **rewrite_query**: Minimal overhead for string analysis
- **execute_optimized_query**: Small overhead for rewrite check and statistics tracking
- **recommend_indexes**: Negligible overhead if schema information is already loaded

For production environments, consider using:

```python
config = OptimizationConfig(```

optimization_level=OptimizationLevel.STANDARD,
analyze_queries=False,  # Disable expensive EXPLAIN analysis
collect_statistics=True,  # Keep tracking statistics
rewrite_queries=True,    # Keep rewriting queries
recommend_indexes=False, # Disable index recommendations
```
)
```

## Testing

The query optimizer includes comprehensive integration tests to ensure it works correctly with the database and query cache:

### Running Tests

```bash
# Run query optimizer integration tests
pytest tests/integration/test_query_optimizer.py --run-integration

# Run all integration tests including query optimizer
hatch run test:integration
```

### Test Coverage

Integration tests for the query optimizer cover:

1. **Query Plan Analysis**: Verify accurate extraction and analysis of execution plans
2. **Index Recommendations**: Test accuracy and usefulness of index recommendations
3. **Query Rewrite**: Validate that query rewrites improve performance and maintain correctness
4. **Slow Query Detection**: Ensure slow queries are properly identified and logged
5. **Query Cache Integration**: Verify seamless integration with the query cache system
6. **Performance Benchmarks**: Measure and compare performance impact of optimizations

### Example Test

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_rewrite(query_optimizer):```

"""Test query rewrite functionality."""
# Define a query that can be rewritten
query = "SELECT COUNT(*) FROM test_optimizer_products"
``````

```
```

# Try to rewrite the query
rewrite_result = await query_optimizer.rewrite_query(query)
``````

```
```

# Check the result
assert rewrite_result is not None
``````

```
```

# If a rewrite was found, check its properties
if rewrite_result.is_success:```

rewrite = rewrite_result.value
assert rewrite.original_query == query
assert rewrite.rewritten_query is not None
assert rewrite.rewrite_type is not None
assert rewrite.estimated_improvement is not None
```
```
```