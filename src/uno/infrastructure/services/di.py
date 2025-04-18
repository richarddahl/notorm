"""
Dependency injection integration for the Uno service pattern.

This module provides functions for registering services with the dependency
injection system and for obtaining services through DI. It integrates with
the service factory to create services with the correct dependencies.
"""

import logging
from typing import (
    Dict,
    Any,
    Type,
    TypeVar,
    Optional,
    Generic,
    cast,
    Callable,
    get_type_hints,
)

from uno.core.base.error import BaseError
from uno.dependencies.scoped_container import (
    ServiceCollection,
    get_container,
    get_service,
)
from uno.dependencies.interfaces import UnoConfigProtocol

from uno.infrastructure.services.protocols import (
    ServiceProtocol,
    CrudServiceProtocol,
    AggregateCrudServiceProtocol,
    QueryServiceProtocol,
    ApplicationServiceProtocol,
    EventCollectingServiceProtocol,
    ReadModelServiceProtocol,
    DomainEventPublisherProtocol,
)

from uno.infrastructure.services.base import (
    Service,
    CrudService,
    AggregateCrudService,
    QueryService,
    RepositoryQueryService,
    ApplicationService,
    EventPublisher,
)

from uno.infrastructure.services.factory import (
    ServiceFactory,
    get_service_factory,
    create_service,
    create_crud_service,
    create_aggregate_service,
    create_query_service,
    create_application_service,
    create_event_publisher,
)

T = TypeVar("T")
EntityT = TypeVar("EntityT")
QueryT = TypeVar("QueryT")
ResultT = TypeVar("ResultT")


def init_service_system(services: Optional[ServiceCollection] = None) -> None:
    """
    Initialize the service system.

    This function registers core service components with the dependency
    injection system, making them available throughout the application.

    Args:
        services: Optional service collection to register with
    """
    # Get the container
    container = get_container()

    # Create a service collection if not provided
    if services is None:
        services = ServiceCollection()

    # Register the service factory
    services.add_singleton(
        ServiceFactory, ServiceFactory, logger=logging.getLogger("uno.services")
    )

    # Register factory functions
    services.add_singleton(Callable[[Type[T]], T], lambda: create_service)

    # Register service base classes
    services.add_transient(Service, Service)
    services.add_transient(CrudService, CrudService)
    services.add_transient(AggregateCrudService, AggregateCrudService)
    services.add_transient(QueryService, QueryService)
    services.add_transient(RepositoryQueryService, RepositoryQueryService)
    services.add_transient(ApplicationService, ApplicationService)
    services.add_transient(EventPublisher, EventPublisher)

    # Register the event publisher
    event_publisher = create_event_publisher()
    services.add_instance(DomainEventPublisherProtocol, event_publisher)

    # Update the container with the service collection
    for service_type, registration in services._registrations.items():
        container.register(
            service_type,
            registration.implementation,
            registration.scope,
            registration.params,
        )

    for service_type, instance in services._instances.items():
        container.register_instance(service_type, instance)

    logger = logging.getLogger("uno.services")
    logger.info("Service system initialized")


def get_service_by_type(service_type: Type[T]) -> T:
    """
    Get a service by its type.

    Args:
        service_type: The service type

    Returns:
        The service instance
    """
    return get_service(service_type)


def get_crud_service(
    entity_type: Type[EntityT], **kwargs
) -> CrudServiceProtocol[EntityT]:
    """
    Get a CRUD service for an entity type.

    Args:
        entity_type: The entity type
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The CRUD service
    """
    # Try to get a registered service first
    try:
        service = get_service(CrudServiceProtocol[entity_type])
        return cast(CrudServiceProtocol[EntityT], service)
    except Exception:
        # Create a new service
        return create_crud_service(entity_type, **kwargs)


