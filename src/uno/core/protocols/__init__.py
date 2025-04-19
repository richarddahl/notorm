"""
Core Protocol Definitions

This package contains the modern core protocol interfaces that define
the contracts for the major components of the system.

All legacy protocol interfaces have been removed in favor of the current architecture.
"""

from uno.core.protocols.entity import (
    AggregateRootProtocol,
    EntityProtocol,
    ValueObjectProtocol,
)
from uno.core.protocols.event import (
    EventBusProtocol,
    EventHandler,
    EventProtocol,
    EventPublisherProtocol,
    EventStoreProtocol,
)
from uno.core.protocols.repository import (
    PageableRepositoryProtocol,
    QueryableRepositoryProtocol,
    RepositoryProtocol,
)
from uno.core.protocols.service import (
    CrudServiceProtocol,
    QueryServiceProtocol,
    Result,
    ServiceProtocol,
)
from uno.infrastructure.database.provider import (
    ConnectionPoolProtocol,
    DatabaseConnectionProtocol,
    DatabaseManagerProtocol,
    DatabaseProviderProtocol,
    DatabaseSessionProtocol,
    QueryExecutorProtocol,
    TransactionManagerProtocol,
    UnoDatabaseProviderProtocol,
)

__all__ = [
    # Repository protocols
    "RepositoryProtocol",
    "QueryableRepositoryProtocol",
    "PageableRepositoryProtocol",
    # Service protocols
    "ServiceProtocol",
    "CrudServiceProtocol",
    "QueryServiceProtocol",
    "Result",
    # Event protocols
    "EventProtocol",
    "EventBusProtocol",
    "EventStoreProtocol",
    "EventPublisherProtocol",
    "EventHandler",
    # Entity protocols
    "EntityProtocol",
    "AggregateRootProtocol",
    "ValueObjectProtocol",
    # Database protocols
    "DatabaseProviderProtocol",
    "DatabaseConnectionProtocol",
    "DatabaseSessionProtocol",
    "TransactionManagerProtocol",
    "ConnectionPoolProtocol",
    "DatabaseManagerProtocol",
    "QueryExecutorProtocol",
    "UnoDatabaseProviderProtocol",
]
