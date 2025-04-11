"""
Dependency injection container for Uno framework.

This module provides a centralized dependency injection container
that can be configured at application startup and accessed throughout
the application.
"""

import logging
from typing import Dict, Any, Optional, Type, Callable, cast, TypeVar

import inject

from uno.settings import uno_settings
from uno.dependencies.interfaces import (
    UnoConfigProtocol,
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    SchemaManagerProtocol,
    EventBusProtocol,
)


T = TypeVar('T')


class UnoConfig(UnoConfigProtocol):
    """
    Configuration provider implementation.
    
    Uses settings from uno_settings as the source.
    """
    
    def __init__(self, settings=None):
        self._settings = settings or uno_settings
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self._settings, key, default)
    
    def all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return {
            k: v for k, v in self._settings.__dict__.items() 
            if not k.startswith('_')
        }


def configure_di(binder: inject.Binder) -> None:
    """
    Configure dependency injection bindings.
    
    Args:
        binder: The inject binder instance
    """
    # Bind core services
    from uno.registry import UnoRegistry
    binder.bind(UnoRegistry, UnoRegistry.get_instance())
    binder.bind(UnoConfigProtocol, UnoConfig())
    binder.bind(logging.Logger, logging.getLogger('uno'))
    
    # Create and bind database provider
    from uno.database.config import ConnectionConfig
    from uno.database.provider import DatabaseProvider
    
    # Create connection config from settings
    config = ConnectionConfig(
        db_role=uno_settings.DB_NAME + "_login",
        db_name=uno_settings.DB_NAME,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_ASYNC_DRIVER,
        db_schema=uno_settings.DB_SCHEMA,
    )
    
    # Create and bind database provider
    db_provider = DatabaseProvider(config, logger=logging.getLogger('uno.database'))
    binder.bind(DatabaseProvider, db_provider)
    binder.bind(UnoDatabaseProviderProtocol, db_provider)
    
    # Create and bind database manager
    from uno.database.db_manager import DBManager
    db_manager = DBManager(
        connection_provider=db_provider.sync_connection,
        logger=logging.getLogger('uno.database')
    )
    binder.bind(DBManager, db_manager)
    binder.bind(UnoDBManagerProtocol, db_manager)
    
    # Create and bind SQL emitter factory service
    from uno.sql.services import SQLEmitterFactoryService, SQLExecutionService
    sql_emitter_factory = SQLEmitterFactoryService(
        config=UnoConfig(),
        logger=logging.getLogger('uno.sql')
    )
    # Register core emitters
    sql_emitter_factory.register_core_emitters()
    # Bind the factory
    binder.bind(SQLEmitterFactoryService, sql_emitter_factory)
    binder.bind(SQLEmitterFactoryProtocol, sql_emitter_factory)
    
    # Create and bind SQL execution service
    sql_execution_service = SQLExecutionService(
        logger=logging.getLogger('uno.sql')
    )
    binder.bind(SQLExecutionService, sql_execution_service)
    binder.bind(SQLExecutionProtocol, sql_execution_service)
    
    # Create and bind Schema Manager service
    from uno.schema.services import SchemaManagerService
    schema_manager_service = SchemaManagerService(
        logger=logging.getLogger('uno.schema')
    )
    # Register standard schema configurations
    schema_manager_service.register_standard_configs()
    # Bind the service
    binder.bind(SchemaManagerService, schema_manager_service)
    binder.bind(SchemaManagerProtocol, schema_manager_service)
    
    # Create and bind Event Bus
    from uno.domain.events import EventBus, EventPublisher
    event_bus = EventBus(logger=logging.getLogger('uno.events'))
    event_publisher = EventPublisher(event_bus, logger=logging.getLogger('uno.events'))
    # Bind the services
    binder.bind(EventBus, event_bus)
    binder.bind(EventBusProtocol, event_bus)
    binder.bind(EventPublisher, event_publisher)
    
    # Create and bind Domain Registry
    from uno.domain.factory import DomainRegistry
    domain_registry = DomainRegistry(logger=logging.getLogger('uno.domain'))
    # Bind the registry
    binder.bind(DomainRegistry, domain_registry)


def get_container() -> inject.Injector:
    """
    Get the current DI container or create a new one.
    
    Returns:
        The injector instance
    """
    if not inject.is_configured():
        inject.configure(configure_di)
    # Use cast to ensure the return type is correct
    return cast(inject.Injector, inject.get_injector())


def get_instance(cls: Type[T]) -> T:
    """
    Get an instance of the given class from the DI container.
    
    Args:
        cls: The class to retrieve
        
    Returns:
        An instance of the requested class
    """
    return cast(T, inject.instance(cls))