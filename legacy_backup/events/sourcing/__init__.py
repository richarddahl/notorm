"""
Event sourcing for domain entities.

This package provides tools for implementing event sourcing in domain entities,
enabling entity state to be rebuilt from an event history.
"""

from uno.events.sourcing.aggregate import AggregateRoot, apply_event
from uno.events.sourcing.repository import EventSourcedRepository

__all__ = [
    "AggregateRoot",
    "EventSourcedRepository",
    "apply_event",
]