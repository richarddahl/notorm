"""
Modern service provider for Uno framework.

This module implements a new service provider pattern that uses the scoped container
to provide enhanced dependency injection functionality, including proper scoping,
automatic dependency resolution, and improved lifecycle management.
"""

import inspect
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import (
    Dict,
    Any,
    Type,
    TypeVar,
    Optional,
    Union,
    List,
    Set,
    cast,
    Callable,
    Generic,
    overload,
)

from uno.settings import uno_settings
from uno.dependencies.scoped_container import (
    ServiceCollection,
    ServiceScope,
    ServiceResolver,
    initialize_container,
    get_container,
    get_service,
    create_scope,
    create_async_scope,
)
from uno.dependencies.interfaces import (
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SchemaManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    EventBusProtocol,
)
from uno.core.base.error import BaseError
from uno.core.errors.core_errors import (
    DependencyNotFoundError,
    DependencyResolutionError,
    DependencyCycleError,
)


T = TypeVar("T")
EntityT = TypeVar("EntityT")
QueryT = TypeVar("QueryT")
ResultT = TypeVar("ResultT")


class ServiceLifecycle:
    """Interface for services with custom initialization and disposal."""

    async def initialize(self) -> None:
        """Initialize the service asynchronously."""
        pass

    async def dispose(self) -> None:
        """Dispose the service asynchronously."""
        pass


