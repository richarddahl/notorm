# Event-Driven Architecture

This guide explains how Event-Driven Architecture (EDA) is implemented in the Uno framework.

## What is Event-Driven Architecture?

Event-Driven Architecture is an architectural pattern where components communicate through events. An event is a significant change in state or a notification that something has happened. In this pattern:

1. Components emit events when something notable happens
2. Other components subscribe to events and react accordingly
3. Event producers and consumers are decoupled
4. Events can be stored for audit, replay, and analytics

Uno provides a comprehensive event system that enables building event-driven applications with strong domain modeling principles.

## Key Concepts

### Events

Events represent something that has happened in the domain:

```python
from uno.core.events import Event
from uuid import UUID
from datetime import datetime

class UserRegistered(Event):
    """Event raised when a new user registers."""
    
    user_id: UUID
    username: str
    email: str
    registration_date: datetime
```

Events in Uno:
- Are immutable value objects
- Have unique identifiers
- Include timestamps
- May contain correlation IDs
- Can include aggregate IDs
- Are serializable

### Event Bus

The event bus manages event publication and subscription:

```python
from uno.core.events import AsyncEventBus, Event

# Create event bus
event_bus = AsyncEventBus()

# Subscribe to events
async def send_welcome_email(event: UserRegistered):
    # Send welcome email logic
    print(f"Sending welcome email to {event.email}")

await event_bus.subscribe("user_registered", send_welcome_email)

# Publish an event
event = UserRegistered(
    user_id=uuid4(),
    username="johndoe",
    email="john@example.com",
    registration_date=datetime.now(datetime.UTC)
)
await event_bus.publish(event)
```

The event bus provides:
- Asynchronous event handling
- Multiple subscribers per event
- Concurrency control
- Error isolation
- Type-based routing

### Event Store

The event store provides persistence for events:

```python
from uno.core.events import PostgresEventStore

# Create event store
event_store = PostgresEventStore(connection_factory)

# Store events
await event_store.append_events([event], aggregate_id=user.id)

# Retrieve events
events = await event_store.get_events_by_aggregate(user.id)
```

The event store enables:
- Event sourcing
- Audit logging
- Event replay
- Temporal querying
- Optimistic concurrency control

### Event Handlers

Event handlers respond to events:

```python
from uno.core.events import SubscriptionManager

# Create subscription manager
subscription_manager = SubscriptionManager(event_bus)

# Register handlers
@subscription_manager.subscribe("user_registered")
async def send_welcome_email(event: UserRegistered):
    # Send welcome email
    pass

@subscription_manager.subscribe("user_registered")
async def update_analytics(event: UserRegistered):
    # Update analytics
    pass

@subscription_manager.subscribe("user_registered")
async def provision_resources(event: UserRegistered):
    # Provision user resources
    pass
```

Event handlers in Uno:
- Are focused on a specific task
- Are independent of each other
- Can run concurrently
- Handle errors without affecting other handlers
- Can be organized by domain context

## Event-Driven Architecture Patterns

### Domain Events

Domain events represent meaningful changes in the domain:

```python
from uno.domain.entity import AggregateRoot
from uno.core.events import Event
from uuid import UUID, uuid4

class OrderPlaced(Event):
    """Event representing an order being placed."""
    
    order_id: UUID
    customer_id: UUID
    total_amount: float

class Order(AggregateRoot[UUID]):
    """Order aggregate root that raises domain events."""
    
    customer_id: UUID
    items: List["OrderItem"] = []
    status: str = "created"
    
    def place(self) -> None:
        """Place the order, raising a domain event."""
        if self.status != "created":
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        self.status = "placed"
        
        # Record domain event
        self.record_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=self.calculate_total()
        ))
```

Domain events:
- Represent business-significant moments
- Use past-tense naming
- Are part of the domain vocabulary
- Capture the complete context of the change
- Are raised by domain entities

### Event Sourcing

Event sourcing uses events as the primary source of truth:

