# Event System Implementations in Uno

This document provides a concise guide to the internal workings of Uno's event systems and how to effectively use them in your applications.

## Event System Architecture

Uno provides two complementary event system implementations:

1. **Core Events System** (`uno.core.events`): A general-purpose, feature-rich event system
2. **Domain Events System** (`uno.domain.event_dispatcher`, `uno.domain.event_store`): A specialized system for Domain-Driven Design (DDD) applications

Both systems share similar concepts but are tailored to different use cases.

## Core Events System Implementation

The Core Events System is designed for flexibility and performance.

### Implementation Details

#### Event Base Class

`UnoEvent` is a Pydantic model with immutable properties (`frozen=True`):

```python
class UnoEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(default_factory=lambda: _cls_name_to_event_type(UnoEvent.__name__))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    topic: Optional[str] = None
```

#### EventBus Implementation

The `EventBus` class maintains a list of subscriptions and dispatches events:

```python
class EventBus:
    def __init__(self, logger=None, max_concurrency=10):
        self.logger = logger or logging.getLogger("uno.events")
        self.max_concurrency = max_concurrency
        self._subscriptions = []  # List of EventSubscription objects
        
    def subscribe(self, event_type, handler, priority=EventPriority.NORMAL, topic_pattern=None):
        # Create and store subscription...
        
    async def publish(self, event):
        # Find matching subscriptions
        matching_subscriptions = [s for s in self._subscriptions if s.matches_event(event)]
        
        # Execute handlers in priority order
        for subscription in matching_subscriptions:
            await subscription.invoke(event)
```

The `publish_async` method runs handlers in parallel with priority grouping:

```python
async def publish_async(self, event):
    # Group subscriptions by priority
    priority_groups = {}
    
    # For each priority level
    for priority in sorted(priority_groups.keys(), key=lambda p: p.value):
        group = priority_groups[priority]
        
        # Execute this priority group concurrently with controlled concurrency
        semaphore = asyncio.Semaphore(self.max_concurrency)
        await asyncio.gather(*(execute_with_semaphore(task) for task in tasks))
```

#### Handler Execution

The `EventHandlerWrapper` manages handler execution with error handling:

```python
async def execute(self, event):
    try:
        # Add context to errors
        async with with_async_error_context(...):
            if isinstance(self.handler, EventHandler):
                # Class-based handler
                result = self.handler.handle(event)
            else:
                # Function-based handler
                result = self.handler(event)
                
            # Await if needed
            if self.is_async:
                await result
    except Exception as e:
        # Wrap exception with context
        raise UnoError(...)
```

### Usage Patterns

#### Creating and Publishing Events

```python
from uno.core.events import UnoEvent, publish_event_async
from pydantic import Field

# Define an event class
class OrderPlacedEvent(UnoEvent):
    order_id: str = Field(...)
    customer_id: str = Field(...)
    amount: Decimal = Field(...)

# Create and publish an event
event = OrderPlacedEvent(
    order_id="order-123",
    customer_id="cust-456",
    amount=Decimal("99.99"),
    topic="orders.placed"  # Optional topic for routing
)

# Async publishing
await publish_event_async(event)
```

#### Handling Events with Handlers

```python
from uno.core.events import event_handler, EventPriority

# Function-based handler with decorator
@event_handler(OrderPlacedEvent, priority=EventPriority.HIGH)
async def notify_order_placed(event: OrderPlacedEvent):
    # High-priority handler runs first
    print(f"High priority: Order {event.order_id} placed")

# Class-based handler
from uno.core.events import EventHandler

class OrderProcessor(EventHandler[OrderPlacedEvent]):
    def __init__(self):
        super().__init__(OrderPlacedEvent)
        
    async def handle(self, event: OrderPlacedEvent):
        print(f"Processing order: {event.order_id}")
```

#### Advanced Event Handling with EventSubscriber

The EventSubscriber base class automatically registers all methods decorated with `@event_handler`:

```python
from uno.core.events import EventSubscriber, event_handler, get_event_bus

class OrderEventSubscriber(EventSubscriber):
    def __init__(self):
        super().__init__(get_event_bus())
        self.processed_orders = []
        
    @event_handler(OrderPlacedEvent)
    async def handle_order_placed(self, event: OrderPlacedEvent):
        self.processed_orders.append(event.order_id)
        
    @event_handler(OrderCanceledEvent)
    async def handle_order_canceled(self, event: OrderCanceledEvent):
        if event.order_id in self.processed_orders:
            self.processed_orders.remove(event.order_id)
```

