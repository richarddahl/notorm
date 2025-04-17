# CQRS and Read Model Integration

This document provides comprehensive API documentation for the integration between the CQRS (Command Query Responsibility Segregation) and Read Model modules in uno.

## Overview

The CQRS and Read Model integration provides a seamless connection between the command side (write operations) and query side (read operations) of your application. Key features include:

- Event-driven projections that transform domain events into read models
- Specialized query handlers that use read models
- Command handlers that update read models
- Integration with FastAPI for exposing CQRS functionality
- Support for WebSocket real-time updates
- Comprehensive testing utilities

## Core Components

### ReadModelQueryHandler

The `ReadModelQueryHandler` is a specialized query handler that retrieves data from read models:

```python
class ReadModelQueryHandler[TQuery, TResult, TReadModel](
    QueryHandler[TQuery, TResult],
    Generic[TQuery, TResult, TReadModel]
):
    """Query handler that retrieves data from read models."""
    
    def __init__(
        self,
        read_model_service: ReadModelService[TReadModel],
        mapper: Optional[Callable[[TReadModel], TResult]] = None
    ):
        self.read_model_service = read_model_service
        self.mapper = mapper or (lambda x: x)
    
    async def handle(self, query: TQuery) -> Result[TResult]:
        """Handle the query by delegating to the read model service."""
        try:
            # Convert the query to a read model query
            read_model_query = self._to_read_model_query(query)
            
            # Execute the query against the read model service
            result = await self.read_model_service.query(read_model_query)
            
            # Map the result to the expected type
            if result.is_success():
                mapped_result = self.mapper(result.value)
                return Success(mapped_result)
            
            return Failure(result.error)
        except Exception as e:
            return Failure(Error(
                code="read_model_query_error",
                message=str(e)
            ))
    
    @abstractmethod
    def _to_read_model_query(self, query: TQuery) -> ReadModelQuery:
        """Convert a domain query to a read model query."""
        pass
```

### ProjectionEventHandler

The `ProjectionEventHandler` listens for domain events and updates read models accordingly:

```python
class ProjectionEventHandler[TEvent, TReadModel](
    EventHandler[TEvent],
    Generic[TEvent, TReadModel]
):
    """Event handler that updates read models based on domain events."""
    
    def __init__(
        self,
        projection_service: ProjectionService,
        event_type: Type[TEvent],
        read_model_type: Type[TReadModel]
    ):
        self.projection_service = projection_service
        self.event_type = event_type
        self.read_model_type = read_model_type
    
    async def handle(self, event: TEvent) -> None:
        """Handle the event by applying it to projections."""
        await self.projection_service.apply_event(
            event,
            event_type=self.event_type.__name__,
            read_model_type=self.read_model_type.__name__
        )
```

### EventSourcingReadModelCommandHandler

The `EventSourcingReadModelCommandHandler` combines event sourcing with read model updates:

```python
class EventSourcingReadModelCommandHandler[TCommand, TResult](
    TransactionalCommandHandler[TCommand, TResult],
    Generic[TCommand, TResult]
):
    """Command handler that combines event sourcing with read model updates."""
    
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        event_store: EventStore,
        projection_service: ProjectionService
    ):
        super().__init__(unit_of_work_factory)
        self.event_store = event_store
        self.projection_service = projection_service
        self.events = []
    
    async def handle(self, command: TCommand) -> Result[TResult]:
        """Handle the command with event sourcing and read model updates."""
        # Clear events from previous command
        self.events = []
        
        # Handle the command using the parent class
        result = await super().handle(command)
        
        # If successful, store events and update read models
        if result.is_success():
            # Store events
            for event in self.events:
                await self.event_store.append(event)
            
            # Update read models
            for event in self.events:
                await self.projection_service.apply_event(event)
        
        return result
    
    def add_event(self, event: DomainEvent) -> None:
        """Add an event to be stored and processed."""
        self.events.append(event)
```

### CQRSEndpointFactory

The `CQRSEndpointFactory` creates FastAPI endpoints for CQRS operations:

