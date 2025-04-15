# Business Logic Best Practices

This document provides comprehensive guidance on implementing business logic using the UnoObj system. It covers best practices, patterns, and examples to help you build maintainable and robust business logic layers.

## Core Principles for Business Logic

When implementing business logic with UnoObj, follow these core principles:

1. **Single Responsibility**: Each UnoObj class should focus on a single domain concept
2. **Rich Domain Model**: Implement behavior directly in domain objects, not in services
3. **Validation at the Source**: Validate data as early as possible
4. **Encapsulation**: Hide implementation details and expose clean interfaces
5. **Domain Language**: Use naming that reflects your business domain
6. **Immutability When Possible**: Make objects immutable where appropriate
7. **Tell, Don't Ask**: Tell objects what to do rather than asking for their state

## Structuring Business Logic

### Domain-Driven Design Patterns

UnoObj works well with Domain-Driven Design (DDD) patterns:

```python
from decimal import Decimal
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.core.errors.base import UnoError, ErrorCode
from datetime import datetime
from typing import List, Optional

# Value Object - Price with currency
class Price:
    def __init__(self, amount: Decimal, currency: str = "USD"):
        if amount < 0:
            raise ValueError("Price cannot be negative")
        self.amount = amount
        self.currency = currency
    
    def __eq__(self, other):
        if not isinstance(other, Price):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def convert_to(self, target_currency: str, exchange_rate: Decimal) -> 'Price':
        """Convert price to another currency."""
        if target_currency == self.currency:
            return self
        return Price(self.amount * exchange_rate, target_currency)

# Domain model using UnoObj
class OrderModel(UnoModel):
    __tablename__ = "orders"
    
    customer_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
    order_date: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False, default="USD")

class Order(UnoObj[OrderModel]):
    customer_id: str
    order_date: datetime
    status: str
    total_amount: Decimal
    currency: str = "USD"
    
    # Lifecycle status constants
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
        "list_schema": UnoSchemaConfig(include_fields={"id", "customer_id", "order_date", "status", "total_amount", "currency"}),
    }
    
    # Business logic methods
    async def confirm(self) -> bool:
        """Confirm the order, moving it from pending to confirmed state."""
        if self.status != self.STATUS_PENDING:
            raise UnoError(
                f"Cannot confirm order that is not pending (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_PENDING
            )
        
        self.status = self.STATUS_CONFIRMED
        await self.save()
        
        # Trigger confirmation events or side effects
        await self._notify_customer_of_confirmation()
        return True
    
    async def cancel(self, reason: str) -> bool:
        """Cancel the order if it hasn't been shipped yet."""
        if self.status in [self.STATUS_SHIPPED, self.STATUS_DELIVERED]:
            raise UnoError(
                f"Cannot cancel order that has been {self.status}",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status
            )
        
        # Record cancellation
        self.status = self.STATUS_CANCELLED
        await self.save()
        
        # Trigger cancellation side effects
        await self._process_refund()
        await self._notify_customer_of_cancellation(reason)
        return True
    
    async def ship(self, tracking_number: str) -> bool:
        """Mark the order as shipped."""
        if self.status != self.STATUS_CONFIRMED:
            raise UnoError(
                f"Cannot ship order that is not confirmed (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_CONFIRMED
            )
        
        self.status = self.STATUS_SHIPPED
        # Assuming we have a tracking_number field or we're updating a related shipment object
        await self.save()
        
        # Trigger shipping events
        await self._notify_customer_of_shipping(tracking_number)
        return True
    
    async def deliver(self) -> bool:
        """Mark the order as delivered."""
        if self.status != self.STATUS_SHIPPED:
            raise UnoError(
                f"Cannot mark as delivered an order that hasn't been shipped (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_SHIPPED
            )
        
        self.status = self.STATUS_DELIVERED
        await self.save()
        
        # Trigger delivery events
        await self._notify_customer_of_delivery()
        return True
    
    @property
    def price(self) -> Price:
        """Get the price as a value object."""
        return Price(self.total_amount, self.currency)
    
    @price.setter
    def price(self, value: Price) -> None:
        """Set the price from a value object."""
        self.total_amount = value.amount
        self.currency = value.currency
    
    # Implementation of internal methods
    async def _notify_customer_of_confirmation(self) -> None:
        """Send confirmation notification to customer."""
        # Implementation details
        pass
    
    async def _notify_customer_of_cancellation(self, reason: str) -> None:
        """Send cancellation notification to customer."""
        # Implementation details
        pass
    
    async def _process_refund(self) -> None:
        """Process refund for canceled order."""
        # Implementation details
        pass
    
    async def _notify_customer_of_shipping(self, tracking_number: str) -> None:
        """Send shipping notification with tracking number."""
        # Implementation details
        pass
    
    async def _notify_customer_of_delivery(self) -> None:
        """Send delivery notification to customer."""
        # Implementation details
        pass
    
    # Custom validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Custom validation for order."""
        context = super().validate(schema_name)
        
        # Business rule validations
        if hasattr(self, "total_amount") and self.total_amount <= 0:
            context.add_error(
                field="total_amount",
                message="Order total amount must be greater than zero",
                error_code="INVALID_AMOUNT"
            )
        
        return context
```

### Entity-Relationship Patterns

Implement relationships between business objects:

