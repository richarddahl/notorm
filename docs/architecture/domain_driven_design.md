# Domain-Driven Design in Uno

This guide explains how Domain-Driven Design (DDD) principles are implemented in the Uno framework.

## What is Domain-Driven Design?

Domain-Driven Design is an approach to software development that focuses on:

1. **Core Domain**: Identifying and focusing on the core business domain
2. **Ubiquitous Language**: Developing a common language shared by developers and domain experts
3. **Model-Driven Design**: Creating a domain model that reflects business concepts
4. **Bounded Contexts**: Establishing clear boundaries between different parts of the model
5. **Strategic Design**: Making large-scale structure decisions to organize complex systems

The Uno framework provides comprehensive support for implementing DDD concepts and patterns.

## Key DDD Patterns in Uno

### Entities

Entities are objects defined by their identity:

```python
from uuid import UUID, uuid4
from uno.domain.entity import EntityBase

class Order(EntityBase[UUID]):
    """Order entity with a distinct identity."""
    
    customer_id: UUID
    status: str = "created"
    total_amount: float = 0.0
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        return cls(
            id=uuid4(),
            customer_id=customer_id
        )
```

In Uno, entities:
- Have a unique identifier
- Maintain state that can change over time
- Have equality based on identity, not attributes
- Can record domain events

### Value Objects

Value objects are immutable objects defined by their attributes:

```python
from uno.domain.entity import ValueObject
from datetime import date

class DateRange(ValueObject):
    """Date range value object."""
    
    start_date: date
    end_date: date
    
    def __post_init__(self):
        """Validate the date range."""
        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
    
    def includes(self, date_to_check: date) -> bool:
        """Check if a date is within this range."""
        return self.start_date <= date_to_check <= self.end_date
    
    def overlaps_with(self, other: "DateRange") -> bool:
        """Check if this range overlaps with another."""
        return (
            self.start_date <= other.end_date and
            self.end_date >= other.start_date
        )
```

In Uno, value objects:
- Are defined by their attributes, not identity
- Are immutable
- Can be replaced rather than changed
- Encapsulate domain concepts and rules

### Aggregates

Aggregates group related entities and value objects with a root entity:

```python
from uno.domain.entity import AggregateRoot
from typing import List

class Order(AggregateRoot[UUID]):
    """Order aggregate root that manages OrderItems."""
    
    customer_id: UUID
    status: str = "created"
    items: List["OrderItem"] = []
    
    def add_item(self, product_id: UUID, quantity: int, price: float) -> None:
        """Add an item to the order."""
        if self.status != "created":
            raise ValueError("Cannot add items to a non-draft order")
            
        item = OrderItem(
            id=uuid4(),
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        
        self.items.append(item)
        self.recalculate_total()
        
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        ))
    
    def recalculate_total(self) -> None:
        """Recalculate the order total."""
        self.total_amount = sum(item.price * item.quantity for item in self.items)
```

In Uno, aggregates:
- Have a single root entity that controls access
- Maintain consistency boundaries
- Enforce invariants across multiple entities
- Generate domain events for changes

### Domain Events

Domain events represent significant occurrences in the domain:

```python
from uno.core.events import Event
from uuid import UUID
from datetime import datetime

class OrderPlaced(Event):
    """Event raised when an order is placed."""
    
    order_id: UUID
    customer_id: UUID
    total_amount: float
    item_count: int
    
class OrderItemAdded(Event):
    """Event raised when an item is added to an order."""
    
    order_id: UUID
    item_id: UUID
    product_id: UUID
    quantity: int
    price: float
```

In Uno, domain events:
- Are immutable records of domain changes
- Include all relevant context data
- Are named using past tense verbs
- Can be persisted and published
- Enable decoupled components to react to domain changes

### Repositories

Repositories provide a collection-like interface for aggregates:

```python
from uno.domain.entity import EntityRepository
from typing import List, Optional

class OrderRepository(EntityRepository[Order, UUID]):
    """Repository for Order aggregates."""
    
    async def find_by_customer(self, customer_id: UUID) -> List[Order]:
        """Find all orders for a customer."""
        # Implementation details...
    
    async def find_recent(self, limit: int = 10) -> List[Order]:
        """Find the most recent orders."""
        # Implementation details...
```

In Uno, repositories:
- Abstract the data access mechanism
- Return fully-reconstituted domain objects
- Can be swapped for different storage implementations
- May provide domain-specific query methods

### Domain Services

Domain services implement domain logic that doesn't belong to entities:

