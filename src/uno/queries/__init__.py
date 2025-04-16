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

# Using query service with dependency injection
from fastapi import FastAPI, Depends
from uno.queries.domain_provider import get_query_service
from uno.queries.domain_services import QueryService

app = FastAPI()

@app.get("/api/v1/queries/{query_id}/execute")
async def execute_query(
    query_id: str,
    query_service: QueryService = Depends(get_query_service),
):
    result = await query_service.execute_query(query_id)
    if result.is_failure:
        return {"error": str(result.error)}
    return {"results": result.value}

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

# Domain providers
from uno.queries.domain_provider import (
    get_query_path_service,
    get_query_value_service,
    get_query_service,
    get_queries_provider,
    setup_query_module,
)

# Domain endpoints (routers)
from uno.queries.domain_endpoints import (
    query_path_router,
    query_value_router,
    query_router,
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
from uno.queries.filter_manager import (
    UnoFilterManager,
    FilterManager,
    FilterConnection,
    get_filter_manager,
)

# Query execution
from uno.queries.executor import (
    QueryExecutor,
    get_query_executor,
    cache_query_result,
)
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

# Initialize the module
setup_query_module()

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
    
    # Domain Providers
    'get_query_path_service',
    'get_query_value_service',
    'get_query_service',
    'get_queries_provider',
    'setup_query_module',
    
    # Domain Endpoints
    'query_path_router',
    'query_value_router',
    'query_router',
    
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
    'UnoFilterManager',
    'FilterManager',
    'FilterConnection',
    'get_filter_manager',
    
    # Query Execution
    'QueryExecutor',
    'get_query_executor',
    'cache_query_result',
    
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