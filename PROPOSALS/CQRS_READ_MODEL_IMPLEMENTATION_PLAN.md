# CQRS and Read Model Implementation Plan

This document outlines the comprehensive implementation plan for the CQRS (Command Query Responsibility Segregation) and Read Model modules in the uno framework.

## Current Status

### CQRS Module

The CQRS module (`uno.core.cqrs`) currently implements:

- Command and Query base classes with proper typing
- Command and Query bus implementations 
- Handler registry and decoration system
- Mediator pattern for executing commands and queries
- Basic error handling

### Read Model Module

The Read Model module (`uno.read_model`) currently implements:

- Domain entities for read models, projections, queries, etc.
- Repository interfaces and basic implementations
- Service interfaces 
- Projection system for transforming domain events into read models
- Caching infrastructure

## Implementation Gaps

Despite having good foundational code, several important components are missing or incomplete:

1. **Integration between CQRS and Read Model**: The two modules are currently separate with no clear integration points.
2. **Event sourcing support**: Limited support for event sourcing, which is essential for CQRS.
3. **Complete repository implementations**: Missing robust database implementations for repositories.
4. **Query optimization**: No specialized query handlers for complex or frequently used queries.
5. **Testing infrastructure**: Limited testing tools for CQRS components.
6. **Documentation**: Incomplete documentation, especially for practical usage patterns.
7. **Dependency injection integration**: Missing comprehensive DI support.
8. **Performance optimizations**: Limited batch operations and caching strategies.
9. **Monitoring and observability**: No built-in monitoring for command/query execution.
10. **FastAPI integration**: Missing integration with FastAPI for automatic endpoint creation.

## Implementation Plan

### Phase 1: Core Infrastructure Completion

#### 1.1 Event Store Implementation (Completed)

A robust event store implementation has been created with the following features:

- ✅ Storing domain events with metadata
- ✅ Retrieving events by aggregate ID and event type
- ✅ Event versioning and conflict detection
- ✅ Optimistic concurrency control
- ✅ PostgreSQL-backed persistent storage
- ✅ SQL schema generation with proper triggers and indices
- ✅ Event sourcing repository implementation
- ✅ Integration with the CQRS system

The implementation includes:

- `EventStore` abstract base class with clear interface
- `PostgresEventStore` concrete implementation using PostgreSQL
- `EventStoreManager` for schema creation and management
- `EventSourcedRepository` for event sourcing-based repositories
- `EventStoreIntegration` to connect with CQRS components

#### 1.2 Command Handler Enhancements

Enhance command handlers with:

- Unit of work integration
- Transaction management
- Event publication
- Pre/post execution hooks
- Validation framework

```python
# src/uno/core/cqrs.py
class TransactionalCommandHandler[TCommand, TResult](BaseCommandHandler[TCommand, TResult]):
    """Command handler with transaction support."""
    
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]):
        self.unit_of_work_factory = unit_of_work_factory
    
    async def handle(self, command: TCommand) -> TResult:
        async with self.unit_of_work_factory() as uow:
            result = await self._handle(command, uow)
            await self.publish_events()
            return result
    
    @abstractmethod
    async def _handle(self, command: TCommand, uow: UnitOfWork) -> TResult:
        pass
```

#### 1.3 Query Handler Optimizations

Implement optimized query handlers:

- Caching support
- Specialized SQL-based handlers
- Pagination support
- Projection integration

```python
# src/uno/core/cqrs.py
class CachedQueryHandler[TQuery, TResult](BaseQueryHandler[TQuery, TResult]):
    """Query handler with caching support."""
    
    def __init__(self, cache_service: CacheService, ttl_seconds: int = 300):
        self.cache_service = cache_service
        self.ttl_seconds = ttl_seconds
    
    async def handle(self, query: TQuery) -> TResult:
        # Try to get from cache
        cache_key = self._get_cache_key(query)
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get fresh result
        result = await self._handle(query)
        
        # Cache result
        await self.cache_service.set(cache_key, result, self.ttl_seconds)
        
        return result
    
    @abstractmethod
    async def _handle(self, query: TQuery) -> TResult:
        pass
    
    def _get_cache_key(self, query: TQuery) -> str:
        """Get cache key for a query."""
        # Default implementation uses query type and its hash
        return f"{query.query_type}:{hash(frozenset(query.__dict__.items()))}"
```

