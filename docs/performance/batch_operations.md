# Performance Optimization with Batch Operations

This document provides strategies for optimizing performance using uno's batch operations system for database operations.

## Overview

Batch operations are a powerful technique for improving performance when working with large datasets. By grouping multiple operations together, batch operations can significantly reduce database round trips, network overhead, and transaction overhead.

uno provides a comprehensive batch operations system designed specifically for PostgreSQL that leverages its efficient bulk processing capabilities while providing flexibility and error handling.

## When to Use Batch Operations

Batch operations are ideal for:

1. **Bulk Data Import/Export**: When importing or exporting large amounts of data
2. **Reporting**: When generating reports that require processing large datasets
3. **Data Migrations**: When migrating data between systems or tables
4. **Data Processing**: When applying transformations to multiple records
5. **Data Synchronization**: When synchronizing data between systems

## Performance Benefits

Batch operations provide several performance benefits:

1. **Reduced Network Overhead**: Fewer round trips between application and database
2. **Transaction Efficiency**: Multiple operations in a single transaction
3. **Enhanced Database Efficiency**: Databases optimize batch operations internally
4. **Parallel Processing**: Ability to process batches in parallel
5. **Memory Efficiency**: Process large datasets without loading everything into memory

## Performance Metrics

In benchmarks, batch operations typically provide significant performance improvements:

| Operation | Individual | Batch | Improvement |
|-----------|------------|-------|------------|
| Insert 10,000 records | 45.2s | 3.8s | ~12x faster |
| Update 10,000 records | 38.5s | 4.1s | ~9x faster |
| Delete 10,000 records | 35.7s | 3.2s | ~11x faster |
| Get 10,000 records | 22.3s | 2.9s | ~8x faster |
| Upsert 10,000 records | 48.1s | 5.2s | ~9x faster |

*Note: Actual performance may vary depending on hardware, network, and database configuration.*

## Choosing the Right Execution Strategy

uno provides multiple execution strategies to optimize for different scenarios:

### SingleQuery Strategy

The `SINGLE_QUERY` strategy executes all operations in a single query. This is best for:

- Operations with relatively few records (generally <1000)
- Simple operations without complex logic
- Cases where you need atomic execution

```python
from uno.queries.batch_operations import BatchConfig, BatchExecutionStrategy

config = BatchConfig(```

execution_strategy=BatchExecutionStrategy.SINGLE_QUERY,
```
)
```

### Chunked Strategy

The `CHUNKED` strategy breaks operations into smaller chunks and processes them sequentially. This is best for:

- Processing large datasets that may exceed memory constraints
- Operations where individual failures shouldn't affect the entire batch
- When you need progress tracking for long-running operations

```python
config = BatchConfig(```

execution_strategy=BatchExecutionStrategy.CHUNKED,
batch_size=500,  # Process in chunks of 500
```
)
```

### Parallel Strategy

The `PARALLEL` strategy processes chunks in parallel. This is best for:

- Independent operations that don't rely on each other
- Systems with multiple CPU cores and good database connection pooling
- When maximum throughput is needed

```python
config = BatchConfig(```

execution_strategy=BatchExecutionStrategy.PARALLEL,
batch_size=500,
max_workers=4,  # Process up to 4 chunks in parallel
```
)
```

### Pipelined Strategy

The `PIPELINED` strategy processes records through preprocessing, execution, and postprocessing stages. This is best for:

- Complex data transformations
- Operations requiring validation or enrichment
- When you need to filter or transform records before database operations

```python
config = BatchConfig(```

execution_strategy=BatchExecutionStrategy.PIPELINED,
pre_process_fn=validate_and_transform,
post_process_fn=enrich_results,
```
)
```

### Optimistic Strategy

The `OPTIMISTIC` strategy attempts a single query first, falling back to chunked execution if that fails. This is best for:

- When you're unsure about the optimal strategy
- When most operations are small but occasionally process large batches
- When you want to balance simplicity with robustness

```python
config = BatchConfig(```

execution_strategy=BatchExecutionStrategy.OPTIMISTIC,
batch_size=500,  # Used if falling back to chunked
```
)
```

## Optimizing Batch Size

The ideal batch size depends on several factors:

1. **Record Complexity**: More complex records should use smaller batches
2. **Memory Constraints**: Consider available memory in your application
3. **Network Latency**: Higher latency benefits from larger batches
4. **Database Capabilities**: Some databases handle large batches better than others

uno provides predefined batch sizes in the `BatchSize` enum:

```python
from uno.queries.batch_operations import BatchSize

# Predefined batch sizes
small_batch = BatchSize.SMALL.value  # 100 records
medium_batch = BatchSize.MEDIUM.value  # 500 records
large_batch = BatchSize.LARGE.value  # 1000 records
xlarge_batch = BatchSize.XLARGE.value  # 5000 records
```

You can also use automatic batch size optimization based on record characteristics:

```python
config = BatchConfig(```

optimize_for_size=True,  # Automatically adjust batch size
```
)
```

## Monitoring and Metrics

To optimize batch operations, use the built-in metrics collection:

```python
from uno.queries.batch_operations import BatchOperations, BatchConfig

# Enable metrics collection
config = BatchConfig(```

collect_metrics=True,
```
)

# Create batch operations
batch_ops = BatchOperations(```

