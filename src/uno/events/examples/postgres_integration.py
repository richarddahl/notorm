"""
PostgreSQL integration example for the Uno event system.

This module demonstrates how to use the PostgreSQL adapter for event
persistence and retrieval.
"""

import asyncio
import os
from datetime import datetime, UTC
from typing import Optional, List

from pydantic import Field

from uno.events import Event, EventBus, EventPublisher, event_handler, subscribe
from uno.events.adapters.postgres import PostgresEventStore, PostgresEventStoreManager


# Define some events
class OrderCreated(Event):
    """Event emitted when an order is created."""
    
    order_id: str
    customer_id: str
    total_amount: float
    items: List[dict]


class OrderShipped(Event):
    """Event emitted when an order is shipped."""
    
    order_id: str
    shipped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tracking_number: str


class OrderDelivered(Event):
    """Event emitted when an order is delivered."""
    
    order_id: str
    delivered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# Define some event handlers
@event_handler(OrderCreated)
async def on_order_created(event: OrderCreated) -> None:
    """Handle the OrderCreated event."""
    print(f"New order created: {event.order_id}")
    print(f"Customer: {event.customer_id}")
    print(f"Total amount: ${event.total_amount:.2f}")
    print(f"Items: {len(event.items)}")


@event_handler(OrderShipped)
async def on_order_shipped(event: OrderShipped) -> None:
    """Handle the OrderShipped event."""
    print(f"Order {event.order_id} has been shipped at {event.shipped_at}")
    print(f"Tracking number: {event.tracking_number}")


@event_handler(OrderDelivered)
async def on_order_delivered(event: OrderDelivered) -> None:
    """Handle the OrderDelivered event."""
    print(f"Order {event.order_id} has been delivered at {event.delivered_at}")


async def run_example() -> None:
    """Run the PostgreSQL integration example."""
    # Get database connection string from environment or use default
    connection_string = os.environ.get(
        "DATABASE_URL",
        "postgresql://username:password@localhost:5432/database"
    )
    
    try:
        # Initialize event store schema
        PostgresEventStore.initialize_schema(
            schema="public",
            table_name="events",
            connection_string=connection_string,
        )
        
        # Create event store
        event_store = PostgresEventStore(
            event_type=Event,
            schema="public",
            table_name="events",
            connection_string=connection_string,
        )
        
        # Create event bus and publisher
        event_bus = EventBus()
        event_publisher = EventPublisher(event_bus, event_store)
        
        # Register event handlers
        subscribe(OrderCreated, on_order_created)
        subscribe(OrderShipped, on_order_shipped)
        subscribe(OrderDelivered, on_order_delivered)
        
        # Create and publish some events
        order_id = "ORD-12345"
        customer_id = "CUST-6789"
        
        # Create order
        order_created = OrderCreated(
            order_id=order_id,
            customer_id=customer_id,
            total_amount=99.99,
            items=[
                {"product_id": "PROD-1", "quantity": 2, "price": 49.99},
            ],
        )
        await event_publisher.publish(order_created)
        print("-" * 50)
        
        # Ship order
        order_shipped = OrderShipped(
            order_id=order_id,
            tracking_number="TRK-987654321",
        )
        await event_publisher.publish(order_shipped)
        print("-" * 50)
        
        # Deliver order
        order_delivered = OrderDelivered(
            order_id=order_id,
        )
        await event_publisher.publish(order_delivered)
        print("-" * 50)
        
        # Retrieve events for a specific order
        print("\nEvent history for order:")
        events = await event_store.get_events_by_aggregate_id(order_id)
        
        for i, event in enumerate(events, 1):
            print(f"{i}. {event.type} at {event.timestamp}")
        
        # Retrieve events by type
        print("\nAll OrderCreated events:")
        created_events = await event_store.get_events_by_type("order_created")
        
        for i, event in enumerate(created_events, 1):
            print(f"{i}. Order {event.order_id} for customer {event.customer_id}")
    
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This example requires a running PostgreSQL database.")
        print("Set the DATABASE_URL environment variable to connect to your database.")


if __name__ == "__main__":
    asyncio.run(run_example())