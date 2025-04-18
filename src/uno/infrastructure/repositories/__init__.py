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

# Import from core base
from uno.core.base.repository import (
    BaseRepository,
    SpecificationRepository,
    BatchRepository,
    StreamingRepository,
    CompleteRepository,
    RepositoryProtocol,
    SpecificationRepositoryProtocol,
    BatchRepositoryProtocol,
    StreamingRepositoryProtocol,
    FilterProtocol,
    FilterType,
)

# Re-export protocols from infrastructure for backward compatibility
from uno.infrastructure.repositories.protocols import (
    EventCollectingRepositoryProtocol,
    AggregateRootRepositoryProtocol,
    UnitOfWorkProtocol,
    RepositoryFactoryProtocol,
)

# For backward compatibility 
from uno.infrastructure.repositories.base import (
    EventCollectingRepository,
    AggregateRepository,
)

from uno.infrastructure.repositories.sqlalchemy import (
    SQLAlchemyRepository,
    SQLAlchemySpecificationRepository,
    SQLAlchemyBatchRepository,
    SQLAlchemyStreamingRepository,
    SQLAlchemyCompleteRepository,
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

# Backward compatibility aliases
Repository = BaseRepository

# Export everything for convenient imports
__all__ = [
    # Core base protocols
    "RepositoryProtocol",
    "SpecificationRepositoryProtocol",
    "BatchRepositoryProtocol",
    "StreamingRepositoryProtocol",
    "FilterProtocol",
    "FilterType",
    
    # Infrastructure-specific protocols
    "EventCollectingRepositoryProtocol",
    "AggregateRootRepositoryProtocol",
    "UnitOfWorkProtocol",
    "RepositoryFactoryProtocol",
    
    # Base implementations
    "BaseRepository",
    "Repository",  # Alias for backward compatibility
    "SpecificationRepository",
    "BatchRepository",
    "StreamingRepository",
    "EventCollectingRepository",
    "AggregateRepository",
    "CompleteRepository",
    
    # SQLAlchemy implementations
    "SQLAlchemyRepository",
    "SQLAlchemySpecificationRepository",
    "SQLAlchemyBatchRepository", 
    "SQLAlchemyStreamingRepository",
    "SQLAlchemyCompleteRepository",
    
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