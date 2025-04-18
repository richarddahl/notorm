"""
Infrastructure layer for the Uno framework.

This package contains infrastructure components that implement technical concerns
and provide concrete implementations of domain interfaces.
"""

# Import repository components for convenience
from uno.infrastructure.repositories import (
    # Protocols
    RepositoryProtocol,
    SpecificationRepositoryProtocol,
    BatchRepositoryProtocol,
    StreamingRepositoryProtocol,
    EventCollectingRepositoryProtocol,
    AggregateRootRepositoryProtocol,
    UnitOfWorkProtocol,
    
    # Base implementations
    Repository,
    SpecificationRepository,
    BatchRepository,
    StreamingRepository,
    EventCollectingRepository,
    AggregateRepository,
    CompleteRepository,
    
    # Unit of Work
    UnitOfWork,
    SQLAlchemyUnitOfWork,
    InMemoryUnitOfWork,
    
    # Factory functions
    initialize_factories,
    create_repository,
    create_unit_of_work,
    
    # DI helpers
    init_repository_system,
    get_repository,
    get_unit_of_work,
)