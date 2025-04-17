"""
Entity classes for the e-commerce domain.

This module contains entity classes that represent the core business objects
in the e-commerce domain, including users, products, and orders.
"""

import uuid
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any, Set

from pydantic import Field, validator

from uno.domain.core import Entity, AggregateRoot, DomainEvent
from examples.ecommerce.domain.value_objects import (
    Money,
    Address,
    Rating,
    EmailAddress,
    PhoneNumber,
    CreditCard,
)
from examples.ecommerce.domain.events import (
    UserRegisteredEvent,
    ProductCreatedEvent,
    OrderPlacedEvent,
    OrderStatusChangedEvent,
    PaymentProcessedEvent,
)


class User(AggregateRoot):
    """
    User entity representing a customer or administrator.

    Users are aggregate roots that contain personal information and preferences.
    They can place orders and leave reviews.
    """

    username: str
    email: EmailAddress
    first_name: str
    last_name: str
    phone: Optional[PhoneNumber] = None
    billing_address: Optional[Address] = None
    shipping_address: Optional[Address] = None
    is_active: bool = True
    is_admin: bool = False

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}"

    def update_contact_info(
        self, email: Optional[EmailAddress] = None, phone: Optional[PhoneNumber] = None
    ) -> None:
        """
        Update the user's contact information.

        Args:
            email: New email address (optional)
            phone: New phone number (optional)
        """
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        self.updated_at = datetime.now(datetime.UTC)

    def update_addresses(
        self,
        billing_address: Optional[Address] = None,
        shipping_address: Optional[Address] = None,
        use_billing_for_shipping: bool = False,
    ) -> None:
        """
        Update the user's billing and shipping addresses.

        Args:
            billing_address: New billing address (optional)
            shipping_address: New shipping address (optional)
            use_billing_for_shipping: If True, use billing address for shipping
        """
        if billing_address is not None:
            self.billing_address = billing_address
            if use_billing_for_shipping:
                self.shipping_address = billing_address

        if not use_billing_for_shipping and shipping_address is not None:
            self.shipping_address = shipping_address

        self.updated_at = datetime.now(datetime.UTC)

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.updated_at = datetime.now(datetime.UTC)

    def reactivate(self) -> None:
        """Reactivate a deactivated user account."""
        self.is_active = True
        self.updated_at = datetime.now(datetime.UTC)

    def make_admin(self) -> None:
        """Make the user an administrator."""
        self.is_admin = True
        self.updated_at = datetime.now(datetime.UTC)

    def remove_admin(self) -> None:
        """Remove administrator privileges from the user."""
        self.is_admin = False
        self.updated_at = datetime.now(datetime.UTC)

    @classmethod
    def register(
        cls,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        billing_address: Optional[Address] = None,
        shipping_address: Optional[Address] = None,
    ) -> "User":
        """
        Factory method to register a new user.

        Args:
            username: Username for the new user
            email: Email address
            first_name: First name
            last_name: Last name
            phone: Optional phone number
            billing_address: Optional billing address
            shipping_address: Optional shipping address

        Returns:
            A new User instance
        """
        # Convert string values to value objects
        email_obj = EmailAddress(address=email)
        phone_obj = PhoneNumber(number=phone) if phone else None

        # Create user
        user = cls(
            id=str(uuid.uuid4()),
            username=username,
            email=email_obj,
            first_name=first_name,
            last_name=last_name,
            phone=phone_obj,
            billing_address=billing_address,
            shipping_address=shipping_address,
            is_active=True,
            is_admin=False,
            created_at=datetime.now(datetime.UTC),
        )

        # Create registration event
        event = UserRegisteredEvent(
            user_id=user.id,
            username=user.username,
            email=user.email.address,
            timestamp=datetime.now(datetime.UTC),
        )
        user.add_event(event)

        return user


