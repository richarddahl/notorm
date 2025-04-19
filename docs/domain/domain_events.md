# Domain Events in UNO

This document explains Domain Events in the UNO framework. It covers what domain events are, how to implement them, and best practices for their use within a domain-driven design architecture.

## Overview

Domain Events represent significant occurrences within the domain model that domain experts care about. They are a crucial part of a rich domain model and enable loosely coupled communication between different parts of the system.

Key characteristics of Domain Events:
- **Named with past-tense verbs**: They represent something that has already happened
- **Immutable**: Events are facts that have occurred and cannot be changed
- **Rich in context**: They contain all relevant information about what happened
- **Time-stamped**: They record when the event occurred
- **Sourceable**: They track which entity or process triggered the event
- **Serializable**: They can be persisted, transmitted, and reconstructed

## Implementation in UNO

### Basic Domain Event

In UNO, domain events extend the `Event` class from the core events module:

```python
from uno.core.events import Event
from uuid import UUID
from datetime import datetime
from typing import Optional

class OrderPlaced(Event):
    """Event raised when a customer places an order."""
    
    order_id: UUID
    customer_id: UUID
    total_amount: float
    items_count: int
    timestamp: datetime = datetime.now()
    
    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
```

### Recording Events in Entities

Entities can record domain events using the `record_event` method:

```python
from uno.domain.entity import EntityBase, AggregateRoot
from uuid import UUID, uuid4

class Order(AggregateRoot[UUID]):
    """Order aggregate root."""
    
    customer_id: UUID
    items: List["OrderItem"] = []
    status: str = "draft"
    total_amount: float = 0.0
    
    def place(self) -> None:
        """Place the order."""
        if self.status != "draft":
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        self.status = "placed"
        
        # Record the domain event
        self.record_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=self.total_amount,
            items_count=len(self.items)
        ))
```

### Publishing Domain Events

UNO provides an event bus for publishing and subscribing to domain events:

```python
from uno.core.events import EventBus
from uno.core.di import get_container

# Get the event bus from the container
event_bus = get_container().get(EventBus)

# Publishing an event
await event_bus.publish(OrderPlaced(
    order_id=order_id,
    customer_id=customer_id,
    total_amount=total_amount,
    items_count=items_count
))
```

### Handling Domain Events

You can create event handlers by subscribing to events:

```python
from uno.core.events import EventHandler

class OrderEventHandler:
    """Handler for order-related events."""
    
    async def handle_order_placed(self, event: OrderPlaced) -> None:
        """Handle OrderPlaced events."""
        print(f"Order {event.order_id} was placed by customer {event.customer_id}")
        print(f"Total amount: ${event.total_amount:.2f}, Items: {event.items_count}")
        
        # Perform additional business logic here
        # e.g., send confirmation email, update inventory, etc.

# Register the handler with the event bus
handler = OrderEventHandler()
event_bus.subscribe(OrderPlaced, handler.handle_order_placed)
```

### Automatic Event Publishing from Aggregates

UNO can automatically publish domain events from aggregates when using a repository:

```python
from uno.domain.entity import AggregateRepository
from uno.core.events import EventBus

class OrderRepository(AggregateRepository[Order, UUID]):
    """Repository for Order aggregates with event publishing."""
    
    def __init__(self, event_bus: EventBus, **kwargs):
        super().__init__(**kwargs)
        self.event_bus = event_bus
    
    async def add(self, order: Order) -> Order:
        """Add an order to the repository and publish its events."""
        result = await super().add(order)
        
        # Publish all recorded events
        for event in order.events:
            await self.event_bus.publish(event)
        
        # Clear events after publishing
        order.clear_events()
        
        return result
    
    async def update(self, order: Order) -> Order:
        """Update an order in the repository and publish its events."""
        result = await super().update(order)
        
        # Publish all recorded events
        for event in order.events:
            await self.event_bus.publish(event)
        
        # Clear events after publishing
        order.clear_events()
        
        return result
```

## Advanced Domain Event Patterns

### Event Sourcing

Event sourcing uses domain events as the primary persistence mechanism:

