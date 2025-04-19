# Domain-Driven Design Guide

This guide provides an overview of how to implement Domain-Driven Design (DDD) using the Uno framework.

## What is Domain-Driven Design?

Domain-Driven Design is an approach to software development that focuses on:

1. **Creating a rich domain model** that captures business concepts and rules
2. **Ubiquitous language** shared between developers and domain experts
3. **Strategic design** with bounded contexts and context mapping
4. **Tactical patterns** such as entities, value objects, aggregates, and repositories

Uno provides comprehensive support for implementing DDD patterns through its domain entity framework.

## Key Domain Concepts

### Entities

Entities are objects with a distinct identity that persists throughout changes:

```python
from uuid import UUID, uuid4
from uno.domain.entity import EntityBase

class User(EntityBase[UUID]):
    """A user in the system."""
    
    username: str
    email: str
    is_active: bool = True
    
    @classmethod
    def create(cls, username: str, email: str) -> "User":
        """Create a new user."""
        return cls(
            id=uuid4(),
            username=username,
            email=email,
            is_active=True
        )
    
    def deactivate(self) -> None:
        """Deactivate the user."""
        if not self.is_active:
            return
        
        self.is_active = False
        self.record_event(UserDeactivated(user_id=self.id))
```

Key features of entities:
- Distinct identity (ID)
- Mutable properties
- Equality based on identity
- Domain methods for behavior
- Event-raising capabilities

### Value Objects

Value objects are immutable objects defined by their attributes rather than identity:

```python
from uno.domain.entity import ValueObject
from decimal import Decimal

class Money(ValueObject):
    """Represents a monetary value with currency."""
    
    amount: Decimal
    currency: str
    
    def add(self, other: "Money") -> "Money":
        """Add another Money value."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        
        return Money(
            amount=self.amount + other.amount,
            currency=self.currency
        )
    
    def multiply(self, factor: Decimal) -> "Money":
        """Multiply by a factor."""
        return Money(
            amount=self.amount * factor,
            currency=self.currency
        )
```

Key features of value objects:
- No identity
- Immutability
- Equality based on attributes
- Self-validation
- Domain methods for operations

### Aggregates

Aggregates are clusters of entities and value objects with a root entity:

```python
from uno.domain.entity import AggregateRoot
from typing import List

class Order(AggregateRoot[UUID]):
    """An order aggregate root."""
    
    customer_id: UUID
    items: List["OrderItem"] = []
    total_amount: Money
    status: str = "created"
    
    @classmethod
    def create(cls, customer_id: UUID, items: List["OrderItem"]) -> "Order":
        """Create a new order."""
        total = Money(amount=Decimal("0"), currency="USD")
        for item in items:
            total = total.add(item.price.multiply(Decimal(item.quantity)))
        
        order = cls(
            id=uuid4(),
            customer_id=customer_id,
            items=items,
            total_amount=total
        )
        
        order.record_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id,
            item_count=len(items),
            total_amount=float(total.amount)
        ))
        
        return order
    
    def add_item(self, item: "OrderItem") -> None:
        """Add an item to the order."""
        if self.status != "created":
            raise ValueError("Cannot add items to a non-draft order")
        
        self.items.append(item)
        self.total_amount = self.total_amount.add(
            item.price.multiply(Decimal(item.quantity))
        )
        
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item.id,
            quantity=item.quantity,
            price=float(item.price.amount)
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
            customer_id=self.customer_id
        ))
```

Key features of aggregates:
- Single entry point through the root entity
- Consistency boundaries
- Transactional consistency
- Event generation for changes
- Business rule enforcement

### Domain Services

Domain services encapsulate operations that don't naturally belong to entities:

```python
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure

class PaymentService(DomainService):
    """Domain service for payment processing."""
    
    def __init__(self, payment_gateway):
        self.payment_gateway = payment_gateway
    
    async def process_payment(self, order: Order, payment_method: PaymentMethod) -> Result[Payment, str]:
        """Process payment for an order."""
        # Business rules that don't belong to Order or PaymentMethod
        if order.status != "placed":
            return Failure("Cannot process payment for an order that hasn't been placed")
        
        if not payment_method.is_valid():
            return Failure("Invalid payment method")
        
        # External operation
        payment_result = await self.payment_gateway.charge(
            amount=order.total_amount.amount,
            currency=order.total_amount.currency,
            payment_method=payment_method
        )
        
        if payment_result.is_success:
            return Success(Payment(
                id=uuid4(),
                order_id=order.id,
                amount=order.total_amount,
                status="completed",
                payment_method=payment_method.type,
                transaction_id=payment_result.transaction_id
            ))
        else:
            return Failure(f"Payment failed: {payment_result.error}")
```

Key features of domain services:
- Stateless operations
- Business logic that doesn't belong to entities
- Operations spanning multiple aggregates
- External system integration

## Repositories

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
        """Find most recent orders."""
        # Implementation details...
    
    async def find_by_status(self, status: str) -> List[Order]:
        """Find orders by status."""
        # Implementation details...
