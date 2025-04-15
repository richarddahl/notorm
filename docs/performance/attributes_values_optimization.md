# Attributes and Values Performance Optimization

This document provides guidance on optimizing performance when working with attributes and values in the UNO framework.

## Overview

The attributes and values modules can be performance-intensive due to their dynamic nature and the potential for complex relationships. This document outlines strategies for optimizing performance in these areas.

## Database Optimization

### Indexing

Ensure that all necessary indexes are in place for attribute and value queries:

- Attribute type ID indexes
- Value type indexes
- `attribute__value` junction table indexes
- `attribute__meta` junction table indexes
- `attribute_type__meta_type` junction table indexes

Most of these are created automatically, but custom queries may require additional indexes.

### Query Optimization

For complex attribute queries, consider the following optimizations:

1. Use bulk operations where possible
2. Eager load related data to prevent N+1 query problems
3. Limit the number of attributes returned in a single query
4. Use pagination for large result sets

## Caching Strategies

### Value Caching

Since values are often reused (especially common values like booleans, dates, and discrete numbers), implement caching:

```python
from uno.caching import CacheManager
from uno.values import ValueService

# Configure the cache
cache_manager = CacheManager()
cache_manager.configure(ttl=3600)  # Cache for 1 hour

# Inject the cache into the value service
value_service = ValueService(```

# other parameters...
cache_manager=cache_manager
```
)
```

### Attribute Type Caching

Attribute types change infrequently but are accessed often, making them good candidates for longer-term caching:

```python
from uno.caching import CacheManager
from uno.attributes import AttributeTypeService

# Configure the cache with a longer TTL
cache_manager = CacheManager()
cache_manager.configure(ttl=86400)  # Cache for 24 hours

# Inject the cache into the attribute type service
attribute_type_service = AttributeTypeService(```

# other parameters...
cache_manager=cache_manager
```
)
```

## Batch Processing

For operations involving multiple attributes or values, use batch processing:

### Bulk Attribute Creation

```python
async def create_many_attributes(```

attribute_service, 
attributes: List[Attribute],
value_lists: List[List[MetaRecord]]
```
) -> List[Attribute]:```

"""Create multiple attributes in batch."""
results = []
``````

```
```

async with attribute_service.db_manager.get_enhanced_session() as session:```

for attribute, values in zip(attributes, value_lists):
    # Validate attribute first
    validation_result = await attribute_service.validate_attribute(attribute, values)
    if validation_result.is_err():
        continue
        
    attribute.values = values
    
# Create attributes in bulk
create_result = await attribute_service.attribute_repository.bulk_create(attributes, session)
if create_result.is_ok():
    results.extend(create_result.unwrap())
```
``````

```
```

return results
```
```

### Bulk Value Operations

```python
async def get_or_create_bulk_values(```

value_service,
value_type: Type[ValueObj],
values: List[ValueType],
names: Optional[List[str]] = None
```
) -> List[ValueObj]:```

"""Get or create multiple values in batch."""
if names is None:```

names = [str(value) for value in values]
```
``````

```
```

repository = value_service._get_repository(value_type)
``````

```
```

# First try to get existing values
existing_values = []
new_values = []
new_names = []
``````

```
```

for i, value in enumerate(values):```

get_result = await repository.get_by_value(value)
if get_result.is_ok() and get_result.unwrap():
    existing_values.append(get_result.unwrap())
else:
    new_values.append(value)
    new_names.append(names[i])
```
``````

```
```

# Create new values in bulk
if new_values:```

value_objs = [value_type(value=value, name=name) for value, name in zip(new_values, new_names)]
create_result = await repository.bulk_create(value_objs)
if create_result.is_ok():
    existing_values.extend(create_result.unwrap())
```
``````

```
```

return existing_values
```
```

## Denormalization Strategies

Consider denormalizing frequently accessed attribute and value data:

### Materialized Views