### Phase 2: Read Model Infrastructure Enhancement

#### 2.1 Repository Implementations (Completed)

Complete repository implementations for different storage backends:

- ✅ PostgreSQL implementation
  - PostgresReadModelRepository
  - PostgresProjectionRepository
  - PostgresQueryRepository
  - PostgresProjectorConfigurationRepository
- ✅ Redis implementation (Using existing RedisCacheRepository)
- ✅ Hybrid (SQL + Redis) implementation
  - HybridReadModelRepository

All implementations have been created in `src/uno/read_model/repository_implementations.py` and are now part of the public API exported from the read_model module.

The PostgreSQL implementations feature:
- Automatic table creation
- JSON data storage for complex structures
- Optimized query capabilities including pagination
- Batch operations for performance
- Type-safe repository interfaces with generics

The Hybrid implementation provides:
- Redis caching for read operations
- Automatic cache invalidation
- Fast read performance with database fallback
- Consistent write operations

Example usage:

```python
# Create a PostgreSQL repository
postgres_repo = PostgresReadModelRepository(
    model_type=CustomerReadModel,
    db_provider=db_provider,
    table_name="customer_read_models"
)

# Create a hybrid repository with caching
hybrid_repo = HybridReadModelRepository(
    model_type=CustomerReadModel,
    db_provider=db_provider,
    redis_cache=redis_cache,
    cache_ttl=3600,  # 1 hour
    cache_prefix="customer:"
)

# Use the repository
customer = await hybrid_repo.get_by_id(ReadModelId("customer-123"))
```

#### 2.2 Projection System Enhancement (Completed)

The projection system has been enhanced with:

- ✅ Batch processing capabilities (BatchProjection)
- ✅ Error handling and retry mechanisms (ResilientProjection)
- ✅ Snapshot support (SnapshotProjector)
- ✅ Projection versioning (VersionedProjection)
- ✅ Progress tracking (ProgressTracker)

The implementation includes these key classes:

1. **VersionedProjection**: Handles different versions of events with method-based dispatch.
   ```python
   class VersionedProjection(Generic[T, EventT], Projection[T, EventT]):
       @property
       def version(self) -> int:
           return 1  # Override in subclasses
       
       async def apply(self, event: EventT) -> Optional[T]:
           event_version = getattr(event, "version", 1)
           method_name = f"apply_v{event_version}"
           if hasattr(self, method_name):
               return await getattr(self, method_name)(event)
           return await self._apply_latest(event)
   ```

2. **ResilientProjection**: Provides error handling and retry capabilities.
   ```python
   class ResilientProjection(Generic[T, EventT], Projection[T, EventT]):
       def __init__(self, 
                  read_model_type: Type[T],
                  event_type: Type[EventT],
                  repository: ReadModelRepository[T],
                  error_strategy: ProjectionErrorHandlingStrategy = ProjectionErrorHandlingStrategy.CONTINUE,
                  max_retries: int = 3):
           # Initialization
       
       async def handle_event(self, event: EventT) -> Result[Optional[T]]:
           # Robust event handling with error tracking
       
       async def retry_failed_events(self) -> Dict[str, bool]:
           # Retry mechanism for failed events
   ```

3. **SnapshotProjector**: Creates and uses snapshots for improved performance.
   ```python
   class SnapshotProjector(Projector):
       def __init__(self,
                  event_bus: EventBus,
                  event_store: EventStore,
                  snapshot_repository: Any,
                  snapshot_config: Optional[SnapshotConfig] = None):
           # Initialization
       
       async def rebuild_for_aggregate(self, aggregate_id: str, aggregate_type: str = None) -> None:
           # Rebuild read models with snapshots
           
       async def _create_snapshot(self, aggregate_id: str, aggregate_type: str, version: int) -> None:
           # Create and manage snapshots
   ```

