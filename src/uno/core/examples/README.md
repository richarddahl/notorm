# Uno Framework Examples

This directory contains example code demonstrating how to use various features of the Uno framework.

## Examples

### Batch Operations

The `batch_operations_example.py` file demonstrates how to use the batch operations system for efficient database operations:

- Different execution strategies (chunked, parallel, optimistic)
- Batch insert, get, update, delete operations
- Batch upsert for conflict handling
- Batch import for data import with validation
- Performance metrics collection

To run the example:

```bash
# Make sure you have Docker running
docker-compose up -d

# Run the example
python -m uno.core.examples.batch_operations_example
```

### Async Examples

The `async_example.py` file demonstrates Uno's async capabilities:

- Task management
- Concurrency control
- Context management
- Integration with other async systems

### Error Handling Examples

The `error_handling_example.py` file demonstrates Uno's error handling system:

- Using the Result type for error handling
- Error catalog for standardized errors
- Structured logging of errors
- Validation error handling

### Migration Examples

The `migration_example.py` file demonstrates Uno's migration system:

- Database schema migrations
- Data migrations
- Migration tracking and dependencies
- Reversible migrations

### Monitoring Examples

The `monitoring_example.py` file demonstrates Uno's monitoring capabilities:

- Health checks
- Metrics collection
- Tracing
- Event monitoring
- Integration with monitoring systems

### Plugin Examples

The `plugin_example.py` file demonstrates Uno's plugin system:

- Creating plugins
- Plugin discovery
- Plugin hooks
- Extension points

### Resource Examples

The `resource_example.py` file demonstrates Uno's resource management:

- Resource lifecycle management
- Resource monitoring
- Resource cleanup
- Resource pools