class UnoServiceProvider:
    """
    Modern service provider for the Uno framework.

    This class provides a centralized registry for all services in the application,
    with support for scoped services, lifecycle management, and automatic dependency resolution.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service provider.

        Args:
            logger: Optional logger for diagnostic information
        """
        self._logger = logger or logging.getLogger("uno.services")
        self._initialized = False
        self._base_services = ServiceCollection()
        self._extensions: Dict[str, ServiceCollection] = {}
        self._lifecycle_queue: List[Type[ServiceLifecycle]] = []
        self._initializing = False

    def configure_services(self, services: ServiceCollection) -> None:
        """
        Configure the base services.

        Args:
            services: The service collection to use
        """
        if self._initialized:
            raise BaseError(
                "Services have already been initialized and cannot be reconfigured",
                "SERVICES_ALREADY_INITIALIZED",
            )
        self._base_services = services

    def register_extension(self, name: str, services: ServiceCollection) -> None:
        """
        Register a service extension.

        Args:
            name: The name of the extension
            services: The service collection containing extension services
        """
        if self._initialized:
            raise BaseError(
                "Services have already been initialized and cannot be extended",
                "SERVICES_ALREADY_INITIALIZED",
            )
        self._extensions[name] = services

    def register_lifecycle_service(self, service_type: Type[ServiceLifecycle]) -> None:
        """
        Register a service that requires lifecycle management.

        Args:
            service_type: The service type to register
        """
        self._lifecycle_queue.append(service_type)

    async def initialize(self) -> None:
        """
        Initialize the service provider.

        This method initializes the container and all registered services.
        It should be called during application startup.
        """
        if self._initialized:
            return

        if self._initializing:
            # Prevent circular initialization
            self._logger.warning("Service initialization is already in progress")
            return

        self._initializing = True
        try:
            # Initialize container with base services
            initialize_container(self._base_services, self._logger)

            # Initialize each extension
            for name, services in self._extensions.items():
                container = get_container()
                for (
                    service_type,
                    registration,
                ) in services._registrations.items():  # Access private attribute
                    container.register(
                        service_type,
                        registration.implementation,
                        registration.scope,
                        registration.params,
                    )
                for (
                    service_type,
                    instance,
                ) in services._instances.items():  # Access private attribute
                    container.register_instance(service_type, instance)

                self._logger.info(f"Initialized extension: {name}")

            # Initialize lifecycle services
            if self._lifecycle_queue:
                self._logger.info(
                    f"Initializing {len(self._lifecycle_queue)} lifecycle services"
                )

                async with create_async_scope("lifecycle_initialization") as scope:
                    # Initialize each service
                    for service_type in self._lifecycle_queue:
                        try:
                            service = scope.resolve(service_type)
                            await service.initialize()
                            self._logger.debug(
                                f"Initialized lifecycle service: {service_type.__name__}"
                            )
                        except Exception as e:
                            self._logger.error(
                                f"Error initializing service {service_type.__name__}: {str(e)}"
                            )
                            raise

            self._initialized = True
            self._logger.info("Service provider initialized successfully")

        finally:
            self._initializing = False

    async def shutdown(self) -> None:
        """
        Shut down the service provider.

        This method disposes all registered services in the reverse order they were initialized.
        It should be called during application shutdown.
        """
        if not self._initialized:
            return

        self._logger.info("Shutting down service provider")

        # Shut down lifecycle services in reverse order
        if self._lifecycle_queue:
            # Make a reversed copy to avoid modifying the original
            reversed_queue = self._lifecycle_queue.copy()
            reversed_queue.reverse()

            self._logger.info(f"Disposing {len(reversed_queue)} lifecycle services")

            for service_type in reversed_queue:
                try:
                    # Get the service if it exists
                    service = get_service(service_type)
                    await service.dispose()
                    self._logger.debug(
                        f"Disposed lifecycle service: {service_type.__name__}"
                    )
                except Exception as e:
                    self._logger.error(
                        f"Error disposing service {service_type.__name__}: {str(e)}"
                    )

        self._initialized = False
        self._logger.info("Service provider shut down")

    def is_initialized(self) -> bool:
        """
        Check if the service provider is initialized.

        Returns:
            True if the service provider is initialized, False otherwise
        """
        return self._initialized

    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service by its type.

        Args:
            service_type: The type of service to retrieve

        Returns:
            An instance of the requested service

        Raises:
            BaseError: If the service provider is not initialized
        """
        if not self._initialized:
            self._logger.error("Service provider not initialized")
            raise BaseError(
                "Service provider must be initialized before retrieving services",
                "SERVICES_NOT_INITIALIZED",
            )

        return get_service(service_type)

    @overload
    def get_service_in_scope(self, service_type: Type[T]) -> T: ...

    @overload
    def get_service_in_scope(self, service_type: Type[T], scope_id: str) -> T: ...

    def get_service_in_scope(
        self, service_type: Type[T], scope_id: Optional[str] = None
    ) -> T:
        """
        Get a service in a new scope.

        This method creates a new scope and resolves the service within it.
        The scope is closed after the service is resolved, so any scoped
        dependencies will be disposed.

        Args:
            service_type: The type of service to retrieve
            scope_id: Optional scope identifier

        Returns:
            An instance of the requested service

        Raises:
            BaseError: If the service provider is not initialized
        """
        if not self._initialized:
            self._logger.error("Service provider not initialized")
            raise BaseError(
                "Service provider must be initialized before retrieving services",
                "SERVICES_NOT_INITIALIZED",
            )

        with create_scope(scope_id) as scope:
            return scope.resolve(service_type)

    async def get_service_async_scope(
        self, service_type: Type[T], scope_id: Optional[str] = None
    ) -> T:
        """
        Get a service in a new async scope.

        This method creates a new async scope and resolves the service within it.
        The scope is closed after the service is resolved, so any scoped
        dependencies will be disposed.

        Args:
            service_type: The type of service to retrieve
            scope_id: Optional scope identifier

        Returns:
            An instance of the requested service

        Raises:
            BaseError: If the service provider is not initialized
        """
        if not self._initialized:
            self._logger.error("Service provider not initialized")
            raise BaseError(
                "Service provider must be initialized before retrieving services",
                "SERVICES_NOT_INITIALIZED",
            )

        async with create_async_scope(scope_id) as scope:
            return scope.resolve(service_type)

    @asynccontextmanager
    async def create_scope(self, scope_id: Optional[str] = None):
        """
        Create a service scope.

        This async context manager creates a new scope for resolving scoped services,
        ensuring they are properly disposed when the scope ends.

        Args:
            scope_id: Optional scope identifier

        Yields:
            The service resolver with the active scope

        Raises:
            BaseError: If the service provider is not initialized
        """
        if not self._initialized:
            self._logger.error("Service provider not initialized")
            raise BaseError(
                "Service provider must be initialized before creating a scope",
                "SERVICES_NOT_INITIALIZED",
            )

        async with create_async_scope(scope_id) as scope:
            yield scope

    # Convenience methods for common services

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

    def get_schema_manager(self) -> SchemaManagerProtocol:
        """
        Get the schema manager service.

        Returns:
            The schema manager service
        """
        # Use the new DTO manager instead of the deprecated schema manager
        from uno.dto import get_dto_manager

        return get_dto_manager()

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

    def get_event_bus(self) -> EventBusProtocol:
        """
        Get the event bus service.

        Returns:
            The event bus service
        """
        return self.get_service(EventBusProtocol)

    def get_vector_config(self):
        """
        Get the vector configuration service.

        Returns:
            The vector configuration service
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import VectorConfigServiceProtocol

        return self.get_service(VectorConfigServiceProtocol)

    def get_vector_update_service(self):
        """
        Get the vector update service.

        Returns:
            The vector update service
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import VectorUpdateServiceProtocol

        return self.get_service(VectorUpdateServiceProtocol)

    def get_batch_vector_update_service(self):
        """
        Get the batch vector update service.

        Returns:
            The batch vector update service
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
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import (
            VectorSearchServiceFactoryProtocol,
        )

        factory = self.get_service(VectorSearchServiceFactoryProtocol)
        return factory.create_search_service(entity_type, table_name, repository)

    def get_rag_service(self, vector_search):
        """
        Get a RAG service using a vector search service.

        Args:
            vector_search: The vector search service to use

        Returns:
            RAG service
        """
        # Import here to avoid circular imports
        from uno.dependencies.vector_interfaces import RAGServiceFactoryProtocol

        factory = self.get_service(RAGServiceFactoryProtocol)
        return factory.create_rag_service(vector_search)


