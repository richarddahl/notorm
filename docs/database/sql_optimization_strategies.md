# SQL Optimization Strategies

This document outlines the SQL optimization strategies used within the uno framework to enhance database performance, reduce query execution time, and efficiently utilize database resources.

## Table of Contents

1. [Common Table Expressions (CTEs)](#common-table-expressions-ctes)
2. [LATERAL Joins](#lateral-joins)
3. [JSONB Aggregation](#jsonb-aggregation)
4. [Function-Based Indexes](#function-based-indexes)
5. [Materialized Views](#materialized-views)
6. [Optimized Index Strategies](#optimized-index-strategies)
7. [Covering Indexes](#covering-indexes)
8. [Query Caching](#query-caching)
9. [Autovacuum Tuning](#autovacuum-tuning)
10. [Execution Plan Management](#execution-plan-management)

## Common Table Expressions (CTEs)

CTEs provide a way to create named temporary result sets that exist for the duration of a query. They can improve query readability and often performance by replacing multiple subqueries.

```sql
-- Original query with subqueries (less optimal):
SELECT
    u.id, u.username,
    (SELECT COUNT(*) FROM schema.posts p WHERE p.user_id = u.id) AS post_count,
    (SELECT COUNT(*) FROM schema.comments c WHERE c.user_id = u.id) AS comment_count,
    (SELECT MAX(p2.created_at) FROM schema.posts p2 WHERE p2.user_id = u.id) AS last_post_date
FROM
    schema.users u
WHERE
    u.is_active = true

-- Optimized query with CTEs:
WITH user_posts AS (
    SELECT 
        user_id,
        COUNT(*) AS post_count,
        MAX(created_at) AS last_post_date
    FROM 
        schema.posts
    GROUP BY 
        user_id
),
user_comments AS (
    SELECT 
        user_id,
        COUNT(*) AS comment_count
    FROM 
        schema.comments
    GROUP BY 
        user_id
)
SELECT
    u.id, u.username,
    COALESCE(up.post_count, 0) AS post_count,
    COALESCE(uc.comment_count, 0) AS comment_count,
    up.last_post_date
FROM
    schema.users u
LEFT JOIN
    user_posts up ON u.id = up.user_id
LEFT JOIN
    user_comments uc ON u.id = uc.user_id
WHERE
    u.is_active = true;
```

## LATERAL Joins

LATERAL joins allow correlated subqueries to reference columns from preceding FROM items. They are especially useful for row-by-row processing that depends on the main query row.

```sql
-- Original query with correlated subqueries (less optimal):
SELECT 
    p.id, p.title,
    (SELECT c.id FROM schema.comments c 
     WHERE c.post_id = p.id 
     ORDER BY c.created_at DESC LIMIT 1) AS latest_comment_id,
    (SELECT c.content FROM schema.comments c 
     WHERE c.post_id = p.id 
     ORDER BY c.created_at DESC LIMIT 1) AS latest_comment,
    (SELECT u.username FROM schema.users u 
     JOIN schema.comments c ON u.id = c.user_id
     WHERE c.post_id = p.id 
     ORDER BY c.created_at DESC LIMIT 1) AS latest_commenter
FROM 
    schema.posts p
WHERE 
    p.published = true

-- Optimized query with LATERAL joins:
SELECT 
    p.id, p.title,
    latest_comment.id AS latest_comment_id,
    latest_comment.content AS latest_comment,
    latest_comment.username AS latest_commenter
FROM 
    schema.posts p
LEFT JOIN LATERAL (
    SELECT 
        c.id,
        c.content,
        u.username
    FROM 
        schema.comments c
    JOIN 
        schema.users u ON c.user_id = u.id
    WHERE 
        c.post_id = p.id
    ORDER BY 
        c.created_at DESC
    LIMIT 1
) latest_comment ON true
WHERE 
    p.published = true;
```

## JSONB Aggregation

JSONB aggregation allows creating hierarchical data structures in a single query, reducing the number of round trips to the database.

```sql
-- Original approach with multiple queries (less optimal):
-- First query: Get posts
SELECT id, title, content FROM schema.posts WHERE user_id = 'some_user_id';

-- Then for each post, query its comments:
SELECT id, content FROM schema.comments WHERE post_id = 'post_id_1';
SELECT id, content FROM schema.comments WHERE post_id = 'post_id_2';
-- ...etc.

-- Optimized query with JSONB_AGG:
SELECT 
    p.id,
    p.title,
    p.content,
    JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'id', c.id,
            'content', c.content,
            'username', u.username,
            'created_at', c.created_at
        ) ORDER BY c.created_at DESC
    ) FILTER (WHERE c.id IS NOT NULL) AS comments
FROM 
    schema.posts p
LEFT JOIN 
    schema.comments c ON p.id = c.post_id
LEFT JOIN 
    schema.users u ON c.user_id = u.id
WHERE 
    p.user_id = 'user_id'
GROUP BY 
    p.id, p.title, p.content;
```

## Function-Based Indexes

Function-based indexes can significantly improve query performance for expressions used in WHERE clauses that would otherwise not benefit from traditional indexes.

```sql
-- Create function-based index for case-insensitive search
CREATE INDEX idx_users_username_lower ON schema.users (LOWER(username));

-- Create function-based index for date range queries
CREATE INDEX idx_posts_year_month ON schema.posts (EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at));

-- Create function-based index for JSON data
CREATE INDEX idx_posts_metadata_published ON schema.posts ((metadata->>'published')::boolean);

-- Example queries that can use these indexes:
-- This query can use the LOWER index:
SELECT * FROM schema.users WHERE LOWER(username) = LOWER('UserName');

-- This query can use the date extraction index:
SELECT * FROM schema.posts 
WHERE EXTRACT(YEAR FROM created_at) = 2023 AND EXTRACT(MONTH FROM created_at) = 6;

-- This query can use the JSON index:
SELECT * FROM schema.posts WHERE (metadata->>'published')::boolean = true;
```

## Materialized Views

Materialized views store the result of a query physically, making it faster to retrieve the data for complex reporting queries. They are particularly useful for data that changes infrequently.

```sql
-- Create materialized view for user activity reports
CREATE MATERIALIZED VIEW schema.user_activity_report AS
SELECT 
    u.id AS user_id,
    u.username,
    COUNT(DISTINCT p.id) AS post_count,
    COUNT(DISTINCT c.id) AS comment_count,
    MAX(p.created_at) AS last_post_date,
    MAX(c.created_at) AS last_comment_date,
    SUM(p.view_count) AS total_views,
    (COUNT(DISTINCT c.id)::float / NULLIF(COUNT(DISTINCT p.id), 0)) AS comments_per_post
FROM 
    schema.users u
LEFT JOIN 
    schema.posts p ON u.id = p.user_id
LEFT JOIN 
    schema.comments c ON u.id = c.user_id
WHERE 
    u.is_active = true
GROUP BY 
    u.id, u.username;

-- Create index on materialized view
CREATE UNIQUE INDEX idx_user_activity_report_user_id ON schema.user_activity_report(user_id);

-- Function to refresh the materialized view
CREATE OR REPLACE FUNCTION schema.refresh_activity_report() 
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY schema.user_activity_report;
END;
$$ LANGUAGE plpgsql;
```

## Optimized Index Strategies

Optimize indexes based on query patterns to ensure the most efficient types are created.

```sql
-- For high-frequency queries with filtering and sorting
-- Use a covering index that includes sort columns
CREATE INDEX idx_posts_user_id_created_at ON schema.posts (user_id) INCLUDE (created_at);

-- For full-text search
CREATE INDEX idx_posts_tsvector ON schema.posts
USING GIN (to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, '')));

-- For JSONB operations
CREATE INDEX idx_posts_metadata ON schema.posts USING GIN (metadata);

-- For composite key searches
CREATE INDEX idx_comments_post_user ON schema.comments (post_id, user_id);
```

## Covering Indexes

Covering indexes include all columns needed for a query, allowing PostgreSQL to retrieve data directly from the index without accessing the table.

```sql
-- Create a covering index for a common query pattern
CREATE INDEX idx_posts_list_covering ON schema.posts (
    user_id, 
    created_at DESC
) INCLUDE (id, title, published);

-- This query can be satisfied entirely from the index:
SELECT id, title, published 
FROM schema.posts 
WHERE user_id = 'user_id' 
ORDER BY created_at DESC 
LIMIT 10;
```

## Query Caching

Implement application-level query caching for frequently accessed, rarely changed data.

```python
# UnoDb implementation with query caching
from uno.database.query_cache import QueryCache

class CachedUnoDB:
    def __init__(self, connection_config, cache_config):
        self.db = UnoDB(connection_config)
        self.query_cache = QueryCache(cache_config)
    
    async def execute_cached_query(self, query, params=None, cache_key=None, ttl=300):
        """Execute a query with caching"""
        cache_key = cache_key or f"sql:{hash(query)}:{hash(str(params))}"
        
        # Try to get from cache
        cached_result = await self.query_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Execute query and cache result
        result = await self.db.execute(query, params)
        await self.query_cache.set(cache_key, result, ttl)
        return result
```

## Autovacuum Tuning

Customize PostgreSQL's autovacuum for tables with different access patterns.

```sql
-- High-write tables: more frequent vacuuming
ALTER TABLE schema.posts SET (
    autovacuum_vacuum_scale_factor = 0.05,  -- Vacuum when 5% of tuples are dead
    autovacuum_analyze_scale_factor = 0.05, -- Analyze when 5% of tuples are modified
    autovacuum_vacuum_cost_limit = 1000     -- Allow more work per vacuum
);

-- Slowly changing tables: less frequent vacuuming
ALTER TABLE schema.settings SET (
    autovacuum_vacuum_scale_factor = 0.2,   -- Vacuum when 20% of tuples are dead
    autovacuum_analyze_scale_factor = 0.1,  -- Analyze when 10% of tuples are modified
    autovacuum_vacuum_cost_limit = 200      -- Standard work per vacuum
);
```

## Execution Plan Management

Manage and optimize query execution plans using PostgreSQL's features.

```sql
-- Collect statistics for improved query plans
ANALYZE schema.posts;

-- Set statistics target for specific columns
ALTER TABLE schema.posts ALTER COLUMN user_id SET STATISTICS 1000;

-- Use optimizer hints for specific queries
SELECT /*+ IndexScan(posts idx_posts_user_id) */ 
    * 
FROM 
    schema.posts 
WHERE 
    user_id = 'specific_user_id';

-- Create statistics for correlated columns
CREATE STATISTICS posts_stats ON user_id, created_at FROM schema.posts;
```

## Implementation in UnoSQL Framework

The uno framework implements these optimization strategies through several components:

1. **SQLEmitter**: Generates optimized SQL based on the query patterns
2. **Query Optimizer**: Analyzes queries and recommends optimization strategies
3. **Index Manager**: Creates and maintains optimal index strategies
4. **Schema Manager**: Handles materialized views and other schema objects
5. **Monitoring Tools**: Track query performance and suggest optimizations

These strategies should be applied judiciously based on specific use cases and performance testing. Not all optimizations are appropriate for all scenarios, and some may even decrease performance in certain situations.