## Domain Events System Implementation

The Domain Events System is optimized for DDD patterns, including event sourcing.

### Implementation Details

#### EventDispatcher

The `EventDispatcher` routes events to registered handlers:

```python
class EventDispatcher:
    def __init__(self, event_store=None, logger=None):
        self.event_store = event_store
        self.logger = logger or logging.getLogger(__name__)
        self._handlers = {}  # event_type -> [handlers]
        self._wildcard_handlers = []
        
    def subscribe(self, event_type, handler):
        # Register a handler for a specific event type
        
    async def publish(self, event):
        # Save event if we have an event store
        if self.event_store:
            await self.event_store.save_event(event)
            
        # Get handlers and execute them concurrently
        handlers = self._handlers.get(event.event_type, []) + self._wildcard_handlers
        tasks = [asyncio.create_task(safe_execute(h, event)) for h in handlers]
        await asyncio.gather(*tasks)
```

#### PostgresEventStore

The `PostgresEventStore` persists events in a PostgreSQL database:

```python
class PostgresEventStore(EventStore[E]):
    def __init__(self, event_type, table_name="domain_events", schema="public"):
        self.event_type = event_type
        # Initialize table definition...
        
    async def save_event(self, event, aggregate_id=None, metadata=None):
        # Prepare event data
        event_data = event.model_dump()
        
        # Insert into database
        insert_stmt = insert(self.events_table).values(
            event_id=event_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            # Other fields...
        )
        
        async with async_session() as session:
            await session.execute(insert_stmt)
            await session.commit()
```

#### EventSourcedRepository

The `EventSourcedRepository` rebuilds aggregates from their event history:

```python
class EventSourcedRepository(Generic[E]):
    def __init__(self, aggregate_type, event_store, logger=None):
        self.aggregate_type = aggregate_type
        self.event_store = event_store
        self.logger = logger or logging.getLogger(__name__)
        self._snapshots = {}  # Cache for reconstructed aggregates
        
    async def get_by_id(self, id):
        # Get events for this aggregate
        events = await self.event_store.get_events_by_aggregate_id(id)
        
        # Create aggregate and apply events
        aggregate = self.aggregate_type(id=id)
        for event in events:
            self._apply_event(aggregate, event)
            
        return aggregate
        
    async def save(self, aggregate):
        # Save uncommitted events
        events = aggregate.clear_events()
        for event in events:
            await self.event_store.save_event(event)
```

### Usage Patterns

#### Aggregate with Event Sourcing

```python
from uno.domain.models import AggregateRoot
from uno.core.events import UnoEvent

class Order(AggregateRoot):
    def __init__(self, id=None):
        super().__init__(id)
        self.items = []
        self.status = "draft"
        
    def place(self, items):
        # Check invariants
        if not items:
            raise ValueError("Order must have items")
            
        # Record event
        event = UnoEvent(
            event_type="order_placed",
            aggregate_id=str(self.id),
            aggregate_type="Order",
        )
        event.items = items  # Add domain data
        
        # Apply and record event
        self.apply_order_placed(event)
        self.add_event(event)
        
    def apply_order_placed(self, event):
        # Update state based on event
        self.items = event.items
        self.status = "placed"
```

#### Using the Event-Sourced Repository

```python
from uno.domain.event_store import PostgresEventStore, EventSourcedRepository

# Set up event store
event_store = PostgresEventStore(UnoEvent)

# Set up repository
order_repository = EventSourcedRepository(Order, event_store)

# Create and save an aggregate
order = Order()
order.place(items=[{"product_id": "prod-123", "quantity": 2}])
await order_repository.save(order)

# Later, reconstruct from events
reconstructed_order = await order_repository.get(order.id)
```

#### Domain Event Handlers

```python
from uno.domain.event_dispatcher import domain_event_handler, EventDispatcher

# Create a dispatcher
dispatcher = EventDispatcher(event_store)

# Register handlers
@domain_event_handler("order_placed")
async def send_confirmation(event):
    print(f"Sending confirmation for order {event.aggregate_id}")
    
dispatcher.subscribe("order_placed", send_confirmation)

# Publish an event
await dispatcher.publish(order_placed_event)
```

## Integration with PostgreSQL Notifications

