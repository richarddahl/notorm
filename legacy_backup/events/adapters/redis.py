"""
Redis adapter for event publishing and subscribing.

This module provides Redis-based implementations for event publishing
and subscribing, enabling distributed event processing across services.
"""

import asyncio
import json
from typing import Dict, List, Optional, Type, TypeVar, Union

import redis.asyncio as aioredis
import structlog

from uno.events.core.bus import EventBus
from uno.events.core.event import Event
from uno.events.core.handler import EventHandler, EventHandlerCallable
from uno.events.core.handler import EventPriority

# Type variable for events
E = TypeVar("E", bound=Event)


class RedisEventPublisher:
    """
    Redis implementation of an event publisher.
    
    This publisher uses Redis Pub/Sub to distribute events to multiple
    subscribers, enabling distributed event processing across services.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        channel_prefix: str = "uno:events:",
    ):
        """
        Initialize the Redis event publisher.
        
        Args:
            redis_url: Redis connection URL
            channel_prefix: Prefix for Redis channels
        """
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.logger = structlog.get_logger("uno.events.redis")
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """
        Connect to Redis.
        
        Raises:
            RuntimeError: If connection fails
        """
        try:
            if not self.redis:
                self.redis = await aioredis.from_url(self.redis_url)
                # Test connection
                await self.redis.ping()
                self.logger.info("Connected to Redis", url=self.redis_url)
        except Exception as e:
            self.logger.error("Failed to connect to Redis", error=str(e))
            raise RuntimeError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            self.logger.info("Disconnected from Redis")
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to Redis.
        
        Args:
            event: The event to publish
            
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Redis is not connected")
        
        # Determine channel name (use event type and optionally topic)
        type_channel = f"{self.channel_prefix}type:{event.type}"
        channels = [type_channel]
        
        # Add topic channel if event has a topic
        if event.topic:
            topic_channel = f"{self.channel_prefix}topic:{event.topic}"
            channels.append(topic_channel)
        
        # Add a channel for all events
        all_channel = f"{self.channel_prefix}all"
        channels.append(all_channel)
        
        # Serialize event to JSON
        event_json = event.to_json()
        
        # Publish to all relevant channels
        for channel in channels:
            try:
                await self.redis.publish(channel, event_json)
                self.logger.debug(
                    "Published event to Redis",
                    event_id=event.id,
                    event_type=event.type,
                    channel=channel,
                )
            except Exception as e:
                self.logger.error(
                    "Failed to publish event to Redis",
                    event_id=event.id,
                    event_type=event.type,
                    channel=channel,
                    error=str(e),
                )
                raise


class RedisEventSubscriber:
    """
    Redis implementation of an event subscriber.
    
    This subscriber listens for events on Redis Pub/Sub channels and
    dispatches them to local handlers, enabling distributed event
    processing across services.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        event_type: Type[Event],
        redis_url: str = "redis://localhost:6379/0",
        channel_prefix: str = "uno:events:",
    ):
        """
        Initialize the Redis event subscriber.
        
        Args:
            event_bus: The event bus to dispatch events to
            event_type: The type of events this subscriber handles
            redis_url: Redis connection URL
            channel_prefix: Prefix for Redis channels
        """
        self.event_bus = event_bus
        self.event_type = event_type
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.logger = structlog.get_logger("uno.events.redis")
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Track subscribed channels
        self.subscribed_channels: List[str] = []
    
    async def connect(self) -> None:
        """
        Connect to Redis.
        
        Raises:
            RuntimeError: If connection fails
        """
        try:
            if not self.redis:
                self.redis = await aioredis.from_url(self.redis_url)
                self.pubsub = self.redis.pubsub()
                # Test connection
                await self.redis.ping()
                self.logger.info("Connected to Redis", url=self.redis_url)
        except Exception as e:
            self.logger.error("Failed to connect to Redis", error=str(e))
            raise RuntimeError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            self.pubsub = None
        
        if self.redis:
            await self.redis.close()
            self.redis = None
        
        self.logger.info("Disconnected from Redis")
    
    async def subscribe_by_type(self, event_type: str) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The event type to subscribe to
            
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self.redis or not self.pubsub:
            await self.connect()
        
        if not self.redis or not self.pubsub:
            raise RuntimeError("Redis is not connected")
        
        channel = f"{self.channel_prefix}type:{event_type}"
        await self.pubsub.subscribe(channel)
        self.subscribed_channels.append(channel)
        
        self.logger.info("Subscribed to events by type", event_type=event_type)
    
    async def subscribe_by_topic(self, topic: str) -> None:
        """
        Subscribe to events with a specific topic.
        
        Args:
            topic: The topic to subscribe to
            
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self.redis or not self.pubsub:
            await self.connect()
        
        if not self.redis or not self.pubsub:
            raise RuntimeError("Redis is not connected")
        
        channel = f"{self.channel_prefix}topic:{topic}"
        await self.pubsub.subscribe(channel)
        self.subscribed_channels.append(channel)
        
        self.logger.info("Subscribed to events by topic", topic=topic)
    
    async def subscribe_all(self) -> None:
        """
        Subscribe to all events.
        
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self.redis or not self.pubsub:
            await self.connect()
        
        if not self.redis or not self.pubsub:
            raise RuntimeError("Redis is not connected")
        
        channel = f"{self.channel_prefix}all"
        await self.pubsub.subscribe(channel)
        self.subscribed_channels.append(channel)
        
        self.logger.info("Subscribed to all events")
    
    async def unsubscribe(self) -> None:
        """Unsubscribe from all channels."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            self.subscribed_channels = []
            self.logger.info("Unsubscribed from all channels")
    
    async def start(self) -> None:
        """
        Start listening for events.
        
        Raises:
            RuntimeError: If Redis is not connected or already running
        """
        if self.running:
            return
        
        if not self.redis or not self.pubsub:
            await self.connect()
        
        if not self.redis or not self.pubsub:
            raise RuntimeError("Redis is not connected")
        
        if not self.subscribed_channels:
            self.logger.warning("No channels subscribed, subscribing to all events")
            await self.subscribe_all()
        
        self.running = True
        self.task = asyncio.create_task(self._listen_for_messages())
        self.logger.info("Started listening for events on Redis")
    
    async def stop(self) -> None:
        """Stop listening for events."""
        if not self.running:
            return
        
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        await self.unsubscribe()
        self.logger.info("Stopped listening for events on Redis")
    
    async def _listen_for_messages(self) -> None:
        """
        Listen for messages on subscribed channels.
        
        This method runs in a loop, processing messages as they arrive.
        """
        if not self.pubsub:
            self.logger.error("PubSub not initialized")
            return
        
        try:
            self.logger.info("Listening for messages on Redis")
            
            while self.running:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                
                if not message:
                    # No message, continue waiting
                    await asyncio.sleep(0.01)
                    continue
                
                # Process message
                try:
                    await self._process_message(message)
                except Exception as e:
                    self.logger.error(
                        "Error processing Redis message",
                        error=str(e),
                        message=message,
                        exc_info=True,
                    )
        
        except asyncio.CancelledError:
            # Task cancelled, exit gracefully
            self.logger.info("Redis message listener cancelled")
            raise
        
        except Exception as e:
            self.logger.error(
                "Error in Redis message listener",
                error=str(e),
                exc_info=True,
            )
            # Reconnect if possible
            if self.running:
                self.logger.info("Attempting to reconnect to Redis")
                await self.disconnect()
                try:
                    await self.connect()
                    channels = self.subscribed_channels.copy()
                    self.subscribed_channels = []
                    for channel in channels:
                        await self.pubsub.subscribe(channel)
                        self.subscribed_channels.append(channel)
                    self.logger.info("Reconnected to Redis")
                except Exception as reconnect_error:
                    self.logger.error(
                        "Failed to reconnect to Redis",
                        error=str(reconnect_error),
                        exc_info=True,
                    )
    
    async def _process_message(self, message: Dict) -> None:
        """
        Process a message from Redis.
        
        Args:
            message: The Redis message
        """
        # Extract message data
        channel = message.get("channel", b"").decode("utf-8")
        data = message.get("data")
        
        if not data or not isinstance(data, bytes):
            self.logger.warning("Received invalid message data", channel=channel)
            return
        
        try:
            # Parse JSON data
            json_data = json.loads(data.decode("utf-8"))
            
            # Create event
            event = self.event_type.from_dict(json_data)
            
            self.logger.debug(
                "Received event from Redis",
                event_id=event.id,
                event_type=event.type,
                channel=channel,
            )
            
            # Dispatch event to local event bus
            await self.event_bus.publish(event)
        
        except json.JSONDecodeError:
            self.logger.error(
                "Failed to decode JSON message",
                channel=channel,
                data=data.decode("utf-8", errors="replace"),
            )
        except Exception as e:
            self.logger.error(
                "Error processing Redis message",
                channel=channel,
                error=str(e),
                exc_info=True,
            )