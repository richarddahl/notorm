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
"""

from uno.core.events.event import Event
from uno.core.events.bus import AsyncEventBus
from uno.core.events.store import EventStore, InMemoryEventStore
from uno.core.events.publisher import EventPublisher

__all__ = [
    'Event',
    'AsyncEventBus',
    'EventStore',
    'InMemoryEventStore',
    'EventPublisher',
]