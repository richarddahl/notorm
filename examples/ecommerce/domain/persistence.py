"""
Persistence implementations for the e-commerce domain.

This module provides concrete implementations of repositories and event
stores for the e-commerce domain using PostgreSQL.
"""

import logging
from typing import Dict, Any, Optional, List, Type

from sqlalchemy import Table, Column, String, TIMESTAMP, TEXT, BOOLEAN, MetaData
from sqlalchemy.dialects.postgresql import JSONB

from uno.domain.repository import UnoDBRepository
from uno.domain.event_store import PostgresEventStore, EventSourcedRepository
from uno.domain.event_dispatcher import EventDispatcher
from examples.ecommerce.domain.entities import Product, Order, User
from examples.ecommerce.domain.events import (
    ProductCreatedEvent, ProductUpdatedEvent, ProductDeletedEvent,
    OrderCreatedEvent, OrderStatusChangedEvent,
    UserCreatedEvent, UserUpdatedEvent
)


class ProductRepository(UnoDBRepository[Product]):
    """PostgreSQL repository for Product entities."""
    
    def __init__(self):
        super().__init__(Product)
        
        # Initialize event dispatcher and stores
        self.event_dispatcher = EventDispatcher()
        self.event_store = PostgresEventStore(ProductCreatedEvent)
        
        # Register event handlers
        self.event_dispatcher.subscribe("product_created", self.handle_product_created)
        self.event_dispatcher.subscribe("product_updated", self.handle_product_updated)
        self.event_dispatcher.subscribe("product_deleted", self.handle_product_deleted)
    
    async def add(self, product: Product) -> Product:
        """Add a product and dispatch creation event."""
        result = await super().add(product)
        
        # Create and dispatch event
        event = ProductCreatedEvent(
            aggregate_id=product.id,
            data=product.model_dump()
        )
        await self.event_dispatcher.publish(event)
        
        return result
    
    async def update(self, product: Product) -> Product:
        """Update a product and dispatch update event."""
        result = await super().update(product)
        
        # Create and dispatch event
        event = ProductUpdatedEvent(
            aggregate_id=product.id,
            data=product.model_dump()
        )
        await self.event_dispatcher.publish(event)
        
        return result
    
    async def remove(self, product: Product) -> None:
        """Remove a product and dispatch deletion event."""
        await super().remove(product)
        
        # Create and dispatch event
        event = ProductDeletedEvent(
            aggregate_id=product.id,
            data={"id": product.id}
        )
        await self.event_dispatcher.publish(event)
    
    async def handle_product_created(self, event: ProductCreatedEvent) -> None:
        """Handle product created events."""
        # Log the event
        logging.getLogger(__name__).info(f"Product created: {event.aggregate_id}")
        
        # Additional handling could be done here, such as:
        # - Sending notifications
        # - Updating caches
        # - Triggering integrations
    
    async def handle_product_updated(self, event: ProductUpdatedEvent) -> None:
        """Handle product updated events."""
        logging.getLogger(__name__).info(f"Product updated: {event.aggregate_id}")
    
    async def handle_product_deleted(self, event: ProductDeletedEvent) -> None:
        """Handle product deleted events."""
        logging.getLogger(__name__).info(f"Product deleted: {event.aggregate_id}")