```python
from uno.domain.entity import AggregateRoot
from typing import List

class Order(AggregateRoot[UUID]):
    """Order aggregate with event sourcing support."""
    
    # State properties
    customer_id: UUID
    status: str = "created"
    items: List[OrderItem] = []
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order = cls(id=uuid4(), customer_id=customer_id)
        order.record_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id
        ))
        return order
    
    def add_item(self, product_id: UUID, quantity: int, price: float) -> None:
        """Add an item to the order."""
        # Business logic validation
        if self.status != "created":
            raise ValueError("Cannot add items to a non-draft order")
        
        # Create the item
        item = OrderItem(
            id=uuid4(),
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        
        # Update state
        self.items.append(item)
        
        # Record event
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        ))
    
    @classmethod
    def from_events(cls, id: UUID, events: List[Event]) -> "Order":
        """Reconstruct an order from its history of events."""
        order = cls(id=id)
        
        for event in events:
            if isinstance(event, OrderCreated):
                order.customer_id = event.customer_id
            elif isinstance(event, OrderItemAdded):
                item = OrderItem(
                    id=event.item_id,
                    order_id=order.id,
                    product_id=event.product_id,
                    quantity=event.quantity,
                    price=event.price
                )
                order.items.append(item)
            elif isinstance(event, OrderPlaced):
                order.status = "placed"
            elif isinstance(event, OrderShipped):
                order.status = "shipped"
            # Add other event types as needed
        
        return order
```

Event sourcing provides:
- Complete audit history
- Temporal querying
- Event replay
- Debugging capabilities
- Integration with CQRS

### CQRS with Events

Command Query Responsibility Segregation with events:

```python
# Command side
class OrderCommandService:
    """Service for order commands."""
    
    def __init__(self, event_store, unit_of_work):
        self.event_store = event_store
        self.unit_of_work = unit_of_work
    
    async def place_order(self, customer_id: UUID, items: List[dict]) -> UUID:
        """Place a new order (command)."""
        async with self.unit_of_work:
            # Create order
            order = Order.create(customer_id)
            
            # Add items
            for item in items:
                order.add_item(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
            
            # Place order
            order.place()
            
            # Persist events
            await self.event_store.append_events(
                order.get_uncommitted_events(),
                aggregate_id=order.id
            )
            
            # Clear events from entity
            order.clear_events()
            
            return order.id

# Query side
class OrderQueryService:
    """Service for order queries."""
    
    def __init__(self, read_db):
        self.read_db = read_db
    
    async def get_order_summary(self, order_id: UUID) -> Optional[OrderSummary]:
        """Get order summary (query)."""
        return await self.read_db.find_one(
            "order_summaries",
            {"_id": str(order_id)}
        )

# Event handler that updates the read model
@subscription_manager.subscribe("order_placed")
async def update_order_summary(event: OrderPlaced):
    """Update the order summary read model."""
    # Get order details
    order = await order_repository.get_by_id(event.order_id)
    
    # Create summary
    summary = OrderSummary(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        item_count=len(order.items),
        total_amount=order.calculate_total(),
        created_at=order.created_at
    )
    
    # Save to read database
    await read_db.insert_or_update(
        "order_summaries",
        {"_id": str(order.id)},
        summary.dict()
    )
```

CQRS with events provides:
- Separation of read and write models
- Optimized data structures for queries
- Scalability of read and write sides
- Event-driven updates to read models
- Eventual consistency

### Event-Driven Sagas

Sagas coordinate complex business processes through events:

```python
class OrderSaga:
    """Saga that manages the order fulfillment process."""
    
    def __init__(self, event_bus, command_bus):
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.register_handlers()
    
    def register_handlers(self):
        """Register event handlers for this saga."""
        self.event_bus.subscribe("order_placed", self.handle_order_placed)
        self.event_bus.subscribe("payment_processed", self.handle_payment_processed)
        self.event_bus.subscribe("items_allocated", self.handle_items_allocated)
        self.event_bus.subscribe("allocation_failed", self.handle_allocation_failed)
    
    async def handle_order_placed(self, event: OrderPlaced):
        """When an order is placed, process payment."""
        await self.command_bus.send(ProcessPayment(
            order_id=event.order_id,
            amount=event.total_amount
        ))
    
    async def handle_payment_processed(self, event: PaymentProcessed):
        """When payment is processed, allocate inventory."""
        await self.command_bus.send(AllocateInventory(
            order_id=event.order_id
        ))
    
    async def handle_items_allocated(self, event: ItemsAllocated):
        """When items are allocated, ship the order."""
        await self.command_bus.send(ShipOrder(
            order_id=event.order_id,
            shipping_address=event.shipping_address
        ))
    
    async def handle_allocation_failed(self, event: AllocationFailed):
        """When allocation fails, refund payment."""
        await self.command_bus.send(RefundPayment(
            order_id=event.order_id,
            payment_id=event.payment_id,
            reason="Inventory allocation failed"
        ))
        
        # Also cancel the order
        await self.command_bus.send(CancelOrder(
            order_id=event.order_id,
            reason="Inventory allocation failed"
        ))
```

