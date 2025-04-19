"""
Redis integration example for the Uno event system.

This module demonstrates how to use the Redis adapter for distributed
event publishing and subscribing across multiple services.
"""

import asyncio
import os
from datetime import datetime, UTC
from typing import Optional, List

from pydantic import Field

from uno.events import Event, EventBus, EventPublisher, event_handler, subscribe
from uno.events.adapters.redis import RedisEventPublisher, RedisEventSubscriber


# Define some events
class MessageSent(Event):
    """Event emitted when a chat message is sent."""
    
    message_id: str
    chat_id: str
    sender_id: str
    content: str
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MessageRead(Event):
    """Event emitted when a chat message is read."""
    
    message_id: str
    chat_id: str
    reader_id: str
    read_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatCreated(Event):
    """Event emitted when a new chat is created."""
    
    chat_id: str
    name: str
    created_by: str
    member_ids: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# Define some event handlers
@event_handler(MessageSent)
async def on_message_sent(event: MessageSent) -> None:
    """Handle the MessageSent event."""
    print(f"New message in chat {event.chat_id}:")
    print(f"From: {event.sender_id}")
    print(f"Content: {event.content}")
    print(f"Sent at: {event.sent_at}")


@event_handler(MessageRead)
async def on_message_read(event: MessageRead) -> None:
    """Handle the MessageRead event."""
    print(f"Message {event.message_id} read by {event.reader_id} at {event.read_at}")


@event_handler(ChatCreated)
async def on_chat_created(event: ChatCreated) -> None:
    """Handle the ChatCreated event."""
    print(f"New chat created: {event.name} (ID: {event.chat_id})")
    print(f"Created by: {event.created_by}")
    print(f"Members: {', '.join(event.member_ids)}")


async def publisher_service() -> None:
    """Simulate a publisher service that sends events to Redis."""
    # Get Redis URL from environment or use default
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    try:
        # Create Redis publisher
        redis_publisher = RedisEventPublisher(redis_url=redis_url)
        await redis_publisher.connect()
        
        print("Publisher service started")
        
        # Publish some events
        chat_id = "CHAT-12345"
        
        # Create a new chat
        chat_created = ChatCreated(
            chat_id=chat_id,
            name="Redis Example Chat",
            created_by="user1",
            member_ids=["user1", "user2", "user3"],
        )
        await redis_publisher.publish(chat_created)
        print("Published ChatCreated event")
        
        # Send a message
        message_id = "MSG-98765"
        message_sent = MessageSent(
            message_id=message_id,
            chat_id=chat_id,
            sender_id="user1",
            content="Hello, Redis event system!",
        )
        await redis_publisher.publish(message_sent)
        print("Published MessageSent event")
        
        # Mark message as read
        message_read = MessageRead(
            message_id=message_id,
            chat_id=chat_id,
            reader_id="user2",
        )
        await redis_publisher.publish(message_read)
        print("Published MessageRead event")
        
        # Disconnect
        await redis_publisher.disconnect()
    
    except Exception as e:
        print(f"Publisher error: {e}")


async def subscriber_service() -> None:
    """Simulate a subscriber service that listens for events from Redis."""
    # Get Redis URL from environment or use default
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    try:
        # Create event bus and register handlers
        event_bus = EventBus()
        
        subscribe(MessageSent, on_message_sent)
        subscribe(MessageRead, on_message_read)
        subscribe(ChatCreated, on_chat_created)
        
        # Create Redis subscriber
        redis_subscriber = RedisEventSubscriber(
            event_bus=event_bus,
            event_type=Event,
            redis_url=redis_url,
        )
        
        # Subscribe to event types
        await redis_subscriber.connect()
        await redis_subscriber.subscribe_by_type("message_sent")
        await redis_subscriber.subscribe_by_type("message_read")
        await redis_subscriber.subscribe_by_type("chat_created")
        
        print("Subscriber service started")
        print("Listening for events (press Ctrl+C to stop)...")
        
        # Start listening for events
        await redis_subscriber.start()
        
        # Keep the service running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            # Stop gracefully
            await redis_subscriber.stop()
            await redis_subscriber.disconnect()
    
    except Exception as e:
        print(f"Subscriber error: {e}")


async def run_example() -> None:
    """Run the Redis integration example."""
    try:
        # Start subscriber first
        subscriber_task = asyncio.create_task(subscriber_service())
        
        # Wait a bit for the subscriber to connect
        await asyncio.sleep(2)
        
        # Then publish events
        await publisher_service()
        
        # Wait a bit to see the subscriber receive events
        await asyncio.sleep(5)
        
        # Cancel the subscriber task
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass
    
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This example requires a running Redis server.")
        print("Set the REDIS_URL environment variable to connect to your Redis server.")


if __name__ == "__main__":
    asyncio.run(run_example())