def get_aggregate_service(
    entity_type: Type[EntityT], **kwargs
) -> AggregateCrudServiceProtocol[EntityT]:
    """
    Get an aggregate CRUD service for an entity type.

    Args:
        entity_type: The entity type
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The aggregate CRUD service
    """
    # Try to get a registered service first
    try:
        service = get_service(AggregateCrudServiceProtocol[entity_type])
        return cast(AggregateCrudServiceProtocol[EntityT], service)
    except Exception:
        # Create a new service
        return create_aggregate_service(entity_type, **kwargs)


def get_query_service(
    entity_type: Type[EntityT], **kwargs
) -> QueryServiceProtocol[EntityT]:
    """
    Get a query service for an entity type.

    Args:
        entity_type: The entity type
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The query service
    """
    # Try to get a registered service first
    try:
        service = get_service(QueryServiceProtocol[entity_type])
        return cast(QueryServiceProtocol[EntityT], service)
    except Exception:
        # Create a new service
        return create_query_service(entity_type, **kwargs)


def get_application_service(
    service_type: Type[ApplicationServiceProtocol], **kwargs
) -> ApplicationServiceProtocol:
    """
    Get an application service.

    Args:
        service_type: The service type
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The application service
    """
    # Try to get a registered service first
    try:
        service = get_service(service_type)
        return cast(ApplicationServiceProtocol, service)
    except Exception:
        # Create a new service
        return create_application_service(service_type, **kwargs)


def get_event_publisher() -> DomainEventPublisherProtocol:
    """
    Get the event publisher.

    Returns:
        The event publisher
    """
    try:
        return get_service(DomainEventPublisherProtocol)
    except Exception:
        return create_event_publisher()


def register_service(service_type: Type[T], implementation: Type[T], **kwargs) -> None:
    """
    Register a service with the DI container.

    Args:
        service_type: The service type to register
        implementation: The implementation class
        **kwargs: Additional arguments to pass to the service constructor
    """
    container = get_container()
    container.register(service_type, implementation, params=kwargs)


def register_service_instance(service_type: Type[T], instance: T) -> None:
    """
    Register a service instance with the DI container.

    Args:
        service_type: The service type to register
        instance: The service instance
    """
    container = get_container()
    container.register_instance(service_type, instance)


def register_crud_service(
    entity_type: Type[EntityT],
    implementation: Type[CrudServiceProtocol[EntityT]],
    **kwargs,
) -> None:
    """
    Register a CRUD service for an entity type.

    Args:
        entity_type: The entity type
        implementation: The service implementation
        **kwargs: Additional arguments to pass to the service constructor
    """
    # Create the service
    service = create_service(implementation, entity_type=entity_type, **kwargs)

    # Register it with the container
    register_service_instance(CrudServiceProtocol[entity_type], service)


def register_aggregate_service(
    entity_type: Type[EntityT],
    implementation: Type[AggregateCrudServiceProtocol[EntityT]],
    **kwargs,
) -> None:
    """
    Register an aggregate CRUD service for an entity type.

    Args:
        entity_type: The entity type
        implementation: The service implementation
        **kwargs: Additional arguments to pass to the service constructor
    """
    # Create the service
    service = create_service(implementation, entity_type=entity_type, **kwargs)

    # Register it with the container
    register_service_instance(AggregateCrudServiceProtocol[entity_type], service)


def register_query_service(
    entity_type: Type[EntityT],
    implementation: Type[QueryServiceProtocol[EntityT]],
    **kwargs,
) -> None:
    """
    Register a query service for an entity type.

    Args:
        entity_type: The entity type
        implementation: The service implementation
        **kwargs: Additional arguments to pass to the service constructor
    """
    # Create the service
    service = create_service(implementation, entity_type=entity_type, **kwargs)

    # Register it with the container
    register_service_instance(QueryServiceProtocol[entity_type], service)


def register_application_service(
    service_type: Type[ApplicationServiceProtocol],
    implementation: Type[ApplicationServiceProtocol],
    **kwargs,
) -> None:
    """
    Register an application service.

    Args:
        service_type: The service type to register
        implementation: The service implementation
        **kwargs: Additional arguments to pass to the service constructor
    """
    # Create the service
    service = create_service(implementation, **kwargs)

    # Register it with the container
    register_service_instance(service_type, service)
