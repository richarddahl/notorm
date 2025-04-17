# Batch Operations

uno provides powerful batch operations for efficiently processing large amounts of data with PostgreSQL. These batch operations optimize database interactions, minimize round trips, and maximize throughput.

## Overview

The batch operations system in uno consists of two main components:

1. **BatchProcessor**: The core engine that handles batch processing with different execution strategies
2. **BatchOperations**: High-level API for performing batch operations on database entities

These components work together to provide efficient batch processing capabilities that are fully integrated with uno's repository pattern.

## Key Features

- **Multiple Execution Strategies**:
  - **Single Query**: Execute the operation as a single query for all records
  - **Chunked**: Split records into chunks and process each chunk sequentially
  - **Parallel**: Process chunks in parallel for maximum throughput
  - **Pipelined**: Process records through preprocessing, execution, and postprocessing stages
  - **Optimistic**: Try a single query first, fall back to chunking if that fails

- **Automatic Optimization**:
  - Automatically determines optimal batch sizes based on record complexity
  - Configurable parallelism levels
  - Comprehensive metrics collection

- **Error Handling**:
  - Built-in retry mechanism with configurable count and delay
  - Detailed error tracking
  - Fallback mechanisms

- **Performance Monitoring**:
  - Collects detailed metrics on operations
  - Tracks execution time, success rates, and throughput
  - Optimization recommendations

## Usage in Repositories

The batch operations system is fully integrated with uno's repository pattern. The `UnoDBRepository` class provides batch methods that can be used directly:

```python
# Initialize repository with batch operations enabled
repo = UnoDBRepository(```

entity_type=MyEntity,
use_batch_operations=True,
batch_size=500,  # Default batch size
```
)

# Batch get entities
entities = await repo.batch_get(```

ids=["1", "2", "3", "4", "5"],
load_relations=["related_items"],
parallel=True,
```
)

# Batch add entities
new_entities = [MyEntity(...), MyEntity(...), MyEntity(...)]
added_entities = await repo.batch_add(new_entities)

# Batch update entities
for entity in entities:```

entity.name = f"Updated {entity.name}"
```
updated_count = await repo.batch_update(entities, fields=["name"])

# Batch remove entities
removed_count = await repo.batch_remove(["1", "2", "3"])
```

## Direct API Usage

For more control, you can use the `BatchOperations` class directly:

```python
from uno.queries.batch_operations import BatchOperations, BatchConfig, BatchExecutionStrategy

# Create batch operations instance
batch_ops = BatchOperations(```

model_class=MyModel,
session=session,
batch_config=BatchConfig(```

batch_size=1000,
execution_strategy=BatchExecutionStrategy.PARALLEL,
max_workers=4,
collect_metrics=True,
```
),
```
)

# Perform batch operations
result = await batch_ops.batch_upsert(```

records=[{'id': 1, 'name': 'Record 1'}, {'id': 2, 'name': 'Record 2'}],
constraint_columns=['id'],
return_models=True,
```
)

# Get metrics
metrics = await batch_ops.get_metrics()
```

## Configuration Options

Batch operations can be configured using the `BatchConfig` class:

```python
from uno.queries.batch_operations import BatchConfig, BatchExecutionStrategy, BatchSize

# Configure batch operations
config = BatchConfig(```

# Size of each batch
batch_size=BatchSize.MEDIUM.value,  # Or use explicit value like 500
``````

```
```

# Maximum number of parallel workers
max_workers=4,
``````

```
```

# Whether to collect metrics
collect_metrics=True,
``````

```
```

# Whether to log progress
log_progress=True,
``````

```
```

# Timeout for operations in seconds
timeout=60.0,
``````

```
```

# Retry count for failed operations
retry_count=3,
``````

```
```

# Delay between retries in seconds
retry_delay=0.5,
``````

```
```

# Execution strategy
execution_strategy=BatchExecutionStrategy.CHUNKED,
``````

```
```

# Functions for pre/post-processing
pre_process_fn=None,
post_process_fn=None,
``````

```
```

# Error callback function
error_callback=None,
``````

```
```

# Automatically optimize batch size based on record size
optimize_for_size=True,
```
)
```

## Available Batch Operations

The following batch operations are available:

### Record Operations

- **batch_get**: Retrieve multiple records by ID
- **batch_insert**: Insert multiple records
- **batch_update**: Update multiple records
- **batch_upsert**: Insert or update multiple records
- **batch_delete**: Delete multiple records

### Advanced Operations

- **batch_compute**: Apply a computation function to multiple records
- **batch_execute_sql**: Execute raw SQL for multiple parameter sets
- **batch_import**: Import data with duplicate handling

## Performance Considerations

- Use `parallel=True` for operations that don't depend on each other
- For very large datasets, use chunked execution to avoid memory issues
- Monitor metrics to identify optimization opportunities
- Use appropriate batch sizes:
  - Small batches (50-100) for complex records
  - Medium batches (500-1000) for most operations
  - Large batches (1000-5000) for simple records

## Integration with Caching

Batch operations integrate with uno's caching system:

- Read operations (like `batch_get`) can use cache
- Write operations (like `batch_update`) will invalidate cache entries
- Cache usage is configurable per operation

## Example: Importing Large Datasets

Here's an example of importing a large dataset efficiently:

```python
from uno.queries.batch_operations import BatchOperations, BatchConfig, BatchExecutionStrategy

# Configure batch operations for import
batch_ops = BatchOperations(```

model_class=Product,
batch_config=BatchConfig(```

batch_size=1000,
execution_strategy=BatchExecutionStrategy.CHUNKED,
max_workers=4,
optimize_for_size=True,
```
),
```
)

# Define preprocessing function
def preprocess_product(record):```

# Clean and validate data
if not record.get('name'):```

return None  # Skip invalid records
```
``````

```
```

# Transform data as needed
record['name'] = record['name'].strip()
record['price'] = float(record['price'])
return record
```

# Import products
import_stats = await batch_ops.batch_import(```

records=product_data,  # Large list of product records
unique_fields=['sku'],
update_on_conflict=True,
pre_process_fn=preprocess_product,
return_stats=True,
```
)

print(f"Imported {import_stats['inserted']} products, updated {import_stats['updated']}")
```

## Example: Batch Processing with Repository

Here's an example of using batch operations through the repository pattern:

```python
from uno.domain.repository import UnoDBRepository

# Create repository with batch operations enabled
repo = UnoDBRepository(```

entity_type=Order,
use_batch_operations=True,
batch_size=500,
```
)

# Get orders that need processing
pending_orders = await repo.list(```

filters={'status': 'pending'},
limit=1000,
```
)

# Process orders in batch
for order in pending_orders:```

order.status = 'processing'
order.updated_at = datetime.now(datetime.UTC)
```

# Update all orders in a single batch operation
updated = await repo.batch_update(pending_orders)
print(f"Updated {updated} orders")
```

## Fallback Behavior

If batch operations are disabled or encounter critical errors, the repository will automatically fall back to individual operations:

```python
# Even if batch operations are disabled
repo = UnoDBRepository(entity_type=Product, use_batch_operations=False)

# batch_add will still work, but will use individual add() calls internally
products = await repo.batch_add(product_entities)
```

## Optimizing for Best Performance

To get the best performance from batch operations:

1. Choose the right execution strategy for your use case
2. Use appropriate batch sizes (test different sizes for your specific data)
3. Enable parallelism when operations are independent
4. Use metrics to identify bottlenecks
5. Consider adding indexes on fields used in batch operations
6. Consider using `pipelined` strategy for complex data transformations