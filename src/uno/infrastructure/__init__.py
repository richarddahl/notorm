"""
Infrastructure layer for the Uno framework.

This package contains infrastructure components that implement technical concerns
and provide concrete implementations of domain interfaces.
"""

# Import modern repository and unit of work components for convenience
from uno.domain.entity import (
    EntityRepository,
    InMemoryRepository,
    SQLAlchemyRepository,
    EntityMapper,
)
from uno.core.uow import (
    AbstractUnitOfWork,
    DatabaseUnitOfWork,
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