```python
class CQRSEndpointFactory:
    """Factory for creating CQRS-based FastAPI endpoints."""
    
    @staticmethod
    def create_command_endpoint(
        router: APIRouter,
        path: str,
        command_type: Type[Command[T]],
        response_model: Optional[Type] = None,
        status_code: int = 200,
        auth_dependency: Optional[Callable] = None,
        **endpoint_kwargs
    ):
        """Create an endpoint that executes a command."""
        
        dependencies = []
        if auth_dependency:
            dependencies.append(Depends(auth_dependency))
        
        @router.post(
            path,
            response_model=response_model,
            status_code=status_code,
            dependencies=dependencies,
            **endpoint_kwargs
        )
        async def endpoint(
            command_data: command_type,
            mediator: Mediator = Depends(get_mediator)
        ):
            result = await mediator.execute_command(command_data)
            
            if not result.is_success():
                # Convert the error to an HTTP exception
                raise HTTPException(
                    status_code=result.error.status_code or 400,
                    detail=result.error.to_dict()
                )
            
            return result.value
        
        return endpoint
    
    @staticmethod
    def create_query_endpoint(
        router: APIRouter,
        path: str,
        query_type: Type[Query[T]],
        response_model: Optional[Type] = None,
        status_code: int = 200,
        auth_dependency: Optional[Callable] = None,
        **endpoint_kwargs
    ):
        """Create an endpoint that executes a query."""
        
        dependencies = []
        if auth_dependency:
            dependencies.append(Depends(auth_dependency))
        
        @router.get(
            path,
            response_model=response_model,
            status_code=status_code,
            dependencies=dependencies,
            **endpoint_kwargs
        )
        async def endpoint(
            # Extract query parameters from the request
            request: Request,
            mediator: Mediator = Depends(get_mediator)
        ):
            # Convert query parameters to the query object
            query_params = dict(request.query_params)
            path_params = request.path_params
            
            # Combine path and query parameters
            params = {**query_params, **path_params}
            
            # Create the query object
            query = query_type(**params)
            
            # Execute the query
            result = await mediator.execute_query(query)
            
            if not result.is_success():
                # Convert the error to an HTTP exception
                raise HTTPException(
                    status_code=result.error.status_code or 400,
                    detail=result.error.to_dict()
                )
            
            return result.value
        
        return endpoint
    
    @staticmethod
    def create_websocket_endpoint(
        router: APIRouter,
        path: str,
        event_dispatcher: EventDispatcher,
        auth_dependency: Optional[Callable] = None,
        allowed_event_types: Optional[List[str]] = None
    ):
        """Create a WebSocket endpoint for real-time updates."""
        
        @router.websocket(path)
        async def websocket_endpoint(
            websocket: WebSocket,
            event_types: Optional[str] = None
        ):
            await websocket.accept()
            
            # Parse event types from query parameter
            requested_event_types = event_types.split(",") if event_types else []
            
            # Filter event types if allowed_event_types is provided
            if allowed_event_types:
                requested_event_types = [
                    et for et in requested_event_types 
                    if et in allowed_event_types
                ]
            
            # Create subscriber function
            async def on_event(event: DomainEvent):
                event_dict = event.to_dict()
                await websocket.send_json(event_dict)
            
            # Subscribe to events
            subscriptions = []
            for event_type in requested_event_types:
                subscription = await event_dispatcher.subscribe(event_type, on_event)
                subscriptions.append(subscription)
            
            try:
                # Keep the connection alive
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                # Unsubscribe from events when disconnected
                for subscription in subscriptions:
                    await event_dispatcher.unsubscribe(subscription)
```

## Testing Infrastructure

### CommandTestHarness

The `CommandTestHarness` facilitates testing command handlers:

```python
class CommandTestHarness[TCommand, TResult](Generic[TCommand, TResult]):
    """Test harness for command handlers."""
    
    def __init__(self, handler: CommandHandler[TCommand, TResult]):
        self.handler = handler
        self.published_events = []
        
        # Set up event capture
        if hasattr(handler, "add_event"):
            self._original_add_event = handler.add_event
            handler.add_event = self._capture_event
    
    async def execute(self, command: TCommand) -> Result[TResult]:
        """Execute a command and capture events."""
        return await self.handler.handle(command)
    
    def _capture_event(self, event: DomainEvent) -> None:
        """Capture an event."""
        self.published_events.append(event)
        if hasattr(self, "_original_add_event"):
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

### QueryTestHarness

The `QueryTestHarness` facilitates testing query handlers:

```python
class QueryTestHarness[TQuery, TResult](Generic[TQuery, TResult]):
    """Test harness for query handlers."""
    
    def __init__(self, handler: QueryHandler[TQuery, TResult]):
        self.handler = handler
    
    async def execute(self, query: TQuery) -> Result[TResult]:
        """Execute a query."""
        return await self.handler.handle(query)
    
    def mock_read_model_service(
        self,
        mock_service: ReadModelService,
        method_name: str,
        return_value: Any
    ) -> None:
        """Mock a read model service method."""
        if not hasattr(self.handler, "read_model_service"):
            raise ValueError("Handler does not have a read_model_service attribute")
        
        # Store the original method
        original_method = getattr(self.handler.read_model_service, method_name)
        
        # Create a mock method
        async def mock_method(*args, **kwargs):
            return return_value
        
        # Replace the original method with the mock
        setattr(self.handler.read_model_service, method_name, mock_method)
        
        # Store the original method for restoration
        setattr(self, f"_original_{method_name}", original_method)
    
    def restore_read_model_service(self, method_name: str) -> None:
        """Restore a previously mocked read model service method."""
        if not hasattr(self, f"_original_{method_name}"):
            raise ValueError(f"Method {method_name} was not mocked")
        
        # Restore the original method
        original_method = getattr(self, f"_original_{method_name}")
        setattr(self.handler.read_model_service, method_name, original_method)
        
        # Remove the stored original method
        delattr(self, f"_original_{method_name}")
