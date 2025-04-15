# Queries Overview

The uno queries module provides a comprehensive system for building, executing, and optimizing database queries. This module is designed to work with PostgreSQL and takes advantage of its advanced features while providing a clean, type-safe API.

## Core Components

The queries module includes several key components:

### Filter System

The filter system allows for building complex query filters with a fluent API:

- **Filter**: Core class for defining query filters
- **FilterItem**: Individual filter condition
- **FilterManager**: Manages and combines filters for models
- **FilterConnection**: Type of connection between filters (AND/OR)

### Query Execution

The query execution system handles the execution of queries with optimizations:

- **QueryExecutor**: Executes queries with caching and optimization
- **OptimizedQuery**: Base class for optimized query building and execution
- **OptimizedModelQuery**: Model-specific query optimizations
- **QueryHints**: Hints for PostgreSQL query optimization

### Common Patterns

The common patterns system provides pre-built implementations of common query patterns:

- **CommonQueryPatterns**: Implementation of frequently used query patterns
- **QueryPattern**: Enum of common query patterns that can be optimized

### Batch Operations

The batch operations system provides efficient processing of large datasets:

- **BatchOperations**: High-level API for batch database operations
- **BatchProcessor**: Core engine for batch processing
- **BatchConfig**: Configuration for batch operations
- **BatchExecutionStrategy**: Strategies for executing batch operations

## Usage Examples

### Basic Filtering

```python
from uno.queries import Filter, FilterItem

# Create a filter
filter = Filter()
filter.add(FilterItem("name", "eq", "Test Product"))
filter.add(FilterItem("price", "gt", 100))

# Use with repository or query executor
products = await product_repository.list(filter=filter)
```

### Advanced Filtering

```python
from uno.queries import Filter, FilterItem, FilterConnection

# Create main filter
filter = Filter()

# Add simple condition
filter.add(FilterItem("category", "eq", "Electronics"))

# Create nested OR filter
or_filter = Filter(connection=FilterConnection.OR)
or_filter.add(FilterItem("brand", "eq", "Apple"))
or_filter.add(FilterItem("brand", "eq", "Samsung"))

# Add nested filter to main filter
filter.add(or_filter)

# Use with repository
products = await product_repository.list(filter=filter)
```

### Optimized Query Execution

```python
from uno.queries import OptimizedModelQuery, QueryHints

# Create optimized query
query = OptimizedModelQuery(```

model_class=Product,
use_cache=True,
cache_ttl=300,  # 5 minutes
```
)

# Build query with hints
select_query = query.build_select(```

where=Product.category == "Electronics",
order_by=[Product.price.desc()],
limit=10,
hints=QueryHints(```

parallel_workers=2,
work_mem="64MB",
```
),
```
)

# Execute query
result = await query.execute(select_query)
```

### Common Query Patterns

```python
from uno.queries import CommonQueryPatterns, QueryPattern

# Create common patterns instance
patterns = CommonQueryPatterns(```

model_class=Product,
use_cache=True,
collect_metrics=True,
```
)

# Use pre-built patterns
products = await patterns.find_by_field(```

field_name="category",
field_value="Electronics",
load_relations=["brand", "reviews"],
```
)

# Pagination
products, total_count, total_pages = await patterns.paginate(```

page=2,
page_size=20,
where=Product.is_active == True,
order_by=[Product.created_at.desc()],
```
)

# Full-text search
search_results = await patterns.fts_search(```

search_text="wireless headphones",
search_fields=["name", "description"],
limit=25,
```
)
```

### Batch Operations

```python
from uno.queries import BatchOperations, BatchConfig, BatchExecutionStrategy

# Create batch operations instance
batch_ops = BatchOperations(```

model_class=Product,
batch_config=BatchConfig(```

batch_size=500,
execution_strategy=BatchExecutionStrategy.CHUNKED,
```
),
```
)

# Batch insert
records = [```

{"name": f"Product {i}", "price": i * 10} 
for i in range(1, 1001)
```
]
inserted = await batch_ops.batch_insert(records)

# Batch update
updates = [```

{"id": i, "price": i * 12}  # 20% price increase
for i in range(1, 501)
```
]
updated = await batch_ops.batch_update(```

records=updates,
id_field="id",
fields_to_update=["price"],
```
)

# Batch delete
deleted = await batch_ops.batch_delete(```

id_values=list(range(501, 701)),
```
)
```

## Integration with Repository Pattern

The queries system integrates seamlessly with uno's repository pattern:

```python
from uno.domain.repository import UnoDBRepository

# Create repository with batch operations enabled
repo = UnoDBRepository(```

entity_type=Product,
use_batch_operations=True,
```
)

# Use batch operations through repository
products = await repo.batch_get(```

ids=["1", "2", "3", "4", "5"],
load_relations=["category"],
```
)

# Update products
for product in products:```

product.price *= 1.1  # 10% price increase
```

# Batch update
updated = await repo.batch_update(products)
```

## Performance Optimization

The queries module includes several performance optimizations:

### Query Caching

```python
# Enable caching
query = OptimizedModelQuery(```

model_class=Product,
use_cache=True,
cache_ttl=300,  # 5 minutes
```
)

# Cached query results
product = await query.get_by_id(1)
```

### Execution Strategies

```python
# Configure batch operations with different strategies
config_chunked = BatchConfig(```

execution_strategy=BatchExecutionStrategy.CHUNKED,
batch_size=500,
```
)

config_parallel = BatchConfig(```

execution_strategy=BatchExecutionStrategy.PARALLEL,
batch_size=500,
max_workers=4,
```
)

config_pipelined = BatchConfig(```

execution_strategy=BatchExecutionStrategy.PIPELINED,
pre_process_fn=validate_data,
post_process_fn=transform_results,
```
)
```

### Query Hints

```python
# Configure SQL query hints
hints = QueryHints(```

parallel_workers=4,
work_mem="128MB",
enable_seqscan=False,
use_hashjoin=True,
```
)

# Use with optimized query
query = query_builder.build_select(```

where=Product.category == "Electronics",
hints=hints,
```
)
```

## Related Documentation

<!-- TODO: Create filter manager documentation -->
<!-- - [Filter Manager](filter-manager.md): Detailed documentation on filter management -->
<!-- TODO: Create optimized queries documentation -->
<!-- - [Optimized Queries](optimized_queries.md): In-depth guide to query optimization -->
<!-- TODO: Create common patterns documentation -->
<!-- - [Common Query Patterns](common_patterns.md): Guide to pre-built query patterns -->
- [Batch Operations](batch_operations.md): Comprehensive guide to batch operations
- [Performance Optimization](/docs/performance/batch_operations.md): Performance tips

## Conclusion

The uno queries module provides a powerful, flexible, and efficient system for working with databases. By combining filtering, optimization, common patterns, and batch operations, it enables high-performance database access while maintaining a clean, type-safe API.