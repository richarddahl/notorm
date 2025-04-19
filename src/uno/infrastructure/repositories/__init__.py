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

The implementation is designed to be flexible and extensible, with support for
different persistence mechanisms (currently SQLAlchemy and in-memory).

NOTE: The Unit of Work pattern has been moved to uno.core.uow and all code
in this package that references UnitOfWork is deprecated.
"""


# Deprecation warnings removed: this module now only exposes modern implementations.

# Import from core base
from uno.core.base import (
    BaseRepository,
    SpecificationRepository,
    BatchRepository,
    StreamingRepository,
    CompleteRepository,
    FilterProtocol,
    FilterType,
)

# Modern repository implementations
from uno.domain.entity import (
    EntityRepository,
    InMemoryRepository,
    SQLAlchemyRepository,
    EntityMapper,
)

# Modern Unit of Work implementations
from uno.core.uow import (
    AbstractUnitOfWork,
    DatabaseUnitOfWork,
)


# For backward compatibility 


from uno.infrastructure.repositories.di import (
    init_repository_system,
    get_repository,
    get_unit_of_work,
    register_specification_translator,
    clear_repository_cache,
)


# Export everything for convenient imports
__all__ = [
    # Core base implementations
    "BaseRepository",
    "SpecificationRepository",
    "BatchRepository",
    "StreamingRepository",
    "CompleteRepository",
    "FilterProtocol",
    "FilterType",
    # Modern repository implementations
    "EntityRepository",
    "InMemoryRepository",
    "SQLAlchemyRepository",
    "EntityMapper",
    # Modern Unit of Work
    "AbstractUnitOfWork",
    "DatabaseUnitOfWork",
    # DI helpers
    "init_repository_system",
    "get_repository",
    "get_unit_of_work",
    "register_specification_translator",
    "clear_repository_cache",
]