The `PostgresEventListener` integrates with PostgreSQL's notification system:

```python
from uno.domain.event_dispatcher import PostgresEventListener

# Create a listener that converts DB notifications to domain events
listener = PostgresEventListener(
    dispatcher=dispatcher,
    event_type=UnoEvent,
    channel="order_events"
)

# Start listening
await listener.start()

# In your database code or trigger:
# NOTIFY order_events, '{"event_type": "order_placed", "aggregate_id": "order-123"}';
```

## Advanced Patterns

### Event Correlation and Causation

For distributed tracing across services:

```python
# Initial event
payment_event = PaymentProcessedEvent(
    payment_id="pmt-123",
    order_id="order-456",
    correlation_id="txn-abc123"  # Transaction identifier
)

# Subsequent event with causality link
shipment_event = OrderShippedEvent(
    order_id="order-456",
    tracking_number="TRACK123",
    correlation_id=payment_event.correlation_id,  # Same correlation ID
    causation_id=payment_event.event_id  # This event was caused by the payment event
)
```

### Batch Processing with Collection

For high-throughput scenarios:

```python
from uno.core.events import collect_event, publish_collected_events_async

# In a bulk order processing function
async def process_bulk_orders(orders):
    for order in orders:
        # Process each order...
        
        # Collect event (don't publish immediately)
        collect_event(OrderProcessedEvent(
            order_id=order.id,
            status="processed"
        ))
    
    # Publish all collected events at once
    await publish_collected_events_async()
```

### Integration with Task Management

For long-running processes:

```python
from uno.core.events import event_handler
from uno.application.tasks import TaskManager

task_manager = TaskManager()

@event_handler(OrderPlacedEvent)
async def schedule_order_processing(event: OrderPlacedEvent):
    # Schedule a task to process the order
    await task_manager.schedule_task(
        "process_order",
        {"order_id": event.order_id},
        schedule_time=datetime.now(UTC) + timedelta(minutes=5)
    )
```

## Performance Optimization

1. **Use Batch Publishing**: For multiple related events
2. **Leverage Event Priorities**: Ensure critical handlers run first
3. **Implement Event Filtering**: Use topics to filter events at source
4. **Consider Async Handling**: For non-critical or long-running handlers
5. **Optimize Event Store**: Use appropriate indexing for your query patterns
6. **Use Snapshots**: For event-sourced aggregates with many events
7. **Leverage Topic Pattern Matching**: For flexible but efficient subscription

## Testing Event Systems

### Testing Event Handlers

```python
import pytest
from uno.core.events import reset_events, initialize_events, get_event_bus, publish_event_sync

@pytest.fixture
def event_system():
    """Reset event system for each test."""
    reset_events()
    initialize_events()
    yield
    reset_events()

def test_order_handler(event_system):
    # Arrange
    mock_handler = MockOrderHandler()
    get_event_bus().subscribe(OrderPlacedEvent, mock_handler)
    
    test_event = OrderPlacedEvent(order_id="test-123")
    
    # Act
    publish_event_sync(test_event)
    
    # Assert
    assert mock_handler.handled_events[0].order_id == "test-123"
```

### Testing Event Sources

```python
async def test_event_sourced_repository():
    # Arrange
    event_store = InMemoryEventStore()
    repository = EventSourcedRepository(Order, event_store)
    
    # Act
    order = Order()
    order.place(items=[...])
    await repository.save(order)
    
    # Get a fresh copy from the repository
    reconstructed = await repository.get(order.id)
    
    # Assert
    assert reconstructed.items == order.items
    assert reconstructed.status == "placed"
```

## Best Practices Summary

1. **Event Design**:
   - Make events immutable and context-rich
   - Use descriptive past-tense naming
   - Include all necessary context but avoid bloat

2. **Handler Implementation**:
   - Keep handlers focused on single responsibilities
   - Use proper error handling in handlers
   - Make handlers idempotent when possible

3. **Event Sourcing**:
   - Follow Command Query Responsibility Segregation (CQRS)
   - Update aggregates only through events
   - Use snapshots for large event streams

4. **Performance**:
   - Use async publishing for non-blocking operations
   - Implement batch processing for high-throughput scenarios
   - Apply appropriate priorities to ensure critical processing

5. **Integration**:
   - Use correlation and causation IDs for traceability
   - Integrate with transaction boundaries when appropriate
   - Consider message brokers for distributed systems