class OrderRepository(UnoDBRepository[Order]):
    """PostgreSQL repository for Order entities."""
    
    def __init__(self):
        super().__init__(Order)
        
        # Initialize event dispatcher and stores
        self.event_dispatcher = EventDispatcher()
        self.event_store = PostgresEventStore(OrderCreatedEvent)
        
        # Register event handlers
        self.event_dispatcher.subscribe("order_created", self.handle_order_created)
        self.event_dispatcher.subscribe("order_status_changed", self.handle_order_status_changed)
    
    async def add(self, order: Order) -> Order:
        """Add an order and dispatch creation event."""
        result = await super().add(order)
        
        # Create and dispatch event
        event = OrderCreatedEvent(
            aggregate_id=order.id,
            data=order.model_dump()
        )
        await self.event_dispatcher.publish(event)
        
        return result
    
    async def update(self, order: Order) -> Order:
        """Update an order and dispatch update event if status changed."""
        # Get the original order to check for status changes
        original_order = await self.get(order.id)
        result = await super().update(order)
        
        # Check if status changed
        if original_order and original_order.status != order.status:
            # Create and dispatch status change event
            event = OrderStatusChangedEvent(
                aggregate_id=order.id,
                data={
                    "order_id": order.id,
                    "previous_status": original_order.status,
                    "new_status": order.status,
                    "timestamp": order.updated_at
                }
            )
            await self.event_dispatcher.publish(event)
        
        return result
    
    async def handle_order_created(self, event: OrderCreatedEvent) -> None:
        """Handle order created events."""
        logging.getLogger(__name__).info(f"Order created: {event.aggregate_id}")
        
        # Additional handling could include:
        # - Sending confirmation emails
        # - Updating inventory
        # - Notifying fulfillment systems
    
    async def handle_order_status_changed(self, event: OrderStatusChangedEvent) -> None:
        """Handle order status changed events."""
        logging.getLogger(__name__).info(
            f"Order {event.aggregate_id} status changed from "
            f"{event.data['previous_status']} to {event.data['new_status']}"
        )
        
        # Different actions based on the new status
        new_status = event.data['new_status']
        
        if new_status == "PAID":
            # Send payment confirmation email
            # Update accounting systems
            pass
        
        elif new_status == "SHIPPED":
            # Send shipping notification
            # Update inventory
            pass
        
        elif new_status == "DELIVERED":
            # Send delivery confirmation
            # Request feedback
            pass
        
        elif new_status == "CANCELLED":
            # Send cancellation confirmation
            # Return items to inventory
            # Process refunds if applicable
            pass


class EventSourcedOrderRepository(EventSourcedRepository[OrderCreatedEvent]):
    """Event-sourced repository for Order entities."""
    
    def __init__(self):
        event_store = PostgresEventStore(OrderCreatedEvent)
        super().__init__(Order, event_store)


class UserRepository(UnoDBRepository[User]):
    """PostgreSQL repository for User entities."""
    
    def __init__(self):
        super().__init__(User)
        
        # Initialize event dispatcher and stores
        self.event_dispatcher = EventDispatcher()
        self.event_store = PostgresEventStore(UserCreatedEvent)
        
        # Register event handlers
        self.event_dispatcher.subscribe("user_created", self.handle_user_created)
        self.event_dispatcher.subscribe("user_updated", self.handle_user_updated)
    
    async def add(self, user: User) -> User:
        """Add a user and dispatch creation event."""
        result = await super().add(user)
        
        # Create and dispatch event
        event = UserCreatedEvent(
            aggregate_id=user.id,
            data=user.model_dump(exclude={"password_hash"})  # Never include sensitive data in events
        )
        await self.event_dispatcher.publish(event)
        
        return result
    
    async def update(self, user: User) -> User:
        """Update a user and dispatch update event."""
        result = await super().update(user)
        
        # Create and dispatch event
        event = UserUpdatedEvent(
            aggregate_id=user.id,
            data=user.model_dump(exclude={"password_hash"})  # Never include sensitive data in events
        )
        await self.event_dispatcher.publish(event)
        
        return result
    
    async def handle_user_created(self, event: UserCreatedEvent) -> None:
        """Handle user created events."""
        logging.getLogger(__name__).info(f"User created: {event.aggregate_id}")
        
        # Additional handling could include:
        # - Sending welcome emails
        # - Creating associated profiles in other systems
        # - Setting up default preferences
    
    async def handle_user_updated(self, event: UserUpdatedEvent) -> None:
        """Handle user updated events."""
        logging.getLogger(__name__).info(f"User updated: {event.aggregate_id}")
        
        # Check for specific updates that need action
        if 'email' in event.data:
            # Send email change confirmation
            pass
        
        if 'address' in event.data:
            # Update shipping preferences
            pass