```python
from uno.domain.entity import EventSourcedAggregate
from typing import List, Type, Dict, Any

class Order(EventSourcedAggregate[UUID]):
    """Event-sourced Order aggregate."""
    
    customer_id: UUID = None
    items: List[Dict[str, Any]] = []
    status: str = "draft"
    total_amount: float = 0.0
    
    # Apply methods for each event type
    def apply_order_created(self, event: OrderCreated) -> None:
        """Apply OrderCreated event."""
        self.id = event.order_id
        self.customer_id = event.customer_id
        self.status = "draft"
    
    def apply_order_item_added(self, event: OrderItemAdded) -> None:
        """Apply OrderItemAdded event."""
        item = {
            "id": event.item_id,
            "product_id": event.product_id,
            "quantity": event.quantity,
            "unit_price": event.unit_price
        }
        self.items.append(item)
        self.total_amount += item["quantity"] * item["unit_price"]
    
    def apply_order_placed(self, event: OrderPlaced) -> None:
        """Apply OrderPlaced event."""
        self.status = "placed"
    
    # Command methods that generate events
    def create(self, customer_id: UUID) -> None:
        """Create a new order."""
        self.apply_new_event(OrderCreated(
            order_id=uuid4(),
            customer_id=customer_id
        ))
    
    def add_item(self, product_id: UUID, quantity: int, unit_price: float) -> None:
        """Add an item to the order."""
        if self.status != "draft":
            raise ValueError("Cannot add items to a non-draft order")
        
        self.apply_new_event(OrderItemAdded(
            order_id=self.id,
            item_id=uuid4(),
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        ))
    
    def place(self) -> None:
        """Place the order."""
        if self.status != "draft":
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        self.apply_new_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=self.total_amount,
            items_count=len(self.items)
        ))
```

### Event Store

UNO provides an event store for persisting and retrieving domain events:

```python
from uno.core.events.store import EventStore
from uno.core.di import get_container
from typing import List

# Get the event store from the container
event_store = get_container().get(EventStore)

# Store events
await event_store.append_events([
    OrderCreated(order_id=order_id, customer_id=customer_id),
    OrderItemAdded(order_id=order_id, item_id=item_id, product_id=product_id,
                  quantity=quantity, unit_price=unit_price)
])

# Retrieve events for an aggregate
events: List[Event] = await event_store.get_events_for_aggregate(order_id)

# Rebuild aggregate from events
order = Order()
for event in events:
    order.apply_event(event)
```

### Integration Events

Integration events are domain events that are published across bounded contexts:

```python
from uno.core.events import IntegrationEvent

class OrderConfirmed(IntegrationEvent):
    """Integration event raised when an order is confirmed."""
    
    order_id: UUID
    customer_id: UUID
    total_amount: float
    shipping_address: Dict[str, str]
    
    # Additional methods for integration events
    def to_message(self) -> dict:
        """Convert to a message format for external systems."""
        return {
            "event_type": "order.confirmed",
            "payload": {
                "order_id": str(self.order_id),
                "customer_id": str(self.customer_id),
                "total_amount": self.total_amount,
                "shipping_address": self.shipping_address
            }
        }
```

### Event Subscriptions

Managing event subscriptions across the application:

```python
from uno.core.events import EventBus, EventHandler, Event
from typing import Callable, Dict, List, Type, TypeVar

T = TypeVar('T', bound=Event)

class EventSubscriptionManager:
    """Manages event subscriptions across the application."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.subscriptions: Dict[Type[Event], List[Callable]] = {}
    
    def subscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        
        self.subscriptions[event_type].append(handler)
        self.event_bus.subscribe(event_type, handler)
    
    def unsubscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self.subscriptions and handler in self.subscriptions[event_type]:
            self.subscriptions[event_type].remove(handler)
            self.event_bus.unsubscribe(event_type, handler)
    
    def unsubscribe_all(self) -> None:
        """Unsubscribe all handlers."""
        for event_type, handlers in self.subscriptions.items():
            for handler in handlers:
                self.event_bus.unsubscribe(event_type, handler)
        
        self.subscriptions = {}
```

## Best Practices

### Naming Conventions

Domain events should be named with past-tense verbs describing what happened:

```python
# Good names
UserRegistered
OrderPlaced
PaymentReceived
EmailSent
ProductCreated

# Bad names
CreateOrder  # Command, not event
UserInfo     # Not a verb, doesn't describe what happened
UpdateProduct  # Command, not event
```