```python
class ProductModel(UnoModel):
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[Decimal] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)

class OrderItemModel(UnoModel):
    __tablename__ = "order_items"
    
    order_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
    product_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price_at_time: Mapped[Decimal] = mapped_column(nullable=False)

class Product(UnoObj[ProductModel]):
    name: str
    description: Optional[str] = None
    price: Decimal
    inventory_count: int = 0
    
    # Business logic methods
    async def adjust_inventory(self, quantity_change: int) -> bool:
        """Adjust inventory count, ensuring it doesn't go below zero."""
        new_count = self.inventory_count + quantity_change
        if new_count < 0:
            raise UnoError(
                f"Cannot reduce inventory below zero (current: {self.inventory_count}, requested change: {quantity_change})",
                ErrorCode.BUSINESS_RULE,
                current_inventory=self.inventory_count,
                requested_change=quantity_change
            )
        
        self.inventory_count = new_count
        await self.save()
        return True
    
    async def reserve_inventory(self, quantity: int) -> bool:
        """Reserve inventory for an order."""
        return await self.adjust_inventory(-quantity)
    
    async def release_inventory(self, quantity: int) -> bool:
        """Release previously reserved inventory."""
        return await self.adjust_inventory(quantity)

class OrderItem(UnoObj[OrderItemModel]):
    order_id: str
    product_id: str
    quantity: int
    price_at_time: Decimal
    
    # Add reference to related objects
    _product: Optional[Product] = None
    
    # Load related objects
    async def load_product(self) -> Product:
        """Load the related product."""
        if not self._product:
            self._product = await Product.get(id=self.product_id)
        return self._product
    
    @property
    async def subtotal(self) -> Decimal:
        """Calculate subtotal for this line item."""
        return self.price_at_time * self.quantity

class Order(UnoObj[OrderModel]):
    # ... previous Order implementation ...
    
    # Add relationship to items
    _items: List[OrderItem] = []
    
    async def load_items(self) -> List[OrderItem]:
        """Load order items for this order."""
        if not self._items:
            items_filter = {"order_id": self.id}
            self._items = await OrderItem.filter(items_filter)
        return self._items
    
    async def add_item(self, product_id: str, quantity: int) -> OrderItem:
        """Add an item to the order."""
        if self.status != self.STATUS_PENDING:
            raise UnoError(
                f"Cannot add items to an order that is not pending (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_PENDING
            )
        
        # Get product
        product = await Product.get(id=product_id)
        
        # Reserve inventory
        await product.reserve_inventory(quantity)
        
        # Create order item
        order_item = OrderItem(
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price_at_time=product.price  # Capture price at time of order
        )
        await order_item.save()
        
        # Add to in-memory items list
        if hasattr(self, "_items") and self._items:
            self._items.append(order_item)
        
        # Update order total
        await self._recalculate_total()
        
        return order_item
    
    async def _recalculate_total(self) -> None:
        """Recalculate order total based on items."""
        items = await self.load_items()
        total = Decimal("0.00")
        
        for item in items:
            total += item.price_at_time * item.quantity
        
        self.total_amount = total
        await self.save()
```

## Validation Strategies

### Domain Validation

Implement domain-specific validation rules:

```python
class Customer(UnoObj[CustomerModel]):
    name: str
    email: str
    phone: Optional[str] = None
    country: str
    tax_id: Optional[str] = None
    
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain validation for customer."""
        context = super().validate(schema_name)
        
        # Email validation
        if hasattr(self, "email") and self.email:
            if "@" not in self.email:
                context.add_error(
                    field="email",
                    message="Invalid email format",
                    error_code="INVALID_EMAIL"
                )
        
        # Country-specific validation
        if hasattr(self, "country") and self.country:
            # Tax ID required for certain countries
            if self.country in ["US", "CA", "UK", "FR", "DE"] and not self.tax_id:
                context.add_error(
                    field="tax_id",
                    message=f"Tax ID is required for customers in {self.country}",
                    error_code="TAX_ID_REQUIRED"
                )
            
            # Phone number format validation by country
            if hasattr(self, "phone") and self.phone:
                if self.country == "US" and not self._is_valid_us_phone(self.phone):
                    context.add_error(
                        field="phone",
                        message="US phone numbers must be in format XXX-XXX-XXXX",
                        error_code="INVALID_PHONE_FORMAT"
                    )
        
        return context
    
    def _is_valid_us_phone(self, phone: str) -> bool:
        """Validate US phone number format."""
        import re
        pattern = r"^\d{3}-\d{3}-\d{4}$"
        return bool(re.match(pattern, phone))
```

### Composite Validation

Validate related objects together:

```python
class ShippingAddress(UnoObj[ShippingAddressModel]):
    customer_id: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    
    def validate(self, schema_name: str) -> ValidationContext:
        context = super().validate(schema_name)
        
        # US-specific postal code validation
        if self.country == "US" and not self._is_valid_us_zip(self.postal_code):
            context.add_error(
                field="postal_code",
                message="US ZIP codes must be in format XXXXX or XXXXX-XXXX",
                error_code="INVALID_ZIP_FORMAT"
            )
        
        # State/province validation
        if self.country == "US" and not self._is_valid_us_state(self.state):
            context.add_error(
                field="state",
                message="Invalid US state code",
                error_code="INVALID_STATE"
            )
        
        return context
    
    def _is_valid_us_zip(self, zip_code: str) -> bool:
        import re
        pattern = r"^\d{5}(-\d{4})?$"
        return bool(re.match(pattern, zip_code))
    
    def _is_valid_us_state(self, state: str) -> bool:
        valid_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
                        "DC", "PR", "VI"]
        return state in valid_states

class Order(UnoObj[OrderModel]):
    # ... existing Order implementation ...
    
    shipping_address_id: Optional[str] = None
    _shipping_address: Optional[ShippingAddress] = None
    
    async def load_shipping_address(self) -> Optional[ShippingAddress]:
        """Load the related shipping address."""
        if not self._shipping_address and self.shipping_address_id:
            self._shipping_address = await ShippingAddress.get(id=self.shipping_address_id)
        return self._shipping_address
    
    async def set_shipping_address(self, address: ShippingAddress) -> None:
        """Set shipping address and validate shipping rules."""
        # Set the address
        self.shipping_address_id = address.id
        self._shipping_address = address
        
        # Validate shipping rules
        if address.country not in ["US", "CA"]:
            raise UnoError(
                f"Cannot ship to country: {address.country}",
                ErrorCode.BUSINESS_RULE,
                country=address.country
            )
        
        # Validate order with shipping address
        context = ValidationContext("Order")
        
        # Check if we have items that can't ship to this address
        items = await self.load_items()
        for item in items:
            product = await item.load_product()
            
            # Example: Check if product is available for this country
            if not await self._can_ship_product_to_country(product, address.country):
                context.add_error(
                    field="shipping_address_id",
                    message=f"Product '{product.name}' cannot be shipped to {address.country}",
                    error_code="PRODUCT_SHIPPING_RESTRICTED"
                )
        
        # Raise validation errors if any
        if context.has_errors():
            raise ValidationError(context.get_errors())
        
        await self.save()
    
    async def _can_ship_product_to_country(self, product: Product, country: str) -> bool:
        """Check if a product can be shipped to a given country."""
        # Implementation details - could check product restrictions, regulations, etc.
        return True  # Simplified example
```

