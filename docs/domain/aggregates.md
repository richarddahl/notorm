# Aggregates in UNO

This document explains the Aggregate pattern implementation in the UNO framework's domain entity package. It covers what aggregates are, how to implement them, and best practices for their use.

## Overview

Aggregates are a key tactical pattern in Domain-Driven Design that help manage complex object graphs. An aggregate is a cluster of domain objects that can be treated as a single unit, with a clearly identified root entity (the aggregate root).

Key characteristics of Aggregates:
- **Aggregate Root**: A single entity that serves as the entry point to the aggregate
- **Consistency Boundary**: All objects within the aggregate must be consistent as a whole
- **Transactional Boundary**: Changes within an aggregate are saved in a single transaction
- **Identity**: Only the aggregate root has a global identity; other entities have local identity
- **Reference**: External objects can only hold references to the aggregate root, not its internal parts
- **Invariants**: Business rules that must be satisfied for the aggregate to be valid

## Implementation in UNO

### Aggregate Root

In UNO, aggregate roots extend the `AggregateRoot` class:

```python
from uno.domain.entity import AggregateRoot
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime

class Order(AggregateRoot[UUID]):
    """Order aggregate root."""
    
    customer_id: UUID
    items: List["OrderItem"] = []
    status: str = "draft"
    total_amount: float = 0.0
    created_at: datetime = datetime.now()
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order = cls(
            id=uuid4(),
            customer_id=customer_id
        )
        
        order.record_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id,
            created_at=order.created_at
        ))
        
        return order
    
    def add_item(self, product_id: UUID, quantity: int, unit_price: float) -> None:
        """Add an item to the order."""
        if self.status != "draft":
            raise ValueError("Cannot add items to a non-draft order")
        
        # Create the item
        item = OrderItem(
            id=uuid4(),
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        
        # Add it to the order
        self.items.append(item)
        
        # Update the total amount
        self.total_amount += item.total_price
        
        # Record the event
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        ))
    
    def remove_item(self, item_id: UUID) -> None:
        """Remove an item from the order."""
        if self.status != "draft":
            raise ValueError("Cannot remove items from a non-draft order")
        
        # Find the item
        item = next((i for i in self.items if i.id == item_id), None)
        if item is None:
            raise ValueError(f"Item with ID {item_id} not found in order")
        
        # Remove it from the order
        self.items.remove(item)
        
        # Update the total amount
        self.total_amount -= item.total_price
        
        # Record the event
        self.record_event(OrderItemRemoved(
            order_id=self.id,
            item_id=item_id
        ))
    
    def place(self) -> None:
        """Place the order."""
        if self.status != "draft":
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        self.status = "placed"
        
        self.record_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=self.total_amount
        ))
```

### Entities within Aggregates

Entities within an aggregate have local identity and are accessed through the aggregate root:

```python
from uno.domain.entity import EntityBase
from uuid import UUID

class OrderItem(EntityBase[UUID]):
    """Order item entity within the Order aggregate."""
    
    product_id: UUID
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        """Calculate the total price for this item."""
        return self.quantity * self.unit_price
```

### Value Objects within Aggregates

Value objects can also be part of the aggregate:

```python
from uno.domain.entity import ValueObject
from typing import Optional

class ShippingAddress(ValueObject):
    """Shipping address value object."""
    
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    apartment: Optional[str] = None
    
    def __str__(self) -> str:
        apt = f", Apt {self.apartment}" if self.apartment else ""
        return f"{self.street}{apt}, {self.city}, {self.state} {self.postal_code}, {self.country}"

# Adding the value object to the aggregate
class Order(AggregateRoot[UUID]):
    # ... existing code ...
    shipping_address: Optional[ShippingAddress] = None
    
    def set_shipping_address(self, address: ShippingAddress) -> None:
        """Set the shipping address."""
        self.shipping_address = address
        
        self.record_event(OrderShippingAddressSet(
            order_id=self.id,
            address=str(address)
        ))
```

## Working with Aggregates

### Repository Patterns for Aggregates

Repositories work with aggregates as a single unit:

```python
from uno.domain.entity import AggregateRepository
from typing import List, Optional

class OrderRepository(AggregateRepository[Order, UUID]):
    """Repository for Order aggregates."""
    
    async def find_by_customer(self, customer_id: UUID) -> List[Order]:
        """Find all orders for a customer."""
        from uno.domain.entity.specification import AttributeSpecification
        
        spec = AttributeSpecification("customer_id", customer_id)
        return await self.find(spec)
    
    async def find_draft_orders(self) -> List[Order]:
        """Find all draft orders."""
        from uno.domain.entity.specification import AttributeSpecification
        
        spec = AttributeSpecification("status", "draft")
        return await self.find(spec)
```

