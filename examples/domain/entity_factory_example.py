"""
Example demonstrating the use of entity factories in domain-driven design.

This example shows how to create and use entity factories for a simple e-commerce domain.
"""

from datetime import datetime, timezone
from typing import List, Optional, Set, Dict, Any
from uuid import uuid4

from uno.domain.models import Entity, AggregateRoot, ValueObject, DomainEvent, CommandResult
from uno.domain.factories import (
    EntityFactory, AggregateFactory, ValueObjectFactory,
    create_entity_factory, create_aggregate_factory, create_value_factory,
    FactoryRegistry
)


# Domain Events
class ProductCreatedEvent(DomainEvent):
    """Event emitted when a product is created."""
    product_id: str
    name: str
    price: float


class OrderCreatedEvent(DomainEvent):
    """Event emitted when an order is created."""
    order_id: str
    customer_id: str
    total_amount: float


# Value Objects
class Money(ValueObject):
    """Money value object."""
    amount: float
    currency: str = "USD"
    
    def validate(self) -> None:
        """Validate the money value."""
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")


class Address(ValueObject):
    """Address value object."""
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    
    def validate(self) -> None:
        """Validate the address."""
        if not self.street or not self.city or not self.state or not self.postal_code:
            raise ValueError("All address fields must be provided")


# Entities
class Product(Entity):
    """Product entity."""
    name: str
    description: Optional[str] = None
    price: Money
    sku: str
    stock_quantity: int = 0
    
    def decrease_stock(self, quantity: int) -> bool:
        """
        Decrease stock quantity.
        
        Args:
            quantity: The quantity to decrease
            
        Returns:
            True if successful, False if not enough stock
        """
        if self.stock_quantity < quantity:
            return False
        
        self.stock_quantity -= quantity
        self.update()
        return True
    
    def increase_stock(self, quantity: int) -> None:
        """
        Increase stock quantity.
        
        Args:
            quantity: The quantity to increase
        """
        self.stock_quantity += quantity
        self.update()


class OrderItem(Entity):
    """Order item entity."""
    product_id: str
    product_name: str
    quantity: int
    unit_price: Money
    
    @property
    def total_price(self) -> Money:
        """Calculate the total price for this item."""
        return Money(amount=self.unit_price.amount * self.quantity, currency=self.unit_price.currency)


class Order(AggregateRoot):
    """Order aggregate root."""
    customer_id: str
    shipping_address: Address
    status: str = "pending"
    order_date: datetime = datetime.now(timezone.utc)
    
    def check_invariants(self) -> None:
        """Check that all order invariants are satisfied."""
        # An order must have at least one item
        if not any(isinstance(entity, OrderItem) for entity in self.get_child_entities()):
            raise ValueError("An order must have at least one item")
    
    def add_item(self, item: OrderItem) -> None:
        """
        Add an item to the order.
        
        Args:
            item: The order item to add
        """
        self.add_child_entity(item)
        self.update()
    
    def calculate_total(self) -> Money:
        """Calculate the total amount for the order."""
        total = 0.0
        currency = "USD"
        
        for entity in self.get_child_entities():
            if isinstance(entity, OrderItem):
                total += entity.total_price.amount
                currency = entity.unit_price.currency
                
        return Money(amount=total, currency=currency)
    
    def confirm(self) -> None:
        """Confirm the order."""
        self.status = "confirmed"
        self.update()
        
        # Register an event
        self.register_event(OrderCreatedEvent(
            order_id=str(self.id),
            customer_id=self.customer_id,
            total_amount=self.calculate_total().amount
        ))


# Create factory classes
MoneyFactory = create_value_factory(Money)
AddressFactory = create_value_factory(Address)
ProductFactory = create_entity_factory(Product)
OrderItemFactory = create_entity_factory(OrderItem)
OrderFactory = create_aggregate_factory(Order)


def create_example_order() -> Order:
    """Create an example order using factories."""
    # Create shipping address
    address = AddressFactory.create(
        street="123 Main St",
        city="Anytown",
        state="CA",
        postal_code="12345"
    )
    
    # Create product prices
    price1 = MoneyFactory.create(amount=29.99)
    price2 = MoneyFactory.create(amount=49.99)
    
    # Create order items
    item1 = OrderItemFactory.create(
        product_id="prod-1",
        product_name="Widget",
        quantity=2,
        unit_price=price1
    )
    
    item2 = OrderItemFactory.create(
        product_id="prod-2",
        product_name="Gadget",
        quantity=1,
        unit_price=price2
    )
    
    # Create the order with items
    order = OrderFactory.create_with_children(
        [item1, item2],
        customer_id="cust-123",
        shipping_address=address
    )
    
    # Confirm the order to trigger event registration
    order.confirm()
    
    return order


def setup_factory_registry() -> FactoryRegistry:
    """Set up a factory registry with all factories."""
    registry = FactoryRegistry()
    
    # Register factories
    registry.register_entity_factory(Product, ProductFactory)
    registry.register_entity_factory(OrderItem, OrderItemFactory)
    registry.register_entity_factory(Order, OrderFactory)
    registry.register_value_factory(Money, MoneyFactory)
    registry.register_value_factory(Address, AddressFactory)
    
    return registry


def main() -> None:
    """Run the example."""
    # Create an order using factories
    order = create_example_order()
    
    # Print order details
    print(f"Order ID: {order.id}")
    print(f"Customer ID: {order.customer_id}")
    print(f"Status: {order.status}")
    print(f"Order Date: {order.order_date}")
    print(f"Shipping Address: {order.shipping_address.street}, {order.shipping_address.city}, {order.shipping_address.state}")
    print(f"Total Amount: ${order.calculate_total().amount:.2f}")
    
    # Print order items
    print("\nOrder Items:")
    for entity in order.get_child_entities():
        if isinstance(entity, OrderItem):
            print(f"  - {entity.product_name}: {entity.quantity} x ${entity.unit_price.amount:.2f} = ${entity.total_price.amount:.2f}")
    
    # Print events
    events = order.get_all_events()
    print(f"\nEvents: {len(events)}")
    for event in events:
        print(f"  - {event.event_type} ({event.timestamp})")
    
    # Create a factory registry
    registry = setup_factory_registry()
    
    # Use the registry to create a product
    product_factory = registry.get_entity_factory(Product)
    product = product_factory.create(
        name="Super Widget",
        sku="SW-001",
        price=MoneyFactory.create(amount=39.99),
        stock_quantity=100
    )
    
    print(f"\nCreated product: {product.name} (${product.price.amount:.2f})")


if __name__ == "__main__":
    main()