class ProductCategory(Entity):
    """
    Product category entity.

    Categories are used to organize products and can form a hierarchy.
    """

    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True

    def deactivate(self) -> None:
        """Deactivate the category."""
        self.is_active = False
        self.updated_at = datetime.now(datetime.UTC)

    def reactivate(self) -> None:
        """Reactivate the category."""
        self.is_active = True
        self.updated_at = datetime.now(datetime.UTC)

    def update_details(
        self, name: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        """
        Update the category details.

        Args:
            name: New category name (optional)
            description: New category description (optional)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(datetime.UTC)


class Product(AggregateRoot):
    """
    Product entity representing a saleable item.

    Products are aggregate roots that contain information about an item for sale,
    including its price, inventory status, and category.
    """

    name: str
    description: str
    price: Money
    category_id: Optional[str] = None
    inventory_count: int = 0
    is_active: bool = True
    ratings: List[Rating] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("inventory_count")
    def inventory_count_non_negative(cls, v):
        """Validate that inventory count is non-negative."""
        if v < 0:
            raise ValueError("Inventory count must be non-negative")
        return v

    def update_price(self, new_price: Money) -> None:
        """
        Update the product's price.

        Args:
            new_price: The new price for the product
        """
        if new_price.amount < 0:
            raise ValueError("Product price cannot be negative")
        self.price = new_price
        self.updated_at = datetime.now(datetime.UTC)

    def update_inventory(self, count: int) -> None:
        """
        Update the product's inventory count.

        Args:
            count: The new inventory count
        """
        if count < 0:
            raise ValueError("Inventory count cannot be negative")
        self.inventory_count = count
        self.updated_at = datetime.now(datetime.UTC)

    def add_inventory(self, quantity: int) -> None:
        """
        Add inventory to the product.

        Args:
            quantity: The quantity to add
        """
        if quantity < 0:
            raise ValueError("Cannot add negative inventory")
        self.inventory_count += quantity
        self.updated_at = datetime.now(datetime.UTC)

    def remove_inventory(self, quantity: int) -> None:
        """
        Remove inventory from the product.

        Args:
            quantity: The quantity to remove

        Raises:
            ValueError: If trying to remove more than available
        """
        if quantity < 0:
            raise ValueError("Cannot remove negative inventory")
        if quantity > self.inventory_count:
            raise ValueError(
                f"Cannot remove {quantity} items, only {self.inventory_count} in stock"
            )
        self.inventory_count -= quantity
        self.updated_at = datetime.now(datetime.UTC)

    def add_rating(self, rating: Rating) -> None:
        """
        Add a customer rating to the product.

        Args:
            rating: The rating to add
        """
        self.ratings.append(rating)
        self.updated_at = datetime.now(datetime.UTC)

    def get_average_rating(self) -> Optional[float]:
        """
        Calculate the average rating for the product.

        Returns:
            The average rating, or None if no ratings
        """
        if not self.ratings:
            return None
        return sum(r.score for r in self.ratings) / len(self.ratings)

    def is_in_stock(self) -> bool:
        """Check if the product is in stock."""
        return self.inventory_count > 0

    def deactivate(self) -> None:
        """Deactivate the product (hide from listings)."""
        self.is_active = False
        self.updated_at = datetime.now(datetime.UTC)

    def reactivate(self) -> None:
        """Reactivate the product."""
        self.is_active = True
        self.updated_at = datetime.now(datetime.UTC)

    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> None:
        """
        Update the product details.

        Args:
            name: New product name (optional)
            description: New product description (optional)
            category_id: New category ID (optional)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if category_id is not None:
            self.category_id = category_id
        self.updated_at = datetime.now(datetime.UTC)

    def update_attribute(self, key: str, value: Any) -> None:
        """
        Update a product attribute.

        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value
        self.updated_at = datetime.now(datetime.UTC)

    def remove_attribute(self, key: str) -> None:
        """
        Remove a product attribute.

        Args:
            key: Attribute key to remove
        """
        if key in self.attributes:
            del self.attributes[key]
            self.updated_at = datetime.now(datetime.UTC)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        price: float,
        category_id: Optional[str] = None,
        inventory_count: int = 0,
        currency: str = "USD",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> "Product":
        """
        Factory method to create a new product.

        Args:
            name: Product name
            description: Product description
            price: Product price amount
            category_id: Optional category ID
            inventory_count: Initial inventory count
            currency: Price currency (default USD)
            attributes: Optional product attributes

        Returns:
            A new Product instance
        """
        # Create the product
        product = cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            price=Money(amount=price, currency=currency),
            category_id=category_id,
            inventory_count=inventory_count,
            is_active=True,
            attributes=attributes or {},
            created_at=datetime.now(datetime.UTC),
        )

        # Create product creation event
        event = ProductCreatedEvent(
            product_id=product.id,
            name=product.name,
            price=product.price.amount,
            currency=product.price.currency,
            timestamp=datetime.now(datetime.UTC),
        )
        product.add_event(event)

        return product


class OrderItem(Entity):
    """
    Order item entity representing a product in an order.

    Order items are part of the Order aggregate and include product details
    at the time of purchase.
    """

    product_id: str
    product_name: str
    price: Money
    quantity: int

    @property
    def total_price(self) -> Money:
        """Calculate the total price for the order item."""
        return self.price * self.quantity


class OrderStatus:
    """Enumeration of possible order statuses."""

    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod:
    """Enumeration of possible payment methods."""

    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"


class Payment(Entity):
    """
    Payment entity representing a payment for an order.

    Payments are part of the Order aggregate and track payment details.
    """

    amount: Money
    method: str
    status: str  # "pending", "completed", "failed", "refunded"
    transaction_id: Optional[str] = None
    payment_details: Dict[str, Any] = Field(default_factory=dict)

    def complete(self, transaction_id: str) -> None:
        """
        Mark the payment as completed.

        Args:
            transaction_id: The ID of the completed transaction
        """
        self.status = "completed"
        self.transaction_id = transaction_id
        self.updated_at = datetime.now(datetime.UTC)

    def fail(self, reason: str) -> None:
        """
        Mark the payment as failed.

        Args:
            reason: The reason for the failure
        """
        self.status = "failed"
        self.payment_details["failure_reason"] = reason
        self.updated_at = datetime.now(datetime.UTC)

    def refund(self, reason: Optional[str] = None) -> None:
        """
        Mark the payment as refunded.

        Args:
            reason: Optional reason for the refund
        """
        self.status = "refunded"
        if reason:
            self.payment_details["refund_reason"] = reason
        self.updated_at = datetime.now(datetime.UTC)


class Order(AggregateRoot):
    """
    Order entity representing a customer order.

    Orders are aggregate roots that contain items, shipping information,
    and payment details.
    """

    user_id: str
    items: List[OrderItem] = Field(default_factory=list)
    shipping_address: Address
    billing_address: Address
    status: str = OrderStatus.PENDING
    payment: Optional[Payment] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    notes: Optional[str] = None

    @property
    def subtotal(self) -> Money:
        """Calculate the subtotal for the order (before tax/shipping)."""
        if not self.items:
            return Money(amount=0, currency="USD")

        # Sum all item totals - all should have the same currency
        currency = self.items[0].price.currency
        amount = sum(item.total_price.amount for item in self.items)
        return Money(amount=amount, currency=currency)

    @property
    def total_items(self) -> int:
        """Calculate the total number of items in the order."""
        return sum(item.quantity for item in self.items)

    def add_item(
        self, product_id: str, product_name: str, price: Money, quantity: int
    ) -> None:
        """
        Add an item to the order.

        Args:
            product_id: The product ID
            product_name: The product name
            price: The product price
            quantity: The quantity to add
        """
        # Check if order can be modified
        if self.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise ValueError(f"Cannot add items to order with status {self.status}")

        # Check if the item already exists in the order
        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity
                self.updated_at = datetime.now(datetime.UTC)
                return

        # Create new order item
        item = OrderItem(
            id=str(uuid.uuid4()),
            product_id=product_id,
            product_name=product_name,
            price=price,
            quantity=quantity,
            created_at=datetime.now(datetime.UTC),
        )

        self.items.append(item)
        self.register_child_entity(item)
        self.updated_at = datetime.now(datetime.UTC)

    def remove_item(self, product_id: str) -> None:
        """
        Remove an item from the order.

        Args:
            product_id: The product ID to remove
        """
        # Check if order can be modified
        if self.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise ValueError(
                f"Cannot remove items from order with status {self.status}"
            )

        # Find and remove the item
        self.items = [item for item in self.items if item.product_id != product_id]
        self.updated_at = datetime.now(datetime.UTC)

    def update_item_quantity(self, product_id: str, quantity: int) -> None:
        """
        Update the quantity of an item in the order.

        Args:
            product_id: The product ID to update
            quantity: The new quantity
        """
        # Check if order can be modified
        if self.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise ValueError(f"Cannot update items in order with status {self.status}")

        # Find and update the item
        for item in self.items:
            if item.product_id == product_id:
                if quantity <= 0:
                    # Remove the item if quantity is zero or negative
                    self.remove_item(product_id)
                else:
                    item.quantity = quantity
                self.updated_at = datetime.now(datetime.UTC)
                return

    def process_payment(
        self,
        method: str,
        amount: Money,
        payment_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Process a payment for the order.

        Args:
            method: The payment method
            amount: The payment amount
            payment_details: Optional payment details
        """
        # Check if payment is possible
        if self.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise ValueError(
                f"Cannot process payment for order with status {self.status}"
            )

        # Create payment
        payment = Payment(
            id=str(uuid.uuid4()),
            amount=amount,
            method=method,
            status="pending",
            payment_details=payment_details or {},
            created_at=datetime.now(datetime.UTC),
        )

        self.payment = payment
        self.register_child_entity(payment)
        self.updated_at = datetime.now(datetime.UTC)

        # Create payment event
        event = PaymentProcessedEvent(
            order_id=self.id,
            payment_id=payment.id,
            amount=payment.amount.amount,
            currency=payment.amount.currency,
            method=payment.method,
            status=payment.status,
            timestamp=datetime.now(datetime.UTC),
        )
        self.add_event(event)

    def update_status(self, new_status: str, notes: Optional[str] = None) -> None:
        """
        Update the order status.

        Args:
            new_status: The new order status
            notes: Optional notes about the status change
        """
        if new_status not in [
            OrderStatus.PENDING,
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ]:
            raise ValueError(f"Invalid order status: {new_status}")

        old_status = self.status
        self.status = new_status

        # Update status-specific timestamps
        if new_status == OrderStatus.SHIPPED and not self.shipped_at:
            self.shipped_at = datetime.now(datetime.UTC)
        elif new_status == OrderStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = datetime.now(datetime.UTC)
        elif new_status == OrderStatus.CANCELLED and not self.cancelled_at:
            self.cancelled_at = datetime.now(datetime.UTC)

        # Add notes if provided
        if notes:
            self.notes = notes

        self.updated_at = datetime.now(datetime.UTC)

        # Create status change event
        event = OrderStatusChangedEvent(
            order_id=self.id,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.now(datetime.UTC),
        )
        self.add_event(event)

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancel the order.

        Args:
            reason: Optional reason for cancellation
        """
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot cancel order with status {self.status}")

        self.update_status(OrderStatus.CANCELLED, notes=reason)

    @classmethod
    def create(
        cls,
        user_id: str,
        shipping_address: Address,
        billing_address: Address,
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> "Order":
        """
        Factory method to create a new order.

        Args:
            user_id: The ID of the user placing the order
            shipping_address: The shipping address
            billing_address: The billing address
            items: Optional list of items to add to the order

        Returns:
            A new Order instance
        """
        # Create the order
        order = cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            shipping_address=shipping_address,
            billing_address=billing_address,
            status=OrderStatus.PENDING,
            created_at=datetime.now(datetime.UTC),
        )

        # Add items if provided
        if items:
            for item in items:
                order.add_item(
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    price=Money(
                        amount=item["price"], currency=item.get("currency", "USD")
                    ),
                    quantity=item["quantity"],
                )

        # Create order placed event
        event = OrderPlacedEvent(
            order_id=order.id,
            user_id=order.user_id,
            total_amount=order.subtotal.amount,
            currency=order.subtotal.currency,
            items_count=order.total_items,
            timestamp=datetime.now(datetime.UTC),
        )
        order.add_event(event)

        return order