Event-driven sagas provide:
- Long-running business processes
- Coordination across bounded contexts
- Compensating transactions for failures
- Clear process visualization
- Resilience through event replay

## Integration with Unit of Work

Events integrate seamlessly with Unit of Work for transactional consistency:

```python
from uno.core.uow import UnitOfWork
from uno.domain.entity import AggregateRoot

class OrderService:
    """Service for order operations."""
    
    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work
    
    async def place_order(self, customer_id: UUID, items: List[dict]) -> Order:
        """Place an order with transaction and event publishing."""
        async with self.unit_of_work:
            # Get repositories
            order_repo = self.unit_of_work.get_repository(OrderRepository)
            
            # Create order
            order = Order.create(customer_id)
            
            # Add items
            for item in items:
                order.add_item(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
            
            # Place order (generates events)
            order.place()
            
            # Save order
            await order_repo.add(order)
            
            # Events are automatically collected by UoW and published after successful commit
            return order
```

The Unit of Work:
- Collects events from entities during transaction
- Publishes events only after successful commit
- Prevents event publishing on transaction failure
- Ensures atomicity of state changes and event publishing

## Implementing Event-Driven Architecture

### Event Definition

```python
# domain/events.py
from uno.core.events import Event
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class OrderCreated(Event):
    """Event raised when an order is created."""
    
    order_id: UUID
    customer_id: UUID
    created_at: datetime

class OrderItemAdded(Event):
    """Event raised when an item is added to an order."""
    
    order_id: UUID
    item_id: UUID
    product_id: UUID
    quantity: int
    price: float

class OrderPlaced(Event):
    """Event raised when an order is placed."""
    
    order_id: UUID
    customer_id: UUID
    total_amount: float
    item_count: int
```

### Event Publishing

```python
# domain/entities/order.py
from uno.domain.entity import AggregateRoot
from myapp.domain.events import OrderCreated, OrderItemAdded, OrderPlaced

class Order(AggregateRoot[UUID]):
    """Order aggregate root that publishes events."""
    
    # ...existing implementation...
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order = cls(
            id=uuid4(),
            customer_id=customer_id,
            created_at=datetime.now(datetime.UTC)
        )
        
        # Record domain event
        order.record_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id,
            created_at=order.created_at
        ))
        
        return order
    
    # ...other methods...
```

### Event Handling

```python
# application/event_handlers.py
from uno.core.events import SubscriptionManager
from myapp.domain.events import OrderCreated, OrderPlaced
from myapp.infrastructure.email import EmailService
from myapp.infrastructure.analytics import AnalyticsService

subscription_manager = SubscriptionManager(event_bus)

@subscription_manager.subscribe("order_created")
async def log_order_created(event: OrderCreated):
    """Log order creation."""
    logger.info(f"Order created: {event.order_id}")

@subscription_manager.subscribe("order_placed")
async def send_order_confirmation(event: OrderPlaced):
    """Send order confirmation email."""
    email_service = EmailService()
    await email_service.send_order_confirmation(event.order_id)

@subscription_manager.subscribe("order_placed")
async def update_sales_analytics(event: OrderPlaced):
    """Update sales analytics."""
    analytics_service = AnalyticsService()
    await analytics_service.record_sale(
        order_id=event.order_id,
        customer_id=event.customer_id,
        amount=event.total_amount
    )
```

### Subscription Management

```python
# main.py
from uno.core.events import EventBus, SubscriptionManager
from myapp.application.event_handlers import subscription_manager

async def startup():
    """Application startup function."""
    # Create event bus
    event_bus = EventBus()
    
    # Create subscription manager
    subscription_manager = SubscriptionManager(event_bus)
    
    # Start all subscriptions
    await subscription_manager.start_all()
    
    # Add to dependency injection container
    container.register(EventBus, event_bus)
    container.register(SubscriptionManager, subscription_manager)

async def shutdown():
    """Application shutdown function."""
    # Stop all subscriptions
    await subscription_manager.stop_all()
```

## Best Practices