### Implementing Aggregate Persistence

Persistence requirements for aggregates:

```python
from uno.infrastructure.database import SqlAlchemyRepository
from sqlalchemy.orm import Session
from typing import List, Optional, Type, Dict, Any

class SqlAlchemyOrderRepository(SqlAlchemyRepository[Order, UUID]):
    """SQLAlchemy implementation of OrderRepository."""
    
    def __init__(self, session: Session):
        super().__init__(Order, session)
    
    async def _save_aggregate(self, aggregate: Order) -> Order:
        """Save the aggregate and all its components."""
        # First save the aggregate root
        saved_root = await self._save_entity(aggregate)
        
        # Then save all items (child entities)
        for item in aggregate.items:
            # Associate the item with the order
            item_dict = item.model_dump()
            item_dict["order_id"] = aggregate.id
            
            await self._save_child_entity(self.OrderItemModel, item_dict)
        
        return saved_root
    
    async def _load_aggregate(self, root_id: UUID) -> Optional[Order]:
        """Load the aggregate with all its components."""
        # Load the aggregate root
        order = await self._load_entity(root_id)
        if order is None:
            return None
        
        # Load all items (child entities)
        items = await self._load_child_entities(
            self.OrderItemModel, 
            {"order_id": root_id}
        )
        
        # Attach items to the order
        order.items = [
            OrderItem(**item) 
            for item in items
        ]
        
        return order
```

## Best Practices

### Designing Effective Aggregates

1. **Keep aggregates small**: Smaller aggregates have better performance and fewer concurrency conflicts
2. **Define clear boundaries**: Clearly define what's inside and outside the aggregate
3. **Choose aggregate roots carefully**: Make the root entity the one that has the most control over the aggregate's invariants
4. **Consider performance**: Balance normalization with query performance
5. **Design for eventual consistency**: Operations spanning multiple aggregates should use eventual consistency
6. **Protect invariants**: All business rules must be enforceable within the aggregate
7. **Implement concurrency control**: Use optimistic or pessimistic concurrency control
8. **Validate commands**: Validate all commands that modify the aggregate
9. **Use domain events**: Publish domain events for aggregate changes

### Aggregate Design Examples

#### Good Aggregate Design

```python
# Good - Customer aggregate with addresses
class Customer(AggregateRoot[UUID]):
    name: str
    email: str
    shipping_addresses: List[Address] = []
    billing_address: Optional[Address] = None
    
    def add_shipping_address(self, address: Address) -> None:
        """Add a shipping address."""
        # Enforce the invariant: maximum of 5 shipping addresses
        if len(self.shipping_addresses) >= 5:
            raise ValueError("Customer cannot have more than 5 shipping addresses")
        
        self.shipping_addresses.append(address)
        
        self.record_event(CustomerShippingAddressAdded(
            customer_id=self.id,
            address=address.model_dump()
        ))
```

#### Poor Aggregate Design

```python
# Poor - Overly complex aggregate
class Order(AggregateRoot[UUID]):
    customer_id: UUID
    items: List[OrderItem] = []
    payments: List[Payment] = []  # Bad: Payment should be its own aggregate
    shipments: List[Shipment] = []  # Bad: Shipment should be its own aggregate
    # ...many more properties and relationships
    
    # This aggregate has too many responsibilities and will
    # be difficult to keep consistent
```

### Common Aggregate Patterns

#### Entity-Value Aggregate

```python
# Entity root with value objects
class Product(AggregateRoot[UUID]):
    name: str
    description: str
    price: Money  # Value object
    dimensions: Dimensions  # Value object
    category: ProductCategory  # Value object
```

#### Entity-Entities Aggregate

```python
# Entity root with child entities
class Invoice(AggregateRoot[UUID]):
    invoice_number: str
    customer_id: UUID
    due_date: date
    lines: List[InvoiceLine] = []  # Child entities
    
    def add_line(self, description: str, amount: float) -> None:
        line = InvoiceLine(
            id=uuid4(),
            description=description,
            amount=amount
        )
        self.lines.append(line)
```

#### Process Aggregate

```python
# Process or transaction aggregate
class PaymentTransaction(AggregateRoot[UUID]):
    payment_method: str
    amount: Money
    status: str = "pending"
    steps: List[TransactionStep] = []
    
    def add_step(self, name: str, status: str) -> None:
        step = TransactionStep(
            id=uuid4(),
            name=name,
            status=status,
            timestamp=datetime.now()
        )
        self.steps.append(step)
        
        # Update overall status based on steps
        if all(s.status == "completed" for s in self.steps):
            self.status = "completed"
        elif any(s.status == "failed" for s in self.steps):
            self.status = "failed"
```