```

### EventStoreTestHarness

The `EventStoreTestHarness` facilitates testing event store operations:

```python
class EventStoreTestHarness:
    """Test harness for event store operations."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.stored_events = []
    
    async def append_event(self, event: DomainEvent) -> None:
        """Append an event to the event store."""
        await self.event_store.append(event)
        self.stored_events.append(event)
    
    async def get_events(self, aggregate_id: str) -> List[DomainEvent]:
        """Get events for an aggregate."""
        return await self.event_store.get_events(aggregate_id)
    
    def assert_events_stored(self, count: int) -> None:
        """Assert that a certain number of events were stored."""
        assert len(self.stored_events) == count, \
            f"Expected {count} events, got {len(self.stored_events)}"
    
    def assert_event_stored(self, event_type: Type[DomainEvent]) -> None:
        """Assert that a certain type of event was stored."""
        for event in self.stored_events:
            if isinstance(event, event_type):
                return
        assert False, f"Expected event of type {event_type.__name__}"
```

### ProjectionTest

The `ProjectionTest` facilitates testing projections:

```python
class ProjectionTest[TReadModel, TEvent](Generic[TReadModel, TEvent]):
    """Test harness for projections."""
    
    def __init__(self, projection: Projection[TReadModel, TEvent]):
        self.projection = projection
    
    async def apply_event(self, event: TEvent) -> Optional[TReadModel]:
        """Apply an event to the projection."""
        return await self.projection.apply(event)
    
    async def apply_events(self, events: List[TEvent]) -> List[Optional[TReadModel]]:
        """Apply multiple events to the projection."""
        results = []
        for event in events:
            result = await self.projection.apply(event)
            results.append(result)
        return results
    
    def assert_read_model_matches(
        self,
        read_model: TReadModel,
        expected_values: Dict[str, Any]
    ) -> None:
        """Assert that a read model has expected values."""
        for key, expected in expected_values.items():
            actual = getattr(read_model, key, None)
            if actual != expected:
                assert False, f"Expected {key}={expected}, got {actual}"
```

### CQRSTestContainer

The `CQRSTestContainer` coordinates testing for CQRS and Read Model components:

```python
class CQRSTestContainer:
    """Container for testing CQRS and Read Model components."""
    
    def __init__(self):
        self.mediator = get_mediator(new_instance=True)
        self.event_dispatcher = EventDispatcher()
        self.event_store = InMemoryEventStore()
        self.read_model_repositories = {}
        self.projection_service = None
        self.command_handlers = {}
        self.query_handlers = {}
    
    def register_command_handler(
        self,
        command_type: Type[Command[T]],
        handler: CommandHandler[Command[T], R]
    ) -> None:
        """Register a command handler."""
        self.mediator.register_command_handler(command_type, handler)
        self.command_handlers[command_type.__name__] = handler
    
    def register_query_handler(
        self,
        query_type: Type[Query[T]],
        handler: QueryHandler[Query[T], R]
    ) -> None:
        """Register a query handler."""
        self.mediator.register_query_handler(query_type, handler)
        self.query_handlers[query_type.__name__] = handler
    
    def create_read_model_repository(
        self,
        model_type: Type[T]
    ) -> ReadModelRepository[T]:
        """Create an in-memory read model repository."""
        repository = InMemoryReadModelRepository(model_type)
        self.read_model_repositories[model_type.__name__] = repository
        return repository
    
    def create_projection_service(self) -> ProjectionService:
        """Create a projection service."""
        if not self.projection_service:
            self.projection_service = ProjectionService(
                projection_repository=InMemoryProjectionRepository(),
                event_dispatcher=self.event_dispatcher
            )
        return self.projection_service
    
    def get_command_test_harness(
        self,
        command_type: Type[Command[T]]
    ) -> Optional[CommandTestHarness[Command[T], Any]]:
        """Get a test harness for a command handler."""
        handler = self.command_handlers.get(command_type.__name__)
        if not handler:
            return None
        return CommandTestHarness(handler)
    
    def get_query_test_harness(
        self,
        query_type: Type[Query[T]]
    ) -> Optional[QueryTestHarness[Query[T], Any]]:
        """Get a test harness for a query handler."""
        handler = self.query_handlers.get(query_type.__name__)
        if not handler:
            return None
        return QueryTestHarness(handler)
    
    def get_event_store_test_harness(self) -> EventStoreTestHarness:
        """Get a test harness for the event store."""
        return EventStoreTestHarness(self.event_store)
    
    async def clean(self) -> None:
        """Clean up the test container."""
        for repository in self.read_model_repositories.values():
            await repository.clear()
        self.mediator = get_mediator(new_instance=True)
        self.event_dispatcher = EventDispatcher()
        self.event_store = InMemoryEventStore()
        self.command_handlers = {}
        self.query_handlers = {}
```

## Usage Examples

### Command Handler with Read Model Updates

```python
# Define a command
class CreateProductCommand(Command[str]):
    name: str
    description: str
    price: Decimal
    category: str

# Define an event
class ProductCreatedEvent(DomainEvent):
    id: str
    name: str
    description: str
    price: Decimal
    category: str

# Define a command handler
class CreateProductCommandHandler(EventSourcingReadModelCommandHandler[CreateProductCommand, str]):
    async def _handle(self, command: CreateProductCommand, uow: UnitOfWork) -> str:
        # Generate ID
        product_id = str(uuid4())
        
        # Create event
        event = ProductCreatedEvent(
            aggregate_id=product_id,
            aggregate_type="Product",
            id=product_id,
            name=command.name,
            description=command.description,
            price=command.price,
            category=command.category
        )
        
        # Add event to be published
        self.add_event(event)
        
        # Return the product ID
        return product_id

# Define a projection
class ProductProjection(Projection[ProductReadModel, ProductCreatedEvent]):
    async def apply(self, event: ProductCreatedEvent) -> Optional[ProductReadModel]:
        # Create a read model from the event
        read_model = ProductReadModel(
            id=ReadModelId(value=event.id),
            version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            data={
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "price": float(event.price),
                "category": event.category
            }
        )
        
        # Save the read model using the repository
        await self.repository.save(read_model)
        
        return read_model
```

### Query Handler with Read Model

```python
# Define a query
class GetProductByIdQuery(Query[Optional[ProductReadModel]]):
    id: str

# Define a read model query handler
class GetProductByIdQueryHandler(ReadModelQueryHandler[GetProductByIdQuery, Optional[Dict], ProductReadModel]):
    def _to_read_model_query(self, query: GetProductByIdQuery) -> ReadModelQuery:
        return ReadModelQuery(
            id=ReadModelId(value=query.id),
            model_type=ProductReadModel
        )

# Define a search query
class SearchProductsQuery(Query[List[ProductReadModel]]):
    search_term: str
    category: Optional[str] = None
    page: int = 1
    page_size: int = 10

# Define a search query handler
class SearchProductsQueryHandler(ReadModelQueryHandler[SearchProductsQuery, PaginatedResult, ProductReadModel]):
    def _to_read_model_query(self, query: SearchProductsQuery) -> SearchQuery:
        filters = {}
        if query.category:
            filters["category"] = query.category
            
        return SearchQuery(
            search_term=query.search_term,
            filters=filters,
            page=query.page,
            page_size=query.page_size,
            model_type=ProductReadModel
        )
```

### FastAPI Integration

```python
# Create a FastAPI app
app = FastAPI()

# Create a mediator
mediator = get_mediator()

# Register handlers
mediator.register_command_handler(CreateProductCommand, create_product_handler)
mediator.register_query_handler(GetProductByIdQuery, get_product_handler)
mediator.register_query_handler(SearchProductsQuery, search_products_handler)

# Create a router
router = APIRouter(prefix="/api/products", tags=["Products"])

# Create endpoints
endpoint_factory = CQRSEndpointFactory()

# Command endpoint
endpoint_factory.create_command_endpoint(
    router=router,
    path="",
    command_type=CreateProductCommand,
    response_model=str,
    status_code=201
)

# Query endpoints
endpoint_factory.create_query_endpoint(
    router=router,
    path="/{id}",
    query_type=GetProductByIdQuery,
    response_model=Dict
)

endpoint_factory.create_query_endpoint(
    router=router,
    path="/search",
    query_type=SearchProductsQuery,
    response_model=PaginatedResult[Dict]
)

# Add the router to the app
app.include_router(router)

# Add a WebSocket endpoint for real-time updates
endpoint_factory.create_websocket_endpoint(
    router=app,
    path="/ws/products",
    event_dispatcher=event_dispatcher,
    allowed_event_types=["ProductCreated", "ProductUpdated", "ProductDeleted"]
)
```

### Testing Example

```python
async def test_create_product_command():
    # Set up test container
    container = CQRSTestContainer()
    
    # Create repositories and services
    product_repository = container.create_read_model_repository(ProductReadModel)
    projection_service = container.create_projection_service()
    
    # Create handler
    handler = CreateProductCommandHandler(
        unit_of_work_factory=lambda: MockUnitOfWork(),
        event_store=container.event_store,
        projection_service=projection_service
    )
    
    # Register handler
    container.register_command_handler(CreateProductCommand, handler)
    
    # Register projection
    projection = ProductProjection(
        repository=product_repository,
        event_type=ProductCreatedEvent
    )
    await projection_service.register_projection(
        event_type=ProductCreatedEvent.__name__,
        projection=projection
    )
    
    # Create test harness
    harness = container.get_command_test_harness(CreateProductCommand)
    
    # Create command
    command = CreateProductCommand(
        name="Test Product",
        description="A test product",
        price=Decimal("29.99"),
        category="Test"
    )
    
    # Execute command
    result = await harness.execute(command)
    
    # Verify result
    assert result.is_success()
    product_id = result.value
    
    # Verify events
    harness.assert_events_published(1)
    harness.assert_event_published(ProductCreatedEvent)
    
    # Verify read model
    read_model = await product_repository.get_by_id(ReadModelId(value=product_id))
    assert read_model is not None
    assert read_model.data["name"] == "Test Product"
    assert read_model.data["price"] == 29.99
```

## Best Practices

1. **Follow Command Query Separation**: Commands change state but return minimal data, while queries return data but don't change state.

2. **Use Meaningful Command and Query Names**:
   - Commands: Use verbs in imperative form (e.g., `CreateProductCommand`, `UpdateOrderCommand`)
   - Queries: Use nouns or descriptive phrases (e.g., `GetProductByIdQuery`, `SearchOrdersQuery`)

3. **Keep Commands and Events Immutable**: Once created, they should not be modified.

4. **Handle Errors Properly**: Use the Result pattern to handle errors and provide meaningful error messages.

5. **Use Dependency Injection**: Inject dependencies like repositories and services into handlers and projections.

6. **Test Each Component Separately**: Use the provided test harnesses to test commands, queries, and projections separately.

7. **Consider Eventual Consistency**: Remember that in CQRS with read models, there may be a delay between command execution and read model updates.

8. **Optimize Read Models for Specific Use Cases**: Design each read model for a specific query scenario.

9. **Use the Right Repository Implementation**: Choose between in-memory, database, or hybrid repositories based on your needs.

10. **Implement Error Handling in Projections**: Use retries and error tracking to handle projection failures.

## Integration with Other Components

### Domain Events

CQRS and Read Model integrate with domain events to propagate state changes:

- Commands publish domain events via the `EventStore` or `EventDispatcher`
- Projections subscribe to specific event types and update read models
- The `EventSourcingReadModelCommandHandler` combines these operations

### Database

The integration leverages uno's database capabilities:

- SQL query optimization for read operations
- Transaction management for write operations
- Optimistic concurrency control
- Connection pooling and health monitoring

### Caching

Read models support multiple caching strategies:

- In-memory caching for frequently accessed data
- Distributed caching with Redis for scaled deployments
- Multi-level caching combining memory and distributed caches
- Cache invalidation based on events or TTL

### API Layer

The integration exposes functionality through FastAPI:

- Automatic endpoint creation for commands and queries
- WebSocket support for real-time updates
- Authentication and authorization middleware
- Swagger documentation

## Conclusion

The CQRS and Read Model integration in uno provides a powerful foundation for building scalable, maintainable applications with clear separation of concerns. By leveraging this integration, you can create applications that handle complex domain logic while providing optimized query capabilities and real-time updates.