4. **ProgressTracker**: Tracks event processing progress.
   ```python
   class ProgressTracker:
       def __init__(self, projection_id: str, repository: Optional[Any] = None):
           # Progress tracking initialization
           
       async def record_progress(self, position: int, timestamp: Optional[datetime] = None) -> None:
           # Record processing position
           
       async def save_checkpoint(self) -> None:
           # Persist progress state
   ```

These enhancements provide robust capabilities for handling large event streams, recovering from failures, and optimizing rebuilding of read models.

#### 2.3 Query Service Enhancement ✅

The query service has been enhanced with the following features:

- ✅ Support for complex query criteria with flexible filtering
- ✅ Full-text search capabilities with vector search integration
- ✅ Sorting, filtering, and pagination
- ✅ Aggregation functions (sum, avg, min, max, count)
- ✅ Integration with PostgreSQL vector search
- ✅ Integration with Apache AGE knowledge graph
- ✅ Hybrid search combining vector and graph capabilities
- ✅ Performance tracking and query metrics
- ✅ Caching and optimization strategies

The implementation includes these key classes:

1. **ReadModelQueryService**: Base query service with core functionality
   ```python
   class ReadModelQueryService(Generic[T]):
       """Service for querying read models."""
       
       def __init__(
           self,
           repository: ReadModelRepository[T],
           model_type: Type[T],
           cache: Optional[ReadModelCache[T]] = None,
           logger: Optional[logging.Logger] = None
       ):
           # Initialization
           
       async def get_by_id(self, id: str) -> Optional[T]:
           """Get a read model by ID."""
           # Implementation with caching
           
       async def find(self, criteria: Dict[str, Any]) -> List[T]:
           """Find read models matching criteria."""
           # Implementation of criteria-based searching
           
       async def paginate(self, query: PaginatedQuery[T]) -> PaginatedResult[T]:
           """Paginate query results."""
           # Implementation of pagination
   ```

2. **EnhancedQueryService**: Advanced search capabilities
   ```python
   class EnhancedQueryService(ReadModelQueryService[T]):
       """Enhanced query service with advanced search capabilities."""
       
       def __init__(
           self,
           repository: ReadModelRepository[T],
           model_type: Type[T],
           cache: Optional[ReadModelCache[T]] = None,
           graph_service: Optional[Any] = None,
           vector_service: Optional[Any] = None,
           logger: Optional[logging.Logger] = None
       ):
           # Initialization with graph and vector services
       
       async def search(self, query: SearchQuery[T]) -> PaginatedResult[T]:
           """Perform a full-text search on read models."""
           # Implementation with vector search integration
           
       async def aggregate(self, query: AggregateQuery[T]) -> List[Dict[str, Any]]:
           """Perform aggregation operations on read models."""
           # Implementation with aggregation functions
           
       async def graph_query(self, query: GraphQuery[T]) -> List[T]:
           """Perform a graph-based query."""
           # Implementation with Apache AGE integration
           
       async def hybrid_query(self, query: HybridQuery[T]) -> PaginatedResult[T]:
           """Perform a hybrid query combining vector and graph search."""
           # Implementation blending vector and graph results
   ```

3. **QueryMetrics**: Performance tracking and analysis
   ```python
   class QueryMetrics(BaseModel):
       """Metrics for query execution."""
       
       query_id: str
       start_time: datetime
       end_time: Optional[datetime] = None
       duration_ms: Optional[float] = None
       cache_hit: bool = False
       result_count: int = 0
       query_type: str = ""
       
       def complete(self, result_count: int) -> None:
           """Mark the query as complete."""
           # Implementation for tracking completion
   ```

This enhances the query system with sophisticated search capabilities that leverage both vector search and graph traversal for high-quality results, while maintaining performance through metrics tracking and caching.

### Phase 3: Integration and API

#### 3.1 CQRS and Read Model Integration

Create integration points between CQRS and Read Model:

- ReadModelQueryHandler for integrating with the read model
- ProjectionEventHandler for updating read models from events
- Unified configuration system