# Global service provider instance
_service_provider = UnoServiceProvider()


def get_service_provider() -> UnoServiceProvider:
    """
    Get the global service provider instance.

    Returns:
        The service provider instance
    """
    return _service_provider


def register_singleton(service_type: Type[T], instance: T) -> None:
    """
    Register a singleton instance in the container.

    This is useful for registering resources and services that should be
    available globally across the application.

    Args:
        service_type: The type to register
        instance: The instance to register

    Raises:
        DependencyResolutionError: If the dependency injection is not set up
    """
    try:
        container = get_container()
        container.register_instance(service_type, instance)
    except Exception as e:
        raise DependencyResolutionError(
            f"Failed to register singleton for {service_type.__name__}: {str(e)}",
            "DEPENDENCY_REGISTRATION_ERROR",
        )


async def initialize_services() -> None:
    """
    Initialize all services.

    This function should be called during application startup to ensure
    that all services are properly initialized and ready to use.
    """
    # Configure the base service collection
    await configure_base_services()

    # Initialize the service provider
    provider = get_service_provider()
    await provider.initialize()


async def shutdown_services() -> None:
    """
    Shut down all services.

    This function should be called during application shutdown to ensure
    that all services are properly disposed.
    """
    provider = get_service_provider()
    await provider.shutdown()


