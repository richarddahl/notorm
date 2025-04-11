"""
Service Provider for Uno framework.

This module implements a unified Service Provider pattern that centralizes
access to all services in the application, providing a consistent interface
for service discovery and retrieval.
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional, Generic, cast, Union, List, Set

import inject

from uno.dependencies.container import configure_di, get_container, get_instance
from uno.dependencies.interfaces import (
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    SchemaManagerProtocol,
)

T = TypeVar("T")


class ServiceProvider:
    """
    Unified Service Provider for the Uno framework.
    
    This class provides a centralized registry for all services in the application,
    offering a consistent and type-safe interface for service discovery and retrieval.
    """
    
    def __init__(self):
        """Initialize the service provider."""
        self._initialized = False
        self._logger = logging.getLogger("uno.services")
        self._custom_services: Dict[Type[Any], Any] = {}
    
    def initialize(self) -> None:
        """
        Initialize the service provider.
        
        This method ensures the DI container is configured and ready to use.
        It should be called during application startup.
        """
        if not self._initialized:
            # Ensure inject is configured
            if not inject.is_configured():
                inject.configure(configure_di)
            self._initialized = True
            self._logger.info("Service Provider initialized")
    
    def register_service(self, service_type: Type[T], service_instance: T) -> None:
        """
        Register a custom service with the provider.
        
        This method allows registering application-specific services that
        aren't part of the core DI container.
        
        Args:
            service_type: The type or protocol of the service
            service_instance: The service instance to register
            
        Returns:
            None
        """
        self._logger.debug(f"Registering custom service of type {service_type.__name__}")
        self._custom_services[service_type] = service_instance
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service by its type.
        
        This is a generic method that retrieves a service from the DI container
        or from custom registered services, and performs type casting to ensure type safety.
        
        Args:
            service_type: The type of service to retrieve
            
        Returns:
            An instance of the requested service
            
        Raises:
            ValueError: If the service provider is not initialized
        """
        if not self._initialized:
            self._logger.error("Service Provider not initialized")
            raise ValueError(
                "Service Provider must be initialized before retrieving services"
            )
        
        # Check if this is a custom registered service
        if service_type in self._custom_services:
            self._logger.debug(f"Retrieving custom service of type {service_type.__name__}")
            return cast(T, self._custom_services[service_type])
        
        # Otherwise get from DI container
        self._logger.debug(f"Retrieving service of type {service_type.__name__}")
        return get_instance(service_type)
    
    def get_config(self) -> UnoConfigProtocol:
        """
        Get the configuration service.
        
        Returns:
            The configuration service
        """
        return self.get_service(UnoConfigProtocol)
    
    def get_db_provider(self) -> UnoDatabaseProviderProtocol:
        """
        Get the database provider service.
        
        Returns:
            The database provider service
        """
        return self.get_service(UnoDatabaseProviderProtocol)
    
    def get_db_manager(self) -> UnoDBManagerProtocol:
        """
        Get the database manager service.
        
        Returns:
            The database manager service
        """
        return self.get_service(UnoDBManagerProtocol)
    
    def get_sql_emitter_factory(self) -> SQLEmitterFactoryProtocol:
        """
        Get the SQL emitter factory service.
        
        Returns:
            The SQL emitter factory service
        """
        return self.get_service(SQLEmitterFactoryProtocol)
    
    def get_sql_execution_service(self) -> SQLExecutionProtocol:
        """
        Get the SQL execution service.
        
        Returns:
            The SQL execution service
        """
        return self.get_service(SQLExecutionProtocol)
    
    def get_schema_manager(self) -> SchemaManagerProtocol:
        """
        Get the schema manager service.
        
        Returns:
            The schema manager service
        """
        return self.get_service(SchemaManagerProtocol)
        
    def get_vector_config(self):
        """
        Get the vector configuration service.
        
        Returns:
            The vector configuration service
            
        Raises:
            ValueError: If the vector services are not initialized
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import VectorConfigServiceProtocol
        return self.get_service(VectorConfigServiceProtocol)
        
    def get_vector_update_service(self):
        """
        Get the vector update service.
        
        Returns:
            The vector update service
            
        Raises:
            ValueError: If the vector services are not initialized
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import VectorUpdateServiceProtocol
        return self.get_service(VectorUpdateServiceProtocol)
        
    def get_batch_vector_update_service(self):
        """
        Get the batch vector update service.
        
        Returns:
            The batch vector update service
            
        Raises:
            ValueError: If the vector services are not initialized
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import BatchVectorUpdateServiceProtocol
        return self.get_service(BatchVectorUpdateServiceProtocol)
        
    def get_vector_search_service(self, entity_type, table_name, repository=None):
        """
        Get a vector search service for a specific entity type.
        
        Args:
            entity_type: The entity type to search
            table_name: The database table name
            repository: Optional repository to use
            
        Returns:
            Vector search service
            
        Raises:
            RuntimeError: If vector services are not initialized
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_provider import get_vector_search_service
        return get_vector_search_service(entity_type, table_name, repository)
        
    def get_rag_service(self, vector_search):
        """
        Get a RAG service using a vector search service.
        
        Args:
            vector_search: The vector search service to use
            
        Returns:
            RAG service
            
        Raises:
            RuntimeError: If vector services are not initialized
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_provider import get_rag_service
        return get_rag_service(vector_search)


# Global service provider instance
_service_provider = ServiceProvider()


def get_service_provider() -> ServiceProvider:
    """
    Get the global service provider instance.
    
    Returns:
        The service provider instance
    """
    return _service_provider


def initialize_services() -> None:
    """
    Initialize all services.
    
    This function should be called during application startup to ensure
    that all services are properly initialized and ready to use.
    """
    provider = get_service_provider()
    provider.initialize()
    
    # Initialize vector search components if available
    try:
        from uno.dependencies.vector_provider import VectorSearchProvider
        vector_provider = VectorSearchProvider()
        vector_provider.register()
        vector_provider.boot()
        logging.getLogger("uno.services").info("Vector search provider initialized")
    except (ImportError, AttributeError) as e:
        logging.getLogger("uno.services").debug(f"Vector search provider not available: {e}")
        pass