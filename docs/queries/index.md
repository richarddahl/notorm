# Queries Module

The uno queries module provides a comprehensive system for building, executing, and optimizing database queries, with special support for batch operations.

## Overview

The queries module is designed to provide efficient database access with a clean, type-safe API. It takes advantage of PostgreSQL's advanced features while providing high-level abstractions for common database operations.

## Key Components

### Filtering System

- [Overview](overview.md) - Overview of the queries module
<!-- TODO: Create filter manager documentation -->
<!-- - [Filter Manager](filter-manager.md) - Managing complex query filters -->

### Query Optimization

<!-- TODO: Create optimized queries documentation -->
<!-- - [Optimized Queries](optimized_queries.md) - Building and executing optimized queries -->
<!-- TODO: Create common query patterns documentation -->
<!-- - [Common Query Patterns](common_patterns.md) - Pre-built implementations of common query patterns -->

### Batch Operations

- [Batch Operations](batch_operations.md) - Efficient processing of large datasets
- [Performance Optimization](/docs/performance/batch_operations.md) - Performance tips for batch operations

## Key Features

- **Type-safe Query Building**: Build queries with type checking to catch errors early
- **Query Optimization**: Automatic query optimization with PostgreSQL-specific hints
- **Efficient Filtering**: Flexible and powerful filtering system
- **Batch Operations**: High-performance batch processing of database operations
- **Caching Integration**: Seamless integration with uno's caching system
- **Repository Integration**: Clean integration with the Repository pattern

## Common Use Cases

- Building complex filters for database queries
- Optimizing queries for better performance
- Using pre-built patterns for common database operations
- Processing large datasets efficiently with batch operations
- Integrating with repositories for clean domain logic

## Getting Started

To start using the queries module, import the necessary components from `uno.queries`:

```python
from uno.queries import (```

# Filtering
Filter, FilterItem, FilterManager, FilterConnection,
``````

```
```

# Query Execution
QueryExecutor, OptimizedQuery, OptimizedModelQuery, QueryHints,
``````

```
```

# Common Patterns
CommonQueryPatterns, QueryPattern,
``````

```
```

# Batch Operations
BatchOperations, BatchConfig, BatchExecutionStrategy, BatchSize,
```
)
```

## Examples

### Basic Query Filtering

```python
filter = Filter()
filter.add(FilterItem("name", "contains", "Phone"))
filter.add(FilterItem("price", "lt", 1000))

products = await product_repository.list(filter=filter)
```

### Using Common Query Patterns

```python
patterns = CommonQueryPatterns(```

model_class=Product,
use_cache=True,
```
)

# Find products by category
products = await patterns.find_by_field(```

field_name="category",
field_value="Electronics",
```
)

# Paginate products
products, total_count, total_pages = await patterns.paginate(```

page=2,
page_size=20,
order_by=[Product.created_at.desc()],
```
)
```

### Batch Processing

```python
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
products = [```

{"name": f"Product {i}", "price": i * 10} 
for i in range(1, 1001)
```
]
inserted = await batch_ops.batch_insert(products)

# Batch update
updates = [```

{"id": i, "price": i * 12}
for i in range(1, 501)
```
]
updated = await batch_ops.batch_update(updates)
```

### Using Repository Batch Operations

```python
repo = UnoDBRepository(```

entity_type=Product,
use_batch_operations=True,
```
)

# Batch add products
products = [Product(...), Product(...), ...]
added_products = await repo.batch_add(products)

# Batch update products
for product in products:```

product.price *= 1.1  # 10% price increase
```
    
updated_count = await repo.batch_update(products)
```

## Next Steps

- Read the [Overview](overview.md) to understand the queries module architecture
- Learn about [Batch Operations](batch_operations.md) for efficient data processing
- Explore [Performance Optimization](/docs/performance/batch_operations.md) for best practices