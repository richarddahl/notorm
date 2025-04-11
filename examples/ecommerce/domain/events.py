"""
Domain events for the e-commerce domain.

This module defines the various domain events that can occur within the 
e-commerce domain, supporting event-driven architecture and domain-driven design.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from uno.domain.core import DomainEvent


# User events

class UserRegisteredEvent(DomainEvent):
    """Event representing a user being registered."""
    
    event_type: str = "user_registered"
    user_id: str
    username: str
    email: str
    timestamp: datetime = None


class UserCreatedEvent(DomainEvent):
    """Event representing a user being created."""
    
    event_type: str = "user_created"
    aggregate_id: str
    aggregate_type: str = "user"
    data: Dict[str, Any]


class UserUpdatedEvent(DomainEvent):
    """Event representing a user being updated."""
    
    event_type: str = "user_updated"
    aggregate_id: str
    aggregate_type: str = "user"
    data: Dict[str, Any]


class UserDeletedEvent(DomainEvent):
    """Event representing a user being deleted."""
    
    event_type: str = "user_deleted"
    aggregate_id: str
    aggregate_type: str = "user"
    data: Dict[str, Any]


# Product events

class ProductCreatedEvent(DomainEvent):
    """Event representing a product being created."""
    
    event_type: str = "product_created"
    product_id: str
    name: str
    price: float
    currency: str
    timestamp: datetime = None


class ProductUpdatedEvent(DomainEvent):
    """Event representing a product being updated."""
    
    event_type: str = "product_updated"
    aggregate_id: str
    aggregate_type: str = "product"
    data: Dict[str, Any]


class ProductDeletedEvent(DomainEvent):
    """Event representing a product being deleted."""
    
    event_type: str = "product_deleted"
    aggregate_id: str
    aggregate_type: str = "product"
    data: Dict[str, Any]


class ProductPriceChangedEvent(DomainEvent):
    """Event representing a product's price being changed."""
    
    event_type: str = "product_price_changed"
    product_id: str
    old_price: float
    new_price: float
    currency: str
    timestamp: datetime = None


# Order events

class OrderPlacedEvent(DomainEvent):
    """Event representing an order being placed."""
    
    event_type: str = "order_placed"
    order_id: str
    user_id: str
    total_amount: float
    currency: str
    items_count: int
    timestamp: datetime = None


class OrderCreatedEvent(DomainEvent):
    """Event representing an order being created."""
    
    event_type: str = "order_created"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderStatusChangedEvent(DomainEvent):
    """Event representing an order's status being changed."""
    
    event_type: str = "order_status_changed"
    order_id: str
    old_status: str
    new_status: str
    timestamp: datetime = None


class PaymentProcessedEvent(DomainEvent):
    """Event representing a payment being processed."""
    
    event_type: str = "payment_processed"
    order_id: str
    payment_id: str
    amount: float
    currency: str
    method: str
    status: str
    timestamp: datetime = None


class OrderItemAddedEvent(DomainEvent):
    """Event representing an item being added to an order."""
    
    event_type: str = "order_item_added"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderItemRemovedEvent(DomainEvent):
    """Event representing an item being removed from an order."""
    
    event_type: str = "order_item_removed"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderItemQuantityChangedEvent(DomainEvent):
    """Event representing an item's quantity being changed in an order."""
    
    event_type: str = "order_item_quantity_changed"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderPaidEvent(DomainEvent):
    """Event representing an order being paid."""
    
    event_type: str = "order_paid"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderShippedEvent(DomainEvent):
    """Event representing an order being shipped."""
    
    event_type: str = "order_shipped"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderDeliveredEvent(DomainEvent):
    """Event representing an order being delivered."""
    
    event_type: str = "order_delivered"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderCancelledEvent(DomainEvent):
    """Event representing an order being cancelled."""
    
    event_type: str = "order_cancelled"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


class OrderRefundedEvent(DomainEvent):
    """Event representing an order being refunded."""
    
    event_type: str = "order_refunded"
    aggregate_id: str
    aggregate_type: str = "order"
    data: Dict[str, Any]


# Cart events

class CartCreatedEvent(DomainEvent):
    """Event representing a cart being created."""
    
    event_type: str = "cart_created"
    aggregate_id: str
    aggregate_type: str = "cart"
    data: Dict[str, Any]


class CartItemAddedEvent(DomainEvent):
    """Event representing an item being added to a cart."""
    
    event_type: str = "cart_item_added"
    aggregate_id: str
    aggregate_type: str = "cart"
    data: Dict[str, Any]