```python
# src/uno/domain/cqrs_read_model.py
class ReadModelQueryHandler[TQuery, T](BaseQueryHandler[TQuery, T]):
    """Query handler that uses read models."""
    
    def __init__(self, read_model_service: ReadModelService[T]):
        self.read_model_service = read_model_service
    
    async def handle(self, query: TQuery) -> Optional[T]:
        # Convert query to read model query
        read_model_query = self._to_read_model_query(query)
        
        # Execute query against read model service
        result = await self.read_model_service.query(read_model_query)
        
        return result
    
    @abstractmethod
    def _to_read_model_query(self, query: TQuery) -> Query:
        """Convert a domain query to a read model query."""
        pass
```

#### 3.2 FastAPI Integration

Create FastAPI integration components:

- Command endpoint factories
- Query endpoint factories
- WebSocket support for real-time updates
- Authentication and authorization middleware

```python
# src/uno/api/cqrs_integration.py
class CQRSEndpointFactory:
    """Factory for creating CQRS-based FastAPI endpoints."""
    
    @staticmethod
    def create_command_endpoint(
        router: APIRouter,
        path: str,
        command_type: Type[Command[T]],
        response_model: Optional[Type] = None,
        status_code: int = 200,
        **endpoint_kwargs
    ):
        """Create an endpoint that executes a command."""
        
        @router.post(path, response_model=response_model, status_code=status_code, **endpoint_kwargs)
        async def endpoint(
            command_data: command_type,
            mediator = Depends(get_mediator)
        ):
            result = await mediator.execute_command(command_data)
            return result
        
        return endpoint
```

#### 3.3 Testing Infrastructure

Create comprehensive testing infrastructure:

- Command test helpers
- Query test helpers
- Event store mocks
- Repository mocks
- Projection testing utilities

```python
# src/uno/testing/cqrs.py
class CommandTestHarness[TCommand, TResult]:
    """Test harness for command handlers."""
    
    def __init__(self, handler: CommandHandler[TCommand, TResult]):
        self.handler = handler
        self.published_events = []
        
        # Set up event capture
        if hasattr(handler, "add_event"):
            self._original_add_event = handler.add_event
            handler.add_event = self._capture_event
    
    async def execute(self, command: TCommand) -> TResult:
        """Execute a command and capture events."""
        return await self.handler.handle(command)
    
    def _capture_event(self, event: DomainEvent) -> None:
        """Capture an event."""
        self.published_events.append(event)
        if self._original_add_event:
            self._original_add_event(event)
    
    def assert_events_published(self, count: int) -> None:
        """Assert that a certain number of events were published."""
        assert len(self.published_events) == count, \
            f"Expected {count} events, got {len(self.published_events)}"
    
    def assert_event_published(self, event_type: Type[DomainEvent]) -> None:
        """Assert that a certain type of event was published."""
        for event in self.published_events:
            if isinstance(event, event_type):
                return
        assert False, f"Expected event of type {event_type.__name__}"
```

### Phase 4: Documentation and Examples

#### 4.1 API Documentation

Create comprehensive API documentation:

- CQRS architecture overview
- Command and query patterns
- Read model patterns
- Integration with other modules

#### 4.2 Usage Examples

Create detailed usage examples:

- Basic CQRS application
- Event sourcing with CQRS
- Read model projections
- Integration with UnoObj
- Integration with FastAPI

#### 4.3 Performance Guidelines

Document performance best practices:

- Command validation strategies
- Query optimization techniques
- Caching strategies
- Scaling considerations

### Phase 5: Advanced Features

#### 5.1 CQRS Performance Optimizations

Implement performance optimizations:

- Command batching
- Query result caching
- Parallelization of independent operations
- Memory usage optimizations

```python
# src/uno/core/cqrs_optimizations.py
class BatchCommandBus(CommandBus):
    """Command bus that supports batching commands."""
    
    async def execute_batch(self, commands: List[Command]) -> List[Any]:
        """Execute multiple commands in a batch."""
        results = []
        for command in commands:
            result = await self.execute(command)
            results.append(result)
        return results
```

#### 5.2 Read Model Performance Optimizations

Implement read model performance optimizations:

- Multi-level caching
- Specialized query processors
- Materialized views
- Denormalized data structures

