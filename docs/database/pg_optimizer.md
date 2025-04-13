# PostgreSQL Query Optimizer

The PostgreSQL-specific query optimizer extends the base query optimizer with specialized optimization strategies that leverage PostgreSQL-specific features.

## Overview

PostgreSQL offers many advanced optimization features beyond standard SQL. This module provides tailored optimizations for PostgreSQL databases, including specialized index types, query rewrites, and table maintenance recommendations.

## Features

- **PostgreSQL-specific index recommendations**:
  - Covering indexes with INCLUDE clauses
  - Partial indexes with WHERE clauses
  - Expression indexes for functions and operations
  - Specialized operator classes and index types

- **PostgreSQL-specific query rewrites**:
  - Common Table Expressions (CTE) optimization
  - LATERAL JOIN optimization
  - JSON operator optimization
  - DISTINCT ON optimization

- **Table statistics and maintenance**:
  - Detailed table and column statistics analysis
  - VACUUM and ANALYZE recommendations
  - Index usage analysis and recommendations
  - Table bloat detection and clustering recommendations

## Components

### PgIndexRecommendation

Enhanced index recommendation for PostgreSQL that supports additional index features.

```python
rec = PgIndexRecommendation(
    table_name="users",
    column_names=["email"],
    include_columns=["name", "status"],  # Covering index
    is_partial=True,                     # Partial index
    where_clause="active = true",        # Condition for partial index
    is_unique=True,                      # Unique constraint
    operator_class="text_pattern_ops",   # Operator class for LIKE queries
    index_tablespace="fast_ssd"          # Custom tablespace
)

# Generate SQL
sql = rec.get_creation_sql()
print(sql)
# CREATE UNIQUE INDEX idx_users_email ON users (email text_pattern_ops) 
# INCLUDE (name, status) WHERE active = true TABLESPACE fast_ssd
```

### PgOptimizationStrategies

Provides PostgreSQL-specific optimization strategies.

```python
# Create optimizer
optimizer = QueryOptimizer(session=session)

# Add PostgreSQL strategies
pg_strategies = add_pg_strategies(optimizer)

# Now you can use PostgreSQL-specific functionality
stats_result = await pg_strategies.get_table_statistics("users")
if stats_result.is_ok():
    stats = stats_result.unwrap()
    print(f"Table size: {stats['total_bytes_human']}")
    print(f"Row count: {stats['row_estimate']:,}")
```

### PgQueryOptimizer

A specialized version of the query optimizer with built-in PostgreSQL-specific optimizations.

```python
# Create the PostgreSQL optimizer
pg_optimizer = create_pg_optimizer(session=session)

# It has all the standard optimizer features plus PostgreSQL specifics
plan = await pg_optimizer.analyze_query("SELECT * FROM users")
recommendations = await pg_optimizer.recommend_indexes(plan)

# PG-specific functionality
maintenance_recs = await pg_optimizer.get_maintenance_recommendations(["users", "orders"])
```

## Usage Examples

### Basic Setup

```python
from uno.database.query_optimizer import QueryOptimizer
from uno.database.pg_optimizer_strategies import (
    PgOptimizationStrategies,
    add_pg_strategies,
    create_pg_optimizer,
)

# Method 1: Create standard optimizer and add PG strategies
optimizer = QueryOptimizer(session=session)
pg_strategies = add_pg_strategies(optimizer)

# Method 2: Create PG-specific optimizer directly
pg_optimizer = create_pg_optimizer(
    session=session,
    config=OptimizationConfig(
        optimization_level=OptimizationLevel.AGGRESSIVE
    )
)
```

### Analyzing Table Statistics

```python
# Get detailed table statistics
stats_result = await pg_strategies.get_table_statistics("users")
if stats_result.is_ok():
    stats = stats_result.unwrap()
    
    # Basic information
    print(f"Table: {stats['table_name']}")
    print(f"Row estimate: {stats['row_estimate']:,}")
    print(f"Total size: {stats['total_bytes_human']}")
    print(f"Table size: {stats['table_bytes_human']}")
    print(f"Index size: {stats['index_bytes_human']}")
    
    # Scan statistics
    print(f"Sequential scans: {stats['seq_scan_count']}")
    print(f"Rows returned: {stats['seq_scan_rows']:,}")
    
    # Column statistics
    for col in stats['columns']:
        print(f"Column: {col['column_name']}")
        print(f"  Distinct values: {col['distinct_values']}")
        print(f"  Null fraction: {col['null_fraction']}")
        print(f"  Correlation: {col['correlation']}")
```

