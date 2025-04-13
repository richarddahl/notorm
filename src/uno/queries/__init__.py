# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Query handling for the Uno framework.

This package provides utilities for building, executing, and optimizing database queries.
It includes several key components:

1. **Filter System**: Build complex query filters with a fluent API
2. **Query Execution**: Execute queries with caching and optimization
3. **Common Patterns**: Pre-built implementations of common query patterns
4. **Batch Operations**: Efficient processing of large datasets

Key classes:

- `Filter` and `FilterManager`: For building and managing complex query filters
- `QueryExecutor`: For executing queries with optimization
- `OptimizedQuery` and `OptimizedModelQuery`: For building optimized queries
- `CommonQueryPatterns`: For using pre-built query patterns
- `BatchOperations`: For efficient batch processing of database operations

Example usage:

```python
# Using batch operations
from uno.queries import BatchOperations, BatchConfig, BatchExecutionStrategy

batch_ops = BatchOperations(
    model_class=Product,
    batch_config=BatchConfig(
        batch_size=500,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
    ),
)

# Batch insert
records = [
    {"name": f"Product {i}", "price": i * 10} 
    for i in range(1, 1001)
]
inserted = await batch_ops.batch_insert(records)
```

See the documentation for more details on each component.
"""

from uno.queries.filter import Filter, FilterItem
from uno.queries.filter_manager import FilterManager, FilterConnection
from uno.queries.executor import QueryExecutor
from uno.queries.optimized_queries import OptimizedQuery, OptimizedModelQuery, QueryHints
from uno.queries.common_patterns import CommonQueryPatterns, QueryPattern
from uno.queries.batch_operations import (
    BatchOperations,
    BatchProcessor,
    BatchConfig,
    BatchExecutionStrategy,
    BatchSize,
    BatchMetrics,
)

__all__ = [
    # Filter
    'Filter',
    'FilterItem',
    'FilterManager',
    'FilterConnection',
    
    # Query Execution
    'QueryExecutor',
    
    # Optimized Queries
    'OptimizedQuery',
    'OptimizedModelQuery',
    'QueryHints',
    'CommonQueryPatterns',
    'QueryPattern',
    
    # Batch Operations
    'BatchOperations',
    'BatchProcessor',
    'BatchConfig',
    'BatchExecutionStrategy',
    'BatchSize',
    'BatchMetrics',
]