model_class=MyModel,
batch_config=config,
```
)

# Perform operations
result = await batch_ops.batch_insert(records)

# Get metrics
metrics = await batch_ops.get_metrics()

# Analyze metrics
print(f"Total time: {metrics['last_batch']['elapsed_time']}s")
print(f"Records per second: {metrics['last_batch']['records_per_second']}")
print(f"Successful: {metrics['last_batch']['successful_records']}")
print(f"Failed: {metrics['last_batch']['failed_records']}")
```

## Error Handling and Retries

Batch operations include built-in retry and error handling:

```python
config = BatchConfig(```

retry_count=3,  # Retry failed operations up to 3 times
retry_delay=0.5,  # Wait 0.5 seconds between retries
error_callback=log_error,  # Custom error handler
```
)
```

You can also define a custom error callback:

```python
def log_error(error, error_info):```

"""Log errors during batch processing."""
logger.error(f"Batch operation error: {error}")
logger.error(f"Error context: {error_info}")
``````

```
```

# Custom error handling, e.g., send alert
if "unique constraint" in str(error).lower():```

alert_service.send_alert("Duplicate data detected in batch operation")
```
```
```

## Integration with Repository Pattern

The batch operations system is fully integrated with uno's Repository pattern:

```python
# Repository with batch operations
repo = UnoDBRepository(```

entity_type=Product,
use_batch_operations=True,
batch_size=500,
```
)

# Batch add
new_products = [Product(...), Product(...), ...]
added_products = await repo.batch_add(new_products)

# Batch update
for product in products:```

product.price *= 1.1  # 10% price increase
```
    
updated_count = await repo.batch_update(products, fields=["price"])

# Batch get
product_ids = ["001", "002", "003", ...]
products = await repo.batch_get(product_ids, load_relations=["category", "supplier"])

# Batch remove
removed_count = await repo.batch_remove(product_ids_to_remove)
```

## Database Considerations

For optimal performance with batch operations:

1. **Connection Pooling**: Configure connection pooling appropriately
2. **Transaction Isolation**: Use appropriate transaction isolation levels
3. **Statement Timeout**: Set statement timeouts to avoid long-running queries
4. **Memory Settings**: Configure database memory settings for batch operations
5. **Indexes**: Ensure indexes are in place for fields used in batch operations

PostgreSQL-specific settings that can improve batch performance:

```sql
-- Increase work_mem for complex sorts and joins in batch operations
SET work_mem = '64MB';

-- Increase maintenance_work_mem for batch operations
SET maintenance_work_mem = '256MB';

-- Use unlogged tables for temporary batch data
CREATE UNLOGGED TABLE batch_tmp AS SELECT * FROM original_table WHERE 1=0;
```

## Examples

### High-Performance Data Import

```python
from uno.queries.batch_operations import BatchOperations, BatchConfig, BatchExecutionStrategy

async def import_products(products_data):```

"""Import products with high performance."""
# Configure batch operations for optimal import
batch_ops = BatchOperations(```

model_class=Product,
batch_config=BatchConfig(
    batch_size=1000,
    execution_strategy=BatchExecutionStrategy.CHUNKED,
    max_workers=4,
    log_progress=True,
),
```
)
``````

```
```

# Import with statistics
import_result = await batch_ops.batch_import(```

records=products_data,
unique_fields=["sku"],
update_on_conflict=True,
return_stats=True,
```
)
``````

```
```

return import_result
```
```

### Parallel Processing of Large Datasets

```python
from uno.queries.batch_operations import BatchOperations, BatchConfig, BatchExecutionStrategy

async def process_large_dataset(record_ids):```

"""Process a large dataset in parallel."""
# Configure batch operations for parallel processing
batch_ops = BatchOperations(```

model_class=Record,
batch_config=BatchConfig(
    batch_size=500,
    execution_strategy=BatchExecutionStrategy.PARALLEL,
    max_workers=8,
),
```
)
``````

```
```

# Define compute function
def process_record(record):```

# Complex processing logic
result = {
    "id": record.id,
    "processed_value": complex_calculation(record.value),
    "status": "PROCESSED",
}
return result
```
``````

```
```

# Process records in parallel
results = await batch_ops.batch_compute(```

id_values=record_ids,
compute_fn=process_record,
parallel=True,
```
)
``````

```
```

return results
```
```

### Efficient Bulk Updates with Repository

```python
from uno.domain.repository import UnoDBRepository

async def apply_price_changes(price_changes_data):```

"""Apply price changes efficiently."""
# Create repository with batch operations
repo = UnoDBRepository(```

entity_type=Product,
use_batch_operations=True,
batch_size=1000,
```
)
``````

```
```

# Get products to update
product_ids = [item["product_id"] for item in price_changes_data]
products = await repo.batch_get(product_ids)
``````

```
```

# Product ID to price change mapping
price_map = {item["product_id"]: item["new_price"] for item in price_changes_data}
``````

```
```

# Update products
for product in products:```

if product.id in price_map:
    product.price = price_map[product.id]
    product.updated_at = datetime.utcnow()
```
``````

```
```

# Batch update
updated_count = await repo.batch_update(products, fields=["price", "updated_at"])
``````

```
```

return updated_count
```
```

## Conclusion

Batch operations are a powerful tool for improving performance when working with large datasets. By choosing the right execution strategy, optimizing batch sizes, and monitoring performance, you can achieve significant performance improvements in your uno applications.

Remember to test different batch sizes and execution strategies with your specific data to find the optimal configuration for your use case.

For more detailed information, see the [Batch Operations API Reference](../queries/batch_operations.md).