## State Management Patterns

### Finite State Machine

Implement a state machine for business processes:

```python
from enum import Enum, auto
from typing import Dict, List, Type, Optional, Union, Callable, Awaitable

class OrderStatus(Enum):
    """Order status enum."""
    PENDING = auto()
    PAYMENT_PROCESSING = auto()
    PAYMENT_FAILED = auto()
    CONFIRMED = auto()
    PREPARING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    RETURNED = auto()
    CANCELLED = auto()

class OrderStateMachine:
    """State machine for order processing."""
    
    # Define valid transitions
    _transitions = {
        OrderStatus.PENDING: [OrderStatus.PAYMENT_PROCESSING, OrderStatus.CANCELLED],
        OrderStatus.PAYMENT_PROCESSING: [OrderStatus.CONFIRMED, OrderStatus.PAYMENT_FAILED],
        OrderStatus.PAYMENT_FAILED: [OrderStatus.PAYMENT_PROCESSING, OrderStatus.CANCELLED],
        OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
        OrderStatus.PREPARING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
        OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
        OrderStatus.DELIVERED: [OrderStatus.RETURNED],
        OrderStatus.RETURNED: [],  # Terminal state
        OrderStatus.CANCELLED: [],  # Terminal state
    }
    
    # Define handlers for state transitions
    _handlers: Dict[tuple, Callable] = {}
    
    @classmethod
    def can_transition(cls, from_state: OrderStatus, to_state: OrderStatus) -> bool:
        """Check if transition is valid."""
        return to_state in cls._transitions.get(from_state, [])
    
    @classmethod
    def register_handler(cls, from_state: OrderStatus, to_state: OrderStatus, 
                        handler: Callable[[Order, dict], Awaitable[bool]]) -> None:
        """Register a handler for a state transition."""
        cls._handlers[(from_state, to_state)] = handler
    
    @classmethod
    async def transition(cls, order: Order, to_state: OrderStatus, 
                        **kwargs) -> bool:
        """Transition an order to a new state."""
        from_state = OrderStatus[order.status.upper()]
        
        # Check if transition is valid
        if not cls.can_transition(from_state, to_state):
            raise UnoError(
                f"Invalid state transition from {from_state.name} to {to_state.name}",
                ErrorCode.BUSINESS_RULE,
                current_state=from_state.name,
                target_state=to_state.name
            )
        
        # Execute handler if registered
        handler = cls._handlers.get((from_state, to_state))
        if handler:
            result = await handler(order, kwargs)
            if not result:
                return False
        
        # Update state
        order.status = to_state.name.lower()
        await order.save()
        return True

# Enhanced Order implementation with state machine
class EnhancedOrder(UnoObj[OrderModel]):
    # ... basic properties ...
    
    async def process_payment(self, payment_method: str, amount: Decimal) -> bool:
        """Process payment for this order."""
        return await OrderStateMachine.transition(
            self, 
            OrderStatus.PAYMENT_PROCESSING,
            payment_method=payment_method,
            amount=amount
        )
    
    async def confirm(self) -> bool:
        """Confirm the order after successful payment."""
        return await OrderStateMachine.transition(
            self,
            OrderStatus.CONFIRMED
        )
    
    async def prepare(self) -> bool:
        """Mark order as being prepared."""
        return await OrderStateMachine.transition(
            self,
            OrderStatus.PREPARING
        )
    
    async def ship(self, tracking_number: str) -> bool:
        """Ship the order."""
        return await OrderStateMachine.transition(
            self,
            OrderStatus.SHIPPED,
            tracking_number=tracking_number
        )
    
    async def deliver(self) -> bool:
        """Mark as delivered."""
        return await OrderStateMachine.transition(
            self,
            OrderStatus.DELIVERED
        )
    
    async def cancel(self, reason: str) -> bool:
        """Cancel the order."""
        return await OrderStateMachine.transition(
            self,
            OrderStatus.CANCELLED,
            reason=reason
        )

# Register handlers for state transitions
async def handle_payment_processing(order: EnhancedOrder, params: dict) -> bool:
    """Handle transition to payment processing state."""
    # Validate payment parameters
    payment_method = params.get("payment_method")
    amount = params.get("amount")
    
    if not payment_method:
        raise UnoError(
            "Payment method is required",
            ErrorCode.VALIDATION_ERROR,
            field="payment_method"
        )
    
    if not amount or amount != order.total_amount:
        raise UnoError(
            f"Payment amount {amount} does not match order total {order.total_amount}",
            ErrorCode.VALIDATION_ERROR,
            field="amount",
            expected=order.total_amount,
            actual=amount
        )
    
    # Process payment with external service
    # ... payment processing logic ...
    
    return True

# Register the handler
OrderStateMachine.register_handler(
    OrderStatus.PENDING,
    OrderStatus.PAYMENT_PROCESSING,
    handle_payment_processing
)
```

