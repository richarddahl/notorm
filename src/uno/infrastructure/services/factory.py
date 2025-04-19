"""
Service factory for the Uno framework.

DEPRECATED: This module has been deprecated and replaced by the ServiceFactory class
in uno.domain.entity.service. Please use the new implementation instead.

This module provides factory functions for creating and configuring services
according to the unified service pattern. The factory supports different service
types, dependency injection, and configuration.
"""

import logging
import warnings
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
    List,
    Tuple,
    Union,
)

warnings.warn(
    "The uno.infrastructure.services.factory module is deprecated. "
    "Use uno.domain.entity.service.ServiceFactory instead.",
    DeprecationWarning,
    stacklevel=2
)

from uno.core.base.error import BaseError
from uno.dependencies.scoped_container import get_container, get_service
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

from uno.infrastructure.repositories.protocols import (
    RepositoryProtocol,
    AggregateRootRepositoryProtocol,
)

T = TypeVar("T")
EntityT = TypeVar("EntityT")
QueryT = TypeVar("QueryT")
ResultT = TypeVar("ResultT")


class ServiceFactory:
    """
    Factory for creating service instances.

    This class provides methods for creating different types of services
    with appropriate dependencies and configuration.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service factory.

        Args:
            logger: Optional logger for service creation
        """
        self._logger = logger or logging.getLogger("uno.services")
        self._service_cache: Dict[Tuple[Type, str], Any] = {}

    def create_service(self, service_type: Type[T], **kwargs) -> T:
        """
        Create a service instance.

        Args:
            service_type: The service type to create
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            An instance of the service

        Raises:
            BaseError: If service creation fails
        """
        try:
            # Determine dependencies based on type hints
            dependencies = {}
            hint_types = get_type_hints(service_type.__init__)

            # Process each hint
            for param_name, param_type in hint_types.items():
                if param_name == "return":
                    continue

                if param_name in kwargs:
                    continue  # Skip if already provided

                # Try to resolve the dependency
                try:
                    dependencies[param_name] = get_service(param_type)
                except Exception:
                    # If we can't resolve it, we'll let the constructor handle it
                    pass

            # Merge dependencies with kwargs
            merged_args = {**dependencies, **kwargs}

            # Create the service
            service = service_type(**merged_args)

            return service
        except Exception as e:
            self._logger.error(
                f"Error creating service {service_type.__name__}: {str(e)}"
            )
            raise BaseError(
                f"Failed to create service {service_type.__name__}: {str(e)}",
                "SERVICE_CREATION_ERROR",
            )

    def create_crud_service(
        self,
        entity_type: Type[EntityT],
        repository: Optional[RepositoryProtocol[EntityT]] = None,
        **kwargs,
    ) -> CrudServiceProtocol[EntityT]:
        """
        Create a CRUD service for an entity type.

        Args:
            entity_type: The entity type
            repository: Optional repository to use
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            The CRUD service
        """
        # Get the repository if not provided
        if repository is None:
            from uno.infrastructure.repositories.di import get_repository

            repository = get_repository(entity_type)

        # Create the service
        return cast(
            CrudServiceProtocol[EntityT],
            self.create_service(
                CrudService, entity_type=entity_type, repository=repository, **kwargs
            ),
        )

    def create_aggregate_service(
        self,
        entity_type: Type[EntityT],
        repository: Optional[AggregateRootRepositoryProtocol[EntityT]] = None,
        **kwargs,
    ) -> AggregateCrudServiceProtocol[EntityT]:
        """
        Create an aggregate CRUD service for an entity type.

        Args:
            entity_type: The entity type
            repository: Optional repository to use
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            The aggregate CRUD service
        """
        # Get the repository if not provided
        if repository is None:
            from uno.infrastructure.repositories.di import get_repository

            repository = cast(
                AggregateRootRepositoryProtocol[EntityT],
                get_repository(entity_type, aggregate=True),
            )

        # Create the service
        return cast(
            AggregateCrudServiceProtocol[EntityT],
            self.create_service(
                AggregateCrudService,
                entity_type=entity_type,
                repository=repository,
                **kwargs,
            ),
        )

    def create_query_service(
        self,
        entity_type: Type[EntityT],
        repository: Optional[RepositoryProtocol[EntityT]] = None,
        **kwargs,
    ) -> QueryServiceProtocol[EntityT]:
        """
        Create a query service for an entity type.

        Args:
            entity_type: The entity type
            repository: Optional repository to use
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            The query service
        """
        # Get the repository if not provided
        if repository is None:
            from uno.infrastructure.repositories.di import get_repository

            repository = get_repository(entity_type)

        # Create the service
        return cast(
            QueryServiceProtocol[EntityT],
            self.create_service(
                RepositoryQueryService,
                entity_type=entity_type,
                repository=repository,
                **kwargs,
            ),
        )

    def create_application_service(
        self, service_type: Type[ApplicationServiceProtocol], **kwargs
    ) -> ApplicationServiceProtocol:
        """
        Create an application service.

        Args:
            service_type: The service type to create
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            The application service
        """
        return cast(
            ApplicationServiceProtocol, self.create_service(service_type, **kwargs)
        )

    def create_event_publisher(self, **kwargs) -> DomainEventPublisherProtocol:
        """
        Create an event publisher.

        Args:
            **kwargs: Additional arguments to pass to the publisher constructor

        Returns:
            The event publisher
        """
        # Try to get the event bus
        try:
            from uno.core.events import EventBus

            event_bus = get_service(EventBus)
            kwargs.setdefault("event_bus", event_bus)
        except Exception:
            # If we can't get the event bus, we'll let the constructor handle it
            pass

        return cast(
            DomainEventPublisherProtocol, self.create_service(EventPublisher, **kwargs)
        )

    def get_cached_service(
        self, service_type: Type[T], cache_key: str = "", **kwargs
    ) -> T:
        """
        Get or create a cached service instance.

        Args:
            service_type: The service type to create
            cache_key: Optional cache key
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            An instance of the service
        """
        cache_key_tuple = (service_type, cache_key)

        if cache_key_tuple not in self._service_cache:
            self._service_cache[cache_key_tuple] = self.create_service(
                service_type, **kwargs
            )

        return self._service_cache[cache_key_tuple]

    def clear_cache(self) -> None:
        """Clear the service cache."""
        self._service_cache.clear()

    def get_cached_crud_service(
        self, entity_type: Type[EntityT], cache_key: str = "", **kwargs
    ) -> CrudServiceProtocol[EntityT]:
        """
        Get or create a cached CRUD service.

        Args:
            entity_type: The entity type
            cache_key: Optional cache key
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            The CRUD service
        """
        key = f"crud_{entity_type.__name__}_{cache_key}"

        if (CrudService, key) not in self._service_cache:
            self._service_cache[(CrudService, key)] = self.create_crud_service(
                entity_type, **kwargs
            )

        return cast(
            CrudServiceProtocol[EntityT], self._service_cache[(CrudService, key)]
        )