async def configure_base_services() -> None:
    """
    Configure the base services for the application.

    This function configures the base services for the application,
    including the configuration service, database provider, and more.
    """
    provider = get_service_provider()
    if provider.is_initialized():
        return

    # Create service collection
    services = ServiceCollection()

    # Register configuration service
    from uno.settings import uno_settings
    from uno.dependencies.interfaces import ConfigProtocol

    class UnoConfig(ConfigProtocol):
        """Configuration provider implementation."""

        def __init__(self, settings=None):
            self._settings = settings or uno_settings
            
        def get(self, key: str, default: Any = None) -> Any:
            """Get a configuration value by key."""
            return getattr(self._settings, key, default)
        
        # Legacy method for backward compatibility
        def get_value(self, key: str, default: Any = None) -> Any:
            """Legacy alias for get() - for backward compatibility."""
            return self.get(key, default)

        def all(self) -> Dict[str, Any]:
            """Get all configuration values."""
            return {
                k: v
                for k, v in self._settings.__dict__.items()
                if not k.startswith("_")
            }
            
        def set(self, key: str, value: Any) -> None:
            """Set a configuration value (not implemented)."""
            # Settings from uno_settings are not mutable at runtime
            # Log a warning that this operation isn't supported
            import logging
            logging.getLogger("uno.config").warning(
                f"set() called on UnoConfig for key '{key}', but this implementation does not support setting values"
            )
            
        def load(self, path: str) -> None:
            """Load configuration from a path (not implemented)."""
            # This implementation doesn't support loading from a path
            import logging
            logging.getLogger("uno.config").warning(
                f"load() called on UnoConfig with path '{path}', but this implementation does not support loading from a path"
            )
            
        def reload(self) -> None:
            """Reload configuration (not implemented)."""
            # This implementation doesn't support reloading
            pass
            
        def get_section(self, section: str) -> Dict[str, Any]:
            """Get a configuration section."""
            # Simple implementation that returns all config values
            # A more sophisticated implementation would filter by section
            if not section:
                return self.all()
            return {}

    # Register with both interfaces for backward compatibility
    services.add_singleton(ConfigProtocol, UnoConfig)
    services.add_singleton(UnoConfigProtocol, UnoConfig)

    # Register logger
    services.add_singleton(logging.Logger, lambda: logging.getLogger("uno"))

    # Registry has been removed in favor of Domain approach
    # No replacement is necessary as the dependency injection system
    # now handles service registration and discovery

    # Register database provider
    from uno.database.config import ConnectionConfig
    from uno.database.provider import DatabaseProvider

    # Create connection config from settings
    connection_config = ConnectionConfig(
        db_role=uno_settings.DB_NAME + "_login",
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_ASYNC_DRIVER,
        db_schema=uno_settings.DB_SCHEMA,
    )

    # Create and register database provider
    db_provider = DatabaseProvider(
        connection_config, logger=logging.getLogger("uno.database")
    )
    services.add_instance(DatabaseProvider, db_provider)
    services.add_instance(UnoDatabaseProviderProtocol, db_provider)

    # Register database manager
    from uno.database.db_manager import DBManager

    services.add_singleton(
        UnoDBManagerProtocol,
        DBManager,
        connection_provider=db_provider.sync_connection,
        logger=logging.getLogger("uno.database"),
    )

    # Register SQL emitter factory
    from uno.sql.services import SQLEmitterFactoryService

    services.add_singleton(
        SQLEmitterFactoryProtocol,
        SQLEmitterFactoryService,
        config=UnoConfig(),
        logger=logging.getLogger("uno.sql"),
    )

    # Register SQL execution service
    from uno.sql.services import SQLExecutionService

    services.add_singleton(
        SQLExecutionProtocol, SQLExecutionService, logger=logging.getLogger("uno.sql")
    )

    # Register schema manager
    from uno.dto.services import SchemaManagerService

    services.add_singleton(
        SchemaManagerProtocol,
        SchemaManagerService,
        logger=logging.getLogger("uno.schema"),
    )

    # Register event bus
    from uno.core.events import EventBus, EventPublisher

    event_bus = EventBus(logger=logging.getLogger("uno.events"))
    services.add_instance(EventBus, event_bus)
    services.add_instance(EventBusProtocol, event_bus)
    services.add_instance(
        EventPublisher,
        EventPublisher(event_bus, logger=logging.getLogger("uno.events")),
    )

    # Register domain registry
    from uno.domain.factory import DomainRegistry

    services.add_singleton(
        DomainRegistry, DomainRegistry, logger=logging.getLogger("uno.domain")
    )

    # Configure the service provider
    provider.configure_services(services)

    # Initialize vector search components if available
    try:
        # Register vector search components
        from uno.dependencies.vector_provider import configure_vector_services

        await configure_vector_services()
    except (ImportError, AttributeError) as e:
        logging.getLogger("uno.services").debug(
            f"Vector search provider not available: {e}"
        )
        pass

    # Register queries provider
    try:
        from uno.queries.domain_provider import get_queries_provider

        provider.register_extension("queries", get_queries_provider())
    except (ImportError, AttributeError) as e:
        logging.getLogger("uno.services").debug(f"Queries provider not available: {e}")
        pass

    # Register reports provider
    try:
        from uno.reports.domain_provider import get_reports_provider

        provider.register_extension("reports", get_reports_provider())
    except (ImportError, AttributeError) as e:
        logging.getLogger("uno.services").debug(f"Reports provider not available: {e}")
        pass