```python
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure

class PaymentService(DomainService):
    """Domain service for payment processing."""
    
    def __init__(self, payment_gateway):
        self.payment_gateway = payment_gateway
    
    async def process_payment(self, order: Order, payment_method: PaymentMethod) -> Result[Payment, str]:
        """Process a payment for an order."""
        # Business logic that doesn't belong to Order or PaymentMethod
        if order.status != "placed":
            return Failure("Cannot process payment for an order that hasn't been placed")
        
        # External interaction
        payment_result = await self.payment_gateway.charge(
            amount=order.total_amount,
            currency="USD",
            payment_method=payment_method
        )
        
        if not payment_result.success:
            return Failure(f"Payment failed: {payment_result.error}")
        
        # Create domain object
        payment = Payment.create(
            order_id=order.id,
            amount=order.total_amount,
            payment_method=payment_method.type,
            transaction_id=payment_result.transaction_id
        )
        
        return Success(payment)
```

In Uno, domain services:
- Implement business logic that spans multiple entities
- Are stateless
- May coordinate interactions with external systems
- Operate on domain objects

## Tactical Design Patterns

### Factories

Factories create complex domain objects:

```python
from uno.domain.entity import EntityFactory
from typing import List

class OrderFactory(EntityFactory[Order]):
    """Factory for creating Order aggregates."""
    
    def create_order_with_items(
        self, 
        customer_id: UUID, 
        items: List[dict]
    ) -> Order:
        """Create an order with multiple items."""
        order = Order.create(customer_id)
        
        for item in items:
            order.add_item(
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"]
            )
        
        return order
```

### Specifications

Specifications encapsulate query criteria:

```python
from uno.domain.entity.specification import Specification

class ActiveOrderSpecification(Specification[Order]):
    """Specification for active orders."""
    
    def is_satisfied_by(self, order: Order) -> bool:
        """Check if an order is active."""
        return order.status in ["created", "placed", "processing"]

class RecentOrderSpecification(Specification[Order]):
    """Specification for recent orders."""
    
    def __init__(self, days: int = 7):
        self.days = days
    
    def is_satisfied_by(self, order: Order) -> bool:
        """Check if an order is recent."""
        from datetime import datetime, timedelta
        cutoff = datetime.now(datetime.UTC) - timedelta(days=self.days)
        return order.created_at >= cutoff

# Combine specifications
active_recent_orders = ActiveOrderSpecification().and_(RecentOrderSpecification())
```

## Strategic Design Patterns

### Bounded Contexts

Uno encourages organizing code into bounded contexts:

```
myapp/
├── catalog/          # Product catalog bounded context
│   ├── domain/
│   │   ├── entities/
│   │   ├── services/
│   │   └── repositories/
│   ├── application/
│   ├── infrastructure/
│   └── api/
├── ordering/         # Order processing bounded context
│   ├── domain/
│   │   ├── entities/
│   │   ├── services/
│   │   └── repositories/
│   ├── application/
│   ├── infrastructure/
│   └── api/
└── shipping/         # Shipping bounded context
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── api/
```

Each bounded context:
- Has its own domain model
- Uses the ubiquitous language appropriate for its context
- Has well-defined interfaces to other contexts
- May contain different representations of the same real-world concept

### Context Maps

Context maps define relationships between bounded contexts:

```python
# Shared Kernel example (common code between contexts)
from myapp.shared.domain.value_objects import Money, Address

# Customer/Supplier relationship example
from myapp.catalog.api import ProductCatalogFacade

class OrderService:
    """Order service that depends on the Product Catalog."""
    
    def __init__(self, product_catalog: ProductCatalogFacade):
        """Initialize with the product catalog facade."""
        self.product_catalog = product_catalog
    
    async def place_order(self, customer_id: UUID, items: List[dict]) -> Order:
        """Place an order, using the product catalog."""
        # Validate products and prices
        for item in items:
            product = await self.product_catalog.get_product(item["product_id"])
            if not product:
                raise ValueError(f"Product {item['product_id']} not found")
            
            if product.price != item["price"]:
                raise ValueError(f"Invalid price for product {product.id}")
        
        # Create the order
        # ...
```

## Implementing DDD with Uno

### Domain Model Layer

