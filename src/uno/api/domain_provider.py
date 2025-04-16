"""
Dependency injection provider for the API module.

This module defines the ApiProvider class, which configures dependencies for the API
module, including registering repositories, services, and adapters.
"""

import logging
import os
from typing import Optional, Type, TypeVar, Any, Dict, ClassVar

import inject

from uno.domain.repositories import Repository

from .domain_repositories import (
    ApiResourceRepositoryProtocol,
    EndpointConfigRepositoryProtocol,
    InMemoryApiResourceRepository,
    InMemoryEndpointConfigRepository,
    FileApiResourceRepository
)
from .domain_services import (
    ApiResourceServiceProtocol,
    EndpointFactoryServiceProtocol,
    RepositoryAdapterServiceProtocol,
    ApiResourceService,
    EndpointFactoryService,
    RepositoryAdapterService
)


# Type variables
T = TypeVar('T')


class ApiProvider:
    """
    Provider class for API module dependencies.
    
    This class is responsible for configuring dependencies for the API module,
    including registering repositories, services, and adapters in the dependency
    injection container. It also provides static methods for accessing common
    services without directly using the dependency injection container.
    """
    
    _configured: ClassVar[bool] = False
    _logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
    
    @classmethod
    def configure(
        cls,
        resource_repository: Optional[ApiResourceRepositoryProtocol] = None,
        endpoint_repository: Optional[EndpointConfigRepositoryProtocol] = None,
        persistence_directory: Optional[str] = None
    ) -> None:
        """
        Configure the API module dependencies.
        
        Args:
            resource_repository: Optional custom implementation of the API resource repository
            endpoint_repository: Optional custom implementation of the endpoint configuration repository
            persistence_directory: Optional directory path for file-based repositories
        """
        if cls._configured:
            cls._logger.warning("ApiProvider is already configured, reconfiguring")
        
        def configure_api_module(binder: inject.Binder) -> None:
            """Configure the API module bindings."""
            # Configure repositories
            if resource_repository:
                binder.bind(ApiResourceRepositoryProtocol, resource_repository)
            elif persistence_directory:
                binder.bind(
                    ApiResourceRepositoryProtocol,
                    FileApiResourceRepository(
                        directory=os.path.join(persistence_directory, "api_resources")
                    )
                )
            else:
                binder.bind(ApiResourceRepositoryProtocol, InMemoryApiResourceRepository())
            
            if endpoint_repository:
                binder.bind(EndpointConfigRepositoryProtocol, endpoint_repository)
            else:
                binder.bind(EndpointConfigRepositoryProtocol, InMemoryEndpointConfigRepository())
            
            # Configure services
            binder.bind(
                ApiResourceServiceProtocol,
                ApiResourceService(
                    resource_repository=inject.instance(ApiResourceRepositoryProtocol),
                    endpoint_repository=inject.instance(EndpointConfigRepositoryProtocol)
                )
            )
            
            binder.bind(
                EndpointFactoryServiceProtocol,
                EndpointFactoryService(
                    api_service=inject.instance(ApiResourceServiceProtocol)
                )
            )
            
            binder.bind(
                RepositoryAdapterServiceProtocol,
                RepositoryAdapterService()
            )
        
        # Install the API module configuration
        inject.clear_and_configure(configure_api_module)
        cls._configured = True
    
    @classmethod
    def get_api_resource_service(cls) -> ApiResourceServiceProtocol:
        """
        Get the API resource service.
        
        Returns:
            The API resource service instance
        """
        return inject.instance(ApiResourceServiceProtocol)
    
    @classmethod
    def get_endpoint_factory_service(cls) -> EndpointFactoryServiceProtocol:
        """
        Get the endpoint factory service.
        
        Returns:
            The endpoint factory service instance
        """
        return inject.instance(EndpointFactoryServiceProtocol)
    
    @classmethod
    def get_repository_adapter_service(cls) -> RepositoryAdapterServiceProtocol:
        """
        Get the repository adapter service.
        
        Returns:
            The repository adapter service instance
        """
        return inject.instance(RepositoryAdapterServiceProtocol)
    
    @classmethod
    def create_repository_adapter(
        cls,
        repository: Repository,
        entity_type: Type,
        schema_type: Type,
        filter_manager: Optional[Any] = None,
        read_only: bool = False,
        batch_support: bool = False
    ) -> Any:
        """
        Create a repository adapter.
        
        Args:
            repository: The domain repository to adapt
            entity_type: The entity type the repository works with
            schema_type: The schema type for API requests/responses
            filter_manager: Optional filter manager for query filtering
            read_only: Whether the adapter should be read-only
            batch_support: Whether the adapter should support batch operations
            
        Returns:
            A repository adapter instance
        """
        adapter_service = cls.get_repository_adapter_service()
        return adapter_service.create_adapter(
            repository=repository,
            entity_type=entity_type,
            schema_type=schema_type,
            filter_manager=filter_manager,
            read_only=read_only,
            batch_support=batch_support
        )


class TestingApiProvider:
    """
    Provider class for API module testing dependencies.
    
    This class is used to configure the API module for testing purposes, allowing
    tests to inject mock repositories and services.
    """
    
    @classmethod
    def configure(
        cls,
        resource_repository: Optional[ApiResourceRepositoryProtocol] = None,
        endpoint_repository: Optional[EndpointConfigRepositoryProtocol] = None
    ) -> Dict[str, Any]:
        """
        Configure the API module for testing.
        
        Args:
            resource_repository: Optional mock resource repository
            endpoint_repository: Optional mock endpoint repository
            
        Returns:
            A dictionary of configured dependencies
        """
        # Create default repositories if not provided
        if not resource_repository:
            resource_repository = InMemoryApiResourceRepository()
        
        if not endpoint_repository:
            endpoint_repository = InMemoryEndpointConfigRepository()
        
        # Create services
        api_service = ApiResourceService(
            resource_repository=resource_repository,
            endpoint_repository=endpoint_repository
        )
        
        endpoint_factory_service = EndpointFactoryService(
            api_service=api_service
        )
        
        adapter_service = RepositoryAdapterService()
        
        # Configure dependency injection
        def configure_test_api_module(binder: inject.Binder) -> None:
            """Configure the API module for testing."""
            binder.bind(ApiResourceRepositoryProtocol, resource_repository)
            binder.bind(EndpointConfigRepositoryProtocol, endpoint_repository)
            binder.bind(ApiResourceServiceProtocol, api_service)
            binder.bind(EndpointFactoryServiceProtocol, endpoint_factory_service)
            binder.bind(RepositoryAdapterServiceProtocol, adapter_service)
        
        # Install the test configuration
        inject.clear_and_configure(configure_test_api_module)
        
        # Return the dependencies for test verification
        return {
            "resource_repository": resource_repository,
            "endpoint_repository": endpoint_repository,
            "api_service": api_service,
            "endpoint_factory_service": endpoint_factory_service,
            "adapter_service": adapter_service
        }