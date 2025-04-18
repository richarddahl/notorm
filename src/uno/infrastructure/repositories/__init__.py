"""
Repository pattern implementation for the Uno framework.

This package provides a comprehensive implementation of the repository pattern,
with support for various repository capabilities, including:

- Basic CRUD operations
- Specification pattern for querying
- Batch operations for efficiency
- Streaming for large datasets
- Event collection for domain events
- Aggregate root support
- Unit of Work pattern for transaction management

The implementation is designed to be flexible and extensible, with support for
different persistence mechanisms (currently SQLAlchemy and in-memory).
"""

from uno.infrastructure.repositories.protocols import (
    RepositoryProtocol,
    SpecificationRepositoryProtocol,
    BatchRepositoryProtocol,
    StreamingRepositoryProtocol,
    EventCollectingRepositoryProtocol,
    AggregateRootRepositoryProtocol,
    UnitOfWorkProtocol,
    RepositoryFactoryProtocol,
)

from uno.infrastructure.repositories.base import (
    Repository,
    SpecificationRepository,
    BatchRepository,
    StreamingRepository,
    EventCollectingRepository,
    AggregateRepository,
    CompleteRepository,
)

from uno.infrastructure.repositories.unit_of_work import (
    UnitOfWork,
    SQLAlchemyUnitOfWork,
    InMemoryUnitOfWork,
)

from uno.infrastructure.repositories.factory import (
    initialize_factories,
    get_repository_factory,
    get_unit_of_work_factory,
    create_repository,
    create_unit_of_work,
)

from uno.infrastructure.repositories.di import (
    init_repository_system,
    get_repository,
    get_unit_of_work,
    register_specification_translator,
    clear_repository_cache,
)

# Export everything for convenient imports
__all__ = [
    # Protocols
    "RepositoryProtocol",
    "SpecificationRepositoryProtocol",
    "BatchRepositoryProtocol",
    "StreamingRepositoryProtocol",
    "EventCollectingRepositoryProtocol",
    "AggregateRootRepositoryProtocol",
    "UnitOfWorkProtocol",
    "RepositoryFactoryProtocol",
    
    # Base implementations
    "Repository",
    "SpecificationRepository",
    "BatchRepository",
    "StreamingRepository",
    "EventCollectingRepository",
    "AggregateRepository",
    "CompleteRepository",
    
    # Unit of Work
    "UnitOfWork",
    "SQLAlchemyUnitOfWork",
    "InMemoryUnitOfWork",
    
    # Factory functions
    "initialize_factories",
    "get_repository_factory",
    "get_unit_of_work_factory",
    "create_repository",
    "create_unit_of_work",
    
    # DI helpers
    "init_repository_system",
    "get_repository",
    "get_unit_of_work",
    "register_specification_translator",
    "clear_repository_cache",
]