```python
# domain/entities/order.py
from uno.domain.entity import AggregateRoot, ValueObject
from uuid import UUID, uuid4
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class Money(ValueObject):
    """Value object representing a monetary amount."""
    
    amount: Decimal
    currency: str = "USD"

class OrderItem(EntityBase[UUID]):
    """Entity representing an item in an order."""
    
    order_id: UUID
    product_id: UUID
    quantity: int
    price: Money
    
    def total(self) -> Money:
        """Calculate the total price for this item."""
        return Money(
            amount=self.price.amount * self.quantity,
            currency=self.price.currency
        )

class Order(AggregateRoot[UUID]):
    """Order aggregate root."""
    
    customer_id: UUID
    items: List[OrderItem] = []
    status: str = "created"
    created_at: datetime = None
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order = cls(
            id=uuid4(),
            customer_id=customer_id,
            created_at=datetime.now(datetime.UTC)
        )
        
        order.record_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id
        ))
        
        return order
    
    def add_item(self, product_id: UUID, quantity: int, price: Decimal) -> None:
        """Add an item to the order."""
        if self.status != "created":
            raise ValueError("Cannot add items to a non-draft order")
        
        item = OrderItem(
            id=uuid4(),
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price=Money(amount=price)
        )
        
        self.items.append(item)
        
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item.id,
            product_id=product_id,
            quantity=quantity,
            price=float(price)
        ))
    
    def place(self) -> None:
        """Place the order."""
        if self.status != "created":
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        self.status = "placed"
        
        self.record_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=float(self.total_amount().amount),
            item_count=len(self.items)
        ))
    
    def total_amount(self) -> Money:
        """Calculate the total amount for this order."""
        if not self.items:
            return Money(amount=Decimal("0"))
        
        total = Decimal("0")
        currency = self.items[0].price.currency
        
        for item in self.items:
            if item.price.currency != currency:
                raise ValueError(f"Multiple currencies in order: {currency} and {item.price.currency}")
            
            total += item.price.amount * item.quantity
        
        return Money(amount=total, currency=currency)
```

### Application Layer

```python
# application/services/order_service.py
from uno.domain.entity import ApplicationService
from uno.core.uow import UnitOfWork
from uno.core.errors.result import Result, Success, Failure
from typing import List, Dict, Any

class OrderApplicationService(ApplicationService):
    """Application service for order processing."""
    
    def __init__(
        self,
        product_service: ProductService,
        order_repository: OrderRepository,
        payment_service: PaymentService,
        unit_of_work: UnitOfWork
    ):
        self.product_service = product_service
        self.order_repository = order_repository
        self.payment_service = payment_service
        self.unit_of_work = unit_of_work
    
    async def place_order(
        self, 
        customer_id: UUID, 
        items: List[Dict[str, Any]],
        payment_details: Dict[str, Any]
    ) -> Result[Order, str]:
        """Place an order with payment."""
        
        # Transaction boundary
        async with self.unit_of_work:
            # Validate products and prices
            for item in items:
                product_result = await self.product_service.get_product(item["product_id"])
                if not product_result.is_success:
                    return Failure(f"Product validation failed: {product_result.error}")
                
                product = product_result.value
                if product.price != item["price"]:
                    return Failure(f"Price mismatch for product {product.id}")
            
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
            
            # Save order
            await self.order_repository.add(order)
            
            # Process payment
            payment_method = PaymentMethod.from_dict(payment_details)
            payment_result = await self.payment_service.process_payment(order, payment_method)
            
            if not payment_result.is_success:
                return Failure(f"Payment failed: {payment_result.error}")
            
            # Update inventory (handled by domain events)
            
            return Success(order)
```

## Best Practices for DDD in Uno

1. **Focus on the Domain**: Start with understanding the business domain
2. **Develop a Ubiquitous Language**: Use domain terms consistently
3. **Create a Rich Domain Model**: Encapsulate business rules in the model
4. **Use Value Objects**: Create immutable objects for concepts without identity
5. **Define Clear Boundaries**: Use bounded contexts to manage complexity
6. **Express Domain Events**: Use events to communicate significant changes
7. **Use Specifications**: Encapsulate query criteria in specification objects
8. **Validate Invariants**: Enforce rules that must always be true
9. **Repository per Aggregate**: Create repositories for aggregate roots only
10. **Keep Aggregates Small**: Design aggregates to be small and focused

## Tools and Utilities

Uno provides several tools to support DDD implementation:

1. **Entity Framework**: Base classes for entities, value objects, and aggregates
2. **Repository Framework**: Support for implementing repositories
3. **Specification Framework**: Tools for creating and combining specifications
4. **Domain Event Framework**: Infrastructure for raising and handling domain events
5. **Unit of Work Pattern**: Transaction management for aggregate consistency

## Conclusion

Domain-Driven Design in Uno provides a powerful approach to building complex software systems. By focusing on the domain model and using DDD patterns, developers can create maintainable, expressive code that accurately reflects the business domain.

For more detailed guidance on specific DDD components:

- [Entity Framework](../domain/entity_framework.md)
- [Repository Pattern](../domain/repository_pattern.md)
- [Event-Driven Architecture](event_driven_architecture.md)
- [CQRS Pattern](cqrs.md)
- [Bounded Contexts](bounded_contexts.md)