### Event-Driven State Changes

Use domain events to drive state changes:

```python
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Type, ClassVar
import uuid
from datetime import datetime

@dataclass
class DomainEvent:
    """Base class for domain events."""
    id: str
    timestamp: datetime
    aggregate_id: str
    aggregate_type: str
    
    @classmethod
    def create(cls, aggregate_id: str, aggregate_type: str, **kwargs) -> 'DomainEvent':
        """Create a new domain event."""
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            **kwargs
        )

@dataclass
class OrderCreatedEvent(DomainEvent):
    """Event for order creation."""
    customer_id: str
    total_amount: Decimal

@dataclass
class OrderConfirmedEvent(DomainEvent):
    """Event for order confirmation."""
    pass

@dataclass
class OrderShippedEvent(DomainEvent):
    """Event for order shipment."""
    tracking_number: str

@dataclass
class OrderCancelledEvent(DomainEvent):
    """Event for order cancellation."""
    reason: str

class EventStore:
    """Simple in-memory event store."""
    _events: ClassVar[List[DomainEvent]] = []
    _subscribers: ClassVar[Dict[Type[DomainEvent], List[Callable]]] = {}
    
    @classmethod
    def add_event(cls, event: DomainEvent) -> None:
        """Add an event to the store and publish it."""
        cls._events.append(event)
        
        # Publish event to subscribers
        event_type = type(event)
        subscribers = cls._subscribers.get(event_type, [])
        for subscriber in subscribers:
            subscriber(event)
    
    @classmethod
    def subscribe(cls, event_type: Type[DomainEvent], 
                 handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to an event type."""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
    
    @classmethod
    def get_events(cls, aggregate_id: str) -> List[DomainEvent]:
        """Get all events for an aggregate."""
        return [e for e in cls._events if e.aggregate_id == aggregate_id]

# Event-driven order implementation
class EventDrivenOrder(UnoObj[OrderModel]):
    # ... basic properties ...
    
    @classmethod
    async def create_order(cls, customer_id: str, items: List[Dict[str, Any]]) -> 'EventDrivenOrder':
        """Create a new order with items."""
        # Create order
        order = cls(
            customer_id=customer_id,
            order_date=datetime.now(),
            status=cls.STATUS_PENDING,
            total_amount=Decimal("0.00")
        )
        await order.save()
        
        # Add items
        total_amount = Decimal("0.00")
        for item_data in items:
            product_id = item_data.get("product_id")
            quantity = item_data.get("quantity", 1)
            
            # Get product
            product = await Product.get(id=product_id)
            
            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                price_at_time=product.price
            )
            await order_item.save()
            
            # Update total
            total_amount += product.price * quantity
        
        # Update order total
        order.total_amount = total_amount
        await order.save()
        
        # Create and publish event
        event = OrderCreatedEvent.create(
            aggregate_id=order.id,
            aggregate_type="Order",
            customer_id=customer_id,
            total_amount=total_amount
        )
        EventStore.add_event(event)
        
        return order
    
    async def confirm(self) -> bool:
        """Confirm the order."""
        if self.status != self.STATUS_PENDING:
            raise UnoError(
                f"Cannot confirm order that is not pending (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_PENDING
            )
        
        # Update state
        self.status = self.STATUS_CONFIRMED
        await self.save()
        
        # Create and publish event
        event = OrderConfirmedEvent.create(
            aggregate_id=self.id,
            aggregate_type="Order"
        )
        EventStore.add_event(event)
        
        return True
    
    async def ship(self, tracking_number: str) -> bool:
        """Ship the order."""
        if self.status != self.STATUS_CONFIRMED:
            raise UnoError(
                f"Cannot ship order that is not confirmed (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_CONFIRMED
            )
        
        # Update state
        self.status = self.STATUS_SHIPPED
        await self.save()
        
        # Create and publish event
        event = OrderShippedEvent.create(
            aggregate_id=self.id,
            aggregate_type="Order",
            tracking_number=tracking_number
        )
        EventStore.add_event(event)
        
        return True
    
    async def cancel(self, reason: str) -> bool:
        """Cancel the order."""
        if self.status in [self.STATUS_SHIPPED, self.STATUS_DELIVERED]:
            raise UnoError(
                f"Cannot cancel order that has been {self.status}",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status
            )
        
        # Update state
        self.status = self.STATUS_CANCELLED
        await self.save()
        
        # Create and publish event
        event = OrderCancelledEvent.create(
            aggregate_id=self.id,
            aggregate_type="Order",
            reason=reason
        )
        EventStore.add_event(event)
        
        return True
    
    @classmethod
    async def replay_events(cls, order_id: str) -> 'EventDrivenOrder':
        """Replay events to reconstruct order state."""
        events = EventStore.get_events(order_id)
        
        # Find the creation event
        creation_events = [e for e in events if isinstance(e, OrderCreatedEvent)]
        if not creation_events:
            raise UnoError(
                f"No creation event found for order {order_id}",
                ErrorCode.RESOURCE_NOT_FOUND,
                order_id=order_id
            )
        
        # Get order from database or create from event
        try:
            order = await cls.get(id=order_id)
        except UnoObjNotFoundError:
            # Create order from creation event
            creation_event = creation_events[0]
            order = cls(
                id=creation_event.aggregate_id,
                customer_id=creation_event.customer_id,
                order_date=creation_event.timestamp,
                status=cls.STATUS_PENDING,
                total_amount=creation_event.total_amount
            )
            await order.save()
        
        # Apply other events in chronological order
        for event in sorted(events, key=lambda e: e.timestamp):
            if isinstance(event, OrderConfirmedEvent):
                order.status = cls.STATUS_CONFIRMED
            elif isinstance(event, OrderShippedEvent):
                order.status = cls.STATUS_SHIPPED
            elif isinstance(event, OrderCancelledEvent):
                order.status = cls.STATUS_CANCELLED
        
        # Save final state
        await order.save()
        return order
```