Create materialized views for commonly used attribute and value combinations:

```sql
-- Example materialized view for product attributes
CREATE MATERIALIZED VIEW product_attributes AS
SELECT```

m.id AS product_id,
m.name AS product_name,
a.id AS attribute_id,
at.name AS attribute_name,
v.id AS value_id,
v.value AS value_value
```
FROM```

meta_record m
```
JOIN```

attribute__meta am ON m.id = am.meta_id
```
JOIN```

attribute a ON a.id = am.attribute_id
```
JOIN```

attribute_type at ON a.attribute_type_id = at.id
```
JOIN```

attribute__value av ON a.id = av.attribute_id
```
JOIN```

text_value v ON av.value_id = v.id
```
WHERE```

m.meta_type_id = '01H3ZEVKY6ZH3F41K5GS77PJ1Z' -- Product type ID
```
;

-- Create indexes
CREATE INDEX idx_product_attributes_product_id ON product_attributes(product_id);
CREATE INDEX idx_product_attributes_attribute_name ON product_attributes(attribute_name);
```

Refresh the materialized view periodically:

```python
from sqlalchemy import text

async def refresh_materialized_views(db_manager):```

"""Refresh materialized views."""
async with db_manager.get_enhanced_session() as session:```

await session.execute(text('REFRESH MATERIALIZED VIEW product_attributes'))
await session.commit()
```
```
```

## Graph Database Optimization

When using graph queries for attributes, optimize your queries:

### Path Optimization

Define efficient traversal paths for attribute queries:

```python
async def find_objects_with_attribute_value(```

attribute_graph,
object_type: str,
attribute_type: str,
value: Any
```
) -> List[str]:```

"""
Find objects with a specific attribute value using an optimized graph query.
``````

```
```

This version uses a direct path query rather than multiple separate queries.
"""
# Build Cypher query for direct path matching
query = """
MATCH (o:MetaRecord {meta_type_id: $object_type})
MATCH (o)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->```

  (at:AttributeType {name: $attribute_type})
```
MATCH (a)-[:HAS_VALUE]->(v:Value {value: $value})
RETURN o.id AS object_id
"""
``````

```
```

params = {```

"object_type": object_type,
"attribute_type": attribute_type,
"value": value
```
}
``````

```
```

# Execute query
result = await attribute_graph.execute_query(query, params)
``````

```
```

return [record["object_id"] for record in result]
```
```

### Attribute Index Optimization

Ensure that your graph database has proper indexes for attribute queries:

```python
async def create_attribute_graph_indexes(graph_manager):```

"""Create indexes for attribute graph queries."""
# Create indexes for attribute nodes
await graph_manager.execute_query(```

"CREATE INDEX attribute_type_name IF NOT EXISTS FOR (at:AttributeType) ON (at.name)"
```
)
``````

```
```

# Create indexes for value nodes
await graph_manager.execute_query(```

"CREATE INDEX value_value IF NOT EXISTS FOR (v:Value) ON (v.value)"
```
)
``````

```
```

# Create indexes for meta record nodes
await graph_manager.execute_query(```

"CREATE INDEX meta_record_type_id IF NOT EXISTS FOR (m:MetaRecord) ON (m.meta_type_id)"
```
)
```
```

## API Performance Optimization

Optimize API endpoints for attribute and value operations:

### Pagination

Always implement pagination for list endpoints:

```python
@router.get(```

"/attributes",
response_model=PaginatedResponse[AttributeResponseDTO],
tags=["Attributes"]
```
)
async def list_attributes(```

page: int = Query(1, ge=1),
page_size: int = Query(20, ge=1, le=100),
context=Depends(get_context)
```
):```

# Paginated query implementation
# ...
```
```

### Response Filtering

Allow clients to specify which fields to include in responses:

```python
@router.get(```

"/attributes/{attribute_id}",
response_model=AttributeResponseDTO,
tags=["Attributes"]
```
)
async def get_attribute(```

