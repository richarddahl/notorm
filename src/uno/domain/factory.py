"""
Factory pattern implementation for the Uno framework domain layer.

This module provides factory classes for creating domain entities, repositories,
and services in a consistent way.
"""

import logging
from typing import TypeVar, Generic, Dict, Type, Optional, Any

from uno.domain.core import Entity
from uno.domain.repository import Repository, UnoDBRepository
from uno.domain.service import DomainService, UnoEntityService


T = TypeVar("T", bound=Entity)
R = TypeVar("R", bound=Repository)
S = TypeVar("S", bound=DomainService)


class RepositoryFactory:
    """
    Factory for creating repositories.

    This factory creates and caches repository instances for domain entities.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the repository factory.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._repositories: Dict[Type[Entity], Repository] = {}

    def create_repository(
        self, entity_type: Type[T], repository_type: Type[R] = UnoDBRepository, **kwargs
    ) -> R:
        """
        Create a repository for an entity type.

        Args:
            entity_type: The entity type to create a repository for
            repository_type: The repository implementation to use
            **kwargs: Additional arguments to pass to the repository constructor

        Returns:
            A repository instance
        """
        if entity_type not in self._repositories:
            self.logger.debug(f"Creating repository for {entity_type.__name__}")
            self._repositories[entity_type] = repository_type(entity_type, **kwargs)

        return self._repositories[entity_type]


class ServiceFactory:
    """
    Factory for creating domain services.

    This factory creates and caches service instances for domain entities.
    """

    def __init__(
        self,
        repository_factory: Optional[RepositoryFactory] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the service factory.

        Args:
            repository_factory: Optional repository factory to use
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory or RepositoryFactory()
        self.logger = logger or logging.getLogger(__name__)
        self._services: Dict[Type[Entity], DomainService] = {}

    def create_service(
        self,
        entity_type: Type[T],
        service_type: Type[S] = UnoEntityService,
        repository: Optional[Repository] = None,
        **kwargs,
    ) -> S:
        """
        Create a service for an entity type.

        Args:
            entity_type: The entity type to create a service for
            service_type: The service implementation to use
            repository: Optional repository to use
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            A service instance
        """
        if entity_type not in self._services:
            self.logger.debug(f"Creating service for {entity_type.__name__}")

            # If no repository is provided, create one
            if repository is None:
                repository = self.repository_factory.create_repository(entity_type)

            # Create the service
            service_kwargs = {"repository": repository, **kwargs}
            self._services[entity_type] = service_type(entity_type, **service_kwargs)

        return self._services[entity_type]


class DomainRegistry:
    """
    Registry for domain components.

    This registry provides centralized access to domain entities, repositories,
    and services, coordinating their creation and lifecycle.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the domain registry.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository_factory = RepositoryFactory(logger)
        self.service_factory = ServiceFactory(self.repository_factory, logger)

    def get_repository(
        self, entity_type: Type[T], repository_type: Type[R] = UnoDBRepository, **kwargs
    ) -> R:
        """
        Get a repository for an entity type.

        Args:
            entity_type: The entity type to get a repository for
            repository_type: The repository implementation to use
            **kwargs: Additional arguments to pass to the repository constructor

        Returns:
            A repository instance
        """
        return self.repository_factory.create_repository(
            entity_type, repository_type, **kwargs
        )

    def get_service(
        self, entity_type: Type[T], service_type: Type[S] = UnoEntityService, **kwargs
    ) -> S:
        """
        Get a service for an entity type.

        Args:
            entity_type: The entity type to get a service for
            service_type: The service implementation to use
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            A service instance
        """
        return self.service_factory.create_service(entity_type, service_type, **kwargs)