## Service Integration Patterns

### Services Composition

Use services with UnoObj for complex operations:

```python
from typing import List, Dict, Any, Optional
from datetime import datetime

class PaymentService:
    """Service for processing payments."""
    
    @staticmethod
    async def process_payment(order: Order, payment_method: str, payment_data: Dict[str, Any]) -> bool:
        """Process payment for an order."""
        # Validate payment data
        if payment_method == "credit_card":
            if not all(k in payment_data for k in ["card_number", "expiry", "cvv"]):
                raise UnoError(
                    "Missing required payment fields",
                    ErrorCode.VALIDATION_ERROR,
                    payment_method=payment_method
                )
        
        # Process payment with external service
        # ... payment processing logic ...
        
        # Update order
        order.payment_status = "paid"
        order.payment_date = datetime.now()
        order.payment_reference = f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        await order.save()
        
        return True
    
    @staticmethod
    async def refund_payment(order: Order, amount: Optional[Decimal] = None) -> bool:
        """Refund payment for an order."""
        if order.payment_status != "paid":
            raise UnoError(
                "Cannot refund unpaid order",
                ErrorCode.BUSINESS_RULE,
                payment_status=order.payment_status
            )
        
        refund_amount = amount or order.total_amount
        
        # Process refund with external service
        # ... refund processing logic ...
        
        # Update order
        order.payment_status = "refunded"
        order.refund_date = datetime.now()
        order.refund_amount = refund_amount
        await order.save()
        
        return True

class InventoryService:
    """Service for managing inventory."""
    
    @staticmethod
    async def reserve_inventory(order: Order) -> bool:
        """Reserve inventory for an order."""
        items = await order.load_items()
        
        # Check and reserve inventory for each item
        for item in items:
            product = await item.load_product()
            
            # Check if sufficient inventory
            if product.inventory_count < item.quantity:
                raise UnoError(
                    f"Insufficient inventory for product {product.name}",
                    ErrorCode.BUSINESS_RULE,
                    product_id=product.id,
                    requested=item.quantity,
                    available=product.inventory_count
                )
            
            # Reserve inventory
            await product.reserve_inventory(item.quantity)
        
        return True
    
    @staticmethod
    async def release_inventory(order: Order) -> bool:
        """Release inventory for a cancelled order."""
        items = await order.load_items()
        
        # Release inventory for each item
        for item in items:
            product = await item.load_product()
            await product.release_inventory(item.quantity)
        
        return True

class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    async def send_order_confirmation(order: Order) -> bool:
        """Send order confirmation notification."""
        # Get customer
        customer = await Customer.get(id=order.customer_id)
        
        # Send email
        # ... email sending logic ...
        
        # Log notification
        # ... logging logic ...
        
        return True
    
    @staticmethod
    async def send_shipping_notification(order: Order, tracking_number: str) -> bool:
        """Send shipping notification."""
        # Get customer
        customer = await Customer.get(id=order.customer_id)
        
        # Send email with tracking number
        # ... email sending logic ...
        
        # Log notification
        # ... logging logic ...
        
        return True

# Enhanced Order class using services
class ServiceOrder(UnoObj[OrderModel]):
    # ... basic properties ...
    
    async def process_checkout(self, payment_method: str, payment_data: Dict[str, Any]) -> bool:
        """Process complete checkout flow."""
        # Validate order state
        if self.status != self.STATUS_PENDING:
            raise UnoError(
                f"Cannot checkout order that is not pending (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_PENDING
            )
        
        try:
            # Reserve inventory
            await InventoryService.reserve_inventory(self)
            
            # Process payment
            await PaymentService.process_payment(self, payment_method, payment_data)
            
            # Update order status
            self.status = self.STATUS_CONFIRMED
            await self.save()
            
            # Send confirmation notification
            await NotificationService.send_order_confirmation(self)
            
            return True
            
        except Exception as e:
            # Handle failures
            # If inventory was reserved but payment failed, release inventory
            if self.payment_status != "paid":
                await InventoryService.release_inventory(self)
            
            # Re-raise the exception
            raise
    
    async def cancel(self, reason: str) -> bool:
        """Cancel order and handle related processes."""
        # Validate order state
        if self.status in [self.STATUS_SHIPPED, self.STATUS_DELIVERED]:
            raise UnoError(
                f"Cannot cancel order that has been {self.status}",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status
            )
        
        # Process refund if payment was made
        if hasattr(self, "payment_status") and self.payment_status == "paid":
            await PaymentService.refund_payment(self)
        
        # Release inventory
        await InventoryService.release_inventory(self)
        
        # Update order status
        self.status = self.STATUS_CANCELLED
        self.cancellation_reason = reason
        self.cancelled_at = datetime.now()
        await self.save()
        
        return True
```

### Command Pattern

Use commands to encapsulate business operations:

```python
from typing import Dict, Any, Generic, TypeVar, Type
from datetime import datetime
from abc import ABC, abstractmethod

# Command type parameter
T = TypeVar('T', bound=UnoObj)

class Command(ABC, Generic[T]):
    """Base class for commands."""
    
    def __init__(self, target_type: Type[T]):
        self.target_type = target_type
    
    @abstractmethod
    async def execute(self, data: Dict[str, Any]) -> T:
        """Execute the command."""
        pass

class CreateOrderCommand(Command[Order]):
    """Command to create a new order."""
    
    def __init__(self):
        super().__init__(Order)
    
    async def execute(self, data: Dict[str, Any]) -> Order:
        """Execute the command to create an order."""
        # Validate required fields
        required_fields = ["customer_id", "items"]
        for field in required_fields:
            if field not in data:
                raise UnoError(
                    f"Missing required field: {field}",
                    ErrorCode.VALIDATION_ERROR,
                    field=field
                )
        
        # Create order
        order = Order(
            customer_id=data["customer_id"],
            order_date=datetime.now(),
            status=Order.STATUS_PENDING,
            total_amount=Decimal("0.00")
        )
        await order.save()
        
        # Add items
        total_amount = Decimal("0.00")
        for item_data in data["items"]:
            product_id = item_data.get("product_id")
            quantity = item_data.get("quantity", 1)
            
            if not product_id:
                raise UnoError(
                    "Product ID is required for order items",
                    ErrorCode.VALIDATION_ERROR,
                    field="items.product_id"
                )
            
            # Get product
            product = await Product.get(id=product_id)
            
            # Check inventory
            if product.inventory_count < quantity:
                raise UnoError(
                    f"Insufficient inventory for product {product.name}",
                    ErrorCode.BUSINESS_RULE,
                    product_id=product.id,
                    requested=quantity,
                    available=product.inventory_count
                )
            
            # Reserve inventory
            await product.reserve_inventory(quantity)
            
            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                price_at_time=product.price
            )
            await order_item.save()
            
            # Update total
            total_amount += product.price * quantity
        
        # Update order total
        order.total_amount = total_amount
        await order.save()
        
        return order

class ProcessPaymentCommand(Command[Order]):
    """Command to process payment for an order."""
    
    def __init__(self):
        super().__init__(Order)
    
    async def execute(self, data: Dict[str, Any]) -> Order:
        """Execute the command to process payment."""
        # Validate required fields
        required_fields = ["order_id", "payment_method", "payment_data"]
        for field in required_fields:
            if field not in data:
                raise UnoError(
                    f"Missing required field: {field}",
                    ErrorCode.VALIDATION_ERROR,
                    field=field
                )
        
        # Get order
        order = await Order.get(id=data["order_id"])
        
        # Validate order state
        if order.status != Order.STATUS_PENDING:
            raise UnoError(
                f"Cannot process payment for order that is not pending (current status: {order.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=order.status,
                expected_status=Order.STATUS_PENDING
            )
        
        # Process payment
        payment_method = data["payment_method"]
        payment_data = data["payment_data"]
        
        # ... payment processing logic ...
        
        # Update order
        order.payment_status = "paid"
        order.payment_date = datetime.now()
        order.status = Order.STATUS_CONFIRMED
        await order.save()
        
        return order

class ShipOrderCommand(Command[Order]):
    """Command to ship an order."""
    
    def __init__(self):
        super().__init__(Order)
    
    async def execute(self, data: Dict[str, Any]) -> Order:
        """Execute the command to ship an order."""
        # Validate required fields
        required_fields = ["order_id", "tracking_number"]
        for field in required_fields:
            if field not in data:
                raise UnoError(
                    f"Missing required field: {field}",
                    ErrorCode.VALIDATION_ERROR,
                    field=field
                )
        
        # Get order
        order = await Order.get(id=data["order_id"])
        
        # Validate order state
        if order.status != Order.STATUS_CONFIRMED:
            raise UnoError(
                f"Cannot ship order that is not confirmed (current status: {order.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=order.status,
                expected_status=Order.STATUS_CONFIRMED
            )
        
        # Update order
        order.status = Order.STATUS_SHIPPED
        order.shipped_at = datetime.now()
        order.tracking_number = data["tracking_number"]
        await order.save()
        
        # Send shipping notification
        # ... notification logic ...
        
        return order

# Command handler
class CommandHandler:
    """Handler for executing commands."""
    
    _commands: Dict[str, Command] = {}
    
    @classmethod
    def register_command(cls, name: str, command: Command) -> None:
        """Register a command."""
        cls._commands[name] = command
    
    @classmethod
    async def execute(cls, command_name: str, data: Dict[str, Any]) -> Any:
        """Execute a command by name."""
        if command_name not in cls._commands:
            raise UnoError(
                f"Command not found: {command_name}",
                ErrorCode.RESOURCE_NOT_FOUND,
                command=command_name
            )
        
        command = cls._commands[command_name]
        return await command.execute(data)

# Register commands
CommandHandler.register_command("create_order", CreateOrderCommand())
CommandHandler.register_command("process_payment", ProcessPaymentCommand())
CommandHandler.register_command("ship_order", ShipOrderCommand())

# Using commands in an API endpoint
async def create_order_endpoint(request_data: Dict[str, Any]):
    """API endpoint for creating an order."""
    try:
        order = await CommandHandler.execute("create_order", request_data)
        return {"status": "success", "order_id": order.id}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
```

## Performance Optimization Patterns

### Lazy Loading

Implement lazy loading for related objects:

```python
class LazyLoadedOrder(UnoObj[OrderModel]):
    # ... basic properties ...
    
    # Private fields for lazy-loaded properties
    _items: Optional[List[OrderItem]] = None
    _customer: Optional[Customer] = None
    _shipping_address: Optional[ShippingAddress] = None
    
    async def items(self) -> List[OrderItem]:
        """Lazy-load order items."""
        if self._items is None:
            self._items = await OrderItem.filter({"order_id": self.id})
        return self._items
    
    async def customer(self) -> Customer:
        """Lazy-load customer."""
        if self._customer is None:
            self._customer = await Customer.get(id=self.customer_id)
        return self._customer
    
    async def shipping_address(self) -> Optional[ShippingAddress]:
        """Lazy-load shipping address."""
        if not hasattr(self, "shipping_address_id") or not self.shipping_address_id:
            return None
        
        if self._shipping_address is None:
            self._shipping_address = await ShippingAddress.get(id=self.shipping_address_id)
        return self._shipping_address
    
    async def total_items(self) -> int:
        """Get total number of items without loading all items."""
        # Use count query directly instead of loading all items
        from uno.database.db import UnoDBFactory
        
        db = UnoDBFactory(OrderItem)
        count = await db.count({"order_id": self.id})
        return count
    
    async def calculate_total(self) -> Decimal:
        """Calculate order total from items."""
        items = await self.items()
        total = Decimal("0.00")
        
        for item in items:
            subtotal = item.price_at_time * item.quantity
            total += subtotal
        
        return total
```

### Batch Operations

Use batch operations for performance:

```python
class BatchOrder(UnoObj[OrderModel]):
    # ... basic properties ...
    
    @classmethod
    async def get_orders_with_items(cls, customer_id: str) -> Dict[str, Dict[str, Any]]:
        """Get orders with items in a single batch operation."""
        # Get orders
        orders = await cls.filter({"customer_id": customer_id})
        if not orders:
            return {}
        
        # Get all order IDs
        order_ids = [order.id for order in orders]
        
        # Batch get all items for these orders
        items = await OrderItem.filter({"order_id__in": order_ids})
        
        # Group items by order
        items_by_order = {}
        for item in items:
            if item.order_id not in items_by_order:
                items_by_order[item.order_id] = []
            items_by_order[item.order_id].append(item)
        
        # Create result structure
        result = {}
        for order in orders:
            order_items = items_by_order.get(order.id, [])
            result[order.id] = {
                "order": order,
                "items": order_items
            }
        
        return result
    
    @classmethod
    async def update_status_batch(cls, order_ids: List[str], status: str) -> Dict[str, bool]:
        """Update status for multiple orders in a batch."""
        # Validate status
        valid_statuses = [cls.STATUS_PENDING, cls.STATUS_CONFIRMED, 
                         cls.STATUS_SHIPPED, cls.STATUS_DELIVERED, 
                         cls.STATUS_CANCELLED]
        
        if status not in valid_statuses:
            raise UnoError(
                f"Invalid status: {status}",
                ErrorCode.VALIDATION_ERROR,
                valid_statuses=valid_statuses
            )
        
        # Get orders
        from uno.database.db import UnoDBFactory
        
        db = UnoDBFactory(OrderModel)
        
        # Update in database
        results = {}
        for order_id in order_ids:
            try:
                await db.update(
                    {"id": order_id},
                    {"status": status, "modified_at": datetime.now()}
                )
                results[order_id] = True
            except Exception as e:
                results[order_id] = False
        
        return results
```

## Testing Strategies

### Unit Testing UnoObj Classes

```python
import pytest
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

# Order unit tests
class TestOrder(unittest.IsolatedAsyncioTestCase):
    """Unit tests for Order business object."""
    
    async def setUp(self):
        """Set up test environment."""
        # Mock database and related services
        self.db_patcher = patch('uno.database.db.UnoDBFactory')
        self.mock_db_factory = self.db_patcher.start()
        self.mock_db = AsyncMock()
        self.mock_db_factory.return_value = self.mock_db
        
        # Mock Product.get to return a mock product
        self.product_patcher = patch('your_module.Product.get')
        self.mock_product_get = self.product_patcher.start()
        
        # Create a mock product
        self.mock_product = MagicMock()
        self.mock_product.id = "product123"
        self.mock_product.name = "Test Product"
        self.mock_product.price = Decimal("10.00")
        self.mock_product.inventory_count = 50
        self.mock_product.reserve_inventory = AsyncMock(return_value=True)
        
        self.mock_product_get.return_value = self.mock_product
    
    async def tearDown(self):
        """Clean up after tests."""
        self.db_patcher.stop()
        self.product_patcher.stop()
    
    async def test_create_order(self):
        """Test order creation."""
        # Arrange
        self.mock_db.create.return_value = (MagicMock(), True)
        
        # Act
        order = Order(
            customer_id="customer123",
            order_date=datetime.now(),
            status=Order.STATUS_PENDING,
            total_amount=Decimal("0.00")
        )
        await order.save()
        
        # Assert
        self.mock_db.create.assert_called_once()
        self.assertEqual(order.status, Order.STATUS_PENDING)
    
    async def test_add_item(self):
        """Test adding an item to an order."""
        # Arrange
        order = Order(
            id="order123",
            customer_id="customer123",
            order_date=datetime.now(),
            status=Order.STATUS_PENDING,
            total_amount=Decimal("0.00")
        )
        
        # Mock OrderItem.save
        with patch('your_module.OrderItem.save', new_callable=AsyncMock) as mock_save:
            # Act
            await order.add_item("product123", 2)
            
            # Assert
            self.mock_product_get.assert_called_once_with(id="product123")
            self.mock_product.reserve_inventory.assert_called_once_with(2)
            mock_save.assert_called_once()
    
    async def test_cancel_order(self):
        """Test order cancellation."""
        # Arrange
        order = Order(
            id="order123",
            customer_id="customer123",
            order_date=datetime.now(),
            status=Order.STATUS_PENDING,
            total_amount=Decimal("20.00")
        )
        
        # Mock order.save
        with patch.object(order, 'save', new_callable=AsyncMock) as mock_save:
            # Act
            await order.cancel("Customer requested cancellation")
            
            # Assert
            self.assertEqual(order.status, Order.STATUS_CANCELLED)
            mock_save.assert_called_once()
    
    async def test_cannot_cancel_shipped_order(self):
        """Test cannot cancel shipped order."""
        # Arrange
        order = Order(
            id="order123",
            customer_id="customer123",
            order_date=datetime.now(),
            status=Order.STATUS_SHIPPED,
            total_amount=Decimal("20.00")
        )
        
        # Act & Assert
        with self.assertRaises(UnoError) as context:
            await order.cancel("Customer requested cancellation")
        
        # Check error details
        self.assertIn("Cannot cancel order", str(context.exception))
        self.assertEqual(context.exception.error_code, ErrorCode.BUSINESS_RULE)
    
    async def test_order_validation(self):
        """Test order validation logic."""
        # Arrange
        order = Order(
            id="order123",
            customer_id="customer123",
            order_date=datetime.now(),
            status=Order.STATUS_PENDING,
            total_amount=Decimal("-10.00")  # Invalid negative amount
        )
        
        # Act
        validation_context = order.validate("edit_schema")
        
        # Assert
        self.assertTrue(validation_context.has_errors())
        errors = validation_context.get_errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].field, "total_amount")
```

