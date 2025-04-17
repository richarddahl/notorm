# CQRS and Read Model Performance Guidelines

This document provides comprehensive performance guidelines for the CQRS (Command Query Responsibility Segregation) pattern and Read Model approach in uno. It covers optimization techniques, scaling strategies, and best practices for achieving optimal performance in production environments.

## Table of Contents

1. [Command Side Optimizations](#command-side-optimizations)
2. [Query Side Optimizations](#query-side-optimizations)
3. [Read Model Optimizations](#read-model-optimizations)
4. [Event Store Optimizations](#event-store-optimizations)
5. [Caching Strategies](#caching-strategies)
6. [Database Optimizations](#database-optimizations)
7. [Scaling Strategies](#scaling-strategies)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Configuration Best Practices](#configuration-best-practices)
10. [Performance Testing](#performance-testing)

## Command Side Optimizations

### Command Validation

Efficient command validation is crucial for performance:

1. **Validate Early**: Validate commands before they enter the processing pipeline
   ```python
   # Early validation in API layer
   @router.post("/products")
   async def create_product(command: CreateProductCommand):
       # Validate before sending to command handler
       validation_result = await command_validator.validate(command)
       if not validation_result.is_valid:
           raise HTTPException(400, validation_result.errors)
       
       return await mediator.execute_command(command)
   ```

2. **Use Tiered Validation**: Separate validation into tiers:
   - **Schema validation**: Fast validation of data types and required fields
   - **Business rule validation**: More complex validation of business rules
   - **Consistency validation**: Validation against the current system state

3. **Batch Validation**: Validate multiple commands in a single operation
   ```python
   # Batch validation for multiple commands
   async def validate_batch(commands: List[Command]) -> Dict[int, List[str]]:
       errors = {}
       validation_tasks = [command_validator.validate(cmd) for cmd in commands]
       results = await asyncio.gather(*validation_tasks)
       
       for i, result in enumerate(results):
           if not result.is_valid:
               errors[i] = result.errors
       
       return errors
   ```

### Command Processing

Optimize command processing for throughput:

1. **Command Batching**: Process multiple commands in a single transaction
   ```python
   class BatchCommandHandler[TCommand](CommandHandler[List[TCommand], List[Any]]):
       async def handle(self, commands: List[TCommand]) -> Result[List[Any]]:
           async with self.unit_of_work_factory() as uow:
               results = []
               for command in commands:
                   result = await self._handle_single(command, uow)
                   results.append(result)
               await uow.commit()
               return Success(results)
   ```

2. **Concurrency Control**: Use optimistic concurrency control for better throughput
   ```python
   # Optimistic concurrency control
   async def update_aggregate(aggregate_id: str, version: int, update_fn):
       # Load the aggregate
       aggregate = await aggregate_repository.get_by_id(aggregate_id)
       
       # Check version
       if aggregate.version != version:
           raise ConcurrencyException(f"Aggregate version mismatch: expected {version}, got {aggregate.version}")
       
       # Apply update
       update_fn(aggregate)
       aggregate.version += 1
       
       # Save
       await aggregate_repository.save(aggregate)
   ```

3. **Command Priority**: Implement priority queues for commands
   ```python
   class PrioritizedCommandBus(CommandBus):
       def __init__(self):
           self.high_priority_queue = asyncio.Queue()
           self.normal_priority_queue = asyncio.Queue()
           self.low_priority_queue = asyncio.Queue()
       
       async def execute(self, command: Command, priority: Priority) -> Any:
           if priority == Priority.HIGH:
               await self.high_priority_queue.put(command)
           elif priority == Priority.NORMAL:
               await self.normal_priority_queue.put(command)
           else:
               await self.low_priority_queue.put(command)
   ```

### Command Handlers

Optimize command handlers for performance:

1. **Minimize Database Operations**: Reduce the number of database operations per command
   ```python
   # Bad: Multiple database operations
   async def handle_bad(self, command: UpdateProductCommand, uow: UnitOfWork) -> None:
       product = await uow.products.get_by_id(command.product_id)
       category = await uow.categories.get_by_id(command.category_id)
       product.update(command.name, command.price)
       product.category = category
       await uow.products.update(product)
   
   # Good: Fewer database operations
   async def handle_good(self, command: UpdateProductCommand, uow: UnitOfWork) -> None:
       product = await uow.products.get_by_id(command.product_id)
       product.update(command.name, command.price, command.category_id)
       await uow.products.update(product)
   ```

2. **Use Bulk Operations**: Use bulk operations for multiple updates
   ```python
   # Bulk update example
   async def handle_bulk_update(self, command: BulkUpdatePricesCommand, uow: UnitOfWork) -> None:
       # Single database operation for multiple updates
       await uow.products.bulk_update_prices(command.price_updates)
   ```

3. **Lazy Loading**: Use lazy loading for related entities
   ```python
   # Lazy loading example
   class Product:
       def __init__(self, id: str, name: str, category_id: str):
           self.id = id
           self.name = name
           self._category_id = category_id
           self._category = None
       
       @property
       async def category(self):
           if self._category is None:
               self._category = await category_repository.get_by_id(self._category_id)
           return self._category
   ```

## Query Side Optimizations

### Query Handlers

Optimize query handlers for read performance:

1. **Specialized Read Models**: Use specialized read models for specific query patterns
   ```python
   # Specialized read model for product listing
   class ProductListingReadModel(ReadModel):
       id: str
       name: str
       price: float
       category_name: str
       average_rating: float
   ```

2. **Projection Selection**: Only project the fields needed for the query
   ```python
   # Select only needed fields
   async def get_product_summary(self, product_id: str) -> Dict[str, Any]:
       query = (
           SelectBuilder()
           .select("id", "name", "price")
           .from_table("products")
           .where("id = ?")
           .bind_params([product_id])
       )
       result = await self.db.execute_query(*self.emitter.emit(query))
       return result[0] if result else None
   ```

3. **Pagination**: Always use pagination for large result sets
   ```python
   class PaginatedProductQueryHandler(QueryHandler[PaginatedProductsQuery, PaginatedResult[Product]]):
       async def handle(self, query: PaginatedProductsQuery) -> Result[PaginatedResult[Product]]:
           # Get total count
           count_query = f"SELECT COUNT(*) FROM products WHERE category = $1"
           count_result = await self.db.execute_query(count_query, [query.category])
           total = count_result[0]['count']
           
           # Get paginated results
           offset = (query.page - 1) * query.page_size
           products_query = f"""
               SELECT * FROM products 
               WHERE category = $1 
               ORDER BY name 
               LIMIT $2 OFFSET $3
           """
           products = await self.db.execute_query(
               products_query, 
               [query.category, query.page_size, offset]
           )
           
           return Success(PaginatedResult(
               items=[Product.from_dict(p) for p in products],
               total=total,
               page=query.page,
               page_size=query.page_size
           ))
   ```

### Query Optimization

Techniques for optimizing query performance:

1. **Query Caching**: Cache frequently used queries
   ```python
   class CachedQueryHandler[TQuery, TResult](QueryHandler[TQuery, TResult]):
       def __init__(self, cache_service: CacheService, ttl_seconds: int = 300):
           self.cache_service = cache_service
           self.ttl_seconds = ttl_seconds
       
       async def handle(self, query: TQuery) -> Result[TResult]:
           # Try to get from cache
           cache_key = self._get_cache_key(query)
           cached_result = await self.cache_service.get(cache_key)
           
           if cached_result:
               return Success(cached_result)
           
           # Get fresh result
           result = await self._handle(query)
           
           # Cache result
           if result.is_success():
               await self.cache_service.set(cache_key, result.value, self.ttl_seconds)
           
           return result
   ```

2. **Query Hints**: Use database query hints for complex queries
   ```python
   # Using PostgreSQL query hints
   async def get_products_with_hint(self, category: str) -> List[Dict[str, Any]]:
       query = """
       SELECT /*+ IndexScan(products products_category_idx) */
       * FROM products 
       WHERE category = $1
       """
       return await self.db.execute_query(query, [category])
   ```

3. **Parallel Query Execution**: Execute independent queries in parallel
   ```python
   async def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
       # Execute queries in parallel
       user_task = asyncio.create_task(self.get_user(user_id))
       orders_task = asyncio.create_task(self.get_recent_orders(user_id))
       recommendations_task = asyncio.create_task(self.get_recommendations(user_id))
       
       # Gather results
       user, orders, recommendations = await asyncio.gather(
           user_task, orders_task, recommendations_task
       )
       
       return {
           "user": user,
           "recent_orders": orders,
           "recommendations": recommendations
       }
   ```

## Read Model Optimizations

### Read Model Design

Optimize read model design for query performance:

1. **Denormalization**: Denormalize data to reduce joins
   ```python
   # Denormalized product read model
   class ProductReadModel(ReadModel):
       id: str
       name: str
       price: float
       category_id: str
       category_name: str  # Denormalized field
       average_rating: float  # Denormalized field
       tag_names: List[str]  # Denormalized field
   ```

2. **Purpose-Specific Models**: Create read models for specific use cases
   ```python
   # Read model for search results
   class ProductSearchResult(ReadModel):
       id: str
       name: str
       price: float
       category: str
       search_score: float
       
   # Read model for product details
   class ProductDetails(ReadModel):
       id: str
       name: str
       description: str
       price: float
       category: str
       specifications: Dict[str, Any]
       related_products: List[Dict[str, Any]]
       reviews: List[Dict[str, Any]]
   ```

3. **Materialized Views**: Use database materialized views for complex aggregations
   ```python
   # Creating a materialized view
   async def create_product_stats_view(self):
       query = """
       CREATE MATERIALIZED VIEW product_stats AS
       SELECT
           p.category_id,
           c.name AS category_name,
           COUNT(p.id) AS product_count,
           AVG(p.price) AS average_price,
           MIN(p.price) AS min_price,
           MAX(p.price) AS max_price
       FROM products p
       JOIN categories c ON p.category_id = c.id
       GROUP BY p.category_id, c.name
       """
       await self.db.execute_query(query, [])
   ```

### Read Model Storage

Optimize read model storage:

1. **Indexing Strategy**: Create appropriate indexes for common query patterns
   ```python
   # Creating indexes for read models
   async def create_indexes(self):
       # Index for category-based queries
       await self.db.execute_query(
           "CREATE INDEX product_read_models_category_idx ON product_read_models((data->>'category'))",
           []
       )
       
       # Index for price range queries
       await self.db.execute_query(
           "CREATE INDEX product_read_models_price_idx ON product_read_models((data->>'price')::float)",
           []
       )
       
       # Full text search index
       await self.db.execute_query(
           "CREATE INDEX product_read_models_name_trgm_idx ON product_read_models USING gin (to_tsvector('english', data->>'name'))",
           []
       )
   ```

2. **JSON Storage**: Use JSON columns for flexible schema storage
   ```python
   # Repository using JSON storage
   class PostgresReadModelRepository[T](ReadModelRepository[T]):
       async def save(self, model: T) -> None:
           query = """
           INSERT INTO read_models (id, type, version, created_at, updated_at, data)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (id, type) DO UPDATE
           SET version = $3, updated_at = $5, data = $6
           """
           
           params = [
               model.id.value,
               self.model_type.__name__,
               model.version,
               model.created_at,
               model.updated_at,
               model.data  # Stored as JSON
           ]
           
           await self.db.execute_query(query, params)
   ```

3. **Partitioning**: Use table partitioning for large read model tables
   ```python
   # Creating a partitioned read model table
   async def create_partitioned_table(self):
       # Create partitioned table
       await self.db.execute_query(
           """
           CREATE TABLE event_read_models (
               id TEXT,
               type TEXT,
               version INTEGER,
               created_at TIMESTAMP WITH TIME ZONE,
               updated_at TIMESTAMP WITH TIME ZONE,
               data JSONB,
               PRIMARY KEY (type, id)
           ) PARTITION BY LIST (type)
           """,
           []
       )
       
       # Create partitions for different read model types
       await self.db.execute_query(
           "CREATE TABLE event_read_models_products PARTITION OF event_read_models FOR VALUES IN ('ProductReadModel')",
           []
       )
       
       await self.db.execute_query(
           "CREATE TABLE event_read_models_orders PARTITION OF event_read_models FOR VALUES IN ('OrderReadModel')",
           []
       )
   ```

## Event Store Optimizations

### Event Storage

Optimize event storage for write and read performance:

1. **Event Serialization**: Use efficient serialization formats
   ```python
   import msgpack
   
   class EventSerializer:
       @staticmethod
       def serialize(event: DomainEvent) -> bytes:
           # Convert to dictionary
           event_dict = event.to_dict()
           # Serialize using msgpack (more compact than JSON)
           return msgpack.packb(event_dict)
       
       @staticmethod
       def deserialize(event_bytes: bytes, event_type: Type[T]) -> T:
           # Deserialize from msgpack
           event_dict = msgpack.unpackb(event_bytes)
           # Create event object
           return event_type.from_dict(event_dict)
   ```

2. **Event Partitioning**: Partition events by aggregate type or time period
   ```python
   # Creating a partitioned event store table
   async def create_partitioned_event_store(self):
       # Create partitioned table
       await self.db.execute_query(
           """
           CREATE TABLE events (
               id SERIAL,
               aggregate_id TEXT,
               aggregate_type TEXT,
               event_type TEXT,
               version INTEGER,
               timestamp TIMESTAMP WITH TIME ZONE,
               data JSONB,
               PRIMARY KEY (aggregate_type, aggregate_id, version)
           ) PARTITION BY LIST (aggregate_type)
           """,
           []
       )
       
       # Create partitions for different aggregate types
       await self.db.execute_query(
           "CREATE TABLE events_products PARTITION OF events FOR VALUES IN ('Product')",
           []
       )
       
       await self.db.execute_query(
           "CREATE TABLE events_orders PARTITION OF events FOR VALUES IN ('Order')",
           []
       )
   ```

3. **Snapshot Strategy**: Implement snapshotting for faster aggregate loading
   ```python
   class SnapshotRepository[T]:
       def __init__(self, db_provider, aggregate_type: Type[T]):
           self.db = db_provider
           self.aggregate_type = aggregate_type.__name__
       
       async def save_snapshot(self, aggregate_id: str, version: int, data: Dict[str, Any]) -> None:
           query = """
           INSERT INTO snapshots (aggregate_id, aggregate_type, version, timestamp, data)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (aggregate_id, aggregate_type) DO UPDATE
           SET version = $3, timestamp = $4, data = $5
           """
           
           params = [
               aggregate_id,
               self.aggregate_type,
               version,
               datetime.now(UTC),
               data
           ]
           
           await self.db.execute_query(query, params)
       
       async def get_latest_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
           query = """
           SELECT version, data FROM snapshots
           WHERE aggregate_id = $1 AND aggregate_type = $2
           """
           
           result = await self.db.execute_query(query, [aggregate_id, self.aggregate_type])
           
           if not result or len(result) == 0:
               return None
           
           return {
               "version": result[0]["version"],
               "data": result[0]["data"]
           }
   ```

### Event Processing

Optimize event processing:

1. **Batch Event Processing**: Process events in batches
   ```python
   class BatchProjector(Projector):
       async def process_events(self, batch_size: int = 100) -> int:
           # Get unprocessed events
           events = await self.event_store.get_unprocessed_events(batch_size)
           
           if not events:
               return 0
           
           # Process events in batch
           for event in events:
               await self.apply_event(event)
           
           # Mark events as processed
           last_event_id = events[-1].id
           await self.event_store.mark_processed(last_event_id)
           
           return len(events)
   ```

2. **Parallel Event Processing**: Process independent events in parallel
   ```python
   class ParallelProjector(Projector):
       async def process_events(self, batch_size: int = 100) -> int:
           # Get unprocessed events
           events = await self.event_store.get_unprocessed_events(batch_size)
           
           if not events:
               return 0
           
           # Group events by aggregate type for parallel processing
           events_by_type = {}
           for event in events:
               aggregate_type = event.aggregate_type
               if aggregate_type not in events_by_type:
                   events_by_type[aggregate_type] = []
               events_by_type[aggregate_type].append(event)
           
           # Process each group in parallel
           tasks = []
           for event_type, event_group in events_by_type.items():
               task = asyncio.create_task(self._process_group(event_type, event_group))
               tasks.append(task)
           
           # Wait for all groups to be processed
           await asyncio.gather(*tasks)
           
           # Mark events as processed
           last_event_id = events[-1].id
           await self.event_store.mark_processed(last_event_id)
           
           return len(events)
       
       async def _process_group(self, event_type: str, events: List[DomainEvent]) -> None:
           # Process events in a group
           for event in events:
               await self.apply_event(event)
   ```

3. **Event Sourcing Optimization**: Optimize event sourcing for aggregate loading
   ```python
   class OptimizedEventStore(EventStore):
       async def get_events_for_aggregate(self, aggregate_id: str, aggregate_type: str) -> List[DomainEvent]:
           # Try to get the latest snapshot
           snapshot = await self.snapshot_repository.get_latest_snapshot(aggregate_id)
           
           if snapshot:
               # Load only events after the snapshot version
               events = await self._load_events_after_version(
                   aggregate_id, 
                   aggregate_type, 
                   snapshot["version"]
               )
               
               # Return the snapshot data and events
               return {
                   "snapshot": snapshot["data"],
                   "events": events
               }
           else:
               # No snapshot, load all events
               return {
                   "snapshot": None,
                   "events": await self._load_all_events(aggregate_id, aggregate_type)
               }
   ```

## Caching Strategies

### Multi-Level Caching

Implement multiple cache levels for optimal performance:

1. **In-Memory Cache**: Fast, local cache for frequently accessed data
   ```python
   class InMemoryCache[T](ReadModelCache[T]):
       def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
           self.cache = {}
           self.max_size = max_size
           self.ttl_seconds = ttl_seconds
           self.access_times = {}
       
       async def get(self, key: str) -> Optional[T]:
           if key not in self.cache:
               return None
           
           value, expiry = self.cache[key]
           if expiry < datetime.now(UTC):
               # Expired
               del self.cache[key]
               return None
           
           # Update access time for LRU
           self.access_times[key] = datetime.now(UTC)
           
           return value
       
       async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
           # Evict if cache is full
           if len(self.cache) >= self.max_size:
               self._evict_lru()
           
           ttl = ttl_seconds or self.ttl_seconds
           expiry = datetime.now(UTC) + timedelta(seconds=ttl)
           
           self.cache[key] = (value, expiry)
           self.access_times[key] = datetime.now(UTC)
       
       def _evict_lru(self) -> None:
           if not self.cache:
               return
           
           # Find least recently used key
           lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
           
           # Remove from cache and access times
           del self.cache[lru_key]
           del self.access_times[lru_key]
   ```

2. **Distributed Cache**: Shared cache for clustered deployments
   ```python
   class RedisCache[T](ReadModelCache[T]):
       def __init__(self, redis_client, prefix: str = "cache:", ttl_seconds: int = 300):
           self.redis = redis_client
           self.prefix = prefix
           self.ttl_seconds = ttl_seconds
       
       async def get(self, key: str) -> Optional[T]:
           # Get from Redis
           value = await self.redis.get(f"{self.prefix}{key}")
           
           if not value:
               return None
           
           # Deserialize
           return pickle.loads(value)
       
       async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
           # Serialize
           serialized = pickle.dumps(value)
           
           # Set in Redis with TTL
           ttl = ttl_seconds or self.ttl_seconds
           await self.redis.set(f"{self.prefix}{key}", serialized, ex=ttl)
       
       async def invalidate(self, key: str) -> None:
           await self.redis.delete(f"{self.prefix}{key}")
       
       async def clear(self) -> None:
           # Delete all keys with the prefix
           cursor = 0
           while True:
               cursor, keys = await self.redis.scan(cursor, f"{self.prefix}*")
               if keys:
                   await self.redis.delete(*keys)
               if cursor == 0:
                   break
   ```

3. **Multi-Level Cache**: Combine memory and distributed caches
   ```python
   class MultiLevelCache[T](ReadModelCache[T]):
       def __init__(self, l1_cache: ReadModelCache[T], l2_cache: ReadModelCache[T]):
           self.l1_cache = l1_cache  # Fast, in-memory cache
           self.l2_cache = l2_cache  # Slower, distributed cache
       
       async def get(self, key: str) -> Optional[T]:
           # Try L1 cache first
           value = await self.l1_cache.get(key)
           
           if value is not None:
               return value
           
           # Try L2 cache
           value = await self.l2_cache.get(key)
           
           if value is not None:
               # Store in L1 for future requests
               await self.l1_cache.set(key, value)
           
           return value
       
       async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
           # Set in both caches
           await self.l1_cache.set(key, value, ttl_seconds)
           await self.l2_cache.set(key, value, ttl_seconds)
       
       async def invalidate(self, key: str) -> None:
           # Invalidate in both caches
           await self.l1_cache.invalidate(key)
           await self.l2_cache.invalidate(key)
       
       async def clear(self) -> None:
           # Clear both caches
           await self.l1_cache.clear()
           await self.l2_cache.clear()
   ```

### Cache Invalidation

Implement efficient cache invalidation strategies:

1. **Event-Based Invalidation**: Invalidate caches based on domain events
   ```python
   class CacheInvalidator(EventHandler[DomainEvent]):
       def __init__(self, cache_service: CacheService):
           self.cache_service = cache_service
       
       async def handle(self, event: DomainEvent) -> None:
           # Invalidate cache based on event type
           if isinstance(event, ProductCreatedEvent) or isinstance(event, ProductUpdatedEvent):
               # Invalidate specific product
               await self.cache_service.invalidate(f"product:{event.aggregate_id}")
               # Invalidate product lists
               await self.cache_service.invalidate("products:list")
               await self.cache_service.invalidate(f"products:category:{event.data.get('category_id')}")
   ```

2. **Selective Invalidation**: Invalidate only affected cache entries
   ```python
   class SelectiveCacheInvalidator:
       def __init__(self, cache_service: CacheService):
           self.cache_service = cache_service
           self.invalidation_maps = {
               "ProductCreatedEvent": ["products:list", "products:count"],
               "ProductUpdatedEvent": ["product:{id}", "products:category:{category_id}"],
               "OrderCreatedEvent": ["orders:user:{user_id}", "orders:count"]
           }
       
       async def invalidate(self, event: DomainEvent) -> None:
           event_type = event.__class__.__name__
           
           if event_type not in self.invalidation_maps:
               return
           
           # Get cache keys to invalidate
           keys_to_invalidate = self.invalidation_maps[event_type]
           
           # Replace placeholders with actual values
           concrete_keys = []
           for key_template in keys_to_invalidate:
               # Replace {placeholders} with event data
               concrete_key = key_template
               for placeholder, value in event.to_dict().items():
                   concrete_key = concrete_key.replace(f"{{{placeholder}}}", str(value))
               
               concrete_keys.append(concrete_key)
           
           # Invalidate concrete keys
           for key in concrete_keys:
               await self.cache_service.invalidate(key)
   ```

3. **Timed Expiration**: Use time-based expiration for less critical data
   ```python
   class TimedCacheService(CacheService):
       def __init__(self, default_ttl_seconds: int = 300):
           self.default_ttl_seconds = default_ttl_seconds
           self.ttl_overrides = {
               # Cache key pattern: TTL in seconds
               "product:*": 3600,             # Product details: 1 hour
               "products:list": 300,          # Product lists: 5 minutes
               "products:search:*": 60,       # Search results: 1 minute
               "user:*": 86400,               # User data: 24 hours
               "stats:*": 1800                # Statistics: 30 minutes
           }
       
       def get_ttl(self, key: str) -> int:
           # Check for pattern overrides
           for pattern, ttl in self.ttl_overrides.items():
               if self._matches_pattern(key, pattern):
                   return ttl
           
           # Use default TTL
           return self.default_ttl_seconds
       
       def _matches_pattern(self, key: str, pattern: str) -> bool:
           import re
           pattern_regex = pattern.replace("*", ".*")
           return bool(re.match(f"^{pattern_regex}$", key))
   ```

## Database Optimizations

### Connection Pooling

Optimize database connections:

1. **Connection Pool Configuration**: Configure connection pools appropriately
   ```python
   # Optimized connection pool configuration
   class ConnectionPoolConfig:
       min_size: int = 5                # Minimum number of connections
       max_size: int = 20               # Maximum number of connections
       max_idle_time: int = 300         # Maximum time a connection can be idle (seconds)
       max_lifetime: int = 3600         # Maximum lifetime of a connection (seconds)
       acquisition_timeout: int = 10    # Maximum time to wait for a connection (seconds)
       statement_cache_size: int = 1000  # Number of prepared statements to cache
   ```

2. **Connection Health Monitoring**: Monitor connection health
   ```python
   class ConnectionHealthMonitor:
       def __init__(self, pool, check_interval: int = 60):
           self.pool = pool
           self.check_interval = check_interval
           self._running = False
       
       async def start(self):
           self._running = True
           while self._running:
               await self._check_pool_health()
               await asyncio.sleep(self.check_interval)
       
       async def stop(self):
           self._running = False
       
       async def _check_pool_health(self):
           # Get pool metrics
           metrics = await self.pool.get_metrics()
           
           # Log metrics
           logging.info(f"Connection pool metrics: {metrics}")
           
           # Check for issues
           if metrics["waiting"] > metrics["max_size"] * 0.5:
               logging.warning(f"High connection wait count: {metrics['waiting']}")
           
           if metrics["used"] > metrics["max_size"] * 0.9:
               logging.warning(f"Pool near capacity: {metrics['used']}/{metrics['max_size']}")
   ```

3. **Connection Pool Sharding**: Shard connection pools for different workloads
   ```python
   class ShardedConnectionPool:
       def __init__(self, db_config):
           self.read_pool = ConnectionPool(db_config, max_size=30)  # Larger pool for reads
           self.write_pool = ConnectionPool(db_config, max_size=10)  # Smaller pool for writes
           self.admin_pool = ConnectionPool(db_config, max_size=5)   # Small pool for admin operations
       
       async def get_read_connection(self):
           return await self.read_pool.acquire()
       
       async def get_write_connection(self):
           return await self.write_pool.acquire()
       
       async def get_admin_connection(self):
           return await self.admin_pool.acquire()
   ```

### Query Optimization

Optimize database queries:

1. **Query Analysis**: Analyze and optimize critical queries
   ```python
   class QueryAnalyzer:
       def __init__(self, db_provider):
           self.db = db_provider
       
       async def analyze_query(self, query: str, params: List[Any]) -> Dict[str, Any]:
           # Execute EXPLAIN ANALYZE
           explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
           result = await self.db.execute_query(explain_query, params)
           
           # Extract execution statistics
           plan = result[0][0]["Plan"]
           
           return {
               "execution_time": plan["Actual Total Time"],
               "planning_time": plan["Planning Time"],
               "rows": plan["Actual Rows"],
               "loops": plan["Actual Loops"],
               "buffers_hit": plan.get("Shared Hit Blocks", 0),
               "buffers_read": plan.get("Shared Read Blocks", 0),
               "buffers_written": plan.get("Shared Written Blocks", 0),
               "plan": plan
           }
   ```

2. **Database Indices**: Create and maintain appropriate indices
   ```python
   class IndexManager:
       def __init__(self, db_provider):
           self.db = db_provider
       
       async def create_indices(self):
           # Create basic indices
           indices = [
               "CREATE INDEX IF NOT EXISTS products_name_idx ON products(name)",
               "CREATE INDEX IF NOT EXISTS products_category_idx ON products(category_id)",
               "CREATE INDEX IF NOT EXISTS order_items_product_idx ON order_items(product_id)",
               "CREATE INDEX IF NOT EXISTS events_aggregate_idx ON events(aggregate_type, aggregate_id)",
               "CREATE INDEX IF NOT EXISTS read_models_type_idx ON read_models(type)"
           ]
           
           for index_sql in indices:
               await self.db.execute_query(index_sql, [])
       
       async def analyze_index_usage(self) -> List[Dict[str, Any]]:
           # Query to get index usage statistics
           query = """
           SELECT
               schemaname || '.' || relname AS table,
               indexrelname AS index,
               idx_scan AS scans,
               idx_tup_read AS tuples_read,
               idx_tup_fetch AS tuples_fetched,
               pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size
           FROM pg_stat_user_indexes ui
           JOIN pg_index i ON ui.indexrelid = i.indexrelid
           WHERE idx_scan > 0
           ORDER BY idx_scan DESC, pg_relation_size(i.indexrelid) DESC
           """
           
           return await self.db.execute_query(query, [])
   ```

3. **Query Transformation**: Transform queries for better performance
   ```python
   class QueryTransformer:
       def transform_count_query(self, query: str) -> str:
           """Transform SELECT COUNT(*) queries to be more efficient."""
           if "SELECT COUNT(*) FROM" in query:
               # Extract table and conditions
               match = re.match(r"SELECT COUNT\(\*\) FROM (\w+)( WHERE .+)?", query)
               if match:
                   table, conditions = match.groups()
                   conditions = conditions or ""
                   
                   # Use approximate count for large tables
                   return f"""
                   SELECT reltuples::bigint AS estimate
                   FROM pg_class
                   WHERE relname = '{table}'
                   """
           
           return query
       
       def transform_pagination_query(self, query: str, page: int, page_size: int) -> str:
           """Transform a query to use keyset pagination instead of offset."""
           if page > 1 and "ORDER BY" in query and "LIMIT" in query:
               # Extract the ORDER BY column and direction
               match = re.search(r"ORDER BY (\w+\.?\w+)( (ASC|DESC))?", query)
               if match:
                   col, _, direction = match.groups()
                   direction = direction or "ASC"
                   
                   # Create a keyset pagination query
                   if "OFFSET" in query:
                       # Remove OFFSET clause
                       query = re.sub(r"OFFSET \d+", "", query)
                   
                   # Get the last value from the previous page
                   # (This is a simplification - in a real implementation, 
                   # you would need to get this value from the previous page results)
                   last_value = "..."
                   
                   # Add WHERE clause for keyset pagination
                   if "WHERE" in query:
                       operator = "<" if direction == "DESC" else ">"
                       query = query.replace("WHERE", f"WHERE {col} {operator} {last_value} AND")
                   else:
                       operator = "<" if direction == "DESC" else ">"
                       query = query.replace("ORDER BY", f"WHERE {col} {operator} {last_value} ORDER BY")
           
           return query
   ```

## Scaling Strategies

### Horizontal Scaling

Strategies for scaling horizontally:

1. **Stateless Services**: Design stateless services for easy scaling
   ```python
   # Stateless service example
   class StatelessCommandProcessor:
       def __init__(self, mediator_factory, event_store_factory):
           # Use factories instead of singletons
           self.mediator_factory = mediator_factory
           self.event_store_factory = event_store_factory
       
       async def process_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
           # Create new instances for each request
           mediator = self.mediator_factory()
           event_store = self.event_store_factory()
           
           # Process command
           command = self._create_command(command_data)
           result = await mediator.execute_command(command)
           
           # Return result
           return result.to_dict() if result.is_success() else {"error": result.error.to_dict()}
   ```

2. **Read Replicas**: Use read replicas for query services
   ```python
   class ReadReplicaQueryService(QueryService):
       def __init__(self, read_replica_pool, write_db_pool):
           self.read_replica_pool = read_replica_pool
           self.write_db_pool = write_db_pool
       
       async def execute_query(self, query: Query) -> Result[Any]:
           # Use read replica for read operations
           async with self.read_replica_pool.acquire() as conn:
               # Execute query against read replica
               result = await conn.execute(query.sql, *query.params)
               return Success(result)
       
       async def execute_update(self, update: Update) -> Result[Any]:
           # Use write database for write operations
           async with self.write_db_pool.acquire() as conn:
               # Execute update against write database
               result = await conn.execute(update.sql, *update.params)
               return Success(result)
   ```

3. **Sharding**: Implement sharding for large datasets
   ```python
   class ShardedReadModelRepository[T](ReadModelRepository[T]):
       def __init__(self, shard_key_fn, shard_count: int = 10):
           self.shard_repositories = [PostgresReadModelRepository() for _ in range(shard_count)]
           self.shard_key_fn = shard_key_fn
           self.shard_count = shard_count
       
       def _get_shard(self, model: T) -> int:
           # Get shard key from model
           shard_key = self.shard_key_fn(model)
           # Calculate shard index
           return hash(shard_key) % self.shard_count
       
       async def save(self, model: T) -> None:
           # Get appropriate shard
           shard_index = self._get_shard(model)
           # Save to shard
           await self.shard_repositories[shard_index].save(model)
       
       async def get_by_id(self, id: Any) -> Optional[T]:
           # For get_by_id, we need to query all shards
           # In a real implementation, you would use a consistent hashing scheme
           # or maintain a lookup table to know which shard contains the ID
           for repo in self.shard_repositories:
               model = await repo.get_by_id(id)
               if model:
                   return model
           return None
   ```

### Vertical Scaling

Strategies for scaling vertically:

1. **Resource Optimization**: Optimize resource usage
   ```python
   # Memory optimization example
   class MemoryOptimizedEventStore(EventStore):
       def __init__(self, db_provider, max_events_in_memory: int = 1000):
           self.db = db_provider
           self.max_events_in_memory = max_events_in_memory
           self.event_cache = LRUCache(max_events_in_memory)
       
       async def append(self, event: DomainEvent) -> None:
           # Store event in database
           await self._store_event(event)
           
           # Update cache with new event
           events = self.event_cache.get(event.aggregate_id, [])
           events.append(event)
           self.event_cache.put(event.aggregate_id, events)
       
       async def get_events(self, aggregate_id: str) -> List[DomainEvent]:
           # Try to get from cache
           events = self.event_cache.get(aggregate_id)
           
           if events is not None:
               return events
           
           # Load from database
           events = await self._load_events(aggregate_id)
           
           # Cache events if not too many
           if len(events) <= self.max_events_in_memory:
               self.event_cache.put(aggregate_id, events)
           
           return events
   ```

2. **Asynchronous Processing**: Use asynchronous processing for better CPU utilization
   ```python
   class AsynchronousProjector(Projector):
       def __init__(self, event_store, projection_service, worker_count: int = 5):
           self.event_store = event_store
           self.projection_service = projection_service
           self.worker_count = worker_count
           self.queue = asyncio.Queue()
           self.workers = []
       
       async def start(self):
           # Start workers
           for _ in range(self.worker_count):
               worker = asyncio.create_task(self._worker())
               self.workers.append(worker)
       
       async def stop(self):
           # Stop workers
           for _ in range(self.worker_count):
               await self.queue.put(None)  # Sentinel value
           
           # Wait for workers to finish
           await asyncio.gather(*self.workers)
       
       async def process_event(self, event: DomainEvent):
           # Add event to processing queue
           await self.queue.put(event)
       
       async def _worker(self):
           while True:
               # Get event from queue
               event = await self.queue.get()
               
               # Check for sentinel value
               if event is None:
                   break
               
               try:
                   # Process event
                   await self.projection_service.apply_event(event)
               except Exception as e:
                   logging.error(f"Error processing event: {e}")
               finally:
                   # Mark task as done
                   self.queue.task_done()
   ```

3. **Database Optimization**: Optimize database configuration for vertical scaling
   ```python
   # PostgreSQL configuration recommendations for vertical scaling
   class PostgresScalingConfig:
       def __init__(self, total_memory_gb: int, cpu_cores: int):
           self.total_memory_gb = total_memory_gb
           self.cpu_cores = cpu_cores
       
       def get_config(self) -> Dict[str, str]:
           # Calculate optimal settings based on available resources
           
           # Memory settings
           shared_buffers = f"{int(self.total_memory_gb * 0.25)}GB"
           effective_cache_size = f"{int(self.total_memory_gb * 0.75)}GB"
           maintenance_work_mem = f"{int(self.total_memory_gb * 0.05)}GB"
           work_mem = f"{int((self.total_memory_gb * 0.25) / (self.cpu_cores * 4))}MB"
           
           # Parallelism settings
           max_worker_processes = self.cpu_cores
           max_parallel_workers_per_gather = max(2, int(self.cpu_cores / 2))
           max_parallel_workers = self.cpu_cores
           
           # Return configuration
           return {
               "shared_buffers": shared_buffers,
               "effective_cache_size": effective_cache_size,
               "maintenance_work_mem": maintenance_work_mem,
               "work_mem": work_mem,
               "max_worker_processes": str(max_worker_processes),
               "max_parallel_workers_per_gather": str(max_parallel_workers_per_gather),
               "max_parallel_workers": str(max_parallel_workers),
               "random_page_cost": "1.1",  # Assuming SSD storage
               "effective_io_concurrency": "200",  # Assuming SSD storage
               "checkpoint_completion_target": "0.9",
               "wal_buffers": "16MB",
               "default_statistics_target": "100"
           }
   ```

## Monitoring and Observability

### Performance Metrics

Implement performance metrics for CQRS:

1. **Command Metrics**: Track command execution metrics
   ```python
   class CommandMetrics:
       def __init__(self, metrics_provider):
           self.metrics_provider = metrics_provider
           
           # Create metrics
           self.command_count = metrics_provider.counter(
               name="cqrs_commands_total",
               description="Total number of commands executed",
               labels=["command_type", "success"]
           )
           
           self.command_duration = metrics_provider.histogram(
               name="cqrs_command_duration_seconds",
               description="Command execution duration in seconds",
               labels=["command_type"],
               buckets=[0.01, 0.05, 0.1, 0.5, 1, 5]
           )
       
       def record_command_execution(self, command_type: str, duration: float, success: bool) -> None:
           # Record command execution
           self.command_count.labels(command_type=command_type, success=str(success)).inc()
           self.command_duration.labels(command_type=command_type).observe(duration)
   ```

2. **Query Metrics**: Track query execution metrics
   ```python
   class QueryMetrics:
       def __init__(self, metrics_provider):
           self.metrics_provider = metrics_provider
           
           # Create metrics
           self.query_count = metrics_provider.counter(
               name="cqrs_queries_total",
               description="Total number of queries executed",
               labels=["query_type", "success", "cached"]
           )
           
           self.query_duration = metrics_provider.histogram(
               name="cqrs_query_duration_seconds",
               description="Query execution duration in seconds",
               labels=["query_type", "cached"],
               buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1]
           )
           
           self.query_result_size = metrics_provider.histogram(
               name="cqrs_query_result_size",
               description="Number of items returned by queries",
               labels=["query_type"],
               buckets=[0, 1, 10, 100, 1000, 10000]
           )
       
       def record_query_execution(
           self, 
           query_type: str, 
           duration: float, 
           success: bool, 
           cached: bool,
           result_size: int = 0
       ) -> None:
           # Record query execution
           self.query_count.labels(
               query_type=query_type, 
               success=str(success), 
               cached=str(cached)
           ).inc()
           
           self.query_duration.labels(
               query_type=query_type, 
               cached=str(cached)
           ).observe(duration)
           
           if success and result_size > 0:
               self.query_result_size.labels(query_type=query_type).observe(result_size)
   ```

3. **Event Metrics**: Track event processing metrics
   ```python
   class EventMetrics:
       def __init__(self, metrics_provider):
           self.metrics_provider = metrics_provider
           
           # Create metrics
           self.event_count = metrics_provider.counter(
               name="cqrs_events_total",
               description="Total number of events processed",
               labels=["event_type", "success"]
           )
           
           self.event_processing_duration = metrics_provider.histogram(
               name="cqrs_event_processing_seconds",
               description="Event processing duration in seconds",
               labels=["event_type"],
               buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1]
           )
           
           self.event_queue_size = metrics_provider.gauge(
               name="cqrs_event_queue_size",
               description="Number of events waiting to be processed",
               labels=["event_type"]
           )
       
       def record_event_processed(
           self, 
           event_type: str, 
           duration: float, 
           success: bool
       ) -> None:
           # Record event processing
           self.event_count.labels(event_type=event_type, success=str(success)).inc()
           self.event_processing_duration.labels(event_type=event_type).observe(duration)
       
       def update_queue_size(self, event_type: str, size: int) -> None:
           # Update queue size
           self.event_queue_size.labels(event_type=event_type).set(size)
   ```

### Tracing

Implement distributed tracing:

1. **Command Tracing**: Trace command execution
   ```python
   class TracingCommandBus(CommandBus):
       def __init__(self, tracer):
           super().__init__()
           self.tracer = tracer
       
       async def execute(self, command: Command) -> Result[Any]:
           command_type = command.__class__.__name__
           
           # Create a span for the command
           with self.tracer.start_as_current_span(
               f"command.{command_type}",
               attributes={
                   "command.type": command_type,
                   "command.id": str(getattr(command, "id", "")),
               }
           ) as span:
               try:
                   # Execute the command
                   result = await super().execute(command)
                   
                   # Record result
                   span.set_attribute("command.success", result.is_success())
                   if not result.is_success():
                       span.set_attribute("error", True)
                       span.set_attribute("error.message", result.error.message)
                   
                   return result
               except Exception as e:
                   # Record exception
                   span.set_attribute("error", True)
                   span.record_exception(e)
                   raise
   ```

2. **Query Tracing**: Trace query execution
   ```python
   class TracingQueryBus(QueryBus):
       def __init__(self, tracer):
           super().__init__()
           self.tracer = tracer
       
       async def execute(self, query: Query) -> Result[Any]:
           query_type = query.__class__.__name__
           
           # Create a span for the query
           with self.tracer.start_as_current_span(
               f"query.{query_type}",
               attributes={
                   "query.type": query_type,
                   "query.id": str(getattr(query, "id", "")),
               }
           ) as span:
               try:
                   # Execute the query
                   result = await super().execute(query)
                   
                   # Record result
                   span.set_attribute("query.success", result.is_success())
                   if not result.is_success():
                       span.set_attribute("error", True)
                       span.set_attribute("error.message", result.error.message)
                   
                   return result
               except Exception as e:
                   # Record exception
                   span.set_attribute("error", True)
                   span.record_exception(e)
                   raise
   ```

3. **Event Tracing**: Trace event processing
   ```python
   class TracingEventHandler[T](EventHandler[T]):
       def __init__(self, handler: EventHandler[T], tracer):
           self.handler = handler
           self.tracer = tracer
       
       async def handle(self, event: T) -> None:
           event_type = event.__class__.__name__
           
           # Create a span for the event
           with self.tracer.start_as_current_span(
               f"event.{event_type}",
               attributes={
                   "event.type": event_type,
                   "event.id": str(getattr(event, "id", "")),
                   "event.aggregate_id": str(getattr(event, "aggregate_id", "")),
                   "event.aggregate_type": str(getattr(event, "aggregate_type", "")),
               }
           ) as span:
               try:
                   # Handle the event
                   await self.handler.handle(event)
               except Exception as e:
                   # Record exception
                   span.set_attribute("error", True)
                   span.record_exception(e)
                   raise
   ```

### Health Checks

Implement health checks for CQRS components:

1. **Command Bus Health**: Check command bus health
   ```python
   class CommandBusHealthCheck(HealthCheck):
       def __init__(self, command_bus):
           self.command_bus = command_bus
       
       async def check_health(self) -> HealthStatus:
           try:
               # Execute a simple ping command
               result = await self.command_bus.execute(PingCommand())
               
               if result.is_success():
                   return HealthStatus(
                       component="command_bus",
                       status="healthy",
                       details={"latency_ms": result.metadata.get("latency_ms", 0)}
                   )
               else:
                   return HealthStatus(
                       component="command_bus",
                       status="unhealthy",
                       details={"error": result.error.message}
                   )
           except Exception as e:
               return HealthStatus(
                   component="command_bus",
                   status="unhealthy",
                   details={"error": str(e)}
               )
   ```

2. **Event Store Health**: Check event store health
   ```python
   class EventStoreHealthCheck(HealthCheck):
       def __init__(self, event_store):
           self.event_store = event_store
       
       async def check_health(self) -> HealthStatus:
           try:
               # Check if event store is accessible
               start_time = time.time()
               await self.event_store.get_events("health-check-aggregate", limit=1)
               latency_ms = (time.time() - start_time) * 1000
               
               return HealthStatus(
                   component="event_store",
                   status="healthy",
                   details={
                       "latency_ms": latency_ms,
                       "implementation": self.event_store.__class__.__name__
                   }
               )
           except Exception as e:
               return HealthStatus(
                   component="event_store",
                   status="unhealthy",
                   details={"error": str(e)}
               )
   ```

3. **Read Model Health**: Check read model health
   ```python
   class ReadModelHealthCheck(HealthCheck):
       def __init__(self, read_model_service):
           self.read_model_service = read_model_service
       
       async def check_health(self) -> HealthStatus:
           try:
               # Check if read model service is accessible
               start_time = time.time()
               await self.read_model_service.get_health_metrics()
               latency_ms = (time.time() - start_time) * 1000
               
               return HealthStatus(
                   component="read_model_service",
                   status="healthy",
                   details={
                       "latency_ms": latency_ms,
                       "cache_hit_rate": self.read_model_service.cache_metrics.hit_rate,
                       "read_model_count": self.read_model_service.metrics.model_count
                   }
               )
           except Exception as e:
               return HealthStatus(
                   component="read_model_service",
                   status="unhealthy",
                   details={"error": str(e)}
               )
   ```

## Configuration Best Practices

### Command Configuration

Best practices for configuring commands:

1. **Command Retries**: Configure command retries
   ```python
   class CommandRetryConfig:
       max_retries: int = 3
       retry_delay_ms: int = 500
       backoff_factor: float = 2.0
       retry_errors: List[str] = ["ConcurrencyError", "TemporaryDatabaseError"]
   ```

2. **Command Validation**: Configure command validation
   ```python
   class CommandValidationConfig:
       # Validation modes: 'strict', 'lenient', 'schema_only'
       validation_mode: str = "strict"
       # Maximum number of validation errors to return
       max_errors: int = 10
       # Whether to validate commands before processing
       validate_early: bool = True
       # Custom validators by command type
       validators: Dict[str, List[Callable]] = {}
   ```

3. **Command Timeout**: Configure command timeouts
   ```python
   class CommandTimeoutConfig:
       # Default timeout for all commands
       default_timeout_ms: int = 5000
       # Specific timeouts by command type
       timeouts: Dict[str, int] = {
           "CreateOrderCommand": 10000,
           "ProcessPaymentCommand": 15000,
           "SendEmailCommand": 30000
       }
   ```

### Query Configuration

Best practices for configuring queries:

1. **Query Caching**: Configure query caching
   ```python
   class QueryCacheConfig:
       # Whether to enable caching
       enabled: bool = True
       # Default TTL for cached queries
       default_ttl_seconds: int = 300
       # Specific TTLs by query type
       ttl_by_query_type: Dict[str, int] = {
           "GetUserByIdQuery": 3600,
           "ListProductsQuery": 300,
           "SearchProductsQuery": 60
       }
       # Maximum number of items to cache
       max_cache_size: int = 10000
       # Cache storage backend: 'memory', 'redis', 'multi_level'
       cache_backend: str = "multi_level"
   ```

2. **Query Defaults**: Configure query defaults
   ```python
   class QueryDefaultsConfig:
       # Default page size for paginated queries
       default_page_size: int = 20
       # Maximum page size allowed
       max_page_size: int = 100
       # Default sort field
       default_sort_field: str = "created_at"
       # Default sort direction
       default_sort_direction: str = "desc"
   ```

3. **Query Timeout**: Configure query timeouts
   ```python
   class QueryTimeoutConfig:
       # Default timeout for all queries
       default_timeout_ms: int = 1000
       # Specific timeouts by query type
       timeouts: Dict[str, int] = {
           "GetDashboardDataQuery": 5000,
           "GenerateReportQuery": 30000,
           "SearchProductsQuery": 3000
       }
   ```

### Read Model Configuration

Best practices for configuring read models:

1. **Read Model Builders**: Configure read model builders
   ```python
   class ReadModelBuildersConfig:
       # Whether to enable automatic read model building
       auto_build: bool = True
       # Maximum number of events to process in a batch
       batch_size: int = 100
       # Number of worker processes
       workers: int = 4
       # How often to check for new events (seconds)
       poll_interval_seconds: int = 5
       # Read model types to build
       read_model_types: List[str] = ["ProductReadModel", "OrderReadModel", "UserReadModel"]
   ```

2. **Read Model Storage**: Configure read model storage
   ```python
   class ReadModelStorageConfig:
       # Storage backend: 'postgres', 'redis', 'hybrid'
       storage_backend: str = "postgres"
       # Table/collection name prefix
       name_prefix: str = "rm_"
       # Whether to create indexes automatically
       auto_create_indexes: bool = True
       # Maximum number of read models per table/collection
       max_items_per_table: int = 1000000
       # Whether to use sharding for large collections
       enable_sharding: bool = False
       # Number of shards (if sharding is enabled)
       shard_count: int = 10
   ```

3. **Read Model Snapshots**: Configure read model snapshots
   ```python
   class ReadModelSnapshotConfig:
       # Whether to enable snapshots
       enabled: bool = True
       # How often to create snapshots (number of events)
       snapshot_frequency: int = 100
       # Maximum number of snapshots to keep per aggregate
       max_snapshots: int = 3
       # Whether to compress snapshots
       compress: bool = True
       # Compression level (1-9, higher is more compression)
       compression_level: int = 6
   ```

## Performance Testing

### Load Testing

Approaches for load testing CQRS:

1. **Command Load Testing**: Test command processing under load
   ```python
   async def command_load_test(
       command_bus: CommandBus,
       command_factory: Callable[[], Command],
       concurrency: int = 10,
       duration_seconds: int = 60
   ) -> Dict[str, Any]:
       """Run a load test on the command bus."""
       start_time = time.time()
       end_time = start_time + duration_seconds
       
       # Statistics
       success_count = 0
       error_count = 0
       latencies = []
       
       # Create semaphore for concurrency control
       semaphore = asyncio.Semaphore(concurrency)
       
       async def worker():
           nonlocal success_count, error_count
           
           while time.time() < end_time:
               async with semaphore:
                   # Create and execute command
                   command = command_factory()
                   
                   command_start = time.time()
                   result = await command_bus.execute(command)
                   latency = time.time() - command_start
                   
                   # Record result
                   if result.is_success():
                       success_count += 1
                   else:
                       error_count += 1
                   
                   latencies.append(latency * 1000)  # Convert to ms
       
       # Start workers
       workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
       
       # Wait for test to complete
       await asyncio.gather(*workers)
       
       # Calculate statistics
       total_count = success_count + error_count
       success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
       
       avg_latency = sum(latencies) / len(latencies) if latencies else 0
       p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
       p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
       
       return {
           "total_commands": total_count,
           "success_count": success_count,
           "error_count": error_count,
           "success_rate": success_rate,
           "commands_per_second": total_count / duration_seconds,
           "avg_latency_ms": avg_latency,
           "p95_latency_ms": p95_latency,
           "p99_latency_ms": p99_latency,
           "duration_seconds": duration_seconds,
           "concurrency": concurrency
       }
   ```

2. **Query Load Testing**: Test query processing under load
   ```python
   async def query_load_test(
       query_bus: QueryBus,
       query_factory: Callable[[], Query],
       concurrency: int = 10,
       duration_seconds: int = 60
   ) -> Dict[str, Any]:
       """Run a load test on the query bus."""
       start_time = time.time()
       end_time = start_time + duration_seconds
       
       # Statistics
       success_count = 0
       error_count = 0
       latencies = []
       
       # Create semaphore for concurrency control
       semaphore = asyncio.Semaphore(concurrency)
       
       async def worker():
           nonlocal success_count, error_count
           
           while time.time() < end_time:
               async with semaphore:
                   # Create and execute query
                   query = query_factory()
                   
                   query_start = time.time()
                   result = await query_bus.execute(query)
                   latency = time.time() - query_start
                   
                   # Record result
                   if result.is_success():
                       success_count += 1
                   else:
                       error_count += 1
                   
                   latencies.append(latency * 1000)  # Convert to ms
       
       # Start workers
       workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
       
       # Wait for test to complete
       await asyncio.gather(*workers)
       
       # Calculate statistics
       total_count = success_count + error_count
       success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
       
       avg_latency = sum(latencies) / len(latencies) if latencies else 0
       p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
       p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
       
       return {
           "total_queries": total_count,
           "success_count": success_count,
           "error_count": error_count,
           "success_rate": success_rate,
           "queries_per_second": total_count / duration_seconds,
           "avg_latency_ms": avg_latency,
           "p95_latency_ms": p95_latency,
           "p99_latency_ms": p99_latency,
           "duration_seconds": duration_seconds,
           "concurrency": concurrency
       }
   ```

3. **Event Processing Load Testing**: Test event processing under load
   ```python
   async def event_processing_load_test(
       event_dispatcher: EventDispatcher,
       event_factory: Callable[[], DomainEvent],
       event_count: int = 1000,
       batch_size: int = 100
   ) -> Dict[str, Any]:
       """Run a load test on the event processing system."""
       start_time = time.time()
       
       # Statistics
       processed_count = 0
       error_count = 0
       
       # Create events
       events = [event_factory() for _ in range(event_count)]
       
       # Process events in batches
       for i in range(0, event_count, batch_size):
           batch = events[i:i+batch_size]
           
           # Dispatch events
           tasks = [event_dispatcher.dispatch(event) for event in batch]
           results = await asyncio.gather(*tasks, return_exceptions=True)
           
           # Record results
           for result in results:
               if isinstance(result, Exception):
                   error_count += 1
               else:
                   processed_count += 1
       
       end_time = time.time()
       duration_seconds = end_time - start_time
       
       return {
           "total_events": event_count,
           "processed_count": processed_count,
           "error_count": error_count,
           "events_per_second": event_count / duration_seconds,
           "duration_seconds": duration_seconds,
           "batch_size": batch_size
       }
   ```

### Benchmarking

Tools for benchmarking CQRS:

1. **Command Benchmarking**: Benchmark command performance
   ```python
   class CommandBenchmark:
       def __init__(self, command_bus: CommandBus):
           self.command_bus = command_bus
           self.results = {}
       
       async def benchmark_command(
           self,
           name: str,
           command_factory: Callable[[], Command],
           iterations: int = 100,
           warmup: int = 10
       ) -> Dict[str, Any]:
           """Benchmark a command."""
           # Warmup
           for _ in range(warmup):
               await self.command_bus.execute(command_factory())
           
           # Benchmark
           latencies = []
           for _ in range(iterations):
               command = command_factory()
               
               start_time = time.perf_counter()
               result = await self.command_bus.execute(command)
               end_time = time.perf_counter()
               
               latency = (end_time - start_time) * 1000  # Convert to ms
               latencies.append(latency)
           
           # Calculate statistics
           avg_latency = sum(latencies) / len(latencies)
           min_latency = min(latencies)
           max_latency = max(latencies)
           p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
           
           # Record result
           benchmark_result = {
               "name": name,
               "iterations": iterations,
               "avg_latency_ms": avg_latency,
               "min_latency_ms": min_latency,
               "max_latency_ms": max_latency,
               "p95_latency_ms": p95_latency
           }
           
           self.results[name] = benchmark_result
           return benchmark_result
   ```

2. **Query Benchmarking**: Benchmark query performance
   ```python
   class QueryBenchmark:
       def __init__(self, query_bus: QueryBus):
           self.query_bus = query_bus
           self.results = {}
       
       async def benchmark_query(
           self,
           name: str,
           query_factory: Callable[[], Query],
           iterations: int = 100,
           warmup: int = 10
       ) -> Dict[str, Any]:
           """Benchmark a query."""
           # Warmup
           for _ in range(warmup):
               await self.query_bus.execute(query_factory())
           
           # Benchmark
           latencies = []
           for _ in range(iterations):
               query = query_factory()
               
               start_time = time.perf_counter()
               result = await self.query_bus.execute(query)
               end_time = time.perf_counter()
               
               latency = (end_time - start_time) * 1000  # Convert to ms
               latencies.append(latency)
           
           # Calculate statistics
           avg_latency = sum(latencies) / len(latencies)
           min_latency = min(latencies)
           max_latency = max(latencies)
           p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
           
           # Record result
           benchmark_result = {
               "name": name,
               "iterations": iterations,
               "avg_latency_ms": avg_latency,
               "min_latency_ms": min_latency,
               "max_latency_ms": max_latency,
               "p95_latency_ms": p95_latency
           }
           
           self.results[name] = benchmark_result
           return benchmark_result
   ```

3. **Performance Comparison**: Compare performance of different implementations
   ```python
   class PerformanceComparison:
       def __init__(self):
           self.results = {}
       
       async def compare(
           self,
           name: str,
           implementations: Dict[str, Callable[[], Awaitable[Any]]],
           iterations: int = 100
       ) -> Dict[str, Any]:
           """Compare performance of different implementations."""
           comparison_results = {}
           
           for impl_name, impl_fn in implementations.items():
               # Benchmark implementation
               latencies = []
               
               for _ in range(iterations):
                   start_time = time.perf_counter()
                   await impl_fn()
                   end_time = time.perf_counter()
                   
                   latency = (end_time - start_time) * 1000  # Convert to ms
                   latencies.append(latency)
               
               # Calculate statistics
               avg_latency = sum(latencies) / len(latencies)
               min_latency = min(latencies)
               max_latency = max(latencies)
               p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
               
               # Record result
               comparison_results[impl_name] = {
                   "avg_latency_ms": avg_latency,
                   "min_latency_ms": min_latency,
                   "max_latency_ms": max_latency,
                   "p95_latency_ms": p95_latency
               }
           
           # Find fastest implementation
           fastest_impl = min(comparison_results.items(), key=lambda x: x[1]["avg_latency_ms"])[0]
           
           # Calculate relative performance
           baseline_latency = comparison_results[fastest_impl]["avg_latency_ms"]
           for impl_name, result in comparison_results.items():
               result["relative_performance"] = baseline_latency / result["avg_latency_ms"]
           
           self.results[name] = comparison_results
           return {
               "name": name,
               "iterations": iterations,
               "results": comparison_results,
               "fastest_implementation": fastest_impl
           }
   ```

## Conclusion

Optimizing CQRS and Read Model performance requires a holistic approach that considers the entire architecture, from command processing to read model queries. By implementing the strategies and best practices outlined in this document, you can achieve a high-performance, scalable CQRS implementation that meets your application's requirements.

Remember that performance optimization is an ongoing process. Continuously monitor your application's performance, identify bottlenecks, and refine your implementation based on real-world usage patterns. The uno framework provides the tools and flexibility needed to build a CQRS implementation that scales from small applications to large, enterprise-grade systems.