## Advanced Topics

### Aggregate References

How to handle references between aggregates:

```python
# Reference by ID (recommended)
class Order(AggregateRoot[UUID]):
    customer_id: UUID  # Reference to Customer aggregate by ID
    
    async def get_customer(self, customer_repo) -> Customer:
        """Load the customer from the repository."""
        return await customer_repo.get(self.customer_id)
```

### Aggregate Factories

Using factories to create aggregates:

```python
from uno.domain.entity import AggregateFactory

class OrderFactory(AggregateFactory[Order]):
    """Factory for creating Order aggregates."""
    
    def create_order(self, customer_id: UUID, items: List[dict]) -> Order:
        """Create a new order with items."""
        order = Order.create(customer_id)
        
        for item in items:
            order.add_item(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"]
            )
        
        return order
    
    def create_subscription_order(self, customer_id: UUID, subscription_id: UUID) -> Order:
        """Create an order from a subscription."""
        order = Order.create(customer_id)
        order.subscription_id = subscription_id
        
        # Add subscription-specific information
        
        return order
```

### Event Sourcing with Aggregates

Using event sourcing to reconstruct aggregate state:

```python
from uno.domain.entity import EventSourcedAggregate
from typing import List

class Order(EventSourcedAggregate[UUID]):
    """Event-sourced Order aggregate."""
    
    customer_id: UUID = None
    items: List[OrderItem] = []
    status: str = "draft"
    total_amount: float = 0.0
    
    # Apply methods for each event type
    def apply_order_created(self, event: OrderCreated) -> None:
        self.id = event.order_id
        self.customer_id = event.customer_id
        self.created_at = event.created_at
    
    def apply_order_item_added(self, event: OrderItemAdded) -> None:
        item = OrderItem(
            id=event.item_id,
            product_id=event.product_id,
            quantity=event.quantity,
            unit_price=event.unit_price
        )
        self.items.append(item)
        self.total_amount += item.total_price
    
    def apply_order_item_removed(self, event: OrderItemRemoved) -> None:
        item = next((i for i in self.items if i.id == event.item_id), None)
        if item:
            self.items.remove(item)
            self.total_amount -= item.total_price
    
    def apply_order_placed(self, event: OrderPlaced) -> None:
        self.status = "placed"
```

## Real-World Example: E-commerce Order

A complete example of an order aggregate for e-commerce:

```python
from uno.domain.entity import AggregateRoot, EntityBase, ValueObject
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto

# Value objects
class Money(ValueObject):
    amount: Decimal
    currency: str = "USD"
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def multiply(self, factor: Decimal) -> "Money":
        return Money(amount=self.amount * factor, currency=self.currency)

class Address(ValueObject):
    street: str
    city: str
    state: str
    postal_code: str
    country: str

class OrderStatus(Enum):
    DRAFT = auto()
    PLACED = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()

# Entities
class OrderItem(EntityBase[UUID]):
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Money
    
    @property
    def total_price(self) -> Money:
        return self.unit_price.multiply(Decimal(str(self.quantity)))

class OrderDiscount(EntityBase[UUID]):
    code: str
    description: str
    amount: Money
    is_percentage: bool = False
    
    def apply_to(self, price: Money) -> Money:
        if self.is_percentage:
            discount_amount = price.multiply(self.amount.amount / Decimal(100))
            return price.add(Money(amount=-discount_amount.amount, currency=price.currency))
        else:
            return price.add(Money(amount=-self.amount.amount, currency=price.currency))

# Aggregate root
class Order(AggregateRoot[UUID]):
    customer_id: UUID
    items: List[OrderItem] = []
    discounts: List[OrderDiscount] = []
    status: OrderStatus = OrderStatus.DRAFT
    shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order = cls(
            id=uuid4(),
            customer_id=customer_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        order.record_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id,
            created_at=order.created_at
        ))
        
        return order
    
    @property
    def subtotal(self) -> Money:
        """Calculate the subtotal of all items."""
        if not self.items:
            return Money(amount=Decimal("0"))
        
        result = self.items[0].total_price
        for item in self.items[1:]:
            result = result.add(item.total_price)
        
        return result
    
    @property
    def total(self) -> Money:
        """Calculate the total after discounts."""
        result = self.subtotal
        
        for discount in self.discounts:
            result = discount.apply_to(result)
        
        return result
    
    def add_item(self, product_id: UUID, product_name: str, quantity: int, unit_price: Money) -> None:
        """Add an item to the order."""
        if self.status != OrderStatus.DRAFT:
            raise ValueError("Cannot add items to a non-draft order")
        
        # Check if the product is already in the order
        existing_item = next((i for i in self.items if i.product_id == product_id), None)
        
        if existing_item:
            # Update the existing item
            existing_item.quantity += quantity
            
            self.record_event(OrderItemUpdated(
                order_id=self.id,
                item_id=existing_item.id,
                quantity=existing_item.quantity
            ))
        else:
            # Create a new item
            item = OrderItem(
                id=uuid4(),
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price
            )
            
            self.items.append(item)
            
            self.record_event(OrderItemAdded(
                order_id=self.id,
                item_id=item.id,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price.amount
            ))
        
        self.updated_at = datetime.now()
    
    def remove_item(self, item_id: UUID) -> None:
        """Remove an item from the order."""
        if self.status != OrderStatus.DRAFT:
            raise ValueError("Cannot remove items from a non-draft order")
        
        item = next((i for i in self.items if i.id == item_id), None)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found in order")
        
        self.items.remove(item)
        
        self.record_event(OrderItemRemoved(
            order_id=self.id,
            item_id=item_id
        ))
        
        self.updated_at = datetime.now()
    
    def add_discount(self, code: str, description: str, amount: Money, is_percentage: bool = False) -> None:
        """Add a discount to the order."""
        if self.status != OrderStatus.DRAFT:
            raise ValueError("Cannot add discounts to a non-draft order")
        
        discount = OrderDiscount(
            id=uuid4(),
            code=code,
            description=description,
            amount=amount,
            is_percentage=is_percentage
        )
        
        self.discounts.append(discount)
        
        self.record_event(OrderDiscountAdded(
            order_id=self.id,
            discount_id=discount.id,
            code=code,
            amount=amount.amount,
            is_percentage=is_percentage
        ))
        
        self.updated_at = datetime.now()
    
    def set_shipping_address(self, address: Address) -> None:
        """Set the shipping address."""
        self.shipping_address = address
        
        self.record_event(OrderShippingAddressSet(
            order_id=self.id,
            address=address.model_dump()
        ))
        
        self.updated_at = datetime.now()
    
    def set_billing_address(self, address: Address) -> None:
        """Set the billing address."""
        self.billing_address = address
        
        self.record_event(OrderBillingAddressSet(
            order_id=self.id,
            address=address.model_dump()
        ))
        
        self.updated_at = datetime.now()
    
    def place(self) -> None:
        """Place the order."""
        if self.status != OrderStatus.DRAFT:
            raise ValueError(f"Cannot place order with status: {self.status}")
        
        if not self.items:
            raise ValueError("Cannot place an empty order")
        
        if not self.shipping_address:
            raise ValueError("Cannot place an order without a shipping address")
        
        self.status = OrderStatus.PLACED
        self.updated_at = datetime.now()
        
        self.record_event(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=float(self.total.amount)
        ))
    
    def pay(self) -> None:
        """Mark the order as paid."""
        if self.status != OrderStatus.PLACED:
            raise ValueError(f"Cannot pay for order with status: {self.status}")
        
        self.status = OrderStatus.PAID
        self.updated_at = datetime.now()
        
        self.record_event(OrderPaid(
            order_id=self.id,
            amount=float(self.total.amount)
        ))
    
    def ship(self) -> None:
        """Mark the order as shipped."""
        if self.status != OrderStatus.PAID:
            raise ValueError(f"Cannot ship order with status: {self.status}")
        
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.now()
        
        self.record_event(OrderShipped(
            order_id=self.id
        ))
    
    def deliver(self) -> None:
        """Mark the order as delivered."""
        if self.status != OrderStatus.SHIPPED:
            raise ValueError(f"Cannot deliver order with status: {self.status}")
        
        self.status = OrderStatus.DELIVERED
        self.updated_at = datetime.now()
        
        self.record_event(OrderDelivered(
            order_id=self.id
        ))
    
    def cancel(self, reason: str) -> None:
        """Cancel the order."""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
        
        self.record_event(OrderCancelled(
            order_id=self.id,
            reason=reason
        ))
```

## Further Reading

- [Domain-Driven Design](https://domaindrivendesign.org/)
- [Effective Aggregate Design by Vaughn Vernon](https://dddcommunity.org/library/vernon_2011/)
- [Entity Framework](entity_framework.md)
- [Repository Pattern](repository_pattern.md)
- [Domain Events](domain_events.md)
- [Value Objects](value_objects.md)