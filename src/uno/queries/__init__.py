# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Query handling for the Uno framework.

This package provides utilities for building, executing, and optimizing database queries
following domain-driven design principles. It includes several key components:

1. **Domain Entities**: Core domain entities (Query, QueryPath, QueryValue)
2. **Repositories**: Data access for query entities using Repository pattern
3. **Services**: Business logic for query operations
4. **DTOs**: Data Transfer Objects for API serialization
5. **Schema Managers**: Entity-DTO conversion
6. **API Integration**: REST API endpoints for querying
7. **Filter System**: Build complex query filters
8. **Query Execution**: Execute queries with caching and optimization
9. **Batch Operations**: Efficient processing of large datasets

Example usage:

```python
# Using domain-driven API integration
from fastapi import FastAPI
from uno.queries import register_query_endpoints

app = FastAPI()

# Register query endpoints
endpoints = register_query_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    dependencies=None,
    include_auth=True,
)

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

# Domain entities
from uno.queries.entities import Query, QueryPath, QueryValue

# Domain repositories
from uno.queries.domain_repositories import (
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)

# Domain services
from uno.queries.domain_services import (
    QueryPathService,
    QueryValueService,
    QueryService,
)

# DTOs
from uno.queries.dtos import (
    QueryPathCreateDto,
    QueryPathViewDto,
    QueryPathUpdateDto,
    QueryValueCreateDto,
    QueryValueViewDto,
    QueryValueUpdateDto,
    QueryCreateDto,
    QueryViewDto,
    QueryUpdateDto,
    QueryExecuteDto,
    QueryExecuteResultDto,
)

# Schema managers
from uno.queries.schemas import (
    QueryPathSchemaManager,
    QueryValueSchemaManager,
    QuerySchemaManager,
)

# API integration
from uno.queries.api_integration import register_query_endpoints

# Filter system
from uno.queries.filter import Filter, FilterItem
from uno.queries.filter_manager import FilterManager, FilterConnection

# Query execution
from uno.queries.executor import QueryExecutor
from uno.queries.optimized_queries import OptimizedQuery, OptimizedModelQuery, QueryHints
from uno.queries.common_patterns import CommonQueryPatterns, QueryPattern

# Batch operations
from uno.queries.batch_operations import (
    BatchOperations,
    BatchProcessor,
    BatchConfig,
    BatchExecutionStrategy,
    BatchSize,
    BatchMetrics,
)

# Error types
from uno.queries.errors import (
    QueryErrorCode,
    QueryExecutionError,
    QueryNotFoundError,
    QueryInvalidDataError,
    QueryPathError,
    QueryValueError,
    FilterError,
    register_query_errors,
)

# Register error codes in the catalog
register_query_errors()

__all__ = [
    # Domain Entities
    'Query',
    'QueryPath',
    'QueryValue',
    
    # Domain Repositories
    'QueryPathRepository',
    'QueryValueRepository',
    'QueryRepository',
    
    # Domain Services
    'QueryPathService',
    'QueryValueService',
    'QueryService',
    
    # DTOs
    'QueryPathCreateDto',
    'QueryPathViewDto',
    'QueryPathUpdateDto',
    'QueryValueCreateDto',
    'QueryValueViewDto',
    'QueryValueUpdateDto',
    'QueryCreateDto',
    'QueryViewDto',
    'QueryUpdateDto',
    'QueryExecuteDto',
    'QueryExecuteResultDto',
    
    # Schema Managers
    'QueryPathSchemaManager',
    'QueryValueSchemaManager',
    'QuerySchemaManager',
    
    # API Integration
    'register_query_endpoints',
    
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
    
    # Error types
    'QueryErrorCode',
    'QueryExecutionError',
    'QueryNotFoundError', 
    'QueryInvalidDataError',
    'QueryPathError',
    'QueryValueError',
    'FilterError',
]