```python
# src/uno/read_model/optimizations.py
class MaterializedViewController:
    """Controller for managing materialized views."""
    
    async def refresh_view(self, view_name: str) -> None:
        """Refresh a materialized view."""
        pass
    
    async def refresh_all_views(self) -> None:
        """Refresh all materialized views."""
        pass
```

#### 5.3 Monitoring and Observability

Implement monitoring and observability features:

- Command/query execution metrics
- Performance tracking
- Error rate monitoring
- Health checks

```python
# src/uno/core/cqrs_monitoring.py
class CQRSMetrics:
    """Metrics collector for CQRS operations."""
    
    def __init__(self, metrics_provider):
        self.metrics_provider = metrics_provider
        
        # Command metrics
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
        
        # Query metrics
        self.query_count = metrics_provider.counter(
            name="cqrs_queries_total",
            description="Total number of queries executed",
            labels=["query_type", "success"]
        )
        
        self.query_duration = metrics_provider.histogram(
            name="cqrs_query_duration_seconds",
            description="Query execution duration in seconds",
            labels=["query_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 5]
        )
```

## Implementation Timeline

| Phase | Task | Priority | Estimated Time | Status |
|-------|------|----------|---------------|--------|
| 1.1 | Event Store Implementation | High | 1 week | ✅ Completed |
| 1.2 | Command Handler Enhancements | High | 1 week | ✅ Completed |
| 1.3 | Query Handler Optimizations | High | 1 week | ✅ Completed |
| 2.1 | Repository Implementations | High | 2 weeks | ✅ Completed |
| 2.2 | Projection System Enhancement | Medium | 2 weeks | ✅ Completed |
| 2.3 | Query Service Enhancement | Medium | 1 week | ✅ Completed |
| 3.1 | CQRS and Read Model Integration | High | 1 week | In Progress |
| 3.2 | FastAPI Integration | Medium | 1 week | Pending |
| 3.3 | Testing Infrastructure | Medium | 1 week | Pending |
| 4.1 | API Documentation | Medium | 1 week | Pending |
| 4.2 | Usage Examples | Medium | 1 week | Pending |
| 4.3 | Performance Guidelines | Low | 0.5 week | Pending |
| 5.1 | CQRS Performance Optimizations | Low | 1 week | Pending |
| 5.2 | Read Model Performance Optimizations | Low | 1 week | Pending |
| 5.3 | Monitoring and Observability | Low | 1 week | Pending |

**Total Estimated Time**: 16 weeks  
**Completed**: 6 phases (37.5%)  
**In Progress**: 1 phase (6.25%)  
**Pending**: 8 phases (50%)

## Success Criteria

The implementation will be considered successful when:

1. All planned components are implemented and tested
2. Documentation and examples are complete
3. Integration tests demonstrate the end-to-end functionality
4. Performance tests show acceptable results under load
5. The API is stable and follows consistent patterns
6. The implementation aligns with domain-driven design principles

## Implementation Steps

For each component, the implementation will follow these steps:

1. Design the API and interfaces
2. Implement the core functionality
3. Write comprehensive unit tests
4. Write integration tests
5. Document the component
6. Create usage examples
7. Perform code review
8. Address feedback
9. Merge into the main codebase

## Dependencies

The implementation has the following dependencies:

- Core domain entities and value objects
- Event system for domain events
- Database access infrastructure
- Caching infrastructure
- Dependency injection system
- FastAPI for HTTP endpoints
- Testing infrastructure

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Performance issues with large event stores | High | Medium | Implement pagination, snapshotting, and caching |
| Complexity of integration between modules | Medium | High | Clear interfaces, comprehensive testing, good documentation |
| Compatibility with existing code | High | Medium | Incremental implementation, compatibility layers, thorough testing |
| Learning curve for developers | Medium | Medium | Comprehensive documentation, examples, and tutorials |
| Scalability concerns | High | Low | Design for horizontal scaling, benchmarking, performance testing |

## Conclusion

This implementation plan provides a comprehensive roadmap for completing the CQRS and Read Model modules in the uno framework. By following this plan, we will create a robust, scalable, and maintainable implementation that follows domain-driven design principles and provides a solid foundation for building complex applications.