attribute_id: str,
include_values: bool = Query(True),
context=Depends(get_context)
```
):```

# Implementation that checks include_values parameter
# ...
```
```

### Bulk Operations

Provide endpoints for bulk operations:

```python
@router.post(```

"/attributes/bulk",
response_model=List[AttributeResponseDTO],
tags=["Attributes"]
```
)
async def create_bulk_attributes(```

attributes: List[AttributeCreateDTO],
context=Depends(get_context)
```
):```

# Bulk creation implementation
# ...
```
```

## Memory Optimization

Optimize memory usage when working with large numbers of attributes and values:

### Lazy Loading

Implement lazy loading for attribute values:

```python
class AttributeWithLazyValues:```

"""Attribute class with lazy-loaded values."""
``````

```
```

def __init__(self, attribute: Attribute, db_manager: DBManager):```

self._attribute = attribute
self._db_manager = db_manager
self._values_loaded = False
self._values = None
```
``````

```
```

@property
async def values(self):```

"""Lazy-load values only when accessed."""
if not self._values_loaded:
    async with self._db_manager.get_enhanced_session() as session:
        # Load values
        self._values = await self._load_values(session)
        self._values_loaded = True
``````

```
```

return self._values
```
``````

```
```

async def _load_values(self, session):```

# Implementation to load values
# ...
```
```
```

### Streaming Results

For large result sets, use streaming responses:

```python
async def stream_attributes(attribute_repository, meta_record_id: str):```

"""Stream attributes for a meta record."""
async with attribute_repository.db_manager.get_enhanced_session() as session:```

# Get cursor for attributes
cursor = await session.execute(
    select(AttributeModel).where(
        AttributeModel.id.in_(
            select(attribute__meta.c.attribute_id).where(
                attribute__meta.c.meta_id == meta_record_id
            )
        )
    )
)
``````

```
```

# Yield attributes one by one
async for row in cursor:
    attribute = Attribute.from_orm(row[0])
    yield attribute
```
```
```

## Monitoring and Profiling

Implement monitoring to identify performance bottlenecks:

### Query Profiling

```python
from uno.monitoring import QueryProfiler

# Create profiler
profiler = QueryProfiler()

# Profile attribute operations
async def profile_attribute_operations():```

with profiler.profile("get_attributes_for_record"):```

attributes = await attribute_service.get_attributes_for_record("01H3ZEVKY6ZH3F41K5GS77PJ1Z")
```
``````

```
```

# Check profiling results
profile_data = profiler.get_profile("get_attributes_for_record")
print(f"Operation took {profile_data.duration_ms}ms")
``````

```
```

# Analyze slow queries
for query in profile_data.queries:```

if query.duration_ms > 100:  # Slow queries
    print(f"Slow query: {query.sql}")
    print(f"Parameters: {query.params}")
    print(f"Duration: {query.duration_ms}ms")
```
```
```

### Performance Metrics

Set up metrics collection for attribute and value operations:

```python
from uno.monitoring import MetricsCollector

# Create metrics collector
metrics = MetricsCollector()

# Register metrics
attributes_created = metrics.register_counter("attributes_created", "Number of attributes created")
attribute_query_time = metrics.register_histogram("attribute_query_time", "Time taken for attribute queries")

# Use in service methods
async def create_attribute_with_metrics(attribute_service, attribute, values):```

start_time = time.time()
result = await attribute_service.create_attribute(attribute, values)
query_time = time.time() - start_time
``````

```
```

# Update metrics
if result.is_ok():```

attributes_created.inc()
```
attribute_query_time.observe(query_time)
``````

```
```

return result
```
```

## Conclusion

By implementing these optimization strategies, you can significantly improve the performance of attribute and value operations in your UNO application. Choose the strategies that best fit your specific use cases and performance requirements.

Remember to measure performance before and after implementing optimizations to ensure they're having the desired effect.