```

Key features of repositories:
- Collection-like interface
- Persistence abstraction
- Query methods
- Transactional support
- Domain-focused API

## Specifications

Specifications encapsulate query criteria in reusable objects:

```python
from uno.domain.entity.specification import Specification

class RecentOrdersSpecification(Specification[Order]):
    """Specification for recent orders."""
    
    def __init__(self, days: int = 7):
        self.days = days
    
    def is_satisfied_by(self, order: Order) -> bool:
        """Check if an order is recent."""
        from datetime import datetime, timedelta
        cutoff = datetime.now(datetime.UTC) - timedelta(days=self.days)
        return order.created_at >= cutoff

class PendingOrdersSpecification(Specification[Order]):
    """Specification for pending orders."""
    
    def is_satisfied_by(self, order: Order) -> bool:
        """Check if an order is pending."""
        return order.status == "placed" and not order.is_delivered

# Combine specifications
recent_pending_orders = RecentOrdersSpecification().and_(PendingOrdersSpecification())
```

Key features of specifications:
- Reusable query criteria
- Combinable with logical operators
- Clear business rule expression
- Independent of persistence mechanism

## Domain Events

Domain events represent meaningful occurrences in the domain:

```python
from uno.core.events import Event
from uuid import UUID
from datetime import datetime

class OrderPlaced(Event):
    """Event raised when an order is placed."""
    
    order_id: UUID
    customer_id: UUID
    
class OrderItemAdded(Event):
    """Event raised when an item is added to an order."""
    
    order_id: UUID
    item_id: UUID
    quantity: int
    price: float
```

Key features of domain events:
- Immutable records of domain changes
- Rich domain context
- Timestamp and identification
- Named with past-tense verbs
- Serializable for persistence

## Application Services

Application services orchestrate operations across multiple domain objects:

```python
from uno.domain.entity import ApplicationService
from uno.core.uow import UnitOfWork
from uno.core.errors.result import Result, Success, Failure

class OrderApplicationService(ApplicationService):
    """Application service for order processing."""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        inventory_service: InventoryService,
        payment_service: PaymentService,
        unit_of_work: UnitOfWork
    ):
        self.order_repository = order_repository
        self.inventory_service = inventory_service
        self.payment_service = payment_service
        self.unit_of_work = unit_of_work
    
    async def place_order(
        self, 
        customer_id: UUID, 
        items: List[dict],
        payment_method: PaymentMethod
    ) -> Result[Order, str]:
        """Place an order with payment."""
        
        async with self.unit_of_work:
            # Check inventory
            inventory_result = await self.inventory_service.check_availability(items)
            if not inventory_result.is_success:
                return Failure(inventory_result.error)
            
            # Create order items
            order_items = [
                OrderItem(
                    id=uuid4(),
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=Money(amount=Decimal(str(item["price"])), currency="USD")
                )
                for item in items
            ]
            
            # Create and save order
            order = Order.create(customer_id, order_items)
            await self.order_repository.add(order)
            
            # Place the order
            order.place()
            await self.order_repository.update(order)
            
            # Process payment
            payment_result = await self.payment_service.process_payment(order, payment_method)
            if not payment_result.is_success:
                return Failure(payment_result.error)
            
            # Update inventory
            await self.inventory_service.reserve_items(items)
            
            return Success(order)
```

Key features of application services:
- Use case implementation
- Orchestration of domain objects
- Transaction management
- Input validation
- Domain event coordination

## Bounded Contexts

Organize your domain into separate bounded contexts:

```
myapp/
├── order/             # Order bounded context
│   ├── domain/
│   │   ├── entities/
│   │   ├── services/
│   │   ├── events/
│   │   └── repositories/
│   ├── application/
│   └── api/
├── customer/          # Customer bounded context
│   ├── domain/
│   ├── application/
│   └── api/
├── inventory/         # Inventory bounded context
│   ├── domain/
│   ├── application/
│   └── api/
└── payment/           # Payment bounded context
    ├── domain/
    ├── application/
    └── api/
```

Key features of bounded contexts:
- Clear boundaries between domains
- Independent models
- Explicit context mapping
- Focused ubiquitous language
- Team ownership

## Best Practices

1. **Start with the Domain**: Focus on the domain model first, then address technical concerns
2. **Use Value Objects**: Use value objects for concepts with no identity
3. **Design Small Aggregates**: Keep aggregates focused and small
4. **Enforce Invariants**: Use entity methods to enforce business rules
5. **Raise Domain Events**: Use events to communicate domain changes
6. **Define Clear Boundaries**: Use bounded contexts to organize large domains
7. **Implement Repository Methods**: Add custom repository methods for domain-specific queries
8. **Prefer Immutability**: Make value objects and entities (when possible) immutable
9. **Apply Specifications**: Use specifications for reusable query criteria
10. **Create Domain Services**: Use domain services for logic that doesn't belong to entities

## Further Resources

- [Entity Framework](entity_framework.md): Detailed guide to the entity framework
- [Repository Pattern](repository_pattern.md): Working with repositories
- [Specification Pattern](specification_pattern.md): Using specifications
- [Aggregates](aggregates.md): Working with aggregate roots
- [Domain Events](domain_events.md): Using domain events