### Getting Maintenance Recommendations

```python
# Get maintenance recommendations for a table
rec_result = await pg_strategies.recommend_table_maintenance("users")
if rec_result.is_ok():
    recommendations = rec_result.unwrap()
    
    print(f"Table: {recommendations['table_name']}")
    
    for rec in recommendations['recommendations']:
        print(f"Recommendation type: {rec['type']}")
        print(f"Priority: {rec['priority']}")
        print(f"Reason: {rec['reason']}")
        print(f"SQL: {rec['sql']}")
```

### PostgreSQL-Specific Index Recommendations

```python
# Get covering index recommendations
query = "SELECT name, email FROM users WHERE status = 'active'"
plan = await pg_optimizer.analyze_query(query)

# Get standard recommendations first
standard_recs = await pg_optimizer.recommend_indexes(plan)

# Get PostgreSQL-specific recommendations
covering_recs = pg_strategies.recommend_covering_index(plan, query)
partial_recs = pg_strategies.recommend_partial_index(plan, query)
expression_recs = pg_strategies.recommend_expression_index(plan, query)

# Implement a recommendation
if covering_recs:
    print(f"Recommended covering index: {covering_recs[0].get_creation_sql()}")
    await session.execute(text(covering_recs[0].get_creation_sql()))
    await session.commit()
```

### PostgreSQL-Specific Query Rewrites

```python
# Rewrite a query using PostgreSQL features
query = """
SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count
FROM users u
WHERE (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 0
"""

rewrite_result = await pg_strategies.rewrite_for_pg_features(query)
if rewrite_result.is_ok():
    rewrite = rewrite_result.unwrap()
    print(f"Rewrite type: {rewrite.rewrite_type}")
    print(f"Rewritten query: {rewrite.rewritten_query}")
    print(f"Reason: {rewrite.reason}")
    
    # Execute the rewritten query
    result = await session.execute(text(rewrite.rewritten_query))
    rows = result.all()
```

### Analyzing and Maintaining Tables

```python
# Run ANALYZE on multiple tables
analysis_results = await pg_optimizer.analyze_tables(["users", "orders", "products"])
for table, result in analysis_results.items():
    if result.is_ok():
        print(f"Successfully analyzed table {table}")
    else:
        print(f"Error analyzing table {table}: {result.unwrap_err()}")

# Get maintenance recommendations for multiple tables
maintenance_recs = await pg_optimizer.get_maintenance_recommendations(
    ["users", "orders", "products"]
)

for table, recs in maintenance_recs.items():
    if "error" in recs:
        print(f"Error analyzing {table}: {recs['error']}")
        continue
        
    print(f"Table: {table}")
    print(f"Size: {recs['statistics']['total_bytes_human']}")
    
    for rec in recs['recommendations']:
        print(f"  {rec['type']} ({rec['priority']} priority): {rec['reason']}")
        
        # For high priority recommendations, execute the SQL
        if rec['priority'] == "high":
            await session.execute(text(rec['sql']))
            await session.commit()
            print(f"  Executed: {rec['sql']}")
```

## PostgreSQL Index Types

### Covering Indexes

Covering indexes include additional columns that are not part of the index key but are included in the index leaf nodes.

```sql
CREATE INDEX idx_users_status ON users (status) INCLUDE (name, email)
```

Benefits:
- Allows index-only scans for queries that filter on status and select name and email
- Reduces table lookups
- Often faster than composite indexes for specific query patterns

### Partial Indexes

Partial indexes cover only a subset of the table, based on a WHERE condition.

```sql
CREATE INDEX idx_orders_created_at ON orders (created_at) WHERE status = 'active'
```

Benefits:
- Smaller index size
- Faster index maintenance
- Better performance for queries that always include the WHERE condition

### Expression Indexes

Expression indexes contain expressions or function calls rather than simple columns.

```sql
CREATE INDEX idx_users_email_lower ON users (LOWER(email))
```

Benefits:
- Optimize queries that use functions in WHERE clauses
- Enable indexing of transformed data
- Support pattern matching and case-insensitive searches

## PostgreSQL Query Rewrites

### Common Table Expressions (CTEs)

```sql
-- Original
SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count
FROM users u
WHERE (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 0

-- Rewritten with CTE
WITH order_counts AS (
    SELECT user_id, COUNT(*) AS count
    FROM orders
    GROUP BY user_id
)
SELECT u.name, oc.count AS order_count
FROM users u
JOIN order_counts oc ON u.id = oc.user_id
WHERE oc.count > 0
```

