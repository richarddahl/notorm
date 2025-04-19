"""
Protocol definitions for dependency injection.

This module defines Protocol classes that provide interfaces for
various components in the Uno framework, enabling dependency injection
and improved testability.
"""

from typing import Protocol, TypeVar, Any, Dict, List, Optional, Type, Generic, AsyncIterator, ContextManager, Callable
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg
import psycopg

import warnings
T = TypeVar('T')
ModelT = TypeVar('ModelT')
SQLEmitterT = TypeVar('SQLEmitterT')
EntityT = TypeVar('EntityT')
EventT = TypeVar('EventT')
VectorT = TypeVar('VectorT')
QueryT = TypeVar('QueryT')
ResultT = TypeVar('ResultT')


class ConfigProtocol(Protocol):
    """
    Protocol for configuration providers.

    Configuration providers are responsible for managing application
    settings and configuration values.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key
            default: Default value if the key is not found

        Returns:
            The configuration value
        """
        ...

    def all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            A dictionary containing all configuration values
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key
            value: The value to set
        """
        ...

    def load(self, path: str) -> None:
        """
        Load configuration from a path.

        Args:
            path: The path to load configuration from
        """
        ...

    def reload(self) -> None:
        """Reload the configuration."""
        ...

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: The section name

        Returns:
            The configuration section
        """
        ...

# Note: The deprecated protocols have been removed
# UnoConfigProtocol, UnoDatabaseProviderProtocol, UnoDBManagerProtocol, UnoServiceProtocol
# Use ConfigProtocol, DatabaseProviderProtocol from uno.core.protocols.database, 
# and ServiceProtocol from uno.core.base.service instead.


class SQLEmitterFactoryProtocol(Protocol):
    """Protocol for SQL emitter factory services."""
    
    def register_emitter(self, name: str, emitter_class: Type[Any]) -> None:
        """Register an SQL emitter class with the factory."""
        ...
    
    def get_emitter(self, name: str, **kwargs) -> Any:
        """Create a new instance of a registered SQL emitter."""
        ...
    
    def create_emitter_instance(self, emitter_class: Type[Any], **kwargs) -> Any:
        """Create a new emitter instance from a class."""
        ...
    
    def register_core_emitters(self) -> None:
        """Register all core SQL emitters with the factory."""
        ...


class SQLExecutionProtocol(Protocol):
    """Protocol for SQL execution services."""
    
    def execute_ddl(self, ddl: str) -> None:
        """Execute a DDL statement."""
        ...
    
    def execute_script(self, script: str) -> None:
        """Execute a SQL script."""
        ...
    
    def execute_emitter(self, emitter: Any, dry_run: bool = False) -> Optional[List[Any]]:
        """Execute an SQL emitter."""
        ...


class SchemaManagerProtocol(Protocol):
    """Protocol for schema manager services."""
    
    def add_schema_config(self, name: str, config: Any) -> None:
        """Add a schema configuration."""
        ...
    
    def create_schema(self, schema_name: str, model: Type[Any]) -> Any:
        """Create a schema for a model."""
        ...
    
    def create_all_schemas(self, model: Type[Any]) -> Dict[str, Any]:
        """Create all schemas for a model."""
        ...
    
    def get_schema(self, schema_name: str) -> Optional[Any]:
        """Get a schema by name."""
        ...
    
    def register_standard_configs(self) -> None:
        """Register standard schema configurations."""
        ...
    
    def create_standard_schemas(self, model: Type[Any]) -> Dict[str, Any]:
        """Create standard schemas for a model."""
        ...


# DomainRepositoryProtocol has been replaced by the unified repository pattern
# in uno.infrastructure.repositories - see RepositoryProtocol and related protocols


class DomainServiceProtocol(Protocol, Generic[EntityT]):
    """Protocol for domain services."""
    
    async def get_by_id(self, id: str) -> Optional[EntityT]:
        """Get an entity by ID."""
        ...
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[EntityT]:
        """List entities with filtering, ordering, and pagination."""
        ...
    
    async def save(self, entity: EntityT) -> Optional[EntityT]:
        """Save an entity (create or update)."""
        ...
    
    async def delete(self, entity: EntityT) -> bool:
        """Delete an entity."""
        ...
    
    async def delete_by_id(self, id: str) -> bool:
        """Delete an entity by ID."""
        ...


class EventBusProtocol(Protocol):
    """Protocol for event buses."""
    
    async def publish(self, event: Any) -> None:
        """Publish an event to all subscribers."""
        ...
    
    async def publish_all(self, events: List[Any]) -> None:
        """Publish multiple events."""
        ...
    
    def subscribe(self, event_type: Type[Any], handler: Any) -> None:
        """Subscribe to a specific event type."""
        ...
    
    def subscribe_all(self, handler: Any) -> None:
        """Subscribe to all events."""
        ...
    
    def unsubscribe(self, event_type: Type[Any], handler: Any) -> None:
        """Unsubscribe from a specific event type."""
        ...
    
    def unsubscribe_all(self, handler: Any) -> None:
        """Unsubscribe from all events."""
        ...