# Global service factory instance
_service_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """
    Get the global service factory instance.

    Returns:
        The service factory
    """
    global _service_factory

    if _service_factory is None:
        _service_factory = ServiceFactory()

    return _service_factory


def create_service(service_type: Type[T], **kwargs) -> T:
    """
    Create a service instance.

    Args:
        service_type: The service type to create
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        An instance of the service
    """
    return get_service_factory().create_service(service_type, **kwargs)


def create_crud_service(
    entity_type: Type[EntityT],
    repository: Optional[RepositoryProtocol[EntityT]] = None,
    **kwargs,
) -> CrudServiceProtocol[EntityT]:
    """
    Create a CRUD service for an entity type.

    Args:
        entity_type: The entity type
        repository: Optional repository to use
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The CRUD service
    """
    return get_service_factory().create_crud_service(entity_type, repository, **kwargs)


def create_aggregate_service(
    entity_type: Type[EntityT],
    repository: Optional[AggregateRootRepositoryProtocol[EntityT]] = None,
    **kwargs,
) -> AggregateCrudServiceProtocol[EntityT]:
    """
    Create an aggregate CRUD service for an entity type.

    Args:
        entity_type: The entity type
        repository: Optional repository to use
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The aggregate CRUD service
    """
    return get_service_factory().create_aggregate_service(
        entity_type, repository, **kwargs
    )


def create_query_service(
    entity_type: Type[EntityT],
    repository: Optional[RepositoryProtocol[EntityT]] = None,
    **kwargs,
) -> QueryServiceProtocol[EntityT]:
    """
    Create a query service for an entity type.

    Args:
        entity_type: The entity type
        repository: Optional repository to use
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The query service
    """
    return get_service_factory().create_query_service(entity_type, repository, **kwargs)


def create_application_service(
    service_type: Type[ApplicationServiceProtocol], **kwargs
) -> ApplicationServiceProtocol:
    """
    Create an application service.

    Args:
        service_type: The service type to create
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        The application service
    """
    return get_service_factory().create_application_service(service_type, **kwargs)


def create_event_publisher(**kwargs) -> DomainEventPublisherProtocol:
    """
    Create an event publisher.

    Args:
        **kwargs: Additional arguments to pass to the publisher constructor

    Returns:
        The event publisher
    """
    return get_service_factory().create_event_publisher(**kwargs)


def get_cached_service(service_type: Type[T], cache_key: str = "", **kwargs) -> T:
    """
    Get or create a cached service instance.

    Args:
        service_type: The service type to create
        cache_key: Optional cache key
        **kwargs: Additional arguments to pass to the service constructor

    Returns:
        An instance of the service
    """
    return get_service_factory().get_cached_service(service_type, cache_key, **kwargs)


def clear_service_cache() -> None:
    """Clear the service cache."""
    get_service_factory().clear_cache()