Benefits:
- Better readability
- Often better execution plans
- Reduced duplication

### LATERAL JOIN

```sql
-- Original
SELECT u.name, o.order_count
FROM users u
JOIN (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    WHERE orders.user_id = users.id
) AS o ON u.id = o.user_id

-- Rewritten with LATERAL
SELECT u.name, o.order_count
FROM users u
CROSS JOIN LATERAL (
    SELECT COUNT(*) as order_count
    FROM orders
    WHERE orders.user_id = u.id
) AS o
```

Benefits:
- Better optimizer support in PostgreSQL
- Clearer expression of correlated subqueries
- Often better performance for queries with subqueries

### JSON Operators

```sql
-- Original
SELECT id, JSON_EXTRACT(data, '$.name') as name,
       JSON_EXTRACT_SCALAR(data, '$.email') as email
FROM users

-- Rewritten with PostgreSQL operators
SELECT id, data -> 'name' as name,
       data ->> 'email' as email
FROM users
```

Benefits:
- Uses native PostgreSQL JSON operators
- Better performance
- Better type handling

### DISTINCT ON

```sql
-- Original
SELECT user_id, MIN(created_at) as first_order_date
FROM orders
GROUP BY user_id
ORDER BY user_id, created_at ASC

-- Rewritten with DISTINCT ON
SELECT DISTINCT ON (user_id) user_id, created_at as first_order_date
FROM orders
ORDER BY user_id, created_at ASC
```

Benefits:
- Often more efficient for "first/last value per group" queries
- Simpler syntax
- Returns additional columns without aggregation

## Table Maintenance

The PostgreSQL optimizer can recommend several types of maintenance operations:

### VACUUM

Recovers space from updated or deleted rows and updates statistics.

```sql
VACUUM [FULL] [ANALYZE] [table_name]
```

When to use:
- Tables with high update/delete activity
- Tables with significant bloat
- After bulk updates or deletes

### ANALYZE

Updates statistics used by the query planner.

```sql
ANALYZE [table_name]
```

When to use:
- After significant data changes
- When statistics are outdated
- When query plans are suboptimal

### CLUSTER

Physically reorders a table based on an index.

```sql
CLUSTER [table_name] USING [index_name]
```

When to use:
- When columns have low correlation
- For tables with range scans
- For sequential access patterns

## Best Practices

1. **Start with standard optimizer**: Use the base query optimizer for initial optimizations, then add PostgreSQL-specific features for problem queries.

2. **Regular maintenance**: Schedule regular maintenance based on the recommendations from `recommend_table_maintenance()`.

3. **Monitor statistics**: Regularly check table statistics to identify issues before they affect performance.

4. **Selective implementation**: Not all recommendations need to be implemented. Focus on high-priority recommendations and those that impact frequently used queries.

5. **Test before production**: Always test index recommendations and query rewrites in a staging environment before applying them to production.

6. **Incremental approach**: Implement recommendations incrementally and measure the impact of each change.

7. **Combination approach**: Sometimes, a combination of standard and PostgreSQL-specific optimizations provides the best performance.

## Integration with Monitoring

The PostgreSQL optimizer integrates well with monitoring systems:

```python
# Get table statistics for monitoring
stats_results = {}
for table in critical_tables:
    result = await pg_strategies.get_table_statistics(table)
    if result.is_ok():
        stats_results[table] = result.unwrap()

# Push metrics to monitoring system
for table, stats in stats_results.items():
    monitoring.gauge(f"pg.table.size.{table}", stats["total_bytes"])
    monitoring.gauge(f"pg.table.rows.{table}", stats["row_estimate"])
    monitoring.gauge(f"pg.table.bloat.{table}", 
                    (stats["table_bytes"] - (stats["row_estimate"] * stats["avg_row_size"])) 
                     / stats["table_bytes"] * 100)
```

## Advanced Configuration

The PostgreSQL optimizer can be further configured to fit specific needs:

```python
# Create a customized PostgreSQL optimizer
pg_optimizer = create_pg_optimizer(
    session=session,
    config=OptimizationConfig(
        # General settings
        optimization_level=OptimizationLevel.AGGRESSIVE,
        
        # Analysis settings
        analyze_queries=True,
        collect_statistics=True,
        
        # Rewrite settings
        rewrite_queries=True,
        safe_rewrites_only=False,  # Allow aggressive rewrites
        
        # Index settings
        recommend_indexes=True,
        auto_implement_indexes=False,
        
        # Logging
        log_recommendations=True,
        log_rewrites=True,
    ),
    logger=custom_logger
)
```