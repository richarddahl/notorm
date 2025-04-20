"""
Infrastructure layer for the Uno framework.

This package contains infrastructure components that implement technical concerns
and provide concrete implementations of domain interfaces.
"""

# Import modern repository and unit of work components for convenience
from uno.core.uow import AbstractUnitOfWork, DatabaseUnitOfWork
from uno.domain.entity import (
    EntityMapper,
    EntityRepository,
    InMemoryRepository,
    SQLAlchemyRepository,
)
from uno.infrastructure.services import (
    # Protocols
    AggregateCrudServiceProtocol,
    ApplicationServiceProtocol,
    CrudServiceProtocol,
    DomainEventPublisherProtocol,
    EventCollectingServiceProtocol,
    QueryServiceProtocol,
    RepositoryQueryServiceProtocol,
    ServiceProtocol,
    TransactionalServiceProtocol,
    ReadModelServiceProtocol,

    # Base implementations
    AggregateCrudService,
    ApplicationService,
    CrudService,
    EventPublisher,
    QueryService,
    RepositoryQueryService,
    Service,
    TransactionalService,

    # Factory functions
    ServiceFactory,
    create_aggregate_service,
    create_application_service,
    create_crud_service,
    create_event_publisher,
    create_query_service,
    create_service,
    get_service_factory,

    # DI helpers
    get_aggregate_service,
    get_application_service,
    get_crud_service,
    get_event_publisher,
    get_query_service,
    get_service_by_type,
    init_service_system,
)