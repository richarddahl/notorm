#!/usr/bin/env python3
"""
Integration demo for DDD architecture with persistence.

This script demonstrates the complete domain-driven design architecture
with the PostgreSQL persistence layer, showing:
1. Entity creation and business logic
2. Repository pattern for data access
3. Event handling and propagation
4. Domain event persistence
"""

import asyncio
import logging
import uuid
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ddd-demo")

# Import domain models
from examples.ecommerce.domain.entities import Product, Order, User, OrderStatus
from examples.ecommerce.domain.value_objects import Money, Address, EmailAddress, PhoneNumber
from examples.ecommerce.domain.persistence import (
    ProductRepository, OrderRepository, UserRepository
)
from examples.ecommerce.domain.events import ProductCreatedEvent, OrderCreatedEvent
from uno.domain.event_store import PostgresEventStore
from uno.domain.event_dispatcher import EventDispatcher, domain_event_handler, EventSubscriber


# Create an event subscriber to demonstrate the event system
class LoggingEventSubscriber(EventSubscriber):
    """Event subscriber that logs all events."""
    
    def __init__(self, dispatcher: EventDispatcher):
        super().__init__(dispatcher)
        self.logger = logging.getLogger("event-subscriber")
    
    @domain_event_handler("product_created")
    async def handle_product_created(self, event: ProductCreatedEvent):
        """Handle product created events."""
        self.logger.info(f"🎉 Product created: {event.aggregate_id} - {event.data.get('name')}")
        self.logger.info(f"  Price: {event.data.get('price', {}).get('amount')} {event.data.get('price', {}).get('currency')}")
    
    @domain_event_handler("order_created")
    async def handle_order_created(self, event: OrderCreatedEvent):
        """Handle order created events."""
        self.logger.info(f"📦 Order created: {event.aggregate_id}")
        self.logger.info(f"  Items: {len(event.data.get('items', []))}")
        self.logger.info(f"  Status: {event.data.get('status')}")
    
    @domain_event_handler("order_status_changed")
    async def handle_order_status_changed(self, event: Any):
        """Handle order status changed events."""
        self.logger.info(
            f"🔄 Order status changed: {event.aggregate_id} - "
            f"{event.data.get('previous_status')} → {event.data.get('new_status')}"
        )
    
    @domain_event_handler("*")
    async def handle_all_events(self, event: Any):
        """Handle all events for monitoring."""
        self.logger.debug(f"Event received: {event.event_type} - {event.event_id}")


async def initialize_event_store():
    """Initialize the event store schema if needed."""
    logger.info("Initializing event store schema...")
    try:
        PostgresEventStore.initialize_schema(logger=logger)
        logger.info("Event store schema initialized.")
    except Exception as e:
        logger.error(f"Error initializing event store: {e}")
        logger.info("Continuing with demo...")


async def create_sample_data():
    """Create sample products, users, and orders."""
    logger.info("Creating repositories...")
    product_repo = ProductRepository()
    user_repo = UserRepository()
    order_repo = OrderRepository()
    
    # Create event dispatcher and subscriber
    dispatcher = EventDispatcher()
    event_subscriber = LoggingEventSubscriber(dispatcher)
    
    logger.info("Creating sample products...")
    # Create sample products
    products = []
    products.append(await create_product(
        product_repo,
        "Smartphone X",
        "Latest smartphone with advanced features",
        699.99,
        inventory_count=50
    ))
    
    products.append(await create_product(
        product_repo,
        "Wireless Headphones",
        "Premium noise-cancelling headphones",
        199.99,
        inventory_count=100
    ))
    
    products.append(await create_product(
        product_repo,
        "Laptop Pro",
        "High-performance laptop for professionals",
        1299.99,
        inventory_count=25
    ))
    
    logger.info("Creating sample user...")
    # Create a sample user
    user = User(
        id=str(uuid.uuid4()),
        username="johndoe",
        email=EmailAddress(address="john.doe@example.com"),
        first_name="John",
        last_name="Doe",
        phone=PhoneNumber(number="+1234567890"),
        billing_address=Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345",
            country="USA"
        ),
        shipping_address=Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345",
            country="USA"
        )
    )
    
    user = await user_repo.add(user)
    logger.info(f"User created: {user.id} - {user.username}")
    
    logger.info("Creating sample order...")
    # Create a sample order
    order = Order(
        id=str(uuid.uuid4()),
        user_id=user.id,
        status=OrderStatus.PENDING,
        shipping_address=user.shipping_address,
        billing_address=user.billing_address,
        created_at=datetime.now(datetime.UTC)
    )
    
    # Add items to the order
    order.add_item(
        product_id=products[0].id,
        product_name=products[0].name,
        price=products[0].price,
        quantity=1
    )
    
    order.add_item(
        product_id=products[1].id,
        product_name=products[1].name,
        price=products[1].price,
        quantity=2
    )
    
    # Save the order
    order = await order_repo.add(order)
    logger.info(f"Order created: {order.id} with {len(order.items)} items")
    
    # Update order status to demonstrate events
    logger.info("Updating order status...")
    order.update_status(OrderStatus.PAID, "Payment received via credit card")
    order = await order_repo.update(order)
    
    # Wait for all events to be processed
    await asyncio.sleep(1)
    
    return {
        "products": products,
        "user": user,
        "order": order
    }


async def create_product(repo, name, description, price, inventory_count=0):
    """Helper to create a product with error handling."""
    try:
        product = Product(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            price=Money(amount=price, currency="USD"),
            inventory_count=inventory_count,
            created_at=datetime.now(datetime.UTC)
        )
        
        return await repo.add(product)
    except Exception as e:
        logger.error(f"Error creating product {name}: {e}")
        raise


async def main():
    """Main demo function."""
    logger.info("Starting DDD architecture demo")
    
    # Initialize event store
    await initialize_event_store()
    
    # Create sample data
    sample_data = await create_sample_data()
    
    # Display summary
    logger.info("\n" + "="*50)
    logger.info("Demo completed successfully!")
    logger.info(f"Created {len(sample_data['products'])} products")
    logger.info(f"Created user: {sample_data['user'].username}")
    logger.info(f"Created order: {sample_data['order'].id} ({sample_data['order'].status})")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(main())