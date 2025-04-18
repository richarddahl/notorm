"""
Core Protocol Definitions

This package contains the core protocol interfaces that define
the contracts for the major components of the system.

Protocols defined in this package form the foundation of the architecture
and should be used as the primary abstraction for dependency injection
and component design.
"""

from uno.core.protocols.repository import (
    RepositoryProtocol,
    QueryableRepositoryProtocol,
    PageableRepositoryProtocol
)
from uno.core.protocols.service import (
    ServiceProtocol,
    CrudServiceProtocol,
    QueryServiceProtocol,
    Result
)
from uno.core.protocols.event import (
    EventProtocol,
    EventBusProtocol,
    EventStoreProtocol,
    EventPublisherProtocol,
    EventHandler
)
from uno.core.protocols.entity import (
    EntityProtocol,
    AggregateRootProtocol,
    ValueObjectProtocol
)
from uno.core.protocols.database import (
    DatabaseProviderProtocol,
    DatabaseConnectionProtocol,
    DatabaseSessionProtocol,
    TransactionManagerProtocol,
    ConnectionPoolProtocol,
    DatabaseManagerProtocol,
    QueryExecutorProtocol,
    UnoDatabaseProviderProtocol
)

__all__ = [
    # Repository protocols
    'RepositoryProtocol',
    'QueryableRepositoryProtocol',
    'PageableRepositoryProtocol',
    
    # Service protocols
    'ServiceProtocol',
    'CrudServiceProtocol',
    'QueryServiceProtocol',
    'Result',
    
    # Event protocols
    'EventProtocol',
    'EventBusProtocol',
    'EventStoreProtocol',
    'EventPublisherProtocol',
    'EventHandler',
    
    # Entity protocols
    'EntityProtocol',
    'AggregateRootProtocol',
    'ValueObjectProtocol',
    
    # Database protocols
    'DatabaseProviderProtocol',
    'DatabaseConnectionProtocol',
    'DatabaseSessionProtocol',
    'TransactionManagerProtocol',
    'ConnectionPoolProtocol',
    'DatabaseManagerProtocol',
    'QueryExecutorProtocol',
    'UnoDatabaseProviderProtocol',
]