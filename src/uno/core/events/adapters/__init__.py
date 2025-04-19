"""
Event store adapters for the UNO framework.

This package provides implementations of the EventStore interface for
various storage backends, such as PostgreSQL, Redis, or other databases.
"""

from uno.core.events.adapters.postgres import (
    PostgresEventStore,
    PostgresEventStoreConfig
)

__all__ = [
    "PostgresEventStore",
    "PostgresEventStoreConfig"
]