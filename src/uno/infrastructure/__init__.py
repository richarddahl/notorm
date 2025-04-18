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

# Import service components for convenience
from uno.infrastructure.services import (
    # Protocols
    ServiceProtocol,
    TransactionalServiceProtocol,
    CrudServiceProtocol,
    AggregateCrudServiceProtocol,
    QueryServiceProtocol,
    RepositoryQueryServiceProtocol,
    ApplicationServiceProtocol,
    EventCollectingServiceProtocol,
    ReadModelServiceProtocol,
    DomainEventPublisherProtocol,
    
    # Base implementations
    Service,
    TransactionalService,
    CrudService,
    AggregateCrudService,
    QueryService,
    RepositoryQueryService,
    ApplicationService,
    EventPublisher,
    
    # Factory functions
    ServiceFactory,
    get_service_factory,
    create_service,
    create_crud_service,
    create_aggregate_service,
    create_query_service,
    create_application_service,
    create_event_publisher,
    
    # DI helpers
    init_service_system,
    get_service_by_type,
    get_crud_service,
    get_aggregate_service,
    get_query_service,
    get_application_service,
    get_event_publisher,
)