1. **Event Naming**: Use past tense verbs (e.g., `OrderPlaced`, `PaymentProcessed`)
2. **Event Content**: Include all necessary data in the event
3. **Immutability**: Events should be immutable
4. **Event Versioning**: Consider versioning for long-lived events
5. **Idempotent Handlers**: Design handlers to be idempotent
6. **Focused Handlers**: Keep handlers small and focused
7. **Error Handling**: Implement proper error handling in event handlers
8. **Event Documentation**: Document events as part of the domain vocabulary
9. **Event Schemas**: Define clear schemas for events
10. **Monitoring**: Implement monitoring for event processing

## Advanced Patterns

### Event Upcasting

Handle event schema evolution:

```python
from uno.core.events import EventUpcastingRegistry

# Create upcasting registry
upcasting_registry = EventUpcastingRegistry()

# Register upcasters
@upcasting_registry.register("order_placed", version=1, target_version=2)
def upcast_order_placed_v1_to_v2(event_data: dict) -> dict:
    """Convert OrderPlaced event from v1 to v2 format."""
    # v1 had total_amount as int (cents), v2 uses float (dollars)
    if "total_amount" in event_data:
        event_data["total_amount"] = event_data["total_amount"] / 100.0
    
    # v2 adds item_count field
    if "item_count" not in event_data:
        event_data["item_count"] = 0
    
    return event_data
```

### Event Replay

Replay events for rebuilding state:

```python
async def rebuild_read_models():
    """Rebuild all read models from events."""
    # Get all events from the beginning of time
    events = await event_store.get_all_events(batch_size=1000)
    
    # Process events in order
    for event in events:
        # Reset handler state if needed
        if event.type == "order_created":
            # Re-create order summary
            await update_order_summary(event)
        elif event.type == "order_placed":
            # Update order status
            await update_order_status(event)
        # ...other event types...
```

### Event Sourcing with Snapshots

Optimize event sourcing with snapshots:

```python
class OrderRepository:
    """Repository for Order aggregates using event sourcing with snapshots."""
    
    def __init__(self, event_store, snapshot_store):
        self.event_store = event_store
        self.snapshot_store = snapshot_store
    
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get an order by ID, using snapshots for optimization."""
        # Try to get snapshot first
        snapshot = await self.snapshot_store.get_latest(order_id)
        
        if snapshot:
            # Get events after snapshot
            events = await self.event_store.get_events_by_aggregate(
                order_id, 
                after_sequence=snapshot.sequence
            )
            
            # Reconstitute from snapshot and newer events
            order = Order.from_snapshot(snapshot)
            for event in events:
                order.apply(event)
                
            return order
        else:
            # No snapshot, get all events
            events = await self.event_store.get_events_by_aggregate(order_id)
            if not events:
                return None
                
            # Reconstitute from all events
            return Order.from_events(order_id, events)
    
    async def save(self, order: Order) -> None:
        """Save an order with its new events."""
        # Get uncommitted events
        events = order.get_uncommitted_events()
        
        # Save events
        await self.event_store.append_events(events, aggregate_id=order.id)
        
        # Create snapshot if needed
        if self._should_create_snapshot(order):
            await self.snapshot_store.save(order.create_snapshot())
        
        # Clear uncommitted events
        order.clear_events()
    
    def _should_create_snapshot(self, order: Order) -> bool:
        """Determine if we should create a snapshot."""
        # Create snapshot every 100 events
        return order.version % 100 == 0
```

## Tools and Utilities

Uno provides several tools to support event-driven architecture:

1. **Event Bus**: For event publishing and subscription
2. **Event Store**: For event persistence
3. **Subscription Manager**: For managing event handlers
4. **Event Sourcing Support**: For event-sourced aggregates
5. **Unit of Work Integration**: For transactional events
6. **Monitoring Tools**: For event processing metrics

## Conclusion

Event-Driven Architecture in Uno provides a powerful approach to building decoupled, scalable systems. By using events as the primary means of communication, components can evolve independently while maintaining clear business process flows and audit trails.

For more detailed guidance on specific event components:

- [Event System](../core/events/index.md): Core event system documentation
- [Domain Events](../domain/domain_events.md): Using events in the domain layer
- [CQRS Pattern](cqrs.md): Command Query Responsibility Segregation
- [Event Sourcing](event_sourcing.md): Event-sourced entities and aggregates