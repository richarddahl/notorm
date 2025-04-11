"""
Example application demonstrating the e-commerce domain.

This script creates a simple command-line application that demonstrates
the capabilities of the e-commerce domain implementation.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from uno.dependencies import initialize_services, get_domain_registry, get_event_publisher
from uno.domain.events import EventBus, EventPublisher
from uno.domain.core import DomainEvent

from examples.ecommerce.domain.entities import (
    User, Product, Order, OrderStatus, PaymentMethod
)
from examples.ecommerce.domain.value_objects import (
    Money, Address, Rating, EmailAddress, PhoneNumber
)
from examples.ecommerce.domain.events import (
    UserRegisteredEvent, ProductCreatedEvent, OrderPlacedEvent,
    OrderStatusChangedEvent, PaymentProcessedEvent
)
from examples.ecommerce.domain.factories import EcommerceServiceFactory


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ecommerce_example")


# Event handlers
async def handle_user_registered(event: UserRegisteredEvent) -> None:
    """Handle user registered events."""
    logger.info(f"🎉 New user registered: {event.username} ({event.email})")
    logger.info(f"  - Would send welcome email to {event.email}")


async def handle_order_placed(event: OrderPlacedEvent) -> None:
    """Handle order placed events."""
    logger.info(f"🛒 New order placed: {event.order_id}")
    logger.info(f"  - User: {event.user_id}")
    logger.info(f"  - Total: {event.total_amount} {event.currency}")
    logger.info(f"  - Items: {event.items_count}")


async def handle_payment_processed(event: PaymentProcessedEvent) -> None:
    """Handle payment processed events."""
    logger.info(f"💰 Payment processed: {event.payment_id}")
    logger.info(f"  - Order: {event.order_id}")
    logger.info(f"  - Amount: {event.amount} {event.currency}")
    logger.info(f"  - Method: {event.method}")
    logger.info(f"  - Status: {event.status}")


async def handle_order_status_changed(event: OrderStatusChangedEvent) -> None:
    """Handle order status changed events."""
    logger.info(f"📦 Order status changed: {event.order_id}")
    logger.info(f"  - From: {event.old_status}")
    logger.info(f"  - To: {event.new_status}")
    
    # In a real application, we'd send notifications based on the new status
    if event.new_status == OrderStatus.SHIPPED:
        logger.info(f"  - Would send shipping notification to customer")
    elif event.new_status == OrderStatus.DELIVERED:
        logger.info(f"  - Would send delivery confirmation to customer")


# Set up event handlers
def setup_event_handlers(event_bus: EventBus) -> None:
    """Set up event handlers for the application."""
    event_bus.subscribe(UserRegisteredEvent, handle_user_registered)
    event_bus.subscribe(OrderPlacedEvent, handle_order_placed)
    event_bus.subscribe(PaymentProcessedEvent, handle_payment_processed)
    event_bus.subscribe(OrderStatusChangedEvent, handle_order_status_changed)


# Sample data
def create_sample_addresses() -> Dict[str, Address]:
    """Create sample addresses for the demo."""
    return {
        "home": Address(
            street="123 Main Street",
            city="Anytown",
            state="CA",
            postal_code="12345"
        ),
        "work": Address(
            street="456 Market Street",
            city="Somecity",
            state="NY",
            postal_code="67890"
        ),
        "shipping": Address(
            street="789 Oak Avenue",
            city="Otherville",
            state="TX",
            postal_code="45678"
        )
    }


async def create_sample_users(user_service) -> Dict[str, User]:
    """Create sample users for the demo."""
    addresses = create_sample_addresses()
    
    users = {}
    
    # Create first user
    users["john"] = await user_service.register_user({
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "555-123-4567",
        "billing_address": addresses["home"],
        "shipping_address": addresses["home"]
    })
    
    # Create second user
    users["jane"] = await user_service.register_user({
        "username": "janedoe",
        "email": "jane@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "555-987-6543",
        "billing_address": addresses["work"],
        "shipping_address": addresses["shipping"]
    })
    
    return users


async def create_sample_products(product_service) -> Dict[str, Product]:
    """Create sample products for the demo."""
    products = {}
    
    # Create first product
    products["laptop"] = await product_service.create_product({
        "name": "Premium Laptop",
        "description": "High-end laptop with 16GB RAM and 1TB SSD",
        "price": 1299.99,
        "inventory_count": 10,
        "attributes": {
            "brand": "TechPro",
            "model": "X5000",
            "color": "Silver",
            "weight": "3.5 lbs",
            "screen_size": "15.6 inches"
        }
    })
    
    # Create second product
    products["phone"] = await product_service.create_product({
        "name": "Smartphone Plus",
        "description": "Latest smartphone with advanced camera and long battery life",
        "price": 899.99,
        "inventory_count": 20,
        "attributes": {
            "brand": "PhoneCo",
            "model": "P12",
            "color": "Black",
            "storage": "256GB",
            "camera": "Triple 12MP"
        }
    })
    
    # Create third product
    products["headphones"] = await product_service.create_product({
        "name": "Wireless Headphones",
        "description": "Noise-cancelling wireless headphones with 30-hour battery life",
        "price": 249.99,
        "inventory_count": 30,
        "attributes": {
            "brand": "AudioLux",
            "model": "SoundPro",
            "color": "Black",
            "connectivity": "Bluetooth 5.0",
            "battery": "30 hours"
        }
    })
    
    return products


async def create_sample_order(
    order_service, 
    user: User, 
    products: Dict[str, Product]
) -> Optional[Order]:
    """Create a sample order for the demo."""
    # Create order
    order, errors = await order_service.create_order(
        user_id=user.id,
        shipping_address=user.shipping_address,
        billing_address=user.billing_address,
        items=[
            {"product_id": products["laptop"].id, "quantity": 1},
            {"product_id": products["headphones"].id, "quantity": 1}
        ]
    )
    
    if errors:
        logger.error(f"Errors creating order: {errors}")
        return None
    
    logger.info(f"Created order: {order.id}")
    logger.info(f"  - User: {order.user_id}")
    logger.info(f"  - Items: {len(order.items)}")
    logger.info(f"  - Subtotal: {order.subtotal.format()}")
    
    return order


async def process_order_payment(
    order_service,
    order: Order
) -> Optional[Order]:
    """Process payment for a sample order."""
    # Process payment
    updated_order, error = await order_service.process_payment(
        order_id=order.id,
        payment_method=PaymentMethod.CREDIT_CARD,
        payment_details={
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "holder_name": "John Doe"
        }
    )
    
    if error:
        logger.error(f"Error processing payment: {error}")
        return None
    
    logger.info(f"Processed payment for order: {updated_order.id}")
    logger.info(f"  - Status: {updated_order.status}")
    logger.info(f"  - Payment method: {updated_order.payment.method}")
    logger.info(f"  - Transaction ID: {updated_order.payment.transaction_id}")
    
    return updated_order


async def ship_order(
    order_service,
    order: Order
) -> Optional[Order]:
    """Ship a sample order."""
    # Update order status to shipped
    updated_order, error = await order_service.update_order_status(
        order_id=order.id,
        new_status=OrderStatus.SHIPPED,
        notes="Shipped via FedEx"
    )
    
    if error:
        logger.error(f"Error shipping order: {error}")
        return None
    
    logger.info(f"Shipped order: {updated_order.id}")
    logger.info(f"  - Status: {updated_order.status}")
    logger.info(f"  - Shipped at: {updated_order.shipped_at}")
    
    return updated_order


async def deliver_order(
    order_service,
    order: Order
) -> Optional[Order]:
    """Mark a sample order as delivered."""
    # Update order status to delivered
    updated_order, error = await order_service.update_order_status(
        order_id=order.id,
        new_status=OrderStatus.DELIVERED,
        notes="Delivered to customer"
    )
    
    if error:
        logger.error(f"Error marking order as delivered: {error}")
        return None
    
    logger.info(f"Delivered order: {updated_order.id}")
    logger.info(f"  - Status: {updated_order.status}")
    logger.info(f"  - Delivered at: {updated_order.delivered_at}")
    
    return updated_order


async def cancel_order(
    order_service,
    order: Order
) -> Optional[Order]:
    """Cancel a sample order."""
    # Cancel the order
    updated_order, error = await order_service.cancel_order(
        order_id=order.id,
        reason="Customer requested cancellation"
    )
    
    if error:
        logger.error(f"Error cancelling order: {error}")
        return None
    
    logger.info(f"Cancelled order: {updated_order.id}")
    logger.info(f"  - Status: {updated_order.status}")
    logger.info(f"  - Cancelled at: {updated_order.cancelled_at}")
    
    return updated_order


async def leave_review(
    product_service,
    product: Product,
    rating: int,
    comment: Optional[str] = None
) -> Optional[Product]:
    """Leave a review for a sample product."""
    # Get the product
    product = await product_service.get_by_id(product.id)
    if not product:
        logger.error(f"Product not found: {product.id}")
        return None
    
    # Add rating
    product.add_rating(Rating(score=rating, comment=comment))
    
    # Save the product
    updated_product = await product_service.save(product)
    
    logger.info(f"Added rating to product: {updated_product.name}")
    logger.info(f"  - Rating: {rating}/5")
    if comment:
        logger.info(f"  - Comment: {comment}")
    logger.info(f"  - Average rating: {updated_product.get_average_rating():.1f}/5")
    
    return updated_product


# Main demo function
async def run_demo():
    """Run the e-commerce demo application."""
    logger.info("Starting e-commerce domain demo")
    
    # Initialize services
    initialize_services()
    
    # Get domain registry and event publisher
    domain_registry = get_domain_registry()
    event_publisher = get_event_publisher()
    event_bus = event_publisher.event_bus
    
    # Set up event handlers
    setup_event_handlers(event_bus)
    
    # Create service factory
    service_factory = EcommerceServiceFactory(
        domain_registry=domain_registry,
        event_publisher=event_publisher,
        logger=logger
    )
    
    # Create services
    user_service = service_factory.create_user_service()
    product_service = service_factory.create_product_service()
    order_service = service_factory.create_order_service()
    
    # Create sample data
    logger.info("Creating sample users")
    users = await create_sample_users(user_service)
    
    logger.info("\nCreating sample products")
    products = await create_sample_products(product_service)
    
    # Demo 1: Create and process an order
    logger.info("\n=== Demo 1: Create and process an order ===")
    order = await create_sample_order(order_service, users["john"], products)
    if order:
        # Process payment
        order = await process_order_payment(order_service, order)
        
        # Ship the order
        if order:
            order = await ship_order(order_service, order)
            
            # Deliver the order
            if order:
                order = await deliver_order(order_service, order)
    
    # Demo 2: Create and cancel an order
    logger.info("\n=== Demo 2: Create and cancel an order ===")
    order2 = await create_sample_order(order_service, users["jane"], products)
    if order2:
        # Cancel the order
        order2 = await cancel_order(order_service, order2)
    
    # Demo 3: Leave product reviews
    logger.info("\n=== Demo 3: Leave product reviews ===")
    laptop = await leave_review(
        product_service, 
        products["laptop"], 
        5, 
        "Excellent laptop, fast and reliable!"
    )
    
    headphones = await leave_review(
        product_service,
        products["headphones"],
        4,
        "Great sound quality but a bit uncomfortable after long use."
    )
    
    phone = await leave_review(
        product_service,
        products["phone"],
        3,
        "Decent phone but battery life could be better."
    )
    
    logger.info("\nE-commerce domain demo completed!")


if __name__ == "__main__":
    asyncio.run(run_demo())