### Event Content

Include all relevant data in the event:

```python
# Good: Includes all relevant information
class OrderPlaced(Event):
    order_id: UUID
    customer_id: UUID
    order_date: datetime
    total_amount: float
    shipping_address: Dict[str, str]
    items: List[Dict[str, Any]]

# Bad: Missing important context
class OrderPlaced(Event):
    order_id: UUID  # Only includes the ID, missing other important details
```

### Event Versioning

Handle event versioning for long-term storage:

```python
class OrderPlaced_v1(Event):
    """Order placed event (version 1)."""
    order_id: UUID
    customer_id: UUID
    total_amount: float

class OrderPlaced_v2(Event):
    """Order placed event (version 2)."""
    order_id: UUID
    customer_id: UUID
    total_amount: float
    items_count: int
    shipping_address: Dict[str, str]
    
    @classmethod
    def from_v1(cls, event_v1: OrderPlaced_v1, items_count: int, shipping_address: Dict[str, str]) -> "OrderPlaced_v2":
        """Convert from version 1 to version 2."""
        return cls(
            order_id=event_v1.order_id,
            customer_id=event_v1.customer_id,
            total_amount=event_v1.total_amount,
            items_count=items_count,
            shipping_address=shipping_address
        )
```

### Error Handling in Event Handlers

Properly handle errors in event handlers:

```python
from uno.core.errors.result import Result, Success, Failure

class OrderEventHandler:
    async def handle_order_placed(self, event: OrderPlaced) -> Result[None, str]:
        """Handle OrderPlaced events with error handling."""
        try:
            # Process the event
            await self.send_confirmation_email(event.customer_id, event.order_id)
            await self.update_inventory(event.items)
            await self.notify_shipping_department(event.order_id, event.shipping_address)
            return Success(None)
        except Exception as e:
            # Log the error
            self.logger.error(f"Error processing OrderPlaced event: {e}", exc_info=True)
            return Failure(f"Failed to process OrderPlaced event: {str(e)}")
    
    # ... implementation of the methods used above
```

### Testing Domain Events

Test domain event generation and handling:

```python
import pytest
from uuid import uuid4
from datetime import datetime

async def test_order_placed_event_generation():
    # Arrange
    customer_id = uuid4()
    order = Order.create(customer_id)
    product_id = uuid4()
    order.add_item(product_id, 2, 10.0)
    
    # Act
    order.place()
    
    # Assert
    assert len(order.events) == 3  # OrderCreated, OrderItemAdded, OrderPlaced
    placed_event = order.events[2]
    assert isinstance(placed_event, OrderPlaced)
    assert placed_event.order_id == order.id
    assert placed_event.customer_id == customer_id
    assert placed_event.total_amount == 20.0
    assert placed_event.items_count == 1

async def test_order_placed_event_handling(mocker):
    # Arrange
    order_id = uuid4()
    customer_id = uuid4()
    event = OrderPlaced(
        order_id=order_id,
        customer_id=customer_id,
        total_amount=100.0,
        items_count=3
    )
    
    # Create handler with mocked dependencies
    email_service = mocker.Mock()
    inventory_service = mocker.Mock()
    handler = OrderEventHandler(email_service, inventory_service)
    
    # Act
    await handler.handle_order_placed(event)
    
    # Assert
    email_service.send_confirmation.assert_called_once_with(
        customer_id=customer_id,
        order_id=order_id
    )
    inventory_service.update_for_order.assert_called_once_with(order_id)
```

## Domain Event Patterns

### Event-Driven Architecture

Using domain events to create an event-driven architecture:

```python
# Order Bounded Context
class OrderService:
    def __init__(self, order_repository, event_bus):
        self.order_repository = order_repository
        self.event_bus = event_bus
    
    async def place_order(self, customer_id, items):
        # Create and place the order
        order = Order.create(customer_id)
        for item in items:
            order.add_item(item.product_id, item.quantity, item.unit_price)
        
        order.place()
        await self.order_repository.add(order)
        
        # Events are automatically published by the repository

# Inventory Bounded Context
class InventoryService:
    def __init__(self, inventory_repository, event_bus):
        self.inventory_repository = inventory_repository
        self.event_bus = event_bus
        
        # Subscribe to relevant events
        self.event_bus.subscribe(OrderPlaced, self.handle_order_placed)
    
    async def handle_order_placed(self, event: OrderPlaced):
        # Update inventory when an order is placed
        order = await self.order_repository.get(event.order_id)
        for item in order.items:
            await self.reserve_inventory(item.product_id, item.quantity)
    
    async def reserve_inventory(self, product_id, quantity):
        # Implementation details...
        pass

# Notification Bounded Context
class NotificationService:
    def __init__(self, notification_sender, event_bus):
        self.notification_sender = notification_sender
        self.event_bus = event_bus
        
        # Subscribe to relevant events
        self.event_bus.subscribe(OrderPlaced, self.handle_order_placed)
    
    async def handle_order_placed(self, event: OrderPlaced):
        # Send notification when an order is placed
        customer = await self.customer_repository.get(event.customer_id)
        await self.notification_sender.send_email(
            to=customer.email,
            subject="Your order has been placed",
            body=f"Your order #{event.order_id} has been placed. Total: ${event.total_amount}"
        )
```

### CQRS with Domain Events

Implementing Command Query Responsibility Segregation with domain events:

```python
# Command side
class PlaceOrderCommandHandler:
    def __init__(self, order_repository):
        self.order_repository = order_repository
    
    async def handle(self, command: PlaceOrderCommand) -> Result[UUID, str]:
        # Create and place the order
        order = Order.create(command.customer_id)
        for item in command.items:
            order.add_item(item.product_id, item.quantity, item.unit_price)
        
        order.place()
        await self.order_repository.add(order)
        
        # Events are published automatically by the repository
        return Success(order.id)

# Query side (read model)
class OrderReadModel:
    def __init__(self, db_connection, event_bus):
        self.db_connection = db_connection
        self.event_bus = event_bus
        
        # Subscribe to events to update the read model
        self.event_bus.subscribe(OrderCreated, self.handle_order_created)
        self.event_bus.subscribe(OrderPlaced, self.handle_order_placed)
        self.event_bus.subscribe(OrderItemAdded, self.handle_order_item_added)
    
    async def handle_order_created(self, event: OrderCreated):
        # Update the read model when an order is created
        await self.db_connection.execute(
            "INSERT INTO order_summary (id, customer_id, status, total_amount) VALUES ($1, $2, $3, $4)",
            event.order_id, event.customer_id, "draft", 0.0
        )
    
    async def handle_order_item_added(self, event: OrderItemAdded):
        # Update the read model when an item is added
        await self.db_connection.execute(
            "INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES ($1, $2, $3, $4, $5)",
            event.item_id, event.order_id, event.product_id, event.quantity, event.unit_price
        )
        
        # Update the order total
        await self.db_connection.execute(
            "UPDATE order_summary SET total_amount = total_amount + $1 WHERE id = $2",
            event.quantity * event.unit_price, event.order_id
        )
    
    async def handle_order_placed(self, event: OrderPlaced):
        # Update the read model when an order is placed
        await self.db_connection.execute(
            "UPDATE order_summary SET status = $1 WHERE id = $2",
            "placed", event.order_id
        )
    
    async def get_orders_for_customer(self, customer_id: UUID):
        # Query the read model
        return await self.db_connection.fetch(
            "SELECT * FROM order_summary WHERE customer_id = $1 ORDER BY created_at DESC",
            customer_id
        )
```

### Event Replay for Recovery

Using event replay for system recovery:

```python
from uno.core.events.store import EventStore
from typing import Dict, Type

class SystemRecoveryService:
    """Service for recovering system state by replaying events."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def recover_aggregate(self, aggregate_id: UUID, aggregate_class: Type[EventSourcedAggregate]) -> EventSourcedAggregate:
        """Recover an aggregate by replaying its events."""
        # Create a new instance of the aggregate
        aggregate = aggregate_class()
        
        # Get all events for the aggregate
        events = await self.event_store.get_events_for_aggregate(aggregate_id)
        
        # Apply the events in order
        for event in sorted(events, key=lambda e: e.timestamp):
            aggregate.apply_event(event)
        
        return aggregate
    
    async def recover_all_aggregates(self, aggregate_class: Type[EventSourcedAggregate]) -> Dict[UUID, EventSourcedAggregate]:
        """Recover all aggregates of a given type."""
        # Get all aggregate IDs for the given type
        aggregate_ids = await self.event_store.get_aggregate_ids(aggregate_class.__name__)
        
        # Recover each aggregate
        aggregates = {}
        for aggregate_id in aggregate_ids:
            aggregates[aggregate_id] = await self.recover_aggregate(aggregate_id, aggregate_class)
        
        return aggregates
    
    async def replay_all_events(self, handlers: Dict[Type[Event], Callable]) -> None:
        """Replay all events through the given handlers."""
        # Get all events from the store
        events = await self.event_store.get_all_events()
        
        # Process events in chronological order
        for event in sorted(events, key=lambda e: e.timestamp):
            event_type = type(event)
            if event_type in handlers:
                await handlers[event_type](event)
```

## Real-World Example: E-commerce Order Processing

A complete example of using domain events in an e-commerce order processing system:

```python
from uno.core.events import Event, EventBus
from uno.domain.entity import AggregateRoot
from uno.core.uow import UnitOfWork
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

# Domain Events
class OrderCreated(Event):
    order_id: UUID
    customer_id: UUID
    created_at: datetime

class OrderItemAdded(Event):
    order_id: UUID
    item_id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal

class OrderPlaced(Event):
    order_id: UUID
    customer_id: UUID
    shipping_address: Dict[str, str]
    total_amount: Decimal
    items_count: int

class PaymentProcessed(Event):
    order_id: UUID
    payment_id: UUID
    amount: Decimal
    payment_method: str
    status: str

class OrderShipped(Event):
    order_id: UUID
    tracking_number: str
    carrier: str
    shipped_at: datetime

# Aggregate Root
class Order(AggregateRoot[UUID]):
    customer_id: UUID
    items: List[Dict[str, Any]] = []
    status: str = "draft"
    shipping_address: Optional[Dict[str, str]] = None
    payment_status: str = "pending"
    shipping_status: str = "pending"
    created_at: datetime = datetime.now()
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order_id = uuid4()
        order = cls(
            id=order_id,
            customer_id=customer_id,
            created_at=datetime.now()
        )
        
        order.record_event(OrderCreated(
            order_id=order_id,
            customer_id=customer_id,
            created_at=order.created_at
        ))
        
        return order
    
    def add_item(self, product_id: UUID, product_name: str, quantity: int, unit_price: Decimal) -> None:
        """Add an item to the order."""
        if self.status != "draft":
            raise ValueError("Cannot add items to a non-draft order")
        
        item_id = uuid4()
        item = {
            "id": item_id,
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": unit_price
        }
        
        self.items.append(item)
        
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item_id,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price
        ))
    
    def set_shipping_address(self, address: Dict[str, str]) -> None:
        """Set the shipping address."""
        self.shipping_address = address
    
    def place(self) -> None:
        """Place the order."""
        if self.status != "draft":
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        if not self.shipping_address:
            raise ValueError("Cannot place an order without a shipping address")
        
        self.status = "placed"
        
        total_amount = sum(item["quantity"] * item["unit_price"] for item in self.items)
        
        self.record_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            shipping_address=self.shipping_address,
            total_amount=total_amount,
            items_count=len(self.items)
        ))
    
    def process_payment(self, payment_id: UUID, amount: Decimal, payment_method: str) -> None:
        """Process payment for the order."""
        if self.status != "placed":
            raise ValueError(f"Cannot process payment for order with status: {self.status}")
        
        if self.payment_status != "pending":
            raise ValueError(f"Payment already processed with status: {self.payment_status}")
        
        self.payment_status = "completed"
        
        self.record_event(PaymentProcessed(
            order_id=self.id,
            payment_id=payment_id,
            amount=amount,
            payment_method=payment_method,
            status="completed"
        ))
    
    def ship(self, tracking_number: str, carrier: str) -> None:
        """Ship the order."""
        if self.status != "placed":
            raise ValueError(f"Cannot ship order with status: {self.status}")
        
        if self.payment_status != "completed":
            raise ValueError("Cannot ship order with pending payment")
        
        if self.shipping_status != "pending":
            raise ValueError(f"Order already shipped with status: {self.shipping_status}")
        
        self.shipping_status = "shipped"
        
        self.record_event(OrderShipped(
            order_id=self.id,
            tracking_number=tracking_number,
            carrier=carrier,
            shipped_at=datetime.now()
        ))

# Application Service
class OrderService:
    def __init__(
        self,
        order_repository,
        unit_of_work: UnitOfWork,
        event_bus: EventBus
    ):
        self.order_repository = order_repository
        self.unit_of_work = unit_of_work
        self.event_bus = event_bus
    
    async def create_order(self, customer_id: UUID) -> Order:
        """Create a new order."""
        async with self.unit_of_work:
            order = Order.create(customer_id)
            await self.order_repository.add(order)
            return order
    
    async def add_item(self, order_id: UUID, product_id: UUID, product_name: str, quantity: int, unit_price: Decimal) -> Order:
        """Add an item to an order."""
        async with self.unit_of_work:
            order = await self.order_repository.get(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            order.add_item(product_id, product_name, quantity, unit_price)
            await self.order_repository.update(order)
            return order
    
    async def place_order(self, order_id: UUID, shipping_address: Dict[str, str]) -> Order:
        """Place an order."""
        async with self.unit_of_work:
            order = await self.order_repository.get(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            order.set_shipping_address(shipping_address)
            order.place()
            await self.order_repository.update(order)
            return order

# Event Handlers
class InventoryHandler:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository
    
    async def handle_order_placed(self, event: OrderPlaced) -> None:
        """Handle OrderPlaced event to update inventory."""
        # Implementation details...
        print(f"Updating inventory for order {event.order_id}")

class NotificationHandler:
    def __init__(self, notification_service):
        self.notification_service = notification_service
    
    async def handle_order_placed(self, event: OrderPlaced) -> None:
        """Send notification when an order is placed."""
        # Implementation details...
        print(f"Sending order confirmation for order {event.order_id}")
    
    async def handle_payment_processed(self, event: PaymentProcessed) -> None:
        """Send notification when a payment is processed."""
        # Implementation details...
        print(f"Sending payment confirmation for order {event.order_id}")
    
    async def handle_order_shipped(self, event: OrderShipped) -> None:
        """Send notification when an order is shipped."""
        # Implementation details...
        print(f"Sending shipping confirmation for order {event.order_id} with tracking {event.tracking_number}")

# Usage example
async def process_order():
    # Set up services
    event_bus = EventBus()
    order_repository = OrderRepository(event_bus)
    unit_of_work = UnitOfWork()
    order_service = OrderService(order_repository, unit_of_work, event_bus)
    
    # Set up event handlers
    inventory_handler = InventoryHandler(inventory_repository)
    notification_handler = NotificationHandler(notification_service)
    
    # Subscribe handlers to events
    event_bus.subscribe(OrderPlaced, inventory_handler.handle_order_placed)
    event_bus.subscribe(OrderPlaced, notification_handler.handle_order_placed)
    event_bus.subscribe(PaymentProcessed, notification_handler.handle_payment_processed)
    event_bus.subscribe(OrderShipped, notification_handler.handle_order_shipped)
    
    # Process an order
    customer_id = uuid4()
    order = await order_service.create_order(customer_id)
    
    await order_service.add_item(
        order.id,
        uuid4(),
        "Smartphone",
        1,
        Decimal("999.99")
    )
    
    await order_service.add_item(
        order.id,
        uuid4(),
        "Phone Case",
        1,
        Decimal("29.99")
    )
    
    shipping_address = {
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "postal_code": "12345",
        "country": "USA"
    }
    
    # Place the order - this will trigger event handlers
    await order_service.place_order(order.id, shipping_address)
```

## Further Reading

- [Domain-Driven Design](https://domaindrivendesign.org/)
- [Event Storming](https://www.eventstorming.com/)
- [UNO Event Bus Implementation](../core/events/bus.md)
- [UNO Event Store](../core/events/store.md)
- [Aggregates](aggregates.md)
- [Value Objects](value_objects.md)
- [Repository Pattern](repository_pattern.md)