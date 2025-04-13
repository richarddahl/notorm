# Performance Benchmarks

This directory contains performance benchmark tests for various modules in the Uno framework.

## Running the Benchmarks

To run the benchmarks, use the following command:

```bash
hatch run test:benchmark
```

Or manually with pytest:

```bash
pytest tests/benchmarks --run-benchmark
```

To run only specific benchmark files:

```bash
# Vector search benchmarks
pytest tests/benchmarks/test_vector_search_performance.py --run-benchmark

# Reports module benchmarks
pytest tests/benchmarks/test_report_performance.py --run-benchmark

# Attributes module benchmarks
pytest tests/benchmarks/test_attributes_performance.py --run-benchmark

# Values module benchmarks
pytest tests/benchmarks/test_values_performance.py --run-benchmark

# Authorization module benchmarks
pytest tests/benchmarks/test_authorization_performance.py --run-benchmark

# Database module benchmarks
pytest tests/benchmarks/test_database_performance.py --run-benchmark

# Queries module benchmarks
pytest tests/benchmarks/test_queries_performance.py --run-benchmark

# Workflows module benchmarks
pytest tests/benchmarks/test_workflows_performance.py --run-benchmark

# Caching module benchmarks
pytest tests/benchmarks/test_caching_performance.py --run-benchmark

# API module benchmarks
pytest tests/benchmarks/test_api_performance.py --run-benchmark

# Dependency Injection benchmarks
pytest tests/benchmarks/test_dependency_injection_performance.py --run-benchmark

# Integration benchmarks
pytest tests/benchmarks/test_integration_performance.py --run-benchmark
```

## Available Benchmarks

### Vector Search

- **Small Dataset**: Measures search performance with 100 documents
- **Medium Dataset**: Measures search performance with 1,000 documents
- **Large Dataset**: Measures search performance with 5,000 documents
- **Limit Variations**: Compares search performance with different result limits
- **Hybrid Search**: Measures combined vector-graph search performance
- **RAG Context Retrieval**: Measures performance of context retrieval for RAG
- **Embedding Generation**: Measures performance of generating embeddings for different text lengths

### Reports Module

- **Template Creation**: Measures performance of creating report templates with different field counts
- **Template Querying**: Measures performance of different template query operations
- **Trigger Processing**: Measures performance of processing report triggers with different batch sizes
- **Report Execution**: Measures performance of report execution with different template sizes
- **Field Updates**: Measures performance of updating fields in templates with different field counts
- **Recent Executions Query**: Measures performance of querying recent executions with different limits
- **Relationship Queries**: Measures performance of querying executions with relationships

### Attributes Module

- **Attribute Type Creation**: Measures performance of creating attribute types
- **Attribute Type Querying**: Measures performance of different attribute type query operations
- **Attribute Creation**: Measures performance of creating attributes
- **Attribute Querying**: Measures performance of querying attributes by type
- **Attribute Type Hierarchy**: Measures performance of retrieving attribute type hierarchies of different depths
- **Relationship Loading**: Measures performance of loading attributes with all relationships
- **Batch Attribute Creation**: Measures performance of creating attributes in batches of different sizes
- **Value Addition**: Measures performance of adding values to attributes

### Values Module

- **Value Creation**: Measures performance of creating different types of values (text, integer, decimal, etc.)
- **Value Querying**: Measures performance of finding values by name and value
- **Text Search**: Measures performance of text search operations with different term lengths
- **Batch Value Creation**: Measures performance of creating values in batches of different sizes
- **Value Listing**: Measures performance of listing values with different filters and limits
- **Value Validation**: Measures performance of validating different types of values

### Authorization Module

- **User Creation**: Measures performance of creating user entities
- **Permission Checking**: Measures performance of checking if a user has a specific permission
- **Role Assignment**: Measures performance of assigning roles to users
- **Role Permission Querying**: Measures performance of querying permissions for a role
- **User-Tenant Querying**: Measures performance of querying users by tenant
- **Tenant Relationship Loading**: Measures performance of loading tenant relationships
- **User-Role Querying**: Measures performance of finding users by role
- **Role Permission Validation**: Measures performance of checking if a role has a permission

### Database Module

- **Connection Establishment**: Measures performance of establishing database connections
- **Session Creation**: Measures performance of creating database sessions
- **Session Context**: Measures performance of using session context managers
- **Query Performance by Size**: Measures query performance on different dataset sizes
- **Transaction Performance**: Compares single vs. batch insert transaction performance
- **Query with Filters**: Measures performance of different query filter types
- **Connection Pooling**: Measures connection pooling performance at various concurrency levels
- **Index Usage**: Compares query performance with and without indexes
- **DB Manager Operations**: Measures performance of database management operations

### Queries Module

