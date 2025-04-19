"""
Core Event System for UNO Framework

This module implements the event system for the UNO framework, providing
a decoupled communication mechanism between components via an event-driven
architecture.

Key components:
- Event: Base class for all domain events
- AsyncEventBus: Implementation of the EventBusProtocol
- EventStore: Interface for event persistence
- EventPublisher: Utility for publishing events
- Adapters: Implementations of EventStore for different backends
- SubscriptionManager: Management of event subscriptions
- API: FastAPI integration for subscription management
"""

from uno.core.events.event import Event
from uno.core.events.bus import AsyncEventBus
from uno.core.events.store import EventStore, InMemoryEventStore
from uno.core.events.publisher import EventPublisher
from uno.core.events.adapters import PostgresEventStore, PostgresEventStoreConfig
from uno.core.events.subscription import (
    SubscriptionManager,
    SubscriptionRepository,
    SubscriptionConfig,
    SubscriptionInfo,
    EventTypeInfo,
    SubscriptionMetrics
)
from uno.core.events.api import create_subscription_router

__all__ = [
    # Core event components
    'Event',
    'AsyncEventBus',
    'EventStore',
    'InMemoryEventStore',
    'EventPublisher',
    
    # Event store adapters
    'PostgresEventStore',
    'PostgresEventStoreConfig',
    
    # Subscription management
    'SubscriptionManager',
    'SubscriptionRepository',
    'SubscriptionConfig',
    'SubscriptionInfo',
    'EventTypeInfo',
    'SubscriptionMetrics',
    'create_subscription_router',
]