### Integration Testing

```python
import pytest
from decimal import Decimal
from datetime import datetime

# Integration tests with actual database
@pytest.mark.asyncio
class TestOrderIntegration:
    """Integration tests for Order business object."""
    
    async def test_order_lifecycle(self):
        """Test the complete order lifecycle."""
        # Create a test customer
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="555-123-4567"
        )
        await customer.save()
        
        # Create test products
        product1 = Product(
            name="Test Product 1",
            description="Test product description",
            price=Decimal("10.00"),
            inventory_count=100
        )
        await product1.save()
        
        product2 = Product(
            name="Test Product 2",
            description="Another test product",
            price=Decimal("15.00"),
            inventory_count=50
        )
        await product2.save()
        
        # Create a new order
        order = Order(
            customer_id=customer.id,
            order_date=datetime.now(),
            status=Order.STATUS_PENDING,
            total_amount=Decimal("0.00")
        )
        await order.save()
        
        # Add items to the order
        await order.add_item(product1.id, 2)
        await order.add_item(product2.id, 1)
        
        # Check order total
        expected_total = (Decimal("10.00") * 2) + Decimal("15.00")
        assert order.total_amount == expected_total
        
        # Check inventory counts were updated
        updated_product1 = await Product.get(id=product1.id)
        updated_product2 = await Product.get(id=product2.id)
        assert updated_product1.inventory_count == 98
        assert updated_product2.inventory_count == 49
        
        # Confirm the order
        await order.confirm()
        assert order.status == Order.STATUS_CONFIRMED
        
        # Ship the order
        await order.ship("TRACK-12345")
        assert order.status == Order.STATUS_SHIPPED
        
        # Deliver the order
        await order.deliver()
        assert order.status == Order.STATUS_DELIVERED
        
        # Try to cancel the delivered order (should fail)
        with pytest.raises(UnoError) as excinfo:
            await order.cancel("Customer requested cancellation")
        assert "Cannot cancel order" in str(excinfo.value)
        
        # Final order state check
        final_order = await Order.get(id=order.id)
        assert final_order.status == Order.STATUS_DELIVERED
        assert final_order.total_amount == expected_total
```

## Common Pitfalls and Solutions

### Circular Imports

Avoid circular imports with deferred imports:

```python
# In order.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .order_item import OrderItem
    from .customer import Customer

class Order(UnoObj[OrderModel]):
    # ... implementation ...
    
    async def load_items(self):
        # Use runtime import
        from .order_item import OrderItem
        return await OrderItem.filter({"order_id": self.id})
```

### Proper Error Handling

Use specific error types:

```python
async def apply_discount(self, discount_code: str) -> Decimal:
    """Apply a discount to the order."""
    try:
        # Get discount
        discount = await Discount.get(code=discount_code)
        
        # Check discount validity
        if discount.is_expired:
            raise UnoError(
                f"Discount code {discount_code} has expired",
                ErrorCode.BUSINESS_RULE,
                discount_code=discount_code,
                expiry_date=discount.expiry_date
            )
        
        # Apply discount
        discount_amount = self.total_amount * (discount.percentage / 100)
        self.discount_amount = discount_amount
        self.total_amount = self.total_amount - discount_amount
        await self.save()
        
        return discount_amount
    
    except UnoObjNotFoundError:
        raise UnoError(
            f"Invalid discount code: {discount_code}",
            ErrorCode.RESOURCE_NOT_FOUND,
            discount_code=discount_code
        )
    except Exception as e:
        raise UnoError(
            f"Error applying discount: {str(e)}",
            ErrorCode.INTERNAL_ERROR,
            discount_code=discount_code
        )
```

### Transaction Management

Ensure data consistency with transactions:

```python
async def complete_order(self) -> bool:
    """Complete the order with transaction handling."""
    from uno.database.db import get_transaction
    
    async with get_transaction() as transaction:
        try:
            # Process payment
            payment_success = await self._process_payment()
            if not payment_success:
                # Roll back transaction
                await transaction.rollback()
                return False
            
            # Update inventory
            inventory_success = await self._update_inventory()
            if not inventory_success:
                # Roll back transaction
                await transaction.rollback()
                return False
            
            # Update order status
            self.status = self.STATUS_CONFIRMED
            await self.save()
            
            # Commit transaction
            await transaction.commit()
            return True
        
        except Exception as e:
            # Roll back transaction
            await transaction.rollback()
            raise UnoError(
                f"Error completing order: {str(e)}",
                ErrorCode.INTERNAL_ERROR,
                order_id=self.id
            )
```

## See Also

- [UnoObj Reference](unoobj.md) - Core UnoObj class documentation
- [Schema Management](schema.md) - Schema management for UnoObj
- [Registry System](registry.md) - Type-safe registry for business objects