- **Filter Manager Creation**: Measures performance of creating filter managers
- **Query Execution**: Measures performance of executing queries of different complexities
- **Match Checking**: Measures performance of checking if entities match query criteria
- **Query Counting**: Measures performance of counting query results
- **Cached Query Performance**: Compares performance of cached vs. uncached queries
- **Filter Validation**: Measures performance of validating filter configurations

### Workflows Module

- **Event Processing**: Measures performance of processing events through the workflow engine
- **Condition Evaluation**: Measures performance of evaluating conditions of different complexities
- **Action Execution**: Measures performance of executing workflow actions
- **Field Path Resolution**: Measures performance of resolving field paths in event data
- **Concurrent Event Processing**: Measures performance of processing multiple events concurrently
- **Recipient Resolution**: Measures performance of resolving different types of recipients

### Caching Module

- **Key Generation**: Measures performance of generating cache keys for different data types
- **Get/Set Operations**: Measures performance of basic cache operations with different data sizes
- **Hit/Miss Performance**: Compares performance between cache hits and misses
- **Decorator Overhead**: Measures the overhead of using @cached and @async_cached decorators
- **Invalidation Strategies**: Compares performance of different cache invalidation approaches
- **Multi-level Caching**: Measures performance across local and distributed cache layers
- **Serialization/Deserialization**: Measures performance of transforming data for caching
- **Async Operations**: Measures performance of asynchronous cache access patterns
- **Concurrency Performance**: Measures cache behavior under concurrent access
- **Monitoring Overhead**: Measures the impact of cache monitoring on performance
- **Bulk Operations**: Compares batch operations versus individual operations

### API Module

- **Endpoint Creation**: Measures performance of creating API endpoints
- **Endpoint Factory**: Measures performance of generating endpoints using the factory pattern
- **API Initialization**: Measures performance of initializing an API with multiple endpoints
- **Request Validation**: Measures performance of validating incoming request data
- **Response Serialization**: Measures performance of serializing different response sizes
- **CRUD Operations**: Measures performance of standard Create/Read/Update/Delete operations
- **Error Handling**: Measures performance of API error handling mechanisms
- **Middleware Processing**: Measures performance impact of different middleware configurations
- **Handler Execution**: Measures performance of different API handler execution patterns
- **API Registry Lookups**: Measures performance of API registry operations
- **Dependency Resolution**: Measures performance of resolving dependencies in API routes
- **Concurrent Request Handling**: Measures performance under concurrent API requests
- **Data Transformation**: Measures performance of data transformation between models

### Dependency Injection Module

- **Service Registration**: Measures performance of registering services with different lifetimes
- **Service Resolution**: Measures performance of resolving singleton, scoped, and transient services
- **Dependency Chain Resolution**: Measures performance impact of deep dependency chains
- **Scope Creation**: Measures performance of creating and using dependency scopes
- **Async Scope Management**: Measures performance of asynchronous scope operations
- **Decorator Injection**: Measures overhead of decorator-based dependency injection
- **Async Injection**: Measures performance of asynchronous function injection
- **Global Service Access**: Measures performance of global service resolution
- **Lifecycle Hooks**: Measures performance of service initialization and disposal
- **Concurrent Resolution**: Measures service resolution under concurrent workloads
- **Collection Operations**: Measures performance of collection cloning and merging
- **Testing Container**: Measures performance of test container setup and usage
- **Dynamic Resolution**: Measures performance of runtime type resolution
- **Factory Resolution**: Measures performance of factory-based service instantiation

### Integration Benchmarks

- **User-Attribute-Values Flow**: Measures performance of user permission checks followed by attribute and value loading
- **Query-Workflow Trigger Flow**: Measures performance of executing queries and processing results through workflows
- **Attribute Change Permission Flow**: Measures performance of attribute updates with permission checks and event processing
- **Concurrent Integrated Operations**: Measures performance under load with multiple operations across modules happening concurrently
- **Complex Business Process Flow**: Measures end-to-end performance of a complex business process spanning multiple modules
- **Authorization-Attribute Filtering Flow**: Measures performance of applying permission-based filters to attribute queries

## Benchmark Environment

The benchmarks create a dedicated table in the database with appropriate indexes and test data. This allows measuring performance in isolation without affecting other tests or the application data.

## Interpreting Results

The benchmark results will show:

- **Mean time**: Average execution time
- **Min time**: Minimum execution time
- **Max time**: Maximum execution time
- **StdDev**: Standard deviation of execution times
- **Median time**: Median execution time

Pay special attention to the mean and median times, as they represent the typical performance a user might experience.

## Best Practices

1. **Run in Isolation**: For accurate results, run benchmarks in a clean environment without other processes competing for resources

2. **Run Multiple Times**: Run benchmarks multiple times to ensure consistent results

3. **Test After Changes**: Run benchmarks after making changes to vector search functionality to detect performance regressions

4. **Scale Testing**: Test with different dataset sizes to understand scaling behavior

5. **Profile Bottlenecks**: Use profiling tools to identify bottlenecks in poorly performing areas